#!/usr/bin/env python3
"""
Stage Metrics Processor.
Deeply parses all cached agent task raw files and transcripts:
- Filters tasks by time window (e.g. past 24 hours via --since-hours 24).
- Computes Thinking duration, block count, and character volume.
- Extracts all tool invocations (tool:Bash, tool:TaskCreate, tool:TaskUpdate, tool:WebFetch, tool:WebSearch, etc.)
  with per-tool success/failure status and execution duration.
- Computes Token usage and cost metrics.
- Aggregates multi-dimensional statistics by Agent, Tool, and Timeline.
- Produces stage_tasks.json ready for instant visualization.
"""

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_iso_time(ts_str: Optional[str]) -> Optional[datetime.datetime]:
    if not ts_str:
        return None
    try:
        clean = ts_str.replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(clean)
    except Exception:
        return None


def normalize_tool_name(raw_name: str) -> str:
    """Normalize tool names into standard tool:ToolName format."""
    if not raw_name:
        return "tool:Unknown"
    name = raw_name.strip()
    if name.startswith("tool:"):
        return name
    if name.startswith("mcp_"):
        name = name[4:]
    return f"tool:{name}"


def is_tool_result_failure(content: str, output: str, is_error: Optional[bool] = None) -> bool:
    """Determine if a tool execution resulted in failure/error."""
    if is_error is True:
        return True
    combined = f"{content} {output}".lower()
    if "exit status " in combined and not "exit status 0" in combined:
        return True
    if "command failed" in combined or "traceback (most recent call last)" in combined or "failed to execute" in combined or "fatal:" in combined:
        return True
    return False


def extract_transcript_metrics(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_thinking_seconds = 0.0
    thinking_blocks_count = 0
    thinking_chars_count = 0

    tool_calls_list = []
    tool_counts: Dict[str, Dict[str, Any]] = {}
    pending_tool_uses: Dict[str, Dict[str, Any]] = {}

    for i, msg in enumerate(messages):
        msg_type = msg.get("type", "")
        content = msg.get("content", "") or ""
        msg_time = parse_iso_time(msg.get("createdAt") or msg.get("created_at"))

        if msg_type == "thinking" or "<thinking>" in content:
            thinking_blocks_count += 1
            thinking_text = content
            if "<thinking>" in content:
                match = re.search(r"<thinking>(.*?)</thinking>", content, re.DOTALL)
                if match:
                    thinking_text = match.group(1)
            thinking_chars_count += len(thinking_text)

            if i + 1 < len(messages) and msg_time:
                next_time = parse_iso_time(messages[i + 1].get("createdAt") or messages[i + 1].get("created_at"))
                if next_time and next_time >= msg_time:
                    dur = (next_time - msg_time).total_seconds()
                    if 0.1 <= dur <= 300.0:
                        total_thinking_seconds += dur

        elif msg_type == "tool_use":
            tool_name = normalize_tool_name(msg.get("tool") or msg.get("name") or "")
            call_id = msg.get("callId") or msg.get("call_id") or f"call_{i}"

            pending_tool_uses[call_id] = {
                "tool": tool_name,
                "start_time": msg_time,
                "input": msg.get("input") or {},
                "call_id": call_id,
            }

        elif msg_type == "tool_result":
            call_id = msg.get("callId") or msg.get("call_id") or ""
            tool_name = normalize_tool_name(msg.get("tool") or "")
            output = msg.get("output") or msg.get("content") or ""
            is_err = msg.get("isError") or msg.get("is_error")

            duration_sec = 0.0
            if call_id in pending_tool_uses:
                use_info = pending_tool_uses.pop(call_id)
                tool_name = use_info["tool"]
                if use_info["start_time"] and msg_time and msg_time >= use_info["start_time"]:
                    duration_sec = round((msg_time - use_info["start_time"]).total_seconds(), 2)

            failed = is_tool_result_failure(content, output, is_err)
            success = not failed

            if tool_name not in tool_counts:
                tool_counts[tool_name] = {
                    "tool": tool_name,
                    "calls": 0,
                    "success": 0,
                    "failed": 0,
                    "total_duration": 0.0,
                }

            tool_counts[tool_name]["calls"] += 1
            if success:
                tool_counts[tool_name]["success"] += 1
            else:
                tool_counts[tool_name]["failed"] += 1
            tool_counts[tool_name]["total_duration"] += duration_sec

            tool_calls_list.append({
                "tool": tool_name,
                "success": success,
                "duration_seconds": duration_sec,
                "call_id": call_id,
            })

    for call_id, use_info in pending_tool_uses.items():
        tname = use_info["tool"]
        if tname not in tool_counts:
            tool_counts[tname] = {"tool": tname, "calls": 0, "success": 0, "failed": 0, "total_duration": 0.0}
        tool_counts[tname]["calls"] += 1
        tool_counts[tname]["failed"] += 1
        tool_calls_list.append({"tool": tname, "success": False, "duration_seconds": 0.0, "call_id": call_id})

    return {
        "thinking": {
            "duration_seconds": round(total_thinking_seconds, 2),
            "blocks_count": thinking_blocks_count,
            "characters_count": thinking_chars_count,
        },
        "tool_summary": list(tool_counts.values()),
        "tool_calls": tool_calls_list,
        "total_tool_calls": len(tool_calls_list),
    }


def extract_guard_diagnostics(task: Dict[str, Any], guard_explain: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Extract or synthesize guard post-mortem diagnostics from task error and failureReason."""
    if guard_explain and isinstance(guard_explain, dict) and (guard_explain.get("reason") or guard_explain.get("observedMemoryBytes")):
        return guard_explain

    fr = str(task.get("failureReason") or task.get("failure_reason") or "")
    err = str(task.get("error") or "")
    raw_status = str(task.get("status") or "")

    is_guard = False
    watcher = "memory"
    reason = fr or "RESOURCE_LIMIT_EXCEEDED"
    observed_mem = 0
    threshold_mem = 0
    over_budget_ms = 0
    procs = 0

    if fr in ("RESOURCE_LIMIT_EXCEEDED", "PROCESS_LIMIT_EXCEEDED", "IDLE_TIMEOUT") or "guard_tripped" in raw_status:
        is_guard = True
    elif "memory budget" in err or "process count limit" in err or "idle watchdog" in err or "resource limit" in err.lower():
        is_guard = True

    if not is_guard:
        return None

    mem_match = re.search(r"memory budget (\d+) bytes exceeded \(observed: (\d+) bytes(?:, duration: (\d+)s)?\)", err)
    if mem_match:
        threshold_mem = int(mem_match.group(1))
        observed_mem = int(mem_match.group(2))
        if mem_match.group(3):
            over_budget_ms = int(mem_match.group(3)) * 1000
        watcher = "memory"
        reason = "RESOURCE_LIMIT_EXCEEDED"
    elif "process count limit" in err:
        proc_match = re.search(r"process count limit (\d+) exceeded \(observed: (\d+)", err)
        if proc_match:
            procs = int(proc_match.group(2))
        watcher = "process_count"
        reason = "PROCESS_LIMIT_EXCEEDED"
    elif "idle" in err.lower() or fr == "IDLE_TIMEOUT":
        watcher = "idle"
        reason = "IDLE_TIMEOUT"

    return {
        "reason": reason,
        "observedMemoryBytes": observed_mem,
        "thresholdBytes": threshold_mem,
        "observedProcessCount": procs,
        "overBudgetDurationMs": over_budget_ms,
        "killedPIDs": [],
        "cgroupPath": "",
        "source": "daemon_guard",
        "watcher": watcher,
        "killedAt": task.get("completedAt") or task.get("completed_at") or task.get("startedAt") or task.get("started_at"),
    }


def process_stage_data(
    data_dir: Path,
    since_hours: Optional[float] = None,
    since_date: Optional[str] = None,
) -> Dict[str, Any]:
    raw_dir = data_dir / "raw_tasks"
    state_file = data_dir / "state_record.json"

    state = {}
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass

    cutoff_time: Optional[datetime.datetime] = None
    time_window_label = "全量历史"
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    if since_hours is not None and since_hours > 0:
        cutoff_time = now_utc - datetime.timedelta(hours=since_hours)
        time_window_label = f"过去 {since_hours:g} 小时"
    elif since_date:
        parsed_d = parse_iso_time(since_date)
        if parsed_d:
            cutoff_time = parsed_d
            time_window_label = f"自 {since_date} 以来"

    guard_events_file = data_dir / "guard_events.json"
    guard_stats_file = data_dir / "guard_stats.json"
    all_guard_events = []
    if guard_events_file.exists():
        try:
            with open(guard_events_file, "r", encoding="utf-8") as f:
                all_guard_events = json.load(f)
        except Exception:
            pass

    guard_stats = {}
    if guard_stats_file.exists():
        try:
            with open(guard_stats_file, "r", encoding="utf-8") as f:
                guard_stats = json.load(f)
        except Exception:
            pass

    events_by_task: Dict[str, List[Dict[str, Any]]] = {}
    for ev in all_guard_events:
        tid = str(ev.get("agentTaskId") or ev.get("agent_task_id") or ev.get("taskId") or "")
        if tid:
            if tid not in events_by_task:
                events_by_task[tid] = []
            events_by_task[tid].append(ev)

    tickets_map_file = data_dir / "tickets_map.json"
    tickets_map = {}
    if tickets_map_file.exists():
        try:
            with open(tickets_map_file, "r", encoding="utf-8") as f:
                tickets_map = json.load(f)
        except Exception:
            pass

    agents_map_file = data_dir / "agents_map.json"
    agents_map = {}
    if agents_map_file.exists():
        try:
            with open(agents_map_file, "r", encoding="utf-8") as f:
                agents_map = json.load(f)
        except Exception:
            pass

    task_files = list(raw_dir.glob("*.json"))
    main_task_files = [f for f in task_files if not f.name.endswith("_messages.json") and not f.name.endswith("_usage.json") and not f.name.endswith("_guard.json")]

    print(f"[*] Processing {len(main_task_files)} cached agent tasks (filter: {time_window_label})...")

    processed_tasks = []
    total_duration_all = 0.0
    total_thinking_all = 0.0
    total_input_tokens_all = 0
    total_output_tokens_all = 0
    total_cache_tokens_all = 0
    total_tokens_all = 0
    total_tool_calls_all = 0

    status_counts = {"completed": 0, "failed": 0, "cancelled": 0, "running": 0, "queued": 0, "other": 0}
    agent_aggregates: Dict[str, Dict[str, Any]] = {}
    tool_aggregates: Dict[str, Dict[str, Any]] = {}
    timeline_daily: Dict[str, Dict[str, Any]] = {}

    guard_alarms_total = 0
    guard_kills_total = 0
    guard_tasks_alarmed = set()
    guard_tasks_killed = set()
    watcher_counts = {
        "memory": {"alarms": 0, "kills": 0, "total": 0},
        "process_count": {"alarms": 0, "kills": 0, "total": 0},
        "idle": {"alarms": 0, "kills": 0, "total": 0},
        "other": {"alarms": 0, "kills": 0, "total": 0},
    }
    agent_guard_counts: Dict[str, Dict[str, int]] = {}
    killed_forensics_list = []

    for tfile in main_task_files:
        try:
            with open(tfile, "r", encoding="utf-8") as f:
                task = json.load(f)
        except Exception:
            continue

        task_id = task.get("id")
        if not task_id:
            continue

        started_at = parse_iso_time(task.get("startedAt") or task.get("started_at") or task.get("createdAt") or task.get("created_at"))
        completed_at = parse_iso_time(task.get("completedAt") or task.get("completed_at"))

        # Apply cutoff time filter
        if cutoff_time and started_at:
            if started_at < cutoff_time:
                continue

        messages_file = raw_dir / f"{task_id}_messages.json"
        usage_file = raw_dir / f"{task_id}_usage.json"
        guard_file = raw_dir / f"{task_id}_guard.json"

        messages = []
        if messages_file.exists():
            try:
                with open(messages_file, "r", encoding="utf-8") as f:
                    messages = json.load(f)
            except Exception:
                pass

        usage_records = []
        if usage_file.exists():
            try:
                with open(usage_file, "r", encoding="utf-8") as f:
                    usage_records = json.load(f)
            except Exception:
                pass

        guard_explain = None
        if guard_file.exists():
            try:
                with open(guard_file, "r", encoding="utf-8") as f:
                    guard_explain = json.load(f)
            except Exception:
                pass

        task_guard_events = events_by_task.get(task_id, [])
        task_alarms = 0
        task_kills = 0
        for gev in task_guard_events:
            etype = str(gev.get("eventType") or gev.get("event_type") or "")
            watcher = str(gev.get("watcher") or "other")
            if watcher not in watcher_counts:
                watcher = "other"
            if "alarm" in etype:
                task_alarms += 1
                guard_alarms_total += 1
                guard_tasks_alarmed.add(task_id)
                watcher_counts[watcher]["alarms"] += 1
                watcher_counts[watcher]["total"] += 1
            elif "kill" in etype:
                task_kills += 1
                guard_kills_total += 1
                guard_tasks_killed.add(task_id)
                watcher_counts[watcher]["kills"] += 1
                watcher_counts[watcher]["total"] += 1

        # Automatically extract or synthesize guard diagnostics from error & failureReason
        guard_diag = extract_guard_diagnostics(task, guard_explain)
        if guard_diag:
            guard_explain = guard_diag
            if task_kills == 0:
                task_kills += 1
                guard_kills_total += 1
                guard_tasks_killed.add(task_id)
                w = guard_diag.get("watcher", "memory")
                if w in watcher_counts:
                    watcher_counts[w]["kills"] += 1
                    watcher_counts[w]["total"] += 1
                else:
                    watcher_counts["other"]["kills"] += 1
                    watcher_counts["other"]["total"] += 1

                # If not already present in all_guard_events, synthesize an audit event
                if not any((ev.get("agentTaskId") == task_id or ev.get("taskId") == task_id or ev.get("agent_task_id") == task_id) for ev in all_guard_events):
                    all_guard_events.append({
                        "id": f"syn-{task_id[:8]}",
                        "agentTaskId": task_id,
                        "eventType": "guard_kill",
                        "watcher": w,
                        "createdAt": guard_diag.get("killedAt") or (started_at.isoformat() if started_at else None),
                        "payload": {
                            "reason": guard_diag.get("reason"),
                            "observedMemoryBytes": guard_diag.get("observedMemoryBytes"),
                            "thresholdBytes": guard_diag.get("thresholdBytes"),
                            "observedProcessCount": guard_diag.get("observedProcessCount"),
                            "overBudgetDurationMs": guard_diag.get("overBudgetDurationMs"),
                        }
                    })

        duration_sec = 0.0
        if started_at and completed_at and completed_at >= started_at:
            duration_sec = round((completed_at - started_at).total_seconds(), 2)
        elif task.get("durationSeconds"):
            duration_sec = float(task["durationSeconds"])

        raw_status = task.get("status")
        if raw_status in (40, 3, "completed", "COMPLETED"):
            norm_status = "completed"
        elif raw_status in (50, 4, "failed", "FAILED"):
            norm_status = "failed"
        elif raw_status in (60, 5, "cancelled", "CANCELLED"):
            norm_status = "cancelled"
        elif raw_status in (30, 2, "running", "RUNNING"):
            norm_status = "running"
        elif raw_status in (10, 0, "queued", "QUEUED"):
            norm_status = "queued"
        else:
            norm_status = "other"

        status_counts[norm_status] = status_counts.get(norm_status, 0) + 1

        input_tokens = 0
        output_tokens = 0
        cache_read_tokens = 0
        cache_write_tokens = 0

        for u in usage_records:
            input_tokens += u.get("inputTokens") or u.get("promptTokens") or u.get("prompt_tokens") or u.get("input_tokens") or 0
            output_tokens += u.get("outputTokens") or u.get("completionTokens") or u.get("completion_tokens") or u.get("output_tokens") or 0
            cache_read_tokens += u.get("cacheReadTokens") or u.get("cache_read_tokens") or u.get("cachedTokens") or 0
            cache_write_tokens += u.get("cacheWriteTokens") or u.get("cache_write_tokens") or 0

        if input_tokens == 0 and output_tokens == 0 and cache_read_tokens == 0 and "result" in task and isinstance(task["result"], dict):
            res_usage = task["result"].get("usage") or {}
            input_tokens = res_usage.get("inputTokens") or res_usage.get("promptTokens") or res_usage.get("input_tokens") or 0
            output_tokens = res_usage.get("outputTokens") or res_usage.get("completionTokens") or res_usage.get("output_tokens") or 0
            cache_read_tokens = res_usage.get("cacheReadTokens") or res_usage.get("cache_read_tokens") or 0
            cache_write_tokens = res_usage.get("cacheWriteTokens") or res_usage.get("cache_write_tokens") or 0

        cache_tokens = cache_read_tokens + cache_write_tokens
        total_tokens = input_tokens + output_tokens + cache_tokens

        transcript_data = extract_transcript_metrics(messages)
        thinking_sec = transcript_data["thinking"]["duration_seconds"]
        task_tool_calls = transcript_data["total_tool_calls"]

        total_duration_all += duration_sec
        total_thinking_all += thinking_sec
        total_input_tokens_all += input_tokens
        total_output_tokens_all += output_tokens
        total_cache_tokens_all += cache_tokens
        total_tokens_all += total_tokens
        total_tool_calls_all += task_tool_calls

        agent_id = str(task.get("agentId") or task.get("agent_id") or "unknown-agent")
        a_info = agents_map.get(agent_id, {})
        agent_name = task.get("agentName") or a_info.get("name") or f"Agent-{agent_id[:8]}"
        agent_model = task.get("agentModel") or a_info.get("model") or "unknown"

        if agent_id not in agent_guard_counts:
            agent_guard_counts[agent_id] = {"agent_name": agent_name, "alarms": 0, "kills": 0}
        agent_guard_counts[agent_id]["alarms"] += task_alarms
        agent_guard_counts[agent_id]["kills"] += task_kills

        if agent_id not in agent_aggregates:
            agent_aggregates[agent_id] = {
                "agent_id": agent_id,
                "agent_name": agent_name,
                "model": agent_model,
                "task_count": 0,
                "completed_count": 0,
                "failed_count": 0,
                "total_duration": 0.0,
                "total_thinking": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_tokens": 0,
                "total_tokens": 0,
                "guard_alarms": 0,
                "guard_kills": 0,
                "tool_distribution": {},
            }
        ag = agent_aggregates[agent_id]
        ag["task_count"] += 1
        if norm_status == "completed":
            ag["completed_count"] += 1
        elif norm_status == "failed":
            ag["failed_count"] += 1
        ag["total_duration"] += duration_sec
        ag["total_thinking"] += thinking_sec
        ag["input_tokens"] += input_tokens
        ag["output_tokens"] += output_tokens
        ag["cache_tokens"] += cache_tokens
        ag["total_tokens"] += total_tokens
        ag["guard_alarms"] += task_alarms
        ag["guard_kills"] += task_kills

        for tsum in transcript_data["tool_summary"]:
            tname = tsum["tool"]
            ag["tool_distribution"][tname] = ag["tool_distribution"].get(tname, 0) + tsum["calls"]

            if tname not in tool_aggregates:
                tool_aggregates[tname] = {
                    "tool_name": tname,
                    "total_calls": 0,
                    "success_calls": 0,
                    "failed_calls": 0,
                    "total_duration": 0.0,
                }
            tool_aggregates[tname]["total_calls"] += tsum["calls"]
            tool_aggregates[tname]["success_calls"] += tsum["success"]
            tool_aggregates[tname]["failed_calls"] += tsum["failed"]
            tool_aggregates[tname]["total_duration"] += tsum["total_duration"]

        day_key = started_at.strftime("%Y-%m-%d") if started_at else "Unknown"
        if day_key not in timeline_daily:
            timeline_daily[day_key] = {"date": day_key, "total": 0, "completed": 0, "failed": 0, "input_tokens": 0, "output_tokens": 0, "cache_tokens": 0, "tokens": 0, "guard_kills": 0, "guard_alarms": 0}
        timeline_daily[day_key]["total"] += 1
        if norm_status == "completed":
            timeline_daily[day_key]["completed"] += 1
        elif norm_status == "failed":
            timeline_daily[day_key]["failed"] += 1
        timeline_daily[day_key]["input_tokens"] += input_tokens
        timeline_daily[day_key]["output_tokens"] += output_tokens
        timeline_daily[day_key]["cache_tokens"] += cache_tokens
        timeline_daily[day_key]["tokens"] += total_tokens
        timeline_daily[day_key]["guard_kills"] += task_kills
        timeline_daily[day_key]["guard_alarms"] += task_alarms

        failure_reason = task.get("failureReason") or task.get("failure_reason") or task.get("error") or ""
        if guard_explain and not failure_reason:
            failure_reason = f"Runtime Guard Kill: {guard_explain.get('reason', 'resource_over_budget')}"
        elif task_kills > 0 and not failure_reason:
            failure_reason = "Runtime Guard Circuit Breaker Kill"

        if guard_explain:
            killed_forensics_list.append({
                "task_id": task_id,
                "agent_name": agent_name,
                "ticket_title": task.get("ticketTitle") or "",
                "reason": guard_explain.get("reason", "unknown"),
                "observed_memory_bytes": guard_explain.get("observedMemoryBytes", 0),
                "threshold_bytes": guard_explain.get("thresholdBytes", 0),
                "observed_process_count": guard_explain.get("observedProcessCount", 0),
                "over_budget_duration_ms": guard_explain.get("overBudgetDurationMs", 0),
                "killed_pids": guard_explain.get("killedPIDs") or guard_explain.get("killedPids") or [],
                "cgroup_path": guard_explain.get("cgroupPath", ""),
                "killed_at": guard_explain.get("killedAt"),
            })

        ticket_id = str(task.get("ticketId") or task.get("ticket_id") or "")
        t_info = tickets_map.get(ticket_id, {})
        ticket_title = task.get("ticketTitle") or t_info.get("title") or ""
        ticket_key = task.get("ticketKey") or t_info.get("key") or (f"MOC-{t_info.get('number')}" if t_info.get("number") else "")
        ticket_num = t_info.get("number")

        processed_tasks.append({
            "id": task_id,
            "ticket_id": ticket_id,
            "ticket_title": ticket_title,
            "ticket_key": ticket_key,
            "ticket_number": ticket_num,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "model": agent_model,
            "status": norm_status,
            "failure_reason": failure_reason,
            "started_at": started_at.isoformat() if started_at else None,
            "completed_at": completed_at.isoformat() if completed_at else None,
            "duration_seconds": duration_sec,
            "thinking": transcript_data["thinking"],
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "prompt": input_tokens,
                "completion": output_tokens,
                "cache_read": cache_read_tokens,
                "cache_write": cache_write_tokens,
                "cache": cache_tokens,
                "total": total_tokens,
            },
            "tool_summary": transcript_data["tool_summary"],
            "tool_calls_count": task_tool_calls,
            "messages_count": len(messages),
            "guard_alarms_count": task_alarms,
            "guard_kills_count": task_kills,
            "guard_explain": guard_explain,
        })

    # Sort tasks descending by start time
    processed_tasks.sort(key=lambda t: t.get("started_at") or "", reverse=True)

    total_count = len(processed_tasks)
    success_count = status_counts["completed"]
    overall_success_rate = round((success_count / total_count * 100), 2) if total_count > 0 else 0.0

    agent_summary_list = []
    for ag in agent_aggregates.values():
        tc = ag["task_count"]
        succ = ag["completed_count"]
        agent_summary_list.append({
            "agent_id": ag["agent_id"],
            "agent_name": ag["agent_name"],
            "model": ag["model"],
            "task_count": tc,
            "completed_count": succ,
            "failed_count": ag["failed_count"],
            "success_rate": round((succ / tc * 100), 2) if tc > 0 else 0.0,
            "total_duration_seconds": round(ag["total_duration"], 2),
            "avg_duration_seconds": round((ag["total_duration"] / tc), 2) if tc > 0 else 0.0,
            "total_thinking_seconds": round(ag["total_thinking"], 2),
            "avg_thinking_seconds": round((ag["total_thinking"] / tc), 2) if tc > 0 else 0.0,
            "total_exec_seconds": round(max(0.0, ag["total_duration"] - ag["total_thinking"]), 2),
            "avg_exec_seconds": round(max(0.0, (ag["total_duration"] - ag["total_thinking"]) / tc), 2) if tc > 0 else 0.0,
            "thinking_ratio": round((ag["total_thinking"] / ag["total_duration"] * 100), 1) if ag["total_duration"] > 0 else 0.0,
            "total_tokens": ag["total_tokens"],
            "avg_tokens": round(ag["total_tokens"] / tc) if tc > 0 else 0,
            "guard_alarms": ag["guard_alarms"],
            "guard_kills": ag["guard_kills"],
            "tool_distribution": ag["tool_distribution"],
        })
    agent_summary_list.sort(key=lambda x: x["task_count"], reverse=True)

    agent_guard_ranking = []
    for ag_id, g_info in agent_guard_counts.items():
        score = g_info["kills"] * 3 + g_info["alarms"]
        agent_guard_ranking.append({
            "agent_id": ag_id,
            "agent_name": g_info["agent_name"],
            "alarms": g_info["alarms"],
            "kills": g_info["kills"],
            "risk_score": score,
        })
    agent_guard_ranking.sort(key=lambda x: x["risk_score"], reverse=True)

    tool_summary_list = []
    for tg in tool_aggregates.values():
        calls = tg["total_calls"]
        succ = tg["success_calls"]
        tool_summary_list.append({
            "tool_name": tg["tool_name"],
            "total_calls": calls,
            "success_calls": succ,
            "failed_calls": tg["failed_calls"],
            "success_rate": round((succ / calls * 100), 2) if calls > 0 else 0.0,
            "total_duration_seconds": round(tg["total_duration"], 2),
            "avg_duration_seconds": round((tg["total_duration"] / calls), 2) if calls > 0 else 0.0,
        })
    tool_summary_list.sort(key=lambda x: x["total_calls"], reverse=True)

    timeline_list = list(timeline_daily.values())
    timeline_list.sort(key=lambda x: x["date"])

    guard_summary = {
        "total_events": len(all_guard_events),
        "total_alarms": guard_alarms_total,
        "total_kills": guard_kills_total,
        "tasks_alarmed_count": len(guard_tasks_alarmed),
        "tasks_killed_count": len(guard_tasks_killed),
        "watcher_breakdown": watcher_counts,
        "agent_risk_ranking": agent_guard_ranking,
        "killed_forensics": killed_forensics_list,
        "stats": guard_stats,
        "recent_events": all_guard_events[:50],
    }

    stage_data = {
        "meta": {
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "time_window": time_window_label,
            "cutoff_time": cutoff_time.isoformat() if cutoff_time else None,
            "workspace_slug": state.get("workspace_slug", "dev"),
            "workspace_id": state.get("workspace_id", ""),
            "total_tasks": total_count,
            "status_breakdown": status_counts,
            "success_count": success_count,
            "failure_count": status_counts["failed"],
            "cancelled_count": status_counts["cancelled"],
            "overall_success_rate": overall_success_rate,
            "total_duration_seconds": round(total_duration_all, 2),
            "avg_duration_seconds": round(total_duration_all / total_count, 2) if total_count > 0 else 0.0,
            "total_thinking_seconds": round(total_thinking_all, 2),
            "total_tokens": total_tokens_all,
            "total_input_tokens": total_input_tokens_all,
            "total_output_tokens": total_output_tokens_all,
            "total_cache_tokens": total_cache_tokens_all,
            "avg_tokens": round(total_tokens_all / total_count) if total_count > 0 else 0,
            "total_tool_calls": total_tool_calls_all,
            "guard_alarms_total": guard_alarms_total,
            "guard_kills_total": guard_kills_total,
            "tasks_killed_count": len(guard_tasks_killed),
        },
        "guard_summary": guard_summary,
        "summary_by_agent": agent_summary_list,
        "summary_by_tool": tool_summary_list,
        "timeline": timeline_list,
        "tasks": processed_tasks,
    }

    stage_file = data_dir / "stage_tasks.json"
    with open(stage_file, "w", encoding="utf-8") as f:
        json.dump(stage_data, f, ensure_ascii=False, indent=2)

    print("[OK] Stage metrics generated successfully:")
    print(f"    - Filter Window:   {time_window_label}")
    print(f"    - Output:          {stage_file}")
    print(f"    - Matching tasks:  {total_count}")
    print(f"    - Success rate:    {overall_success_rate}%")
    print(f"    - Total tokens:    {total_tokens_all:,}")
    print(f"    - Distinct tools:  {len(tool_summary_list)} ({total_tool_calls_all} calls)")

    return stage_data


def main():
    parser = argparse.ArgumentParser(description="Process cached agent task transcripts into stage metrics JSON")
    parser.add_argument("-w", "--workspace", default="dev", help="Workspace slug")
    parser.add_argument("--since-hours", type=float, help="Only include tasks started in the past N hours (e.g. 24)")
    parser.add_argument("--since", help="Only include tasks started after ISO datetime (e.g. 2026-08-25T00:00:00Z)")
    parser.add_argument("--data-dir", help="Data directory containing raw_tasks (default: ~/.mopheus/analytics/<workspace>)")

    args = parser.parse_args()
    env_dir = os.environ.get("MOPHEUS_ANALYTICS_DATA_DIR") or os.environ.get("MOPHEUS_DATA_DIR")
    if args.data_dir:
        data_dir = Path(args.data_dir)
    elif env_dir:
        data_dir = Path(env_dir) / args.workspace
    else:
        data_dir = Path.home() / ".mopheus" / "analytics" / args.workspace

    process_stage_data(data_dir, since_hours=args.since_hours, since_date=args.since)


if __name__ == "__main__":
    main()
