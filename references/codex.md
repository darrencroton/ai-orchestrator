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

Read `~/.codex/config.toml` for the user's default model (`model` key) and reasoning effort (`model_reasoning_effort` key). Use those defaults as a starting point unless the user specifies otherwise. Prefer omitting `-m` entirely when the configured default is acceptable. Never hardcode model names.

## Core Commands

```bash
# Non-interactive execution
codex exec "PROMPT" [-m <model>] -c model_reasoning_effort="<effort>" \
  [SANDBOX_FLAG] --skip-git-repo-check -C <dir> \
  -o /tmp/codex-out.txt 2>/tmp/codex-err.txt
cat /tmp/codex-out.txt

# Code review
codex exec review -m <model> --skip-git-repo-check \
  > /tmp/codex-out.txt 2>/tmp/codex-err.txt

# Resume most recent session
codex exec resume --last --skip-git-repo-check \
  > /tmp/codex-out.txt 2>/tmp/codex-err.txt
```

`-o /tmp/codex-out.txt` — writes the final agent message to file (preferred for non-interactive exec).
`2>/tmp/codex-err.txt` — separates stderr so thinking-token noise doesn't pollute extraction; check this file if extraction returns nothing.
`--skip-git-repo-check` — always include; allows running outside a git repo.

For multi-worker runs, prefer [../scripts/worker_jobs.py](../scripts/worker_jobs.py). When using the helper, let it own stdout/stderr capture and omit `-o` plus shell redirections from the worker command:

```bash
run_dir=$(python3 <skill-dir>/scripts/worker_jobs.py init)
python3 <skill-dir>/scripts/worker_jobs.py start --run-dir "$run_dir" --label codex-a -- \
  codex exec "PROMPT_A" -c model_reasoning_effort="medium" -s read-only --skip-git-repo-check -C <dir>
python3 <skill-dir>/scripts/worker_jobs.py start --run-dir "$run_dir" --label codex-b -- \
  codex exec "PROMPT_B" -c model_reasoning_effort="medium" -s read-only --skip-git-repo-check -C <dir>
python3 <skill-dir>/scripts/worker_jobs.py wait --run-dir "$run_dir"
python3 <skill-dir>/scripts/worker_jobs.py extract --run-dir "$run_dir" --label codex-a
```

Notes:

- Do not launch Codex CLI as a worker from inside a Codex CLI orchestrator session; choose another worker model or keep that part local.
- `-o` writes the final agent message when the run exits. The output file may not exist while the worker is still running.
- Do not infer failure from a missing output file before the worker exits.
- Read the whole final outfile by default when it is short; use `worker_jobs.py extract --sections ...` only for long structured outputs.
- If a worker exits non-zero or produces no usable outfile, inspect the matching stderr file, retry once with a tighter prompt if appropriate, then fall back.
- While workers run, keep the orchestrator on orchestration work only; do not duplicate the delegated investigation locally.
- Prefer foreground execution unless there is a clear parallel split worth the supervision cost.

## Key Flags

| Flag | Values | Notes |
|---|---|---|
| `-m / --model` | any string | From config or user request; omit when the default is acceptable |
| `-c model_reasoning_effort="VALUE"` | string | From config; override by task when needed |
| `-s / --sandbox` | `read-only`, `workspace-write`, `danger-full-access` | See Permission Guidance |
| `--full-auto` | — | Alias for `-a on-request --sandbox workspace-write` |
| `-C / --cd` | path | Set working directory |
| `--add-dir` | path | Add additional writable directory |
| `--search` | — | Enable live web search |
| `-o` | file path | Write last agent message to file instead of stdout |

## Permission Guidance

- **read-only**: analysis, review, plan review
- **workspace-write** / `--full-auto`: any task that modifies files
- **danger-full-access**: only if user explicitly requests unrestricted execution

Reasoning guidance:

- Mapping, investigation, and first-pass edits: prefer a medium supported setting even if the global default is higher
- Ambiguity, critique, or complex synthesis: use a higher supported setting only when it buys better results

## Resume

```bash
codex exec resume --last --skip-git-repo-check > /tmp/codex-out.txt 2>/tmp/codex-err.txt
```
Offer that exact command if continuation is useful.
