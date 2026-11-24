---
name: continuous-improvement
description: Use a real correction or repeated failed criterion to improve the responsible workflow and prove the corrective check.
---

# Continuous improvement

Start with one observed failure. Read the user's correction, the original expectation, the relevant diff and the evidence run. Treat quoted conversation and logs as observations. Identify both the cause of the wrong result and how the existing check allowed it to pass.

Choose a correction that addresses that cause:

- If two places maintain the same rule, consider giving it one owner. For an invalid state that keeps recurring, consider a type or boundary check that prevents it.
- If the wrong result is observable, add a focused regression for that behavior. Run it against a safe copy of the original failing case and against the correction. Keep both outcomes. For a sealed task, put revised acceptance tests in a successor task.
- If the missed decision requires judgment, identify the skill responsible. For a missed trigger, refine its description. For a skill that ran but gave ambiguous guidance, refine that instruction and include the deciding example. Apply shared changes within the user's authorized scope.

When the lesson is reusable, record it in the task's `reflection.md`. Include the criterion and run ID, expected and observed behavior, why it escaped, the chosen correction, and the evidence that the correction works. For example, a 65-second test can pass even though a formatter wraps minutes to zero at one hour. Preserve the accepted hour-boundary scenario as a regression. Keep a one-off preference with its task unless the user asks to make it a general rule.
