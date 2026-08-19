#!/usr/bin/env python3
"""Start one preview service in a new session and record its process ID across platforms."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse the service launch arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--pid-file", required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.command:
        parser.error("a command is required")
    return args


def main() -> None:
    """Launch the command independently from the calling terminal session."""
    args = parse_args()
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path = Path(args.pid_file)
    pid_path.parent.mkdir(parents=True, exist_ok=True)

    popen_kwargs = {
        "cwd": args.cwd,
        "stdin": subprocess.DEVNULL,
        "stdout": open(log_path, "ab"),
        "stderr": subprocess.STDOUT,
    }

    command = list(args.command)
    if sys.platform == "win32":
        # DETACHED_PROCESS (0x00000008) | CREATE_NEW_PROCESS_GROUP (0x00000200)
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        if command:
            resolved = shutil.which(command[0])
            if resolved:
                command[0] = resolved
            elif os.path.exists(command[0]):
                command[0] = str(Path(command[0]).resolve())
            else:
                popen_kwargs["shell"] = True
    else:
        popen_kwargs["start_new_session"] = True

    process = subprocess.Popen(command, **popen_kwargs)
    pid_path.write_text(f"{process.pid}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
