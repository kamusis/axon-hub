#!/usr/bin/env python3
"""
check_version.py - Mopheus CLI capability matrix detector and version checker.
Zero external dependencies. Works on Windows, Linux, and macOS.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

# Ensure UTF-8 stdout
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mop_client import create_base_parser, apply_global_args

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CAPABILITIES_PATH = os.path.join(SCRIPT_DIR, "..", "references", "capabilities.json")



def parse_semver(version_str: str) -> Tuple[int, int, int, str]:
    """Parse a version string like v2.2.4-beta.20260903 into (major, minor, patch, prerelease)."""
    v = version_str.strip().lstrip("v")
    m = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:-(.+))?$", v)
    if not m:
        return (0, 0, 0, "")
    major = int(m.group(1)) if m.group(1) else 0
    minor = int(m.group(2)) if m.group(2) else 0
    patch = int(m.group(3)) if m.group(3) else 0
    pre = m.group(4) if m.group(4) else ""
    return (major, minor, patch, pre)


def is_version_gte(current: str, required: str) -> bool:
    """Check if current >= required."""
    cur = parse_semver(current)
    req = parse_semver(required)
    if cur[:3] > req[:3]:
        return True
    if cur[:3] < req[:3]:
        return False
    return True


def load_capabilities() -> Dict[str, Any]:
    """Load the bundled capability matrix."""
    if not os.path.exists(CAPABILITIES_PATH):
        return {"version": "1.0.0", "latestRelease": "v2.2.4", "capabilities": {}}
    with open(CAPABILITIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def probe_local_cli() -> Tuple[Optional[str], Optional[str], bool]:
    """
    Probe local mop / mopheus binary.
    Returns (raw_version_string, binary_path, has_daemon).
    """
    try:
        from mop_client import find_mop_binary
        bin_path = find_mop_binary()
    except ImportError:
        bin_path = "mop"

    for candidate in [bin_path, "mopheus", "mop"]:
        try:
            proc = subprocess.run(
                [candidate, "version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            output = proc.stdout.strip()
            m = re.search(r"version\s+(v?[\d\.]+[\w\.\-]*)", output, re.IGNORECASE)
            if m:
                ver = m.group(1)
                if not ver.startswith("v"):
                    ver = "v" + ver
                return ver, candidate, False
        except Exception:
            continue

    return None, None, False


def check_single_capability(cap_key: str, cur_version: Optional[str], matrix: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Check a single capability against current version.
    Returns (is_supported, warning_message_if_unsupported).
    """
    caps = matrix.get("capabilities", {})
    cap = caps.get(cap_key)
    if not cap:
        return True, None

    min_ver = cap.get("minCliVersion", "v1.0.0")
    req_daemon = cap.get("requiresDaemon", False)
    desc = cap.get("description", "")
    fallback = cap.get("fallback", "")
    upgrade_cmd = matrix.get("upgradeCommand", "mop upgrade")

    if not cur_version:
        msg = f"""> [!WARNING]
> **Mopheus CLI Not Found**: Unable to detect `mop` or `mopheus` in PATH.
> **Required for**: `{cap_key}` ({cap.get('name', '')})
> **Install**: Download or install the CLI from https://mopheus.ai or configure host PATH.
> **Fallback**: {fallback}"""
        return False, msg

    if req_daemon:
        msg = f"""> [!NOTE]
> **Daemon Required**: `{cap_key}` requires a local Mopheus Daemon.
> **Environment Note**: You are currently operating in non-daemon pure CLI mode.
> **Fallback**: {fallback}"""
        return False, msg

    if not is_version_gte(cur_version, min_ver):
        msg = f"""> [!WARNING]
> **Capability Not Supported**: `{cap_key}` requires Mopheus CLI `>= {min_ver}`, but your installed version is `{cur_version}`.
> **Description**: {desc}
> **Fallback**: {fallback}
> **Upgrade**: Run `{upgrade_cmd}` to update your CLI to the latest version."""
        return False, msg

    return True, None


def main():
    base_parser = create_base_parser()
    parser = argparse.ArgumentParser(
        description="Mopheus CLI Capability & Version Checker",
        parents=[base_parser],
    )
    parser.add_argument("--check", help="Check if a specific capability key is supported")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()
    apply_global_args(args)


    matrix = load_capabilities()
    cur_version, bin_path, has_daemon = probe_local_cli()
    latest_ver = matrix.get("latestRelease", "unknown")

    if args.check:
        supported, warn_msg = check_single_capability(args.check, cur_version, matrix)
        if args.json:
            print(json.dumps({
                "capability": args.check,
                "supported": supported,
                "currentVersion": cur_version,
                "requiredVersion": matrix.get("capabilities", {}).get(args.check, {}).get("minCliVersion"),
                "warning": warn_msg
            }, indent=2, ensure_ascii=False))
        else:
            if not supported and warn_msg:
                print(warn_msg)
            else:
                print(f"Capability '{args.check}' is supported (installed: {cur_version})")
        sys.exit(0 if supported else 1)

    # Full report mode
    caps = matrix.get("capabilities", {})
    supported_caps = []
    missing_caps = []

    for k, v in caps.items():
        if cur_version and is_version_gte(cur_version, v.get("minCliVersion", "v1.0.0")):
            if not v.get("requiresDaemon", False):
                supported_caps.append((k, v))
            else:
                missing_caps.append((k, v, "requires local daemon"))
        else:
            missing_caps.append((k, v, f"requires >= {v.get('minCliVersion')}"))

    if args.json:
        res = {
            "installed": cur_version is not None,
            "currentVersion": cur_version,
            "latestRelease": latest_ver,
            "binaryPath": bin_path,
            "isOutdated": not is_version_gte(cur_version, latest_ver) if cur_version else True,
            "supportedCount": len(supported_caps),
            "missingCount": len(missing_caps),
            "supportedCapabilities": [k for k, _ in supported_caps],
            "missingCapabilities": [{
                "key": k,
                "name": v.get("name"),
                "reason": reason,
                "fallback": v.get("fallback")
            } for k, v, reason in missing_caps]
        }
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    # Formatted Markdown report
    print("# Mopheus CLI Version & Capability Diagnostic\n")
    if cur_version:
        is_up_to_date = is_version_gte(cur_version, latest_ver)
        status_badge = "✅ Up to date" if is_up_to_date else f"⚠️ Outdated (Latest: {latest_ver})"
        print(f"- **Installed Version**: `{cur_version}` ({status_badge})")
        print(f"- **Binary Path**: `{bin_path}`")
        print(f"- **Runtime Mode**: Non-daemon pure client")
    else:
        print("- **Installed Version**: ❌ CLI binary not found in PATH")
        print(f"- **Latest Available**: `{latest_ver}`")

    print("\n### Supported Capabilities in Current Version")
    for k, v in supported_caps:
        print(f"- ✅ **{v.get('name')}** (`{k}`): {v.get('description')}")

    if missing_caps:
        print("\n### Missing or Restricted Capabilities")
        for k, v, reason in missing_caps:
            print(f"- ❌ **{v.get('name')}** (`{k}`): {reason}")
            print(f"  └─ *Fallback*: {v.get('fallback')}")

    if cur_version and not is_version_gte(cur_version, latest_ver):
        print(f"\n> [!TIP]\n> Run `{matrix.get('upgradeCommand', 'mop upgrade')}` to upgrade to `{latest_ver}` and unlock all latest capabilities.")


if __name__ == "__main__":
    main()
