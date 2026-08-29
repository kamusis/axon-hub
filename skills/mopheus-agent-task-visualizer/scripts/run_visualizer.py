#!/usr/bin/env python3
"""
Mopheus Agent Task Visualizer One-Click Runner.
Orchestrates:
1. Incremental Raw Collection (collect_raw_tasks.py)
2. Stage Metrics Aggregation & Transcript Parsing (process_stage_metrics.py)
3. Interactive HTML Report Generation (generate_html_report.py)
"""

import argparse
import datetime
import os
import sys
import webbrowser
from pathlib import Path

from mopheus_client import MopheusClient
from collect_raw_tasks import collect_raw_data
from process_stage_metrics import process_stage_data
from generate_html_report import generate_report


def run_pipeline(
    workspace: str = "dev",
    profile: str = "",
    server_url: str = "",
    token: str = "",
    since_hours: Optional[float] = None,
    since_date: Optional[str] = None,
    data_dir: str = "",
    output_html: str = "",
    force_refresh: bool = False,
    open_browser: bool = False,
) -> Path:
    print("=================================================================")
    print("[RUN] Mopheus Agent Task Visualizer Pipeline")
    print("=================================================================")

    client = MopheusClient(
        workspace_slug_or_id=workspace,
        profile=profile,
        server_url=server_url,
        token=token,
    )

    env_dir = os.environ.get("MOPHEUS_ANALYTICS_DATA_DIR") or os.environ.get("MOPHEUS_DATA_DIR")
    if data_dir:
        base_data_dir = Path(data_dir)
    elif env_dir:
        base_data_dir = Path(env_dir) / client.workspace_slug
    else:
        base_data_dir = Path.home() / ".mopheus" / "analytics" / client.workspace_slug

    base_data_dir.mkdir(parents=True, exist_ok=True)
    print(f"[*] Target Workspace: {client.workspace_slug}")
    print(f"[*] Storage Directory: {base_data_dir}")
    if since_hours:
        print(f"[*] Time Filter:      Past {since_hours:g} Hours")

    print("\n--- Step 1: Incremental Raw Tasks & Transcripts Collection ---")
    collect_raw_data(client, base_data_dir, force_refresh=force_refresh)

    print("\n--- Step 2: Stage Metrics & Transcript Deep-Dive Processing ---")
    process_stage_data(base_data_dir, since_hours=since_hours, since_date=since_date)

    print("\n--- Step 3: Generating Standalone Interactive HTML Report ---")
    stage_file = base_data_dir / "stage_tasks.json"
    if output_html:
        out_file = Path(output_html)
    else:
        today_str = datetime.date.today().strftime("%Y%m%d")
        suffix = f"_{int(since_hours)}h" if since_hours else ""
        out_file = base_data_dir / f"agent_task_report_{client.workspace_slug}_{today_str}{suffix}.html"

    report_path = generate_report(stage_file, out_file)

    print("\n=================================================================")
    print(f"[OK] Visualization Report Ready: {report_path.resolve()}")
    print("=================================================================")

    if open_browser:
        try:
            webbrowser.open(report_path.resolve().as_uri())
        except Exception:
            pass

    return report_path


def main():
    parser = argparse.ArgumentParser(description="Mopheus Agent Task Visualizer One-Click Runner")
    parser.add_argument("-w", "--workspace", default="dev", help="Mopheus workspace slug or ID (default: dev)")
    parser.add_argument("-p", "--profile", default="", help="Mopheus CLI profile")
    parser.add_argument("-s", "--server-url", help="Mopheus server URL")
    parser.add_argument("-t", "--token", help="Mopheus API auth token")
    parser.add_argument("--since-hours", type=float, help="Only include tasks started in the past N hours (e.g. 24)")
    parser.add_argument("--since", help="Only include tasks started after ISO datetime (e.g. 2026-08-25T00:00:00Z)")
    parser.add_argument("--data-dir", help="Data directory (default: ~/.mopheus/analytics/<workspace>)")
    parser.add_argument("-o", "--output", help="Output HTML file path")
    parser.add_argument("--force", action="store_true", help="Force re-fetch all completed historical tasks")
    parser.add_argument("--open", action="store_true", help="Open generated HTML report in default browser")

    args = parser.parse_args()

    run_pipeline(
        workspace=args.workspace,
        profile=args.profile,
        server_url=args.server_url or "",
        token=args.token or "",
        since_hours=args.since_hours,
        since_date=args.since,
        data_dir=args.data_dir or "",
        output_html=args.output or "",
        force_refresh=args.force,
        open_browser=args.open,
    )


if __name__ == "__main__":
    main()
