---
name: task-planning
description: Turn an agreed spec into ordered file-level implementation steps with a discriminating check for each outcome.
---

# Task planning

Read the contract, spec, actual caller and existing tests. Work backward from each acceptance criterion. Locate the entry point through which the user will reach the change, the code it calls, and the test or observation that can prove the connection.

For each ordered step in `plan.json`:

- Give it a stable `id`. In `action`, identify the decision already made, the behavior to change, and any assumption needed by the next step.
- In `files`, list real project-relative paths to edit or create. Include the caller when a new component needs connecting. Use `criteria` for the contract IDs that this step advances.
- In `verify`, name the focused command or observation, its input, and the expected result. For a defect, specify the distinguishing failure on the old behavior and the expected result after the change.

For example, a step that adds a formatter cannot establish that the status command uses it. Plan the caller change and a check through the status command if that is the promised interface. Prepare acceptance tests before sealing. For high assurance fill in `negative_case` and `recovery` with the specific failure and the action that restores service or data.

**Before handing off**, read the plan as someone new to the project. Follow each dependency in order, compare file and symbol names to the repository, and replace vague instructions such as "verify formatting" with the expected observation. Run `plan-check TASK`. Give plan-checker the original request, contract, spec, plan, policy and relevant fixture paths. A passing structural check is the starting point for independent review.
