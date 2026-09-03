#!/usr/bin/env python3
"""
mop_task.py - Advanced helper script for managing and diagnosing Agent Tasks.
Reconstructs streaming transcripts, tool invocations, bash commands, and error logs cleanly.
"""

import argparse
import json
import os
import re
import sys

# Ensure UTF-8 stdout on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mop_client import run_mop_json, run_mop_raw, create_base_parser, apply_global_args




def cmd_get(args):
    data = run_mop_json(["agent-task", "get", args.task_id])
    print(json.dumps(data, indent=2, ensure_ascii=False))


def reconstruct_transcript(raw_messages, include_thinking=False, tools_only=False, grep_pattern=None):
    """
    Reconstructs continuous text from streaming token chunks, extracts tool calls & results.
    """
    if not isinstance(raw_messages, list):
        return []

    events = []
    current_thought = []
    current_text = []

    def flush_text():
        nonlocal current_text
        if current_text:
            text = "".join(current_text).strip()
            if text and not tools_only:
                events.append({"type": "assistant_text", "content": text})
            current_text = []

    def flush_thought():
        nonlocal current_thought
        if current_thought:
            thought = "".join(current_thought).strip()
            if thought and include_thinking and not tools_only:
                events.append({"type": "thinking", "content": thought})
            current_thought = []

    for msg in raw_messages:
        role = msg.get("role", "")
        mtype = msg.get("type", "")
        content = msg.get("content", "")

        if mtype == "thinking":
            flush_text()
            current_thought.append(content)
        elif mtype == "tool_use":
            flush_thought()
            flush_text()
            events.append({
                "type": "tool_use",
                "tool": msg.get("tool", ""),
                "callId": msg.get("callId", ""),
                "input": msg.get("input", {}),
            })
        elif mtype == "tool_result":
            flush_thought()
            flush_text()
            out_raw = msg.get("output", "")
            # Try to parse inner json output if formatted as {"content":[{"type":"text","text":"..."}]}
            output_text = out_raw
            if isinstance(out_raw, str) and out_raw.startswith("{"):
                try:
                    parsed = json.loads(out_raw)
                    if "content" in parsed and isinstance(parsed["content"], list):
                        output_text = "\n".join(
                            c.get("text", "") for c in parsed["content"] if isinstance(c, dict)
                        )
                except Exception:
                    pass
            events.append({
                "type": "tool_result",
                "tool": msg.get("tool", ""),
                "callId": msg.get("callId", ""),
                "output": output_text,
            })
        elif role == "user":
            flush_thought()
            flush_text()
            if not tools_only:
                events.append({"type": "user", "content": content})
        elif role == "assistant":
            flush_thought()
            current_text.append(content)

    flush_thought()
    flush_text()

    if grep_pattern:
        rgx = re.compile(grep_pattern, re.IGNORECASE)
        filtered = []
        for ev in events:
            text_repr = json.dumps(ev, ensure_ascii=False)
            if rgx.search(text_repr):
                filtered.append(ev)
        return filtered

    return events


def cmd_transcript(args):
    raw_messages = run_mop_json(["agent-task", "messages", args.task_id])
    events = reconstruct_transcript(
        raw_messages,
        include_thinking=args.thinking,
        tools_only=args.tools_only,
        grep_pattern=args.grep,
    )

    if args.step:
        step_idx = args.step - 1
        if 0 <= step_idx < len(events):
            events = [events[step_idx]]
        else:
            print(f"Error: Step {args.step} out of range (1..{len(events)})", file=sys.stderr)
            sys.exit(1)
    elif args.limit and len(events) > args.limit:
        events = events[:args.limit]

    if args.json:
        print(json.dumps(events, indent=2, ensure_ascii=False))
        return

    print(f"=== RECONSTRUCTED TRANSCRIPT FOR TASK {args.task_id} ===")
    print(f"Showing {len(events)} structured steps\n")

    for i, ev in enumerate(events, 1):
        step_num = args.step if args.step else i
        etype = ev["type"]
        if etype == "user":
            print(f"[{step_num}] 👤 USER:\n{ev['content']}\n{'-'*60}")
        elif etype == "thinking":
            print(f"[{step_num}] 💭 THINKING:\n{ev['content']}\n{'-'*60}")
        elif etype == "assistant_text":
            print(f"[{step_num}] 🤖 ASSISTANT:\n{ev['content']}\n{'-'*60}")
        elif etype == "tool_use":
            tool_name = ev.get("tool", "Unknown")
            tool_input = ev.get("input", {})
            print(f"[{step_num}] 🛠️ TOOL CALL: {tool_name}")
            if tool_name.lower() == "bash" and "command" in tool_input:
                print(f"COMMAND:\n{tool_input['command']}")
            else:
                print(f"INPUT: {json.dumps(tool_input, indent=2, ensure_ascii=False)}")
            print("-" * 60)
        elif etype == "tool_result":
            tool_name = ev.get("tool", "Unknown")
            output = ev.get("output", "")
            print(f"[{step_num}] 📋 TOOL RESULT: {tool_name}\nOUTPUT:\n{output.strip()}\n{'-'*60}")


def main():
    base_parser = create_base_parser()
    parser = argparse.ArgumentParser(description="Mopheus Agent Task Helper", parents=[base_parser])
    subparsers = parser.add_subparsers(dest="command", required=True)

    # get
    p_get = subparsers.add_parser("get", help="Get agent task details", parents=[base_parser])
    p_get.add_argument("task_id", help="Agent Task UUID")
    p_get.set_defaults(func=cmd_get)

    # transcript
    p_tr = subparsers.add_parser("transcript", help="Reconstruct cleaned transcript and tool actions", parents=[base_parser])
    p_tr.add_argument("task_id", help="Agent Task UUID")
    p_tr.add_argument("--thinking", action="store_true", help="Include internal thinking/reasoning blocks")
    p_tr.add_argument("--tools-only", action="store_true", help="Show only tool invocations and results")
    p_tr.add_argument("--grep", help="Filter steps matching regex or keyword (e.g. email, error)")
    p_tr.add_argument("--limit", type=int, default=None, help="Limit number of steps to show")
    p_tr.add_argument("--step", type=int, default=None, help="Show a specific 1-indexed step")
    p_tr.add_argument("--json", action="store_true", help="Output as structured JSON")
    p_tr.set_defaults(func=cmd_transcript)

    args = parser.parse_args()
    apply_global_args(args)

    args.func(args)




if __name__ == "__main__":
    main()
