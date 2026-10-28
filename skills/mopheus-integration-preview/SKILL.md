---
name: mopheus-integration-preview
description: Discover, synchronize, start, and end-to-end self-verify reusable local Mopheus integration-test previews on Linux and macOS from Git checkouts or worktrees. Use this whenever the user asks to start, prepare, bootstrap, reopen, or verify a Mopheus preview, integration-test environment, local worktree environment, runtime, daemon, or test login. Automatically synchronizes latest worktree/branch code, runs migrations, restarts backend/frontend/daemon, enables all registered features dynamically, executes autonomous browser/CLI end-to-end verification of the target feature/fix, and captures visual screenshot proof before reporting completion. By default uses fixed profile wt-preview-test; only uses dynamic isolated profiles when explicitly requested ("开单独分支靶场").
compatibility: Linux (Ubuntu/Debian) or macOS (Colima/Docker).
---

# Mopheus Integration Preview

Start or refresh the local Mopheus integration preview environment on **Linux** or **macOS**, then **proactively complete end-to-end functional testing and screenshot verification** before handing off to the user.

> [!NOTE]
> **原生 Linux / macOS 执行准则**：
> Agent 直接运行在标准 Linux 或 macOS Shell 环境中，所有命令、脚本路径（如 `$HOME/...`）及服务访问地址（`http://localhost:3230`、`http://localhost:8230`）均直接使用本地原生路径与 `localhost`，**严禁**调用 `wsl.exe`、`powershell.exe` 或访问 `/mnt/c/...` 跨系统路径。

## Profile & Port Modes

### 1. Default Mode: Fixed Preview Profile (默认固定靶场模式)
Unless explicitly instructed to open an isolated branch preview ("开单独分支靶场"), **ALWAYS** use the fixed preview profile and deterministic endpoints:
- **CLI Profile**: `wt-preview-test`
- **Backend Port**: `8230` (`http://localhost:8230`)
- **Frontend Port**: `3230` (`http://localhost:3230`)
- **Database**: `mopheus_wt_preview_test` on `localhost:5432` (`mopheus-postgres-1`)
- **Fixed Daemon ID**: `5864c916-5e33-4137-8244-d435fd451561`
- **Test Accounts**:
  - `alice@mopheus.dev` / `Mopheus@123` (Workspace Member & Owner in `dev-space`, **mandatory for Daemon execution & regular member testing**)
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

### 3. Host CLI Isolation (禁止污染宿主正式 CLI)

> [!CAUTION]
> **严禁把 preview 编译产物接入宿主正式 CLI**：
> - 绝不允许对 `~/.local/bin/mopheus`、`~/.local/bin/mop`、`/usr/local/bin/mopheus` 或任何 PATH 目录执行 `ln -s`、`cp`、`install`，把它们指向或替换为 `.worktrees/preview-test/server/bin/mopheus` 或任何临时编译产物。
> - 正式 CLI 是生产工具，指向 `https://dev.mopheus.ai`；被 preview binary 覆盖后会静默改变工具行为与目标环境，且极难察觉。
> - 所有靶场测试必须用**刚编译产物**的绝对路径调用：`"$PREVIEW_DIR/server/bin/mopheus" --profile wt-preview-test --server_url http://localhost:8230 ...`。
> - `start_preview.sh` 会把 `$HOME/.local/bin` 前置到 `PATH`，因此裸写 `mopheus` / `mop` 命中的是**宿主正式 CLI**，绝不能用于靶场登录、建数据或启动 daemon。
> - 若发现 `~/.local/bin/mop*` 解析到仓库或 worktree 内，先报告并恢复正式二进制，不要在旧软链上继续测试。

### 4. Isolated Mode: Dynamic Worktree Profile (单独分支隔离靶场模式)
Triggered **ONLY** when the user explicitly requests an isolated/dynamic branch environment (e.g. "开单独分支靶场", "动态Profile靶场", or `--dynamic`):
- **CLI Profile**: `<worktree-slug>` (e.g. `feat_cli_ticket_labels`)
- **Backend Port**: `18080 + offset` (e.g. `18153`)
- **Frontend Port**: `13000 + offset` (e.g. `13073`)
- **Database**: `mopheus_<slug>_<offset>` on `localhost:5432`
- **Invocation**: `DYNAMIC_WORKTREE=1 make setup-worktree` or `bash scripts/init-worktree-env.sh --dynamic`

---

## Unified Execution Flow (Linux & macOS)

Run the cross-platform launcher script `scripts/start_preview.sh`, passing the active feature worktree or repository directory as the first argument (defaults to `$PWD` if omitted):

```bash
bash ~/.gemini/config/skills/mopheus-integration-preview/scripts/start_preview.sh "<source-worktree-or-repo-dir>"
```

### What `scripts/start_preview.sh` Performs Automatically (Linux & macOS)
1. **Worktree Resolution & Sync**: Resolves the primary repository via `git rev-parse --git-common-dir`. If `.worktrees/preview-test` exists, syncs `<source-worktree-or-repo-dir>` into `.worktrees/preview-test` via `rsync`; otherwise runs directly in `<source-worktree-or-repo-dir>`.
2. **Stale Process Cleanup**: Stops any existing `wt-preview-test` daemon and frees ports `8230` and `3230` via `lsof`.
3. **Database & Migrations**: Starts Colima (on macOS if stopped) and `mopheus-postgres-1`, initializes `.env.worktree` if missing, ensures `mopheus_wt_preview_test` exists, and runs `go run ./cmd/migrate up`.
4. **Build & Backend Startup**: Compiles `server/bin/mopheusd` and `server/bin/mopheus`, launches `mopheusd` detached via `start_detached.py`, and waits for `:8230`.
5. **Deterministic Seed**: Resets `alice@mopheus.dev` and `admin@mopheus.dev` passwords to `Mopheus@123` (`must_change_password = false`), seeds `dev-space` (`bb08a9c4-9f3f-414d-8632-d23909bada79`) with `alice@mopheus.dev` as Owner (`role = 0`), enables all registered features in `workspace_feature`, and prunes offline/stale `daemon_runtime` entries.
6. **Daemon & Frontend Startup**: Logs in CLI profile `wt-preview-test` as `alice@mopheus.dev`, switches workspace to `dev-space`, starts `mopheus daemon start --daemon-id 5864c916-5e33-4137-8244-d435fd451561 --sandbox-enabled=false --allow-root`, launches Next.js on `:3230` detached via `start_detached.py`, and waits until `:3230` is listening.

---

## Mandatory Self-Test & Visual Verification Loop (强制自主测试与截图验证闭环)

> [!IMPORTANT]
> **切勿仅启动服务后就停手等待用户测试！**
> 只要当前会话涉及任何功能开发、Bug 修复或 UI/CLI 变更（或者用户要求启动靶场进行验证），在靶场启动就绪后，Agent **必须自动执行以下完整测试与截图验证流程**，确保一切功能在真实靶场中验证无误后再向用户汇报。

1. **构造真实测试场景与数据 (Seed Scenario under `alice@mopheus.dev`)**：
   - 使用 `--profile wt-preview-test`（`alice@mopheus.dev` 身份）通过 CLI 或 API 创建验证本次改动所需的业务对象（如 Ticket、Widget 评论、Agent、Skill、Team 等）。
   - 若存量测试 Agent 归属于 `admin`，先通过 `PUT /api/v1/agents/:id/owner` 将其所有权转移给 `alice@mopheus.dev`。
2. **自主执行全链路交互测试 (End-to-End Interactive Self-Testing)**：
   - 启动浏览器自动化工具（Playwright 或 Browser Subagent）访问 `http://localhost:3230`，使用 `alice@mopheus.dev` / `Mopheus@123` 登录进入 `dev-space` 工作区。
   - 按照真实用户操作路径，逐项执行本次需求或修复的正向交互、状态流转与边界场景（如点击控件、提交表单、切换状态、验证提示文案与 i18n 渲染）。
   - 检查网络请求响应与浏览器控制台（Console），确保无未捕获异常、无 `4xx/5xx` 非预期错误、无 i18n 裸 key 泄露。
   - **若测试发现任何缺陷**：立即在源 Worktree 中修复代码 → 重新运行 `start_preview.sh` 同步并重启对应服务 → 重新执行浏览器验证，直至所有验证项 100% 通过。
3. **关键状态截图取证 (Capture Visual Screenshot Evidence)**：
   - 对验证通过的核心界面状态、交互前后对比及关键提示信息进行截图保存（存放于会话 Artifact 目录中，切勿提交到 Git 仓库）。
   - 在最终回复或验证 Artifact 中直接内嵌展示验证截图，直观证明全部功能已实现无误。

---

## Success Report Format

```markdown
==================================================
Mopheus Preview is ready & verified!
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
