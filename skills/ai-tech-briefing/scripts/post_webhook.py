#!/usr/bin/env python3
"""
Product News Daily - WeChat Work Webhook Poster

Posts Markdown briefing to Enterprise WeChat webhook with automatic length splitting
to comply with WeChat's 4096-byte limit per message.
"""

import sys
import os
import json
import time
import urllib.request
import urllib.error
import argparse

DEFAULT_MAX_BYTES = 3800  # Leave buffer below WeChat 4096 byte hard limit

def post_message(webhook_url, markdown_content):
    """Post single markdown message payload to WeChat Work webhook."""
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": markdown_content
        }
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            res_json = json.loads(body)
            errcode = res_json.get("errcode", -1)
            errmsg = res_json.get("errmsg", "unknown")
            return errcode, errmsg
    except Exception as e:
        return -1, str(e)

def split_markdown_content(full_content, max_bytes=DEFAULT_MAX_BYTES):
    """Split markdown content by top-level sections if it exceeds byte limit."""
    content_bytes = full_content.encode("utf-8")
    if len(content_bytes) <= max_bytes:
        return [full_content]

    # Split by section headers '## '
    sections = re.split(r'\n(?=##\s+)', full_content)
    if len(sections) <= 1:
        # Fallback to line-by-line split
        lines = full_content.split("\n")
        chunks = []
        cur_lines = []
        cur_len = 0
        for ln in lines:
            ln_len = len(ln.encode("utf-8")) + 1
            if cur_len + ln_len > max_bytes and cur_lines:
                chunks.append("\n".join(cur_lines))
                cur_lines = [ln]
                cur_len = ln_len
            else:
                cur_lines.append(ln)
                cur_len += ln_len
        if cur_lines:
            chunks.append("\n".join(cur_lines))
        return chunks

    header = sections[0]
    body_sections = sections[1:]
    
    chunks = []
    current_chunk = header
    for sec in body_sections:
        test_chunk = current_chunk + "\n" + sec
        if len(test_chunk.encode("utf-8")) > max_bytes and current_chunk != header:
            chunks.append(current_chunk)
            current_chunk = header + "\n" + sec
        else:
            current_chunk = test_chunk
            
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def main():
    import re
    globals()['re'] = re
    
    parser = argparse.ArgumentParser(description="Post Markdown briefing to WeChat Work Webhook")
    parser.add_argument("--url", required=True, help="WeChat Work webhook URL")
    parser.add_argument("--content-file", help="Path to file containing Markdown content")
    parser.add_argument("--content", help="Inline markdown content")
    parser.add_argument("--dry-run", action="store_true", help="Test splitting without sending")
    
    args = parser.parse_args()
    
    if args.content_file:
        with open(args.content_file, "r", encoding="utf-8") as f:
            content = f.read()
    elif args.content:
        content = args.content
    else:
        print("[ERROR] Must provide --content-file or --content", file=sys.stderr)
        sys.exit(1)
        
    chunks = split_markdown_content(content)
    total_chunks = len(chunks)
    print(f"Content prepared: {len(content)} chars ({len(content.encode('utf-8'))} bytes), split into {total_chunks} chunk(s).")
    
    if args.dry_run:
        print("[DRY-RUN] Chunks calculated successfully. Exiting without network call.")
        sys.exit(0)
        
    for i, chunk in enumerate(chunks):
        if total_chunks > 1:
            chunk_header = f"> *(第 {i+1}/{total_chunks} 部分)*\n\n"
            chunk = chunk_header + chunk
            
        errcode, errmsg = post_message(args.url, chunk)
        if errcode == 0:
            print(f"[OK] Chunk {i+1}/{total_chunks} delivered successfully.")
        else:
            print(f"[ERROR] Chunk {i+1}/{total_chunks} failed: errcode={errcode}, errmsg={errmsg}", file=sys.stderr)
            sys.exit(1)
            
        if i < total_chunks - 1:
            time.sleep(1.0)
            
    print("All chunks posted successfully.")

if __name__ == "__main__":
    main()
