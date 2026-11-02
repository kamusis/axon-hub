---
name: mopheus-integration-preview
description: Synchronize feature code into local Mopheus preview worktree (wt-preview-test), cleanly start backend/frontend, run database migrations/seeds, and capture visual verification screenshots locally without external uploads. Use whenever asked to start, prepare, test, or verify changes in the Mopheus preview environment.
compatibility: Linux (Ubuntu/Debian) or macOS.
---

# Mopheus Integration Preview

Synchronize latest code from a feature worktree into the reusable local preview environment (`wt-preview-test`), launch backend and frontend cleanly, and capture local verification screenshots for chat review.

## Fixed Endpoints & Credentials

All preview operations run against deterministic local endpoints:
- **CLI Profile**: `wt-preview-test`
- **Backend**: `http://localhost:8230`
- **Frontend**: `http://localhost:3230`
- **Database**: `mopheus_wt_preview_test` on `localhost:5432` (`mopheus-postgres-1`)
- **Fixed Daemon ID**: `5864c916-5e33-4137-8244-d435fd451561`
- **Test Accounts**:
  - `alice@mopheus.dev` / `Mopheus@123` (Dev Space Owner, regular testing & daemon runner)
  - `admin@mopheus.dev` / `Mopheus@123` (System Admin)
- **Default Workspace**: `dev-space` (`bb08a9c4-9f3f-414d-8632-d23909bada79`)

---

## Standard Workflow

### Step 1: Start or Refresh Preview Environment
Run the launcher script with the current workspace or source worktree:

```bash
bash ~/.gemini/config/skills/mopheus-integration-preview/scripts/start_preview.sh ["<source-worktree-or-repo-dir>"]
```

**What it automatically guarantees**:
1. **Code Sync**: Rsyncs feature code into `.worktrees/preview-test`.
2. **Clean Process Lifecycle**: Kills stale processes on `:8230` and `:3230`.
3. **Database Migrations & Feature Flags**: Executes `go run ./cmd/migrate up` so new migrations and schema changes are immediately applied; syncs `workspace_feature` so newly added features are enabled in `dev-space`.
4. **Backend Build**: Incremental compile of `server/bin/mopheusd` and `server/bin/mopheus`.
5. **Clean Frontend State**: Purges `apps/web/.next` compile cache before starting Next.js on `:3230` to prevent Turbopack CSS/chunk reuse.

### Step 1b (Optional): Single Service Restart
When only frontend or backend needs restarting without running the full pipeline:

```bash
# Restart frontend only (cleans .next, inherits .env.worktree, awaits :3230)
bash ~/.gemini/config/skills/mopheus-integration-preview/scripts/restart_service.sh frontend

# Rebuild and restart backend only (awaits :8230)
bash ~/.gemini/config/skills/mopheus-integration-preview/scripts/restart_service.sh backend

# Restart daemon only
bash ~/.gemini/config/skills/mopheus-integration-preview/scripts/restart_service.sh daemon
```

---

### Step 2: Seed Scenario Data (if required)
Use the freshly built preview binary to create or update test data under `alice@mopheus.dev`:

```bash
"$PREVIEW_DIR/server/bin/mopheus" --profile wt-preview-test --server_url http://localhost:8230 ticket create --title "..."
```

---

### Step 3: Capture Verification Screenshot
Use the built-in, authenticated headless screenshot tool:

```bash
node ~/.gemini/config/skills/mopheus-integration-preview/scripts/preview_screenshot.js \
    --url "/dev-space/tickets/<ticket-id>" \
    --output "<artifact-dir>/screenshot.png" \
    [--selector "<css-selector>"] \
    [--hover "<css-selector>"] \
    [--wait 1000]
```

- **Authentication**: Automatically authenticates via backend API as `alice@mopheus.dev`, injecting both the `mopheus_auth` cookie and `localStorage` auth state.
- **Headless Browser**: Automatically locates Playwright Chromium / headless-shell binaries.
- **Selective Capture**: Pass `--selector` to capture a specific component (e.g. `[data-ticket-description]` or `table`) or omit for full viewport.
- **Hover Interactions**: Pass `--hover` to trigger HoverCards, dropdowns, or tooltips before capturing.

---

### Step 4: Visual Review in Chat (Zero External Upload)

> [!IMPORTANT]
> **切勿调用 see-uploader 或任何第三方图床！**
> 截图为本地临时验证凭据，严禁浪费图床配额。
> 直接通过 Antigravity 的 `read_file` 工具查看截图并呈现在聊天对话流中供用户直观校验。
