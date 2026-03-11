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

All Claude Code output should be redirected and extracted from the capture file.

```bash
# Non-interactive execution (edit task)
claude -p "PROMPT" --permission-mode acceptEdits --output-format text --add-dir <dir> \
  > /tmp/claude-out.txt 2>/tmp/claude-err.txt
cat /tmp/claude-out.txt

# Read-only review / plan review
claude -p "PROMPT" --permission-mode plan --output-format text --add-dir <dir> \
  > /tmp/claude-out.txt 2>/tmp/claude-err.txt
cat /tmp/claude-out.txt

# Resume most recent session in the current directory
claude --continue
```

If extraction returns nothing, check `/tmp/claude-err.txt` before retrying.
For multi-worker runs, prefer [../scripts/worker_jobs.py](../scripts/worker_jobs.py) for per-run directories, status tracking, and robust extraction. When using the helper, let it own stdout/stderr capture and omit extra shell redirections from the worker command.

Notes:

- Do not launch Claude Code as a worker from inside a Claude Code orchestrator session; nested Claude sessions are blocked.
- Read the whole final outfile by default when it is short; use `worker_jobs.py extract --sections ...` only for long structured outputs.
- If a worker exits non-zero or produces no usable outfile, inspect the matching stderr file, retry once with a tighter prompt if appropriate, then fall back.
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
