from collections import UserString
from pathlib import Path
import re
import sys
import tomllib

SUPPORTED_OPERATORS = {">=", "<"}
BADGE_URL_TEMPLATE = "https://img.shields.io/badge/python-{}-blue.svg"
MINOR_VERSION_RE = re.compile(r"^3\.[0-9]+$")
SPECIFIER_RE = re.compile(r"(?P<operator>>=|<)(?P<version>3\.[0-9]+)")
PYTHON_BADGE_RE = r"(?<=\[\!\[Python\]\()[^)]*(?=\)\])"
README_PATH = Path(__file__).parents[1] / "README.md"
PYPROJECT_PATH = Path(__file__).parents[1] / "pyproject.toml"


class Version(UserString):
    """Light wrapper to compare Python versions like '3.10' and '3.8'."""

    @property
    def minor(self) -> int:
        return int(self.data.split(".")[1])

    def __lt__(self, other: str | UserString, /) -> bool:
        other_data = other if isinstance(other, str) else other.data
        return self.minor < Version(other_data).minor


def _print(*values, **kwargs):
    print("[scripts.update_python_badge]", *values, **kwargs, flush=True)


def load_files():
    readme = README_PATH.read_text(encoding="utf-8")
    with PYPROJECT_PATH.open("rb") as stream:
        pyproject = tomllib.load(stream)

    return readme, pyproject


def get_requires_python(pyproject):
    project_table = pyproject.get("project")
    if not isinstance(project_table, dict):
        _print("missing expected key 'project' in pyproject.json")
        sys.exit(1)

    requires_python = project_table.get("requires-python")
    if not isinstance(requires_python, str):
        _print("missing expected key 'requires-python' in 'project'")
        sys.exit(1)

    return requires_python


def parse_specifiers(requires_python: str) -> list[dict[str, str]]:
    specifiers = []
    for part in requires_python.replace(" ", "").split(","):
        match = SPECIFIER_RE.fullmatch(part)
        if not match:
            _print(f"Invalid specifier: {part}")
            sys.exit(1)

        operator, version = match.group("operator"), match.group("version")
        if operator not in SUPPORTED_OPERATORS:
            _print(f"Unsupported operator: {operator}")
            _print(f"Supported operators: {SUPPORTED_OPERATORS}")
            sys.exit(1)

        if not MINOR_VERSION_RE.match(version):
            _print(f"Unsupported version format: {version}")
            _print("Only minor versions like '3.8' or '3.12' are supported")
            sys.exit(1)

        specifiers.append({"operator": operator, "version": version})

    return specifiers


def generate_badge_url(specifiers: list[dict[str, str]]) -> str:
    if not 1 <= len(specifiers) <= 2:
        _print("Expected between 1 and 2 specifiers")
        sys.exit(1)

    if len(specifiers) == 1:
        spec = specifiers[0]
        if spec["operator"] != ">=":
            _print("Single specifier must use '>='")
            sys.exit(1)
        return BADGE_URL_TEMPLATE.format(f"{spec['version']}%2B")  # "+" encoded

    # Two-spec range: >= and <
    operators = {s["operator"] for s in specifiers}
    if operators != {">=", "<"}:
        _print("Expected a range using '>=' and '<'")
        sys.exit(1)

    sorted_specs = sorted(specifiers, key=lambda s: Version(s["version"]))
    vmin, vmax = (Version(s["version"]) for s in sorted_specs)
    versions = (f"3.{minor}" for minor in range(vmin.minor, vmax.minor))
    return BADGE_URL_TEMPLATE.format("%20%7C%20".join(versions))  # " | " encoded


def get_old_badge_url(readme):
    m = re.search(PYTHON_BADGE_RE, readme)
    if not m:
        _print("did not find python badge in README.md")
        sys.exit(1)

    return m.group()


if __name__ == "__main__":
    readme, pyproject = load_files()
    requires_python = get_requires_python(pyproject)
    specifiers = parse_specifiers(requires_python)
    new_badge_url = generate_badge_url(specifiers)
    old_badge_url = get_old_badge_url(readme)

    if new_badge_url == old_badge_url:
        _print("coverage has not changed")
        sys.exit(0)

    readme = readme.replace(old_badge_url, new_badge_url, 1)
    README_PATH.write_text(readme, encoding="utf-8")
    _print(f"new badge url: {new_badge_url}")
