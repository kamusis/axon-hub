#!/usr/bin/env python3
"""
log_grep.py - 日志关键词上下文搜索
用法: python log_grep.py <关键词> [日志文件路径]
示例: python log_grep.py "shutdown|ERROR" app.log
       python log_grep.py "xlog"                   # 从 stdin 读
"""
import sys
import os

DEFAULT_KEYWORDS = ["error", "shutdown", "fatal", "abnormal", "terminated"]

def main():
    keywords = sys.argv[1].split("|") if len(sys.argv) > 1 else DEFAULT_KEYWORDS
    filepath = sys.argv[2] if len(sys.argv) > 2 else None

    if filepath and not os.path.exists(filepath):
        print(f"[ERROR] 文件不存在: {filepath}")
        sys.exit(1)

    # 从文件或 stdin 读取
    try:
        if filepath:
            f = open(filepath, "r", encoding="utf-8", errors="replace")
        else:
            f = sys.stdin
            filepath = "<stdin>"

        buf = []
        match_count = 0
        print(f"[grep] 关键词: {' | '.join(keywords)} | 文件: {filepath}")
        print("=" * 80)

        for i, line in enumerate(f, 1):
            hit = any(kw.lower() in line.lower() for kw in keywords)
            buf.append((i, line))

            if hit:
                match_count += 1
                # 打印前10行上下文
                context = buf[max(0, len(buf) - 11):]
                for ln, txt in context:
                    flag = " >>> " if any(kw.lower() in txt.lower() for kw in keywords) else "     "
                    print(f"{flag} {ln:>8}: {txt.rstrip()}")
                print("-" * 80)
                buf = []  # 重置缓冲，避免重复打印

        if filepath != "<stdin>":
            f.close()

        print(f"\n[OK] 共匹配 {match_count} 处")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()