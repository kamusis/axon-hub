#!/usr/bin/env python3
"""
mop_agent.py - Advanced helper script for managing Mopheus Agents.
Handles listing, owner/mine filtering, inspecting prompts, and bound skills.
"""

import argparse
import json
import os
import sys

# Ensure UTF-8 stdout on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mop_client import (
    run_mop_json,
    run_mop_raw,
    get_current_user,
    get_current_user_id,
    create_base_parser,
    apply_global_args,
)



def format_agents_markdown(agents):
    if not agents:
        return "No agents found matching criteria."

    lines = [
        "| Agent Name | Description | Model / Runtime | Agent ID |",
        "| :--- | :--- | :--- | :--- |"
    ]
    for a in agents:
        name = a.get("name", "").replace("|", "\\|")
        desc = (a.get("description") or "").replace("|", "\\|").replace("\n", " ")
        if len(desc) > 60:
            desc = desc[:57] + "..."
        tags = a.get("runtimeTags") or {}
        model_info = tags.get("provider", "")
        aid = a.get("id", "")
        lines.append(f"| **{name}** | {desc} | `{model_info or 'default'}` | `{aid}` |")

    return "\n".join(lines)


def resolve_agent_id(val: str) -> str:
    """Resolve an agent name to its UUID if not already a UUID."""
    if len(val) == 36 and val.count("-") == 4:
        return val
    agents = run_mop_json(["agent", "list"])
    if isinstance(agents, list):
        for a in agents:
            if a.get("name", "").lower() == val.lower():
                return a.get("id", val)
    return val


def cmd_get(args):
    target_id = resolve_agent_id(args.agent_id)
    data = run_mop_json(["agent", "get", target_id])
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_list(args):
    cmd = ["agent", "list"]
    if getattr(args, "include_archived", False):
        cmd.append("--include-archived")

    data = run_mop_json(cmd)
    if not isinstance(data, list):
        data = []

    user_name = None
    if getattr(args, "mine", False):
        user = get_current_user()
        uid = user.get("id")
        user_name = user.get("name", "me")
        if uid:
            data = [a for a in data if a.get("ownerId") == uid]
        else:
            print("Error: Could not resolve current user ID for --mine", file=sys.stderr)
            sys.exit(1)

    if getattr(args, "json", False):
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        target_info = f" (Owner: {user_name})" if user_name else ""
        print(f"Total matching: {len(data)}{target_info}\n")
        print(format_agents_markdown(data))


def cmd_skills(args):
    target_id = resolve_agent_id(args.agent_id)
    data = run_mop_json(["agent", "skills", "list", target_id])
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_prompt(args):
    target_id = resolve_agent_id(args.agent_id)
    data = run_mop_json(["agent", "get", target_id])
    instructions = data.get("instructions", "")
    if instructions:
        print(instructions)
    else:
        print("No custom instructions configured for this agent.")



def main():
    base_parser = create_base_parser()
    parser = argparse.ArgumentParser(description="Mopheus Agent Helper", parents=[base_parser])
    subparsers = parser.add_subparsers(dest="command", required=True)

    # get
    p_get = subparsers.add_parser("get", help="Get agent details JSON", parents=[base_parser])
    p_get.add_argument("agent_id", help="Agent UUID or name")
    p_get.set_defaults(func=cmd_get)

    # list
    p_list = subparsers.add_parser("list", help="List agents with filtering and Markdown formatting", parents=[base_parser])
    p_list.add_argument("--mine", action="store_true", help="Filter by current authenticated user as owner")
    p_list.add_argument("--include-archived", action="store_true", help="Include archived agents")
    p_list.add_argument("--json", action="store_true", help="Output raw JSON instead of Markdown table")
    p_list.set_defaults(func=cmd_list)

    # list-mine (ergonomic shortcut)
    p_mine = subparsers.add_parser("list-mine", help="Shortcut to list current user's agents", parents=[base_parser])
    p_mine.add_argument("--include-archived", action="store_true", help="Include archived agents")
    p_mine.add_argument("--json", action="store_true", help="Output raw JSON instead of Markdown table")

    def _cmd_list_mine(args):
        args.mine = True
        cmd_list(args)

    p_mine.set_defaults(func=_cmd_list_mine)

    # skills
    p_sk = subparsers.add_parser("skills", help="List bound skills for an agent", parents=[base_parser])
    p_sk.add_argument("agent_id", help="Agent UUID or name")
    p_sk.set_defaults(func=cmd_skills)

    # prompt
    p_pr = subparsers.add_parser("prompt", help="Print agent system instructions/prompt directly", parents=[base_parser])
    p_pr.add_argument("agent_id", help="Agent UUID or name")
    p_pr.set_defaults(func=cmd_prompt)

    args = parser.parse_args()
    apply_global_args(args)

    args.func(args)



if __name__ == "__main__":
    main()
