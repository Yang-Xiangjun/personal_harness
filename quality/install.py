"""Create-only Codex adapter installation. No dependency manager or global config merge."""
import io
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import zipfile

from .common import encoded, identifier, local, lock, put, require

SOURCE = Path(__file__).resolve().parent.parent


def bundle():
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        files = {"__main__.py": b"from quality.cli import main\nraise SystemExit(main())\n"}
        for path in sorted((SOURCE / "quality").glob("*.py")):
            files["quality/" + path.name] = path.read_bytes()
        for name, content in files.items():
            archive.writestr(zipfile.ZipInfo(name), content, compress_type=zipfile.ZIP_DEFLATED)
    return data.getvalue()


def hook_available():
    binary = shutil.which("codex")
    if not binary:
        return False
    try:
        proc = subprocess.run([binary, "features", "list"], stdin=subprocess.DEVNULL, capture_output=True,
                              timeout=12, cwd=SOURCE, text=True, errors="replace")
        return proc.returncode == 0 and any(line.split()[:1] in (["hooks"], ["codex_hooks"])
                                             and line.split()[-1:] == ["true"]
                                             for line in proc.stdout.splitlines())
    except (OSError, subprocess.TimeoutExpired):
        return False


def hook_settings(root):
    script = SOURCE / "adapters" / "codex" / "stop.py"
    args = [sys.executable, "-I", "-S", str(script), str(root)]
    if os.name == "nt":
        # Codex's native Windows PowerShell accepts the call operator and literal strings.
        quoted = ["'" + arg.replace("'", "''") + "'" for arg in args]
        command = "& " + " ".join(quoted)
    else:
        command = shlex.join(args)
    handler = {"type": "command", "command": command, "timeout": 5,
               "statusMessage": "Checking the recorded task verification"}
    if os.name == "nt":
        handler["commandWindows"] = command
    return {"hooks": {"Stop": [{"hooks": [handler]}]}}


def install(root, user_skills=False, hook=False, dry_run=False):
    require((SOURCE / "skills").is_dir(), "Run install using harness.py in the source checkout.")
    require(root.is_dir(), f"Create the project directory first: {root}")
    skill_root = Path.home().resolve() if user_skills else root
    files = {}
    notes = []
    for path in sorted((SOURCE / "skills").glob("*/SKILL.md")):
        name = identifier(path.parent.name)
        files[local(skill_root, f".agents/skills/{name}/SKILL.md")] = path.read_bytes()
    require(len(files) == 7, "Source checkout must contain all seven skills.")
    files[local(root, ".quality/quality.pyz")] = bundle()
    for src, dest in (("docs/workflow.md", "WORKFLOW.md"), ("docs/policy.md", "POLICY.md"),
                      ("adapters/codex/AGENTS.md", "CODEX.md")):
        files[local(root, ".quality/" + dest)] = (SOURCE / src).read_bytes()
    # Codex can use the working interpreter even if "python" is a Store alias or only "python3" exists.
    interpreter = ("& '" + sys.executable.replace("'", "''") + "'" if os.name == "nt"
                   else shlex.quote(sys.executable))
    guidance_path = local(root, ".quality/CODEX.md")
    files[guidance_path] = files[guidance_path].replace(b"python -I ", (interpreter + " -I ").encode("utf-8"))
    config = local(root, ".quality/policy.json")
    if not config.exists():
        files[config] = (SOURCE / "quality/default-policy.json").read_bytes()
    else:
        require(config.is_file(), f"Expected a policy file at {config}")
        notes.append("Preserving project policy.")
    agents = local(root, "AGENTS.md")
    guidance = files[guidance_path]
    if agents.exists() and (not agents.is_file() or agents.read_bytes() != guidance):
        notes.append("Existing AGENTS.md preserved. To enable automatic routing, add a reference to .quality/CODEX.md.")
    else:
        files[agents] = guidance
    if (root / "AGENTS.override.md").exists():
        notes.append("AGENTS.override.md takes precedence. Include .quality/CODEX.md in the active guidance.")
    if hook:
        if hook_available():
            fragment = encoded(hook_settings(root))
            config_path = local(root, ".codex/hooks.json")
            if config_path.exists() and (not config_path.is_file() or config_path.read_bytes() != fragment):
                files[local(root, ".quality/stop-hook.fragment.json")] = fragment
                notes.append("Existing hooks preserved. Review .quality/stop-hook.fragment.json for a manual merge.")
            else:
                files[config_path] = fragment
                notes.append("Stop registration prepared. Review and trust the project hook in /hooks.")
            notes.append(f"Hook invokes {sys.executable} -I -S {SOURCE / 'adapters/codex/stop.py'} for {root}.")
        else:
            notes.append("FAIL-OPEN: enabled native hooks could not be confirmed. Use explicit verify.")
    else:
        notes.append("Explicit verification available. Optional Stop hook was not requested.")

    def missing():
        todo = []
        conflicts = []
        for path, data in files.items():
            if not path.exists():
                todo.append((path, data))
            elif not path.is_file() or path.read_bytes() != data:
                conflicts.append(str(path))
        require(not conflicts, "Install conflict; existing files preserved. Inspect these paths:\n" + "\n".join(conflicts))
        return todo

    todo = missing()
    if todo and not dry_run:
        with lock(root):
            todo = missing()
            for path, data in todo:
                put(path, data, exclusive=True)
    return {"status": "preview" if dry_run else "installed", "project": str(root),
            "created" if not dry_run else "would_create": [str(path) for path, _ in todo], "notes": notes}
