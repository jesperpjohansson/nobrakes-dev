"""
Update the Python version badge in README.md.

This script parses the `requires-python` field from `pyproject.toml` and updates the
Python version badge in `README.md` accordingly.

Intended Use Cases
------------------
- GitHub workflows

Usage
-----
python -m scripts.update_python_badge

Notes
-----
This script assumes that `requires-python` uses minor versions only, with an inclusive
lower bound (`>=`) and a non-inclusive upper bound (`<`), e.g., `>=3.8,<3.12`.
"""

from collections import UserString
from pathlib import Path
import re
import sys
import tomllib

from scripts._utils import print_func_factory

README_PATH = Path(__file__).parents[1] / "README.md"
PYPROJECT_PATH = Path(__file__).parents[1] / "pyproject.toml"

REQUIRES_PYTHON_RE = re.compile(r">=3\.[0-9]+,<3\.[0-9]+")
SPECIFIER_RE = re.compile(r"(?P<operator>>=|<)(?P<version>3\.[0-9]+)")
MINOR_VERSION_RE = re.compile(r"(?<=3\.)[0-9]+")

PYTHON_BADGE_RE = r"(?<=\[\!\[Python\]\()[^)]*(?=\)\])"
BADGE_URL_TEMPLATE = "https://img.shields.io/badge/python-{}-blue.svg"


class Version(UserString):
    """Light wrapper to compare Python versions like '3.10' and '3.8'."""

    @property
    def minor(self) -> int:
        return int(self.data.split(".")[1])

    def __lt__(self, other: str | UserString, /) -> bool:
        other_data = other if isinstance(other, str) else other.data
        return self.minor < Version(other_data).minor


_print = print_func_factory("update_python_badge")


def load_files() -> tuple[str, dict]:
    readme = README_PATH.read_text(encoding="utf-8")
    with PYPROJECT_PATH.open("rb") as stream:
        pyproject = tomllib.load(stream)

    return readme, pyproject


def get_requires_python(pyproject: dict) -> str:
    project_table = pyproject.get("project")
    if not isinstance(project_table, dict):
        _print("missing expected key 'project' in pyproject.json")
        sys.exit(1)

    requires_python = project_table.get("requires-python")
    if not isinstance(requires_python, str):
        _print("missing expected key 'requires-python' in 'project'")
        sys.exit(1)

    if not REQUIRES_PYTHON_RE.match(requires_python):
        _print("'requires-python' does not match regular expression")
        sys.exit(1)

    return requires_python


def generate_badge_url(requires_python: str) -> str:
    minor_versions_bounds = map(int, MINOR_VERSION_RE.findall(requires_python))
    versions = (f"3.{mv}" for mv in range(*minor_versions_bounds))
    return BADGE_URL_TEMPLATE.format("%20%7C%20".join(versions))  # " | " encoded


def get_old_badge_url(readme: str) -> str:
    m = re.search(PYTHON_BADGE_RE, readme)
    if not m:
        _print("did not find python badge in README.md")
        sys.exit(1)

    return m.group()


if __name__ == "__main__":
    readme, pyproject = load_files()
    requires_python = get_requires_python(pyproject)
    new_badge_url = generate_badge_url(requires_python)
    old_badge_url = get_old_badge_url(readme)

    if new_badge_url == old_badge_url:
        _print("version metadata has not changed")
        sys.exit(0)

    readme = readme.replace(old_badge_url, new_badge_url, 1)
    README_PATH.write_text(readme, encoding="utf-8")
    _print(f"new badge url: {new_badge_url}")
