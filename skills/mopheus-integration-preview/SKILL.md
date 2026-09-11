---
name: mopheus-integration-preview
description: Discover, synchronize, and start reusable local Mopheus integration-test previews on macOS (Colima/Docker) and WSL Ubuntu-24.04 from Git checkouts or worktrees. Use this whenever the user asks to start, prepare, bootstrap, reopen, or inspect a Mopheus preview, integration-test environment, local worktree environment, runtime, daemon, or test login. Synchronize latest code, run migrations, restart backend/frontend/daemon, enable all registered features dynamically, and print local test credentials. By default uses fixed profile wt-preview-test; only uses dynamic isolated profiles when explicitly requested ("开单独分支靶场").
compatibility: macOS (Colima/Docker) or Windows host with WSL2 distro Ubuntu-24.04.
---

# Mopheus Integration Preview

Start or refresh the local Mopheus integration preview environment on **macOS (Colima/Docker)** or **WSL Ubuntu-24.04**.

## Profile & Port Modes

### 1. Default Mode: Fixed Preview Profile (默认固定靶场模式)
Unless explicitly instructed to open an isolated branch preview ("开单独分支靶场"), **ALWAYS** use the fixed preview profile and deterministic endpoints:
- **CLI Profile**: `wt-preview-test`
- **Backend Port**: `8230` (`http://localhost:8230` or `http://<WSL_IP>:8230`)
- **Frontend Port**: `3230` (`http://localhost:3230` or `http://<WSL_IP>:3230`)
- **Database**: `mopheus_wt_preview_test` on `localhost:5432` (`mopheus-postgres-1`)
- **Fixed Daemon ID**: `5864c916-5e33-4137-8244-d435fd451561`
- **Test Account**: `preview-admin@test.local` / `MopheusPreview123!` or `admin@mopheus.dev` / `Mopheus@123`
- **Test Workspace**: `dev-space` (`bb08a9c4-9f3f-414d-8632-d23909bada79`)

### 2. Isolated Mode: Dynamic Worktree Profile (单独分支隔离靶场模式)
Triggered **ONLY** when the user explicitly requests an isolated/dynamic branch environment (e.g. "开单独分支靶场", "动态Profile靶场", or `--dynamic`):
- **CLI Profile**: `<worktree-slug>` (e.g. `feat_cli_ticket_labels`)
- **Backend Port**: `18080 + offset` (e.g. `18153`)
- **Frontend Port**: `13000 + offset` (e.g. `13073`)
- **Database**: `mopheus_<slug>_<offset>` on `localhost:5432`
- **Invocation**: `DYNAMIC_WORKTREE=1 make setup-worktree` or `bash scripts/init-worktree-env.sh --dynamic`

---

## macOS Execution Flow

1. **Verify Docker/Colima**: Ensure `colima status` is running and `docker compose up -d postgres` starts `mopheus-postgres-1`.
2. **Init Environment & Migrate**:
   ```bash
   bash scripts/init-worktree-env.sh .env.worktree
   bash scripts/ensure-postgres.sh .env.worktree
   (cd server && DATABASE_URL="postgres://mopheus:mopheus@localhost:5432/mopheus_wt_preview_test?sslmode=disable" go run ./cmd/migrate up)
   ```
3. **Seed Preview Workspace & Owner Role**:
   ```bash
   docker exec mopheus-postgres-1 psql -U mopheus -d mopheus_wt_preview_test -c "
   INSERT INTO workspace (id, name, slug, description, identifier_prefix)
   VALUES ('bb08a9c4-9f3f-414d-8632-d23909bada79', 'Dev Space', 'dev-space', 'Development Workspace', 'DEV')
   ON CONFLICT (id) DO NOTHING;

   INSERT INTO workspace_member (workspace_id, user_id, role)
   SELECT 'bb08a9c4-9f3f-414d-8632-d23909bada79', u.id, 1
   FROM \"user\" u
   ON CONFLICT DO NOTHING;

   INSERT INTO workspace_actor_role (workspace_id, actor_id, actor_type, role_id)
   SELECT 'bb08a9c4-9f3f-414d-8632-d23909bada79', u.id, 0, 'f47ac10b-58cc-4372-a567-0e02b2c3d400'
   FROM \"user\" u
   ON CONFLICT DO NOTHING;

   INSERT INTO workspace_feature (workspace_id, feature_id, enabled)
   SELECT 'bb08a9c4-9f3f-414d-8632-d23909bada79', f.id, true
   FROM feature f
   ON CONFLICT (workspace_id, feature_id) DO UPDATE SET enabled = true;
   "
   ```
4. **Compile & Start Services**:
   - Backend: `make bin` -> launch `server/bin/mopheusd` with `.env.worktree` (port 8230).
   - Frontend: `pnpm --filter @mopheus/web dev -p 3230`.
5. **Login Profile & Set Active Workspace**:
   ```bash
   server/bin/mopheus --profile wt-preview-test --server_url http://localhost:8230 login --email admin@mopheus.dev --password Mopheus@123
   server/bin/mopheus --profile wt-preview-test --server_url http://localhost:8230 workspace switch bb08a9c4-9f3f-414d-8632-d23909bada79
   ```

---

## WSL Ubuntu-24.04 Execution Flow (Windows Host)

Run the launcher from PowerShell:
```powershell
& "C:\Users\kamus\.gemini\config\skills\mopheus-integration-preview\scripts\start_preview_wsl.ps1" -SourcePath "<source-dir>"
```

---

## Success Report Format

```markdown
==================================================
Mopheus Preview is ready!
- Frontend:  http://localhost:3230
- Backend:   http://localhost:8230
- Workspace: http://localhost:3230/dev-space/dashboard
- Skills:    http://localhost:3230/dev-space/skills
- Profile:   wt-preview-test
- Database:  mopheus_wt_preview_test
- Test User: admin@mopheus.dev / Mopheus@123
==================================================
```
