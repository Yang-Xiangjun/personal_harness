"""Check real Claude Code skill and memory discovery using its local /context command."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

SOURCE = Path(__file__).resolve().parents[1]


def main():
    claude = shutil.which("claude")
    if not claude:
        raise SystemExit("This optional discovery check needs Claude Code on PATH.")
    with tempfile.TemporaryDirectory(prefix="claude-quality-") as temp:
        base = Path(temp).resolve()
        project, profile = base / "project", base / "profile"
        project.mkdir()
        profile.mkdir()
        (project / "AGENTS.md").write_text("Use the team's established contribution process.\n", encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("ANTHROPIC_", "CLAUDE"))}
        env.update(CLAUDE_CONFIG_DIR=str(profile), CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1",
                   DISABLE_AUTOUPDATER="1", ANTHROPIC_API_KEY="offline-fixture",
                   ANTHROPIC_BASE_URL="http://127.0.0.1:1", API_TIMEOUT_MS="2500")
        subprocess.run([sys.executable, str(SOURCE / "harness.py"), "install", "--client", "claude",
                        "--project", str(project)], env=env, check=True, stdout=subprocess.DEVNULL)
        proc = subprocess.run([claude, "-p", "/context", "--output-format", "json",
                               "--setting-sources", "project,local", "--strict-mcp-config",
                               "--no-session-persistence"], cwd=project, env=env, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, encoding="utf-8", timeout=30, check=True)
        context = json.loads(proc.stdout)["result"].replace("\\", "/")
        names = sorted(path.parent.name for path in (SOURCE / "skills").glob("*/SKILL.md"))
        missing = [name for name in names if f"| {name} | Project |" not in context]
        memory = ["AGENTS.md", "CLAUDE.md", ".quality/CLAUDE.md"]
        for path in memory:
            if (project / path).as_posix() not in context:
                missing.append(path)
        if missing:
            raise SystemExit(f"Missing from Claude's /context report: {', '.join(missing)}")
        version = subprocess.check_output([claude, "--version"], env=env, text=True).strip()
        print(json.dumps({"client": version, "project_skills": names, "project_memory": memory}, indent=2))


if __name__ == "__main__":
    main()
