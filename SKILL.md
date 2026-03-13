---
name: ai-orchestrator
description: Routes coding and analysis tasks to external AI CLI tools (e.g. Claude Code, Codex CLI, GitHub Copilot CLI). Use when the user wants to delegate a task to an external AI agent, mentions "claude", "codex", or "copilot" explicitly, asks to "use another model", or wants to spread work across multiple models while keeping one orchestrator responsible for quality and direction.
---

# AI Orchestrator

Only the assistant directly handling the user's request may act as the orchestrator and use this skill for delegation. Delegated workers are never orchestrators. If the current assistant is not marked as orchestrator-capable in the model table below, it must not orchestrate with this skill.

The orchestrator owns context, planning, delegation, verification, testing, and final responsibility. It should push the bulk of eligible work to workers and spend its own tokens on plan quality, context packaging, verification, testing, and synthesis. Keep work local only when delegation would materially weaken correctness, lose critical context, slow verification enough to outweigh the token savings, or when prompt construction cost exceeds the task cost itself.

Use [scripts/worker_jobs.py](scripts/worker_jobs.py) to create a unique run directory, track worker artifacts, wait safely, check lightweight worker activity, cancel cleanly, and extract outputs for every worker run.
When using the helper, worker labels must use lowercase kebab-case in the form `<nn>-<tool>-<subtask-slug>[-rN]` (for example `01-codex-trace-login`). The helper writes `<label>-out.txt`, `<label>-err.txt`, and `<label>-status.json` inside the per-run directory and rejects bad labels before launch.
Use `worker_jobs.py activity --run-dir "$run_dir" --label <label>` as the health check. If it reports `healthy=yes`, keep waiting on cadence.

## Execution Checklist

At the start of each orchestration task, write a short checklist or todo list and keep it updated. Keep it operational, not narrative.

- planned worker split and labels
- launch and extraction steps
- any promised follow-up reviewer
- synthesis and final response

Before replying, every checklist item must be completed, deferred, or explicitly cancelled with a reason.

## Roles

| Role | Purpose | Typical tasks | Hard limits |
|---|---|---|---|
| **Orchestrator** | Human-facing controller | Planning, context packaging, verification, testing, final synthesis | Only the assistant directly handling the user may do this |
| **Senior worker** | Deep technical worker | Multi-file edits, refactors, complex logic, plan review | Self-contained prompt only; no re-delegation; if unavailable, keep the task local |
| **Junior worker** | Tactical worker | Surgical edits, approved git/GitHub operations, low-stakes web research, codebase mapping, non-critical summarising | Escalate when scope, context depth, or importance grows; never own correctness-critical decisions |

## Available Models

| Model | Roles | Best used for | Avoid for | Reference |
|---|---|---|---|---|
| **Claude Code** | Orchestrator, Senior worker | Complex edits, long-running coding, plan review, deep debugging | Low-value tactical chores when a junior worker is available | [references/claude.md](references/claude.md) |
| **Codex CLI** | Orchestrator, Senior worker | Complex edits, refactors, plan review, deep debugging | Low-value tactical chores when a junior worker is available | [references/codex.md](references/codex.md) |
| **GitHub Copilot CLI** | Junior worker | Surgical edits, approved git/GitHub operations, low-stakes web research, codebase mapping, non-critical summarising | Multi-file refactors, correctness-critical judgement, owning complex plans | [references/copilot.md](references/copilot.md) |

## Role Selection

Choose a role first:

| Task type | Role |
|---|---|
| Multi-file edits, refactoring, complex logic | Senior worker |
| Correctness-sensitive code investigation, parity analysis, migration analysis, ordering analysis | Senior worker |
| Second opinion / review of the orchestrator's plan | Senior worker (read-only) |
| Step-by-step plan verification against code | Senior worker (read-only) |
| Long-running agentic coding tasks | Senior worker |
| Single-file surgical edit, clear spec | Junior worker |
| Draft commit / PR / issue text | Junior worker |
| Execute an explicitly approved git or GitHub action | Junior worker |
| Low-stakes web research, documentation lookup | Junior worker |
| "Find where X happens" / execution trace / codebase map | Junior worker, only when non-critical |
| Summarise a large codebase or long document | Junior worker, only when the output is non-critical |

## Model Selection

After choosing a role, choose a model from the table above:

1. Follow the user's explicit model preference unless it conflicts with a hard limit or approval rule.
2. The orchestrator is the current assistant, but only if that model is marked orchestrator-capable.
3. For worker roles, prefer a non-orchestrator model that is marked suitable for the role and best matches the task.
4. For planning or architecture tasks, prefer one senior worker to map the code and another senior worker to critique the synthesized plan when multiple senior tools are available.
5. For workplan verification, use parallel code-mapping workers only when the codebase splits cleanly. Otherwise prefer one senior investigation and keep the second senior worker for plan review after a first synthesis draft.
6. Do not launch the same tool as a worker from inside itself. Choose another worker model or keep that part local.
7. If no suitable worker is available, keep the task with the orchestrator rather than forcing delegation.

## Delegation Discipline

Every prompt sent to an external tool must be self-contained. Always use the role templates in [references/templates.md](references/templates.md) — do not improvise. They exist to package the right context so delegation can be the default for eligible work. Include: specific task, relevant code or file paths, constraints, approval state for any state-changing git/GitHub action, and expected output format.

Every delegated prompt must also place the receiver in worker mode: it is not the orchestrator, it must not invoke `ai-orchestrator`, and it must not re-delegate to another model. If blocked, it should report the blocker instead of bouncing the task onward.
Use absolute file paths when practical. For analysis and investigation prompts, require `path:line` evidence for every material claim. Inside shell-quoted prompts, use `SECTION: NAME` markers rather than Markdown headings that start with `#`. Keep worker outputs compact and high-signal.

## Workflow

Each new task requires a fresh role selection decision — do not carry forward a prior delegation choice.

1. **Preflight** — confirm the chosen CLI is installed, authenticated if needed, and allowed by user approval constraints; load user config defaults as a starting point when the model reference requires it
2. **Plan** — determine what needs doing and which role owns each piece
3. **Checklist** — write a short execution checklist with worker labels, launch/extract steps, any promised follow-up reviewer, and the final synthesis step
4. **Select role and model** — use the role matrix, model table, and any user directive
5. **Load references** — read [references/templates.md](references/templates.md) and the selected model reference
6. **Fill template** — include all context; the worker knows nothing else. When an edit follows a planning worker, carry the exact target files, `path:line` anchors, and current snippets into the edit prompt so the worker can move straight to the edit
7. **Run** — invoke the model using its reference file and [scripts/worker_jobs.py](scripts/worker_jobs.py) so outputs live under one run directory with a manifest
8. **Monitor** — use a calm cadence. For senior or otherwise complex tasks, wait 5 minutes, then run `worker_jobs.py activity --run-dir "$run_dir" --label <label>` and re-check every 3 minutes while it stays `healthy=yes`. Very complex tasks may legitimately run for 15+ minutes. For simpler tasks, wait 3 minutes, then re-check every 2 minutes. Do not infer failure from empty stdout/stderr alone while `activity` is still healthy.
9. **Stay in role** — while workers run, do orchestration-only work such as monitoring status, updating the checklist, preparing the synthesis shell, or drafting a follow-up review prompt. Do not independently re-read or solve the same delegated investigation in parallel. A targeted local tie-break read is allowed only after worker outputs are back and there is a real conflict or missing evidence that materially affects the synthesis.
10. **Check** — use `worker_jobs.py extract` when you need the clean final answer or section filtering; otherwise read the short final outfile directly. Inspect stderr only when extraction is still empty or clearly malformed after completion; never reuse a differently named old file from another run; do not launch probe commands or retries while an equivalent worker is still running normally
11. **Test** (when appropriate) — the orchestrator runs tests via shell, interprets failures, and delegates follow-up fixes only when that helps quality

When a worker needs to stop, use `worker_jobs.py cancel --run-dir "$run_dir" --label <label>` so the helper records the final cancelled state cleanly.

For tasks that ask to verify a plan or workplan, return a compact step matrix:

- Step
- Evidence (`path:line`)
- Confidence
- Blocker or divergence

End with:

- Recommended next actions
- Non-blocking gaps or follow-up debt

Before replying:

- Remove duplicated sections
- If the checklist promised a follow-up worker or reviewer, either run it or say explicitly why it was skipped
- If a cheap missing file would materially change confidence, inspect it locally or with one targeted read-only follow-up before finalizing
- Do not mark a step `High` confidence when the blocker says more files or code paths are still needed for full verification

## Orchestrator Summary

After orchestration, summarize each model actually used with:

- What it did
- Brief feedback on how effective it was
- A rough score out of 10
- An estimated percentage of total work

Treat scores and percentages as rough operating feedback, not objective metrics. Keep the summary short and useful.
