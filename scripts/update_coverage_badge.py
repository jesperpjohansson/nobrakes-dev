from pathlib import Path
import json
import sys
import re

COVREPORT_PATH = Path(__file__).parents[1] / "coverage.json"
README_PATH = Path(__file__).parents[1] / "README.md"

# Regular expression matching the coverage badge in README.md
COVERAGE_BADGE_RE = r"(?<=\[\!\[Coverage\]\()[^)]*(?=\)\])"

def _print(*values, **kwargs):
    print("[scripts.update_coverage_badge]", *values, **kwargs, flush=True)

def extract_pct() -> float:
    """Extract total percentage covered from coverage.json."""

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
    
    return pct

def create_badge_url(pct: float) -> str:
    color = "brightgreen" if pct == 100 else "yellow" if pct >= 90 else "red"
    return f"https://img.shields.io/badge/coverage-{pct:.1f}%25-{color}"

def update_readme(badge_url: str) -> None:
    """Replace the coverage badge url in README.md."""
    readme = README_PATH.read_text(encoding="utf-8")
    match_ = re.search(COVERAGE_BADGE_RE, readme)
    if not match_:
        _print("did not find coverage badge in README.md")
        sys.exit(1)
    
    span = match_.span()
    new_readme = readme[:span[0]] + badge_url + readme[span[1]:]

    README_PATH.write_text(new_readme, encoding="utf-8")
    _print(f"new badge: {badge_url}")

pct = extract_pct()
badge_url = create_badge_url(pct)
update_readme(badge_url)
