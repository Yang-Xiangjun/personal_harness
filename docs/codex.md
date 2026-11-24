# Codex CLI adapter

Checked on 2026-11-21 against the official local Codex docs and the installed `codex-cli 0.171.0`. Native discovery reads project `.agents/skills` and personal `~/.agents/skills`. Project instruction discovery prefers a nonempty `AGENTS.override.md` over `AGENTS.md`. A fresh CLI session is a reliable way to pick up an installation. [Skills](https://developers.openai.com/codex/skills) · [AGENTS.md](https://developers.openai.com/codex/guides/agents-md)

## Optional Stop reminder

From the source checkout run `python harness.py install --project PATH --hook`. The installer probes `codex features list`. If an enabled hook feature is unavailable, it prints **FAIL-OPEN** and leaves explicit verification available. When supported, the project adapter prepares `.codex/hooks.json`. Existing registrations are preserved. On a conflict it writes a fragment for the project owner to merge. It never changes trust settings. Inspect the generated command and the source script before trusting it. The Windows override uses native PowerShell literal paths. Unix uses POSIX shell quoting. If a custom shell is incompatible, use explicit verification.

Open the target as a trusted project, start a fresh Codex CLI session and inspect `/hooks`. Review and trust the Stop command there. Trust or admin policy can suppress a registered hook. Keep the source checkout and Python interpreter at the original paths while the hook is enabled. The explicit CLI installed in the target works independently of that checkout.

Opt in for a particular Codex session by running `python -I .quality/quality.pyz watch TASK` from it. This uses `CODEX_THREAD_ID` when present. Supply `--session ID` if needed. The marker contains the task ID and is keyed by a hash of the session ID. Use `unwatch` to detach. Other sessions are unaffected.

The handler reads JSON from stdin and writes JSON to stdout with exit code 0. Codex uses the `reason` in a `decision: "block"` response as a continuation prompt. The handler builds that prompt from fixed wording and the validated task ID. Free-form issues, test output and transcript content stay out of the prompt. [Native Stop semantics](https://developers.openai.com/codex/hooks)

| Recorded evidence on the first Stop for a watched task | Hook response |
| --- | --- |
| Missing report | Requests a continuation to run `verify TASK` when ready or report the outstanding work. |
| `running` | Requests a continuation to check whether the verification process is active. An interrupted run can be repeated once the project is idle. |
| `fail` | Points to the task's `evidence.json` so the agent can inspect failed criteria or integrity issues, repair within scope or report a blocker. |
| `pass` | Returns an empty object. Run fresh verification after subsequent edits. |
| Unreadable JSON, wrong task ID, or an unrecognized status | Returns a fail-open `systemMessage` and leaves the completion decision to explicit verification. |

Unwatched sessions, other events and a repeated Stop with `stop_hook_active` pass through. The handler reads bounded local records. Only an explicit `verify` invocation executes the registered project checks.

## Other adapters

Codex and Claude Code share the Stop handler, task directory, policy, evidence and Python checks. Use `install --client both` to expose this workflow in both clients. The existing `adapters/codex/stop.py` entry point delegates to `adapters/stop.py`. [Claude Code adapter](claude.md)
