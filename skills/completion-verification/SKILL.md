---
name: completion-verification
description: Verify final deliverables after the last edit and substantiate each completion claim with fresh, criterion-level evidence.
---

# Completion verification

Start with the claim the user needs to trust. Identify the observation that would justify it. For a bug fix, exercise the original input. For a user-facing command, exercise its real entry point. For a regression check, retain the earlier failing result when available. Reproduce an old failure in a disposable copy if necessary to preserve current work.

1. From the installed project root, use the interpreter in your client guide (`.quality/CODEX.md` or `.quality/CLAUDE.md`) to run `verify TASK` after the final edit. Capture its exit code and open the task's newly written `evidence.json`. Match the task and run ID to this invocation.
2. Read the top-level status and `issues` as well as each criterion. A successful command can coexist with an overall failure when a deliverable is absent or a protected input changed. A `not-run` row means a prerequisite prevented the check.
3. Check what each assertion actually covered. If one command served several criteria, identify the assertion for each one. If collection, skips, or a human inspection matter, examine the relevant runner output or record the outstanding judgment. Use `--include-output` only when the saved log excerpt is appropriate to share.
4. Report the deliverable, criterion IDs, observed outcomes, evidence path and run ID. Limit the conclusion to what was exercised. If the command failed before producing a fresh report, identify that error and any earlier report as historical.

After a repair, rerun verification. A Stop reminder reads saved status and can be quiet after an earlier pass. The fresh invocation supplies the evidence for the final answer.
