#!/usr/bin/env python3
"""Start a reproducible Mopheus integration preview environment across platforms."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

PREVIEW_EMAIL_DEFAULT = "preview-admin@test.local"
PREVIEW_PASSWORD_DEFAULT = "MopheusPreview123!"
PREVIEW_WORKSPACE_SLUG_DEFAULT = "dev-space"
PREVIEW_WORKSPACE_NAME_DEFAULT = "Dev Space"
POSTGRES_CONTAINER_NAME = "mopheus-postgres-1"
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def fail(msg: str) -> None:
    sys.stderr.write(f"ERROR: {msg}\n")
    sys.exit(1)


def is_port_listening(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


def get_port_pid(port: int) -> str:
    if not is_port_listening(port):
        return "none"
    if sys.platform == "win32":
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", f"(Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue).OwningProcess"],
                capture_output=True, text=True, check=False,
            )
            pids = res.stdout.strip().split()
            if pids and pids[0].isdigit():
                return pids[0]
        except Exception:
            pass
        return "active"
    else:
        try:
            res = subprocess.run(["lsof", "-nP", f"-tiTCP:{port}", "-sTCP:LISTEN"], capture_output=True, text=True, check=False)
            pids = res.stdout.strip().split()
            if pids:
                return pids[0]
        except Exception:
            pass
        return "active"


def read_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.is_file():
        return values
    try:
        content = env_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip().strip("'\"")
    except Exception:
        pass
    return values


def write_env_file(env_path: Path, updates: dict[str, str]) -> None:
    lines: list[str] = []
    keys_updated = set()
    if env_path.is_file():
        content = env_path.read_text(encoding="utf-8")
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                k = stripped.split("=", 1)[0].strip()
                if k in updates:
                    lines.append(f"{k}={updates[k]}")
                    keys_updated.add(k)
                    continue
            lines.append(line)
    for k, v in updates.items():
        if k not in keys_updated:
            lines.append(f"{k}={v}")
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_preview_cli_boundary(profile: str, server_url: str) -> None:
    """Reject formal profiles and non-loopback servers in preview environments."""
    if not profile.startswith("wt-"):
        fail(f"preview MOPHEUS_PROFILE must start with 'wt-'; refusing profile: {profile or '<missing>'}")

    parsed = urllib.parse.urlparse(server_url)
    try:
        port = parsed.port
    except ValueError:
        port = None
    if parsed.scheme != "http" or parsed.hostname not in LOOPBACK_HOSTS or port is None:
        fail(f"preview MOPHEUS_SERVER_URL must be an HTTP loopback URL; refusing: {server_url or '<missing>'}")


def api_request(method: str, url: str, token: str = "", workspace_slug: str = "", payload: dict | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if workspace_slug:
        headers["X-Workspace-Slug"] = workspace_slug

    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return json.loads(body)
        except Exception:
            fail(f"HTTP {e.code} for {method} {url}: {body}")
    except Exception as e:
        fail(f"Request failed for {method} {url}: {e}")
    return {}


def is_http_ready(url: str) -> bool:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return 200 <= resp.status < 400
    except Exception:
        return False


def wait_for_http(url: str, timeout_seconds: int) -> bool:
    start = time.time()
    while time.time() - start < timeout_seconds:
        if is_http_ready(url):
            return True
        time.sleep(1)
    return False


def wait_for_runtimes(api_base: str, token: str, workspace_slug: str, timeout_seconds: int) -> bool:
    """Wait until the preview workspace has at least one registered runtime."""
    start = time.time()
    while time.time() - start < timeout_seconds:
        try:
            response = api_request("GET", f"{api_base}/runtimes", token=token, workspace_slug=workspace_slug)
            runtimes = response.get("data", [])
            if response.get("success") is True and isinstance(runtimes, list) and runtimes:
                return True
        except SystemExit:
            # The daemon may still be completing registration while the API is ready.
            pass
        time.sleep(1)
    return False


def discover_previews(script_dir: Path, target_worktree: Path) -> list[dict]:
    py_script = script_dir / "discover_previews.py"
    res = subprocess.run([sys.executable, str(py_script), str(target_worktree)], capture_output=True, text=True, check=False)
    results = []
    for line in res.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 6:
            results.append({
                "worktree": parts[0],
                "frontend_port": parts[1],
                "frontend_pid": parts[2],
                "backend_port": parts[3],
                "backend_pid": parts[4],
                "database": parts[5],
            })
    return results


def check_git_worktree(worktree_path: Path) -> tuple[Path, Path]:
    try:
        res = subprocess.run(["git", "-C", str(worktree_path), "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True, check=True)
    except Exception:
        fail(f"not a Git worktree: {worktree_path}")

    try:
        git_dir_str = subprocess.run(["git", "-C", str(worktree_path), "rev-parse", "--absolute-git-dir"], capture_output=True, text=True, check=True).stdout.strip()
        common_dir_str = subprocess.run(["git", "-C", str(worktree_path), "rev-parse", "--path-format=absolute", "--git-common-dir"], capture_output=True, text=True, check=True).stdout.strip()
        git_dir = Path(git_dir_str).resolve()
        common_dir = Path(common_dir_str).resolve()
        if git_dir == common_dir:
            fail("primary checkout is not accepted; provide an existing linked Mopheus worktree")
        return git_dir, common_dir
    except Exception as e:
        fail(f"failed resolving git paths: {e}")
    return Path(), Path()


def ensure_env_worktree(worktree_path: Path) -> Path:
    env_file = worktree_path / ".env.worktree"
    if env_file.is_file():
        return env_file

    # Generate default .env.worktree
    branch = "preview"
    try:
        branch_res = subprocess.run(["git", "-C", str(worktree_path), "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True)
        branch = branch_res.stdout.strip().replace("/", "-")
    except Exception:
        pass

    slug = f"mopheus_wt_{branch}"
    db_name = slug.replace("-", "_").lower()
    profile = f"wt-{branch}"

    # Calculate deterministic ports from path hash
    h = int(hashlib.md5(str(worktree_path).encode("utf-8")).hexdigest()[:4], 16)
    offset = h % 500
    be_port = 8100 + offset
    fe_port = 3100 + offset

    env_content = f"""# Worktree environment generated for preview
POSTGRES_USER=mopheus
POSTGRES_PASSWORD=mopheus
POSTGRES_DB={db_name}
POSTGRES_PORT=5432
DATABASE_URL=postgres://mopheus:mopheus@localhost:5432/{db_name}?sslmode=disable
BACKEND_PORT={be_port}
FRONTEND_PORT={fe_port}
FRONTEND_ORIGIN=http://localhost:{fe_port}
NEXT_PUBLIC_API_URL=http://localhost:{be_port}
REMOTE_API_URL=http://localhost:{be_port}
ADMIN_EMAIL=admin@test.local
ADMIN_PASSWORD=AdminPassword123!
JWT_SECRET=preview-secret-key-12345678901234567890
MOPHEUS_PROFILE={profile}
MOPHEUS_SERVER_URL=http://localhost:{be_port}
"""
    env_file.write_text(env_content, encoding="utf-8")
    return env_file


def is_daemon_running(worktree_path: Path, profile: str) -> bool:
    try:
        res = subprocess.run(
            ["go", "run", "./cmd/mopheus", "--profile", profile, "daemon", "status"],
            cwd=str(worktree_path / "server"),
            capture_output=True,
            text=True,
            check=False,
        )
        return "running" in res.stdout.lower()
    except Exception:
        return False


def sync_code_from_source(source_path: Path, target_path: Path) -> dict[str, bool]:
    """Sync code changes from source worktree to target preview worktree and detect what changed."""
    check_git_worktree(source_path)
    check_git_worktree(target_path)

    # Record target HEAD before sync to compute diff
    target_old_head = ""
    try:
        target_old_head = subprocess.run(
            ["git", "-C", str(target_path), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        pass

    # Get source HEAD
    src_head = subprocess.run(
        ["git", "-C", str(source_path), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True
    ).stdout.strip()

    print(f"==> Syncing code from {source_path} (commit {src_head[:8]}) to {target_path}...")

    # Fast reset target to source commit (preserves untracked/ignored files like .env.worktree)
    subprocess.run(["git", "-C", str(target_path), "reset", "--hard", src_head], capture_output=True, check=True)

    # Check for uncommitted working-tree modifications in source
    status_res = subprocess.run(
        ["git", "-C", str(source_path), "status", "--porcelain"],
        capture_output=True, text=True, check=True
    )
    if status_res.stdout.strip():
        print("==> Applying uncommitted working-tree changes from source...")
        diff_res = subprocess.run(
            ["git", "-C", str(source_path), "diff", "HEAD"],
            capture_output=True, check=True
        )
        if diff_res.stdout:
            subprocess.run(
                ["git", "-C", str(target_path), "apply", "--whitespace=nowarn"],
                input=diff_res.stdout,
                capture_output=True,
                check=False
            )

    # Detect modified paths
    changed_files: list[str] = []
    if target_old_head:
        diff_res = subprocess.run(
            ["git", "-C", str(target_path), "diff", "--name-only", target_old_head],
            capture_output=True, text=True, check=False
        )
        changed_files = diff_res.stdout.splitlines()

    go_changed = any(f.startswith("server/") and f.endswith(".go") for f in changed_files)
    pkg_changed = any("package.json" in f or "pnpm-lock.yaml" in f for f in changed_files)
    migrations_changed = any("migrations/" in f for f in changed_files)

    return {
        "go_changed": go_changed,
        "pkg_changed": pkg_changed,
        "migrations_changed": migrations_changed,
    }


IGNORED_WATCH_DIRS = {
    ".git", "node_modules", ".next", ".turbo", "dist", "bin",
    "__pycache__", ".vscode", ".idea", "coverage", ".worktrees"
}
IGNORED_WATCH_EXTS = {
    ".log", ".tmp", ".pid", ".swp", ".swo", ".pyc"
}


def get_source_mtimes(root_dir: Path) -> dict[str, float]:
    """Collect source file relative paths and their mtimes, skipping ignored directories."""
    mtimes: dict[str, float] = {}
    for top in ("apps", "server", "packages"):
        top_path = root_dir / top
        if not top_path.exists():
            continue
        for parent, dirs, files in os.walk(top_path):
            dirs[:] = [d for d in dirs if d not in IGNORED_WATCH_DIRS and not d.startswith(".")]
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in IGNORED_WATCH_EXTS or f.startswith("."):
                    continue
                full_path = Path(parent) / f
                try:
                    rel = str(full_path.relative_to(root_dir))
                    mtimes[rel] = full_path.stat().st_mtime
                except OSError:
                    pass
    return mtimes


def sync_single_file(source_path: Path, target_path: Path, rel_file: str) -> None:
    """Copy or remove a single file from source worktree to target worktree."""
    src_file = source_path / rel_file
    dst_file = target_path / rel_file
    if src_file.exists():
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst_file)
    elif dst_file.exists():
        dst_file.unlink(missing_ok=True)


def watch_and_sync(
    source_path: Path,
    target_path: Path,
    auth_ready_url: str,
    backend_pid: Path,
    backend_log: Path,
    script_dir: Path,
    run_env: dict[str, str],
) -> None:
    """Continuously watch for file changes in source worktree and sync in real time."""
    print(f"\n==> Watching for file changes in {source_path}...")
    print("    (Press Ctrl+C to stop watcher; preview services will remain running)")

    last_mtimes = get_source_mtimes(source_path)
    start_detached = script_dir / "start_detached.py"

    try:
        while True:
            time.sleep(0.5)
            current_mtimes = get_source_mtimes(source_path)

            # Detect added, modified, deleted files
            changed: list[str] = []
            for rel_file, mtime in current_mtimes.items():
                if rel_file not in last_mtimes or mtime > last_mtimes[rel_file]:
                    changed.append(rel_file)
            for rel_file in last_mtimes:
                if rel_file not in current_mtimes:
                    changed.append(rel_file)

            if not changed:
                continue

            # Small debounce sleep for batch editor saves
            time.sleep(0.15)
            current_mtimes = get_source_mtimes(source_path)
            last_mtimes = current_mtimes

            now_str = time.strftime("%H:%M:%S")
            go_changed = False
            migrations_changed = False

            for rel_file in changed:
                sync_single_file(source_path, target_path, rel_file)
                if rel_file.startswith("server/") and rel_file.endswith(".go"):
                    go_changed = True
                if "migrations/" in rel_file:
                    migrations_changed = True

            print(f"[{now_str}] Synced {len(changed)} file(s): {', '.join(changed[:3])}{'...' if len(changed) > 3 else ''}")

            if migrations_changed:
                print(f"[{now_str}] Migrations changed, running db migrate...")
                subprocess.run(["go", "run", "./cmd/migrate", "up"], cwd=str(target_path / "server"), env=run_env, check=False)

            if go_changed:
                print(f"[{now_str}] Go backend modified, reloading backend...")
                if backend_pid.is_file():
                    try:
                        old_pid = int(backend_pid.read_text().strip())
                        if sys.platform == "win32":
                            subprocess.run(["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {old_pid} -Force -ErrorAction SilentlyContinue"], capture_output=True, check=False)
                        else:
                            subprocess.run(["kill", "-9", str(old_pid)], capture_output=True, check=False)
                    except Exception:
                        pass
                    time.sleep(0.3)

                subprocess.run([
                    sys.executable, str(start_detached),
                    "--cwd", str(target_path / "server"),
                    "--log", str(backend_log),
                    "--pid-file", str(backend_pid),
                    "go", "run", "./cmd/mopheusd"
                ], check=True, env=run_env)

                if wait_for_http(auth_ready_url, 30):
                    print(f"[{now_str}] Backend reloaded and ready.")
                else:
                    print(f"[{now_str}] Warning: backend reload check timed out.")

    except KeyboardInterrupt:
        print("\n==> Watcher stopped. Preview services are still running.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Start a Mopheus integration preview")
    parser.add_argument("--allow-existing-previews", action="store_true", help="Allow starting while other previews are active")
    parser.add_argument("--reuse-db-from", help="Absolute linked worktree path to reuse database from")
    parser.add_argument("--sync-from", help="Absolute linked worktree path to sync code changes from")
    parser.add_argument("--watch", action="store_true", help="Continuously watch source worktree and sync modifications in real time")
    parser.add_argument("target_worktree", help="Absolute path to the target linked Git worktree")
    args = parser.parse_args()

    target_path = Path(args.target_worktree).resolve()
    if not target_path.exists():
        fail(f"worktree path does not exist: {target_path}")

    script_dir = Path(__file__).resolve().parent

    check_git_worktree(target_path)

    go_mod = target_path / "server" / "go.mod"
    if not go_mod.is_file() or "module mopheus" not in go_mod.read_text(encoding="utf-8"):
        fail("server/go.mod is missing or not the Mopheus module")

    # Discover other running previews
    existing = discover_previews(script_dir, target_path)
    if existing and not args.allow_existing_previews and not args.reuse_db_from:
        sys.stderr.write("Existing Mopheus previews are running:\n")
        sys.stderr.write("WORKTREE\tFRONTEND_PORT\tFRONTEND_PID\tBACKEND_PORT\tBACKEND_PID\tDATABASE\n")
        for item in existing:
            sys.stderr.write(f"{item['worktree']}\t{item['frontend_port']}\t{item['frontend_pid']}\t{item['backend_port']}\t{item['backend_pid']}\t{item['database']}\n")
        fail("existing preview confirmation required; ask whether to stop one and reuse its database, or rerun with --allow-existing-previews after explicit approval")

    env_file = ensure_env_worktree(target_path)

    if args.reuse_db_from:
        source_path = Path(args.reuse_db_from).resolve()
        if source_path == target_path:
            fail("reuse source and target worktrees must differ")
        check_git_worktree(source_path)
        source_env_file = source_path / ".env.worktree"
        if not source_env_file.is_file():
            fail(f"reuse source is missing .env.worktree: {source_path}")
        source_env = read_env_file(source_env_file)
        if not source_env.get("POSTGRES_DB") or not source_env.get("DATABASE_URL"):
            fail("reuse source database settings are incomplete")

        # Check source is not running
        src_fe_port = int(source_env.get("FRONTEND_PORT", "0"))
        src_be_port = int(source_env.get("BACKEND_PORT", "0"))
        if is_port_listening(src_fe_port) or is_port_listening(src_be_port):
            fail(f"reuse source services are still running on port {src_fe_port}/{src_be_port}; stop them first")

        write_env_file(env_file, {
            "POSTGRES_DB": source_env["POSTGRES_DB"],
            "DATABASE_URL": source_env["DATABASE_URL"],
        })
    sync_stats: dict[str, bool] = {}
    if args.sync_from:
        source_path = Path(args.sync_from).resolve()
        if source_path == target_path:
            fail("sync source and target worktrees must differ")
        sync_stats = sync_code_from_source(source_path, target_path)
        if sync_stats.get("pkg_changed"):
            print("==> Package manifests changed, updating node dependencies...")
            pnpm_bin = shutil.which("pnpm") or "pnpm"
            subprocess.run([pnpm_bin, "install"], cwd=str(target_path), check=False)

    env_vars = read_env_file(env_file)
    db_name = env_vars.get("POSTGRES_DB")
    be_port = int(env_vars.get("BACKEND_PORT", "8080"))
    fe_port = int(env_vars.get("FRONTEND_PORT", "3000"))
    admin_email = env_vars.get("ADMIN_EMAIL", "admin@test.local")
    admin_password = env_vars.get("ADMIN_PASSWORD", "AdminPassword123!")
    profile = env_vars.get("MOPHEUS_PROFILE", "").strip()
    server_url = env_vars.get("MOPHEUS_SERVER_URL", "").strip()
    validate_preview_cli_boundary(profile, server_url)
    db_port = env_vars.get("POSTGRES_PORT", "5432")

    # Start PostgreSQL container if stopped
    ps_res = subprocess.run(["docker", "ps", "-aq", "--filter", f"name=^/{POSTGRES_CONTAINER_NAME}$"], capture_output=True, text=True, check=False)
    if not ps_res.stdout.strip():
        fail(f"shared PostgreSQL container '{POSTGRES_CONTAINER_NAME}' does not exist")
    subprocess.run(["docker", "start", POSTGRES_CONTAINER_NAME], capture_output=True, check=False)

    print("==> Preparing worktree dependencies, database, and migrations...")
    # Ensure database exists
    create_db_cmd = f"SELECT 1 FROM pg_database WHERE datname = '{db_name}';"
    check_db = subprocess.run(
        ["docker", "exec", "-i", POSTGRES_CONTAINER_NAME, "psql", "-U", "mopheus", "-tc", create_db_cmd],
        capture_output=True, text=True, check=False
    )
    if "1" not in check_db.stdout:
        subprocess.run(
            ["docker", "exec", "-i", POSTGRES_CONTAINER_NAME, "psql", "-U", "mopheus", "-c", f"CREATE DATABASE \"{db_name}\";"],
            capture_output=True, check=False
        )

    # Run migrations
    run_env = os.environ.copy()
    run_env.update(env_vars)
    migrate_res = subprocess.run(
        ["go", "run", "./cmd/migrate", "up"],
        cwd=str(target_path / "server"),
        env=run_env,
        capture_output=True,
        text=True,
        check=False,
    )
    if migrate_res.returncode != 0:
        fail(f"database migration failed:\n{migrate_res.stderr}\n{migrate_res.stdout}")

    backend_url = f"http://localhost:{be_port}"
    frontend_url = f"http://localhost:{fe_port}"
    api_base = f"{backend_url}/api/v1"
    auth_ready_url = f"{api_base}/config/auth"
    login_url = f"{frontend_url}/login"

    run_env["NEXT_PUBLIC_API_URL"] = backend_url
    run_env["REMOTE_API_URL"] = backend_url
    run_env["BACKEND_URL"] = backend_url
    run_env["FRONTEND_PORT"] = str(fe_port)

    runtime_hash = hashlib.md5(str(target_path).encode("utf-8")).hexdigest()[:8]
    runtime_dir = Path(tempfile.gettempdir()) / f"mopheus-preview-{runtime_hash}"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    backend_log = runtime_dir / "backend.log"
    frontend_log = runtime_dir / "frontend.log"
    backend_pid = runtime_dir / "backend.pid"
    frontend_pid = runtime_dir / "frontend.pid"
    daemon_log = runtime_dir / "daemon.log"
    daemon_pid = runtime_dir / "daemon.pid"

    services_state = "reused"
    log_display = "existing processes"

    backend_ready = is_http_ready(auth_ready_url)
    frontend_ready = is_http_ready(login_url)

    # If backend is already running and Go code changed during sync, reload backend
    if backend_ready and args.sync_from and sync_stats.get("go_changed"):
        print("==> Go backend code modified during sync, restarting backend process...")
        if backend_pid.is_file():
            try:
                old_pid = int(backend_pid.read_text().strip())
                if sys.platform == "win32":
                    subprocess.run(["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {old_pid} -Force -ErrorAction SilentlyContinue"], capture_output=True, check=False)
                else:
                    subprocess.run(["kill", "-9", str(old_pid)], capture_output=True, check=False)
            except Exception:
                pass
            time.sleep(0.5)
        backend_ready = False

    if not backend_ready or not frontend_ready:
        start_detached = script_dir / "start_detached.py"

        if not backend_ready:
            print("==> Starting backend...")
            subprocess.run([
                sys.executable, str(start_detached),
                "--cwd", str(target_path / "server"),
                "--log", str(backend_log),
                "--pid-file", str(backend_pid),
                "go", "run", "./cmd/mopheusd"
            ], check=True, env=run_env)

        if not frontend_ready:
            # Clear next cache only on frontend cold start
            next_cache = target_path / "apps" / "web" / ".next"
            if next_cache.exists():
                shutil.rmtree(next_cache, ignore_errors=True)

            print("==> Starting frontend...")
            pnpm_cmd = ["pnpm", "--filter=@mopheus/web", "exec", "next", "dev", "--turbo", "-p", str(fe_port)]
            if sys.platform == "win32":
                pnpm_cmd[0] = shutil.which("pnpm") or "pnpm"
            subprocess.run([
                sys.executable, str(start_detached),
                "--cwd", str(target_path),
                "--log", str(frontend_log),
                "--pid-file", str(frontend_pid),
                *pnpm_cmd,
            ], check=True, env=run_env)

        services_state = "started" if (not backend_ready and not frontend_ready) else "reloaded"
        log_display = f"backend: {backend_log}; frontend: {frontend_log}"

        timeout = int(os.environ.get("MOPHEUS_PREVIEW_START_TIMEOUT", "180"))
        if not wait_for_http(auth_ready_url, timeout):
            fail(f"backend did not become ready within {timeout}s")
        if not wait_for_http(login_url, timeout):
            fail(f"frontend did not become ready within {timeout}s")

    print("==> Enabling every registered system feature...")
    admin_login_resp = api_request("POST", f"{api_base}/auth/login", payload={"email": admin_email, "password": admin_password})
    if not admin_login_resp.get("success"):
        fail("bootstrap Admin login failed")
    admin_token = admin_login_resp["data"]["accessToken"]

    features_resp = api_request("GET", f"{api_base}/admin/features", token=admin_token)
    feature_list = features_resp.get("data", [])
    if not feature_list:
        fail("admin feature list is empty")

    for f in feature_list:
        key = f["key"]
        encoded_key = urllib.parse.quote(key, safe="")
        api_request("PUT", f"{api_base}/admin/features/{encoded_key}", token=admin_token, payload={"systemState": 2})

    preview_email = os.environ.get("MOPHEUS_PREVIEW_EMAIL", PREVIEW_EMAIL_DEFAULT)
    preview_password = os.environ.get("MOPHEUS_PREVIEW_PASSWORD", PREVIEW_PASSWORD_DEFAULT)
    workspace_slug = os.environ.get("MOPHEUS_PREVIEW_WORKSPACE_SLUG", PREVIEW_WORKSPACE_SLUG_DEFAULT)
    workspace_name = os.environ.get("MOPHEUS_PREVIEW_WORKSPACE_NAME", PREVIEW_WORKSPACE_NAME_DEFAULT)

    print("==> Creating or reusing the regular preview user and workspace...")
    preview_auth = api_request("POST", f"{api_base}/auth/login", payload={"email": preview_email, "password": preview_password})
    if not preview_auth.get("success"):
        reg_resp = api_request("POST", f"{api_base}/auth/register", payload={"name": "Mopheus Preview", "email": preview_email, "password": preview_password})
        if not reg_resp.get("success"):
            fail("preview user login failed and registration did not succeed")
        preview_auth = reg_resp

    preview_token = preview_auth["data"]["accessToken"]
    workspaces_resp = api_request("GET", f"{api_base}/workspaces", token=preview_token)
    ws_list = workspaces_resp.get("data", [])
    workspace_id = None
    for ws in ws_list:
        if ws.get("slug") == workspace_slug:
            workspace_id = ws["id"]
            break

    if not workspace_id:
        ws_create = api_request("POST", f"{api_base}/workspaces", token=preview_token, payload={
            "name": workspace_name,
            "slug": workspace_slug,
            "description": "Local integration preview workspace",
            "identifierPrefix": "DEV",
        })
        if not ws_create.get("success"):
            fail(f"failed to create preview workspace '{workspace_slug}'")
        workspace_id = ws_create["data"]["id"]

    api_request("POST", f"{api_base}/auth/onboarding/complete", token=preview_token, payload={
        "workspaceName": workspace_name,
        "displayName": "Mopheus Preview",
    })

    print(f"==> Enabling every feature for workspace {workspace_slug}...")
    for f in feature_list:
        key = f["key"]
        encoded_key = urllib.parse.quote(key, safe="")
        api_request("PUT", f"{api_base}/workspaces/{workspace_id}/features/{encoded_key}", token=preview_token, payload={"enabled": True})

    eff_resp = api_request("GET", f"{api_base}/features/effective", token=preview_token, workspace_slug=workspace_slug)
    eff_data = eff_resp.get("data", {})
    disabled = [k for k, v in eff_data.items() if v is not True]
    if disabled:
        fail(f"effective feature verification failed: {disabled}")
    enabled_features = ", ".join(sorted(eff_data.keys()))

    daemon_state = "reused"
    daemon_log_display = "existing process"

    if not is_daemon_running(target_path, profile):
        print("==> Starting daemon and registering runtimes...")
        start_detached = script_dir / "start_detached.py"
        if sys.platform != "win32" and shutil.which("make"):
            daemon_cwd = target_path
            daemon_command = [
                "make", "daemon-worktree",
                f"DEFAULT_EMAIL={preview_email}",
                f"DEFAULT_PASSWORD={preview_password}",
            ]
        else:
            login_res = subprocess.run(
                ["go", "run", "./cmd/mopheus", "--profile", profile, "login",
                 "--email", preview_email, "--password", preview_password],
                cwd=str(target_path / "server"),
                env=run_env,
                input="y\n",
                capture_output=True,
                text=True,
                check=False,
            )
            if login_res.returncode != 0:
                fail(f"daemon profile login failed:\n{login_res.stderr}\n{login_res.stdout}")
            daemon_cwd = target_path / "server"
            daemon_command = [
                "go", "run", "./cmd/mopheus", "--profile", profile,
                "daemon", "start", "--foreground",
            ]
        subprocess.run([
            sys.executable, str(start_detached),
            "--cwd", str(daemon_cwd),
            "--log", str(daemon_log),
            "--pid-file", str(daemon_pid),
            *daemon_command,
        ], check=True, env=run_env)
        daemon_state = "started"
        daemon_log_display = str(daemon_log)

    daemon_timeout = int(os.environ.get("MOPHEUS_PREVIEW_DAEMON_TIMEOUT", "120"))
    if not wait_for_runtimes(api_base, preview_token, workspace_slug, daemon_timeout):
        if daemon_log.is_file():
            tail = daemon_log.read_text(encoding="utf-8", errors="replace").splitlines()[-80:]
            sys.stderr.write("Daemon log tail:\n" + "\n".join(tail) + "\n")
        fail(f"daemon did not register any runtime for workspace '{workspace_slug}' within {daemon_timeout}s")

    print("\n" + "=" * 50)
    print("Mopheus integration preview is ready.")
    print(f"Application services: {services_state}")
    print(f"Daemon: {daemon_state} (profile: {profile})")
    print(f"Frontend login: {login_url}")
    print(f"Workspace: {frontend_url}/{workspace_slug}/dashboard")
    print(f"Backend: {backend_url}")
    print(f"PostgreSQL: {POSTGRES_CONTAINER_NAME} on localhost:{db_port}")
    print(f"Database: {db_name}")
    print(f"Enabled features: {enabled_features}")
    print(f"Test email: {preview_email}")
    print(f"Test password: {preview_password}")
    print(f"Service logs: {log_display}")
    print(f"Daemon log: {daemon_log_display}")
    print("=" * 50)

    if args.watch:
        if not args.sync_from:
            fail("--watch requires --sync-from <dev-worktree>")
        source_path = Path(args.sync_from).resolve()
        watch_and_sync(source_path, target_path, auth_ready_url, backend_pid, backend_log, script_dir, run_env)

    return 0


if __name__ == "__main__":
    sys.exit(main())
