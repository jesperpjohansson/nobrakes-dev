"""
Produce a coverage report.

This script silently runs the test suite and write a coverage report to
the projects root directory.

Intended Use Cases
------------------
- Local development.
- CI workflows.

Positional Arguments
--------------------
type : {"term-missing", "json", "html"}
    Coverage report type.

Usage
-----
python -m scripts.update_coverage_badge TYPE

Notes
-----
If the selected report type is `json`, the output is reformatted with indentation
for improved readability.

"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from scripts._utils import check_dependencies_installed


def _print(*values: object, **kwargs) -> None:
    print("[scripts.update_coverage_badge]", *values, **kwargs, flush=True)


REPORT_TYPES = ["term-missing", "json", "html"]
REPORT_PATHS = [".coverage", "coverage.json", "htmlcov"]
REPORT_TYPE_TO_PATH = dict(zip(REPORT_TYPES, REPORT_PATHS, strict=False))

parser = argparse.ArgumentParser()
parser.add_argument("type", choices=REPORT_TYPES, help="report type")
args = parser.parse_args()

check_dependencies_installed("covreport")

_print(f"running tests and saving {args.type} report")

code = subprocess.run(
    ["pytest", "--cov=nobrakes", f"--cov-report={args.type}"],
    check=False,
    capture_output=True,
).returncode

if code > 0:
    sys.exit(code)

path = Path(__file__).parents[1] / REPORT_TYPE_TO_PATH[args.type]

# Indentation is added to json reports to increase readability
if args.type == "json":
    with path.open("r", encoding="utf-8") as stream:
        covreport = json.load(stream)

    with path.open("w", encoding="utf-8") as stream:
        json.dump(covreport, stream, ensure_ascii=False, indent=4)

_print(f"report saved: {path}")
