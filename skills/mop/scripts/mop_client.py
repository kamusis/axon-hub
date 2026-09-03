#!/usr/bin/env python3
"""
mop_client.py - Unified Python helper wrapper for Mopheus CLI (mop / mopheus).
Executes CLI commands with JSON output, handles quoting, and returns parsed data.
"""

import argparse
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
    """Find mop or mopheus binary across system PATH and standard user bin directories."""
    # 1. Check system PATH first
    for bin_name in ["mopheus", "mop"]:
        path = shutil.which(bin_name)
        if path:
            return path

    # 2. Check standard user go/bin paths
    home = os.path.expanduser("~")
    common_paths = [
        os.path.join(home, "go", "bin", "mopheus.exe"),
        os.path.join(home, "go", "bin", "mopheus"),
        os.path.join(home, "go", "bin", "mop.exe"),
        os.path.join(home, "go", "bin", "mop"),
        os.path.join(home, ".local", "bin", "mopheus"),
        os.path.join(home, ".local", "bin", "mop"),
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p

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
        # Try trimming trailing CLI pagination messages (e.g. "Page 1/4, 17 items total...")
        idx_bracket = stdout.rfind("]")
        idx_brace = stdout.rfind("}")
        cut_idx = max(idx_bracket, idx_brace)
        if cut_idx != -1:
            try:
                return json.loads(stdout[: cut_idx + 1])
            except json.JSONDecodeError:
                pass
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


_CACHED_USER: Optional[Dict[str, Any]] = None


def get_current_user() -> Dict[str, Any]:
    """
    Retrieve and cache current authenticated user profile.
    Returns dictionary with 'id', 'name', 'email', etc.
    """
    global _CACHED_USER
    if _CACHED_USER is not None:
        return _CACHED_USER

    try:
        data = run_mop_json(["user", "profile", "get"])
        if isinstance(data, dict) and "id" in data:
            _CACHED_USER = data
            return _CACHED_USER
    except Exception as e:
        print(f"Warning: Failed to fetch user profile via API: {e}", file=sys.stderr)

    return {}


def get_current_user_id() -> Optional[str]:
    """Return the UUID of the current authenticated user or None."""
    user = get_current_user()
    return user.get("id")


_CACHED_WORKSPACES: Optional[List[Dict[str, Any]]] = None


def resolve_workspace_id(val: Optional[str]) -> Optional[str]:
    """Resolve a workspace name, slug, or UUID to a workspace UUID."""
    if not val:
        return None
    if len(val) == 36 and val.count("-") == 4:
        return val

    global _CACHED_WORKSPACES
    if _CACHED_WORKSPACES is None:
        try:
            ws_list = run_mop_json(["workspace", "list"])
            if isinstance(ws_list, list):
                _CACHED_WORKSPACES = ws_list
            else:
                _CACHED_WORKSPACES = []
        except Exception:
            _CACHED_WORKSPACES = []

    val_lower = val.lower()
    for w in _CACHED_WORKSPACES:
        if (
            (w.get("name") or "").lower() == val_lower
            or (w.get("slug") or "").lower() == val_lower
            or w.get("id") == val
        ):
            return w.get("id")

    return val


def create_base_parser() -> argparse.ArgumentParser:
    """Create a common parent parser containing global -p/--profile and -w/--workspace options."""
    base = argparse.ArgumentParser(add_help=False)
    base.add_argument(
        "-p",
        "--profile",
        default=argparse.SUPPRESS,
        help="Mopheus configuration profile name (env: MOPHEUS_PROFILE)",
    )
    base.add_argument(
        "-w",
        "--workspace",
        "--workspace-id",
        dest="workspace",
        default=argparse.SUPPRESS,
        help="Target workspace UUID, name, or slug (env: MOPHEUS_WORKSPACE_ID)",
    )
    return base



def apply_global_args(args: Any) -> None:
    """Propagate --profile and --workspace arguments to environment variables."""
    if getattr(args, "profile", None):
        os.environ["MOPHEUS_PROFILE"] = args.profile
    if getattr(args, "workspace", None):
        ws_id = resolve_workspace_id(args.workspace)
        if ws_id:
            os.environ["MOPHEUS_WORKSPACE_ID"] = ws_id
