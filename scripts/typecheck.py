import subprocess
import sys

from scripts._utils import check_dependencies_installed

check_dependencies_installed("typecheck")

code = subprocess.run([sys.executable, "-m", "mypy"], check=False).returncode
sys.exit(code)
