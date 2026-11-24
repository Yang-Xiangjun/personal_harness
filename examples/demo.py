"""Run a red/green task in a NEW directory, or leave it ready for the selected client."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent


def cli(program, root, *args, expected=0):
    proc = subprocess.run([sys.executable, "-I", str(program), *args, "--project", str(root)],
                          capture_output=True, text=True)
    if proc.returncode != expected:
        raise SystemExit(f"Unexpected exit {proc.returncode} from {args}:\n{proc.stdout}\n{proc.stderr}")
    print(f"{args[0]}: exit {proc.returncode}")
    return json.loads(proc.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--client", choices=("codex", "claude", "both"), default="codex")
    parser.add_argument("--leave-broken", action="store_true")
    args = parser.parse_args()
    root = args.project.resolve()
    if root.exists():
        parser.error("Choose a new directory. Existing directories are preserved.")
    shutil.copytree(HERE / "clock", root, ignore=shutil.ignore_patterns("__pycache__"))
    # Source entrypoint imports its sibling package; isolated mode is for the installed zipapp.
    subprocess.run([sys.executable, str(SOURCE / "harness.py"), "install", "--client", args.client, "--project", str(root)],
                   check=True, stdout=subprocess.DEVNULL)
    tool = root / ".quality" / "quality.pyz"
    cfg = root / ".quality" / "policy.json"
    policy = json.loads(cfg.read_text(encoding="utf-8"))
    policy["commands"] = {
        "format-example": ["{python}", "-I", "tests/test_clock.py", "ClockLabelTests.test_minutes_and_seconds"],
        "clock-boundaries": ["{python}", "-I", "tests/test_clock.py", "ClockLabelTests.test_boundaries"],
    }
    cfg.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    task = "clock-label"
    folder = root / ".quality" / "tasks" / task
    cli(tool, root, "new", task, "--mode", "fast", "--objective", "Format elapsed seconds")
    shutil.copyfile(HERE / "clock-contract.json", folder / "contract.json")
    cli(tool, root, "plan-check", task)
    cli(tool, root, "seal", task)
    red = cli(tool, root, "verify", task, "--include-output", expected=1)
    if not all(c["status"] == "fail" and c["evidence"]["exit_code"] == 1 for c in red["criteria"]):
        raise SystemExit("The baseline must fail both behavior checks.")
    shutil.copyfile(folder / "evidence.json", folder / "baseline-failure.json")
    print("Broken formatter: " + ", ".join(c["id"] + "=" + c["status"] for c in red["criteria"]))
    if args.leave_broken:
        print(f"Prepared {root}. Open the selected client here and ask it to finish the sealed clock-label task.")
        return
    shutil.copyfile(HERE / "solution/clock_label.py", root / "clock_label.py")
    green = cli(tool, root, "verify", task)
    print("Corrected formatter: " + ", ".join(c["id"] + "=" + c["status"] for c in green["criteria"]))
    print(f"Reports: {folder / 'baseline-failure.json'} and {folder / 'evidence.json'}")


if __name__ == "__main__":
    main()
