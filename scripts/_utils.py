import importlib.util
import sys
import re
from pathlib import Path

# Names of scripts that requires nobrakes
REQUIRES_NOBRAKES = frozenset(("covreport", "test"))

# Mapping of script name to requirements file name
REQUIREMENTS_FILE = {
    "covreport": "covreport.txt",
    "format": "lint.txt",
    "lint": "lint.txt",
    "test": "test.txt",
    "typecheck": "typecheck.txt"
}

# Absolute path to the requirements directory
REQUIREMENTS_DIR = Path(__file__).parents[1] / "requirements"

# Regular expression used when parsing requirements/*.txt files
DEPENDENCY_RE = re.compile(
    r"([\w\.-]+?)" # Distribution name
    r"\s*#\s*import:\s*"
    r"([\w\.-]+)"  # Import name
)

def _make_requirements_mapping(filename: str) -> dict[str, str]:
    """
    Extract and map aliases of all dependencies listed in requirements/`filename`.
    
    This function reads and parses a `.txt` file listing script dependencies. Each
    specified distribution name is assumed to be followed by a comment starting with
    `import:`, followed by the import name of the corresponding distribution,
    for example: `my-package # import: my_package`.
    """
    with (REQUIREMENTS_DIR / filename).open("r", encoding="utf-8") as stream:
        return dict(m.groups() for line in stream if (m := DEPENDENCY_RE.match(line)))


def check_dependencies_installed(script_name: str):
    """Exit with code 1 if not all required dependencies are installed."""
    requirements = _make_requirements_mapping(REQUIREMENTS_FILE[script_name])
    if script_name in REQUIRES_NOBRAKES:
        requirements["nobrakes"] = "nobrakes"

    missing = tuple(
        distribution_name
        for distribution_name, import_name in requirements.items()
        if not importlib.util.find_spec(import_name)
    )
    if missing:
        print(
            f"[scripts.{script_name}] missing requirements: {', '.join(missing)}"
            f"\ninstall: python -m pip install -e .[dev]",
            flush=True,
        )
        sys.exit(1)