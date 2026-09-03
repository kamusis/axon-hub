#!/usr/bin/env python3
"""
mop_client.py - Unified Python helper wrapper for Mopheus CLI (mop / mopheus).
Executes CLI commands with JSON output, handles quoting, and returns parsed data.
"""

import json
import os
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional, Union

# Ensure UTF-8 stdout on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def find_mop_binary() -> str:
    """Find mop or mopheus binary, prioritizing newest local Go bin."""
    common_paths = [
        os.path.expanduser("~/go/bin/mopheus.exe"),
        os.path.expanduser("~/go/bin/mopheus"),
        os.path.expanduser("~/go/bin/mop.exe"),
        os.path.expanduser("~/go/bin/mop"),
        "C:\\Users\\kamus\\go\\bin\\mopheus.exe",
        "C:\\Users\\kamus\\go\\bin\\mop.exe",
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p

    for bin_name in ["mopheus", "mop"]:
        path = shutil.which(bin_name)
        if path:
            return path
            
    return "mop"


def run_mop_json(args: List[str], input_data: Optional[str] = None) -> Union[Dict[str, Any], List[Any]]:
    """
    Run a mop CLI command with --output json and return parsed JSON data.
    Raises RuntimeError on non-zero exit code or JSON parse failure.
    """
    bin_path = find_mop_binary()
    cmd = [bin_path] + args
    if "--output" not in cmd and "-o" not in cmd:
        cmd.extend(["--output", "json"])

    proc = subprocess.run(
        cmd,
        input=input_data.encode("utf-8") if input_data else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout = proc.stdout.decode("utf-8", errors="replace").strip()
    stderr = proc.stderr.decode("utf-8", errors="replace").strip()

    if proc.returncode != 0:
        err_msg = stderr if stderr else stdout
        raise RuntimeError(f"mop CLI failed (exit code {proc.returncode}):\n{err_msg}")

    if not stdout:
        return {}

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        # Fallback if raw text output
        return {"raw_output": stdout, "warning": f"Failed to parse JSON: {e}"}


def run_mop_raw(args: List[str], input_data: Optional[str] = None) -> str:
    """Run a mop CLI command and return raw stdout string."""
    bin_path = find_mop_binary()
    cmd = [bin_path] + args
    proc = subprocess.run(
        cmd,
        input=input_data.encode("utf-8") if input_data else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout = proc.stdout.decode("utf-8", errors="replace").strip()
    stderr = proc.stderr.decode("utf-8", errors="replace").strip()

    if proc.returncode != 0:
        err_msg = stderr if stderr else stdout
        raise RuntimeError(f"mop CLI failed (exit code {proc.returncode}):\n{err_msg}")

    return stdout
