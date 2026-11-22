"""Filesystem and policy primitives shared by the CLI and adapter."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile


class Problem(ValueError):
    """A validation failure suitable for display to the task owner."""


def require(condition, message):
    if not condition:
        raise Problem(message)


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(131072), b""):
            h.update(block)
    return h.hexdigest()


def encoded(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read(path):
    require(path.is_file(), f"Missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_keys)


def object_at(path):
    value = read(path)
    require(isinstance(value, dict), f"Expected an object in {path}")
    return value


def words(value):
    return isinstance(value, str) and bool(value.strip())


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", value),
            f"Expected a lowercase identifier (1-64 letters, digits or hyphens): {value!r}")
    return value


def linked(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0)
                                              & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def local(root, relative):
    """Reject links (including broken links/junctions), drives, streams and traversal."""
    require(words(relative) and "\\" not in relative, f"Use a relative forward-slash path: {relative!r}")
    current = root
    for part in relative.split("/"):
        device_name = part.partition(".")[0].rstrip(" ").upper()
        require(part not in ("", ".", "..") and not part.endswith((".", " "))
                and not re.search(r'[<>:"|?*\x00-\x1f]', part)
                and not re.fullmatch(r"(CON|AUX|NUL|PRN|CONIN\$|CONOUT\$|(?:COM|LPT)[1-9¹²³])", device_name),
                f"Unsafe path: {relative!r}")
        current = current / part
        require(not linked(current), f"Linked paths are unsupported: {current}")
    return current


def artifact(root, relative):
    path = local(root, relative)
    require(relative.split("/")[0].lower() not in (".quality", ".git", ".codex", ".agents"),
            "Deliverables and check inputs must be outside harness and agent metadata.")
    return path


def put(path, data, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    if exclusive:
        with path.open("xb") as stream:
            stream.write(data)
        return
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temp = Path(stream.name)
        try:
            stream.write(data)
        except BaseException:
            stream.close()
            temp.unlink(missing_ok=True)
            raise
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


@contextmanager
def lock(root):
    path = local(root, ".quality/busy.lock")
    try:
        put(path, f"pid={os.getpid()}\n".encode(), exclusive=True)
    except FileExistsError:
        raise Problem(f"Another harness operation holds {path}. See recovery in the README.") from None
    try:
        yield
    finally:
        path.unlink()


def policy(root):
    p = object_at(local(root, ".quality/policy.json"))
    require(p.get("version") == 1, "Unsupported policy version.")
    modes = p.get("modes")
    require(isinstance(modes, dict) and set(modes) == {"fast", "standard", "high"}
            and isinstance(p.get("default_mode"), str) and p["default_mode"] in modes, "Invalid modes.")
    for rules in modes.values():
        require(isinstance(rules, dict) and set(rules) == {"spec", "plan", "review"}
                and all(type(v) is bool for v in rules.values())
                and (not rules["review"] or rules["plan"]), "Invalid mode rules.")
    require(type(p.get("timeout_seconds")) is int and 1 <= p["timeout_seconds"] <= 600,
            "timeout_seconds must be 1-600.")
    require(type(p.get("max_repair_attempts")) is int and 0 <= p["max_repair_attempts"] <= 10,
            "max_repair_attempts must be 0-10.")
    globs = p.get("protected_globs")
    require(isinstance(globs, list) and globs and all(words(g) for g in globs), "Invalid protected_globs.")
    commands = p.get("commands")
    require(isinstance(commands, dict), "commands must map names to argument arrays.")
    for name, argv in commands.items():
        identifier(name)
        require(isinstance(argv, list) and argv and all(words(v) for v in argv),
                f"Invalid argument array for {name}")
        require(argv[0] == "{python}" or Path(argv[0]).is_absolute(),
                f"Use an absolute executable or {{python}} for {name}.")
        require(Path(argv[0]).suffix.lower() not in (".bat", ".cmd"), "Batch wrappers are unsupported.")
    return p
