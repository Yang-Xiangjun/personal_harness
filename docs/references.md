# Design lineage

The skills and playbooks here are original text. These upstream workflow ideas informed the division of responsibilities. Installation uses the files in this repository.

| Harness part | Upstream pattern | Implementation here |
| --- | --- | --- |
| task-router | Pstack poteto-mode | Classify a task by the kind of deliverable and the cost of a mistake. |
| requirements-clarification | Pstack sharpen and gstack spec | Resolve material ambiguity and commit observable expectations to a task contract. |
| task-planning | Superpowers writing-plans | Order file-level actions and associate each step with criteria and a verification outcome. |
| plan-checker | GSD plan checker and gstack plan-eng-review | Check coverage mechanically, then obtain and bind a separate review. |
| Persistent spec | OpenSpec change specifications | Keep a versionable spec beside the contract and plan. |
| task-execution and completion-verification | Superpowers executing-plans and verification-before-completion | Execute bounded steps and report newly generated verification evidence. |
| continuous-improvement | Pstack reflect and correct | Connect a specific observed failure to a regression and a future correction. |

Upstream projects: [Cursor Pstack](https://github.com/cursor/plugins/tree/main/pstack), [gstack](https://github.com/garrytan/gstack), [Superpowers](https://github.com/obra/superpowers), [GSD](https://github.com/open-gsd/gsd-core), [OpenSpec](https://github.com/Fission-AI/OpenSpec).
