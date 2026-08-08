#!/usr/bin/env python3
"""Validate an explicit Mopheus release version and release source."""

from __future__ import annotations

import functools
import json
import re
import subprocess
import sys
from typing import TypeAlias


Prerelease: TypeAlias = tuple[str, ...]
ParsedVersion: TypeAlias = tuple[int, int, int, Prerelease]

SEMVER_PATTERN = re.compile(
    r"^v(0|[1-9][0-9]*)\."
    r"(0|[1-9][0-9]*)\."
    r"(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
SOURCE_VERSION_PATTERN = re.compile(r'^var Version = "(v[^"]+)"$', re.MULTILINE)


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run Git with captured text output."""

    result = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise RuntimeError(message)
    return result


def parse_version(value: str) -> ParsedVersion:
    """Parse the supported v-prefixed SemVer subset."""

    if "-dirty" in value:
        raise ValueError(f"Version '{value}' is excluded from the release workflow.")
    match = SEMVER_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError(
            f"Version '{value}' must be vX.Y.Z or vX.Y.Z-prerelease without build metadata."
        )
    prerelease = tuple(match.group(4).split(".")) if match.group(4) else ()
    for identifier in prerelease:
        if identifier.isdigit() and len(identifier) > 1 and identifier.startswith("0"):
            raise ValueError(
                f"Version '{value}' has a numeric prerelease identifier with a leading zero."
            )
    return int(match.group(1)), int(match.group(2)), int(match.group(3)), prerelease


def compare_prerelease(left: Prerelease, right: Prerelease) -> int:
    """Compare SemVer prerelease identifiers."""

    if not left and not right:
        return 0
    if not left:
        return 1
    if not right:
        return -1
    for left_part, right_part in zip(left, right):
        if left_part == right_part:
            continue
        left_numeric = left_part.isdigit()
        right_numeric = right_part.isdigit()
        if left_numeric and right_numeric:
            return -1 if int(left_part) < int(right_part) else 1
        if left_numeric != right_numeric:
            return -1 if left_numeric else 1
        return -1 if left_part < right_part else 1
    if len(left) == len(right):
        return 0
    return -1 if len(left) < len(right) else 1


def compare_versions(left: ParsedVersion, right: ParsedVersion) -> int:
    """Compare two parsed versions using SemVer precedence."""

    left_core = left[:3]
    right_core = right[:3]
    if left_core != right_core:
        return -1 if left_core < right_core else 1
    return compare_prerelease(left[3], right[3])


def read_source_version(requested: ParsedVersion, release_sha: str) -> str | None:
    """Read and validate the base version from the release commit."""

    version_file = "server/pkg/version/version.go"
    exists = run_git("cat-file", "-e", f"{release_sha}:{version_file}", check=False)
    if exists.returncode != 0:
        return None
    content = run_git("show", f"{release_sha}:{version_file}").stdout
    match = SOURCE_VERSION_PATTERN.search(content)
    if match is None:
        raise RuntimeError(f"Could not read var Version from {version_file}.")
    source_version = match.group(1)
    expected = f"v{requested[0]}.{requested[1]}.{requested[2]}"
    if source_version != expected:
        raise RuntimeError(
            f"Requested release base is {expected}, but {version_file} contains {source_version}."
        )
    return source_version


def reachable_versions(release_sha: str) -> list[tuple[str, ParsedVersion]]:
    """Return valid release tags reachable from the release commit."""

    result = run_git("tag", "--merged", release_sha, "--list", "v*")
    versions: list[tuple[str, ParsedVersion]] = []
    for tag in result.stdout.splitlines():
        try:
            versions.append((tag, parse_version(tag)))
        except ValueError:
            continue
    versions.sort(
        key=functools.cmp_to_key(lambda left, right: compare_versions(left[1], right[1])),
        reverse=True,
    )
    return versions


def select_previous_tag(
    requested: ParsedVersion,
    versions: list[tuple[str, ParsedVersion]],
) -> str | None:
    """Select the changelog boundary for stable or prerelease targets."""

    if requested[3]:
        same_core = [tag for tag, parsed in versions if parsed[:3] == requested[:3] and parsed[3]]
        if same_core:
            return same_core[0]
    stable = [tag for tag, parsed in versions if not parsed[3]]
    return stable[0] if stable else None


def validate(version: str) -> dict[str, str | None]:
    """Validate repository state and return release metadata."""

    requested = parse_version(version)
    inside_repo = run_git("rev-parse", "--is-inside-work-tree").stdout.strip()
    if inside_repo != "true":
        raise RuntimeError("Current directory is not inside a Git worktree.")
    if run_git("status", "--porcelain").stdout.strip():
        raise RuntimeError("The Git worktree must be clean before release validation.")

    run_git("remote", "get-url", "origin")
    run_git("fetch", "--quiet", "--prune", "--tags", "origin")

    main_sha = run_git("rev-parse", "refs/remotes/origin/main^{commit}").stdout.strip()
    release_sha = run_git("rev-parse", "refs/remotes/origin/release^{commit}").stdout.strip()
    ancestry = run_git("merge-base", "--is-ancestor", release_sha, main_sha, check=False)
    if ancestry.returncode == 1:
        raise RuntimeError(
            "origin/release must be an ancestor of origin/main before release: "
            f"main={main_sha}, release={release_sha}."
        )
    if ancestry.returncode != 0:
        message = ancestry.stderr.strip() or "Could not verify release ancestry."
        raise RuntimeError(message)

    existing = run_git("show-ref", "--verify", "--quiet", f"refs/tags/{version}", check=False)
    if existing.returncode == 0:
        raise RuntimeError(f"Release tag '{version}' already exists.")

    versions = reachable_versions(release_sha)
    if versions and compare_versions(requested, versions[0][1]) <= 0:
        raise RuntimeError(
            f"Requested version '{version}' must be newer than latest reachable tag '{versions[0][0]}'."
        )

    source_version = read_source_version(requested, release_sha)
    return {
        "version": version,
        "releaseSha": release_sha,
        "previousTag": select_previous_tag(requested, versions),
        "latestTag": versions[0][0] if versions else None,
        "sourceVersion": source_version,
    }


def main() -> int:
    """Run command-line validation and emit JSON metadata."""

    if len(sys.argv) != 2:
        print("Usage: validate_release.py <vX.Y.Z[-prerelease]>", file=sys.stderr)
        return 2
    try:
        result = validate(sys.argv[1])
    except (RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
