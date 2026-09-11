#!/usr/bin/env python3
"""Unit tests for SwissQL regression contract script."""

import os
import sys
import unittest
from pathlib import Path

# Add scripts directory to path
SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import regression_contract


class TestSwissQLRegressionContract(unittest.TestCase):
    def setUp(self):
        self.repo_dir = Path.home() / "CascadeProjects" / "swissql-core"

    def test_build_contract_finds_guides(self):
        if not self.repo_dir.exists():
            self.skipTest(f"Repository not found at {self.repo_dir}")
        contract = regression_contract.build_contract(self.repo_dir)
        self.assertEqual(contract["stageCount"], 10)
        self.assertEqual(contract["scenarioCount"], 37)
        self.assertTrue(len(contract["testedRevision"]) >= 40)
        self.assertEqual(len(contract["guides"]), 3)

    def test_generate_template(self):
        if not self.repo_dir.exists():
            self.skipTest(f"Repository not found at {self.repo_dir}")
        template = regression_contract.generate_template(self.repo_dir)
        self.assertIn("**Revision:**", template)
        self.assertIn("## Scenario Coverage", template)
        self.assertIn("| 0.1 |", template)
        self.assertIn("| 9.3 |", template)

    def test_verify_report_validation(self):
        if not self.repo_dir.exists():
            self.skipTest(f"Repository not found at {self.repo_dir}")
        contract = regression_contract.build_contract(self.repo_dir)
        template = regression_contract.generate_template(self.repo_dir)

        # Replace NOT RUN with PASS and add evidence
        filled_report = template
        for stage in contract["stages"]:
            for s in stage["scenarios"]:
                filled_report = filled_report.replace(
                    f"| {s['id']} | {s['title']} | NOT RUN | - |",
                    f"| {s['id']} | {s['title']} | PASS | run-001 / ok |"
                )

        temp_report_path = SKILL_DIR / "scratch_test_report.md"
        try:
            temp_report_path.write_text(filled_report, encoding="utf-8")
            # If repo is currently dirty (e.g. untracked live-tests file), verify_report will raise ContractError for dirty.
            # We test that dirty check works or passes.
            if contract["dirty"]:
                with self.assertRaises(regression_contract.ContractError) as ctx:
                    regression_contract.verify_report(self.repo_dir, temp_report_path)
                self.assertIn("dirty", str(ctx.exception).lower())
            else:
                result = regression_contract.verify_report(self.repo_dir, temp_report_path)
                self.assertEqual(result["passed"], 37)
                self.assertEqual(result["failed"], 0)
        finally:
            if temp_report_path.exists():
                temp_report_path.unlink()


if __name__ == "__main__":
    unittest.main()
