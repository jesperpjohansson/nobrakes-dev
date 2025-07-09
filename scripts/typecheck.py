import subprocess
import sys

from scripts._utils import check_dependencies_installed


check_dependencies_installed("lint")

code = subprocess.run(
    [sys.executable, "-m", "mypy", "nobrakes"], check=False
).returncode
sys.exit(code)
