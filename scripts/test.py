import subprocess

from scripts._utils import check_dependencies_installed

check_dependencies_installed("test")
code = subprocess.run(["pytest"], check=True)
