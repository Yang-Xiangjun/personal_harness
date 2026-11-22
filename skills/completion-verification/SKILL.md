---
name: completion-verification
description: Run fresh harness checks on final deliverables and report evidence, failed criteria and verification limits.
---

# Completion verification

From the installed project root run `verify TASK` after the final edit using the interpreter and command in `.quality/CODEX.md`. Read the exit code, top-level status, each criterion, deliverable hashes and issues in the newly written `evidence.json`. Trace the observed output to the request. A command's zero exit code supports only the assertions the command actually ran.

Report the artifact paths, criterion IDs and outcomes, evidence path and material limits. If a result fails, distinguish implementation failure, protected-input drift, unavailable verification and an incomplete request. Repair within scope and rerun, or tell the user exactly what remains. A cached report or quiet Stop hook cannot establish freshness.
