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

## Config Discovery

Read `~/.claude/settings.json` for relevant user defaults if present. If no model is configured there, omit `--model` and let Claude Code use its default. Never hardcode model names.

## Core Commands

All Claude Code output should be redirected and extracted from the capture file.

```bash
# Non-interactive execution (edit task)
claude -p "PROMPT" --permission-mode acceptEdits --output-format text --add-dir <dir> \
  > /tmp/claude-out.txt 2>/tmp/claude-err.txt
grep -A4 "^RESULT:" /tmp/claude-out.txt || sed -n '/^SECTION: /,$p' /tmp/claude-out.txt

# Read-only review / plan review
claude -p "PROMPT" --permission-mode plan --output-format text --add-dir <dir> \
  > /tmp/claude-out.txt 2>/tmp/claude-err.txt
grep -A4 "^RESULT:" /tmp/claude-out.txt || sed -n '/^SECTION: /,$p' /tmp/claude-out.txt

# Resume most recent session in the current directory
claude --continue
```

If extraction returns nothing, check `/tmp/claude-err.txt` before retrying.
For parallel workers, use unique filenames and wait on each worker pid instead of polling for output-file creation.

## Key Flags

| Flag | Notes |
|---|---|
| `-p / --print` | Non-interactive prompt string |
| `--model` | Any valid model string; omit to use the CLI default |
| `--effort` | Reasoning effort for the session: `low`, `medium`, `high` |
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
