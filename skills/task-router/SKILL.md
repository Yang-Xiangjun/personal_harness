---
name: task-router
description: Select a quality-harness workflow for a new delivery request, or resume the right stage of an existing task.
---

# Task router

Start from the requested outcome. Identify who will use it, where they will see it, and one observation that would show it works. For an explanation or code walkthrough, answer directly. For a plan-only request, hand off the plan at the requested review stage and stop there.

## Route a new deliverable

| Signal in the request or repository | Route and first move |
| --- | --- |
| Local, reversible change with a direct check | **Fast.** Capture the original symptom and the observable correction. |
| New behavior, a changed interface, or several components that must work together | **Standard.** Trace a caller first. Create a persistent spec and a plan for independent review. |
| Costly rollback, a migration, or a failure that could affect many users | **High.** Identify a realistic failure and a recovery procedure for the reviewer to challenge. |

Honor an explicit mode. Otherwise explain the choice with one fact from the task. A one-line edit to a shared data format can warrant high assurance. Use the command in your installed project guide (`.quality/CODEX.md` or `.quality/CLAUDE.md`) to run `new TASK --mode MODE --objective "..."`. Hand the objective, route reason and evidence source to requirements-clarification. The project's `.quality/policy.json` defines which artifacts each route requires.

## Resume a task

Open its directory under `.quality/tasks/`. An incomplete contract goes to clarification. A plan awaiting review goes to plan-checker. A sealed task goes to execution or, if the deliverables are ready, completion-verification. Reuse the task ID while its agreed scope holds. If new evidence changes that scope after sealing, identify the change before creating a successor. If project guidance is missing, explain how to install the harness before making verification claims.
