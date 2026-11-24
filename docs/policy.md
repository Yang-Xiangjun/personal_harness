# Quality policy

The machine-readable defaults ship in `quality/default-policy.json`. Installation seeds the project-owned `.quality/policy.json`. Each command reads that project copy. Its `modes` select required artifacts. The repair budget guides the executing skill. The CLI enforces contract validity, required artifacts, review binding, protected-file integrity and fresh check results.

## Baseline

Prepare and inspect the criteria, acceptance tests, policy, and plan before implementation. `seal` records SHA-256 hashes of those inputs, including review where required. The CLI refuses to overwrite a seal. `verify` inventories matching files before and after running checks and rejects added, deleted or modified protected files. A revised requirement or test needs an explicit decision and a new task ID. Keep the earlier spec and evidence and reference their IDs in the successor.

`protected_globs` are case-insensitive shell-style matches on full project-relative paths. A star can cross a slash. The defaults cover test folders, common test filenames and selected test configuration. Extend these patterns for fixtures, scripts, build rules or other dependencies your checks trust. The inventory skips directories named `.git`, `.quality`, `.agents`, `.codex`, `.claude`, `.venv`, `venv`, `node_modules`, `.tox`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache` and `__pycache__`. An unignored linked directory or protected linked file prevents sealing. Paths explicitly named in a contract cannot traverse a link or enter harness metadata.

## Command authority

Projects start with an empty command registry. Text checks can run immediately. A contract may name a command already in the project policy. The policy stores an argument array beginning with an absolute executable or `{python}` (the running interpreter). Choose a reviewed local test entry point. Inspect transitive inputs, test counts and skips. Some test runners exit zero when they collect zero tests. Prefer a named test or a runner configured to fail empty suites. Use direct executables, one command per entry.

Command checks run as the invoking user, from the project root, with the current environment, closed input, a timeout and no implicit shell. Output capture stores byte counts and a SHA-256 digest. `verify --include-output TASK` adds up to 2 KiB of the combined output per check. Use this only for logs you are comfortable saving. Keep network access, credentials and system permissions constrained through the invoking client or your operating system. Review any new checkout before executing its commands or tests.

## Authority and freshness

Use the top-level report status and process exit code. Every verification replaces `evidence.json`, marks it running first, then writes a final status. A failure in a prerequisite can leave criteria marked `not-run`. Each named command runs once per verification, and criteria referencing it share that result. Deliverable hashes describe the bytes examined. Run again after any edit.

A local user or agent with write access to the harness can edit its code, seals, evidence or reviewer record. These hashes detect drift within a cooperative workspace. For a stronger boundary, keep a trusted checkout and baseline outside the edit workspace, or verify in separately controlled CI with reviewed tests and restricted permissions. Restore agreed inputs or open a successor task when the baseline changes.
