# Personal quality harness for Claude Code

For a new deliverable in this project, use the task-router skill. You can invoke it explicitly as `/task-router` followed by the request. For a continuation, inspect the task in `.quality/tasks/TASK/` and resume at its current stage. Answer inspection-only questions directly.

Run harness subcommands from the installed project root.

{{HARNESS_COMMANDS}}

Read `.quality/WORKFLOW.md` for the routes and `.quality/POLICY.md` for protected inputs. Use the existing contract, plan, independent review, seal and evidence even when another client started the task. A real reviewer must supply any required independent verdict.

After the final edit run `verify TASK`. Read the new run ID, criteria and issues before reporting completion. An optional Stop reminder refers only to recorded status. Use the project's normal permissions for tools and external actions.
