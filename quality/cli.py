"""Command-line interface shared by the source checkout and installed zip application."""
import argparse
import json
import os
from pathlib import Path
import sys

from .common import digest, encoded, local, lock, policy, put, require, words
from .tasks import Task, create, plan_inputs, review, seal
from .verify import verify


def parser():
    cli = argparse.ArgumentParser(description="Personal quality harness for Codex CLI")
    cmds = cli.add_subparsers(dest="command", required=True)

    def add(name, help_text, task=False):
        sub = cmds.add_parser(name, help=help_text)
        sub.add_argument("--project", default=".", type=Path, help="target project root (default: current directory)")
        if task:
            sub.add_argument("task", help="task ID, lowercase letters, digits and hyphens")
        return sub

    ins = add("install", "install or preview a create-only project integration from the source checkout")
    ins.add_argument("--user-skills", action="store_true", help="install skills under ~/.agents/skills")
    ins.add_argument("--hook", action="store_true", help="probe for an optional project Stop hook")
    ins.add_argument("--dry-run", action="store_true", help="report destinations without writing")
    new = add("new", "create a task contract and route-specific drafts", True)
    new.add_argument("--mode", choices=("fast", "standard", "high"))
    new.add_argument("--objective", required=True)
    add("plan-check", "validate the contract, spec and plan coverage", True)
    rev = add("review", "record an actual independent review tied to current inputs", True)
    rev.add_argument("--source", required=True, choices=("human", "separate-session"))
    rev.add_argument("--by", required=True)
    rev.add_argument("--ref", required=True, help="review session ID or human review reference")
    rev.add_argument("--note", required=True, help="reviewer's findings and reasoning")
    rev.add_argument("--verdict", required=True, choices=("pass", "changes"))
    rev.add_argument("--inputs-sha256", required=True, help="inputs_sha256 returned by the reviewer's plan-check")
    add("seal", "freeze acceptance inputs and protected files before implementation", True)
    ver = add("verify", "run checks now and write a fresh evidence.json", True)
    ver.add_argument("--include-output", action="store_true", help="include the last 2048 command-output bytes")
    watch = add("watch", "bind an existing task to the optional Stop reminder for this session", True)
    watch.add_argument("--session", default=os.environ.get("CODEX_THREAD_ID"))
    off = add("unwatch", "detach the session's Stop reminder")
    off.add_argument("--session", default=os.environ.get("CODEX_THREAD_ID"))
    return cli


def run(args):
    root = Path(args.project).resolve(strict=True)
    require(root.is_dir(), "Project must be a directory.")
    if args.command == "install":
        from .install import install
        return install(root, args.user_skills, args.hook, args.dry_run), 0
    require(local(root, ".quality").is_dir(), "Install the project integration first.")
    task = Task(root, args.task) if hasattr(args, "task") else None
    with lock(root):
        if args.command == "verify":
            r = verify(task, args.include_output)
            return r, 0 if r["status"] == "pass" else 1
        if args.command in ("watch", "unwatch"):
            require(words(args.session), "Supply --session with the Codex session ID.")
            key = digest(args.session.encode())
            path = local(root, f".quality/sessions/{key}.json")
            if args.command == "unwatch":
                path.unlink(missing_ok=True)
                return {"watching": None}, 0
            require(task.path("contract.json").is_file(), "Unknown task.")
            put(path, encoded({"task": task.name}))
            return {"watching": task.name}, 0
        p = policy(root)
        if args.command == "new":
            mode = args.mode or p["default_mode"]
            create(task, mode, args.objective, p)
            return {"task": task.name, "mode": mode, "folder": str(task.folder)}, 0
        if args.command == "plan-check":
            c, inputs = plan_inputs(task, p)
            return {"status": "pass", "kind": "structural", "criteria": [a["id"] for a in c["criteria"]],
                    "inputs_sha256": digest(encoded(inputs))}, 0
        if args.command == "review":
            review(task, p, args.source, args.by, args.ref, args.note, args.verdict, args.inputs_sha256)
            return {"task": task.name, "review": args.verdict}, 0 if args.verdict == "pass" else 1
        record = seal(task, p)
        return {"task": task.name, "sealed": True, "protected_file_count": len(record["protected"])}, 0


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result, code = run(args)
    except (OSError, ValueError, RecursionError) as exc:
        result, code = {"status": "error", "issue": str(exc)}, 1
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return code
