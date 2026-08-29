#!/usr/bin/env python3
"""
Incremental Raw Agent Task Data Collector.
Reads and updates state_record.json to ensure completed historical tasks
are never re-fetched or re-parsed.
Downloads new / active task details, usage, and transcript messages into raw cache.
"""

import argparse
import concurrent.futures
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from mopheus_client import MopheusClient


STATUS_NAMES = {
    1: "deferred",
    10: "queued",
    20: "dispatched",
    30: "running",
    40: "completed",
    50: "failed",
    60: "cancelled",
    0: "queued",
    2: "running",
    3: "completed",
    4: "failed",
    5: "cancelled",
}


def normalize_status(status_val: Any) -> str:
    if isinstance(status_val, int):
        return STATUS_NAMES.get(status_val, str(status_val))
    if isinstance(status_val, str):
        return status_val.lower()
    return "unknown"


def is_terminal_status(status_val: Any) -> bool:
    norm = normalize_status(status_val)
    return norm in ("completed", "failed", "cancelled")


def load_state_record(state_file: Path, workspace_slug: str, workspace_id: str) -> Dict[str, Any]:
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            print(f"[WARN] Failed to read state record {state_file}: {e}. Initializing fresh state.")

    return {
        "workspace_slug": workspace_slug,
        "workspace_id": workspace_id,
        "last_synced_at": None,
        "total_tasks_tracked": 0,
        "processed_task_ids": {},
        "active_task_ids": [],
    }


def save_state_record(state_file: Path, state_data: Dict[str, Any]) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file = state_file.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(state_data, f, ensure_ascii=False, indent=2)
    temp_file.replace(state_file)


def collect_raw_data(
    client: MopheusClient,
    data_dir: Path,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """Collect raw tasks and transcripts incrementally."""
    raw_dir = data_dir / "raw_tasks"
    raw_dir.mkdir(parents=True, exist_ok=True)

    state_file = data_dir / "state_record.json"
    state = load_state_record(state_file, client.workspace_slug, client.workspace_id or "")

    processed_map: Dict[str, Any] = state.get("processed_task_ids", {})
    active_ids: Set[str] = set(state.get("active_task_ids", []))

    print(f"[*] Discovering agent tasks for workspace '{client.workspace_slug}'...")
    all_tasks = client.fetch_all_agent_tasks()
    print(f"[*] Found {len(all_tasks)} total tasks in workspace.")

    agents_map = client.fetch_agents_map()
    tickets_map = client.fetch_tickets_map()

    print(f"[*] Discovering runtime guard events for workspace '{client.workspace_slug}'...")
    guard_events = client.fetch_runtime_guard_events(limit=2000)
    guard_stats = client.fetch_runtime_guard_stats()
    print(f"[*] Found {len(guard_events)} runtime guard events.")

    tasks_with_guard_events: Set[str] = set()
    for ev in guard_events:
        tid = ev.get("agentTaskId") or ev.get("agent_task_id") or ev.get("taskId")
        if tid:
            tasks_with_guard_events.add(str(tid))

    with open(data_dir / "agents_map.json", "w", encoding="utf-8") as f:
        json.dump(agents_map, f, ensure_ascii=False, indent=2)
    with open(data_dir / "tickets_map.json", "w", encoding="utf-8") as f:
        json.dump(tickets_map, f, ensure_ascii=False, indent=2)
    with open(data_dir / "guard_events.json", "w", encoding="utf-8") as f:
        json.dump(guard_events, f, ensure_ascii=False, indent=2)
    if guard_stats:
        with open(data_dir / "guard_stats.json", "w", encoding="utf-8") as f:
            json.dump(guard_stats, f, ensure_ascii=False, indent=2)

    new_processed_count = 0
    skipped_count = 0
    updated_active_count = 0

    tasks_to_fetch = []
    for task in all_tasks:
        task_id = task.get("id")
        if not task_id:
            continue

        raw_task_file = raw_dir / f"{task_id}.json"
        raw_msg_file = raw_dir / f"{task_id}_messages.json"
        raw_guard_file = raw_dir / f"{task_id}_guard.json"

        if not force_refresh and task_id in processed_map and processed_map[task_id].get("terminal"):
            if raw_task_file.exists() and raw_msg_file.exists():
                if task_id in tasks_with_guard_events and not raw_guard_file.exists():
                    guard_explain = client.fetch_task_guard_explain(task_id)
                    if guard_explain:
                        with open(raw_guard_file, "w", encoding="utf-8") as f:
                            json.dump(guard_explain, f, ensure_ascii=False, indent=2)
                skipped_count += 1
                continue

        tasks_to_fetch.append(task)

    def process_single_task(task_item: Dict[str, Any]) -> Tuple[str, Dict[str, Any], bool]:
        t_id = task_item.get("id")
        raw_t_file = raw_dir / f"{t_id}.json"
        raw_m_file = raw_dir / f"{t_id}_messages.json"
        raw_u_file = raw_dir / f"{t_id}_usage.json"
        raw_g_file = raw_dir / f"{t_id}_guard.json"

        t_status = normalize_status(task_item.get("status"))
        t_terminal = is_terminal_status(task_item.get("status"))

        msgs = client.fetch_task_messages(t_id)
        usg = client.fetch_task_usage(t_id)

        g_explain = None
        if t_status in ("failed", "cancelled") or t_id in tasks_with_guard_events:
            g_explain = client.fetch_task_guard_explain(t_id)

        ag_id = task_item.get("agentId") or task_item.get("agent_id")
        if ag_id and ag_id in agents_map:
            task_item["agentName"] = agents_map[ag_id].get("name", "Unknown Agent")
            task_item["agentModel"] = agents_map[ag_id].get("model", "unknown")

        tk_id = task_item.get("ticketId") or task_item.get("ticket_id")
        if tk_id and tk_id in tickets_map:
            task_item["ticketTitle"] = tickets_map[tk_id].get("title", "")
            task_item["ticketKey"] = tickets_map[tk_id].get("key", "")

        with open(raw_t_file, "w", encoding="utf-8") as tf:
            json.dump(task_item, tf, ensure_ascii=False, indent=2)
        with open(raw_m_file, "w", encoding="utf-8") as mf:
            json.dump(msgs, mf, ensure_ascii=False, indent=2)
        with open(raw_u_file, "w", encoding="utf-8") as uf:
            json.dump(usg, uf, ensure_ascii=False, indent=2)
        if g_explain:
            with open(raw_g_file, "w", encoding="utf-8") as gf:
                json.dump(g_explain, gf, ensure_ascii=False, indent=2)

        meta_res = {
            "status": t_status,
            "terminal": t_terminal,
            "processed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "started_at": task_item.get("startedAt") or task_item.get("started_at"),
            "completed_at": task_item.get("completedAt") or task_item.get("completed_at"),
            "messages_count": len(msgs),
            "usage_count": len(usg),
            "has_guard_events": t_id in tasks_with_guard_events,
            "has_guard_explain": g_explain is not None,
        }
        return t_id, meta_res, t_terminal

    total_to_fetch = len(tasks_to_fetch)
    print(f"[*] Need to synchronize {total_to_fetch} tasks (concurrent 16 workers, {skipped_count} cached)...")

    if total_to_fetch > 0:
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            future_to_task = {executor.submit(process_single_task, t): t for t in tasks_to_fetch}
            completed_tasks = 0
            for future in concurrent.futures.as_completed(future_to_task):
                completed_tasks += 1
                if completed_tasks % 50 == 0 or completed_tasks == total_to_fetch:
                    print(f"[*] Progress: [{completed_tasks}/{total_to_fetch}] tasks synchronized ({completed_tasks * 100 // total_to_fetch}%)...")
                try:
                    t_id, meta_res, t_terminal = future.result()
                    processed_map[t_id] = meta_res
                    if t_terminal:
                        active_ids.discard(t_id)
                        new_processed_count += 1
                    else:
                        active_ids.add(t_id)
                        updated_active_count += 1
                except Exception as ex:
                    print(f"[WARN] Error syncing task: {ex}")

    state["workspace_slug"] = client.workspace_slug
    state["workspace_id"] = client.workspace_id or state.get("workspace_id") or ""
    state["last_synced_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state["total_tasks_tracked"] = len(all_tasks)
    state["processed_task_ids"] = processed_map
    state["active_task_ids"] = list(active_ids)
    state["guard_events_count"] = len(guard_events)

    save_state_record(state_file, state)

    print("\n[OK] Raw collection completed:")
    print(f"    - Skipped already cached terminal tasks: {skipped_count}")
    print(f"    - Newly synchronized tasks:             {new_processed_count}")
    print(f"    - Active / in-flight tasks tracked:      {updated_active_count}")
    print(f"    - Total state records:                  {len(processed_map)}")
    print(f"    - Runtime guard events collected:       {len(guard_events)}")
    print(f"    - State saved to:                       {state_file}")

    return state


def main():
    parser = argparse.ArgumentParser(description="Collect raw agent task data and transcripts incrementally")
    parser.add_argument("-w", "--workspace", help="Workspace slug or ID (default: dev or from config)")
    parser.add_argument("-p", "--profile", default="", help="Mopheus CLI profile")
    parser.add_argument("-s", "--server-url", help="Mopheus server URL")
    parser.add_argument("-t", "--token", help="Mopheus API auth token")
    parser.add_argument("--data-dir", help="Directory to store state and raw files (default: ~/.mopheus/analytics/<workspace>)")
    parser.add_argument("--force", action="store_true", help="Force re-fetching all tasks ignoring state record")

    args = parser.parse_args()

    client = MopheusClient(
        workspace_slug_or_id=args.workspace,
        profile=args.profile,
        server_url=args.server_url,
        token=args.token,
    )

    env_dir = os.environ.get("MOPHEUS_ANALYTICS_DATA_DIR") or os.environ.get("MOPHEUS_DATA_DIR")
    if args.data_dir:
        data_dir = Path(args.data_dir)
    elif env_dir:
        data_dir = Path(env_dir) / client.workspace_slug
    else:
        data_dir = Path.home() / ".mopheus" / "analytics" / client.workspace_slug

    collect_raw_data(client, data_dir, force_refresh=args.force)


if __name__ == "__main__":
    main()
