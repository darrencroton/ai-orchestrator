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

Launch all Copilot worker runs via [../scripts/worker_jobs.py](../scripts/worker_jobs.py). The commands below are the worker command payloads to pass after `worker_jobs.py start --label <label> --`. Prefer `--silent` for captured non-interactive runs.

```bash
# Non-interactive execution worker command
copilot -p "PROMPT" --allow-all-tools --autopilot --silent --add-dir <dir>

# Low-stakes web research worker command
copilot -p "PROMPT" --allow-all-tools --allow-all-urls --autopilot --silent --add-dir <dir>

# GitHub operations worker command (with MCP tools)
copilot -p "PROMPT" --allow-all-tools --add-github-mcp-toolset all --autopilot --silent --add-dir <dir>

# Resume most recent session
copilot --continue --allow-all-tools
```

Use [../scripts/worker_jobs.py](../scripts/worker_jobs.py). Let it own stdout/stderr capture, and use its extraction step rather than adding brittle post-processing. It matches `SECTION:` header lines by pattern instead of relying on one exact formatting variant. Worker labels must use `<nn>-<tool>-<subtask-slug>[-rN]`, for example `02-copilot-map-config`.
If extraction returns nothing, check the matching `<label>-err.txt` file in the run directory before retrying.

Notes:

- Follow the monitoring cadence in `SKILL.md`: let healthy workers run through their role-appropriate wait window, treat empty live captures as normal startup or analysis time, and do not probe or retry an equivalent healthy worker.

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
