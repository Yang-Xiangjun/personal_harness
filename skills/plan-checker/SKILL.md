---
name: plan-checker
description: Independently evaluate a proposed harness plan, identify coverage gaps and record a review against the current plan inputs.
---

# Plan checker

Act as reviewer only when you are a separate review session or a human supplied a real review. The author can run the structural check and prepare a handoff. Never invent reviewer identity, findings or independence.

Read the request, contract, spec, plan and policy. Trace each criterion to a step and a discriminating check. Look for an implementation that could pass the checks while violating the user's request. Examine ordering, test authority, compatibility and recovery. Return a verdict, one concrete reason, and specific changes for any blocking gap.

Run `plan-check TASK` before examining the files and retain its `inputs_sha256`. Include that digest in the review handoff. Record the verdict with `review TASK --inputs-sha256 DIGEST --source human|separate-session --by NAME --ref REFERENCE --verdict pass|changes --note FINDINGS` (choose one value per option). A changed input makes that review stale. If a separate review is unavailable, report structural results and leave the review pending.
