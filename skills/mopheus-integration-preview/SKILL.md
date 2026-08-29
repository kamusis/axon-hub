---
name: mopheus-integration-preview
description: Discover, create, and start reusable local Mopheus integration-test previews from linked Git worktrees, including backend, frontend, and daemon runtimes across Windows, Linux, and macOS. Use this whenever the user asks to start, prepare, bootstrap, reopen, or inspect a Mopheus preview, integration-test environment, local worktree environment, runtime, daemon, or test login. Detect already-running previews before startup, require confirmation before parallel startup or service shutdown, preserve and optionally reuse preview databases, enable every registered feature dynamically, and print local test credentials after readiness checks.
compatibility: Requires Windows (PowerShell/CMD), macOS, or Linux with git, Docker, Node.js, pnpm, Python 3, and Go. The target must be an existing linked Mopheus Git worktree using a local .env.worktree database.
---

# Mopheus Integration Preview

Discover and start a disposable local preview from an existing Mopheus linked worktree. Preserve databases and test data between runs so future integration checks can reuse the same state without silently creating competing application processes.

## 0. Check Host Operating System and Execution Mode First

At the very beginning of execution, determine the host environment and required execution mode:

- **Windows Host (Default: Full-Stack in WSL)**:
  - Because Mopheus Agent Daemon and ACP tool runtimes require POSIX PTY/process namespaces (not supported natively on Windows), **the default preview execution mode on Windows is WSL Full-Stack Mode** (Backend + Frontend + Daemon all running inside WSL native Linux).
  - **Code Synchronization**: Always push code from Windows into WSL using Windows native `robocopy` over UNC path `\\wsl.localhost\Ubuntu-24.04\home\<user>\CascadeProjects\mopheus\.worktrees\preview-test` (using the default WSL distro, e.g. `Ubuntu-24.04`). **NEVER use `--sync-from /mnt/c/...` from inside WSL** (which causes severe 9P file system degradation and git ownership errors).
  - **Port Protection**: Before starting in WSL, check and terminate any lingering Windows host processes holding ports 3230 or 8230.
- **Windows (Native Lightweight Web-Only, Opt-in)**:
  - Only when the user explicitly requests Windows-native execution (no Agent daemon / offline runtimes): run `python <skill-directory>/scripts/start_preview.py <dev-worktree>`.
- **Linux / macOS**:
  - Run natively with `python3 <skill-directory>/scripts/start_preview.py <preview-test-worktree>`.

## Worktree and Harness Resolution (Default: Dedicated Preview Harness)

By default, Mopheus integration preview runs in **Dedicated Preview Harness Mode** to reuse the existing preview database (`mopheus_wt_preview_test`), test credentials, and fixed ports (`3230`/`8230`):

1. **Identify Current Development Worktree (`<dev-worktree>`)**:
   - If the conversation/agent is in a feature worktree (e.g., `C:\Users\<user>\CascadeProjects\mopheus\.worktrees\<name>`), treat it as `<dev-worktree>`.
2. **Locate Dedicated Preview Harness (`<preview-test>`)**:
   - On Windows $\to$ WSL: Target `\\wsl.localhost\Ubuntu-24.04\home\<user>\CascadeProjects\mopheus\.worktrees\preview-test` (native Linux path: `/home/<user>/CascadeProjects/mopheus/.worktrees/preview-test`).
3. **Execution Steps on Windows**:
   - **Step 1: Clean Windows listeners**: Stop any Windows host process on ports 3230 / 8230:
     ```powershell
     Get-NetTCPConnection -LocalPort 3230, 8230 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
     ```
   - **Step 2: Clean WSL stale processes**:
     ```bash
     wsl bash -c "killall -9 mopheusd node mopheus next-server 2>/dev/null || true"
     ```
   - **Step 3: Push code from Windows into WSL (preserving uploads & build caches)**:
     ```powershell
     robocopy <win-dev-worktree> \\wsl.localhost\Ubuntu-24.04\home\<user>\CascadeProjects\mopheus\.worktrees\preview-test /MIR /NFL /NDL /NJH /NJS /nc /ns /np /XD .git node_modules .next .turbo .worktrees uploads dist bin __pycache__ /XF .env.worktree .env.local *.log *.pid *.tmp
     ```
   - **Step 4: Launch Preview inside WSL with login shell**:
     ```bash
     wsl bash -i -c "python3 ~/.gemini/config/skills/mopheus-integration-preview/scripts/start_preview.py /home/<user>/CascadeProjects/mopheus/.worktrees/preview-test"
     ```

## Opt-in: Worktree-Specific Isolated Database (`--isolated-db`)

Only when the user explicitly requests an isolated, independent preview database for the current worktree (e.g., saying "新建隔离数据库", "独立环境", or passing `--isolated-db`):

- **Windows**:
  ```powershell
  python <skill-directory>/scripts/start_preview.py --isolated-db <absolute-worktree-path>
  ```
- **Linux / macOS / WSL**:
  ```bash
  python3 <skill-directory>/scripts/start_preview.py --isolated-db <absolute-worktree-path>
  ```

In isolated mode, a new worktree-specific database (`mopheus_wt_<branch>`) and dynamic ports are allocated.

## Discover existing previews first

Before every startup attempt, execute the cross-platform discovery tool:

- **Windows**:
  ```powershell
  python <skill-directory>/scripts/discover_previews.py <absolute-target-worktree-path>
  ```
- **Linux / macOS**:
  ```bash
  python3 <skill-directory>/scripts/discover_previews.py <absolute-target-worktree-path>
  ```

The discovery script maps active frontend and backend listeners from other linked worktrees to their ports and database names. If it prints any row, report the complete mapping and pause for an explicit user decision. Ask whether to:

1. stop one existing preview's frontend and backend, then reuse its database for the target worktree; or
2. keep existing previews running and start an independent target preview.

Do not stop services, rewrite `.env.worktree`, switch databases, or start another preview before the user chooses. Merely asking to start a preview does not authorize shutting down an existing one.

## Run the preview

When running in default Dedicated Harness mode:

- **Windows**:
  ```powershell
  python <skill-directory>/scripts/start_preview.py <dev-worktree>
  ```
- **Linux / macOS**:
  ```bash
  python3 <skill-directory>/scripts/start_preview.py --sync-from <dev-worktree> <preview-test-worktree> --watch
  ```
- **Windows (WSL Mode)**:
  ```bash
  wsl bash -i -c "python3 ~/.gemini/config/skills/mopheus-integration-preview/scripts/start_preview.py --sync-from <wsl-dev-worktree> <wsl-preview-test-worktree> --watch"
  ```

After the user explicitly approves stopping an existing preview and reusing its database:

1. Stop the source preview services and daemon.
2. Stop the target preview too if it is already running.
3. Execute:
   - **Windows**:
     ```powershell
     python <skill-directory>/scripts/start_preview.py --reuse-db-from <absolute-source-worktree> <absolute-target-worktree>
     ```
   - **Linux / macOS**:
     ```bash
     python3 <skill-directory>/scripts/start_preview.py --reuse-db-from <absolute-source-worktree> <absolute-target-worktree>
     ```

Database reuse copies only `POSTGRES_DB` and `DATABASE_URL` into the target's ignored `.env.worktree`. The target retains its own frontend and backend ports. The source database and all test data remain intact. The command refuses reuse while either source or target application services are still listening.

### Code synchronization to a dedicated preview worktree (`--sync-from`, `--watch`)

To support a persistent preview harness (e.g., keeping a persistent `preview-test` worktree running while actively editing code in a separate development worktree):

- **One-shot sync**:
  - **Windows (Native)**:
    ```powershell
    python <skill-directory>/scripts/start_preview.py --sync-from <absolute-dev-worktree-path> <absolute-target-preview-worktree-path>
    ```
  - **Linux / macOS**:
    ```bash
    python3 <skill-directory>/scripts/start_preview.py --sync-from <absolute-dev-worktree-path> <absolute-target-preview-worktree-path>
    ```
  - **Windows (WSL Mode)**:
    ```bash
    wsl bash -i -c "python3 ~/.gemini/config/skills/mopheus-integration-preview/scripts/start_preview.py --sync-from <wsl-dev-worktree-path> <wsl-target-preview-worktree-path>"
    ```

- **Continuous watch & auto-sync mode (`--watch`)**:
  - **Windows (Native)**:
    ```powershell
    python <skill-directory>/scripts/start_preview.py --sync-from <absolute-dev-worktree-path> <absolute-target-preview-worktree-path> --watch
    ```
  - **Linux / macOS**:
    ```bash
    python3 <skill-directory>/scripts/start_preview.py --sync-from <absolute-dev-worktree-path> <absolute-target-preview-worktree-path> --watch
    ```
  - **Windows (WSL Mode)**:
    ```bash
    wsl bash -i -c "python3 ~/.gemini/config/skills/mopheus-integration-preview/scripts/start_preview.py --sync-from <wsl-dev-worktree-path> <wsl-target-preview-worktree-path> --watch"
    ```

`--sync-from` (and `--watch`) automatically:
1. Fast-syncs tracked commits and uncommitted working-tree modifications from the development worktree into the target preview worktree without modifying `.env.worktree`, database credentials, or active ports.
2. Runs `pnpm install` if package dependencies or locks changed.
3. Runs database migrations (`go run ./cmd/migrate up`) if schema migrations changed.
4. Leverages Next.js Turbopack for instant frontend hot reloading in the browser (~100ms) without restarting the frontend process.
5. Gracefully restarts the backend process if Go backend code was modified, preserving the same ports, database, and registered daemon runtimes.
6. When `--watch` is enabled, runs an active file watcher on the development worktree: saving files in the editor automatically syncs changes and hot-reloads the preview environment with zero manual terminal commands.

The startup script owns the remaining workflow after discovery and confirmation:

1. Validate that the path is a linked worktree of the Mopheus repository.
2. Refuse an unconfirmed parallel startup when another linked-worktree preview is active.
3. Generate or reuse `.env.worktree` with worktree-specific application ports and database name, or reuse an explicitly approved source database.
4. Reuse the shared Docker container named `mopheus-postgres-1`.
5. Install dependencies, create the selected database when missing, and run migrations.
6. Clear only the ignored worktree-local Next.js build cache before a cold start, then start backend and frontend as persistent local background processes.
7. Wait until the auth API and login page both respond successfully.
8. Dynamically list every registered feature and set its system state to `enabled`.
9. Create or reuse the dedicated regular test user and `dev-space` workspace.
10. Set every registered feature override to `true` for the test workspace and verify every effective value is enabled.
11. On non-Windows hosts, start or reuse the worktree-profile daemon as a persistent local background process. Prefer `make daemon-worktree` with the regular preview account; if `make` is unavailable, perform the equivalent profile login and run `go run ./cmd/mopheus ... daemon start --foreground --allow-root`. Windows uses the platform-specific daemon startup path.
12. Wait until at least one runtime is registered in `dev-space`; a running process without registered runtimes is not ready.
13. Print URLs, database details, enabled features, backend/frontend/daemon log paths, daemon profile and state, and test email/password.

Do not manually repeat these steps unless diagnosing a script failure. The bundled script is the source of truth for deterministic setup.

## Preview CLI profile boundary

Preview CLI state is disposable and must remain isolated from formal Mopheus delivery state:

- Require `.env.worktree` to define a worktree-specific `MOPHEUS_PROFILE` beginning with `wt-`. Treat a missing profile, `default`, `local`, or any other profile name as a setup error.
- Require `MOPHEUS_SERVER_URL` to use plain HTTP on a loopback host (`localhost`, `127.0.0.1`, or `::1`). Refuse remote hosts and HTTPS endpoints before login or daemon startup.
- Never run the host-installed formal `mopheus` CLI for preview login or daemon startup. The preview-only `go run ./cmd/mopheus` path is permitted here solely because it is bound to the validated worktree profile and loopback server.
- Never repoint a preview profile to `https://dev.mopheus.ai`, and never use the formal `default` profile or its credentials for preview operations.
- These preview exceptions do not apply to release, GitHub delivery, or formal ticket-management skills; those workflows must use the host-installed CLI and formal `default` profile.

### Executing mop CLI Commands in the Preview Harness (go run)

When operating or testing against the preview environment (e.g., managing test jobs, tickets, agents, tokens, or verifying new CLI features):

- **Always use `go run ./cmd/mopheus` with the worktree environment loaded**, rather than the globally installed `mop` binary.
- **Why this is the most appropriate approach**:
  1. **Immediate Source Validation**: Executes directly against the latest code in the worktree, allowing immediate testing of CLI modifications without rebuilding or reinstalling binaries.
  2. **Isolated Environment & Configuration**: Sourcing `.env.worktree` automatically binds `MOPHEUS_SERVER_URL`, `MOPHEUS_PROFILE`, and worktree database context to the preview instance, preventing accidental interaction with host production/dev environments.
  3. **Reproducibility**: Works consistently across Windows, WSL, Linux, and macOS without relying on global binary PATHs.

- **Standard Execution Pattern in WSL / Linux**:
  ```bash
  cd <preview-worktree-path>
  set -a && [ -f .env.worktree ] && . ./.env.worktree && set +a
  cd server && go run ./cmd/mopheus <subcommand> [flags]
  ```


## Credential exception

The dedicated preview credential is intentionally safe to print because it is restricted to disposable local integration environments. The script prints it at the end of every successful run.

Never use this credential against:

- a production deployment;
- `dev.kamusis.me` or another remote server;
- the server in the user's default Mopheus CLI profile.

Keep the test identity at system `role = 0`. The workspace-local Owner membership supplies preview permissions. Never assign the test email to `ADMIN_EMAIL`, because Mopheus would promote it to system Admin and workspace pages would become inaccessible.

## Feature policy

Preview environments enable all current and future feature flags dynamically. Do not hard-code `memory`, `git`, or any other key in the Skill.

The script must satisfy both tiers:

- system state is `2` (`enabled`);
- the target workspace override is `true`.

After updates, require `/features/effective` to return `true` for every discovered key. A partial result is a failed preview setup.

## PostgreSQL reuse and conflicts

The preview database must be local and worktree-specific, but all previews share the existing `mopheus-postgres-1` container and its persistent Docker volume.

- Start `mopheus-postgres-1` when it exists but is stopped.
- Do not remove or recreate the shared container or volume.
- Do not clean databases or test data after integration testing.
- If another process or container occupies the configured PostgreSQL port, stop and report its identity. Do not stop unrelated containers without explicit user authorization.
- If `mopheus-postgres-1` does not exist, stop and explain that the shared prerequisite is missing. Do not create a second PostgreSQL container implicitly.

## Idempotency

Repeated runs against the same worktree must reuse:

- `.env.worktree`;
- the worktree database;
- the regular test account;
- the `dev-space` workspace;
- existing user-created test data;
- already-running healthy backend and frontend processes.
- an already-running healthy daemon for the worktree's `MOPHEUS_PROFILE`.

Database reuse across worktrees is allowed only after explicit confirmation and after both affected application pairs are stopped. It must not delete the target's former database; changing `.env.worktree` only changes which preserved database the target uses.

Do not delete, truncate, reseed, or reset existing data.

## Success report

Return the script's final summary without redacting the local test email or password. Include:

- frontend login and workspace URLs;
- backend URL;
- PostgreSQL container, port, and database name;
- enabled feature keys;
- test email and password;
- backend and frontend log paths;
- daemon profile and log path;
- whether application services and the daemon were started or reused.

Do not claim readiness merely because processes were spawned. HTTP readiness checks, effective-feature verification, daemon status, and runtime registration must all pass.

## Failure handling

- Invalid or primary checkout path: ask for a linked Mopheus worktree.
- Dirty worktree: allowed; preview setup does not edit tracked source files.
- Missing command: report the exact dependency and stop.
- Port conflict: report the PID or container and wait for user authorization.
- Other linked-worktree preview detected: report its worktree, frontend/backend ports and PIDs, and database; pause for the user's decision.
- Database reuse requested while source or target services are running: report the listeners and stop without changing configuration.
- Database reuse requested while the source or target daemon is running: report its profile and stop without changing configuration.
- Shared PostgreSQL missing: report the missing `mopheus-postgres-1` prerequisite.
- Migration or startup failure: show the relevant log tail and keep all data.
- Test-account password mismatch: stop rather than resetting a persistent account silently.
- Feature enablement mismatch: list the keys that remain disabled and stop.

## Running Full-Stack Preview in WSL on Windows (WSL Mode)

When on Windows and the user requests running the preview in WSL (or when full Agent daemon execution, ACP providers like Claude/Codex/Kimi/Mimo, and Linux bash tool runtimes are needed):

### 1. File System Requirement: Native Linux Path Only
- **CRITICAL**: Never launch preview processes in WSL using `/mnt/c/...` or Windows NTFS paths. Cross-OS 9P file system access causes severe I/O degradation on `node_modules`, Next.js build cache, and Go compilation.
- Always use the native Linux clone/worktree under the WSL user home directory (e.g., `/home/<user>/CascadeProjects/mopheus/.worktrees/<worktree-name>`).

### 2. Cleanup Lingering Processes First
Before starting, ensure both Windows host and WSL have no conflicting preview listeners or orphan daemons:
- Terminate any lingering Windows preview processes on the target ports:
  ```powershell
  Get-NetTCPConnection -LocalPort <frontend_port>, <backend_port> -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
  ```
- Terminate lingering WSL background processes (`mopheusd`, `mopheus daemon`, `next dev`):
  ```bash
  wsl sh -c "pkill -9 -f mopheusd || true; pkill -9 -f 'mopheus.*daemon' || true; pkill -9 -f 'next.*dev' || true"
  ```

### 3. Worktree & Dependency Preparation in WSL
In WSL:
```bash
wsl bash -i -c "cd /home/<user>/CascadeProjects/mopheus && git worktree add .worktrees/<name> <branch-or-commit> -B <name> || true"
wsl bash -i -c "cd /home/<user>/CascadeProjects/mopheus/.worktrees/<name> && pnpm install"
```

### 4. Discover and Start Preview in WSL
Execute the preview start script via WSL interactive shell using the native WSL path:
```bash
wsl bash -i -c "python3 ~/.gemini/config/skills/mopheus-integration-preview/scripts/start_preview.py /home/<user>/CascadeProjects/mopheus/.worktrees/<name>"
```
To reuse a database from an existing worktree in WSL:
```bash
wsl bash -i -c "python3 ~/.gemini/config/skills/mopheus-integration-preview/scripts/start_preview.py --reuse-db-from /home/<user>/CascadeProjects/mopheus/.worktrees/<source-name> /home/<user>/CascadeProjects/mopheus/.worktrees/<target-name>"
```

### 5. Access from Windows Host
- WSL2 automatically forwards loopback ports to the Windows host.
- The user can directly open the printed URLs (e.g., `http://localhost:<frontend_port>/login`, `http://localhost:<backend_port>`) in their Windows browser.
- Backend, Frontend, Daemon, and WebSocket all run within the same WSL network stack, guaranteeing real-time WebSocket push notifications and seamless Agent task lifecycle updates.

## Stop application processes

Only when the user asks to stop this preview:

- **Linux / macOS**:
  ```bash
  make -C <absolute-worktree-path> daemon-stop-worktree
  make -C <absolute-worktree-path> stop-worktree
  ```
- **Windows (Native)**:
  Use PowerShell to stop the backend, frontend, and daemon processes recorded in the preview log directory (`%TEMP%\mopheus-preview-<hash>\*.pid`).
- **Windows (WSL Mode)**:
  ```bash
  wsl sh -c "pkill -9 -f mopheusd || true; pkill -9 -f 'mopheus.*daemon' || true; pkill -9 -f 'next.*dev' || true"
  ```
