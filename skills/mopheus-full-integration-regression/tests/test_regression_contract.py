#!/usr/bin/env python3
"""Unit tests for the revision-bound integration contract helper."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIRECTORY = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIRECTORY))

import regression_contract  # noqa: E402


class RegressionContractTests(unittest.TestCase):
    """Verify dynamic contract discovery and report completion checks."""

    def setUp(self) -> None:
        """Create a minimal committed Mopheus-like repository fixture."""

        self.temporary_directory = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary_directory.name)
        integration_directory = self.repository / "tests" / "integration"
        integration_directory.mkdir(parents=True)
        (self.repository / "tests" / "integration-testing-guide.md").write_text(
            "# Integration Guide\n", encoding="utf-8"
        )
        (self.repository / "tests" / "TEST-EXECUTION-GUIDE.md").write_text(
            "# Execution Guide\n", encoding="utf-8"
        )
        self.write_specification(1, "auth", [("1.1", "Register user")])
        self.write_specification(2, "workspace", [("2.1", "Create workspace")])
        self.run_git("init", "-b", "main")
        self.run_git("config", "user.email", "integration@example.test")
        self.run_git("config", "user.name", "Integration Fixture")
        self.run_git("add", ".")
        self.run_git("commit", "-m", "test: add integration contract fixture")

    def tearDown(self) -> None:
        """Release the temporary repository fixture."""

        self.temporary_directory.cleanup()

    def run_git(self, *arguments: str) -> None:
        """Run a Git command in the temporary repository."""

        subprocess.run(
            ["git", "-C", str(self.repository), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )

    def write_specification(
        self, group: int, name: str, scenarios: list[tuple[str, str]]
    ) -> Path:
        """Write one numbered specification to the fixture repository."""

        path = self.repository / "tests" / "integration" / f"{group:02d}-{name}.md"
        headings = "\n\n".join(f"## {identifier} {title}" for identifier, title in scenarios)
        path.write_text(
            "---\n"
            f"name: integration_group_{group:02d}\n"
            "metadata:\n"
            "  type: integration_test\n"
            f"  group: {group}\n"
            "---\n\n"
            f"# Test Group {group}\n\n"
            f"{headings}\n",
            encoding="utf-8",
        )
        return path

    def write_report(self, status: str = "PASS") -> Path:
        """Write a report containing both fixture scenarios."""

        revision = subprocess.run(
            ["git", "-C", str(self.repository), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        report = self.repository / "report.md"
        report.write_text(
            "# Report\n\n"
            f"**Revision:** {revision}\n\n"
            "## Scenario Coverage\n\n"
            "| Scenario | User journey | Execution source | Status | Redacted evidence |\n"
            "|---|---|---|---|---|\n"
            f"| 1.1 | Register user | SHELL | {status} | shell.log:10 |\n"
            "| 2.1 | Create workspace | AGENT | PASS | api.json:1 |\n\n"
            "## Failures and Diagnostics\n",
            encoding="utf-8",
        )
        return report

    def test_build_contract_discovers_current_groups_and_scenarios(self) -> None:
        """Discover groups and scenarios without hard-coded totals."""

        contract = regression_contract.build_contract(self.repository)
        self.assertEqual(contract["groupCount"], 2)
        self.assertEqual(contract["scenarioCount"], 2)
        self.assertFalse(contract["dirty"])

    def test_verify_report_accepts_complete_revision_bound_coverage(self) -> None:
        """Accept a report with exact scenarios, evidence, and revision."""

        result = regression_contract.verify_report(self.repository, self.write_report())
        self.assertTrue(result["complete"])
        self.assertEqual(result["outcome"], "PASS")

    def test_verify_report_rejects_not_run_status(self) -> None:
        """Reject a report that still contains an unexecuted scenario."""

        result = regression_contract.verify_report(
            self.repository, self.write_report(status="NOT RUN")
        )
        self.assertFalse(result["complete"])
        self.assertTrue(any("NOT RUN" in error for error in result["errors"]))

    def test_build_contract_rejects_mismatched_scenario_group(self) -> None:
        """Reject a scenario heading that does not match its file group."""

        self.write_specification(2, "workspace", [("9.1", "Wrong group")])
        with self.assertRaises(regression_contract.ContractError):
            regression_contract.build_contract(self.repository)


if __name__ == "__main__":
    unittest.main()
