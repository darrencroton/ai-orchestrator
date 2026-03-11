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

## Config Discovery

Read `~/.codex/config.toml` for the user's default model (`model` key) and reasoning effort (`model_reasoning_effort` key). Use those defaults unless the user specifies otherwise. Prefer omitting `-m` entirely when the configured default is acceptable. Never hardcode model names.

## Core Commands

```bash
# Non-interactive execution
codex exec "PROMPT" [-m <model>] -c model_reasoning_effort="<effort>" \
  [SANDBOX_FLAG] --skip-git-repo-check -C <dir> \
  -o /tmp/codex-out.txt 2>/tmp/codex-err.txt
grep -A4 "^RESULT:" /tmp/codex-out.txt || sed -n '/^SECTION: /,$p' /tmp/codex-out.txt

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

For parallel workers, use unique filenames and wait on the worker pid instead of polling for file existence:

```bash
codex exec "PROMPT_A" -c model_reasoning_effort="medium" -s read-only --skip-git-repo-check \
  -C <dir> -o /tmp/codex-a-out.txt 2>/tmp/codex-a-err.txt &
pid_a=$!

codex exec "PROMPT_B" -c model_reasoning_effort="medium" -s read-only --skip-git-repo-check \
  -C <dir> -o /tmp/codex-b-out.txt 2>/tmp/codex-b-err.txt &
pid_b=$!

wait "$pid_a"; rc_a=$?
wait "$pid_b"; rc_b=$?
```

Notes:

- `-o` writes the final agent message when the run exits. The output file may not exist while the worker is still running.
- Do not infer failure from a missing output file before the worker exits.
- If a worker exits non-zero or produces no usable output, inspect the matching stderr file, retry once with a tighter prompt if appropriate, then fall back.
- Prefer foreground execution unless there is a clear parallel split worth the supervision cost.

## Key Flags

| Flag | Values | Notes |
|---|---|---|
| `-m / --model` | any string | From config or user request; omit when the default is acceptable |
| `-c model_reasoning_effort="VALUE"` | `low`, `medium`, `high` | From config; override when needed |
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

- `medium`: default for mapping, investigation, and most edits
- `high`: ambiguity, deep review, or complex synthesis

## Resume

```bash
codex exec resume --last --skip-git-repo-check > /tmp/codex-out.txt 2>/tmp/codex-err.txt
```
Offer that exact command if continuation is useful.
