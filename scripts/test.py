import argparse
import subprocess
import sys

from scripts._utils import check_dependencies_installed

PARSER = argparse.ArgumentParser()
PARSER.add_argument(
    "-o",
    "--opargs",
    nargs="+",
    help='optional pytest args, without the "--" prefix',
    default=(),
)
ARGS = PARSER.parse_args()

dependencies = {
    "nobrakes": "nobrakes",
    "pytest": "pytest",
    "pytest-asyncio": "pytest_asyncio",
    "aiohttp": "aiohttp",
    "httpx": "httpx",
    "pyyaml": "yaml",
}

if any(str.startswith(arg, "cov") for arg in ARGS.opargs):
    dependencies |= {"pytest-cov": "pytest_cov"}

check_dependencies_installed("test", dependencies)

input_ = ["pytest", "tests"]

if ARGS.opargs:
    input_.extend("--" + arg for arg in ARGS.opargs)

code = subprocess.run(input_, check=False).returncode
sys.exit(code)
