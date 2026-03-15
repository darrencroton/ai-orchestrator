# AI Orchestrator — Proposed Improvements

**Date:** 2026-03-15
**Status:** For dev team consideration
**Origin:** Design review drawing on external comparisons (see Research section)

---

## Background & Research

We reviewed three external projects as reference points:

**ClassicalDude/gist** — Two standalone Python scripts (`agent_lm.py`, `query_lm.py`) for local LM Studio models. Single-agent, synchronous, no persistence. Takeaway: path-traversal safety on file reads is worth codifying in our delegation templates.

**steveyegge/beads** — Distributed, git-backed issue tracker built for AI agents. Uses Dolt (version-controlled SQL) for persistence, hash-based collision-free IDs, dependency graph modelling (`blocks`, `parent-child`, `related`), atomic task claiming, and semantic memory decay for context compression. Targets many concurrent agents.

**steveyegge/gastown** — Multi-agent orchestration runtime for 20–30+ Claude Code agents. Git-worktree-backed persistent hooks, hierarchical roles (Mayor, Deacon, Witness, Polecat), performance-based work routing, OTel observability, and a four-tier integration strategy requiring no imports.

### Where we already exceed both

- Structured output contracts (`SECTION:`/`RESULT:`) with regex extraction
- Per-tool CLI references with exact flags, sandbox modes, and fallback extraction
- Hard role capability limits (Junior/Senior/Orchestrator) with enforced escalation thresholds
- Delegation template discipline requiring `path:line` evidence and self-contained prompts
- Graceful worker cancellation via SIGTERM + process group teardown
- Session extraction fallback when stdout is empty

The gaps identified below are the areas where Beads/Gastown have genuinely useful ideas applicable to our architecture.

---

## Agreed Decisions

### 1. Move manifest storage from `/tmp` to `.ai-orchestrator/`

**Current state:** `worker_jobs.py` writes run directories to `/private/tmp/ai-orchestrator/` (macOS default). This path is hardcoded, requires platform detection workarounds, and is wiped on restart — making multi-session work impossible.

**Proposed change:** Write all run artefacts to `.ai-orchestrator/runs/` within the project repository.

**Proposed structure:**

```
.ai-orchestrator/
  runs/
    run-20260315-120000-1234/     ← existing internal structure, unchanged
      manifest.json
      01-claude-foo-out.txt
      01-claude-foo-err.txt
      01-claude-foo-status.json
      .manifest.lock
  current -> runs/run-20260315-120000-1234/   ← symlink, updated on each init
  index.json                                   ← lightweight run registry
```

`index.json` stays small — one entry per run:

```json
[
  {
    "run": "run-20260315-120000-1234",
    "created_at": "2026-03-15T12:00:00Z",
    "status": "active",
    "task_slug": "add-auth-middleware"
  }
]
```

**Benefits:**
- Eliminates platform-specific tmp path detection from `worker_jobs.py`
- Run artefacts survive restarts and are available for post-hoc review
- `current` symlink lets a resumed orchestrator call `worker_jobs.py status --run current` without knowing the timestamped path
- `index.json` gives quick lookup of all past runs without scanning directories
- Aligns with Gastown's hook persistence approach without requiring Dolt or external infrastructure

**`worker_jobs.py` changes required:**
- Replace `DEFAULT_ROOT` constant and any platform detection with project-relative `.ai-orchestrator/runs/`
- `init` subcommand: write `current` symlink and append to `index.json`
- `status` subcommand: accept `--run current` as an alias

**`.gitignore` note:** Add `.ai-orchestrator/runs/` to `.gitignore` to keep worker artefacts (stdout/stderr dumps) out of version control. The directory itself and `index.json` can optionally be committed as a lightweight audit trail — team decision.

---

### 2. No git worktrees for worker isolation

**Considered:** Giving each worker its own git branch/worktree so parallel edits don't conflict, merging back after completion (Gastown's approach).

**Decision: Do not adopt.**

Our current delegation discipline — the orchestrator assigns non-overlapping file scopes per worker — already prevents the problem worktrees solve. Worktrees make sense for 20–30 agents with overlapping ownership. We coordinate 2–5 workers with intentionally separated scopes.

The costs outweigh the benefit:
- `worker_jobs.py` would need to create, track, and tear down worktrees per worker
- Every delegation template would need the worktree path injected rather than the repo root
- A mandatory merge step after every parallel edit run substantially increases orchestrator token cost
- For sequential workers (the common case) worktrees add zero value

**What to do instead:** Add a constraint to `SKILL.md` under delegation discipline: *"If two workers must edit overlapping files, serialise them or refactor the split — do not run them in parallel."* This is cheaper and safer than worktree infrastructure.

Worktrees remain available as a manual escape hatch for edge cases where a user's task genuinely requires parallel edits to shared files.

---

### 3. Add a handoff skill for session continuity

**Problem:** When an orchestrator session ends (usage limit, tool switch, crash), all planning context is lost. The next session must rediscover everything — what was planned, what's done, what workers ran, what comes next.

**Solution:** Adopt a `HANDOFF.md`-based handoff skill. The orchestrator writes (and keeps updated) a compact, high-signal document that a resumed session can use as its source of truth.

**Handoff skill additions specific to our use case:**

Add an **Orchestrator State** section to the standard handoff template:

```md
## Orchestrator State
- Run dir: `.ai-orchestrator/runs/run-YYYYMMDD-HHMMSS-PPPP/` (or `current/`)
- Workers: `01-claude-refactor-auth` (completed), `02-codex-add-tests` (in-progress)
- Model ratings so far: codex 8/10 targeted edits, claude 7/10 review
- Next planned workers: `03-copilot-git-ops` — pending 02 completion
```

This lets the resumed orchestrator immediately call `worker_jobs.py status` to check in-flight workers, skip re-planning for completed work, and carry forward model routing hints without repeating the task.

**Location open question (see below).**

---

## Open Questions

The following items came up in discussion but no decision was reached. Flagging for the team.

### A. Dependency notation between workers

Beads models `blocks` relationships between issues. Our manifest tracks workers in a flat dict — sequencing is implicit in the orchestrator's head, not in the data.

A lightweight addition to the manifest worker record:

```json
{
  "label": "02-codex-add-tests",
  "depends_on": ["01-claude-refactor-auth"]
}
```

This would make the `status` and `activity` subcommands able to warn when a worker is running whose dependency hasn't completed. Low implementation cost, meaningful value for complex multi-worker tasks. Worth adding alongside the `/tmp` migration.

### B. HANDOFF.md location

Two options:

| Location | Pro | Con |
|---|---|---|
| Project root (`HANDOFF.md`) | Discoverable, standard | Gets committed unless gitignored; pollutes root |
| `.ai-orchestrator/HANDOFF.md` | Co-located with other orchestration artefacts, easy to gitignore | Slightly less visible |

Recommendation: `.ai-orchestrator/HANDOFF.md`, gitignored by default, with an option to commit deliberately. Keeps the root clean and all orchestration state in one place.

### C. Prompt scoping / path safety

From the Gist review: `agent_lm.py` validates that file paths stay within the declared working directory before reading. Our framework delegates this entirely to worker CLIs and doesn't codify the boundary.

Low-cost addition: add a note to `references/templates.md` and the senior-worker edit template to always pass `--add-dir` with the tightest directory scope applicable to the task, not the repo root. Prevents workers from reading outside their intended scope if a prompt is poorly scoped.

### D. Context summarisation for long sessions

Beads implements "memory decay" — semantic summarisation of closed tasks to compress context over time. For very long tasks spanning many workers, our orchestrator accumulates growing context.

This doesn't require Beads infrastructure. A convention in `SKILL.md` would suffice: *"After completing a worker batch, summarise completed work in two to three lines and drop the raw worker output from active context."* The handoff skill partially handles this at session boundaries; this would cover within-session compression.

---

## Implementation Priority

| Item | Effort | Value | Recommended order |
|---|---|---|---|
| Move manifest to `.ai-orchestrator/` | Medium | High — eliminates tmp path hacks, enables persistence | 1 |
| Handoff skill (+ Orchestrator State section) | Low | High — closes multi-session gap immediately | 2 |
| `current` symlink + `index.json` | Low | Medium — discoverability, pairs with manifest move | 3 (with item 1) |
| Dependency notation in manifest | Low | Medium — makes sequencing explicit | 4 |
| HANDOFF.md location decision | Trivial | Low — convention only | 5 |
| Prompt scoping note in templates | Trivial | Low-medium — defensive, cheap to add | 6 |
| Context summarisation convention | Trivial | Medium for long tasks | 7 |
| Worktrees | High | Low for our scale | Not recommended |

---

## What We Are Not Adopting (and Why)

| Idea | Source | Reason not adopted |
|---|---|---|
| Dolt-backed distributed issue tracker | Beads | Infrastructure dependency far exceeds our coordination needs |
| Atomic `--claim` for concurrent assignment | Beads | Single-orchestrator model makes this unnecessary |
| Performance-based dynamic routing | Gastown | Static model table is sufficient; routing hints via handoff is a lighter alternative |
| OTel observability | Gastown | mtime-based health checks cover our monitoring needs at current scale |
| Hierarchical Mayor/Deacon/Witness roles | Gastown | Our 3-tier role model is sufficient; additional infrastructure roles add complexity without value at 2–5 worker scale |
| Git worktrees per worker | Gastown | See Decision 2 above |
