#!/usr/bin/env python3
"""
mop_ticket.py - Advanced helper script for managing Mopheus Tickets and Comments.
Avoids shell escaping pitfalls for large Markdown descriptions, structured comments,
and handles compound queries like "my uncompleted tickets" with UTF-8 safety.
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



STATUS_NAMES = {
    0: "Backlog",
    1: "Todo",
    2: "In Progress",
    3: "In Review",
    4: "Done",
    5: "Blocked",
    6: "Cancelled",
    7: "Archived"
}

PRIORITY_NAMES = {
    -1: "Low",
    0: "Normal",
    1: "High",
    2: "Urgent",
}


UNCOMPLETED_STATUSES = {0, 1, 2, 3, 5}
STATUS_ORDER = {2: 0, 3: 1, 1: 2, 0: 3, 5: 4}



def format_tickets_markdown(tickets):
    if not tickets:
        return "No tickets found matching criteria."

    lines = [
        "| # | Status | Priority | Title | Ticket ID |",
        "| :--- | :--- | :--- | :--- | :--- |"
    ]
    for t in tickets:
        num = t.get("number", "-")
        st = STATUS_NAMES.get(t.get("status"), str(t.get("status")))
        pr = PRIORITY_NAMES.get(t.get("priority"), str(t.get("priority")))
        ticket_title = t.get("title", "").replace("|", "\\|")
        tid = t.get("id", "")
        lines.append(f"| **#{num}** | `{st}` | {pr} | {ticket_title} | `{tid}` |")

    return "\n".join(lines)


def cmd_get(args):
    data = run_mop_json(["ticket", "get", args.ticket_id])
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_list(args):
    assignee_id = None
    user_name = None

    if getattr(args, "mine", False):
        user = get_current_user()
        if user and "id" in user:
            assignee_id = user["id"]
            user_name = user.get("name", "me")
        else:
            print("Error: Could not resolve current user ID for --mine", file=sys.stderr)
            sys.exit(1)
    elif getattr(args, "assignee", None):
        assignee_id = args.assignee

    cmd = ["ticket", "list", "--limit", str(args.limit)]
    if assignee_id:
        cmd.extend(["--assignee-id", assignee_id])
    if getattr(args, "status", None):
        cmd.extend(["--status", args.status])
    if getattr(args, "project", None):
        cmd.extend(["--project", args.project])
    if getattr(args, "priority", None):
        cmd.extend(["--priority", args.priority])

    data = run_mop_json(cmd)
    if not isinstance(data, list):
        data = []

    if getattr(args, "uncompleted", False):
        data = [t for t in data if t.get("status") in UNCOMPLETED_STATUSES]

    # Sort tickets (In Progress first, then In Review, Todo, Backlog, Blocked)
    data.sort(key=lambda t: (STATUS_ORDER.get(t.get("status"), 99), -t.get("number", 0)))

    if getattr(args, "json", False):
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        target_info = f" (Assignee: {user_name})" if user_name else ""
        filter_info = " [Uncompleted only]" if getattr(args, "uncompleted", False) else ""
        print(f"Total matching: {len(data)}{target_info}{filter_info}\n")
        print(format_tickets_markdown(data))


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

    cmd = ["ticket", "comment", "add", args.ticket_id, "--content-stdin"]
    out = run_mop_raw(cmd, input_data=comment_content)
    print(out)



def main():
    base_parser = create_base_parser()
    parser = argparse.ArgumentParser(description="Mopheus Ticket & Comment Helper", parents=[base_parser])
    subparsers = parser.add_subparsers(dest="command", required=True)

    # get
    p_get = subparsers.add_parser("get", help="Get ticket details JSON", parents=[base_parser])
    p_get.add_argument("ticket_id", help="Ticket UUID or number")
    p_get.set_defaults(func=cmd_get)

    # list
    p_list = subparsers.add_parser("list", help="List tickets with advanced filtering and markdown formatting", parents=[base_parser])
    p_list.add_argument("--mine", action="store_true", help="Filter by current authenticated user as assignee")
    p_list.add_argument("--assignee", help="Filter by specific assignee UUID")
    p_list.add_argument("--uncompleted", action="store_true", help="Filter out done, cancelled, and archived tickets")
    p_list.add_argument("--status", help="Filter by status (backlog, todo, in_progress, in_review, done, blocked, cancelled, archived)")
    p_list.add_argument("--priority", help="Filter by priority (low, normal, high, urgent)")
    p_list.add_argument("--project", help="Filter by project UUID or slug")
    p_list.add_argument("--limit", type=int, default=50, help="Max tickets to list")
    p_list.add_argument("--json", action="store_true", help="Output raw JSON instead of Markdown table")
    p_list.set_defaults(func=cmd_list)

    # list-mine (ergonomic shortcut)
    p_mine = subparsers.add_parser("list-mine", help="Shortcut to list current user's uncompleted tickets", parents=[base_parser])
    p_mine.add_argument("--all", action="store_true", help="Include completed, cancelled, and archived tickets")
    p_mine.add_argument("--status", help="Filter by specific status")
    p_mine.add_argument("--priority", help="Filter by priority")
    p_mine.add_argument("--project", help="Filter by project UUID or slug")
    p_mine.add_argument("--limit", type=int, default=50, help="Max tickets to list")
    p_mine.add_argument("--json", action="store_true", help="Output raw JSON instead of Markdown table")

    def _cmd_list_mine(args):
        args.mine = True
        args.uncompleted = not args.all
        cmd_list(args)

    p_mine.set_defaults(func=_cmd_list_mine)


    # comments
    p_comm = subparsers.add_parser("comments", help="List all comments for a ticket JSON", parents=[base_parser])
    p_comm.add_argument("ticket_id", help="Ticket UUID or number")
    p_comm.set_defaults(func=cmd_comments)

    # update-desc
    p_ud = subparsers.add_parser("update-desc", help="Update ticket description from a Markdown file", parents=[base_parser])
    p_ud.add_argument("ticket_id", help="Ticket UUID")
    p_ud.add_argument("file", help="Path to markdown file")
    p_ud.set_defaults(func=cmd_update_desc)

    # add-comment
    p_ac = subparsers.add_parser("add-comment", help="Add a comment to ticket from file or text", parents=[base_parser])
    p_ac.add_argument("ticket_id", help="Ticket UUID or number")
    p_ac.add_argument("--file", help="Path to markdown file containing comment body")
    p_ac.add_argument("--text", help="Direct comment text string")
    p_ac.set_defaults(func=cmd_add_comment)

    args = parser.parse_args()
    apply_global_args(args)

    args.func(args)




if __name__ == "__main__":
    main()
