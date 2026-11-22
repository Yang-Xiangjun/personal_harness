---
name: requirements-clarification
description: Turn a routed task into explicit deliverables, measurable criteria and a persistent specification when the route requires one.
---

# Requirements clarification

Read the request, existing behavior and fixtures. Name the output files in `contract.json`. Give each criterion a stable ID, an observable expectation and a supported check. Cover a meaningful failure or boundary case where it can change the result. See the contract example in `.quality/WORKFLOW.md`.

Resolve ambiguity from the repository first. Ask one focused question when different answers would change what the user receives. Record reversible assumptions and the agreed exclusions. For a substantive change, put current behavior, desired behavior, constraints and an input/output scenario in the task's `spec.md`. Separate user intent from implementation choices.

A command check references a project-owned policy entry. Agree on the test and command before sealing. A visual or subjective requirement needs human evidence or an explicit outstanding limitation. Never substitute file existence for that assessment.
