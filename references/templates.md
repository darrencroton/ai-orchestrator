# Delegation Prompt Templates

Use these templates to define the work by role. Fill in all fields. Remove placeholder text. Include only task-relevant context, but include enough that the worker does not need unstated background.

Templates define prompt shape only. To run a template, choose a model from [SKILL.md](../SKILL.md), then use that model's reference file for the actual CLI invocation.

## Role Ranges

- **Senior worker**: multi-file changes, refactors, complex logic, plan review, deep debugging
- **Junior worker**: surgical edits, approved git/GitHub operations, low-stakes web research, codebase mapping, non-critical summarising

## Output Patterns

**Confirmation tasks** (make a change, run an operation):
Append to prompt: `"When done, print RESULT: followed by 1-2 sentences of what was done."`
Extract: `grep -A4 "^RESULT:" /tmp/<tool>-out.txt || tail -10 /tmp/<tool>-out.txt`

**Information tasks** (find, analyse, research):
Use structured section headers in the prompt (e.g. `## FINDINGS`, `## ALTERNATIVES`).
Default extract: `sed -n '/^## [Ff]indings/,$p' /tmp/<tool>-out.txt | sed '/^<task_complete>/q'`
If you requested multiple sections, extract only those sections instead of reading the whole file.

Both patterns always capture output to `/tmp/<tool>-out.txt`. Use redirection or a tool-specific output flag as appropriate.
Inspect only the requested `RESULT:` block or structured sections, not the raw transcript.

## Worker Mode

This line is pre-baked at the top of every template below:

```
WORKER MODE: Delegated worker only — no ai-orchestrator skill, no re-delegation, complete locally, report blockers.
```

---

## SENIOR WORKER — Complex Edit

```
WORKER MODE: Delegated worker only — no ai-orchestrator skill, no re-delegation, complete locally, report blockers.

TASK: <imperative verb + specific description>

FILES:
  - <exact/path/to/file1.ext>
  - <exact/path/to/file2.ext>

CONTEXT:
<Paste relevant code or describe current state. Include function signatures,
data structures, or key logic that bears on the task.>

CONSTRAINTS:
  - <What must not change>
  - <Coding style / conventions>

EXPECTED OUTPUT: <What done looks like>

When done, print RESULT: followed by 1-2 sentences of what was done.
```

---

## SENIOR WORKER — Plan Review

```
WORKER MODE: Delegated worker only — no ai-orchestrator skill, no re-delegation, complete locally, report blockers.

REVIEW THIS PLAN AND FIND PROBLEMS:
---
<Paste the orchestrator's full plan, approach, or proposed code>
---

CODEBASE CONTEXT:
<Relevant file paths, function names, data structures, or constraints.>

RETURN: Numbered list of concerns, risks, missed edge cases, logic errors,
or better approaches. Do not implement anything. Analysis only.

When done, print RESULT: followed by 1 sentence on the number and severity of issues found.
```

---

## JUNIOR WORKER — Surgical Edit

```
WORKER MODE: Delegated worker only — no ai-orchestrator skill, no re-delegation, complete locally, report blockers.

TASK: <Single specific change — one sentence, imperative>

FILE: <exact/path/to/file.ext>

LOCATION: <Function name, class name, or line range>

CURRENT CODE:
<Paste exact current code>

CHANGE TO:
<Paste exact replacement or describe precisely>

CONSTRAINTS:
  - Do not touch any other files
  - Do not refactor surrounding code

VERIFY: <Test command to run after change, if applicable>

When done, print RESULT: followed by 1 sentence of what was changed.
```

---

## JUNIOR WORKER — Git / GitHub Operation

```
WORKER MODE: Delegated worker only — no ai-orchestrator skill, no re-delegation, complete locally, report blockers.

TASK: <Specific git or GitHub operation>

REPO: <Local path or GitHub owner/repo>

CONTEXT:
<What was done, what this commit/PR represents, relevant branch names,
issue numbers, or anything needed to write a good message.>

USER APPROVAL: <explicitly approved / not approved>

REQUIREMENTS:
  - <Commit message format, PR title, labels, etc.>
  - <Constraints — e.g. do not push to main>

APPROVAL GATE:
If approval is not explicit, stop after preparing the message/body/command summary.
Do not commit, push, merge, open a PR, or modify remote state.

When done, print RESULT: followed by 1-2 sentences of what was done.
```

---

## JUNIOR WORKER — Low-Stakes Web Research

```
WORKER MODE: Delegated worker only — no ai-orchestrator skill, no re-delegation, complete locally, report blockers.

RESEARCH: <Specific question or topic>

FIND:
  - <Exactly what is needed>
  - <Any secondary questions>

SOURCE PREFERENCE: <official docs / recent articles / GitHub issues / papers>

## FINDINGS
<Bullet list only. Include source URLs and dates where relevant. Call out uncertainty.>

IMPORTANT:
  - Low-stakes task only
  - Do not edit any files
  - Do not make correctness-critical decisions
  - If the task becomes important or high-risk, stop and say so
```

---

## JUNIOR WORKER — Low-Stakes Codebase Mapping

```
WORKER MODE: Delegated worker only — no ai-orchestrator skill, no re-delegation, complete locally, report blockers.

TASK: <Low-stakes codebase-mapping question>

SCOPE:
  - <Directories, files, or symbols to inspect>
  - <What to ignore, if relevant>

RETURN:
## FINDINGS
<Bullet list only. Include file paths and symbols where relevant. Call out uncertainty.>

IMPORTANT:
  - Do not edit any files
  - Do not make correctness-critical decisions
  - If the task becomes important or high-risk, stop and say so
```

---

## Escalation Rules

| Condition | Action |
|---|---|
| Junior worker task touches > 1 file | Escalate to a senior worker |
| Junior worker task requires understanding > ~100 lines | Escalate to a senior worker |
| Junior worker research or mapping becomes correctness-critical | Keep it with the orchestrator or escalate to a senior worker |
| Git/GitHub action lacks explicit user approval | Do not execute the state-changing action; draft only |
| Any tool given an ambiguous prompt | Clarify with user before delegating |
