# Workflow playbooks

Run the commands below from the installed project root. Prefix each harness subcommand with `python -I .quality/quality.pyz`. Task records live under `.quality/tasks/TASK/`. On a source checkout you can instead use `python /path/to/harness.py COMMAND --project /path/to/project`.

| Route | Choose it for | Path through the skills |
| --- | --- | --- |
| Fast | A bounded reversible fix with a direct check | Router → clarification → seal → execution → fresh verification |
| Standard (default) | New behavior or multiple connected files | Router → clarification and persistent spec → planning → independent plan check → seal → execution → verification |
| High | Changes with broad impact, sensitive data or costly recovery | Standard plus a negative scenario, a recovery procedure and review of both |
| Read-only | Explanation or exploration with no promised deliverable | Answer directly |

**Fast bug fix.** Create a task, describe a reproducible wrong output and the expected result. Add the protecting test before `seal`. Run `verify` on the broken state. Implement, run `verify` again and report which criterion changed. Run continuous-improvement if the correction warrants reuse.

**Substantive feature.** Save scope, prior behavior, constraints, examples and exclusions in `spec.md`. Put ordered implementation steps in `plan.json`. Have a human or a fresh Codex session review the exact inputs. Record a real verdict. Seal the accepted inputs. Execute, verify and retain the spec with its task ID. Reference it when a later change supersedes it. This is a persistent spec convention with no OpenSpec dependency.

**High assurance.** Include a realistic failure in `negative_case` and concrete recovery in `recovery`. Ask the reviewer to challenge both against current code. Add a criterion that exercises the negative path if it can run locally. Identify external validation the user still needs. Stop after the repair budget and report the failing evidence.

## Contract and plan

For a task created by `new timing --mode standard --objective "Format elapsed time"`, a complete contract could be:

```json
{
  "version": 1,
  "id": "timing",
  "mode": "standard",
  "objective": "Show elapsed seconds as minutes and seconds.",
  "deliverables": ["clock_label.py"],
  "criteria": [
    {"id": "format", "expect": "65 seconds displays as 01:05, including zero padding.",
     "check": {"kind": "command", "name": "clock-tests"}}
  ]
}
```

Register the named check under `commands` in `.quality/policy.json` before sealing:

```json
{"clock-tests": ["{python}", "-I", "tests/test_clock.py"]}
```

For a text artifact, use `{"kind":"text-equals","path":"label.txt","text":"01:05\n"}` or `text-contains` with a nonblank substring. Text checks accept up to 8 MiB of UTF-8, accept an optional BOM and normalize CRLF. Evidence hashes the original bytes. Use a registered streaming validator for larger text files. File paths are project-relative with forward slashes. Deliverables must be regular files. Directory delivery can be represented by its required files.

Example `plan.json`:

```json
{
  "steps": [
    {"id":"format-clock", "action":"Format the quotient and remainder with two-digit minimum widths.",
     "files":["clock_label.py"], "criteria":["format"], "verify":"Run clock-tests and inspect the 65-second case."}
  ],
  "negative_case":"Check the minute rollover with 59 and 60 seconds.",
  "recovery":"Restore the previous formatter in clock_label.py and rerun its callers' tests."
}
```

## Independent review and execution

1. Run `plan-check timing`. It checks structure, path safety and criterion coverage.
2. In a fresh Codex CLI session in the same project, use `$plan-checker Review task timing against the original request. Record your verdict and identify the actual review session.` A human reviewer may use a review artifact or ticket as the source reference. Supply the original request to that reviewer.
3. The reviewer retains the `inputs_sha256` from their initial `plan-check` and includes it with the verdict. Record their response using `review timing --inputs-sha256 DIGEST --source separate-session --by NAME --ref SESSION-ID --verdict pass --note "Actual reviewer rationale"`. A reviewer can record `changes`. Revise and review again. If independent review is pending, say so.
4. Run `seal timing`. Implement the agreed plan, then run `verify timing`. Check `evidence.json` after each run. Archive a copy before rerunning if the previous observation should be kept.
5. After a repeated failure or user correction, write a short reflection with the evidence run ID and a failing regression case.

The default standard and high routes require a review. Its input hash includes exact bytes of the contract, plan, spec and policy. Review identity is a local attestation. A separate session still requires ordinary user authorization to launch.
