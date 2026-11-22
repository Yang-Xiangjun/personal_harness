---
name: task-planning
description: Write a criterion-linked implementation plan for a standard or high assurance task before the quality baseline is sealed.
---

# Task planning

Work backwards from the contract. In ordered `plan.json` steps, record a focused change in `action`, concrete project paths in `files`, the supporting criterion IDs in `criteria`, and a result the reviewer can observe in `verify`. Put a prerequisite before the step that consumes it. Include how to see the original defect when possible.

Keep the plan small enough to execute one step at a time. Include the migration boundary or compatibility case when the change affects existing data. For high assurance, write the `negative_case` and a specific `recovery` procedure at the top level. Run `plan-check TASK`. Hand the exact contract, spec, plan, project policy and relevant repository context to plan-checker.
