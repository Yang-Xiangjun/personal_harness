# Codex CLI adapter

Checked on 2026-11-21 against the official local Codex docs and the installed `codex-cli 0.171.0`. Native discovery reads project `.agents/skills` and personal `~/.agents/skills`. Project instruction discovery prefers a nonempty `AGENTS.override.md` over `AGENTS.md`. A fresh CLI session is a reliable way to pick up an installation. [Skills](https://developers.openai.com/codex/skills) · [AGENTS.md](https://developers.openai.com/codex/guides/agents-md)

## Optional Stop reminder

From the source checkout run `python harness.py install --project PATH --hook`. The installer probes `codex features list`. If an enabled hook feature is unavailable, it prints **FAIL-OPEN** and leaves explicit verification available. When supported, the project adapter prepares `.codex/hooks.json`. Existing registrations are preserved. On a conflict it writes a fragment for the project owner to merge. It never changes trust settings. Inspect the generated command and the source script before trusting it. The Windows override uses native PowerShell literal paths. Unix uses POSIX shell quoting. If a custom shell is incompatible, use explicit verification.

Open the target as a trusted project, start a fresh Codex CLI session and inspect `/hooks`. Review and trust the Stop command there. Trust or admin policy can suppress a registered hook. Keep the source checkout and Python interpreter at the original paths while the hook is enabled. The explicit CLI installed in the target works independently of that checkout.

Opt in for a particular Codex session by running `python -I .quality/quality.pyz watch TASK` from it. This uses `CODEX_THREAD_ID` when present. Supply `--session ID` if needed. The marker contains the task ID and is keyed by a hash of the session ID. Use `unwatch` to detach. Other sessions are unaffected.

The handler reads a JSON event from stdin and returns JSON on stdout with exit code 0. On the first Stop for a watched task with missing or nonpassing evidence it requests one continuation through `decision: "block"` and a reason. On an already continued turn (`stop_hook_active`) it returns an empty object. Unsupported events and unwatched sessions pass through. Invalid state or payload yields a fail-open warning. It reads only bounded local records and never runs project test code. A saved pass can be stale. The reminder checks the recorded status only. Run `verify` for a completion decision. [Native hook discovery, trust and Stop semantics](https://developers.openai.com/codex/hooks)

## Other adapters

The source-specific pieces are `adapters/codex/`, skill installation destinations and the hook installer. The task directory, JSON policy and evidence, Python checks, and portable playbooks can be reused by another client. Codex CLI is the implemented integration.
