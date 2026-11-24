import contextlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from quality.cli import main
from quality.common import encoded
from quality.install import SOURCE, hook_settings


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value))


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project with spaces"
        self.root.mkdir()
        self.q = self.root / ".quality"
        self.folder = self.q / "tasks" / "example"
        self.call("install")

    def call(self, *args, code=0):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            got = main([*args, "--project", str(self.root)])
        self.assertEqual(got, code, output.getvalue())
        return json.loads(output.getvalue())

    def make(self, mode="fast"):
        self.call("new", "example", "--mode", mode, "--objective", "Write a correct label")
        self.c = json.loads((self.folder / "contract.json").read_bytes())
        self.c.update(deliverables=["label.txt"], criteria=[{
            "id": "label", "expect": "A line reading OK",
            "check": {"kind": "text-equals", "path": "label.txt", "text": "OK\n"}}])
        write(self.folder / "contract.json", self.c)
        (self.root / "label.txt").write_bytes(b"OK\r\n")
        if mode != "fast":
            (self.folder / "spec.md").write_text("The label must read OK on one line.", encoding="utf-8")
            self.plan = {"steps": [{"id": "write", "action": "Update label", "files": ["label.txt"],
                                    "criteria": ["label"], "verify": "Compare full label"}]}
            write(self.folder / "plan.json", self.plan)

    def record(self, verdict="pass", code=0, reviewed_hash=None):
        if reviewed_hash is None:
            reviewed_hash = self.call("plan-check", "example")["inputs_sha256"]
        self.call("review", "example", "--source", "human", "--by", "fixture reviewer",
                  "--ref", "synthetic-review-01", "--note", "Fixture checks exact output.",
                  "--verdict", verdict, "--inputs-sha256", reviewed_hash, code=code)

    def check(self, code=0):
        report = self.call("verify", "example", code=code)
        self.assertEqual(report, json.loads((self.folder / "evidence.json").read_bytes()))
        return report

    def set_command(self, args, timeout=10):
        path = self.q / "policy.json"
        p = json.loads(path.read_bytes())
        p.update(commands={"fixture": ["{python}", "-I", "-c", *args]}, timeout_seconds=timeout)
        write(path, p)
        self.c["criteria"][0]["check"] = {"kind": "command", "name": "fixture"}
        write(self.folder / "contract.json", self.c)

    def test_fresh_verification_replaces_a_previous_pass(self):
        self.make()
        self.call("seal", "example")
        r = self.check()
        self.assertEqual(r["criteria"][0]["status"], "pass")
        (self.root / "label.txt").write_text("WRONG", encoding="utf-8")
        bad = self.check(1)
        self.assertEqual(bad["criteria"][0]["status"], "fail")
        self.assertNotEqual(bad["run_id"], r["run_id"])

    def test_absent_deliverable_fails_even_when_command_passes(self):
        self.make()
        self.set_command(["print('OK')"])
        self.call("seal", "example")
        (self.root / "label.txt").unlink()
        report = self.check(1)
        self.assertEqual(report["criteria"][0]["status"], "pass")
        self.assertIn("Missing deliverable", report["issues"][0])

    def test_requires_a_seal_and_never_silently_reseals(self):
        self.make()
        self.assertEqual(self.check(1)["criteria"][0]["status"], "not-run")
        self.call("seal", "example")
        self.call("seal", "example", code=1)

    def test_changed_added_and_deleted_tests_are_detected(self):
        self.make()
        test = self.root / "tests/test_sample.py"
        test.parent.mkdir()
        test.write_bytes(b"assert 1")
        self.call("seal", "example")
        test.write_bytes(b"")
        self.assertIn("tests/test_sample.py", self.check(1)["issues"][0])
        test.unlink()
        self.assertIn("tests/test_sample.py", self.check(1)["issues"][0])
        test.write_bytes(b"assert 1")
        (test.parent / "test_extra.py").touch()
        self.assertIn("tests/test_extra.py", self.check(1)["issues"][0])

    def test_changed_criteria_and_policy_are_detected(self):
        self.make()
        self.call("seal", "example")
        self.c["criteria"][0]["expect"] = "Different objective"
        write(self.folder / "contract.json", self.c)
        self.assertIn("contract.json", self.check(1)["issues"][0])
        self.c["criteria"][0]["expect"] = "A line reading OK"
        write(self.folder / "contract.json", self.c)
        with (self.q / "policy.json").open("ab") as stream:
            stream.write(b" ")
        self.assertIn("policy.json", self.check(1)["issues"][0])

    def test_changed_protected_inputs_during_command_fail_closed(self):
        self.make()
        test = self.root / "test_something.py"
        test.touch()
        self.set_command(["from pathlib import Path; Path('test_something.py').write_bytes(b'changed')"])
        self.call("seal", "example")
        report = self.check(1)
        self.assertEqual(report["criteria"][0]["status"], "pass")
        self.assertIn("test_something.py", report["issues"][0])

    def test_structural_coverage_and_actual_review_are_distinct(self):
        self.make("standard")
        self.c["criteria"].append({"id": "another", "expect": "OK included",
                                    "check": {"kind": "text-contains", "path": "label.txt", "text": "OK"}})
        write(self.folder / "contract.json", self.c)
        self.assertIn("misses criteria", self.call("plan-check", "example", code=1)["issue"])
        self.plan["steps"][0]["criteria"].append("another")
        write(self.folder / "plan.json", self.plan)
        self.call("plan-check", "example")
        self.call("seal", "example", code=1)
        self.record("changes", 1)
        self.call("seal", "example", code=1)
        self.record()
        (self.folder / "spec.md").write_bytes(b"Revised observable requirement")
        self.assertIn("stale", self.call("seal", "example", code=1)["issue"])
        self.record()
        self.call("seal", "example")
        self.check()

    def test_high_route_requires_negative_case_and_recovery(self):
        self.make("high")
        self.call("plan-check", "example", code=1)
        self.plan.update(negative_case="An empty result fails.", recovery="Restore the previous label.")
        write(self.folder / "plan.json", self.plan)
        self.record()
        self.call("seal", "example")
        self.check()

    def test_review_handoff_rejects_edits_before_recording(self):
        self.make("standard")
        reviewed = self.call("plan-check", "example")["inputs_sha256"]
        (self.folder / "spec.md").write_bytes(b"New behavior after handoff.")
        self.record(reviewed_hash=reviewed, code=1)
        self.assertFalse((self.folder / "review.json").exists())

    def test_bad_contracts_cannot_pass_vacuously(self):
        self.make()
        criterion = self.c["criteria"][0]
        for rows in ([], [criterion, criterion], [{"id": "empty", "expect": "x",
                     "check": {"kind": "text-contains", "path": "label.txt", "text": ""}}]):
            with self.subTest(rows=rows):
                self.c["criteria"] = rows
                write(self.folder / "contract.json", self.c)
                self.call("plan-check", "example", code=1)

    def test_path_validation(self):
        self.make()
        for path in ("../outside", "/outside", "C:/outside", ".quality/tasks/example/seal.json",
                     ".git/config", "secret:stream", "nested/../file", "CON", "con.txt"):
            with self.subTest(path=path):
                self.c["deliverables"] = [path]
                write(self.folder / "contract.json", self.c)
                self.call("plan-check", "example", code=1)
        self.call("new", "../outside", "--objective", "bad id", code=1)

    def test_unknown_command_and_embedded_arguments_rejected(self):
        self.make()
        for check in ({"kind": "command", "name": "unregistered"},
                      {"kind": "command", "name": "unregistered", "argv": ["launch"]}):
            self.c["criteria"][0]["check"] = check
            write(self.folder / "contract.json", self.c)
            self.call("seal", "example", code=1)

    def test_install_refuses_a_reparse_point_before_writing(self):
        self.root = Path(self.temp.name) / "reparse-project"
        self.root.mkdir()
        agents = self.root / ".agents"
        agents.mkdir()
        real_lstat = Path.lstat

        def lstat(path):
            if path == agents:
                return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
            return real_lstat(path)

        with patch.object(Path, "lstat", lstat):
            result = self.call("install", code=1)
        self.assertIn("Linked paths", result["issue"])
        self.assertFalse((self.root / ".quality").exists())

    def test_real_linked_directory_cannot_redirect_an_install(self):
        self.root = Path(self.temp.name) / "linked-project"
        target = Path(self.temp.name) / "outside"
        target.mkdir()
        self.root.mkdir()
        link = self.root / ".agents"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"System cannot create the directory symlink fixture (OS error {exc.errno}).")
        self.call("install", code=1)
        self.assertEqual(list(target.iterdir()), [])
        self.assertFalse((self.root / ".quality").exists())

    def test_oversized_text_yields_a_failed_criterion(self):
        self.make()
        self.call("seal", "example")
        with (self.root / "label.txt").open("wb") as stream:
            stream.truncate(8 * 1024 * 1024 + 1)
        row = self.check(1)["criteria"][0]
        self.assertIn("exceeds 8 MiB", row["error"])

    def test_command_failure_timezone_and_no_default_output_disclosure(self):
        self.make()
        self.set_command(["import sys; print('fixture-marker'); sys.exit(7)"])
        self.call("seal", "example")
        r = self.check(1)
        ev = r["criteria"][0]["evidence"]
        self.assertEqual(ev["exit_code"], 7)
        self.assertGreater(ev["output_bytes"], 0)
        self.assertNotIn("output_tail", ev)
        self.assertIn("+00:00", r["finished_at"])
        detail = self.call("verify", "example", "--include-output", code=1)
        self.assertIn("fixture-marker", detail["criteria"][0]["evidence"]["output_tail"])

    def test_command_timeout(self):
        self.make()
        self.set_command(["import time; time.sleep(4)"], timeout=1)
        self.call("seal", "example")
        self.assertTrue(self.check(1)["criteria"][0]["evidence"]["timed_out"])

    def test_malformed_policy_invalidates_existing_report(self):
        self.make()
        self.call("seal", "example")
        self.check()
        (self.q / "policy.json").write_bytes(b"{")
        self.assertEqual(self.check(1)["status"], "fail")

    def test_missing_policy_invalidates_existing_report(self):
        self.make()
        self.call("seal", "example")
        self.check()
        (self.q / "policy.json").unlink()
        self.assertEqual(self.check(1)["status"], "fail")

    def test_install_preserves_settings_and_is_idempotent(self):
        agents = self.root / "AGENTS.md"
        agents.write_bytes(b"User conventions\r\n")
        p = self.q / "policy.json"
        p.write_bytes(p.read_bytes() + b" ")
        saved = p.read_bytes()
        result = self.call("install")
        self.assertEqual(result["created"], [])
        self.assertEqual(agents.read_bytes(), b"User conventions\r\n")
        self.assertEqual(p.read_bytes(), saved)

    def test_conflicts_are_checked_before_writes(self):
        changed = self.root / ".agents/skills/task-router/SKILL.md"
        changed.write_bytes(b"Locally customized")
        missing = self.root / ".agents/skills/task-execution/SKILL.md"
        missing.unlink()
        self.call("install", code=1)
        self.assertFalse(missing.exists())
        self.assertEqual(changed.read_bytes(), b"Locally customized")

    def test_optional_user_skills_preserve_global_files(self):
        home = Path(self.temp.name) / "fake-home"
        home.mkdir()
        global_config = home / ".codex/config.toml"
        global_config.parent.mkdir()
        global_config.write_bytes(b"owner settings")
        with patch("quality.install.Path.home", return_value=home):
            self.call("install", "--user-skills", "--dry-run")
            self.assertFalse((home / ".agents").exists())
            self.call("install", "--user-skills")
            self.assertEqual(len(list((home / ".agents/skills").glob("*/SKILL.md"))), 7)
            changed = home / ".agents/skills/task-router/SKILL.md"
            changed.write_bytes(b"personal customization")
            self.call("install", "--user-skills", code=1)
            self.assertEqual(changed.read_bytes(), b"personal customization")
        self.assertEqual(global_config.read_bytes(), b"owner settings")

    def test_hook_unsupported_and_existing_config(self):
        with patch("quality.install.hook_available", return_value=False):
            result = self.call("install", "--hook")
            self.assertTrue(any("FAIL-OPEN" in n for n in result["notes"]))
            self.assertFalse((self.root / ".codex/hooks.json").exists())
        old = self.root / ".codex/hooks.json"
        old.parent.mkdir()
        old.write_bytes(b'{"hooks":{"Stop":[]}}')
        with patch("quality.install.hook_available", return_value=True):
            self.call("install", "--hook")
        self.assertEqual(old.read_bytes(), b'{"hooks":{"Stop":[]}}')
        payload = json.loads((self.q / "stop-hook.fragment.json").read_bytes())
        self.assertEqual(payload["hooks"]["Stop"][0]["hooks"][0]["type"], "command")

    def test_hook_protocol_scoping_retry_guard_and_invalid_state(self):
        self.make()
        script = SOURCE / "adapters/codex/stop.py"

        def invoke(data):
            proc = subprocess.run([sys.executable, "-I", "-S", str(script), str(self.root)],
                                  input=json.dumps(data), text=True, capture_output=True, check=True)
            return json.loads(proc.stdout)

        event = {"hook_event_name": "Stop", "session_id": "abc", "cwd": str(self.root),
                 "stop_hook_active": False}
        self.assertEqual(invoke(event), {})
        self.call("watch", "example", "--session", "abc")
        missing = invoke(event)
        self.assertEqual(missing["decision"], "block")
        self.assertIn("verify example", missing["reason"])
        self.assertEqual(invoke(dict(event, cwd=self.temp.name)), {})
        self.assertEqual(invoke(dict(event, session_id="other")), {})
        self.assertEqual(invoke(dict(event, stop_hook_active=True)), {})
        report_path = self.folder / "evidence.json"
        write(report_path, {"task": "example", "status": "running"})
        running = invoke(event)
        self.assertEqual(running["decision"], "block")
        self.assertIn("in progress", running["reason"])
        # A continuation is a model prompt. Keep free-form report content out of it.
        detail = "arbitrary text from a failing test"
        write(report_path, {"task": "example", "status": "fail", "issues": [detail]})
        failed = invoke(event)
        self.assertEqual(failed["decision"], "block")
        self.assertIn("evidence.json", failed["reason"])
        self.assertNotIn(detail, failed["reason"])
        for task_name, status in (("other", "pass"), ("example", "unknown")):
            write(report_path, {"task": task_name, "status": status})
            response = invoke(event)
            self.assertNotIn("decision", response)
            self.assertIn("fail-open", response["systemMessage"])
        self.call("seal", "example")
        self.check()
        self.assertEqual(invoke(event), {})
        (self.folder / "evidence.json").write_bytes(b"{")
        self.assertIn("fail-open", invoke(event)["systemMessage"])
        self.call("unwatch", "--session", "abc")
        self.assertEqual(invoke(event), {})

    def test_generated_hook_command_runs_from_nested_working_directory(self):
        self.make()
        self.call("watch", "example", "--session", "hook-command-fixture")
        nested = self.root / "nested"
        nested.mkdir()
        event = {"hook_event_name": "Stop", "session_id": "hook-command-fixture",
                 "cwd": str(nested), "stop_hook_active": False}
        command = hook_settings(self.root)["hooks"]["Stop"][0]["hooks"][0]["command"]
        interpreter = (["powershell.exe", "-NoProfile", "-NonInteractive", "-Command"]
                       if os.name == "nt" else ["/bin/sh", "-c"])
        proc = subprocess.run([*interpreter, command], input=json.dumps(event), cwd=nested,
                              text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(proc.stdout)["decision"], "block")

    def test_exclusive_lock_preserves_interrupted_state(self):
        self.make()
        (self.q / "busy.lock").write_bytes(b"pid=fixture")
        self.call("seal", "example", code=1)
        self.assertFalse((self.folder / "seal.json").exists())
        self.assertEqual((self.q / "busy.lock").read_bytes(), b"pid=fixture")

    def test_claude_only_install_and_preview(self):
        self.root = Path(self.temp.name) / "Claude's project"
        self.root.mkdir()
        self.call("install", "--client", "claude", "--dry-run")
        self.assertEqual(list(self.root.iterdir()), [])
        self.call("install", "--client", "claude")
        self.assertEqual((self.root / "CLAUDE.md").read_text(), "@.quality/CLAUDE.md\n")
        guide = (self.root / ".quality/CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn(Path(sys.executable).as_posix(), guide)
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertFalse((self.root / ".agents").exists())
        self.assertFalse((self.root / ".quality/CODEX.md").exists())
        skills = list((self.root / ".claude/skills").glob("*/SKILL.md"))
        self.assertEqual(len(skills), 7)
        for skill in skills:
            self.assertEqual(skill.read_bytes(), (SOURCE / "skills" / skill.parent.name / "SKILL.md").read_bytes())
        self.assertEqual(self.call("install", "--client", "claude")["created"], [])

    def test_both_clients_verify_the_same_sealed_task(self):
        self.assertFalse((self.root / ".claude").exists())
        self.make()
        self.call("seal", "example")
        baseline = self.check()
        self.call("install", "--client", "both")
        proc = subprocess.run([sys.executable, "-I", str(self.q / "quality.pyz"), "verify", "example"],
                              cwd=self.root, capture_output=True, text=True, check=True)
        report = json.loads(proc.stdout)
        self.assertEqual(report["seal_sha256"], baseline["seal_sha256"])
        self.assertNotEqual(report["run_id"], baseline["run_id"])
        self.assertEqual(report["status"], "pass")
        (self.root / "label.txt").write_bytes(b"wrong")
        self.assertEqual(self.check(1)["criteria"][0]["status"], "fail")
        self.assertEqual(self.call("install", "--client", "both")["created"], [])

    def test_claude_metadata_cannot_be_used_as_acceptance_evidence(self):
        self.make()
        self.c["criteria"][0]["check"]["path"] = ".claude/settings.json"
        write(self.folder / "contract.json", self.c)
        self.call("plan-check", "example", code=1)

    def test_claude_install_preserves_owner_instructions_settings_and_skill_edits(self):
        owner = self.root / "CLAUDE.md"
        owner.write_bytes(b"Team instructions\r\n")
        shared = self.root / ".claude/settings.json"
        personal = shared.with_name("settings.local.json")
        write(shared, {"language": "french"})
        write(personal, {"hooks": {"SessionStart": []}})
        before = [p.read_bytes() for p in (owner, shared, personal)]
        with patch("quality.install.hook_available", return_value=True):
            result = self.call("install", "--client", "claude", "--hook")
        self.assertEqual(before, [p.read_bytes() for p in (owner, shared, personal)])
        self.assertTrue(any("@.quality/CLAUDE.md" in note for note in result["notes"]))
        self.assertIn("Stop", json.loads((self.q / "claude-stop-hook.fragment.json").read_bytes())["hooks"])
        skill = self.root / ".claude/skills/task-router/SKILL.md"
        skill.write_bytes(b"Team skill")
        missing = self.root / ".agents/skills/task-router/SKILL.md"
        missing.unlink()
        self.call("install", "--client", "both", code=1)
        self.assertEqual(skill.read_bytes(), b"Team skill")
        self.assertFalse(missing.exists())

    def test_claude_personal_skills_use_selected_profile(self):
        for custom in (False, True):
            with self.subTest(custom=custom):
                home = Path(self.temp.name).resolve() / f"account-{custom}"
                profile = home / ("custom profile" if custom else ".claude")
                with patch("quality.install.Path.home", return_value=home), patch.dict(
                    os.environ, {"CLAUDE_CONFIG_DIR": str(profile) if custom else ""}
                ):
                    self.call("install", "--client", "claude", "--user-skills")
                    self.assertEqual(len(list((profile / "skills").glob("*/SKILL.md"))), 7)
                    self.assertFalse((self.root / ".claude/skills").exists())
                    self.assertFalse((profile / "settings.json").exists())

    def test_claude_keeps_project_instructions_visible(self):
        project_guide = self.root / "AGENTS.md"
        project_guide.write_bytes(b"Team instructions\n")
        hidden = self.root / ".claude"
        hidden.mkdir()
        (hidden / "AGENTS.md").write_bytes(b"More team instructions\n")
        claude_guide = hidden / "CLAUDE.md"
        claude_guide.write_bytes(b"Claude team instructions\n")
        result = self.call("install", "--client", "both")
        self.assertFalse((self.root / "CLAUDE.md").exists())
        self.assertEqual(claude_guide.read_bytes(), b"Claude team instructions\n")
        self.assertTrue(any("@../.quality/CLAUDE.md" in note for note in result["notes"]))
        claude_guide.unlink()
        self.call("install", "--client", "both")
        self.assertEqual((self.root / "CLAUDE.md").read_text().splitlines(),
                         ["@AGENTS.md", "@.claude/AGENTS.md", "@.quality/CLAUDE.md"])
        self.assertEqual(project_guide.read_bytes(), b"Team instructions\n")
        self.assertEqual(self.call("install", "--client", "both")["created"], [])

    def test_claude_stop_uses_session_id_and_native_shell(self):
        self.make()
        with patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": "claude-fixture", "CODEX_THREAD_ID": ""}):
            self.call("watch", "example")
        with patch("quality.install.hook_available", return_value=True):
            self.call("install", "--client", "claude", "--hook")
        path = self.root / ".claude/settings.local.json"
        handler = json.loads(path.read_bytes())["hooks"]["Stop"][0]["hooks"][0]
        self.assertNotIn("commandWindows", handler)
        if os.name == "nt":
            self.assertEqual(handler["shell"], "powershell")
            shell = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command"]
        else:
            shell = ["/bin/sh", "-c"]
        event = {"hook_event_name": "Stop", "session_id": "claude-fixture", "cwd": str(self.root),
                 "stop_hook_active": False}
        def invoke():
            proc = subprocess.run([*shell, handler["command"]], cwd=self.root, input=json.dumps(event),
                                  capture_output=True, text=True, check=True)
            return json.loads(proc.stdout)

        self.assertEqual(invoke()["decision"], "block")
        event["stop_hook_active"] = True
        self.assertEqual(invoke(), {})
        event["stop_hook_active"] = False
        with patch.dict(os.environ, {"CLAUDE_CODE_SESSION_ID": "claude-fixture", "CODEX_THREAD_ID": "outer"}):
            self.call("unwatch", code=1)
            self.call("unwatch", "--session", "claude-fixture")
        self.assertEqual(invoke(), {})

    def test_unsupported_claude_hook_leaves_codex_available(self):
        with patch("quality.install.hook_available", side_effect=lambda client: client == "codex"):
            result = self.call("install", "--client", "both", "--hook")
        self.assertTrue(any("FAIL-OPEN (claude)" in note for note in result["notes"]))
        self.assertTrue((self.root / ".codex/hooks.json").is_file())
        self.assertFalse((self.root / ".claude/settings.local.json").exists())

    def test_installed_entrypoint_is_independent_of_source_cwd(self):
        self.assertIn(sys.executable, (self.q / "CODEX.md").read_text(encoding="utf-8"))
        proc = subprocess.run([sys.executable, "-I", str(self.q / "quality.pyz"), "new",
                               "installed", "--objective", "A portable task"], cwd=self.root,
                              text=True, capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertTrue((self.q / "tasks/installed/spec.md").exists())


if __name__ == "__main__":
    unittest.main()
