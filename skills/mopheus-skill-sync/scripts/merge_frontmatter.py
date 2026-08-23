"""Merge local Markdown frontmatter with remote Mopheus-only fields."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


TOP_LEVEL_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(\s|$)")


def split_frontmatter(text: str) -> tuple[list[str], list[str], str]:
    """Return frontmatter lines, body lines, and the detected line ending."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")

    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return lines[1:index], lines[index + 1 :], "\r\n" if "\r\n" in text else "\n"
    raise ValueError("SKILL.md frontmatter has no closing --- delimiter")


def frontmatter_blocks(lines: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    """Split top-level YAML entries while retaining their original raw lines."""
    preamble: list[str] = []
    blocks: dict[str, list[str]] = {}
    current_key: str | None = None

    for line in lines:
        match = TOP_LEVEL_KEY.match(line.rstrip("\r\n"))
        if match:
            current_key = match.group(1)
            if current_key in blocks:
                raise ValueError(f"duplicate frontmatter key: {current_key}")
            blocks[current_key] = [line]
        elif current_key is None:
            preamble.append(line)
        else:
            blocks[current_key].append(line)

    return preamble, blocks


def merge_skill(local_text: str, remote_text: str) -> tuple[str, list[str], list[str]]:
    """Merge local values and body with remote-only frontmatter blocks."""
    local_lines, local_body, newline = split_frontmatter(local_text)
    remote_lines, _, _ = split_frontmatter(remote_text)
    local_preamble, local_blocks = frontmatter_blocks(local_lines)
    _, remote_blocks = frontmatter_blocks(remote_lines)

    if "name" not in local_blocks:
        raise ValueError("local frontmatter must contain name")

    retained_keys = [key for key in remote_blocks if key not in local_blocks]
    merged_lines = list(local_preamble)
    for block in local_blocks.values():
        merged_lines.extend(block)
    for key in retained_keys:
        merged_lines.extend(remote_blocks[key])

    merged = "---" + newline + "".join(merged_lines) + "---" + newline + "".join(local_body)
    synchronized_keys = list(local_blocks)
    return merged, retained_keys, synchronized_keys


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", required=True, type=Path, help="Local SKILL.md path")
    parser.add_argument("--remote", required=True, type=Path, help="Remote SKILL.md content path")
    parser.add_argument("--output", required=True, type=Path, help="Merged SKILL.md output path")
    return parser.parse_args()


def main() -> int:
    """Merge the two files and print the retained and synchronized keys."""
    args = parse_args()
    merged, retained_keys, synchronized_keys = merge_skill(
        args.local.read_text(encoding="utf-8"),
        args.remote.read_text(encoding="utf-8"),
    )
    args.output.write_text(merged, encoding="utf-8", newline="")
    print(f"retained_remote_only={','.join(retained_keys) or 'none'}")
    print(f"synchronized_local={','.join(synchronized_keys)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
