---
name: requirements-clarification
description: Convert a routed request into observable acceptance criteria and, for substantive changes, a scenario-based specification.
---

# Requirements clarification

1. **Find the evidence.** Inspect the relevant entry point, a real sample or fixture, and the behavior today. Describe the smallest change that would serve the user. Record any constraints, consumers, and explicit exclusions that affect acceptance.
2. **Resolve a consequential ambiguity.** Use a small reversible observation or experiment when the repository can answer the question. When a product choice remains, give the user the concrete alternatives and how the result would differ. State reversible assumptions where work can proceed.
3. **Write the contract.** In `contract.json`, name the deliverable files. Give each criterion a stable ID, a user-observable expectation, and a check that could distinguish success from a plausible wrong result. Use `text-equals` for exact text, `text-contains` for an agreed fragment, or `command` for behavior tested by a reviewed command in project policy. Keep subjective or external acceptance outstanding until a person or external system supplies evidence.
4. **Describe the change.** When the route requires `spec.md`, identify the behavior being added, changed, or removed. Write a scenario with an input or event and the expected result. Include a boundary case when it changes the interpretation. Keep the spec with the task so a later revision can refer to the original decision.

For example, "show minutes" leaves the hour boundary open. Specifying that 3,600 seconds displays as `60:00` resolves a choice that a single 65-second example cannot settle. Use the product's actual decision and link it to the relevant criterion. Hand the contract, spec and remaining questions to planning, or to execution for a fast task.
