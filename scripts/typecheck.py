"""
Typecheck codebase.

This script runs static type analysis on python code in `nobrakes/` and `scripts/`.

Intended Use Cases
------------------
- Local development.
- CI workflows.

Usage
-----
python -m scripts.typecheck


"""
import subprocess
import sys

from scripts._utils import check_dependencies_installed

check_dependencies_installed("typecheck")

code = subprocess.run([sys.executable, "-m", "mypy"], check=False).returncode
sys.exit(code)
