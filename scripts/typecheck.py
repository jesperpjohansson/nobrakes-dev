import subprocess
import sys

from scripts._utils import check_dependencies_installed

DEPENDENCIES = {
    "mypy": "mypy",
    "aiohttp": "aiohttp",
    "httpx": "httpx",
    "lxml-stubs": "lxml-stubs",
}
check_dependencies_installed("lint", DEPENDENCIES)

code = subprocess.run(
    [sys.executable, "-m", "mypy", "nobrakes"], check=False
).returncode
sys.exit(code)
