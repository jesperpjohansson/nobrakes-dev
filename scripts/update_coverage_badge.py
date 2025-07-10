import json
from pathlib import Path
import re
import sys


def _print(*values: object, **kwargs) -> None:
    print("[scripts.update_coverage_badge]", *values, **kwargs, flush=True)


COVREPORT_PATH = Path(__file__).parents[1] / "coverage.json"
README_PATH = Path(__file__).parents[1] / "README.md"

# Regular expression matching the coverage badge in README.md
COVERAGE_BADGE_RE = r"(?<=\[\!\[Coverage\]\()[^)]*(?=\)\])"

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

color = "brightgreen" if pct == 100 else "yellow" if pct >= 90 else "red"
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
