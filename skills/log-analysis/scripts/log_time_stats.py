#!/usr/bin/env python3
"""
log_time_stats.py - 按时间聚合统计日志中关键词出现频次
用法: python log_time_stats.py [日志文件路径]
       python log_time_stats.py app.log
"""
import sys
import os
import re
from collections import defaultdict

# 常用时间戳格式（按优先级尝试解析）
TIME_PATTERNS = [
    re.compile(r"(\d{4}-\d{2}-\d{2} \d{2})"),        # 2026-04-27 12
    re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2})"),        # 2026-04-27T12
    re.compile(r"(\d{4}/\d{2}/\d{2} \d{2})"),        # 2026/04/27 12
    re.compile(r"(\d{2}/\d{2}/\d{4} \d{2})"),        # 04/27/2026 12
    re.compile(r"(\d{10})"),                          # Unix timestamp (秒)
    re.compile(r"(\d{13})"),                          # Unix timestamp (毫秒)
]

# 默认关键词（统计 ERROR 和 WARNING）
DEFAULT_KEYWORDS = ["ERROR", "WARN", "FATAL", "exception", "failed", "timeout"]

def parse_timestamp(line):
    """从一行日志中提取时间戳前缀"""
    for pat in TIME_PATTERNS:
        m = pat.search(line)
        if m:
            ts = m.group(1)
            # 处理毫秒时间戳
            if ts.isdigit() and len(ts) >= 13:
                import datetime
                try:
                    sec = int(ts[:10])
                    return datetime.datetime.fromtimestamp(sec).strftime("%Y-%m-%d %H")
                except:
                    return ts
            return ts
    return None

def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    keywords = [k.strip().upper() for k in sys.argv[2:]] if len(sys.argv) > 2 else DEFAULT_KEYWORDS

    if filepath and not os.path.exists(filepath):
        print(f"[ERROR] 文件不存在: {filepath}")
        sys.exit(1)

    print(f"[统计] 关键词: {', '.join(keywords)} | 文件: {filepath or 'stdin'}")
    print("=" * 60)

    counts = defaultdict(lambda: defaultdict(int))
    total_lines = 0
    total_match = 0

    try:
        f = open(filepath, "r", encoding="utf-8", errors="replace") if filepath else sys.stdin

        for line in f:
            total_lines += 1
            upper_line = line.upper()
            line_hit = False
            for kw in keywords:
                if kw in upper_line:
                    counts[kw][line.rstrip()[:80]] += 1  # 截断避免过长
                    line_hit = True
                    total_match += 1

        if filepath:
            f.close()
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    # 打印每个关键词 Top 10 最常见行
    for kw in keywords:
        print(f"\n[{kw}] 出现频次 Top 10:")
        sorted_lines = sorted(counts[kw].items(), key=lambda x: -x[1])
        for i, (text, cnt) in enumerate(sorted_lines[:10], 1):
            bar = "█" * min(cnt, 50)
            print(f"  {i:>2}. [{cnt:>4}x] {text}{'...' if counts[kw][text] > 1 and len(text) >= 80 else ''}")

    print(f"\n{'=' * 60}")
    print(f"[汇总] 总行数: {total_lines} | 匹配行: {total_match} | 命中率: {total_match/total_lines*100:.1f}%")

if __name__ == "__main__":
    main()