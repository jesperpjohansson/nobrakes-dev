# Contributing

Thank you for your interest in contributing to `nobrakes`! We welcome contributions from the community and appreciate your help to make this project better.

## Code of Conduct

This project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). **By participating in this project you agree to abide by its terms**.

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub:

- Provide a clear and descriptive title.
- Describe the steps to reproduce the issue.
- Include any relevant code snippets or error messages.
- Mention your environment (Python version, OS, etc.).

## Submitting Pull Requests

1. **Create a new branch:**

    ```bash
    git checkout -b my-feature
    ```

2. **Make your changes**, ensuring you follow the project's [coding style](#quality-standards).

3. **Write tests** for your changes, if applicable.

4. **Run relevant [scripts](#quality-standards)** locally to verify everything works:

    ```bash
    pytest
    ```

5. **Commit your changes** with a clear message:

    ```bash
    git commit -m "Add feature X with Y"
    ```

6. **Push your branch** and open a Pull Request on GitHub.

## Quality Standards

The repository contains three packages with Python modules: `nobrakes`, `scripts`, and `tests`. 

All contributions must meet quality standards regarding [code](#code), [docstrings](#docstrings), [typing](#typing), and [testing](#testing). These are checked during CI. Configurations for the tools checking this can be found in `pyproject.toml`.

To make contributing as frictionless as possible, the repository provides a [scripts](https://github.com/jesperpjohansson/nobrakes-dev/tree/main/scripts) package containing OS-agnostic, standardized scripts for use in development and CI. You are encouraged to utilize these scripts to ensure your code meets all quality expectations.

```bash
# Run a script
python -m scripts.script_name
```

### Code

Code formatting and linting are [ruff](https://docs.astral.sh/ruff/)-based. As a starting point:

- Comply with [PEP8](https://peps.python.org/pep-0008/) but allow line lengths up to 88 characters.
- Run [scripts.format](scripts/format.py) to fix formatting issues and safely fixable lint rule violations.
- Run [scripts.lint](scripts/lint.py) to check for formatting issues and lint rule violations.

---
### Docstrings

Docstring linting is [ruff](https://docs.astral.sh/ruff/)-based. Run [scripts.lint](scripts/lint.py) to check for formatting issues and lint rule violations.

#### nobrakes

- Docstrings are mandatory for all code.
- Internal code demands less extensive documentation.
- Follow the [NumPy](https://numpydoc.readthedocs.io/en/latest/format.html) docstring convention.

#### scripts
- Module docstrings are mandatory.
- Any other docstrings are optional, but welcomed.
- Follow the [NumPy](https://numpydoc.readthedocs.io/en/latest/format.html) docstring convention.

#### tests
- Docstrings are optional, but welcomed.
- No docstring convention is enforced.

---
### Typing

Typechecking is [MyPy](https://mypy.readthedocs.io/en/stable/index.html)-based. Run [scripts.typecheck](scripts/typecheck.py) to check for typing related errors.

#### nobrakes

- `nobrakes` is a [py.typed](https://peps.python.org/pep-0561/) package.
- All types are to be defined in [nobrakes/typing/_typing.py](nobrakes/typing/_typing.py).
- Types that are exposed in the public API **must** be re-exported in [nobrakes/typing/\_\_init\_\_.py](nobrakes/typing/__init__.py).

#### scripts

All public functions and classes in scripts must include type annotations. Internal helpers are encouraged but not strictly required to be typed.

#### tests

Typing is **not** required.

---
### Testing

- The general rule is that unit tests are expected to be written for all code paths in `nobrakes` (100% coverage).
- Certain code paths may be exempted from the rule if there are valid reasons to do so.
- Tests are to be written using a framework consisting of [pytest](https://docs.pytest.org/en/stable/), [pytest-asyncio](https://pytest-asyncio.readthedocs.io/en/latest/), and [unittest.mock](https://docs.python.org/3/library/unittest.mock.html).
- In addition to the unit tests, other tests such as integration tests are welcomed but not required.
- Run [scripts.test](scripts/test.py) to test `nobrakes`.
- Run [scripts.covreport](scripts/covreport.py) with a required positional report type argument to produce a `nobrakes` coverage report.

## Need Help?

If you have questions or need guidance, feel free to open an issue or join discussions on GitHub.

Thanks again for contributing to `nobrakes`! Your help is greatly appreciated.