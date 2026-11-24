"""Create-only installation for Codex CLI and Claude Code."""
import io
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import zipfile

from .common import encoded, identifier, linked, local, lock, put, require

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


def hook_available(client="codex"):
    binary = shutil.which(client)
    if not binary:
        return False
    try:
        flags = ["features", "list"] if client == "codex" else ["--version"]
        proc = subprocess.run([binary, *flags], stdin=subprocess.DEVNULL, capture_output=True,
                              timeout=12, cwd=SOURCE, text=True, errors="replace")
        if client == "claude":
            return proc.returncode == 0 and "(Claude Code)" in proc.stdout
        return proc.returncode == 0 and any(line.split()[:1] in (["hooks"], ["codex_hooks"])
                                             and line.split()[-1:] == ["true"]
                                             for line in proc.stdout.splitlines())
    except (OSError, subprocess.TimeoutExpired):
        return False


def powershell_command(args):
    return "& " + " ".join("'" + arg.replace("'", "''") + "'" for arg in args)


def hook_settings(root, client="codex"):
    script = SOURCE / "adapters" / ("codex/stop.py" if client == "codex" else "stop.py")
    args = [sys.executable, "-I", "-S", str(script), str(root)]
    command = powershell_command(args) if os.name == "nt" else shlex.join(args)
    handler = {"type": "command", "command": command, "timeout": 5,
               "statusMessage": "Checking the recorded task verification"}
    if os.name == "nt" and client == "codex":
        handler["commandWindows"] = command
    elif os.name == "nt":
        handler["shell"] = "powershell"
    return {"hooks": {"Stop": [{"hooks": [handler]}]}}


def skill_directory(root, client, personal):
    base = Path.home().resolve() if personal else root
    if personal and client == "claude" and os.environ.get("CLAUDE_CONFIG_DIR"):
        base = Path(os.environ["CLAUDE_CONFIG_DIR"]).expanduser().absolute()
        require(all(not linked(p) for p in (base, *base.parents)), f"Linked Claude config path: {base}")
        return local(base, "skills")
    return local(base, ".agents/skills" if client == "codex" else ".claude/skills")


def add_guidance(files, notes, root, client):
    codex = client == "codex"
    name = "AGENTS.md" if codex else "CLAUDE.md"
    guide = ".quality/CODEX.md" if codex else ".quality/CLAUDE.md"
    template = (SOURCE / "adapters" / client / name).read_bytes()
    if codex:
        interpreter = powershell_command([sys.executable]) if os.name == "nt" else shlex.quote(sys.executable)
        content = template.replace(b"python -I ", (interpreter + " -I ").encode("utf-8"))
    else:
        args = ["-I", ".quality/quality.pyz"]
        bash = shlex.join([Path(sys.executable).as_posix(), *args])
        commands = f"- Bash: `{bash}` followed by the subcommand."
        if os.name == "nt":
            commands += f"\n- PowerShell: `{powershell_command([sys.executable, *args])}` followed by the subcommand."
        content = template.replace(b"{{HARNESS_COMMANDS}}", commands.encode("utf-8"))
    files[local(root, guide)] = content
    instructions = local(root, name)
    body = content
    if not codex:
        if not instructions.exists() and (root / ".claude/CLAUDE.md").is_file():
            notes.append("Existing .claude/CLAUDE.md preserved. For automatic routing, add @../.quality/CLAUDE.md there.")
            return
        # Creating CLAUDE.md changes Claude's default AGENTS.md discovery.
        imports = []
        for rel in ("AGENTS.md", ".claude/AGENTS.md"):
            path = root / rel
            if path in files or (path.is_file() and not linked(path) and not linked(path.parent)):
                imports.append(f"@{rel}\n")
        imports.append(f"@{guide}\n")
        body = "".join(imports).encode("utf-8")
    if instructions.exists() and (not instructions.is_file() or instructions.read_bytes() != body):
        directive = f"a reference to {guide}" if codex else f"the import @{guide}"
        notes.append(f"Existing {name} preserved. For automatic routing, include {directive} in the active guidance.")
    else:
        files[instructions] = body
    if codex and (root / "AGENTS.override.md").exists():
        notes.append("AGENTS.override.md takes precedence. Include .quality/CODEX.md in the active guidance.")


def add_hook(files, notes, root, client):
    if not hook_available(client):
        notes.append(f"FAIL-OPEN ({client}): native hook setup unavailable. Use explicit verify.")
        return
    if client == "codex":
        dest, fragment = ".codex/hooks.json", ".quality/stop-hook.fragment.json"
    else:
        dest, fragment = ".claude/settings.local.json", ".quality/claude-stop-hook.fragment.json"
    config = local(root, dest)
    data = encoded(hook_settings(root, client))
    if config.exists() and (not config.is_file() or config.read_bytes() != data):
        files[local(root, fragment)] = data
        notes.append(f"Existing {dest} preserved. Review {fragment} for a manual merge.")
    else:
        files[config] = data
        notes.append(f"{client}: review {dest} and confirm the project Stop hook in /hooks.")


def install(root, user_skills=False, hook=False, dry_run=False, client="codex"):
    require((SOURCE / "skills").is_dir(), "Run install using harness.py in the source checkout.")
    require(root.is_dir(), f"Create the project directory first: {root}")
    require(client in ("codex", "claude", "both"), "Unknown client.")
    clients = ("codex", "claude") if client == "both" else (client,)
    files = {}
    notes = []
    skills = sorted((SOURCE / "skills").glob("*/SKILL.md"))
    require(len(skills) == 7, "Source checkout must contain all seven skills.")
    for selected in clients:
        skill_root = skill_directory(root, selected, user_skills)
        for path in skills:
            name = identifier(path.parent.name)
            files[local(skill_root, f"{name}/SKILL.md")] = path.read_bytes()
        add_guidance(files, notes, root, selected)
        if hook:
            add_hook(files, notes, root, selected)
    if not hook:
        notes.append("Explicit verification available. Optional Stop hook was not requested.")
    files[local(root, ".quality/quality.pyz")] = bundle()
    for src, dest in (("docs/workflow.md", "WORKFLOW.md"), ("docs/policy.md", "POLICY.md"),
                      ("docs/references.md", "REFERENCES.md")):
        files[local(root, ".quality/" + dest)] = (SOURCE / src).read_bytes()
    config = local(root, ".quality/policy.json")
    if not config.exists():
        files[config] = (SOURCE / "quality/default-policy.json").read_bytes()
    else:
        require(config.is_file(), f"Expected a policy file at {config}")
        notes.append("Preserving project policy.")

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
