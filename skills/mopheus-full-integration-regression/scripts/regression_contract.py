#!/usr/bin/env python3
"""Inspect a Mopheus integration contract and verify its regression report."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SPEC_FILE_PATTERN = re.compile(r"^(?P<group>\d{2})-.+\.md$")
METADATA_GROUP_PATTERN = re.compile(r"^  group: (?P<group>\d+)$", re.MULTILINE)
SCENARIO_PATTERN = re.compile(r"^## (?P<group>\d+)\.(?P<number>\d+) (?P<title>.+)$", re.MULTILINE)
REVISION_PATTERN = re.compile(r"^\*\*Revision:\*\* (?P<revision>.+)$", re.MULTILINE)
VALID_STATUSES = {"PASS", "FAIL", "SKIP"}
VALID_SOURCES = {"SHELL", "PLAYWRIGHT", "AGENT"}


class ContractError(RuntimeError):
    """Represent an invalid repository contract or regression report."""


def run_git(repository: Path, *arguments: str, allow_empty: bool = False) -> str:
    """Run a read-only Git command and return its trimmed standard output."""

    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        if allow_empty:
            return ""
        detail = result.stderr.strip() or result.stdout.strip() or "unknown Git error"
        raise ContractError(f"Git command failed: {detail}")
    return result.stdout.strip()


def resolve_repository(candidate: Path) -> Path:
    """Resolve a path inside a Git checkout to its physical repository root."""

    candidate = candidate.expanduser().resolve()
    if not candidate.exists():
        raise ContractError(f"Repository path does not exist: {candidate}")
    root = run_git(candidate, "rev-parse", "--show-toplevel")
    return Path(root).resolve()


def parse_specification(path: Path) -> dict[str, Any]:
    """Parse and validate one numbered integration specification."""

    file_match = SPEC_FILE_PATTERN.match(path.name)
    if not file_match:
        raise ContractError(f"Invalid numbered specification filename: {path.name}")
    file_group = int(file_match.group("group"))
    content = path.read_text(encoding="utf-8")
    metadata_match = METADATA_GROUP_PATTERN.search(content)
    if not metadata_match:
        raise ContractError(f"Missing metadata group in {path}")
    metadata_group = int(metadata_match.group("group"))
    if metadata_group != file_group:
        raise ContractError(
            f"Metadata group {metadata_group} does not match filename group {file_group} in {path}"
        )

    scenarios: list[dict[str, str]] = []
    for match in SCENARIO_PATTERN.finditer(content):
        heading_group = int(match.group("group"))
        if heading_group != file_group:
            raise ContractError(
                f"Scenario group {heading_group} does not match filename group {file_group} in {path}"
            )
        scenarios.append(
            {
                "id": f"{heading_group}.{int(match.group('number'))}",
                "title": match.group("title").strip(),
            }
        )
    if not scenarios:
        raise ContractError(f"No numbered scenarios found in {path}")

    return {
        "group": file_group,
        "file": str(path),
        "scenarios": scenarios,
    }


def build_contract(repository: Path) -> dict[str, Any]:
    """Build the current revision-bound integration contract inventory."""

    repository = resolve_repository(repository)
    guide_paths = [
        repository / "tests" / "integration-testing-guide.md",
        repository / "tests" / "TEST-EXECUTION-GUIDE.md",
    ]
    for guide_path in guide_paths:
        if not guide_path.is_file():
            raise ContractError(f"Required integration guide is missing: {guide_path}")

    spec_directory = repository / "tests" / "integration"
    spec_paths = sorted(spec_directory.glob("[0-9][0-9]-*.md"))
    if not spec_paths:
        raise ContractError(f"No numbered integration specifications found in {spec_directory}")

    groups = [parse_specification(path) for path in spec_paths]
    group_numbers = [group["group"] for group in groups]
    if len(group_numbers) != len(set(group_numbers)):
        raise ContractError("Duplicate integration group numbers found")

    scenario_ids = [scenario["id"] for group in groups for scenario in group["scenarios"]]
    duplicates = sorted(identifier for identifier, count in Counter(scenario_ids).items() if count > 1)
    if duplicates:
        raise ContractError(f"Duplicate scenario IDs found: {', '.join(duplicates)}")

    revision = run_git(repository, "rev-parse", "HEAD")
    branch = run_git(repository, "symbolic-ref", "--short", "-q", "HEAD", allow_empty=True)
    dirty_entries = run_git(repository, "status", "--porcelain", "--untracked-files=all")
    return {
        "repositoryRoot": str(repository),
        "testedRevision": revision,
        "branch": branch or None,
        "dirty": bool(dirty_entries),
        "dirtyEntries": dirty_entries.splitlines(),
        "guides": [str(path) for path in guide_paths],
        "groupCount": len(groups),
        "scenarioCount": len(scenario_ids),
        "groups": groups,
    }


def parse_report_rows(report_path: Path) -> tuple[str, list[dict[str, str]]]:
    """Read the tested revision and scenario coverage rows from a report."""

    if not report_path.is_file():
        raise ContractError(f"Integration report does not exist: {report_path}")
    content = report_path.read_text(encoding="utf-8")
    revision_match = REVISION_PATTERN.search(content)
    if not revision_match:
        raise ContractError("Integration report is missing the Revision field")

    rows: list[dict[str, str]] = []
    in_coverage_section = False
    for line in content.splitlines():
        if line == "## Scenario Coverage":
            in_coverage_section = True
            continue
        if in_coverage_section and line.startswith("## "):
            break
        if not in_coverage_section or not line.startswith("|"):
            continue
        columns = [column.strip() for column in line.strip().strip("|").split("|")]
        if not columns or columns[0] == "Scenario" or set(columns[0]) == {"-"}:
            continue
        if len(columns) != 5:
            raise ContractError(f"Invalid scenario coverage row: {line}")
        rows.append(
            {
                "id": columns[0],
                "title": columns[1],
                "source": columns[2],
                "status": columns[3],
                "evidence": columns[4],
            }
        )
    if not rows:
        raise ContractError("Integration report contains no scenario coverage rows")
    return revision_match.group("revision").strip(), rows


def verify_report(repository: Path, report_path: Path) -> dict[str, Any]:
    """Verify report coverage against the current repository contract."""

    contract = build_contract(repository)
    report_revision, rows = parse_report_rows(report_path.expanduser().resolve())
    expected = {
        scenario["id"]: scenario["title"]
        for group in contract["groups"]
        for scenario in group["scenarios"]
    }
    errors: list[str] = []
    if report_revision != contract["testedRevision"]:
        errors.append(
            f"Report revision {report_revision} does not match checkout revision {contract['testedRevision']}"
        )

    seen: dict[str, dict[str, str]] = {}
    for row in rows:
        scenario_id = row["id"]
        if scenario_id in seen:
            errors.append(f"Duplicate report row for scenario {scenario_id}")
            continue
        seen[scenario_id] = row
        if scenario_id not in expected:
            errors.append(f"Unexpected report scenario {scenario_id}")
            continue
        if row["title"] != expected[scenario_id]:
            errors.append(f"Scenario {scenario_id} title does not match the current specification")
        if row["status"] not in VALID_STATUSES:
            errors.append(f"Scenario {scenario_id} has incomplete or invalid status {row['status']}")
        if row["source"] not in VALID_SOURCES:
            errors.append(f"Scenario {scenario_id} has invalid execution source {row['source']}")
        if not row["evidence"] or row["evidence"] in {"-", "NOT RECORDED"}:
            errors.append(f"Scenario {scenario_id} has no evidence")

    missing = sorted(set(expected) - set(seen))
    if missing:
        errors.append(f"Missing report scenarios: {', '.join(missing)}")

    status_counts = Counter(row["status"] for row in rows if row["status"] in VALID_STATUSES)
    return {
        "complete": not errors,
        "testedRevision": contract["testedRevision"],
        "expectedScenarioCount": len(expected),
        "reportedScenarioCount": len(seen),
        "statusCounts": {status: status_counts.get(status, 0) for status in sorted(VALID_STATUSES)},
        "outcome": "FAIL" if status_counts.get("FAIL", 0) else "PASS",
        "errors": errors,
    }


def emit_json(payload: dict[str, Any], output_path: Path | None) -> None:
    """Print a JSON payload and optionally persist it to a UTF-8 file."""

    rendered = json.dumps(payload, indent=2, sort_keys=True)
    print(rendered)
    if output_path is not None:
        output_path = output_path.expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(f"{rendered}\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect the current integration contract")
    inspect_parser.add_argument("repository", type=Path)
    inspect_parser.add_argument("--output", type=Path)

    verify_parser = subparsers.add_parser("verify-report", help="Verify a completed integration report")
    verify_parser.add_argument("repository", type=Path)
    verify_parser.add_argument("report", type=Path)
    verify_parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    """Run the selected contract command."""

    arguments = build_parser().parse_args()
    try:
        if arguments.command == "inspect":
            payload = build_contract(arguments.repository)
            if payload["dirty"]:
                raise ContractError(
                    "Repository checkout is dirty; the regression cannot be bound to a commit SHA"
                )
        else:
            payload = verify_report(arguments.repository, arguments.report)
        emit_json(payload, arguments.output)
        if arguments.command == "verify-report" and not payload["complete"]:
            return 1
        return 0
    except ContractError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
