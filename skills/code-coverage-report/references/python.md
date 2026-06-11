# Python Coverage Reference

Use this reference for Python projects.

## Detection

Look for:

- `pyproject.toml`
- `setup.cfg`
- `setup.py`
- `requirements.txt`
- `Pipfile`
- `tox.ini`
- `pytest.ini`
- `.coveragerc`
- Existing test commands in README, Makefile, nox, tox, or CI.

Prefer project commands such as `pytest`, `tox`, `nox`, or documented Make targets.

## Common Tools

Most Python coverage uses:

- `coverage.py`
- `pytest-cov`

## Commands

With pytest-cov:

```bash
pytest --cov=<package_or_src_dir> --cov-report=term-missing
pytest --cov=<package_or_src_dir> --cov-report=html --cov-report=xml
```

With coverage.py directly:

```bash
coverage run -m pytest
coverage report -m
coverage html
coverage xml
```

For projects with tox:

```bash
tox
tox -e py
tox -e coverage
```

For nox:

```bash
nox
nox -s tests
```

## Report Files

Common output paths:

```text
.coverage
htmlcov/index.html
coverage.xml
```

## Parsing Reports

Terminal missing-lines report:

```bash
coverage report -m
```

If XML exists, inspect package/file summaries:

```bash
rg -n '<package|<class|line-rate|branch-rate' coverage.xml
```

## Interpretation

Python coverage often highlights:

- Error paths.
- Optional dependency branches.
- CLI entry points.
- Configuration loading.
- Serialization/deserialization.
- Context managers and cleanup.
- Async cancellation and timeout branches.

High-signal gaps often include:

- Input validation and exception translation.
- Auth, permission, and secret handling.
- File/database persistence and migration.
- CLI command behavior and output.
- External API clients and retry/fallback logic.
- Async resource cleanup.

Lower-signal gaps often include:

- `if __name__ == "__main__"` guards.
- Type-checking-only branches.
- Version compatibility fallbacks that are impossible in the current runtime.
- Trivial dataclasses with no validation or behavior.

## Branch Coverage

Enable branch coverage when error paths and conditional logic matter:

```bash
coverage run --branch -m pytest
coverage report -m
```

or:

```bash
pytest --cov=<package_or_src_dir> --cov-branch --cov-report=term-missing
```

## Common Pitfalls

- Running tests from the wrong working directory can produce misleading paths.
- Missing `--cov=<package>` can measure tests instead of source.
- `mock` can cover code while bypassing the behavior under test.
- Async code may need explicit tests for cancellation, timeout, and cleanup.
- Coverage from subprocesses requires configuration.
- Multiprocessing, threads, and subprocesses may need `.coveragerc` settings.
