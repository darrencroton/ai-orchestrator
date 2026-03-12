# Codex CLI Reference

## Roles It Can Fill

- **Orchestrator**: Yes
- **Senior worker**: Yes
- **Junior worker**: Not preferred

## Best Used For

- Complex edits and refactors
- Plan review
- Deep debugging

## Avoid Using It For

- Low-value tactical chores when a junior worker is available
- Launching Codex CLI workers from inside a Codex CLI orchestrator session

## Config Discovery

Read `~/.codex/config.toml` for the user's default model (`model` key). Use that model as a starting point unless the user specifies otherwise. Prefer `model_reasoning_effort="high"` for Codex worker tasks, and reserve `xhigh` for especially complex review or synthesis. Prefer omitting `-m` entirely when the configured default is acceptable. Never hardcode model names.

## Core Commands

Launch all Codex worker runs via [../scripts/worker_jobs.py](../scripts/worker_jobs.py). The commands below are the worker command payloads to pass after `worker_jobs.py start --label <label> --`.

```bash
# Non-interactive execution worker command
codex exec "PROMPT" [-m <model>] -c model_reasoning_effort="<effort>" \
  [SANDBOX_FLAG] --skip-git-repo-check -C <dir>

# Code review worker command
codex exec review -m <model> --skip-git-repo-check

# Resume most recent session
codex exec resume --last --skip-git-repo-check
```

`--skip-git-repo-check` — always include; allows running outside a git repo.

Use [../scripts/worker_jobs.py](../scripts/worker_jobs.py). Let it own stdout/stderr capture and omit `-o` plus shell redirections from the worker command. Worker labels must use `<nn>-<tool>-<subtask-slug>[-rN]`.

```bash
run_dir=$(python3 <skill-dir>/scripts/worker_jobs.py init --prefix auth-bug)
python3 <skill-dir>/scripts/worker_jobs.py start --run-dir "$run_dir" --label 01-codex-plan-scan -- \
  codex exec "PROMPT_PLAN_SCAN" -c model_reasoning_effort="high" -s read-only --skip-git-repo-check -C <dir>
python3 <skill-dir>/scripts/worker_jobs.py start --run-dir "$run_dir" --label 02-codex-review-plan -- \
  codex exec "PROMPT_PLAN_REVIEW" -c model_reasoning_effort="high" -s read-only --skip-git-repo-check -C <dir>
python3 <skill-dir>/scripts/worker_jobs.py wait --run-dir "$run_dir"
python3 <skill-dir>/scripts/worker_jobs.py extract --run-dir "$run_dir" --label 01-codex-plan-scan
```

Notes:

- Do not launch Codex CLI as a worker from inside a Codex CLI orchestrator session; choose another worker model or keep that part local.
- Do not infer failure from a missing helper-managed output file before the worker exits.
- Read the whole final outfile by default when it is short; use `worker_jobs.py extract --sections ...` only for long structured outputs.
- Follow the monitoring cadence in `SKILL.md`: let healthy workers run through their role-appropriate wait window, treat empty live captures as normal startup/analysis time, and do not probe or retry an equivalent healthy worker.
- If a worker exits non-zero, dies unexpectedly, or completes with no usable output, inspect the matching `<label>-err.txt` file, retry once with a tighter prompt if appropriate, then fall back.
- While workers run, keep the orchestrator on orchestration work only; do not duplicate the delegated investigation locally.
- Prefer foreground execution unless there is a clear parallel split worth the supervision cost.

## Key Flags

| Flag | Values | Notes |
|---|---|---|
| `-m / --model` | any string | From config or user request; omit when the default is acceptable |
| `-c model_reasoning_effort="VALUE"` | string | Prefer `high`; use `xhigh` only for especially complex work or explicit user preference |
| `-s / --sandbox` | `read-only`, `workspace-write`, `danger-full-access` | See Permission Guidance |
| `--full-auto` | — | Alias for `-a on-request --sandbox workspace-write` |
| `-C / --cd` | path | Set working directory |
| `--add-dir` | path | Add additional writable directory |
| `--search` | — | Enable live web search |

## Permission Guidance

- **read-only**: analysis, review, plan review
- **workspace-write** / `--full-auto`: any task that modifies files
- **danger-full-access**: only if user explicitly requests unrestricted execution

Reasoning guidance:

- Default to `high` for Codex worker tasks
- Escalate to `xhigh` only for especially complex review, ambiguity, or synthesis

## Resume

```bash
codex exec resume --last --skip-git-repo-check
```
Offer that exact command if continuation is useful.
