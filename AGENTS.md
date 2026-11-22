# Working on the harness

This checkout contains the harness source. The project guidance installed into a user's repository lives in `adapters/codex/AGENTS.md`.

Run `python -m unittest discover -s tests -v` after a code change. Run `python examples/demo.py --project PATH` with a fresh scratch directory when changing the normal CLI workflow. Keep the validator dependency-free. Preserve installer collision behavior, fresh verification, and the distinction between a structural check and an independent review. Put client-specific event handling under `adapters/`. Keep task contract and evidence semantics shared.
