---
name: plan-checker
description: Review the feasibility and coverage of a task plan independently, and bind a real verdict to the exact reviewed inputs.
---

# Plan checker

The author may run the structural check and prepare the handoff. A human reviewer or a separate review session supplies the independent verdict. If unavailable, report the review as pending. Use the original request as the reviewer's starting point.

Run `plan-check TASK` before examining the proposed solution. If it fails, return the structural error to the planner. Once it passes, retain the returned `inputs_sha256` and read the contract, spec, plan, policy and actual check definitions. Apply these questions to the parts of the plan they affect.

| Review question | Evidence to inspect |
| --- | --- |
| Would the plan deliver each promised result? | Follow each user scenario through its criterion ID, implementing step and check. Identify omitted behavior even if every listed ID is covered. |
| Would the user reach the implementation? | Follow a real caller across the affected interface. Identify a step that creates a component but leaves the existing path disconnected. |
| Can the steps run in the stated order? | Check that data, interfaces and fixtures exist before use. Inspect shared writes, compatibility and recovery where the change introduces them. |
| Could a wrong implementation still pass? | Try a specific counterexample against the assertion. Inspect which test the registered command runs, and whether it exercises the promised interface. For high assurance challenge the negative case and recovery procedure. |

Return `changes` for a blocking gap. Name the criterion or step, a concrete failure the current plan permits, and the smallest amendment that would resolve it. For `pass`, give the reason the evidence covers the goal and any residual limitation. For example, if a formatter unit test can pass while a status command still calls the old function, request a caller-level check when the status command is the deliverable.

Record the actual verdict with `review TASK --inputs-sha256 DIGEST --source SOURCE --by NAME --ref REFERENCE --verdict VERDICT --note FINDINGS`. Use `human` or `separate-session` for the source. If the digest is stale, review the revised inputs before recording another verdict.
