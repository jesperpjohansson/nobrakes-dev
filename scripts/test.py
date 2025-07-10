"""
Run test suite.

This script executes the `tests/` test suite.

Intended Use Cases
------------------
- Local development.
- CI workflows.

Usage
-----
python -m scripts.test



Notes
-----
Before running, it checks that all necessary testing dependencies are installed.
"""
import subprocess

from scripts._utils import check_dependencies_installed

check_dependencies_installed("test")
code = subprocess.run(["pytest"], check=True)
