---
name: mopheus-integration-preview
description: Discover, synchronize, and start reusable local Mopheus integration-test previews in WSL Ubuntu-24.04 from Windows Git checkouts or worktrees. Use this whenever the user asks to start, prepare, bootstrap, reopen, or inspect a Mopheus preview, integration-test environment, local worktree environment, runtime, daemon, or test login. Synchronize latest Windows code into WSL Ubuntu-24.04 preview-test harness, run migrations, restart backend/frontend/daemon, enable all registered features dynamically, and print local test credentials.
compatibility: Windows host with WSL2 distro Ubuntu-24.04. Target preview harness is /home/kamus/CascadeProjects/mopheus/.worktrees/preview-test using PostgreSQL container mopheus-postgres-1 on localhost:5432.
---

# Mopheus Integration Preview (WSL Ubuntu-24.04 Mode)

Start or refresh the local Mopheus integration preview in the dedicated WSL `Ubuntu-24.04` preview harness (`preview-test`).

## Core Invariants

1. **Fixed WSL Distro**: ALWAYS pass `-d Ubuntu-24.04` to every `wsl` invocation. Never use bare `wsl` or `-d Ubuntu` (which points to an inactive, obsolete distro).
2. **Native Linux ext4 Only**: All Go compilation, Node execution, Next.js dev server, and Docker operations run natively inside `/home/kamus/CascadeProjects/mopheus/.worktrees/preview-test`. **NEVER** search or execute code across `/mnt/c/...` from inside WSL.
3. **Canonical WSL Toolchain PATH**: Non-interactive shells must export full PATH including `/home/kamus/.local/bin` (where `claude`, `kimi-code`, `mop` live):
   ```bash
   export PATH="/home/kamus/.local/bin:/home/kamus/.nvm/versions/node/v24.14.0/bin:/usr/local/go/bin:$HOME/go/bin:/home/kamus/.local/share/pnpm:$PATH"
   ```
4. **Fixed Runtime Server Identity**:
   - Fixed Daemon ID: `5864c916-5e33-4137-8244-d435fd451561`
   - Stale offline daemon records from other IDs are automatically pruned on start.
5. **Direct WSL IP Access**: Connect directly to the WSL IP (or localhost port mirroring if enabled):
   - Backend: `http://<WSL_IP>:8230` or `http://localhost:8230`
   - Frontend: `http://<WSL_IP>:3230` or `http://localhost:3230`
   - Database: `mopheus_wt_preview_test` on `localhost:5432` (`mopheus-postgres-1`)
   - Test Account: `preview-admin@test.local` / `MopheusPreview123!`
   - Test Workspace: `dev-space` (`bb08a9c4-9f3f-414d-8632-d23909bada79`)

---

## One-Click Launch (PowerShell)

Run the bundled launcher from the Windows host:

```powershell
& "C:\Users\kamus\.gemini\config\skills\mopheus-integration-preview\scripts\start_preview_wsl.ps1" -SourcePath "<source-worktree-or-repo-root>"
```

If `-SourcePath` is omitted, it defaults to `C:\Users\kamus\CascadeProjects\mopheus`.

---

## Manual 2-Step Execution (Transparent CLI)

If running commands individually, only two commands are needed:

### Step 1: Push Code from Windows to WSL Harness

Use Windows native `robocopy` over the UNC path. This takes ~2 seconds and preserves `.env.worktree`, build artifacts, and node_modules:

```powershell
robocopy "<source-dir>" "\\wsl.localhost\Ubuntu-24.04\home\kamus\CascadeProjects\mopheus\.worktrees\preview-test" /MIR /NFL /NDL /NJH /NJS /nc /ns /np /XD .git node_modules .next .turbo .worktrees uploads dist bin __pycache__ /XF .env.worktree .env.local *.log *.pid *.tmp
```
*(Exit codes 0 to 7 indicate successful file synchronization).*

### Step 2: Run Native Startup Script in WSL

Execute the native Linux startup script inside `Ubuntu-24.04`:

```powershell
wsl -d Ubuntu-24.04 -- bash /home/kamus/CascadeProjects/mopheus/.worktrees/preview-test/scripts/start_preview.sh
```

---

## What the Native Startup Script Does

The native script (`scripts/start_preview.sh` / `scripts/start_preview_wsl.sh`) executes directly inside Linux:
1. **Frees Ports & Stops Stale Daemon**: Stops old daemon process via `mopheus daemon stop` and clears ports 8230/3230 via `fuser -k`.
2. **Starts Database**: Ensures `docker start mopheus-postgres-1`.
3. **Applies Migrations**: Loads `.env.worktree` and runs `go run ./cmd/migrate up`.
4. **Enables Features & Prunes Runtimes**: Enables all features for `dev-space`, and removes stale/offline daemon records (`WHERE daemon_id != '$FIXED_DAEMON_ID' OR status = 0`).
5. **Compiles Binaries**: Builds `server/bin/mopheusd` and `server/bin/mopheus`.
6. **Starts Backend**: Launches backend detached via `setsid` and waits for port 8230 to be ready.
7. **Registers & Starts Daemon**: Logs in with preview credentials and launches `mopheus daemon start --daemon-id $FIXED_DAEMON_ID --allow-root`.
8. **Starts Frontend**: Launches Next.js detached via `setsid` and waits for port 3230 to be ready.
9. **Prints Status**: Queries eth0 IP and outputs all access URLs and test credentials.

---

## Success Report Format

Present the active endpoints clearly:

```markdown
==================================================
Mopheus WSL Preview is ready!
- Frontend:  http://172.24.94.189:3230 (or http://localhost:3230)
- Backend:   http://172.24.94.189:8230 (or http://localhost:8230)
- Workspace: http://172.24.94.189:3230/dev-space/dashboard
- Skills:    http://172.24.94.189:3230/dev-space/skills
- Runtimes:  http://172.24.94.189:3230/dev-space/settings/runtimes
- Test User: preview-admin@test.local / MopheusPreview123!
- Daemon:    Online (ID: 5864c916-5e33-4137-8244-d435fd451561)
==================================================
```
