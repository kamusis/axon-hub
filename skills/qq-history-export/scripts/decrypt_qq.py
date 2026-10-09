#!/usr/bin/env python3
"""decrypt_qq.py -- Automate QQ NT database memory key scanning and decryption.

Uses x_key_scanner to extract SQLCipher 4 keys non-invasively from QQ.exe
memory and decrypts nt_msg.db and related databases into plain SQLite.
"""
import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
import urllib.request


def find_scanner_bin():
    """Locate x_key_scanner executable in bin/ directory or PATH."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_root = os.path.dirname(script_dir)
    bundled = os.path.join(skill_root, "bin", "x_key_scanner.exe")
    if os.path.isfile(bundled):
        return bundled

    which_bin = shutil.which("x_key_scanner") or shutil.which("x_key_scanner.exe")
    if which_bin:
        return which_bin

    return bundled


def download_scanner_bin(target_path):
    """Download x_key_scanner Windows binary from GitHub Releases if missing."""
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    url = (
        "https://github.com/QQBackup/x_key_scanner/releases/download/"
        "v0.2.0/x_key_scanner-x86_64-pc-windows-msvc.exe"
    )
    print(f"[*] Downloading x_key_scanner binary from {url}...")
    try:
        urllib.request.urlretrieve(url, target_path)
        print(f"[OK] Downloaded successfully to {target_path}")
        return True
    except Exception as e:
        print(f"[!] Failed to download: {e}")
        return False


def verify_decrypted_db(db_path):
    """Verify that the decrypted database is a valid, readable SQLite database."""
    if not os.path.isfile(db_path):
        return False, "File does not exist"
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        counts = {}
        for t in ["c2c_msg_table", "group_msg_table", "profile_table", "group_table"]:
            if t in tables:
                try:
                    c = con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                    counts[t] = c
                except Exception:
                    pass
        con.close()
        return True, counts
    except Exception as e:
        return False, str(e)


def main():
    ap = argparse.ArgumentParser(description="Decrypt QQ NT databases via x_key_scanner")
    ap.add_argument("--data-root", default="", help="Tencent Files root path (e.g. D:\\Documents\\Tencent Files)")
    ap.add_argument("--output", default="decrypted", help="Output directory for decrypted plain SQLite databases")
    ap.add_argument("--strong", action="store_true", help="Enable strong memory scanning mode")
    args = ap.parse_args()

    scanner_bin = find_scanner_bin()
    if not os.path.isfile(scanner_bin):
        success = download_scanner_bin(scanner_bin)
        if not success:
            print("[!] Unable to locate or download x_key_scanner. Please ensure internet access.")
            return 1

    cmd = [scanner_bin, "--output", os.path.abspath(args.output), "--force"]
    if args.data_root:
        cmd.extend(["--data-root", args.data_root])
    if args.strong:
        cmd.append("--strong")

    print("=" * 60)
    print("QQ NT Database Decryption Tool")
    print("=" * 60)
    print(f"[*] Scanner binary: {scanner_bin}")
    print(f"[*] Output directory: {os.path.abspath(args.output)}")
    print(f"[*] Command: {' '.join(cmd)}")
    print("[*] Scanning memory and decrypting... (QQ must be running and logged in)\n")

    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"\n[!] Decryption process exited with code {res.returncode}")
        return res.returncode

    # Check output directory
    out_dir = os.path.abspath(args.output)
    print("\n" + "=" * 60)
    print("Verifying Decrypted Databases:")
    print("=" * 60)

    found_any = False
    for root, dirs, files in os.walk(out_dir):
        if "nt_msg.db" in files:
            msg_db = os.path.join(root, "nt_msg.db")
            ok, info = verify_decrypted_db(msg_db)
            if ok:
                found_any = True
                print(f"[OK] Plain SQLite verified: {msg_db}")
                for tbl, cnt in info.items():
                    print(f"     - Table '{tbl}': {cnt} rows")
            else:
                print(f"[!] Verification failed for {msg_db}: {info}")

    if not found_any:
        print("[!] No decrypted nt_msg.db found in output directory.")
        return 1

    print("\n[OK] Decryption complete and verified. You can now run query_qq_messages.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
