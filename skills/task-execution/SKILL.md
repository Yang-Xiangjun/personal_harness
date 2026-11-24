---
name: task-execution
description: Implement a sealed harness task one verifiable step at a time, including recovery when a check or a plan assumption fails.
---

# Task execution

**Establish the starting point.** Read the contract, spec and plan together, or the contract alone on the fast route. Locate the real entry point and inspect existing work before editing. Prepare the acceptance checks and obtain any required review, then run `seal TASK` once. On a resumed task, inspect the existing seal and compare the working files and recent evidence to the remaining steps.

**Work one observable change at a time.** For a reported defect, run the focused check against the original behavior where practical. Read the failure and confirm it shows the reported symptom. An import error or missing fixture calls for a setup fix before treating that result as a baseline. Implement the step, run its planned check, and compare the observed result to the expected result. Check the public caller when the change crosses an interface.

**Use a mismatch to choose the next action.**

- If the implementation is wrong, isolate the first point where actual output diverges. Apply a focused repair and rerun the same check. Use the project's `max_repair_attempts` as the repair budget.
- If a plan assumption or sealed expectation needs revision, identify the affected step and evidence. Record the authorized decision and use a successor task for revised inputs. Keep the original seal and evidence intact.
- If a dependency, permission or product decision blocks verification, record the affected criterion and continue any independent in-scope work.

For a handoff, state the last completed step, the check actually run, its observed result, and the next open step. Run completion-verification against the final deliverables after the last edit.
