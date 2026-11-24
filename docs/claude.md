# Claude Code adapter

From the harness checkout, run `python harness.py install --project PATH --client claude` for Claude Code, or select `--client both` to include Codex. Use `--dry-run` to preview. The installer preserves existing user settings, project instructions and edited skills. For an older harness installation, preview and resolve any shared-file version conflicts before installing the second adapter.

This version reserves `.claude` for client metadata. If an older sealed task names a deliverable or protected test inside that directory, finish it with the previously installed verifier before upgrading. Keep new acceptance inputs in the project's normal source and test directories.

Open Claude Code in the target project. Use `/task-router` for intake or `/task-execution` to resume a sealed task. The installed `.quality/CLAUDE.md` shows the Python command for Bash and, on Windows, PowerShell. The same `.quality/tasks/TASK/` directory stays valid across clients. A reviewer in another genuine session can check a plan and return the digest to its author.

## Skills and project instructions

Project installation writes `.claude/skills/<name>/SKILL.md`. With `--user-skills`, skills go under `~/.claude/skills` or the selected `CLAUDE_CONFIG_DIR/skills`. The validator and task records remain project-local. In a fresh Claude session, use `/context` to inspect skill and memory discovery. [Claude Code skills](https://code.claude.com/docs/en/skills) · [Configuration scopes](https://code.claude.com/docs/en/settings)

The generated project `CLAUDE.md` imports `@.quality/CLAUDE.md`. It also imports regular project instruction files at `AGENTS.md` and `.claude/AGENTS.md` when present, because creating a Claude instruction file can suppress Claude's automatic discovery of those files. If your team relies on instructions above the project directory, check their visibility with `/context` after installation. [Claude Code instruction loading](https://code.claude.com/docs/en/memory#when-claude-code-reads-agentsmd)

If you already maintain `CLAUDE.md` or `.claude/CLAUDE.md`, the installer preserves it and prints the relative import you can add. When working on the harness source itself, its root `CLAUDE.md` imports the contributor instructions in `AGENTS.md`. [Claude Code project instructions and imports](https://code.claude.com/docs/en/memory)

## Optional Stop hook

Add `--hook` to the install command. If the `claude` executable identifies itself as Claude Code, the installer prepares a command hook in `.claude/settings.local.json`. This machine-local registration uses the installing Python and the shared script in the source checkout. Keep both at their registered paths. Windows uses the PowerShell hook shell. Other systems use POSIX shell quoting. Check the hook in a trusted project with `/hooks`. Its availability depends on the client's version, project trust and managed settings. [Claude Code hooks](https://code.claude.com/docs/en/hooks)

An existing settings file is preserved. If its contents differ, the installer writes `.quality/claude-stop-hook.fragment.json`. To enable it, review and merge its Stop group into the existing `hooks.Stop` array. An unavailable client leaves the explicit verifier usable.

Run `watch TASK` using the installed harness command inside the Claude session you want to watch. It reads `CLAUDE_CODE_SESSION_ID`. If the shell also inherited a different Codex session ID, specify the intended ID with `--session` for both `watch` and `unwatch`. In Claude's Bash tool you can use `watch TASK --session "$CLAUDE_CODE_SESSION_ID"`. [Session environment variables](https://code.claude.com/docs/en/env-vars)

The handler receives event JSON on stdin. For a watched task with missing, running or failed evidence, it returns one `decision: "block"` with a reason. Claude can take another turn. A repeated Stop with `stop_hook_active` passes through. Invalid state produces a fail-open message. A saved pass is historical, so run `verify TASK` after the final edit. The hook only reads local status.
