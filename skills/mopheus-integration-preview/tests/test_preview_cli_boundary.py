#!/usr/bin/env python3
"""Regression tests for preview/formal Mopheus CLI isolation."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "start_preview.py"
SPEC = importlib.util.spec_from_file_location("start_preview", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load preview script: {SCRIPT_PATH}")
START_PREVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(START_PREVIEW)


class PreviewCLIBoundaryTests(unittest.TestCase):
    """Verify preview startup fails closed at the profile/server boundary."""

    def assert_rejected(self, profile: str, server_url: str) -> None:
        """Assert that an unsafe profile and server combination exits."""
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            START_PREVIEW.validate_preview_cli_boundary(profile, server_url)

    def test_accepts_worktree_profiles_on_http_loopback(self) -> None:
        """Accept generated preview profiles on supported loopback hosts."""
        for server_url in (
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://[::1]:8080",
        ):
            with self.subTest(server_url=server_url):
                START_PREVIEW.validate_preview_cli_boundary("wt-issue-603", server_url)

    def test_rejects_formal_and_legacy_preview_profiles(self) -> None:
        """Reject profiles that could overlap durable formal CLI state."""
        for profile in ("", "default", "local", "preview", "wt"):
            with self.subTest(profile=profile):
                self.assert_rejected(profile, "http://localhost:8080")

    def test_rejects_remote_https_and_incomplete_server_urls(self) -> None:
        """Reject URLs that are not explicit HTTP loopback endpoints."""
        for server_url in (
            "",
            "https://mopheus.enmotech.com",
            "http://mopheus.enmotech.com:8080",
            "https://localhost:8080",
            "http://localhost",
            "http://localhost:not-a-port",
        ):
            with self.subTest(server_url=server_url):
                self.assert_rejected("wt-issue-603", server_url)


if __name__ == "__main__":
    unittest.main()
