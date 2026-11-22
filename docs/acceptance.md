# MVP acceptance results

Verified on Windows with Python 3.12.4 and Codex CLI 0.171.0 on 2026-11-21 (Pacific). The regression suite completed **27 tests in 4.219 seconds**, with zero failures or skips. [Full test output](evidence/regression.txt)

| Criterion | Observed result |
| --- | --- |
| Codex discovers all seven skills | The native CLI's discovery endpoint returned all seven from an installed temporary project. All seven source files also passed the Codex skill-format validator. [Native result](evidence/codex-discovery.json) |
| Installation preserves existing settings | Tests exercised repeated and preview installations, user-scope skill collisions, existing AGENTS.md, policy and hooks. A linked destination was rejected before an outside write. |
| Real changes use a persistent, independently reviewed spec and plan | Standard and high route tests rejected missing coverage, a changes-requested verdict, a stale review handoff and edits after a review. The valid sequence reached verification. High mode also required a negative case and recovery plan. Reviewer identities in automated tests are synthetic. |
| A task cannot silently lower its acceptance bar | Tests rejected changed criteria or policy and added, removed or modified protected tests. A check that modified a protected file failed overall even with command exit 0. |
| Evidence distinguishes a broken deliverable from a repaired one | The executable demo ran actual Python tests against both implementations. The broken baseline exited 1 with both criteria failed. The corrected formatter exited 0 with both passed. Both reports reference the same seal. [Broken report](evidence/baseline-failure.json) · [Corrected report](evidence/evidence.json) |
| Verification failure stays visible | Nonzero commands, timeouts, missing files, malformed or missing policy and stale prior passes were exercised. The latest report records the failed attempt. |
| Native hook integration is optional | The installed CLI reported the project Stop hook with zero loading errors and an untrusted status. A separate test launched the generated native PowerShell command from a nested directory and got a continuation request. Protocol tests covered unbound sessions, recorded passes, malformed state and the second-stop loop guard. |
| No new runtime is needed | The installed zip application ran from a target project using the Python standard library. Demo, regression tests and native discovery required no model calls. |

## Reproduce

From the source checkout, run:

```sh
python -m unittest discover -s tests -v
python tests/native_discovery.py
python examples/demo.py --project ../quality-acceptance-demo
```

The native discovery check uses a disposable Codex profile with a trusted temporary project. It leaves the hook untrusted for inspection. Hook decisions were exercised with test events. This run did not include a model-backed interactive turn or a live independent review. The synthetic review tests demonstrate binding and rejection behavior. Linux, macOS and other Codex CLI versions were outside this verification run.
