#!/usr/bin/env python3
"""
HTML Report Generator.
Reads stage_tasks.json and populates dashboard_template.html to produce a standalone,
interactive, and fully offline-capable visualization report.
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def generate_report(stage_file: Path, output_file: Path, template_file: Optional[Path] = None) -> Path:
    """Generate interactive HTML dashboard from stage_tasks.json."""
    if not stage_file.exists():
        raise FileNotFoundError(f"Stage file not found: {stage_file}")

    with open(stage_file, "r", encoding="utf-8") as f:
        stage_data = json.load(f)

    if template_file is None or not template_file.exists():
        template_file = Path(__file__).resolve().parent.parent / "templates" / "dashboard_template.html"

    with open(template_file, "r", encoding="utf-8") as f:
        html_template = f.read()

    meta = stage_data.get("meta", {})
    total_tasks = meta.get("total_tasks", 0)
    success_count = meta.get("success_count", 0)
    failure_count = meta.get("failure_count", 0)
    cancelled_count = meta.get("cancelled_count", 0)
    overall_success_rate = meta.get("overall_success_rate", 0.0)

    total_duration_sec = meta.get("total_duration_seconds", 0.0)
    total_duration_hours = round(total_duration_sec / 3600.0, 1)
    avg_duration_seconds = meta.get("avg_duration_seconds", 0.0)

    total_thinking_sec = meta.get("total_thinking_seconds", 0.0)
    total_thinking_min = round(total_thinking_sec / 60.0, 1)
    avg_thinking_seconds = meta.get("avg_thinking_seconds", 0.0)

    total_tool_calls = meta.get("total_tool_calls", 0)
    distinct_tools_count = len(stage_data.get("summary_by_tool", []))

    total_tokens = meta.get("total_tokens", 0)
    total_input_tokens = meta.get("total_input_tokens", 0)
    total_output_tokens = meta.get("total_output_tokens", 0)
    total_cache_tokens = meta.get("total_cache_tokens", 0)
    avg_tokens = meta.get("avg_tokens", 0)

    total_tokens_m = f"{total_tokens / 1_000_000:.1f}M" if total_tokens >= 1_000_000 else f"{total_tokens:,}"
    total_input_tokens_m = f"{total_input_tokens / 1_000_000:.1f}M" if total_input_tokens >= 1_000_000 else f"{total_input_tokens:,}"
    total_output_tokens_m = f"{total_output_tokens / 1_000_000:.1f}M" if total_output_tokens >= 1_000_000 else f"{total_output_tokens:,}"
    total_cache_tokens_m = f"{total_cache_tokens / 1_000_000:.1f}M" if total_cache_tokens >= 1_000_000 else f"{total_cache_tokens:,}"

    guard_summary = stage_data.get("guard_summary", {})
    guard_kills = guard_summary.get("total_kills", 0)
    guard_alarms = guard_summary.get("total_alarms", 0)
    tasks_killed_count = guard_summary.get("tasks_killed_count", 0)
    tasks_alarmed_count = guard_summary.get("tasks_alarmed_count", 0)
    guard_events_count = guard_summary.get("total_events", 0)

    completion_rate = round(((success_count + failure_count + cancelled_count) / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    agent_options = "".join(
        f'<option value="{ag.get("agent_name")}">{ag.get("agent_name")}</option>'
        for ag in stage_data.get("summary_by_agent", [])
    )

    html = html_template
    html = html.replace("{{workspace_slug}}", str(meta.get("workspace_slug", "dev")))
    html = html.replace("{{time_window}}", str(meta.get("time_window", "全量历史")))
    html = html.replace("{{generated_at}}", str(meta.get("generated_at", "")[:19].replace("T", " ")))
    html = html.replace("{{total_tasks}}", f"{total_tasks:,}")
    html = html.replace("{{overall_success_rate}}", str(overall_success_rate))
    html = html.replace("{{success_count}}", f"{success_count:,}")
    html = html.replace("{{failure_count}}", f"{failure_count:,}")
    html = html.replace("{{cancelled_count}}", f"{cancelled_count:,}")
    html = html.replace("{{completion_rate}}", str(completion_rate))
    html = html.replace("{{avg_duration_seconds}}", str(avg_duration_seconds))
    html = html.replace("{{total_duration_hours}}", str(total_duration_hours))
    html = html.replace("{{total_thinking_min}}", str(total_thinking_min))
    html = html.replace("{{avg_thinking_seconds}}", str(avg_thinking_seconds))
    html = html.replace("{{total_tool_calls}}", f"{total_tool_calls:,}")
    html = html.replace("{{distinct_tools_count}}", str(distinct_tools_count))
    html = html.replace("{{total_tokens_formatted}}", f"{total_tokens:,}")
    html = html.replace("{{total_tokens_m}}", total_tokens_m)
    html = html.replace("{{total_input_tokens_m}}", total_input_tokens_m)
    html = html.replace("{{total_output_tokens_m}}", total_output_tokens_m)
    html = html.replace("{{total_cache_tokens_m}}", total_cache_tokens_m)
    html = html.replace("{{avg_tokens_formatted}}", f"{avg_tokens:,}")
    html = html.replace("{{guard_kills}}", str(guard_kills))
    html = html.replace("{{guard_alarms}}", str(guard_alarms))
    html = html.replace("{{tasks_killed_count}}", str(tasks_killed_count))
    html = html.replace("{{tasks_alarmed_count}}", str(tasks_alarmed_count))
    html = html.replace("{{guard_events_count}}", str(guard_events_count))
    html = html.replace("{{agent_filter_options}}", agent_options)
    html = html.replace("{{STAGE_DATA_JSON}}", json.dumps(stage_data, ensure_ascii=False))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print("[OK] Dashboard HTML report generated:")
    print(f"    - File: {output_file.resolve()}")

    return output_file


def main():
    parser = argparse.ArgumentParser(description="Generate HTML dashboard report from stage_tasks.json")
    parser.add_argument("-w", "--workspace", default="dev", help="Workspace slug")
    parser.add_argument("--data-dir", help="Data directory containing stage_tasks.json")
    parser.add_argument("-o", "--output", help="Output HTML file path")

    args = parser.parse_args()
    env_dir = os.environ.get("MOPHEUS_ANALYTICS_DATA_DIR") or os.environ.get("MOPHEUS_DATA_DIR")
    if args.data_dir:
        data_dir = Path(args.data_dir)
    elif env_dir:
        data_dir = Path(env_dir) / args.workspace
    else:
        data_dir = Path.home() / ".mopheus" / "analytics" / args.workspace

    stage_file = data_dir / "stage_tasks.json"

    if args.output:
        output_file = Path(args.output)
    else:
        today_str = datetime.date.today().strftime("%Y%m%d")
        output_file = data_dir / f"agent_task_report_{args.workspace}_{today_str}.html"

    generate_report(stage_file, output_file)


if __name__ == "__main__":
    main()
