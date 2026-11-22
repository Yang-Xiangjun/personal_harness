---
name: task-execution
description: Implement an agreed harness task in verified increments while preserving its sealed acceptance inputs.
---

# Task execution

Before implementation, run `seal TASK` once, after preparing acceptance tests and the required review. If resuming, inspect the existing seal and task files. Reproduce a failing criterion where appropriate. Use the ordered steps in the plan, or the contract for a fast task. Make the smallest change that satisfies each observed gap and rerun its focused check.

Keep tests, policy, review and criteria stable. When the agreed expectation genuinely changes, record the user's decision and start a successor task with its own baseline. Keep prior evidence. Use repository permissions and normal Codex approvals for external actions.

After the last edit, hand off to completion-verification. If a bounded repair fails again, use the policy's repair budget and report the remaining observation.
