#!/usr/bin/env python3
"""Discover running Mopheus preview instances across linked Git worktrees."""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
from pathlib import Path


def is_port_listening(port: int) -> bool:
    """Check whether a TCP port is accepting connections on localhost."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


def get_port_pid(port: int) -> str:
    """Find the process ID listening on a given port."""
    if not is_port_listening(port):
        return "none"

    if sys.platform == "win32":
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", f"(Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue).OwningProcess"],
                capture_output=True,
                text=True,
                check=False,
            )
            pids = res.stdout.strip().split()
            if pids and pids[0].isdigit():
                return pids[0]
        except Exception:
            pass
        return "active"
    else:
        try:
            res = subprocess.run(
                ["lsof", "-nP", f"-tiTCP:{port}", "-sTCP:LISTEN"],
                capture_output=True,
                text=True,
                check=False,
            )
            pids = res.stdout.strip().split()
            if pids:
                return pids[0]
        except Exception:
            pass
        return "active"


def read_env_file(env_path: Path) -> dict[str, str]:
    """Parse a simple KEY=VALUE env file."""
    values: dict[str, str] = {}
    if not env_path.is_file():
        return values
    try:
        content = env_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip().strip("'\"")
    except Exception:
        pass
    return values


def list_git_worktrees(target_dir: Path) -> list[Path]:
    """List all worktree directories registered in the git repository."""
    try:
        res = subprocess.run(
            ["git", "-C", str(target_dir), "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        worktrees: list[Path] = []
        for line in res.stdout.splitlines():
            if line.startswith("worktree "):
                wt_path = Path(line[len("worktree "):].strip()).resolve()
                worktrees.append(wt_path)
        return worktrees
    except Exception:
        return []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover active Mopheus worktree previews")
    parser.add_argument("target_path", help="Absolute path to the target worktree")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target_path = Path(args.target_path).resolve()
    if not target_path.exists():
        sys.stderr.write(f"ERROR: target path does not exist: {target_path}\n")
        return 1

    worktrees = list_git_worktrees(target_path)
    if not worktrees:
        # If target_path is a standalone directory or git failed
        return 0

    target_resolved = target_path.resolve()

    for candidate in worktrees:
        if candidate.resolve() == target_resolved:
            continue

        env_file = candidate / ".env.worktree"
        if not env_file.is_file():
            continue

        env = read_env_file(env_file)
        frontend_port_str = env.get("FRONTEND_PORT", "")
        backend_port_str = env.get("BACKEND_PORT", "")
        database_name = env.get("POSTGRES_DB", "")

        if not frontend_port_str or not backend_port_str or not database_name:
            continue

        try:
            frontend_port = int(frontend_port_str)
            backend_port = int(backend_port_str)
        except ValueError:
            continue

        frontend_listening = is_port_listening(frontend_port)
        backend_listening = is_port_listening(backend_port)

        if frontend_listening or backend_listening:
            frontend_pid = get_port_pid(frontend_port) if frontend_listening else "none"
            backend_pid = get_port_pid(backend_port) if backend_listening else "none"
            print(f"{candidate}\t{frontend_port}\t{frontend_pid}\t{backend_port}\t{backend_pid}\t{database_name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
