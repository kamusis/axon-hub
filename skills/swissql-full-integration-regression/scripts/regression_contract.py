#!/usr/bin/env python3
"""Inspect a SwissQL Core integration contract and verify its regression report."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REVISION_PATTERN = re.compile(r"^\*\*Revision:\*\* (?P<revision>.+)$", re.MULTILINE)
VALID_STATUSES = {"PASS", "FAIL", "SKIP"}

STANDARD_STAGES = [
    {
        "group": 0,
        "name": "Pre-flight & Build Contract",
        "scenarios": [
            {"id": "0.1", "title": "Prerequisite Toolchain Verification (Java 21, Maven, Go 1.23+, curl)"},
            {"id": "0.2", "title": "Clean Repository Checkout (no dirty files or uncommitted diffs)"},
            {"id": "0.3", "title": "Backend Jar Build (mvn package -DskipTests)"},
            {"id": "0.4", "title": "CLI Binary Build (go build)"},
        ],
    },
    {
        "group": 1,
        "name": "Backend Daemon Lifecycle & Health",
        "scenarios": [
            {"id": "1.1", "title": "Isolated Daemon Startup & Readiness Probe (GET /v1/status)"},
            {"id": "1.2", "title": "Capabilities Discovery Probe (GET /v1/capabilities)"},
            {"id": "1.3", "title": "CLI Health & Status Ping (swissql status)"},
        ],
    },
    {
        "group": 2,
        "name": "Connection Profile Lifecycle",
        "scenarios": [
            {"id": "2.1", "title": "Connection Profile Creation (CLI add & REST POST)"},
            {"id": "2.2", "title": "Connection Profile Retrieval & List (CLI list & REST GET)"},
            {"id": "2.3", "title": "Connection Profile Metadata & DSN Update (CLI update & REST PATCH)"},
            {"id": "2.4", "title": "Connection Profile Deletion (CLI delete & REST DELETE)"},
            {"id": "2.5", "title": "File-based Persistence Verification (connections.json)"},
        ],
    },
    {
        "group": 3,
        "name": "Credential Resolution",
        "scenarios": [
            {"id": "3.1", "title": "Inline Password & Credentials Resolution"},
            {"id": "3.2", "title": "External Profile Credential Store Resolution (credentials.json)"},
            {"id": "3.3", "title": "Environment Variable Credential Resolution Override"},
        ],
    },
    {
        "group": 4,
        "name": "Domain Isolation & Security",
        "scenarios": [
            {"id": "4.1", "title": "Isolation Disabled Preserves Default Behavior"},
            {"id": "4.2", "title": "Isolation Enabled Rejects Missing Domain (400 Bad Request)"},
            {"id": "4.3", "title": "Audit Label Precedence Over Declared Domain"},
            {"id": "4.4", "title": "Cross-Domain Access Denial (403 Forbidden / Isolation Boundary)"},
            {"id": "4.5", "title": "Profile Domain Ownership Transfer (connections move)"},
        ],
    },
    {
        "group": 5,
        "name": "SQL Execution & Safety Engine",
        "scenarios": [
            {"id": "5.1", "title": "Read-Only Query Execution & Result Set Marshalling"},
            {"id": "5.2", "title": "Mutating SQL Blocked Without --allow-write (Safety Validator)"},
            {"id": "5.3", "title": "Authorized Mutating SQL Execution With --allow-write"},
            {"id": "5.4", "title": "Query Result Limits Capping & Statement Timeout Handling"},
        ],
    },
    {
        "group": 6,
        "name": "SQL Rules Engine & Hot-Reload",
        "scenarios": [
            {"id": "6.1", "title": "YAML Rules Loading & Label-Scoped Matching (sql-rules.yaml)"},
            {"id": "6.2", "title": "Deny and Warning Rule Enforcement"},
            {"id": "6.3", "title": "AI Stop-Directive Comment Interception"},
            {"id": "6.4", "title": "Authenticated Rules Hot-Reload (POST /v1/sql/rules/reload)"},
        ],
    },
    {
        "group": 7,
        "name": "Dynamic JDBC Driver Autoloading & Admin Security",
        "scenarios": [
            {"id": "7.1", "title": "Built-in Driver Discovery (PostgreSQL, Oracle, MySQL)"},
            {"id": "7.2", "title": "Dynamic Directory Driver Hot-Loading (POST /v1/drivers/reload)"},
            {"id": "7.3", "title": "Admin Authentication Enforcement (SWISSQL_ADMIN_AUTH_TOKEN)"},
        ],
    },
    {
        "group": 8,
        "name": "Audit Logging & Traceability",
        "scenarios": [
            {"id": "8.1", "title": "Execution Request Header Propagation (X-Executor, X-Ticket-Id)"},
            {"id": "8.2", "title": "Audit Log File Emission & JSON Record Structure"},
            {"id": "8.3", "title": "Audit Labels and Domain Capture Verification"},
        ],
    },
    {
        "group": 9,
        "name": "Global Teardown & Process Audit",
        "scenarios": [
            {"id": "9.1", "title": "Graceful Daemon Shutdown & Process Termination"},
            {"id": "9.2", "title": "Server Port & Socket Release Verification"},
            {"id": "9.3", "title": "Sandbox Directory Cleanup & Zero Leaked Processes Audit"},
        ],
    },
]


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


def build_contract(repository: Path) -> dict[str, Any]:
    """Build the current revision-bound integration contract inventory."""
    repository = resolve_repository(repository)
    guide_paths = [
        repository / "tests" / "integration-test-guide.md",
        repository / "tests" / "issue-80-integration-test-guide.md",
        repository / "tests" / "README.md",
    ]
    for guide_path in guide_paths:
        if not guide_path.is_file():
            raise ContractError(f"Required integration guide is missing: {guide_path}")

    revision = run_git(repository, "rev-parse", "HEAD")
    branch = run_git(repository, "symbolic-ref", "--short", "-q", "HEAD", allow_empty=True)
    dirty_entries = run_git(repository, "status", "--porcelain", "--untracked-files=all")

    scenario_ids = [s["id"] for stage in STANDARD_STAGES for s in stage["scenarios"]]
    duplicates = sorted(identifier for identifier, count in Counter(scenario_ids).items() if count > 1)
    if duplicates:
        raise ContractError(f"Duplicate scenario IDs found: {', '.join(duplicates)}")

    return {
        "repositoryRoot": str(repository),
        "testedRevision": revision,
        "branch": branch or None,
        "dirty": bool(dirty_entries),
        "dirtyEntries": dirty_entries.splitlines() if dirty_entries else [],
        "guides": [str(path) for path in guide_paths],
        "stageCount": len(STANDARD_STAGES),
        "scenarioCount": len(scenario_ids),
        "stages": STANDARD_STAGES,
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
        if "## Scenario Coverage" in line:
            in_coverage_section = True
            continue
        if in_coverage_section and line.startswith("## ") and "Scenario Coverage" not in line:
            break
        if not in_coverage_section or not line.strip().startswith("|"):
            continue

        columns = [column.strip() for column in line.strip().strip("|").split("|")]
        if len(columns) < 4:
            continue
        scenario_id, title, status, evidence = columns[0], columns[1], columns[2], columns[3]
        if scenario_id.lower() in {"scenario", "id", "---", ":---", "---:"} or scenario_id.startswith("-"):
            continue
        rows.append(
            {
                "id": scenario_id,
                "title": title,
                "status": status,
                "evidence": evidence,
            }
        )

    if not rows:
        raise ContractError(f"No scenario rows found in {report_path}")
    return revision_match.group("revision").strip(), rows


def verify_report(repository: Path, report_path: Path) -> dict[str, Any]:
    """Verify that a report covers all required integration scenarios."""
    contract = build_contract(repository)
    if contract["dirty"]:
        raise ContractError(
            "Repository checkout is dirty. Regression must be bound to a clean commit SHA."
        )

    tested_revision, rows = parse_report_rows(report_path)
    if tested_revision != contract["testedRevision"]:
        raise ContractError(
            f"Report revision {tested_revision} does not match repository revision {contract['testedRevision']}"
        )

    expected_scenarios = {
        s["id"]: s["title"]
        for stage in contract["stages"]
        for s in stage["scenarios"]
    }
    reported_scenarios = {row["id"]: row for row in rows}

    missing = sorted(set(expected_scenarios) - set(reported_scenarios))
    extra = sorted(set(reported_scenarios) - set(expected_scenarios))
    if missing:
        raise ContractError(f"Missing required scenarios in report: {', '.join(missing)}")
    if extra:
        raise ContractError(f"Unexpected scenarios in report: {', '.join(extra)}")

    invalid_statuses: list[str] = []
    missing_evidence: list[str] = []
    status_counts: Counter[str] = Counter()

    for scenario_id, expected_title in expected_scenarios.items():
        row = reported_scenarios[scenario_id]
        status = row["status"].upper()
        status_counts[status] += 1
        if status not in VALID_STATUSES:
            invalid_statuses.append(f"{scenario_id}: {row['status']}")
        evidence = row["evidence"].strip()
        if not evidence or evidence in {"-", "N/A", "none", "TODO", "NOT RUN"}:
            missing_evidence.append(scenario_id)

    if invalid_statuses:
        raise ContractError(
            f"Invalid statuses (must be PASS, FAIL, or SKIP): {', '.join(invalid_statuses)}"
        )
    if missing_evidence:
        raise ContractError(
            f"Missing required evidence for scenarios: {', '.join(missing_evidence)}"
        )

    return {
        "repositoryRoot": contract["repositoryRoot"],
        "testedRevision": tested_revision,
        "branch": contract["branch"],
        "totalScenarios": len(expected_scenarios),
        "statusCounts": dict(status_counts),
        "passed": status_counts.get("PASS", 0),
        "failed": status_counts.get("FAIL", 0),
        "skipped": status_counts.get("SKIP", 0),
    }


def generate_template(repository: Path, output_path: Path | None = None) -> str:
    """Generate a blank integration regression report template."""
    contract = build_contract(repository)
    lines = [
        "# SwissQL Core Full Integration Regression Report",
        "",
        f"**Revision:** {contract['testedRevision']}",
        f"**Branch:** {contract['branch'] or 'HEAD'}",
        "**Date:** YYYY-MM-DD HH:MM:SS",
        "**Executor:** <agent-or-tester-id>",
        "**Port:** 18080",
        "**Sandbox Directory:** test-results/integration/<runId>",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | --- |",
        f"| Total Scenarios | {contract['scenarioCount']} |",
        "| Passed | 0 |",
        "| Failed | 0 |",
        "| Skipped | 0 |",
        "",
        "## Scenario Coverage",
        "",
        "| Scenario | Title | Status | Evidence |",
        "| --- | --- | --- | --- |",
    ]

    for stage in contract["stages"]:
        for scenario in stage["scenarios"]:
            lines.append(
                f"| {scenario['id']} | {scenario['title']} | NOT RUN | - |"
            )

    lines.extend([
        "",
        "## Failure Details",
        "",
        "None.",
        "",
        "## Teardown & Resource Verification",
        "",
        "- [ ] Backend process terminated (kill signal sent and confirmed)",
        "- [ ] Port 18080 freed (verified via socket check)",
        "- [ ] Sandbox data directory cleaned or archived in test-results/",
        "- [ ] Zero leaked Java/Go/Postgres processes confirmed",
        "",
    ])

    content = "\n".join(lines) + "\n"
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
    return content


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect SwissQL integration contract and verify reports.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect integration contract for a repository")
    inspect_parser.add_argument("repository", type=Path, help="Path to repository checkout")

    verify_parser = subparsers.add_parser("verify-report", help="Verify a regression report against repository contract")
    verify_parser.add_argument("repository", type=Path, help="Path to repository checkout")
    verify_parser.add_argument("report", type=Path, help="Path to regression report markdown")

    template_parser = subparsers.add_parser("generate-template", help="Generate a blank report template")
    template_parser.add_argument("repository", type=Path, help="Path to repository checkout")
    template_parser.add_argument("-o", "--output", type=Path, default=None, help="Output report file path")

    args = parser.parse_args()

    try:
        if args.command == "inspect":
            data = build_contract(args.repository)
            print(json.dumps(data, indent=2))
        elif args.command == "verify-report":
            result = verify_report(args.repository, args.report)
            print(json.dumps(result, indent=2))
        elif args.command == "generate-template":
            out = generate_template(args.repository, args.output)
            if not args.output:
                print(out)
            else:
                print(f"Generated template at {args.output}")
    except ContractError as exc:
        print(f"Contract Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
