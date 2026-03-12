# AI Orchestrator

A skill for AI coding assistants (Claude Code, Codex CLI, GitHub Copilot CLI) that turns the current assistant into an **orchestrator** — routing coding and analysis work to external AI CLI tools while retaining ownership of planning, quality, and final synthesis.

## Purpose

The orchestrator delegates the bulk of eligible work to worker models, spending its own tokens on plan quality, context packaging, verification, and synthesis rather than execution. This distributes load across models, reduces context pressure on the orchestrator, and lets each tool do what it does best.

## Supported Tools

| Tool | Role | Best for |
|---|---|---|
| **Claude Code** (`claude`) | Orchestrator, Senior worker | Complex edits, refactors, deep debugging, plan review |
| **Codex CLI** (`codex`) | Orchestrator, Senior worker | Complex edits, refactors, deep debugging, plan review |
| **GitHub Copilot CLI** (`copilot`) | Junior worker | Surgical edits, git/GitHub ops, low-stakes research, codebase mapping |

## Structure

```
SKILL.md                  # Main skill definition, roles, workflow, model table
ai-reminder               # tmux reminder helper for Codex/Claude sessions
scripts/
  worker_jobs.py          # tracked worker launcher/status/extract helper
references/
  claude.md               # Claude Code CLI reference and commands
  codex.md                # Codex CLI reference and commands
  copilot.md              # GitHub Copilot CLI reference and commands
  templates.md            # Delegation prompt templates by role and task type
```

## Usage

This skill is loaded by an AI coding assistant that supports skill files (e.g. Claude Code). Once loaded, the assistant acts as orchestrator and uses the templates and model references to delegate work.

Operating conventions:
- Start with a short execution checklist and keep it updated through the run
- Use self-contained worker prompts with absolute paths when practical
- For analysis tasks, ask workers to return `SECTION:` markers plus `path:line` evidence
- Use `scripts/worker_jobs.py` for worker launches
- Use worker labels in lowercase kebab-case: `<nn>-<tool>-<subtask-slug>[-rN]` so files sort cleanly within each run directory
- Read each worker's final outfile by default when it is short; inspect stderr only for failures or missing output
- While workers run, stay in the orchestrator role: monitor status, manage the checklist, and prepare synthesis or follow-up review prompts rather than duplicating the delegated investigation

Trigger conditions:
- The user wants to delegate a task to an external AI agent
- The user mentions `claude`, `codex`, or `copilot` explicitly
- The user asks to "use another model"
- The user wants to spread work across multiple models

## Optional Helper

`ai-reminder` is a small companion script for long-running Codex or Claude sessions. The skill itself works without it, but on long coding tasks an orchestrator can drift and stop delegating as consistently as the workflow intends. Running `ai-reminder` alongside the session provides a periodic nudge back toward the current task, plan, and delegation discipline.

Typical usage:
- `ai-reminder start --tool codex`
- `ai-reminder start --tool claude --interval 120`

Ensure the script is executable before first use: `chmod +x ai-reminder`.

If you use it regularly, add a shell alias so it can be launched from whatever project you are currently working in. Run `ai-reminder --help` for the full command set and option details.

## Roles

| Role | Purpose | Hard limits |
|---|---|---|
| **Orchestrator** | Human-facing controller: planning, delegation, verification, synthesis | Only the assistant directly handling the user |
| **Senior worker** | Deep technical work: multi-file edits, refactors, complex logic, plan review | No re-delegation |
| **Junior worker** | Tactical work: surgical edits, approved git ops, low-stakes research | Escalate when scope or importance grows |

## Adding (Removing) a Model

1. Add a new row to the model table in `SKILL.md` (or remove the relevant row)
2. Add `references/<model>.md` following the structure of the existing model files (or remove the relevant file)
3. Only update `references/templates.md` if the new model requires a new role, prompt shape, or output-extraction pattern
