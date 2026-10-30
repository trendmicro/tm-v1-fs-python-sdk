"""Guard against Requires-Python metadata regressions."""

import configparser
import pathlib
import re
import sys
import tomllib

PUBLIC_DIR = pathlib.Path(__file__).resolve().parent.parent
SUPPORTED_SERIES = [(3, 11), (3, 12), (3, 13), (3, 14)]
# Retired from the support floor (both end-of-life; C1AMAAS-21165).
RETIRED_SERIES = [(3, 9), (3, 10)]

try:
    from packaging.specifiers import SpecifierSet
except ImportError:  # pragma: no cover - packaging is a pytest dependency
    SpecifierSet = None


def _requires_python() -> str:
    """Read requires-python from pyproject.toml.

    The checked-in file carries the `_VERSION_` placeholder in `version =`,
    which is not valid TOML, so parse only when the Makefile has substituted
    it and fall back to a line match otherwise.
    """
    text = (PUBLIC_DIR / "pyproject.toml").read_text()
    try:
        return tomllib.loads(text)["project"]["requires-python"]
    except tomllib.TOMLDecodeError:
        pass
    m = re.search(r'^requires-python\s*=\s*"([^"]+)"', text, re.M)
    if not m:
        raise AssertionError("requires-python not found in pyproject.toml")
    return m.group(1)


def test_requires_python_admits_patch_releases_of_supported_series():
    assert SpecifierSet is not None
    spec = SpecifierSet(_requires_python())
    for major, minor in SUPPORTED_SERIES:
        # Latest plausible patch of the series, as a full release version.
        assert spec.contains(f"{major}.{minor}.99"), (
            f"requires-python={_requires_python()!r} excludes Python "
            f"{major}.{minor}.99 — an upper bound must be a bound on the "
            f"series (<3.{minor + 1}), not on a single release (<=3.{minor})"
        )


def test_requires_python_rejects_unsupported_series():
    assert SpecifierSet is not None
    spec = SpecifierSet(_requires_python())
    first_unsupported = SUPPORTED_SERIES[-1][1] + 1
    assert not spec.contains(f"3.{first_unsupported}.0")
    for major, minor in RETIRED_SERIES:
        assert not spec.contains(f"{major}.{minor}.0"), (
            f"requires-python={_requires_python()!r} still admits retired Python {major}.{minor}"
        )


def _expand_envlist(envlist: str) -> set[str]:
    """Expand tox factor syntax: 'py{39,310}' -> {'py39', 'py310'}."""
    envs: set[str] = {""}
    i = 0
    while i < len(envlist):
        ch = envlist[i]
        if ch == "{":
            close = envlist.index("}", i)
            factors = envlist[i + 1 : close].split(",")
            envs = {e + f for e in envs for f in factors}
            i = close + 1
        else:
            run = i
            while run < len(envlist) and envlist[run] not in "{,":
                run += 1
            envs = {e + envlist[i:run] for e in envs}
            i = run
    return envs


def test_tox_envlist_covers_every_supported_series():
    tox = configparser.ConfigParser()
    tox.read(PUBLIC_DIR / "tox.ini")
    envs = _expand_envlist(tox["tox"]["envlist"])
    for major, minor in SUPPORTED_SERIES:
        assert f"py{major}{minor}" in envs, f"tox envlist is missing py{major}{minor}"


def test_tox_envlist_excludes_retired_series():
    tox = configparser.ConfigParser()
    tox.read(PUBLIC_DIR / "tox.ini")
    envs = _expand_envlist(tox["tox"]["envlist"])
    for major, minor in RETIRED_SERIES:
        assert f"py{major}{minor}" not in envs, f"tox envlist still lists retired py{major}{minor}"


def test_current_interpreter_is_inside_declared_range():
    spec = SpecifierSet(_requires_python())
    current = ".".join(str(p) for p in sys.version_info[:3])
    assert spec.contains(current), (
        f"running interpreter {current} is excluded by requires-python={_requires_python()!r}"
    )
