import importlib.util
import sys


def check_dependencies_installed(script_name, dependencies):
    missing_dependencies = tuple(
        pkg_name
        for pkg_name, import_name in dependencies.items()
        if not importlib.util.find_spec(import_name)
    )
    if missing_dependencies:
        print(
            f"[scripts.{script_name}] missing dependencies: "
            f"{', '.join(missing_dependencies)}"
            f"\ninstall: python -m pip install -e .[dev]",
            flush=True,
        )
        sys.exit(1)
