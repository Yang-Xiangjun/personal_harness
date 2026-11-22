"""Produce a new criterion-by-criterion evidence report on every invocation."""
import hashlib
import os
import subprocess
import sys
import tempfile
import time
import uuid

from .common import (artifact, digest, encoded, fingerprint, policy,
                     put, require, timestamp)
from .tasks import check_seal, contract

ERRORS = (OSError, ValueError, UnicodeError, RecursionError)


def run_command(root, argv, timeout, include_output):
    args = [sys.executable if index == 0 and arg == "{python}" else arg
            for index, arg in enumerate(argv)]
    started = time.monotonic()
    with tempfile.TemporaryFile() as stream:
        result = {"argv": args, "exit_code": None, "timed_out": False}
        try:
            proc = subprocess.run(args, cwd=root, stdin=subprocess.DEVNULL, stdout=stream,
                                  stderr=subprocess.STDOUT, timeout=timeout, shell=False)
            result["exit_code"] = proc.returncode
        except subprocess.TimeoutExpired:
            result["timed_out"] = True
        except OSError as exc:
            result["error"] = str(exc)
        result["elapsed_seconds"] = round(time.monotonic() - started, 3)
        stream.seek(0, os.SEEK_END)
        result["output_bytes"] = stream.tell()
        stream.seek(0)
        h = hashlib.sha256()
        for block in iter(lambda: stream.read(131072), b""):
            h.update(block)
        result["output_sha256"] = h.hexdigest()
        if include_output:
            stream.seek(max(0, result["output_bytes"] - 2048))
            result["output_tail"] = stream.read(2048).decode("utf-8", errors="replace")
    return result["exit_code"] == 0, result


def file_evidence(root, name):
    file = artifact(root, name)
    require(file.is_file(), f"Missing deliverable: {name}")
    return {"path": name, "sha256": fingerprint(file), "bytes": file.stat().st_size}


def run_check(task, p, check, cache, include_output):
    if check["kind"] == "command":
        name = check["name"]
        if name not in cache:
            cache[name] = run_command(task.root, p["commands"][name], p["timeout_seconds"], include_output)
        ok, details = cache[name]
        return ok, {"kind": "command", "name": name, **details}
    path = artifact(task.root, check["path"])
    require(path.is_file(), f"Missing text file: {check['path']}")
    with path.open("rb") as stream:
        raw = stream.read(8 * 1024 * 1024 + 1)
    require(len(raw) <= 8 * 1024 * 1024, "Text check exceeds 8 MiB. Register a streaming validator.")
    # Make text checks portable between CRLF and LF while hashing the original bytes.
    value = raw.decode("utf-8-sig").replace("\r\n", "\n")
    expected = check["text"].replace("\r\n", "\n")
    ok = value == expected if check["kind"] == "text-equals" else expected in value
    return ok, {"kind": check["kind"], "path": check["path"], "sha256": digest(raw),
                "bytes": len(raw), "matched": ok}


def verify(task, include_output=False):
    require(task.folder.is_dir(), f"Unknown task: {task.name}")
    path = task.path("evidence.json")
    report = {"version": 1, "task": task.name, "run_id": str(uuid.uuid4()), "started_at": timestamp(),
              "status": "running", "criteria": [], "deliverables": [], "issues": []}
    put(path, encoded(report))
    try:
        p = policy(task.root)
        c = contract(task, p)
        report["criteria"] = [{"id": ac["id"], "expect": ac["expect"], "status": "not-run"}
                              for ac in c["criteria"]]
        report["seal_sha256"] = check_seal(task, p)
        for name in c["deliverables"]:
            try:
                report["deliverables"].append(file_evidence(task.root, name))
            except ERRORS as exc:
                report["issues"].append(str(exc))
        cache = {}
        for ac, row in zip(c["criteria"], report["criteria"]):
            try:
                ok, row["evidence"] = run_check(task, p, ac["check"], cache, include_output)
                row["status"] = "pass" if ok else "fail"
            except ERRORS as exc:
                row.update(status="fail", error=str(exc))
        require(check_seal(task, policy(task.root)) == report["seal_sha256"], "Seal changed during verification.")
        for item in report["deliverables"]:
            require(file_evidence(task.root, item["path"]) == item, f"Deliverable changed during checks: {item['path']}")
        for row in report["criteria"]:
            ev = row.get("evidence", {})
            if "path" in ev:
                require(file_evidence(task.root, ev["path"])["sha256"] == ev["sha256"],
                        f"Check input changed during verification: {ev['path']}")
    except ERRORS as exc:
        report["issues"].append(str(exc))
    complete = bool(report["criteria"]) and all(row["status"] == "pass" for row in report["criteria"])
    report["status"] = "pass" if complete and not report["issues"] else "fail"
    report["finished_at"] = timestamp()
    put(path, encoded(report))
    return report
