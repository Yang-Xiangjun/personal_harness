# Design references

The harness ships original instructions for Codex CLI and Claude Code and a shared local Python validator. The sources below identify the upstream workflows used to design each skill. Running the validator requires no network access.

| Installed skill | Upstream reference | Adaptation in this harness |
| --- | --- | --- |
| `task-router` | [Cursor Pstack · poteto-mode](https://github.com/cursor/plugins/blob/main/pstack/skills/poteto-mode/SKILL.md) | Select a playbook from cues in the request. Here the cost of a mistake and the evidence needed determine the route. Existing task files determine where to resume. |
| `requirements-clarification` | [Pstack · sharpen](https://github.com/cursor/plugins/blob/main/pstack/skills/sharpen/SKILL.md), [gstack · spec](https://github.com/garrytan/gstack/blob/main/spec/SKILL.md), [OpenSpec · change-spec template](https://github.com/Fission-AI/OpenSpec/blob/main/schemas/spec-driven/templates/spec.md) | Inspect original evidence, settle technical unknowns locally, and give changed behavior a concrete scenario. Keep the scenario in a task spec and its observable check in the contract. |
| `task-planning` | [Superpowers · writing-plans](https://github.com/obra/superpowers/blob/main/skills/writing-plans/SKILL.md) | Identify paths, dependencies, and expected test results in small executable steps. The author's pass checks names and spec coverage before independent review. |
| `plan-checker` | [GSD · gsd-plan-checker agent](https://github.com/open-gsd/gsd-core/blob/main/agents/gsd-plan-checker.md), [gstack · plan-eng-review](https://github.com/garrytan/gstack/blob/main/plan-eng-review/SKILL.md) | Work backward from the outcome. Check the caller, dependency order, failure paths and discriminating assertions. Record the real reviewer's verdict against a digest of the reviewed inputs. |
| `task-execution` | [Superpowers · executing-plans](https://github.com/obra/superpowers/blob/main/skills/executing-plans/SKILL.md) | Compare each step's observed result with the plan. Diagnose a wrong implementation, an obsolete plan assumption, or a blocked dependency before choosing the next action. |
| `completion-verification` | [Superpowers · verification-before-completion](https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md) | Match each completion claim to a fresh observation at the correct interface. The CLI records outcomes, hashes and integrity issues. The skill interprets their scope. |
| `continuous-improvement` | [Pstack · reflect](https://github.com/cursor/plugins/blob/main/pstack/skills/reflect/SKILL.md), [Pstack · correct](https://github.com/cursor/plugins/blob/main/pstack/skills/correct/SKILL.md) | Decide whether a lesson belongs in a design constraint, a regression check, a skill trigger or its instructions. Verify a mechanical correction on the original failure and the repaired behavior. |

## Client adapters and local settings

| Integration | Native reference | Local behavior |
| --- | --- | --- |
| Codex skills and project guidance | [Codex skills](https://developers.openai.com/codex/skills), [Codex AGENTS.md](https://developers.openai.com/codex/guides/agents-md) | Install seven `SKILL.md` files in project or user scope. The project instructions point to the route, task directory and working Python command. The installer preserves collisions. |
| Codex Stop hook | [Codex hook events and output](https://developers.openai.com/codex/hooks) | A trusted project hook can request one continuation in a watched session. Its reason is selected from fixed messages for missing, in-progress, or failed verification. Invalid report state fails open. |
| Claude skills and project instructions | [Claude Code skills](https://code.claude.com/docs/en/skills), [project memory](https://code.claude.com/docs/en/memory) | Install the same seven skills in Claude's skill directory. Project memory imports the local command guide. |
| Claude Stop hook | [Claude Code hooks](https://code.claude.com/docs/en/hooks) | Project-local settings register the same read-only reminder using Claude's command-hook format and session ID. |
| Quality policy | Project-owned `.quality/policy.json`, seeded from `quality/default-policy.json` | The three assurance modes, protected-file inventory, review binding, repair budget and command timeout are harness decisions. Each client supplies its own execution permissions. |
