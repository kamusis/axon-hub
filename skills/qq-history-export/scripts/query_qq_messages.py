#!/usr/bin/env python3
"""query_qq_messages.py -- Search and export messages from decrypted QQ NT databases.

Pure Python standard library implementation.
Extracts and parses messages from decrypted SQLite databases (nt_msg.db),
resolves contact and group identities, and exports to TXT, JSON, and CSV.
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

# Reconfigure stdout/stderr on Windows to prevent UnicodeEncodeError with emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def ts_to_str(ts):
    """Convert Unix timestamp to formatted datetime string."""
    try:
        return dt.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(ts)


def date_to_ts(s, end_of_day=False):
    """Convert YYYY-MM-DD string to Unix timestamp."""
    if not s:
        return None
    d = dt.datetime.strptime(s, "%Y-%m-%d")
    if end_of_day:
        d = d.replace(hour=23, minute=59, second=59)
    return int(d.timestamp())


def open_ro(path):
    """Open SQLite database in read-only mode."""
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.text_factory = lambda b: b.decode("utf-8", "replace")
    return con


def read_varint(data, offset):
    """Read a protobuf varint from binary buffer."""
    value = 0
    shift = 0
    while offset < len(data) and shift <= 63:
        b = data[offset]
        offset += 1
        value |= (b & 0x7F) << shift
        if b < 0x80:
            return value, offset
        shift += 7
    return None, offset


def extract_elements_from_blob(data):
    """Recursively parse protobuf wire fields from message blob 40800."""
    texts = []
    offset = 0
    while offset < len(data):
        key, offset = read_varint(data, offset)
        if key is None:
            break
        wire_type = key & 7
        number = key >> 3
        if number <= 0:
            break

        if wire_type == 0:  # Varint
            _, offset = read_varint(data, offset)
        elif wire_type == 1:  # 64-bit
            offset += 8
        elif wire_type == 2:  # Length-delimited
            length, offset = read_varint(data, offset)
            if length is None or offset + length > len(data):
                break
            val = data[offset:offset + length]
            offset += length

            if number == 45101:  # Message text field
                try:
                    s = val.decode("utf-8", "replace").strip()
                    if s:
                        texts.append(s)
                except Exception:
                    pass
            elif number in (45300, 45301, 45302):  # Image
                texts.append("[Image]")
            elif number in (45400, 45402, 45403):  # File
                try:
                    fname = val.decode("utf-8", "ignore").strip()
                    if fname and "." in fname and len(fname) < 100:
                        texts.append(f"[File: {fname}]")
                    else:
                        texts.append("[File]")
                except Exception:
                    texts.append("[File]")
            elif number == 45600:  # Sticker / Emoji
                texts.append("[Sticker]")
            else:
                # Recurse into subfields
                texts.extend(extract_elements_from_blob(val))
        elif wire_type == 5:  # 32-bit
            offset += 4
        else:
            break

    # Clean up adjacent duplicates like [Image] [Image]
    cleaned = []
    for item in texts:
        if not cleaned or item != cleaned[-1] or not item.startswith("["):
            cleaned.append(item)
    return cleaned


def parse_message_text(blob):
    """Extract clean text representation from message protobuf blob."""
    if not blob:
        return ""
    try:
        elems = extract_elements_from_blob(blob)
        if elems:
            return " ".join(elems)
    except Exception:
        pass
    return ""


def load_session_metadata(db_dir):
    """Build contacts and sessions index from decrypted databases."""
    sessions_meta = {}
    query2target = {}

    nt_msg_db = os.path.join(db_dir, "nt_msg.db")
    if os.path.isfile(nt_msg_db):
        try:
            con = open_ro(nt_msg_db)
            # Query recent_contact_v3_table
            tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            if "recent_contact_v3_table" in tables:
                sql = "SELECT [40021], [40030], [40093], [40094], [40095] FROM recent_contact_v3_table"
                for row in con.execute(sql):
                    peer_uid, peer_qq, name, nick, remark = row
                    uin_str = str(peer_qq) if peer_qq and peer_qq != 0 else ""
                    disp = (remark or nick or name or uin_str or peer_uid or "").strip()
                    if not disp:
                        continue
                    key = uin_str or peer_uid
                    sessions_meta[key] = {
                        "peer_uid": str(peer_uid or ""),
                        "peer_qq": uin_str,
                        "display": disp,
                        "name": name or "",
                        "nick": nick or "",
                        "remark": remark or "",
                    }
                    for cand in [uin_str, peer_uid, remark, nick, name]:
                        if cand and str(cand).strip():
                            k = str(cand).strip().lower()
                            if k not in query2target:
                                query2target[k] = key
            con.close()
        except Exception as e:
            print(f"[!] Warning reading contacts from nt_msg.db: {e}")

    # Also load from profile_info.db if available
    profile_db = os.path.join(db_dir, "profile_info.db")
    if os.path.isfile(profile_db):
        try:
            con = open_ro(profile_db)
            tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            if "buddy_list" in tables:
                for row in con.execute("SELECT [1000], [1001], [1002] FROM buddy_list"):
                    uid, remark, uin = row
                    uin_str = str(uin) if uin else ""
                    if not uin_str:
                        continue
                    disp = remark.strip() if remark and remark.strip() else uin_str
                    if uin_str not in sessions_meta:
                        sessions_meta[uin_str] = {
                            "peer_uid": str(uid or ""),
                            "peer_qq": uin_str,
                            "display": disp,
                            "name": "",
                            "nick": "",
                            "remark": remark or "",
                        }
                    for cand in [uin_str, uid, remark]:
                        if cand and str(cand).strip():
                            k = str(cand).strip().lower()
                            if k not in query2target:
                                query2target[k] = uin_str
            con.close()
        except Exception:
            pass

    return sessions_meta, query2target


def resolve_session_query(query_str, query2target, sessions_meta):
    """Resolve user input (QQ number, nickname, remark, group name) to target session identifier."""
    if not query_str:
        return ""
    q = query_str.strip()
    low = q.lower()

    if low in query2target:
        target = query2target[low]
        disp = sessions_meta.get(target, {}).get("display", target)
        print(f"[+] Target session resolved: '{q}' -> '{disp}' (ID: {target})")
        return target

    # Fuzzy substring search
    candidates = []
    for k, target in query2target.items():
        if low in k or k in low:
            disp = sessions_meta.get(target, {}).get("display", target)
            candidates.append((target, disp))

    if candidates:
        # Deduplicate
        seen = set()
        unique = []
        for t, d in candidates:
            if t not in seen:
                seen.add(t)
                unique.append((t, d))
        best_target, best_disp = unique[0]
        print(f"[+] Fuzzy matched target session: '{q}' -> '{best_disp}' (ID: {best_target})")
        return best_target

    return q


def find_decrypted_db(root_dir):
    """Find the path to the decrypted nt_msg.db."""
    if os.path.isfile(os.path.join(root_dir, "nt_msg.db")):
        return os.path.join(root_dir, "nt_msg.db"), root_dir

    for candidate in glob.glob(os.path.join(root_dir, "**", "nt_msg.db"), recursive=True):
        return candidate, os.path.dirname(candidate)

    return None, None


def main():
    ap = argparse.ArgumentParser(description="Search and export decrypted QQ NT messages")
    ap.add_argument("--decrypted-dir", required=True, help="Directory containing decrypted SQLite databases")
    ap.add_argument("--keywords", default="", help="Comma-separated keywords; empty matches all")
    ap.add_argument("--session", default="", help="Target session (QQ number, friend remark/nick, or group name)")
    ap.add_argument("--since", default="", help="Start date YYYY-MM-DD")
    ap.add_argument("--until", default="", help="End date YYYY-MM-DD")
    ap.add_argument("--list", action="store_true", help="List active session rankings only without exporting content")
    ap.add_argument("--top", type=int, default=15, help="Number of top sessions to display/export")
    ap.add_argument("--max-per-session", type=int, default=0, help="Max messages to export per session (0 = unlimited)")
    ap.add_argument("--out-dir", default="out", help="Output directory for exported files")
    args = ap.parse_args()

    msg_db_path, db_dir = find_decrypted_db(args.decrypted_dir)
    if not msg_db_path or not os.path.isfile(msg_db_path):
        print(f"[!] No nt_msg.db found in {args.decrypted_dir}. Please ensure decrypt_qq.py completed successfully.")
        return 1

    print("=" * 60)
    print("QQ NT Message Query & Export Tool")
    print("=" * 60)
    print(f"[*] Database file: {msg_db_path}")

    sessions_meta, query2target = load_session_metadata(db_dir)
    print(f"[*] Session metadata loaded: {len(sessions_meta)} sessions indexed")

    my_uin = os.path.basename(db_dir) if os.path.basename(db_dir).isdigit() else ""

    target_session = resolve_session_query(args.session, query2target, sessions_meta)

    kws = [k.strip().lower() for k in args.keywords.split(",") if k.strip()]
    t_from = date_to_ts(args.since)
    t_to = date_to_ts(args.until, end_of_day=True)

    con = open_ro(msg_db_path)
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]

    by_session = defaultdict(list)
    total_scanned = 0

    # 1. Query Friend / Direct messages (c2c_msg_table)
    if "c2c_msg_table" in tables:
        sql = (
            "SELECT [40001], [40050], [40013], [40020], [40033], [40021], [40030], [40090], [40800] "
            "FROM c2c_msg_table"
        )
        where = []
        params = []
        if t_from is not None:
            where.append("[40050] >= ?")
            params.append(t_from)
        if t_to is not None:
            where.append("[40050] <= ?")
            params.append(t_to)
        if where:
            sql += " WHERE " + " AND ".join(where)

        try:
            for row in con.execute(sql, params):
                total_scanned += 1
                msg_id, ts, direction, s_uid, s_qq, p_uid, p_qq, sender_nick, blob = row
                uin_str = str(p_qq) if p_qq and p_qq != 0 else ""
                sess_id = uin_str or p_uid or "Unknown"

                # Filter target session
                if target_session:
                    if target_session not in (sess_id, uin_str, p_uid, str(s_qq)):
                        continue

                content = parse_message_text(blob)
                if not content:
                    continue

                if kws and not any(k in content.lower() for k in kws):
                    continue

                # In NTQQ, direction: 2 = sent (Me), 0 = received
                is_me = (direction == 2) or (my_uin and str(s_qq) == my_uin)
                if is_me:
                    sender_name = "Me"
                else:
                    peer_meta = sessions_meta.get(str(s_qq), {}) or sessions_meta.get(p_uid, {})
                    sender_name = peer_meta.get("display") or sender_nick or (str(s_qq) if s_qq else s_uid)

                by_session[sess_id].append({
                    "time": int(ts),
                    "sender": sender_name,
                    "sender_qq": s_qq,
                    "content": content,
                    "kind": "Direct",
                })
        except Exception as e:
            print(f"[!] Error querying c2c_msg_table: {e}")

    # 2. Query Group messages (group_msg_table)
    if "group_msg_table" in tables:
        sql = (
            "SELECT [40001], [40050], [40013], [40020], [40033], [40021], [40030], [40090], [40800] "
            "FROM group_msg_table"
        )
        where = []
        params = []
        if t_from is not None:
            where.append("[40050] >= ?")
            params.append(t_from)
        if t_to is not None:
            where.append("[40050] <= ?")
            params.append(t_to)
        if where:
            sql += " WHERE " + " AND ".join(where)

        try:
            for row in con.execute(sql, params):
                total_scanned += 1
                msg_id, ts, direction, s_uid, s_qq, p_uid, p_qq, sender_nick, blob = row
                group_id = str(p_qq) if p_qq and p_qq != 0 else str(p_uid or "Unknown")

                # Filter target session
                if target_session:
                    if target_session not in (group_id, str(p_uid), str(p_qq)):
                        continue

                content = parse_message_text(blob)
                if not content:
                    continue

                if kws and not any(k in content.lower() for k in kws):
                    continue

                is_me = (direction == 2) or (my_uin and str(s_qq) == my_uin)
                if is_me:
                    sender_name = "Me"
                else:
                    peer_meta = sessions_meta.get(str(s_qq), {})
                    sender_name = sender_nick or peer_meta.get("display") or (str(s_qq) if s_qq else s_uid)

                by_session[group_id].append({
                    "time": int(ts),
                    "sender": sender_name,
                    "sender_qq": s_qq,
                    "content": content,
                    "kind": "Group",
                })
        except Exception as e:
            print(f"[!] Error querying group_msg_table: {e}")

    con.close()

    total_hits = sum(len(v) for v in by_session.values())
    print(f"[*] Scanned: {total_scanned} records, Matched: {total_hits} messages across {len(by_session)} sessions")

    ranked = sorted(by_session.items(), key=lambda kv: len(kv[1]), reverse=True)

    print("\nSession Ranking:")
    for sess_id, msgs in ranked[:args.top]:
        kind = msgs[0]["kind"] if msgs else "Chat"
        disp = sessions_meta.get(sess_id, {}).get("display", sess_id)
        print(f"  {len(msgs):>5} msgs  [{kind}] {disp} (ID: {sess_id})")

    if args.list:
        return 0

    if not ranked:
        print("[!] No matching messages found.")
        return 0

    os.makedirs(args.out_dir, exist_ok=True)
    digest_path = os.path.join(args.out_dir, "digest.txt")
    json_path = os.path.join(args.out_dir, "matches.json")
    csv_path = os.path.join(args.out_dir, "chat.csv")

    payload = []
    csv_rows = []

    with open(digest_path, "w", encoding="utf-8") as f_txt:
        for sess_id, msgs in ranked[:args.top]:
            msgs.sort(key=lambda m: m["time"])
            kind = msgs[0]["kind"] if msgs else "Chat"
            disp = sessions_meta.get(sess_id, {}).get("display", sess_id)

            export_msgs = msgs if args.max_per_session <= 0 else msgs[:args.max_per_session]

            f_txt.write("=" * 72 + "\n")
            f_txt.write(f"Session: {disp}  ({kind} ID: {sess_id})  Matched: {len(msgs)}, Exported: {len(export_msgs)}\n")
            f_txt.write("=" * 72 + "\n")

            session_payload = {
                "session_id": sess_id,
                "display": disp,
                "kind": kind,
                "total_count": len(msgs),
                "exported_count": len(export_msgs),
                "messages": [],
            }

            for m in export_msgs:
                time_str = ts_to_str(m["time"])
                sender_name = m["sender"]
                text = m["content"]

                f_txt.write(f"[{time_str}] {sender_name}: {text}\n")

                session_payload["messages"].append({
                    "time": time_str,
                    "ts": m["time"],
                    "sender": sender_name,
                    "sender_qq": m.get("sender_qq"),
                    "content": text,
                })

                csv_rows.append([time_str, disp, sess_id, kind, sender_name, text])

            f_txt.write("\n")
            payload.append(session_payload)

    with open(json_path, "w", encoding="utf-8") as f_json:
        json.dump(payload, f_json, ensure_ascii=False, indent=2)

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(["Time", "Session", "Session_ID", "Type", "Sender", "Content"])
        writer.writerows(csv_rows)

    print(f"\n[OK] Digest text -> {digest_path}")
    print(f"[OK] Structured JSON -> {json_path}")
    print(f"[OK] Structured CSV -> {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
