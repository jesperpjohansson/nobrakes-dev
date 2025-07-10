"""
Update the coverage badge in README.md.

This script reads `coverage.json` to extract the total test coverage percentage.
If the percentage has changed, it updates the coverage badge in the `README.md` file.

Intended Use Cases
------------------
- GitHub workflows

Usage
-----
python -m scripts.update_coverage_badge

Notes
-----
This script assumes that `coverage.json` already exists.
"""

import json
from pathlib import Path
import re
import sys

from scripts._utils import print_func_factory

_print = print_func_factory("update_coverage_badge")

COVREPORT_PATH = Path(__file__).parents[1] / "coverage.json"
README_PATH = Path(__file__).parents[1] / "README.md"

# Regular expression matching the coverage badge in README.md
COVERAGE_BADGE_RE = r"(?<=\[\!\[Coverage\]\()[^)]*(?=\)\])"

# Threshold (cov %) and badge color
BADGE_COLOR = {100: "brightgreen", 90: "yellow", 0: "red"}

# Extract total percent covered from coverage.json

if not COVREPORT_PATH.is_file():
    _print("could not locate coverage.json")
    sys.exit(1)

with COVREPORT_PATH.open(encoding="utf-8") as stream:
    covreport: dict = json.load(stream)

totals = covreport.get("totals")
if not isinstance(totals, dict):
    _print("missing expected key 'totals' in coverage.json")
    sys.exit(1)

pct = totals.get("percent_covered")
if not isinstance(pct, float):
    _print("missing expected key 'percent_covered' in 'totals'")
    sys.exit(1)

# Make coverage badge url

color = BADGE_COLOR[max(threshold for threshold in BADGE_COLOR if pct >= threshold)]
new_badge_url = f"https://img.shields.io/badge/coverage-{pct:.1f}%25-{color}"

# Replace the coverage badge url in README.md

readme = README_PATH.read_text(encoding="utf-8")
match_ = re.search(COVERAGE_BADGE_RE, readme)

if not match_:
    _print("did not find coverage badge in README.md")
    sys.exit(1)

old_badge_url = match_.group()
if new_badge_url == old_badge_url:
    _print("coverage has not changed")
    sys.exit(0)

readme = readme.replace(old_badge_url, new_badge_url, count=1)
README_PATH.write_text(readme, encoding="utf-8")
_print(f"new badge url: {new_badge_url}")
