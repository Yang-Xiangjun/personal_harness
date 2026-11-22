---
name: continuous-improvement
description: Turn a user correction or repeated verification failure into a scoped improvement backed by a new regression case.
---

# Continuous improvement

Use the actual failed criterion, evidence run ID and correction. Record expected behavior, observed behavior, root cause, and the smallest rule, fixture or test that would have caught it. Save a brief `reflection.md` next to the task's evidence when there is a lesson worth keeping.

Prove the new check fails on the old behavior and passes after the fix. If the task was sealed, use a successor task for revised acceptance tests. Propose a general skill or policy change only when the observation applies across tasks. Keep the original user's wording and test evidence available for review.
