#!/usr/bin/env python3
"""
mop_ticket.py - Advanced helper script for managing Mopheus Tickets and Comments.
Avoids shell escaping pitfalls for large Markdown descriptions and structured comments.
"""

import argparse
import json
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mop_client import run_mop_json, run_mop_raw


def cmd_get(args):
    data = run_mop_json(["ticket", "get", args.ticket_id])
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_list(args):
    cmd = ["ticket", "list", "--limit", str(args.limit)]
    if args.status:
        cmd.extend(["--status", args.status])
    if args.project:
        cmd.extend(["--project", args.project])
    data = run_mop_json(cmd)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_comments(args):
    data = run_mop_json(["ticket", "comment", "list", args.ticket_id])
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_update_desc(args):
    if not os.path.isfile(args.file):
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
        
    with open(args.file, "r", encoding="utf-8") as f:
        desc_content = f.read()

    # Pass description via stdin to avoid shell argument length/escaping issues
    cmd = ["ticket", "update", args.ticket_id, "--description-stdin"]
    out = run_mop_raw(cmd, input_data=desc_content)
    print(out)


def cmd_add_comment(args):
    if args.file:
        if not os.path.isfile(args.file):
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            comment_content = f.read()
    elif args.text:
        comment_content = args.text
    else:
        print("Reading comment from standard input (Ctrl+D / Ctrl+Z to finish)...", file=sys.stderr)
        comment_content = sys.stdin.read()

    cmd = ["ticket", "comment", "create", args.ticket_id, "--content-stdin"]
    out = run_mop_raw(cmd, input_data=comment_content)
    print(out)


def main():
    parser = argparse.ArgumentParser(description="Mopheus Ticket & Comment Helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # get
    p_get = subparsers.add_parser("get", help="Get ticket details JSON")
    p_get.add_argument("ticket_id", help="Ticket UUID or number")
    p_get.set_defaults(func=cmd_get)

    # list
    p_list = subparsers.add_parser("list", help="List tickets JSON")
    p_list.add_argument("--status", help="Filter by status (open, in_progress, in_review, done, closed)")
    p_list.add_argument("--project", help="Filter by project UUID or slug")
    p_list.add_argument("--limit", type=int, default=20, help="Max tickets to list")
    p_list.set_defaults(func=cmd_list)

    # comments
    p_comm = subparsers.add_parser("comments", help="List all comments for a ticket JSON")
    p_comm.add_argument("ticket_id", help="Ticket UUID or number")
    p_comm.set_defaults(func=cmd_comments)

    # update-desc
    p_ud = subparsers.add_parser("update-desc", help="Update ticket description from a Markdown file")
    p_ud.add_argument("ticket_id", help="Ticket UUID")
    p_ud.add_argument("file", help="Path to markdown file")
    p_ud.set_defaults(func=cmd_update_desc)

    # add-comment
    p_ac = subparsers.add_parser("add-comment", help="Add a comment to ticket from file or text")
    p_ac.add_argument("ticket_id", help="Ticket UUID or number")
    p_ac.add_argument("--file", help="Path to markdown file containing comment body")
    p_ac.add_argument("--text", help="Direct comment text string")
    p_ac.set_defaults(func=cmd_add_comment)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
