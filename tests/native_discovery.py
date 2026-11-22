"""Optional offline smoke check for Codex CLI's native skills/list and hooks/list endpoints."""
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tempfile
import threading

SOURCE = Path(__file__).resolve().parents[1]


def discover(binary, project, env):
    process = subprocess.Popen([binary, "app-server", "--listen", "stdio://"], cwd=project, env=env,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               text=True, encoding="utf-8")
    received = queue.Queue()

    def collect():
        try:
            for line in process.stdout:
                received.put(json.loads(line))
        finally:
            received.put(None)

    threading.Thread(target=collect, daemon=True).start()

    def send(method, params, key=None):
        request = {"method": method, "params": params}
        if key is not None:
            request["id"] = key
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()
        if key is None:
            return
        while True:
            try:
                msg = received.get(timeout=20)
            except queue.Empty as exc:
                raise RuntimeError(f"Codex timed out during {method}") from exc
            if msg is None:
                raise RuntimeError(f"Codex exited during {method}")
            if msg.get("id") == key:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg["result"]

    try:
        send("initialize", {"clientInfo": {"name": "quality_probe", "version": "1"},
                            "capabilities": {"experimentalApi": True}}, 1)
        send("initialized", {})
        skills = send("skills/list", {"cwds": [str(project)], "forceReload": True}, 2)["data"][0]
        hooks = send("hooks/list", {"cwds": [str(project)]}, 3)["data"][0]
        names = sorted(s["name"] for s in skills["skills"] if Path(s["path"]).is_relative_to(project))
        rows = [{"event": h["eventName"], "source": h["source"], "trust": h["trustStatus"]}
                for h in hooks["hooks"] if h["source"] == "project"]
        return {"project_skills": names, "project_hooks": rows, "hook_errors": hooks["errors"]}
    finally:
        process.stdin.close()
        try:
            process.wait(8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        process.stdout.close()


def main():
    binary = shutil.which("codex")
    if not binary or not shutil.which("git"):
        raise SystemExit("This optional check needs local Codex CLI and Git.")
    with tempfile.TemporaryDirectory(prefix="codex-quality-") as temp:
        base = Path(temp).resolve()
        project, profile = base / "project", base / "profile"
        project.mkdir()
        profile.mkdir()
        subprocess.run(["git", "init", "-q", str(project)], check=True)
        # Trust only the disposable project for discovery. Leave the actual hook untrusted.
        (profile / "config.toml").write_text(
            "[projects." + json.dumps(str(project)) + "]\ntrust_level = \"trusted\"\n", encoding="utf-8")
        env = dict(os.environ, CODEX_HOME=str(profile))
        subprocess.run([sys.executable, str(SOURCE / "harness.py"), "install", "--project", str(project),
                        "--hook"], env=env, check=True, stdout=subprocess.DEVNULL)
        result = discover(binary, project, env)
        result["codex_version"] = subprocess.check_output([binary, "--version"], text=True, env=env).strip()
        print(json.dumps(result, indent=2))
        expected = sorted(p.name for p in (SOURCE / "skills").iterdir() if p.is_dir())
        if result["project_skills"] != expected or result["hook_errors"]:
            raise SystemExit("Codex discovery mismatch.")
        if not any(h["event"] == "stop" for h in result["project_hooks"]):
            raise SystemExit("Stop registration unavailable on this Codex installation.")


if __name__ == "__main__":
    main()
