"""Read-only Stop reminder for the common Codex and Claude Code JSON protocol."""
import hashlib
import json
from pathlib import Path
import re
import stat
import sys


def get(path):
    # Do not follow links to arbitrary JSON or read unbounded files on a Stop event.
    for part in (path, *path.parents):
        if part.is_symlink() or (getattr(part.lstat(), "st_file_attributes", 0)
                                 & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise ValueError("linked state")
    with path.open("rb") as stream:
        data = stream.read(262145)
    if len(data) > 262144:
        raise ValueError("oversized state")
    return json.loads(data)


def reply(event, project):
    if not isinstance(event, dict) or event.get("hook_event_name") != "Stop":
        return {}
    if event.get("stop_hook_active") is not False:
        return {}
    session = event.get("session_id")
    if not isinstance(session, str) or not session:
        return {}
    cwd = Path(event["cwd"]).resolve(strict=True)
    if not cwd.is_relative_to(project):
        return {}
    key = hashlib.sha256(session.encode()).hexdigest()
    binding = project / ".quality" / "sessions" / (key + ".json")
    if not binding.exists():
        return {}
    task = get(binding)["task"]
    if not isinstance(task, str) or not re.fullmatch("[a-z0-9][a-z0-9-]{0,63}", task):
        raise ValueError("invalid task")
    relative = f".quality/tasks/{task}/evidence.json"
    report = project / relative
    if not report.exists():
        reason = (f"No verification report exists for {task}. If the deliverable is ready, run "
                  f"`verify {task}` using the installed project instructions. Otherwise report what is outstanding.")
    else:
        data = get(report)
        if data.get("task") != task:
            raise ValueError("report belongs to another task")
        status = data.get("status")
        if status == "pass":
            return {}
        if status == "running":
            reason = (f"Verification for {task} is marked in progress. Check whether the run is still "
                      f"active and read {relative} when it finishes. If it was interrupted, report "
                      f"that or rerun `verify {task}` once the project is idle.")
        elif status == "fail":
            reason = (f"The last verification for {task} failed. Inspect the criteria and issues in "
                      f"{relative}. After an in-scope repair, run `verify {task}` again. If a blocker "
                      "remains, report the affected requirement.")
        else:
            raise ValueError("unknown verification status")
    # Both clients give the reason to the model. Only interpolate the validated task ID.
    return {"decision": "block", "reason": reason}


def main():
    try:
        data = sys.stdin.buffer.read(131073)
        if len(data) > 131072:
            raise ValueError("oversized event")
        result = reply(json.loads(data), Path(sys.argv[1]).resolve(strict=True))
    except Exception:
        result = {"systemMessage": "Quality reminder unavailable (fail-open). Use the explicit verify command."}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
