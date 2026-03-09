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
references/
  claude.md               # Claude Code CLI reference and commands
  codex.md                # Codex CLI reference and commands
  copilot.md              # GitHub Copilot CLI reference and commands
  templates.md            # Delegation prompt templates by role and task type
```

## Usage

This skill is loaded by an AI coding assistant that supports skill files (e.g. Claude Code). Once loaded, the assistant acts as orchestrator and uses the templates and model references to delegate work.

Trigger conditions:
- The user wants to delegate a task to an external AI agent
- The user mentions `claude`, `codex`, or `copilot` explicitly
- The user asks to "use another model"
- The user wants to spread work across multiple models

## Roles

| Role | Purpose | Hard limits |
|---|---|---|
| **Orchestrator** | Human-facing controller: planning, delegation, verification, synthesis | Only the assistant directly handling the user |
| **Senior worker** | Deep technical work: multi-file edits, refactors, complex logic, plan review | No re-delegation |
| **Junior worker** | Tactical work: surgical edits, approved git ops, low-stakes research | Escalate when scope or importance grows |

## Adding a Model

1. Add one row to the model table in `SKILL.md`
2. Add `references/<model>.md` following the structure of the existing model files
3. Only update `references/templates.md` if the new model requires a new role, prompt shape, or output-extraction pattern
