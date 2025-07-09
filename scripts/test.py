import subprocess

from scripts._utils import check_dependencies_installed

check_dependencies_installed("test")

input_ = ["pytest", "tests"]

code = subprocess.run(input_, check=True)
