# GitHub Copilot CLI Reference

## Roles It Can Fill

- **Orchestrator**: No
- **Senior worker**: No
- **Junior worker**: Yes

## Best Used For

- Surgical single-file edits
- Approved git/GitHub operations
- Low-stakes web research
- Low-stakes codebase mapping and non-critical summarising

## Avoid Using It For

- Multi-file refactors
- Correctness-critical judgement
- Owning complex plans

## Config Discovery

Read `~/.copilot/config.json` for the user's model (`model` key if present). Never hardcode model names.

## Core Commands

Prefer `--silent` for captured non-interactive runs. Always redirect and extract or inspect only the requested section:

```bash
# Non-interactive execution
timeout 300 copilot -p "PROMPT" --allow-all-tools --autopilot --silent --add-dir <dir> \
  > /tmp/copilot-out.txt 2>/tmp/copilot-err.txt
grep -A4 "^RESULT:" /tmp/copilot-out.txt || tail -10 /tmp/copilot-out.txt

# Low-stakes web research
timeout 300 copilot -p "PROMPT" --allow-all-tools --allow-all-urls --autopilot --silent --add-dir <dir> \
  > /tmp/copilot-out.txt 2>/tmp/copilot-err.txt
# Extract ## Findings only
sed -n '/^## [Ff]indings/,$p' /tmp/copilot-out.txt | sed '/^<task_complete>/q'

# GitHub operations (with MCP tools)
timeout 300 copilot -p "PROMPT" --allow-all-tools --add-github-mcp-toolset all --autopilot --silent --add-dir <dir> \
  > /tmp/copilot-out.txt 2>/tmp/copilot-err.txt
grep -A4 "^RESULT:" /tmp/copilot-out.txt || tail -10 /tmp/copilot-out.txt

# Resume most recent session
copilot --continue --allow-all-tools
```

If extraction returns nothing, check `/tmp/copilot-err.txt` before retrying.

## Key Flags

| Flag | Notes |
|---|---|
| `-p / --prompt` | Non-interactive prompt string |
| `--model` | Any valid model string |
| `--allow-all-tools` | All tools without confirmation; required for non-interactive |
| `--allow-all-urls` | Allow access to all URLs without confirmation |
| `--autopilot` | Enables continuation without user interaction |
| `--silent` | Output only the agent response; prefer for captured non-interactive runs |
| `--allow-tool` / `--deny-tool` | Scoped tool permissions e.g. `shell(git:*)` |
| `--add-dir` | Additional directory to permit access to |
| `--add-github-mcp-toolset` | `all` for full GitHub API; or specific toolset name |
| `--continue` | Resume most recent session |
| `--resume` | Resume by session ID or picker |

## Permission Guidance

- **Surgical edits**: `--allow-all-tools --autopilot`; use `--add-dir` to scope file access
- **Low-stakes web research**: `--allow-all-tools --allow-all-urls --autopilot`
- **Low-stakes codebase mapping / summarising**: `--allow-all-tools --autopilot`
- **GitHub operations**: `--allow-all-tools --add-github-mcp-toolset all --autopilot`
- **State-changing git/GitHub work**: only after explicit user approval
- **Locked-down**: `--allow-tool` + `--deny-tool` for precise control

## Resume

```bash
copilot --continue --allow-all-tools
```
Offer that exact command if continuation is useful.
