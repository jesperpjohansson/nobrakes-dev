import argparse
import subprocess
import sys

from scripts._utils import check_dependencies_installed

check_dependencies_installed("lint")

TASKS = {
    "format diff": [sys.executable, "-m", "ruff", "format", "--diff"],
    "lint check": [sys.executable, "-m", "ruff", "check"],
}

PARSER = argparse.ArgumentParser()
PARSER.add_argument("--ff", action="store_true", help="fail fast")
ARGS = PARSER.parse_args()

failed = False
for task, cmd in TASKS.items():
    code = subprocess.run(cmd, check=False).returncode
    status = "OK" if code == 0 else "FAIL"
    print(f"[{task}] code {code} | status {status}", flush=True)

    if status == "FAIL" and not failed:
        failed = True
        if ARGS.ff:
            break

sys.exit(int(failed))
