# Claude Code Reference

## Roles It Can Fill

- **Orchestrator**: Yes
- **Senior worker**: Yes
- **Junior worker**: Not preferred

## Best Used For

- Complex edits and refactors
- Long-running coding tasks
- Plan review and deep debugging

## Avoid Using It For

- Low-value tactical chores when a junior worker is available
- Launching Claude Code workers from inside a Claude Code orchestrator session

## Config Discovery

Read `~/.claude/settings.json` for relevant user defaults if present. If no model is configured there, omit `--model` and let Claude Code use its default. Never hardcode model names.

## Core Commands

Launch all Claude worker runs via [../scripts/worker_jobs.py](../scripts/worker_jobs.py). The commands below are the worker command payloads to pass after `worker_jobs.py start --label <label> --`.

```bash
# Edit task worker command
claude -p "PROMPT" --permission-mode acceptEdits --output-format text --add-dir <dir>

# Read-only review / plan review worker command
claude -p "PROMPT" --permission-mode plan --output-format text --add-dir <dir>

# Resume most recent session in the current directory
claude --continue
```

Use [../scripts/worker_jobs.py](../scripts/worker_jobs.py) for per-run directories, status tracking, and robust extraction. Let it own stdout/stderr capture and omit extra shell redirections from the worker command. Worker labels must use `<nn>-<tool>-<subtask-slug>[-rN]`, for example `01-claude-review-plan`.
If extraction returns nothing, check the matching `<label>-err.txt` file in the run directory before retrying.

Notes:

- Do not launch Claude Code as a worker from inside a Claude Code orchestrator session; nested Claude sessions are blocked.
- Read the whole final outfile by default when it is short; use `worker_jobs.py extract --sections ...` only for long structured outputs.
- Follow the monitoring cadence in `SKILL.md`: let healthy workers run through their role-appropriate wait window, treat empty live captures as normal startup/analysis time, and do not probe or retry an equivalent healthy worker.
- If a worker exits non-zero, dies unexpectedly, or completes with no usable output, inspect the matching stderr file, retry once with a tighter prompt if appropriate, then fall back.
- While workers run, keep the orchestrator on orchestration work only; do not duplicate the delegated investigation locally.

## Key Flags

| Flag | Notes |
|---|---|
| `-p / --print` | Non-interactive prompt string |
| `--model` | Any valid model string; omit to use the CLI default |
| `--permission-mode` | Use `acceptEdits` for edit tasks, `plan` for read-only review |
| `--output-format` | `text`, `json`, `stream-json` |
| `--add-dir` | Additional directory to permit tool access to |
| `--continue` | Resume the most recent session in the current directory |
| `--resume` | Resume by session ID or picker |

## Permission Guidance

- **Edit tasks**: `--permission-mode acceptEdits`
- **Read-only review**: `--permission-mode plan`
- **Unrestricted execution**: only if the user explicitly requests it

## Resume

```bash
claude --continue
```
Offer that exact command if continuation is useful.
