# Personal AI quality harness for Codex CLI

Use Codex as you normally would. Seven native skills guide a task from intake to delivery, and a small local Python CLI checks what was actually produced. A verified task has measurable criteria, a frozen baseline and a fresh evidence report. Python 3.10+ and its standard library are sufficient. Install Codex CLI separately for the interactive workflow.

## Quickstart

From this source directory, run the regression suite and the working example. On systems where Python is named `python3`, use that name in the commands.

```sh
python -m unittest discover -s tests -v
python examples/demo.py --project ../clock-harness-demo
```

The demo needs a **new** directory. It installs the integration, runs two checks against a broken formatter, saves that failure, repairs the formatter and runs both checks again. Read `../clock-harness-demo/.quality/tasks/clock-label/evidence.json` and `baseline-failure.json` beside it.

To have Codex do the repair itself, prepare another directory:

```sh
python examples/demo.py --project ../clock-codex-task --leave-broken
cd ../clock-codex-task
codex
```

In Codex, ask: **Use $task-execution to finish the sealed clock-label task. Run $completion-verification and show which checks passed.** The example's success criterion includes the minute rollover and the output for 3,600 seconds.

## Install into an existing project

Run these from the harness source directory. Replace the final argument with the path to the existing project. Quote paths containing spaces.

```sh
python harness.py install --dry-run --project "../my-project"
python harness.py install --project "../my-project"
cd "../my-project"
codex
```

Start a new Codex CLI session and try **$task-router Add an elapsed-time label to the status command.** The router selects the amount of planning. Use `/skills` to inspect discovery where available, or invoke a skill explicitly by name.

| What gets installed | Destination and behavior |
| --- | --- |
| Seven skills | Project `.agents/skills/<name>/SKILL.md`. To use personal discovery instead, add `--user-skills` to the install command. Choose one scope for a given project. |
| Validator and playbooks | Self-contained `.quality/quality.pyz`, `WORKFLOW.md`, `POLICY.md` and `CODEX.md` in the project. |
| Project settings | Seeds `.quality/policy.json` on first install. Edit the project copy to register trusted test commands. |
| Codex guidance | Creates project `AGENTS.md` if absent. The installed guidance includes the Python executable used during setup. For an existing active instructions file, add **Read .quality/CODEX.md for this project's quality workflow.** Explicit skill invocation also works. |
| Optional reminder | Add `--hook` to probe native support. Review the registration in `/hooks`, then use `watch TASK` for a specific session. [Hook setup and fail-open behavior](docs/codex.md) |

Re-running the same installation creates missing files and skips identical content. Conflicting installed files produce a list before copying starts. The installer preserves existing global files and never changes `config.toml`. For an upgrade, preview first, compare conflicts, then move aside only the versions you want to replace and rerun. Existing policy and task history stay project-owned. Project-only installation is the default. Global skills can be invoked in any project where you have installed the validator and playbooks.

## Working on a real task

From the installed project:

```sh
python -I .quality/quality.pyz new timing --mode standard --objective "Format elapsed time"
```

Fill in `.quality/tasks/timing/contract.json`, `spec.md` and `plan.json`. Each criterion names a text assertion or a command registered in project policy. Prepare its tests, run `plan-check timing`, obtain the independent review, then `seal timing` before changing the implementation. Run the following after the final edit:

```sh
python -I .quality/quality.pyz verify timing
```

Exit **0** means every declared check passed, all deliverables existed and the protected snapshot matched. Exit **1** reports a failed gate or operational error. Argument errors exit **2**. Read the JSON printed and the task's `evidence.json` for the criterion, command exit status, output digest, deliverable hashes and integrity issues. A single report is point-in-time evidence. Archive selected runs when comparing revisions.

- [Route playbooks, contract examples and review commands](docs/workflow.md)
- [Canonical default configuration](quality/default-policy.json) and [quality policy](docs/policy.md)
- [Codex adapter and official documentation](docs/codex.md)
- [Design lineage](docs/references.md)
- [MVP acceptance results and saved evidence](docs/acceptance.md)

To repeat the optional native discovery check, run `python tests/native_discovery.py` from this checkout with Git and Codex CLI installed. It uses a temporary project and Codex profile and makes no model request.

## Known limits and recovery

- Skills guide Codex through tasks. Routing, meaningful requirements, reviewer identity, semantic judgment and the repair budget rely on the people or sessions using the workflow. The CLI validates structure and recorded evidence. A passing check is only as strong as its assertions.
- Frozen records and test hashes catch changes under normal use. Someone with workspace write access can replace any local baseline, verifier or report. Use a separately controlled verifier or CI to establish a stronger trust boundary.
- Each registered command runs trusted project code as the current user. The timeout covers the immediate process. Subprocess trees, disk output volume, environment secrets and network access require host controls. Optional output tails can include sensitive content. The independent reviewer should inspect the selected commands.
- The Stop hook is an opt-in reminder. Disabled, untrusted or unsupported hooks leave the CLI workflow usable. A quiet hook does not establish a fresh pass.
- Workflows support regular files and the three documented check types. Subjective outcomes need separate human review. Record outstanding human checks before claiming the user's full request is satisfied.
- Operations in one project serialize on `.quality/busy.lock`. After an abrupt termination, confirm the recorded process and its checks have stopped before removing that lock. Rerun verification after recovery. Repeating installation repairs missing files. Resolve any partially written or conflicting file through the preview.
- Commit the spec, contract, plan, review, seal, project policy and tests when they are part of the project's maintained history. Generated evidence can contain local paths or test output. Review it before sharing. No hosted service, API key, agent daemon or external orchestration dependency is used by the validator.
