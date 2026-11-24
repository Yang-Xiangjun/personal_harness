"""Task contracts, plan coverage and a write-once snapshot of protected inputs."""
import fnmatch
import os
from pathlib import Path
import tempfile

from .common import (Problem, artifact, digest, encoded, fingerprint, identifier, linked,
                     local, object_at, put, require, timestamp, words)

IGNORED_DIRS = {".git", ".quality", ".agents", ".codex", ".claude", "__pycache__", ".venv", "venv",
                "node_modules", ".tox", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


class Task:
    def __init__(self, root, name):
        self.root = root
        self.name = identifier(name)
        self.rel = f".quality/tasks/{self.name}"
        self.folder = local(root, self.rel)

    def path(self, name):
        return local(self.root, f"{self.rel}/{name}")


def create(task, mode, objective, p):
    require(words(objective), "Supply a nonempty objective.")
    require(mode in p["modes"], f"Unknown mode: {mode}")
    require(not task.folder.exists(), f"Task already exists: {task.name}")
    parent = task.folder.parent
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent) as temp:
        staging = Path(temp) / "task"
        contract = {"version": 1, "id": task.name, "mode": mode, "objective": objective,
                    "deliverables": [], "criteria": []}
        put(staging / "contract.json", encoded(contract))
        if p["modes"][mode]["spec"]:
            put(staging / "spec.md", b"")
        if p["modes"][mode]["plan"]:
            put(staging / "plan.json", encoded({"steps": [], "negative_case": "", "recovery": ""}))
        staging.rename(task.folder)


def contract(task, p):
    c = object_at(task.path("contract.json"))
    require(c.get("version") == 1 and c.get("id") == task.name, "Task version or ID mismatch.")
    require(isinstance(c.get("mode"), str) and c["mode"] in p["modes"], "Unknown route.")
    require(words(c.get("objective")), "Missing objective.")
    paths = c.get("deliverables")
    require(isinstance(paths, list) and paths, "List at least one deliverable file.")
    for item in paths:
        artifact(task.root, item)
    require(len(paths) == len(set(paths)), "Duplicate deliverable.")
    criteria = c.get("criteria")
    require(isinstance(criteria, list) and criteria, "Define at least one acceptance criterion.")
    seen = set()
    for ac in criteria:
        require(isinstance(ac, dict) and words(ac.get("expect")), "Each criterion needs an expectation.")
        key = identifier(ac.get("id"))
        require(key not in seen, f"Duplicate criterion: {key}")
        seen.add(key)
        check = ac.get("check")
        require(isinstance(check, dict), f"Missing check for {key}")
        kind = check.get("kind")
        if kind in ("text-equals", "text-contains"):
            require(set(check) == {"kind", "path", "text"} and isinstance(check["text"], str),
                    f"Invalid text check for {key}")
            require(kind == "text-equals" or check["text"].strip(), f"Empty substring for {key}")
            artifact(task.root, check["path"])
        elif kind == "command":
            require(set(check) == {"kind", "name"} and isinstance(check["name"], str)
                    and check["name"] in p["commands"], f"Unknown or unapproved command for {key}")
        else:
            raise Problem(f"Unsupported check for {key}: {kind}")
    return c


def plan_inputs(task, p):
    c = contract(task, p)
    rules = p["modes"][c["mode"]]
    inputs = {"contract.json": fingerprint(task.path("contract.json")),
              "policy.json": fingerprint(local(task.root, ".quality/policy.json"))}
    if rules["spec"]:
        spec = task.path("spec.md")
        require(spec.is_file() and spec.read_text(encoding="utf-8-sig").strip(), "Write the persistent spec.md.")
        inputs["spec.md"] = fingerprint(spec)
    if rules["plan"]:
        path = task.path("plan.json")
        plan = object_at(path)
        steps = plan.get("steps")
        require(isinstance(steps, list) and steps, "The plan needs ordered steps.")
        required = {ac["id"] for ac in c["criteria"]}
        covered = set()
        step_ids = set()
        for step in steps:
            require(isinstance(step, dict) and words(step.get("action")) and words(step.get("verify")),
                    "Each plan step needs an action and an observable verification.")
            key = identifier(step.get("id"))
            require(key not in step_ids, f"Duplicate plan step: {key}")
            step_ids.add(key)
            refs = step.get("criteria")
            require(isinstance(refs, list) and refs and all(isinstance(v, str) and v in required for v in refs),
                    f"Missing or unknown criterion in {key}")
            covered.update(refs)
            files = step.get("files")
            require(isinstance(files, list) and files, f"Name files touched in {key}")
            for file in files:
                artifact(task.root, file)
        require(covered == required, f"Plan misses criteria: {', '.join(sorted(required - covered))}")
        if c["mode"] == "high":
            require(words(plan.get("negative_case")) and words(plan.get("recovery")),
                    "High assurance needs a negative case and a recovery procedure.")
        inputs["plan.json"] = fingerprint(path)
    return c, inputs


def review(task, p, source, by, ref, note, verdict, reviewed_hash):
    require(not task.path("seal.json").exists(), "This task is sealed.")
    c, inputs = plan_inputs(task, p)
    require(p["modes"][c["mode"]]["review"], "This route does not require a review.")
    require(all(words(s) for s in (by, ref, note)), "Record reviewer, source reference and rationale.")
    require(reviewed_hash == digest(encoded(inputs)),
            "Review is stale. Provide the inputs_sha256 the reviewer actually checked.")
    record = {"source": source, "reviewer": by, "reference": ref, "note": note, "verdict": verdict,
              "inputs_sha256": reviewed_hash, "recorded_at": timestamp()}
    put(task.path("review.json"), encoded(record))


def protected_files(root, patterns):
    result = {}

    def failed(error):
        raise error

    for directory, dirs, files in os.walk(root, followlinks=False, onerror=failed):
        parent = Path(directory)
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for name in dirs:
            require(not linked(parent / name), f"Cannot inventory linked directory: {parent / name}")
        for name in files:
            path = parent / name
            relative = path.relative_to(root).as_posix()
            if any(fnmatch.fnmatchcase(relative.casefold(), g.casefold()) for g in patterns):
                require(not linked(path) and path.is_file(), f"Unsupported protected file: {relative}")
                result[relative] = fingerprint(path)
    return result


def snapshot(task, p):
    c, inputs = plan_inputs(task, p)
    if p["modes"][c["mode"]]["review"]:
        path = task.path("review.json")
        r = object_at(path)
        require(r.get("verdict") == "pass" and r.get("source") in ("human", "separate-session")
                and all(words(r.get(k)) for k in ("reviewer", "reference", "note")),
                "An independent passing review is required.")
        require(r.get("inputs_sha256") == digest(encoded(inputs)), "Review is stale. Review the revised plan inputs.")
        inputs["review.json"] = fingerprint(path)
    return {"inputs": inputs, "protected": protected_files(task.root, p["protected_globs"])}


def seal(task, p):
    path = task.path("seal.json")
    require(not path.exists(), "A baseline already exists. Use a new task ID for an authorized revision.")
    record = snapshot(task, p)
    put(path, encoded({"version": 1, "task": task.name, "created_at": timestamp(), **record}), exclusive=True)
    return record


def check_seal(task, p):
    sealed = object_at(task.path("seal.json"))
    require(sealed.get("version") == 1 and sealed.get("task") == task.name, "Invalid seal.")
    current = snapshot(task, p)
    for label, values in current.items():
        before = sealed.get(label)
        require(isinstance(before, dict), f"Invalid {label} baseline.")
        changed = sorted(k for k in set(before) | set(values) if before.get(k) != values.get(k))
        require(not changed, f"Changed {label}: {', '.join(changed)}")
    return fingerprint(task.path("seal.json"))
