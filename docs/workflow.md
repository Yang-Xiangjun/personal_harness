# Workflow playbooks

Run the commands below from the installed project root. Use the interpreter in your client guide (`.quality/CODEX.md` or `.quality/CLAUDE.md`) with `-I .quality/quality.pyz`. Both clients use the task records in `.quality/tasks/TASK/`. On a source checkout you can use `python /path/to/harness.py COMMAND --project /path/to/project`. The upstream source map is installed in `.quality/REFERENCES.md`.

| Route | Choose it for | Path through the skills |
| --- | --- | --- |
| Fast | A bounded reversible fix with a direct check | Router → clarification → seal → execution → fresh verification |
| Standard (default) | New behavior or multiple connected files | Router → clarification and persistent spec → planning → independent plan check → seal → execution → verification |
| High | Changes with broad impact, sensitive data or costly recovery | Standard plus a negative scenario, a recovery procedure and review of both |
| Read-only | Explanation or exploration with no promised deliverable | Answer directly |

**Fast bug fix.** Create a task, describe a reproducible wrong output and the expected result. Add the protecting test before `seal`. Run `verify` on the broken state. Implement, run `verify` again and report which criterion changed. Run continuous-improvement if the correction warrants reuse.

**Substantive feature.** Save scope, prior behavior, constraints, examples and exclusions in `spec.md`. Put ordered implementation steps in `plan.json`. Have a human or a fresh session in either client review the exact inputs. Record a real verdict. Seal the accepted inputs. Execute, verify and retain the spec with its task ID. Reference it when a later change supersedes it. This is a persistent spec convention with no OpenSpec dependency.

**High assurance.** Include a realistic failure in `negative_case` and concrete recovery in `recovery`. Ask the reviewer to challenge both against current code. Add a criterion that exercises the negative path if it can run locally. Identify external validation the user still needs. Stop after the repair budget and report the failing evidence.

## Contract and plan

For a task created by `new timing --mode standard --objective "Format elapsed time"`, the following spec excerpt makes an hour-boundary decision explicit.

> **Changed behavior.** The formatter accepts nonnegative whole seconds and returns elapsed minutes and seconds. When it receives 65, it returns `01:05`. When it receives 3,600, it returns `60:00`. Fractional inputs are outside this change.

Capture those observations in the contract:

```json
{
  "version": 1,
  "id": "timing",
  "mode": "standard",
  "objective": "Show elapsed seconds as minutes and seconds.",
  "deliverables": ["clock_label.py"],
  "criteria": [
    {"id": "format", "expect": "65 seconds displays as 01:05, including zero padding.",
     "check": {"kind": "command", "name": "format-example"}},
    {"id": "boundaries", "expect": "Zero, minute rollover and the first hour retain total elapsed minutes.",
     "check": {"kind": "command", "name": "clock-boundaries"}}
  ]
}
```

Register both checks under `commands` in `.quality/policy.json` before sealing. These names target the two actual test methods in the clock example.

```json
{
  "format-example": ["{python}", "-I", "tests/test_clock.py", "ClockLabelTests.test_minutes_and_seconds"],
  "clock-boundaries": ["{python}", "-I", "tests/test_clock.py", "ClockLabelTests.test_boundaries"]
}
```

For a text artifact, use `{"kind":"text-equals","path":"label.txt","text":"01:05\n"}` or `text-contains` with a nonblank substring. Text checks accept up to 8 MiB of UTF-8, accept an optional BOM and normalize CRLF. Evidence hashes the original bytes. Use a registered streaming validator for larger text files. File paths are project-relative with forward slashes. Deliverables must be regular files. Directory delivery can be represented by its required files.

Example `plan.json`:

```json
{
  "steps": [
    {"id":"format-clock", "action":"Format the quotient and remainder with two-digit minimum widths.",
     "files":["clock_label.py"], "criteria":["format","boundaries"],
     "verify":"Run format-example and clock-boundaries. Confirm 65 gives 01:05 and 3600 gives 60:00."}
  ],
  "negative_case":"Check the minute rollover with 59 and 60 seconds.",
  "recovery":"Restore the previous formatter in clock_label.py and rerun its callers' tests."
}
```

## Independent review and execution

1. Run `plan-check timing`. It checks structure, path safety and criterion coverage.
2. In a fresh session in the same project, invoke `$plan-checker` in Codex or `/plan-checker` in Claude Code. Supply the original request and ask the reviewer to check task `timing`, record their verdict and identify the actual review session. A human reviewer may use a review artifact or ticket as the source reference.
3. The reviewer retains the `inputs_sha256` from their initial `plan-check` and includes it with the verdict. Record their response using `review timing --inputs-sha256 DIGEST --source separate-session --by NAME --ref SESSION-ID --verdict pass --note "Actual reviewer rationale"`. A reviewer can record `changes`. Revise and review again. If independent review is pending, say so.
4. Run `seal timing`. Implement the agreed plan, then run `verify timing`. Check `evidence.json` after each run. Archive a copy before rerunning if the previous observation should be kept.
5. After a repeated failure or user correction, write a short reflection with the evidence run ID and a failing regression case.

The default standard and high routes require a review. Its input hash includes exact bytes of the contract, plan, spec and policy. Review identity is a local attestation. A separate session still requires ordinary user authorization to launch.

**Example review finding.** A plan that tests only 65 seconds could accept a formatter that wraps minutes back to zero at an hour. The reviewer can name the `boundaries` criterion, the passing-but-incorrect behavior, and the missing 3,600-second assertion in a `changes` verdict. In the example above, the boundary check already exercises that case. Inspect the test before deciding the verdict.
