#!/usr/bin/env python3
"""
mop_job.py - Advanced helper script for managing Mopheus Jobs and Triggers.
Handles complex JSON outputs, event filter schemas, and trigger updates.
"""

import argparse
import json
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mop_client import run_mop_json, run_mop_raw


def cmd_get(args):
    data = run_mop_json(["job", "get", args.job_id])
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_list(args):
    data = run_mop_json(["job", "list"])
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_triggers(args):
    data = run_mop_json(["job", "trigger-list", args.job_id])
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_runs(args):
    cmd = ["job", "runs", args.job_id, "--limit", str(args.limit)]
    data = run_mop_json(cmd)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_create(args):
    cmd = [
        "job", "create",
        "--name", args.name,
        "--trigger-type", args.trigger_type,
        "--action-type", args.action_type,
    ]
    if args.description:
        cmd.extend(["--description", args.description])
    if args.instruction:
        cmd.extend(["--instruction", args.instruction])
    if args.action_config:
        cmd.extend(["--action-config", args.action_config])
    
    if args.filter_file:
        with open(args.filter_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        cmd.extend(["--event-filter", content])
    elif args.filter_json:
        cmd.extend(["--event-filter", args.filter_json])
        
    out = run_mop_raw(cmd)
    print(out)


def cmd_update_trigger(args):
    cmd = ["job", "trigger-update", args.job_id, args.trigger_id]
    
    if args.enabled is not None:
        cmd.append(f"--enabled={'true' if args.enabled else 'false'}")
        
    if args.filter_file:
        with open(args.filter_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        cmd.extend(["--event-filter", content])
    elif args.filter_json:
        cmd.extend(["--event-filter", args.filter_json])
        
    if args.cron:
        cmd.extend(["--cron", args.cron])
    if args.label:
        cmd.extend(["--label", args.label])
        
    out = run_mop_raw(cmd)
    print(out)


def cmd_add_trigger(args):
    cmd = ["job", "trigger-add", args.job_id, "--kind", args.kind]
    
    if args.kind == "schedule":
        if not args.cron:
            print("Error: --cron is required for schedule triggers", file=sys.stderr)
            sys.exit(1)
        cmd.extend(["--cron", args.cron])
        if args.timezone:
            cmd.extend(["--timezone", args.timezone])
            
    elif args.kind == "event":
        if args.filter_file:
            with open(args.filter_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
            cmd.extend(["--event-filter", content])
        elif args.filter_json:
            cmd.extend(["--event-filter", args.filter_json])
        else:
            print("Error: --filter-json or --filter-file is required for event triggers", file=sys.stderr)
            sys.exit(1)
            
    if args.label:
        cmd.extend(["--label", args.label])
        
    out = run_mop_raw(cmd)
    print(out)


def cmd_event_schema(args):
    cmd = ["job", "event-schema"]
    if args.event_type:
        cmd.append(args.event_type)
    data = run_mop_json(cmd)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Mopheus Job & Trigger Helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # get
    p_get = subparsers.add_parser("get", help="Get job details JSON")
    p_get.add_argument("job_id", help="Job UUID")
    p_get.set_defaults(func=cmd_get)

    # list
    p_list = subparsers.add_parser("list", help="List all jobs JSON")
    p_list.set_defaults(func=cmd_list)

    # create
    p_create = subparsers.add_parser("create", help="Create a new job (schedule, event, or webhook)")
    p_create.add_argument("--name", required=True, help="Job name")
    p_create.add_argument("--trigger-type", required=True, choices=["schedule", "event", "webhook"], help="Trigger type")
    p_create.add_argument("--action-type", required=True, choices=["create_ticket", "assign_agent", "send_notification"], help="Action type")
    p_create.add_argument("--description", help="Job description")
    p_create.add_argument("--instruction", help="Agent instruction goal / template")
    p_create.add_argument("--action-config", help="Action configuration JSON string")
    p_create.add_argument("--filter-json", help="Inline JSON string for eventFilters")
    p_create.add_argument("--filter-file", help="Path to JSON file containing eventFilters")
    p_create.set_defaults(func=cmd_create)

    # triggers
    p_trig = subparsers.add_parser("triggers", help="List triggers JSON for a job")
    p_trig.add_argument("job_id", help="Job UUID")
    p_trig.set_defaults(func=cmd_triggers)

    # runs
    p_runs = subparsers.add_parser("runs", help="List runs JSON for a job")
    p_runs.add_argument("job_id", help="Job UUID")
    p_runs.add_argument("--limit", type=int, default=5, help="Number of runs to fetch")
    p_runs.set_defaults(func=cmd_runs)

    # update-trigger
    p_ut = subparsers.add_parser("update-trigger", help="Update job trigger")
    p_ut.add_argument("job_id", help="Job UUID")
    p_ut.add_argument("trigger_id", help="Trigger UUID")
    p_ut.add_argument("--enabled", type=lambda v: v.lower() in ("true", "1", "yes"), default=None)
    p_ut.add_argument("--filter-json", help="Inline JSON string for eventFilters")
    p_ut.add_argument("--filter-file", help="Path to JSON file containing eventFilters")
    p_ut.add_argument("--cron", help="Cron expression")
    p_ut.add_argument("--label", help="Trigger label")
    p_ut.set_defaults(func=cmd_update_trigger)

    # add-trigger
    p_at = subparsers.add_parser("add-trigger", help="Add job trigger")
    p_at.add_argument("job_id", help="Job UUID")
    p_at.add_argument("--kind", choices=["schedule", "webhook", "event"], required=True)
    p_at.add_argument("--filter-json", help="Inline JSON string for eventFilters")
    p_at.add_argument("--filter-file", help="Path to JSON file containing eventFilters")
    p_at.add_argument("--cron", help="Cron expression for schedule")
    p_at.add_argument("--timezone", default="UTC", help="Timezone for schedule")
    p_at.add_argument("--label", help="Trigger label")
    p_at.set_defaults(func=cmd_add_trigger)

    # event-schema
    p_es = subparsers.add_parser("event-schema", help="Get event schema and variables")
    p_es.add_argument("event_type", nargs="?", default=None, help="Optional event type (ticket, comment, etc.)")
    p_es.set_defaults(func=cmd_event_schema)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
