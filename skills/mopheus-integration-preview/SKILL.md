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
- **Test Accounts**:
  - `alice@mopheus.dev` / `Mopheus@123` (Workspace Member & Owner in `dev-space`, **recommended for Daemon execution & regular member testing**)
  - `admin@mopheus.dev` / `Mopheus@123` (System Admin, for system settings & user administration)
- **Test Workspace**: `dev-space` (`bb08a9c4-9f3f-414d-8632-d23909bada79`)

### 2. Runtime & Daemon Principles (运行时与守护进程准则)

> [!CAUTION]
> **严禁向数据库手动插入 Runtime 假数据**：
> - 绝对禁止使用 SQL 向 `daemon_runtime` 表插入任何模拟记录！伪造记录不仅会导致设备名缺失（显示为 `-`），还会绕过真实探活，产生权限与状态机冲突。
> - 所有 Runtime（`antigravity`、`claude`、`codex` 等）必须且只能由运行中的 `mopheus daemon start` 自动探测并上报注册。

> [!IMPORTANT]
> **切勿以系统管理员 (admin) 身份启动 Daemon**：
> - Daemon 注册上报的所有 Runtime 默认归属于启动它的当前登录用户，且可见性为 Private。
> - 若使用系统管理员 `admin@mopheus.dev` 启动 Daemon，普通工作区成员（如 Alice）在触发任务或重试时将无权使用该私有 Runtime（导致 `403/409 runtime access forbidden`）。
> - 务必使用工作区普通成员账号（如 `alice@mopheus.dev`）登录 CLI Profile 并启动 Daemon。

> [!IMPORTANT]
> **预置测试对象必须归属于测试普通成员（如 Alice）**：
> - 帮助或预先创建的所有测试对象（工单 Ticket、智能体 Agent、运行任务 Task、团队 Team 等业务对象），必须由即将交付给用户测试的普通成员账号（如 `alice@mopheus.dev`）创建与归属，严禁默认使用系统管理员 `admin@mopheus.dev`。
> - **原因**：在 Mopheus 权限与隔离体系中，Agent 的所有权、私有 Runtime 的调度权以及任务重试权限均受用户身份约束。若测试 Agent 或工单由 Admin 创建，普通用户登录后不仅可能受限，还可能因 Agent Owner 不是当前用户而无法调度当前用户拥有的本地私有 Runtime（触发 `409 RUNTIME_OFFLINE` 或 `403 forbidden`）。
> - **例外**：仅在明确测试系统管理员专属功能（如全局配置、用户邀请、系统审计日志等）时，才使用 `admin` 账号创建相关测试对象。

### 3. Isolated Mode: Dynamic Worktree Profile (单独分支隔离靶场模式)
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
   SELECT 'bb08a9c4-9f3f-414d-8632-d23909bada79', u.id, CASE WHEN u.email = 'alice@mopheus.dev' THEN 0 ELSE 1 END
   FROM \"user\" u
   ON CONFLICT (workspace_id, user_id) DO UPDATE SET role = EXCLUDED.role;

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
4. **Login Profile & Set Active Workspace**:
   Log in with the workspace test member (`alice@mopheus.dev`) rather than `admin` so runtimes registered by the daemon are owned by the workspace member:
   ```bash
   server/bin/mopheus --profile wt-preview-test --server_url http://localhost:8230 login --email alice@mopheus.dev --password Mopheus@123
   server/bin/mopheus --profile wt-preview-test --server_url http://localhost:8230 workspace switch bb08a9c4-9f3f-414d-8632-d23909bada79
   ```

5. **Compile & Start Services**:
   - **Backend**: `make bin` -> launch `server/bin/mopheusd` with `.env.worktree` (port 8230):
     ```bash
     bash -c "set -a && source .env.worktree && set +a && exec server/bin/mopheusd"
     ```
   - **Frontend**: Next.js development server (port 3230):
     ```bash
     bash -c "set -a && source .env.worktree && set +a && pnpm --filter @mopheus/web dev -p 3230"
     ```
   - **Daemon**: Local agent runtime daemon (discovers installed CLIs such as `agy`, `claude`, `codex` naturally; do NOT manually insert into `daemon_runtime`):
     ```bash
     PATH="$HOME/.local/bin:$PATH" server/bin/mopheus --profile wt-preview-test --server_url http://localhost:8230 daemon start --daemon-id 5864c916-5e33-4137-8244-d435fd451561 --sandbox-enabled=false --foreground
     ```

6. **Pre-seed Test Objects (Tickets, Agents, Tasks)**:
   If creating or preparing test resources for preview verification, ensure commands run under the test member profile (`alice@mopheus.dev`) so that resources are owned by the user under test:
   ```bash
   # Objects created via wt-preview-test profile automatically have owner_id = alice
   server/bin/mopheus --profile wt-preview-test --server_url http://localhost:8230 agent create --name "DevBot" ...
   server/bin/mopheus --profile wt-preview-test --server_url http://localhost:8230 ticket create --title "..." ...
   ```
   If pre-existing agents were created by `admin`, transfer their ownership to the test user (`PUT /api/v1/agents/:id/owner`).

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
- Frontend:    http://localhost:3230
- Backend:     http://localhost:8230
- Workspace:   http://localhost:3230/dev-space/dashboard
- Skills:      http://localhost:3230/dev-space/skills
- Profile:     wt-preview-test
- Database:    mopheus_wt_preview_test
- Test Member: alice@mopheus.dev / Mopheus@123 (for workspace & agent task testing)
- Admin User:  admin@mopheus.dev / Mopheus@123 (for system settings)
==================================================
```
