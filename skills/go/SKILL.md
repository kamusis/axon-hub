---
name: go
description: End-to-end development workflow from ticket or chat consensus to peer-reviewed code. Given a ticket URL/ID or an agreed plan in chat, automatically provisions an isolated git worktree via using-git-worktrees, guides code implementation and verification (enforcing Repro-First and Sequence-Verifiable-Units), and drives autonomous Qoder peer review via relay until approval.
---

# Go: End-to-End Development & Peer Review Workflow

This skill chains the full developer lifecycle from an incoming ticket or an in-flight conversation consensus to peer-reviewed, verified code:
1. **Requirement & Scope Ingestion**: Dual-mode ingestion — parse ticket URL/ID, or inherit an agreed solution plan directly from the current conversation without external API calls.
2. **Worktree Provisioning**: Create an isolated Git worktree branching from synced `origin/main` (`using-git-worktrees`).
3. **Goal-Driven Implementation**: Surgical coding, mandatory Repro-First check, Sequence-Verifiable-Units (2-commit rule for bug fixes: Red then Green), diff-scoped unit verification, and mandatory local feature E2E / runtime test pass with physical evidence.
4. **Autonomous Peer Review**: Orchestrate Qoder code review via `relay` CLI (`relay send -t review`), pull verdict back, and loop fixes until `Verdict: APPROVED`.
5. **Readiness Report & Handoff**: Deliver verified summary and await user instruction (strictly honoring the git safety boundary: no unauthorized commits/pushes/PRs).

---

## Quick Reference Pipeline

```
[User: /go <ticket-url> OR /go [action-hint]]
          │
          ▼
[Phase 1: Ingestion (Dual-Mode)]
  ├── Mode A (Ticket-Driven): Resolve Mopheus ticket (`mop ticket get`) or GitHub issue (`gh issue view`)
  └── Mode B (Context-Ready): Zero external calls; inherit in-flight chat consensus plan, derive branch & AC
          │
          ▼
[Phase 2: Provision Worktree (using-git-worktrees)]
  - Sync local `main` with `origin/main` (fast-forward only)
  - Verify `.worktrees/` is in `.gitignore`
  - Create isolated branch & worktree: `git worktree add .worktrees/<branch> -b <branch> main`
  - Link synced `.codegraph` from main worktree into new worktree
  - Switch to worktree directory
          │
          ▼
[Phase 3: Implement & Verify Scoped Changes]
  - Explore symbols and callers via `codegraph` CLI instead of bare grep
  - Surgical edits matching project guidelines (Simplicity First, TDD)
  - Bug Fixes: Mandatory Repro-First (failing check) -> Commit RED -> Fix -> Commit GREEN
  - Run diff-scoped verification (backend/frontend/docs tests)
  - Mandatory Feature E2E & Runtime Verification Gate: run local E2E / `verify-mopheus`, sync feature map, and capture physical evidence before review
          │
          ▼
[Phase 4: Autonomous Qoder Peer Review (relay)]
  - Auto-bootstrap Qoder session & link (`review-<workspace>`)
  - Send review request: `relay send <link> --to qoder -t review -m "..."`
  - Pull review verdict: `relay send <link> --to agy`
  - If blocking items: fix in worktree → re-verify → `relay send -t followup` until APPROVED
          │
          ▼
[Phase 5: Completion Report & User Handoff]
  - Present worktree path, branch, diff summary, verification evidence, and Qoder verdict
  - STOP and await user instruction (no unprompted commit/push/PR)
```

---

## Phase 1: Requirement & Scope Ingestion (Dual-Mode)

Ensure `~/.local/bin` is in `PATH`:
```bash
export PATH=$PATH:$HOME/.local/bin
```

Support two parallel ingestion modes based on user invocation:

### Mode A: Ticket-Driven Ingestion (Explicit Ticket URL / ID / Issue)
Triggered when the user invokes `/go <ticket-url>`, `/go <ticket-id>`, or `/go #<issue-num>`:
1. **Extract Ticket Identifier**:
   - **Mopheus Ticket URL** (e.g. `https://dev.mopheus.ai/w/<workspace>/tickets/<id>` or `MOP-XXXX`):
     - Query ticket details using `mop` or `mopheus` CLI:
       ```bash
       mop ticket get <ticket-id> -o json
       ```
     - Extract: Title, Description, Acceptance Criteria, Priority, Labels, and Target Repository.
   - **GitHub Issue URL** (e.g. `https://github.com/<owner>/<repo>/issues/<num>` or `#<num>`):
     - Query issue details using `gh`:
       ```bash
       gh issue view <num> --json title,body,labels
       ```
2. **Summarize Scope**:
   - State the target feature or bug fix.
   - Identify affected layers/components (e.g. backend Go, web Next.js, database migrations, documentation).
   - Define observable completion criteria.

### Mode B: Context-Ready Ingestion (Chat Consensus / In-Flight Plan)
Triggered when the user invokes `/go` with no arguments, or with an action hint like `/go 修复`, `/go 按上述方案实现`, `/go 开始开发`:
1. **Zero External API Calls**: Do not call `mop ticket get` or `gh issue view`. Immediately inherit the solution plan, architecture consensus, or reproduction findings discussed and agreed upon in the current conversation.
2. **Synthesize In-Flight Specification**:
   - **Target & Scope**: Extract the core objective from recent consensus (e.g. "Task Flow 弹窗尺寸瘦身与滚动穿透修复").
   - **Branch Name Derivation**:
     - If a ticket ID or number was mentioned earlier in the session (e.g. `MOC-1202`), derive branch name: `fix/moc-1202-<slug>` or `feat/moc-1202-<slug>`.
     - Otherwise, derive a concise kebab-case branch name from the problem description: `fix/<short-slug>` or `feat/<short-slug>`.
   - **Acceptance Criteria (AC)**: Convert the agreed plan points directly into numbered observable acceptance criteria to guide Phase 3 implementation and Phase 4 review.
3. **Brief Echo & Proceed**: State the derived branch name, target scope, and AC in 1-2 lines and transition directly into Phase 2 without asking repetitive confirmation questions.

---

## Phase 2: Isolated Workspace Setup (`using-git-worktrees`)

Follow the rules of `using-git-worktrees` strictly:

1. **Detect Project Name & Root**:
   ```bash
   project=$(basename "$(git rev-parse --show-toplevel)")
   ```

2. **Sync Local `main` Branch**:
   Ensure local `main` is strictly up to date with `origin/main` before branching:
   ```bash
   current_branch=$(git symbolic-ref --short -q HEAD)
   if [ "$current_branch" = "main" ]; then
     git fetch origin main
     git merge --ff-only origin/main
   else
     git fetch origin main:main
   fi
   ```
   *If fast-forward fails (local `main` diverged or unpushed commits exist): **STOP** and report divergence to the user before proceeding.*

3. **Verify Worktree Directory & `.gitignore`**:
   - Preferred directory: `.worktrees/`.
   - Ensure it is ignored:
     ```bash
     git check-ignore -q .worktrees 2>/dev/null
     ```
   - If not ignored, add `.worktrees/` to `.gitignore`, commit immediately, and continue.

4. **Derive Branch Name & Create Worktree**:
   - Format: `feat/<ticket-id-or-slug>` or `fix/<ticket-id-or-slug>` (e.g. `feat/mop-1234-login-fix` or `fix/issue-56-auth`).
   - Create worktree branching explicitly from `main`:
     ```bash
     git worktree add .worktrees/<branch-name> -b <branch-name> main
     cd .worktrees/<branch-name>
     ```

5. **Link Synced CodeGraph Index from Main Worktree**:
   Probe the main worktree for an existing, synced `.codegraph` database:
   ```bash
   main_worktree=$(git worktree list | head -n 1 | awk '{print $1}')
   if [ -s "$main_worktree/.codegraph/codegraph.db" ]; then
     mkdir -p .codegraph
     ln -sf "$main_worktree/.codegraph/codegraph.db" .codegraph/codegraph.db
   fi
   ```
   *Benefit*: Equips the isolated worktree with instant semantic code intelligence for Phase 3 without slow re-indexing or duplicating database disk consumption (~300MB). Preserves git cleanliness for `.codegraph/.gitignore`.

6. **Stop at Git Isolation**:
   - Do NOT run heavy monolithic builds, dependency reinstalls, or container migrations during worktree creation.
   - Only execute targeted setup/verification commands when needed during development.

---

## Phase 3: Goal-Driven Coding & Diff-Scoped Verification

1. **Code Intelligence & Architecture Exploration (`codegraph` CLI)**:
   Before modifying or writing code, explore existing architecture, symbol definitions, and caller impact using `codegraph` CLI instead of blindly guessing or relying solely on plain text `grep`:
   - **Symbol Lookup**: `codegraph query <symbol>` (semantic AST resolution, bypassing comments/fixtures).
   - **Area Context**: `codegraph explore <query>` (captures relevant symbols and call paths in one shot).
   - **Caller Blast Radius**: `codegraph callers <symbol>` (traces external call sites of modified functions).
   - **Callee Dependencies**: `codegraph callees <symbol>` (inspects downstream dependencies).
   - **Impact Analysis**: `codegraph impact <symbol>` (evaluates blast radius before changing public signatures).
   - **Affected Tests**: `codegraph affected <file...>` (identifies test suites covering changed files).
   *Fallback rule: Only use `grep` / `rg` for non-code files (markdown, YAML, config) or when the project has not initialized a CodeGraph index.*

2. **Coding Discipline & Repro-First Pipeline**:
   - **Think Before Coding**: Surface assumptions, verify existing architectural patterns, and evaluate contracts.
   - **Simplicity First**: Minimum code that solves the problem. No speculative abstractions or unasked flexibility.
   - **Surgical Changes**: Touch only necessary lines. Match existing codebase style.
   - **Bug Fix Workflow (Mandatory Repro-First & Sequence-Verifiable-Units)**:
     - *Hard Prohibition*: Strictly forbid editing production/business code until the defect is reproduced as an executable check.
     - *Step A (Reproduction Check)*: Write the narrowest executable check (Go package test, Vitest, CLI invocation, or preview test). Run it and capture the failing output matching the reported defect.
     - *Step B (Commit RED)*: In the feature worktree, commit the failing test/reproduction first:
       ```bash
       git add <test-files> && git commit -m "test: add failing reproduction for <ticket-id>"
       ```
     - *Step C (Fix Implementation)*: Implement the minimal production change that resolves the failure without touching adjacent logic.
     - *Step D (Verify GREEN)*: Rerun the check and confirm it passes cleanly.
     - *Step E (Commit GREEN)*: Commit the fix on top:
       ```bash
       git add <source-files> && git commit -m "fix: <concise summary>"
       ```
     - *Evidence Trail*: Retain both the failing-before log and passing-after log for the Phase 4 review handoff.
   - **New Feature Workflow (Sequence-Verifiable-Units)**:
     - Deliver in clean, compilable, verifiable units per `tdd` Story Orders.
     - Either commit atomic units (`feat: add <feature> and tests`) or layered dependency order (`models/migrations` -> `service` -> `web/E2E`).
     - Never create artificial failing commits that break compilation.
   - **Refactoring & Optimization Workflow**:
     - *Refactoring*: Subtraction before reshape (first commit cleans dead code/callers, second commit restructures).
     - *Optimization*: Baseline capture before treatment (first commit records baseline metrics, second commit applies algorithmic improvement).
   - **Anti-Mock Hell ("Prefer No Test Over a Bad Test")**:
     - Do not write mock-heavy unit tests that mock owned internal collaborators or state.
     - If unit testing requires excessive mocks of internal code, skip the bad unit test and rely on the closest real-surface executable check: integration tests with real DB, CLI invocations, or `verify-mopheus` preview driving.

3. **Execute Diff-Scoped Verification**:
   Analyze changed files (`git status --porcelain` or `git diff --name-only origin/main...HEAD`) and run scoped checks:
   - **Mopheus Backend Go** (`server/**`, `cmd/**`):
     ```bash
     cd server && go test -race <package_path>
     ```
   - **Mopheus Frontend Web** (`apps/web/**`):
     ```bash
     make check-web
     ```
     *(Or focused test: `cd apps/web && pnpm vitest run path/to/file.test.ts`)*
   - **Documentation** (`packages/docs-content/**`, `docs/**`):
     ```bash
     make check-docs-nav
     ```
   - **General Repositories**:
     Execute the repository's native test / typecheck / lint command as specified in `AGENTS.md` or `package.json` / `Makefile`.

4. **Targeted Feature E2E Verification & Feature Map Gate (Mandatory Gate Before Qoder Review)**:
   Before submitting code to Qoder for the first review, **you must execute the corresponding E2E / runtime test locally for any modified or newly added feature**, ensuring the end-to-end user journey passes completely and physical evidence is captured. Never proceed to review with unverified claims:
   - **Feature Map Synchronization**:
     - Check the verification skill (e.g. `verify-mopheus`, inspecting `features/` directory):
     - If touching an existing mapped domain (such as `ticket-lifecycle.md`), execute its driving recipe.
     - If introducing a new user-facing domain or materially altering user flows/contracts: **synchronously add or update features/<domain>.md in verify-mopheus** (recording Sub-features, User POV entry points, Driving commands, and Gotchas).
   - **Identify or Synchronously Add/Update the E2E Spec**:
     - Locate the spec file under `tests/e2e/services/<domain>/` covering the touched feature, API, or UI component;
     - For new features or altered workflows/contracts, synchronously write or update the corresponding E2E spec (in strict compliance with `AGENTS.md` E2E synchronization rules).
   - **Execute Local Feature E2E & Runtime Verification**:
     - **Direct Preview Driving via `verify-mopheus`**:
       Use `verify-mopheus` to drive the preview instance (`:8230`/`:3230`), execute API mutations, assert DB state, and capture local verification screenshots via `preview_screenshot.js` to `/tmp/mopheus-verify-<ticket-id>.png`.
     - **Direct External-Services Playwright Mode**: If local dev or preview services are already running (e.g. `localhost:3000` / `localhost:8080`), run directly in seconds:
       ```bash
       E2E_SKIP_SETUP=1 \
       E2E_FRONTEND_URL=http://localhost:3000 \
       E2E_BACKEND_URL=http://localhost:8080 \
       pnpm exec playwright test --config=playwright.full.config.ts --project=external-services tests/e2e/services/<domain>/<spec-file>.spec.ts
       ```
     - **Isolated Container Mode**: Run the target spec in an isolated container environment:
       ```bash
       make test-e2e-full ARGS="tests/e2e/services/<domain>/<spec-file>.spec.ts"
       ```
   - **Hard Gate**: Require exit code 0, zero test failures, and non-empty physical evidence (console test log, screenshot paths, DB query result). If verification fails, fix locally until clean before dispatching to Phase 4.

5. **Verification Guardrail**:
   - Require exit code 0 and confirm zero failure markers in unit tests, typecheck, and the targeted feature E2E / runtime output.
   - Inspect `git diff` line-by-line to ensure no accidental changes, leftover debugging statements, or commented-out code.

---

## Phase 4: Autonomous Peer Review via Relay (`relay`)

Once local changes, diff-scoped checks, and the feature's targeted E2E test pass, automatically invoke the peer-review gate with Qoder. Do not ask the user for permission to start the review — this is an integral part of `/go`.

1. **Resolve Sessions and Links**:
   ```bash
   # 1. Resolve source Antigravity session ID (current session)
   # 2. Check for existing Qoder session in the current workspace
   relay session list -w "$(pwd)"

   # If no Qoder session exists, auto-bootstrap one:
   qodercli -w "$(pwd)" --dangerously-skip-permissions -p "你是本项目的资深架构与代码评审员，请保持待命进行审查。"

   # 3. Check or create communication link (format: review-<workspace-basename>)
   relay link list
   # If link missing:
   relay link create <link-name> <agy-session-id> <qoder-session-id>
   ```

2. **Dispatch Review Request to Qoder (Template Mode: `-t review`)**:
   Send the structured review prompt (including confirmed passing unit tests, feature map sync, and physical proof evidence):
   ```bash
   relay send <link-name> --to qoder -t review -m "工单: <工单标题/ID>\nURL: <工单URL>\nWorktree: <worktree_path>\n分支: <branch_name>\n【重点关注与改动说明】\n<简述改动核心逻辑>\n【物理验证证据】\n- 单测/E2E 结果: <测试通过日志与退出码 0>\n- 复现时序证明 (Bug修复时必填): <红灯提交 SHA 与复现失败日志 -> 绿灯提交 SHA 与通过日志>\n- 预览截图/接口断言: <截图路径 /tmp/...png 或 DB 查询记录>\n- 特性地图同步: <新增/更新的 features/*.md 路径>"
   ```
   *Execution note: `relay send` will wait for Qoder's headless execution to finish (typically 30–60s).*

3. **Retrieve Review Verdict into Antigravity**:
   ```bash
   relay send <link-name> --to agy
   ```
   *If Qoder is still busy, wait 5–10s and re-run `relay send <link-name> --to agy`. NEVER bypass relay by reading private JSONL or SQLite files directly.*

4. **Multi-Round Convergence Loop**:
   - Inspect the retrieved review verdict in Antigravity.
   - **Case A: `Verdict: APPROVED`**
     - Peer-review gate passed. Proceed to Phase 5.
   - **Case B: `Verdict: CHANGES REQUESTED (N blocking)`**
     - Review the blocking issues identified by Qoder.
     - Implement the fixes in the worktree.
     - Re-run local verification commands to confirm tests pass.
     - Dispatch followup review using `-t followup`:
       ```bash
       relay send <link-name> --to qoder -t followup -m "已针对上一轮意见整改：\n1. <修复点1>\n2. <修复点2>\n本地验证已通过，请复核终审裁决。"
       ```
     - Retrieve updated verdict: `relay send <link-name> --to agy`.
     - Repeat until `Verdict: APPROVED`.

---

## Phase 5: Delivery Readiness Report & Boundaries

Present a clear, high-signal summary report:

1. **Delivery Summary**:
   - **Ticket**: `[<Ticket-ID>] <Title>` (<Ticket-URL>)
   - **Worktree**: `<full-worktree-path>`
   - **Branch**: `<branch-name>` (based on `main` @ `<short-sha>`)
   - **Changes**: Bulleted summary of modified files and architectural impact
   - **Self-Verification**: Exact test/typecheck commands and feature E2E tests executed and confirmed passing
   - **Qoder Peer Review**: `Verdict: APPROVED` (Transmission ID, round count, key review highlights)

2. **Iron Boundary (Safety Rule)**:
   - **DO NOT commit, push, create a pull request, or merge automatically.**
   - Developing in a worktree represents substantial feature work.
   - **STOP here** and hand control back to the user with actionable next options:
     - Preview testing in local environment (e.g. `make start` or preview harness)
     - Staging and committing changes (`/git-commit` or `git commit`)
     - Complete delivery pipeline (`/github-mopheus-dev-delivery` or `git-commit-and-push`)
