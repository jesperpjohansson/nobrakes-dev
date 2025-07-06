import argparse
import subprocess
import sys

from scripts._utils import check_dependencies_installed

DEPENDENCIES = {
    "nobrakes": "nobrakes",
    "pytest": "pytest",
    "pytest-asyncio": "pytest_asyncio",
    "pytest-cov": "pytest_cov",
    "aiohttp": "aiohttp",
    "httpx": "httpx",
    "pyyaml": "yaml",
}

check_dependencies_installed("test", DEPENDENCIES)


parser = argparse.ArgumentParser()
parser.add_argument("-o", "--opargs", help="optional pytest args as a string")
args = parser.parse_args()

input_ = ["pytest", "tests"]

if args.opargs:
    input_.extend(args.opargs.split(" "))

code = subprocess.run(input_, check=False).returncode
sys.exit(code)
