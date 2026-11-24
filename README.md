# Personal AI quality harness for Codex CLI and Claude Code

Seven skills guide a task from intake to delivery in either client. One local Python CLI checks the deliverables against a frozen baseline and writes fresh evidence. Python 3.10+ and its standard library are sufficient. Install whichever interactive client you use.

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

To try the same task in Claude Code, choose a new directory and start Claude there:

```sh
python examples/demo.py --project ../clock-claude-task --client claude --leave-broken
cd ../clock-claude-task
claude
```

Enter `/task-execution Finish the sealed clock-label task and run completion-verification.` Use `--client both` to work on the same task from either client.

## Install into an existing project

Run these from the harness source directory. Replace the final argument with the path to the existing project. Quote paths containing spaces.

```sh
python harness.py install --dry-run --project "../my-project"
python harness.py install --project "../my-project"
cd "../my-project"
codex
```

Start a new Codex CLI session and try **$task-router Add an elapsed-time label to the status command.** The router selects the amount of planning. Use `/skills` to inspect discovery where available, or invoke a skill explicitly by name.

For Claude Code, run `python harness.py install --client claude --project "../my-project"` from the checkout, open `claude` in that project and use `/task-router`. Choose `--client both` for both integrations in one installation. Omitting `--client` selects Codex. [Claude Code setup and optional hook](docs/claude.md)

| What gets installed | Destination and behavior |
| --- | --- |
| Seven skills | Codex reads `.agents/skills/<name>/SKILL.md`. Claude reads `.claude/skills/<name>/SKILL.md`. Add `--user-skills` for the selected client's personal skill directory. |
| Validator and playbooks | Shared `.quality/quality.pyz`, workflow, policy and per-skill source map in `.quality/REFERENCES.md`. Each client gets instructions with its working Python command. |
| Project settings | Seeds `.quality/policy.json` on first install. Edit the project copy to register trusted test commands. |
| Codex guidance | Creates project `AGENTS.md` if absent. The installed guidance includes the Python executable used during setup. For an existing active instructions file, add **Read .quality/CODEX.md for this project's quality workflow.** Explicit skill invocation also works. |
| Claude guidance | Creates a project `CLAUDE.md` importing the local guide and existing project `AGENTS.md` instructions. If a team Claude file already exists at the root or in `.claude/`, the installer prints the import to add there. |
| Optional reminder | Add `--hook` to prepare the selected client's Stop registration. Review it in `/hooks`, then use `watch TASK` in the intended session. [Codex hook](docs/codex.md) · [Claude hook](docs/claude.md) |

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
- [Claude Code adapter and official documentation](docs/claude.md)
- [Design lineage](docs/references.md)
- [MVP acceptance results and saved evidence](docs/acceptance.md)

To repeat native discovery, run `python tests/native_discovery.py` with Git and Codex CLI or `python tests/claude_discovery.py` with Claude Code. Both use temporary projects and profiles. The Claude check reads the client's local `/context` report for all seven skills, the imported command guide and pre-existing team instructions.

## Known limits and recovery

- The skills guide both clients. Routing, meaningful requirements, reviewer identity, semantic judgment and the repair budget rely on the people or sessions using the workflow. The CLI validates structure and recorded evidence. A passing check is only as strong as its assertions.
- Frozen records and test hashes catch changes under normal use. Someone with workspace write access can replace any local baseline, verifier or report. Use a separately controlled verifier or CI to establish a stronger trust boundary.
- Each registered command runs trusted project code as the current user. The timeout covers the immediate process. Subprocess trees, disk output volume, environment secrets and network access require host controls. Optional output tails can include sensitive content. The independent reviewer should inspect the selected commands.
- The Stop hook is an opt-in reminder. Disabled, untrusted or unsupported hooks leave the CLI workflow usable. A quiet hook does not establish a fresh pass.
- Workflows support regular files and the three documented check types. Subjective outcomes need separate human review. Record outstanding human checks before claiming the user's full request is satisfied.
- Operations in one project serialize on `.quality/busy.lock`. After an abrupt termination, confirm the recorded process and its checks have stopped before removing that lock. Rerun verification after recovery. Repeating installation repairs missing files. Resolve any partially written or conflicting file through the preview.
- Commit the spec, contract, plan, review, seal, project policy and tests when they are part of the project's maintained history. Generated evidence can contain local paths or test output. Review it before sharing. No hosted service, API key, agent daemon or external orchestration dependency is used by the validator.
