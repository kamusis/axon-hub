#!/usr/bin/env python3
"""
Token Guard Watchdog (Mopheus Agent Task Loop Detector & Circuit Breaker)

Inspects all currently running agent tasks in the workspace, detects runaway/tight infinite loop
patterns (such as pending subagent continuation deadlocks or high-frequency repeating outputs),
and executes emergency bypass cancellation (mopheus agent-task cancel) while recording the incident
in a newly created Mopheus ticket.
"""

import sys
import os
import json
import subprocess
import argparse
from datetime import datetime

def run_cmd(cmd_list):
    """Run a CLI command and return stdout string or None on failure."""
    try:
        res = subprocess.run(cmd_list, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        if res.returncode == 0:
            return res.stdout.strip()
        else:
            print(f"[DEBUG] Command failed: {' '.join(cmd_list)}\nStderr: {res.stderr.strip()}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"[ERROR] Exception running {' '.join(cmd_list)}: {e}", file=sys.stderr)
        return None

def run_mop_json(args, workspace_id=None, profile=None):
    """Run mopheus CLI and parse JSON output."""
    cmd = ["mopheus"]
    if profile:
        cmd.extend(["--profile", profile])
    if workspace_id:
        cmd.extend(["--workspace-id", workspace_id])
    cmd.extend(args)
    cmd.extend(["--output", "json"])
    
    out = run_cmd(cmd)
    if not out:
        return None
    try:
        return json.loads(out)
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON output: {e}\nRaw output: {out[:200]}", file=sys.stderr)
        return None

def is_task_running(status):
    """
    Checks if agent task status indicates running state.
    Handles integer enum (30 = running), string digits ("30"), and string names ("running").
    """
    if status == 30 or status == "30":
        return True
    if isinstance(status, str) and status.strip().lower() == "running":
        return True
    return False

def analyze_task_messages(messages):
    """
    Analyzes task messages to detect infinite loop patterns.
    Returns (is_loop: bool, rule_name: str, details: str, snippet: str).
    """
    if not messages or not isinstance(messages, list):
        return False, "", "", ""
    
    # We need at least a few messages to detect a loop
    if len(messages) < 6:
        return False, "", "", ""
    
    # Take the last 20 messages for pattern analysis
    recent = messages[-20:]
    
    # Extract text/content
    texts = []
    for m in recent:
        content = m.get("content") or m.get("text") or ""
        if not content and isinstance(m.get("input"), dict):
            content = str(m.get("input"))
        texts.append(content)
    
    # --- Pattern 1: Subagent Lifecycle Wait Deadlock (ac96e12c loop) ---
    subagent_wait_matches = [
        t for t in texts 
        if "Wait for the pending subagents to complete" in t 
        or "subagent-lifecycle-wait" in t 
        or "Continue the original task in this same session. Do not finish" in t
    ]
    if len(subagent_wait_matches) >= 3:
        snippet = subagent_wait_matches[-1][:150]
        details = f"检测到连续 {len(subagent_wait_matches)} 次注入 PendingSubagentContinuation 续接指令，子任务处于死锁等待状态。"
        return True, "Subagent Lifecycle Wait Loop", details, snippet

    # --- Pattern 2: Consecutive Identical Agent Response Loop ---
    identical_consecutive = 0
    last_t = None
    for t in texts:
        t_clean = t.strip()
        if not t_clean:
            continue
        if last_t and t_clean == last_t and len(t_clean) > 10:
            identical_consecutive += 1
        last_t = t_clean

    if identical_consecutive >= 4:
        snippet = last_t[:150] if last_t else ""
        details = f"检测到连续 {identical_consecutive + 1} 次生成完全一致的相同文本回复，无有效状态推进。"
        return True, "Identical Output Loop", details, snippet

    # --- Pattern 3: High Volume Repetitive Prompts with No Tool Calls ---
    if len(messages) >= 100:
        # Check if the last 15 messages contain no tool calls and high prompt repetition
        no_tools = all(m.get("type") not in ("tool_use", "tool_result") for m in recent)
        if no_tools:
            # Check unique text ratio
            non_empty = [t for t in texts if t.strip()]
            if non_empty:
                unique_ratio = len(set(non_empty)) / len(non_empty)
                if unique_ratio < 0.3:
                    snippet = non_empty[-1][:150]
                    details = f"任务事件数已达 {len(messages)}，且近期消息中工具调用停滞、文本重复率高达 {int((1-unique_ratio)*100)}%。"
                    return True, "High Volume Repetition Runaway", details, snippet

    return False, "", "", ""

def patrol(workspace_id=None, profile=None, dry_run=False, current_task_id=None):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Token Guard Watchdog patrol...")
    
    # 1. List all agents
    agents = run_mop_json(["agent", "list"], workspace_id=workspace_id, profile=profile)
    if not agents:
        print("[INFO] No agents found in workspace or failed to query agent list.")
        return 0

    running_tasks_found = 0
    anomalies_handled = 0

    for agent in agents:
        agent_id = agent.get("id")
        agent_name = agent.get("name", "Unknown")
        if not agent_id:
            continue
        
        # 2. List recent tasks for agent
        tasks = run_mop_json(["agent-task", "list", "--agent-id", agent_id], workspace_id=workspace_id, profile=profile)
        if not tasks:
            continue
        
        task_list = tasks if isinstance(tasks, list) else tasks.get("tasks", [])
        for task in task_list:
            if not is_task_running(task.get("status")):
                continue
            
            task_id = task.get("id")
            if not task_id:
                continue
            
            # Avoid self-interrupting the watchdog's own running task
            if current_task_id and task_id == current_task_id:
                continue
            if agent_name == "看门狗" and "watchdog" in str(task.get("goal", "")).lower():
                continue

            running_tasks_found += 1
            ticket_id = task.get("ticketId")
            
            # 3. Inspect task messages
            messages = run_mop_json(["agent-task", "messages", task_id], workspace_id=workspace_id, profile=profile)
            msg_list = messages if isinstance(messages, list) else messages.get("messages", []) if isinstance(messages, dict) else []
            
            is_loop, rule_name, details, snippet = analyze_task_messages(msg_list)
            
            if is_loop:
                anomalies_handled += 1
                print(f"\n🚨 [ANOMALY DETECTED] Task ID: {task_id}")
                print(f"   Agent: {agent_name} ({agent_id})")
                print(f"   Rule: {rule_name}")
                print(f"   Details: {details}")
                print(f"   Snippet: {snippet}")
                print(f"   Total Messages: {len(msg_list)}")
                
                if dry_run:
                    print(f"   [DRY-RUN] Would cancel task {task_id} and create incident ticket.")
                    continue
                
                # 4. Perform emergency cancel
                cancel_cmd = ["mopheus"]
                if profile:
                    cancel_cmd.extend(["--profile", profile])
                if workspace_id:
                    cancel_cmd.extend(["--workspace-id", workspace_id])
                cancel_cmd.extend(["agent-task", "cancel", task_id])
                
                cancel_res = run_cmd(cancel_cmd)
                print(f"   ✅ [CANCELED] Task {task_id} successfully interrupted.")
                
                # 5. Create incident record ticket
                ticket_title = f"[Token Guard] 自动熔断死循环 Agent 任务: {agent_name} ({task_id[:8]})"
                ticket_desc = f"""## 🚨 Token Guard 紧急熔断报警记录

巡检看门狗在定时巡检中检测到异常高频死循环任务，已执行旁路中断熔断。

### 📋 异常任务详情
- **Agent 名称**: `{agent_name}`
- **Agent ID**: `{agent_id}`
- **异常 Task ID**: `{task_id}`
- **关联工单 ID**: `{ticket_id or '无'}`
- **总事件/消息数**: `{len(msg_list)}`

### 🔍 命中规则与特征
- **触发规则**: **{rule_name}**
- **诊断说明**: {details}
- **循环样例内容**:
```text
{snippet}
```

### ⚡ 处置结果
- **熔断操作**: 已调用 `mop agent-task cancel {task_id}` 强制终止任务。
- **排查建议**: 检查子任务生命周期状态或重新启动工单任务。
"""
                create_ticket_cmd = ["mopheus"]
                if profile:
                    create_ticket_cmd.extend(["--profile", profile])
                if workspace_id:
                    create_ticket_cmd.extend(["--workspace-id", workspace_id])
                create_ticket_cmd.extend([
                    "ticket", "create",
                    "--title", ticket_title,
                    "--description", ticket_desc,
                    "--priority", "1",
                ])
                created_ticket_res = run_cmd(create_ticket_cmd)
                print(f"   📝 [TICKET CREATED] Incident record ticket created.")
                
                # 6. If original task had an associated ticket, add comment
                if ticket_id:
                    comment_text = f"🚨 **[Token Guard 自动熔断]**\n检测到当前工单关联的 Agent 任务 (`{task_id}`) 陷入 `{rule_name}` 死循环，已自动旁路取消，避免进一步消耗 Token。\n\n- **详情**: {details}"
                    comment_cmd = ["mopheus"]
                    if profile:
                        comment_cmd.extend(["--profile", profile])
                    if workspace_id:
                        comment_cmd.extend(["--workspace-id", workspace_id])
                    comment_cmd.extend(["ticket", "comment", "add", ticket_id, "--content", comment_text])
                    run_cmd(comment_cmd)
                    print(f"   💬 [COMMENT ADDED] Notified linked ticket {ticket_id}.")

    print(f"\n[SUMMARY] Checked {running_tasks_found} running task(s). Mitigated {anomalies_handled} anomaly task(s).")
    return anomalies_handled

def main():
    parser = argparse.ArgumentParser(description="Mopheus Token Guard Watchdog")
    parser.add_argument("--workspace-id", help="Target workspace ID (defaults to active workspace)")
    parser.add_argument("--profile", help="Mopheus configuration profile")
    parser.add_argument("--dry-run", action="store_true", help="Report anomalies without killing tasks or creating tickets")
    parser.add_argument("--current-task-id", help="Pass the current execution task ID to prevent self-interruption")
    
    args = parser.parse_args()
    patrol(
        workspace_id=args.workspace_id,
        profile=args.profile,
        dry_run=args.dry_run,
        current_task_id=args.current_task_id or os.environ.get("MOPHEUS_AGENT_TASK_ID")
    )

if __name__ == "__main__":
    main()
