---
name: ai-orchestrator
description: Routes coding and analysis tasks to external AI CLI tools (e.g. Claude Code, Codex CLI, GitHub Copilot CLI). Use when the user wants to delegate a task to an external AI agent, mentions "claude", "codex", or "copilot" explicitly, asks to "use another model", or wants to spread work across multiple models while keeping one orchestrator responsible for quality and direction.
---

# AI Orchestrator

Only the assistant directly handling the user's request may act as the orchestrator and use this skill for delegation. Delegated workers are never orchestrators. If the current assistant is not marked as orchestrator-capable in the model table below, it must not orchestrate with this skill.

The orchestrator owns context, planning, delegation, verification, testing, and final responsibility. It should push the bulk of eligible work to workers and spend its own tokens on plan quality, context packaging, verification, testing, and synthesis. Keep work local only when delegation would materially weaken correctness, lose critical context, slow verification enough to outweigh the token savings, or when prompt construction cost exceeds the task cost itself.

## Roles

| Role | Purpose | Typical tasks | Hard limits |
|---|---|---|---|
| **Orchestrator** | Human-facing controller | Planning, context packaging, verification, testing, final synthesis | Only the assistant directly handling the user may do this |
| **Senior worker** | Deep technical worker | Multi-file edits, refactors, complex logic, plan review | Self-contained prompt only; no re-delegation; if unavailable, keep the task local |
| **Junior worker** | Tactical worker | Surgical edits, approved git/GitHub operations, low-stakes web research, codebase mapping, non-critical summarising | Escalate when scope, context depth, or importance grows; never own correctness-critical decisions |

## Available Models

| Model | Roles | Best used for | Avoid for | Reference |
|---|---|---|---|---|
| **Claude Code** | Orchestrator, Senior worker | Complex edits, long-running coding, plan review, deep debugging | Low-value tactical chores when a junior worker is available | [references/claude.md](references/claude.md) |
| **Codex CLI** | Orchestrator, Senior worker | Complex edits, refactors, plan review, deep debugging | Low-value tactical chores when a junior worker is available | [references/codex.md](references/codex.md) |
| **GitHub Copilot CLI** | Junior worker | Surgical edits, approved git/GitHub operations, low-stakes web research, codebase mapping, non-critical summarising | Multi-file refactors, correctness-critical judgement, owning complex plans | [references/copilot.md](references/copilot.md) |

## Role Selection

Choose a role first:

| Task type | Role |
|---|---|
| Multi-file edits, refactoring, complex logic | Senior worker |
| Second opinion / review of the orchestrator's plan | Senior worker (read-only) |
| Long-running agentic coding tasks | Senior worker |
| Single-file surgical edit, clear spec | Junior worker |
| Draft commit / PR / issue text | Junior worker |
| Execute an explicitly approved git or GitHub action | Junior worker |
| Low-stakes web research, documentation lookup | Junior worker |
| "Find where X happens" / execution trace / codebase map | Junior worker |
| Summarise a large codebase or long document | Junior worker, only when the output is non-critical |

## Model Selection

After choosing a role, choose a model from the table above:

1. Follow the user's explicit model preference unless it conflicts with a hard limit or approval rule.
2. The orchestrator is the current assistant, but only if that model is marked orchestrator-capable.
3. For worker roles, prefer a non-orchestrator model that is marked suitable for the role and best matches the task.
4. If no suitable worker is available, keep the task with the orchestrator rather than forcing delegation.

## Delegation Discipline

Every prompt sent to an external tool must be self-contained. Always use the role templates in [references/templates.md](references/templates.md) — do not improvise. They exist to package the right context so delegation can be the default for eligible work. Include: specific task, relevant code or file paths, constraints, approval state for any state-changing git/GitHub action, and expected output format.

Every delegated prompt must also place the receiver in worker mode: it is not the orchestrator, it must not invoke `ai-orchestrator`, and it must not re-delegate to another model. If blocked, it should report the blocker instead of bouncing the task onward.

## Workflow

Each new task requires a fresh role selection decision — do not carry forward a prior delegation choice.

1. **Preflight** — confirm the chosen CLI is installed, authenticated if needed, and allowed by user approval constraints
2. **Plan** — determine what needs doing and which role owns each piece
3. **Select role and model** — use the role matrix, model table, and any user directive
4. **Load references** — read [references/templates.md](references/templates.md) and the selected model reference
5. **Fill template** — include all context; the worker knows nothing else
6. **Run** — invoke the model using its reference file, with output capture and a bounded timeout when possible
7. **Check** — review only the extracted result or requested structured sections; if a worker fails, hangs, or returns only startup noise, do at most one targeted retry and then fall back
8. **Test** (when appropriate) — the orchestrator runs tests via shell, interprets failures, and delegates follow-up fixes only when that helps quality

## Orchestrator Summary

After orchestration, summarize each model actually used with:

- What it did
- Brief feedback on how effective it was
- A rough score out of 10
- An estimated percentage of total work

Treat scores and percentages as rough operating feedback, not objective metrics. Keep the summary short and useful.

## Adding / Removing a Model

To add another model or local LLM:

1. Add [or remove] one row to [from] the model table above.
2. Add [or delete] `references/<model>.md` following the structure of the existing model files.
3. Only change [references/templates.md](references/templates.md) if the new model requires a new role, prompt shape, or output-extraction pattern.
