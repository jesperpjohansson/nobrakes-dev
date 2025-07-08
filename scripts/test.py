import subprocess

from scripts._utils import check_dependencies_installed

dependencies = {
    "nobrakes": "nobrakes",
    "pytest": "pytest",
    "pytest-asyncio": "pytest_asyncio",
    "aiohttp": "aiohttp",
    "httpx": "httpx",
    "pyyaml": "yaml",
}

check_dependencies_installed("test", dependencies)

input_ = ["pytest", "tests"]

code = subprocess.run(input_, check=True)
