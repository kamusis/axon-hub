#!/usr/bin/env python3
"""find_qq.py -- Discover QQ NT processes, data directories, and active accounts.

Checks running QQ.exe processes and scans Tencent Files data directories
to identify active logged-in accounts and database paths.
"""
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys


def get_qq_processes():
    """List running QQ.exe processes with PID and memory usage."""
    try:
        out = subprocess.run(
            ["tasklist", "/fo", "csv", "/nh"],
            capture_output=True, text=True, timeout=15, errors="replace"
        ).stdout
    except Exception as e:
        print(f"[!] Failed to execute tasklist: {e}")
        return []

    found = []
    for line in out.splitlines():
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) < 5:
            continue
        name, pid, mem = parts[0].strip('"'), parts[1], parts[4].rstrip('"')
        low = name.lower()
        if low == "qq.exe":
            kb = int(re.sub(r"[^\d]", "", mem) or "0")
            found.append({"name": name, "pid": int(pid), "mem_kb": kb})
    return found


def get_qq_executable_path(pid):
    """Retrieve full executable path and file version for a given process PID."""
    ps_cmd = (
        f"$p = Get-Process -Id {pid} -ErrorAction SilentlyContinue; "
        "if ($p) { $p.Path; $p.MainModule.FileVersionInfo.FileVersion }"
    )
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=10, errors="replace"
        ).stdout.strip().splitlines()
        if len(res) >= 2:
            return res[0].strip(), res[1].strip()
        elif len(res) == 1:
            return res[0].strip(), "Unknown"
    except Exception:
        pass
    return None, None


def find_tencent_files_roots():
    """Search for 'Tencent Files' data roots across common drives and registry."""
    candidates = []

    # 1. Check user Documents
    user_profile = os.environ.get("USERPROFILE", "")
    if user_profile:
        candidates.append(os.path.join(user_profile, "Documents", "Tencent Files"))

    # 2. Check other fixed drives (e.g. D:, E:)
    for drive in ["D:\\", "E:\\", "F:\\"]:
        if os.path.isdir(drive):
            candidates.append(os.path.join(drive, "Documents", "Tencent Files"))
            candidates.append(os.path.join(drive, "Tencent Files"))

    # 3. Query Windows Registry for custom document or save paths
    reg_cmd = 'Get-ItemProperty "HKCU:\\Software\\Tencent\\*" -ErrorAction SilentlyContinue | Out-String'
    try:
        reg_out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", reg_cmd],
            capture_output=True, text=True, timeout=10, errors="replace"
        ).stdout
        for match in re.findall(r"([A-Za-z]:\\[^\r\n]+)", reg_out):
            clean_path = match.strip()
            if "tencent files" in clean_path.lower():
                candidates.append(clean_path)
            elif os.path.isdir(clean_path):
                candidates.append(os.path.join(clean_path, "Tencent Files"))
    except Exception:
        pass

    valid_roots = []
    seen = set()
    for c in candidates:
        norm = os.path.normpath(c)
        if norm.lower() not in seen and os.path.isdir(norm):
            seen.add(norm.lower())
            valid_roots.append(norm)

    return valid_roots


def scan_accounts(tencent_files_root):
    """Scan account folders inside Tencent Files and find nt_msg.db files."""
    accounts = []
    if not os.path.isdir(tencent_files_root):
        return accounts

    for entry in os.listdir(tencent_files_root):
        account_dir = os.path.join(tencent_files_root, entry)
        if not os.path.isdir(account_dir):
            continue
        # Account folders are usually numeric QQ numbers
        nt_db_dir = os.path.join(account_dir, "nt_qq", "nt_db")
        msg_db = os.path.join(nt_db_dir, "nt_msg.db")
        if os.path.isfile(msg_db):
            st = os.stat(msg_db)
            mtime = dt.datetime.fromtimestamp(st.st_mtime)
            accounts.append({
                "uin": entry,
                "account_dir": account_dir,
                "nt_db_dir": nt_db_dir,
                "msg_db_path": msg_db,
                "msg_db_size_mb": round(st.st_size / (1024 * 1024), 2),
                "last_modified": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                "mtime_ts": st.st_mtime,
            })

    accounts.sort(key=lambda a: a["mtime_ts"], reverse=True)
    return accounts


def main():
    print("=" * 60)
    print("QQ NT Environment & Data Discovery Tool")
    print("=" * 60)

    # 1. Process detection
    procs = get_qq_processes()
    if procs:
        print(f"[*] Found {len(procs)} QQ.exe process(es):")
        for p in procs:
            exe_path, ver = get_qq_executable_path(p["pid"])
            exe_str = f" ({exe_path}, v{ver})" if exe_path else ""
            print(f"    - PID: {p['pid']}, Mem: {p['mem_kb'] // 1024} MB{exe_str}")
    else:
        print("[!] No running QQ.exe process detected.")
        print("    Note: QQ must be running and logged in to extract in-memory keys.")

    # 2. Data directories detection
    roots = find_tencent_files_roots()
    if not roots:
        print("[!] No 'Tencent Files' data root directory discovered.")
        return 1

    print(f"\n[*] Discovered Tencent Files root(s):")
    all_accounts = []
    for r in roots:
        print(f"    - {r}")
        accs = scan_accounts(r)
        all_accounts.extend(accs)

    if not all_accounts:
        print("[!] No account databases (nt_msg.db) found in discovered roots.")
        return 1

    print(f"\n[*] Discovered Account Databases ({len(all_accounts)} account(s)):")
    for idx, acc in enumerate(all_accounts):
        flag = " (Latest Active)" if idx == 0 else ""
        print(f"  [{idx + 1}] UIN / QQ ID: {acc['uin']}{flag}")
        print(f"      Database : {acc['msg_db_path']}")
        print(f"      Size     : {acc['msg_db_size_mb']} MB")
        print(f"      Last Write: {acc['last_modified']}")

    active = all_accounts[0]
    print("\n" + "-" * 60)
    print("Summary for Decryption:")
    print(f"  Target Root : {os.path.dirname(os.path.dirname(active['nt_db_dir']))}")
    print(f"  Active UIN  : {active['uin']}")
    print("-" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
