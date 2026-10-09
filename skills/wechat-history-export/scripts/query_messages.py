#!/usr/bin/env python3
"""query_messages.py -- 在解密后的微信 4.x 数据库中检索并导出消息。

功能特性:
  - 自动将用户传入的微信号(alias)、备注名(remark)、昵称(nick_name)解析为内部 username
  - 遍历合并所有 FTS 分片（message_fts_v4_0 ~ _3），杜绝分片漏扫
  - 自动基于 name2id 表反查会话与发言人
  - 支持关键词、时间范围筛选
  - 默认全量导出（无条数上限截断），支持自定义上限
  - 自动输出易读时间线文本 (digest.txt)、结构化 JSON (matches.json) 及 CSV (chat.csv)
"""
import argparse
import csv
import datetime as dt
import glob
import json
import os
import sqlite3
import sys
from collections import defaultdict


def ts_to_str(ts):
    try:
        return dt.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(ts)


def date_to_ts(s, end_of_day=False):
    if not s:
        return None
    d = dt.datetime.strptime(s, "%Y-%m-%d")
    if end_of_day:
        d = d.replace(hour=23, minute=59, second=59)
    return int(d.timestamp())


def open_ro(path):
    """只读打开 SQLite 数据库，避免修改源数据。"""
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.text_factory = lambda b: b.decode("utf-8", "replace")
    return con


def table_cols(con, table):
    try:
        return [r[1] for r in con.execute(f'PRAGMA table_info("{table}")')]
    except sqlite3.Error:
        return []


def all_tables(con):
    try:
        return [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view')")]
    except sqlite3.Error:
        return []


def pick(cols, *candidates):
    """在列名列表中按优先级挑选一个存在的列。"""
    low = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in low:
            return low[cand.lower()]
    return None


def find_fts_dbs(root):
    hits = []
    for p in glob.glob(os.path.join(root, "**", "*.db"), recursive=True):
        base = os.path.basename(p).lower()
        if "fts" in base:
            hits.append(p)
    return sorted(hits)


def find_content_tables(con):
    shadow_suffix = ("_data", "_idx", "_docsize", "_config", "_content")
    out = []
    for t in all_tables(con):
        if t.lower().endswith(shadow_suffix):
            continue
        cols = table_cols(con, t)
        if not cols:
            continue
        c_content = pick(cols, "acontent", "content", "message_content", "msg_content")
        c_sess = pick(cols, "session_id", "sessionid", "chat_id", "talker_id")
        c_time = pick(cols, "create_time", "createtime", "timestamp", "msg_time")
        if not (c_content and c_sess and c_time):
            continue
        try:
            if con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] == 0:
                continue
        except sqlite3.Error:
            continue
        c_send = pick(cols, "sender_id", "senderid", "from_id", "talker")
        out.append((t, c_content, c_sess, c_send, c_time))
    return out


def load_name2id(con):
    """解析 message_fts.db 中的 name2id 表。"""
    for t in all_tables(con):
        if "name2id" not in t.lower():
            continue
        cols = table_cols(con, t)
        c_name = pick(cols, "user_name", "username", "name", "str_value")
        if not c_name:
            continue
        c_id = pick(cols, "id", "local_id", "rowid")
        sel = f'SELECT {c_id or "rowid"}, "{c_name}" FROM "{t}"'
        try:
            return {int(r[0]): r[1] for r in con.execute(sel) if r[0] is not None}
        except sqlite3.Error:
            continue
    return {}


def load_contacts_index(root):
    """从 contact.db 中构建多维联系人索引:
    - user2display: username -> 显示名(优先 remark > nick_name > alias)
    - query2username: (微信号/备注名/昵称/username) -> username 映射表
    """
    user2display = {}
    query2username = {}

    for path in glob.glob(os.path.join(root, "**", "contact*.db"), recursive=True):
        try:
            con = open_ro(path)
        except sqlite3.Error:
            continue
        for t in all_tables(con):
            cols = table_cols(con, t)
            c_user = pick(cols, "user_name", "username")
            if not c_user:
                continue
            c_remark = pick(cols, "remark")
            c_nick = pick(cols, "nick_name", "nickname", "display_name")
            c_alias = pick(cols, "alias")

            fields = [c for c in [c_user, c_remark, c_nick, c_alias] if c]
            sel = 'SELECT %s FROM "%s"' % (", ".join('"%s"' % c for c in fields), t)
            try:
                for row in con.execute(sel):
                    user = row[0]
                    if not user:
                        continue
                    remark = row[1] if len(row) > 1 and row[1] else ""
                    nick = row[2] if len(row) > 2 and row[2] else ""
                    alias = row[3] if len(row) > 3 and row[3] else ""

                    # 显示名选优
                    disp = remark.strip() or nick.strip() or alias.strip() or user
                    if user not in user2display:
                        user2display[user] = disp

                    # 反查索引全部建上（支持小写对比）
                    for val in (user, alias, remark, nick):
                        if val and str(val).strip():
                            k = str(val).strip().lower()
                            if k not in query2username:
                                query2username[k] = user
            except sqlite3.Error:
                continue
        con.close()
    return user2display, query2username


def resolve_session(query_str, query2username, display_names):
    """自动将用户输入的微信号、备注名或昵称解析为内部真实的 username。"""
    if not query_str:
        return ""
    q = query_str.strip()
    low = q.lower()

    if low in query2username:
        actual_user = query2username[low]
        disp = display_names.get(actual_user, actual_user)
        if q != actual_user:
            print(f"[+] 会话目标解析成功: '{q}' -> 内部 username: '{actual_user}' (名称: '{disp}')")
        return actual_user

    # 模糊包含匹配尝试
    candidates = []
    for k, u in query2username.items():
        if low in k or k in low:
            candidates.append((u, display_names.get(u, u)))
    if candidates:
        # 去重
        seen = set()
        unique = []
        for u, d in candidates:
            if u not in seen:
                seen.add(u)
                unique.append((u, d))
        best_u, best_d = unique[0]
        print(f"[+] 模糊匹配到联系人: '{q}' -> '{best_d}' ({best_u})")
        return best_u

    # 无法解析时直接回退为原始输入
    return q


def main():
    ap = argparse.ArgumentParser(description="微信 4.x 消息检索与多格式导出工具")
    ap.add_argument("--decrypted-dir", required=True, help="解密后的数据库输出目录")
    ap.add_argument("--keywords", default="", help="关键词（多个逗号分隔；留空则全量导出）")
    ap.add_argument("--session", default="", help="目标会话（可为微信号、备注名、昵称或原始 username）")
    ap.add_argument("--since", default="", help="起始日期 YYYY-MM-DD")
    ap.add_argument("--until", default="", help="结束日期 YYYY-MM-DD")
    ap.add_argument("--list", action="store_true", help="只列出会话活跃排行，不导出消息")
    ap.add_argument("--top", type=int, default=15, help="会话排行榜显示数量")
    ap.add_argument("--max-per-session", type=int, default=0, help="单会话最大导出条数（默认 0 表示无限制，全量导出）")
    ap.add_argument("--out-dir", default="out", help="导出文件存放目录")
    args = ap.parse_args()

    root = args.decrypted_dir
    if not os.path.isdir(root):
        print(f"[NG] 目录不存在: {root}")
        return 1

    kws = [k.strip().lower() for k in args.keywords.split(",") if k.strip()]
    t_from = date_to_ts(args.since)
    t_to = date_to_ts(args.until, end_of_day=True)

    fts_dbs = find_fts_dbs(root)
    if not fts_dbs:
        print(f"[NG] 在 {root} 下未找到 *fts*.db。请确认解密已成功完成。")
        return 1
    print(f"[*] 全文检索库: {len(fts_dbs)} 个")

    display_names, query2username = load_contacts_index(root)
    print(f"[*] 联系人索引: {len(display_names)} 位用户")

    target_session = resolve_session(args.session, query2username, display_names)

    by_session = defaultdict(list)
    total_scanned = 0

    for db in fts_dbs:
        try:
            con = open_ro(db)
        except sqlite3.Error as e:
            print(f"[!] 无法打开 {os.path.basename(db)}: {e}")
            continue

        tables = find_content_tables(con)
        if not tables:
            con.close()
            continue
        id2name = load_name2id(con)

        for tbl, c_content, c_sess, c_send, c_time in tables:
            send_expr = '"%s"' % c_send if c_send else "NULL"
            sql = ('SELECT "%s", %s, "%s", "%s" FROM "%s"'
                   % (c_sess, send_expr, c_time, c_content, tbl))
            where, params = [], []
            if t_from is not None:
                where.append('"%s" >= ?' % c_time)
                params.append(t_from)
            if t_to is not None:
                where.append('"%s" <= ?' % c_time)
                params.append(t_to)
            if where:
                sql += " WHERE " + " AND ".join(where)

            try:
                rows = con.execute(sql, params).fetchall()
            except sqlite3.Error as e:
                print(f"[!] 查询失败 {os.path.basename(db)}.{tbl}: {e}")
                continue

            for sid, send_id, ts, content in rows:
                total_scanned += 1
                if not content:
                    continue
                sess_user = id2name.get(int(sid), f"?sid{sid}") if sid is not None else "?"
                if target_session and sess_user != target_session:
                    continue
                if kws:
                    low = str(content).lower()
                    if not any(k in low for k in kws):
                        continue
                sender = id2name.get(int(send_id), f"?uid{send_id}") if send_id else ""
                by_session[sess_user].append({
                    "time": int(ts), "sender": sender, "content": str(content),
                })
        con.close()

    total_hits = sum(len(v) for v in by_session.values())
    print(f"[*] 扫描数据: {total_scanned} 条，匹配消息: {total_hits} 条，涉及会话: {len(by_session)} 个")

    ranked = sorted(by_session.items(), key=lambda kv: len(kv[1]), reverse=True)

    print("\n会话列表:")
    for user, msgs in ranked[:args.top]:
        label = display_names.get(user, user)
        kind = "群聊" if user.endswith("@chatroom") else "私聊"
        print(f"  {len(msgs):>5} 条  [{kind}] {label}")
        if label != user:
            print(f"            内部ID: {user}")

    if args.list:
        return 0

    if not ranked:
        print("[!] 未检索到任何匹配消息。")
        return 0

    os.makedirs(args.out_dir, exist_ok=True)
    digest_path = os.path.join(args.out_dir, "digest.txt")
    json_path = os.path.join(args.out_dir, "matches.json")
    csv_path = os.path.join(args.out_dir, "chat.csv")

    payload = []
    csv_rows = []

    with open(digest_path, "w", encoding="utf-8") as f_txt:
        for user, msgs in ranked[:args.top]:
            label = display_names.get(user, user)
            msgs.sort(key=lambda m: m["time"])

            export_msgs = msgs if args.max_per_session <= 0 else msgs[:args.max_per_session]

            f_txt.write("=" * 72 + "\n")
            f_txt.write(f"会话: {label}  ({user})  共命中 {len(msgs)} 条，本次导出 {len(export_msgs)} 条\n")
            f_txt.write("=" * 72 + "\n")

            session_payload = {
                "session": user, "display": label, "total_count": len(msgs),
                "exported_count": len(export_msgs), "messages": []
            }

            for m in export_msgs:
                sender_name = display_names.get(m["sender"], m["sender"]) or "我"
                text = " ".join(m["content"].split())
                time_str = ts_to_str(m["time"])
                f_txt.write(f"[{time_str}] {sender_name}: {text}\n")

                session_payload["messages"].append({
                    "time": time_str,
                    "ts": m["time"],
                    "sender": sender_name,
                    "sender_id": m["sender"],
                    "content": m["content"]
                })

                csv_rows.append([time_str, label, user, sender_name, m["content"]])

            f_txt.write("\n")
            payload.append(session_payload)

    with open(json_path, "w", encoding="utf-8") as f_json:
        json.dump(payload, f_json, ensure_ascii=False, indent=2)

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(["时间", "会话名称", "会话ID", "发言人", "消息内容"])
        writer.writerows(csv_rows)

    print(f"\n[OK] 对话摘录文本已生成: {digest_path}")
    print(f"[OK] 结构化 JSON 已生成: {json_path}")
    print(f"[OK] 结构化 CSV 已生成: {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
