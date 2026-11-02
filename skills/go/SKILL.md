---
name: go
description: End-to-end development workflow from ticket to peer-reviewed code. Given a ticket URL or ID, automatically provisions an isolated git worktree via using-git-worktrees, guides code implementation and verification, and drives autonomous Qoder peer review via relay until approval.
---

# Go: End-to-End Ticket Development & Peer Review Workflow

This skill chains the full developer lifecycle from an incoming ticket to peer-reviewed, verified code:
1. **Ticket & Requirement Ingestion**: Parse ticket URL/ID, acceptance criteria, and target repository.
2. **Worktree Provisioning**: Create an isolated Git worktree branching from synced `origin/main` (`using-git-worktrees`).
3. **Goal-Driven Implementation**: Surgical coding, red-green tests, and diff-scoped local verification.
4. **Autonomous Peer Review**: Orchestrate Qoder code review via `relay` CLI (`relay send -t review`), pull verdict back, and loop fixes until `Verdict: APPROVED`.
5. **Readiness Report & Handoff**: Deliver verified summary and await user instruction (strictly honoring the git safety boundary: no unauthorized commits/pushes/PRs).

---

## Quick Reference Pipeline

```
[User: /go <ticket-url>]
          │
          ▼
[Phase 1: Parse Ticket & Requirements]
  - Resolve Mopheus ticket (`mop ticket get`) or GitHub issue (`gh issue view`)
  - State explicit acceptance criteria
          │
          ▼
[Phase 2: Provision Worktree (using-git-worktrees)]
  - Sync local `main` with `origin/main` (fast-forward only)
  - Verify `.worktrees/` is in `.gitignore`
  - Create isolated branch & worktree: `git worktree add .worktrees/<branch> -b <branch> main`
  - Switch to worktree directory
          │
          ▼
[Phase 3: Implement & Verify Scoped Changes]
  - Explore symbols and callers via `codegraph` CLI instead of bare grep
  - Surgical edits matching project guidelines (Simplicity First, TDD)
  - Run diff-scoped verification (backend/frontend/docs tests)
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

## Phase 1: Ticket & Requirement Ingestion

Ensure `~/.local/bin` is in `PATH`:
```bash
export PATH=$PATH:$HOME/.local/bin
```

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
   - **Raw Text / Ad-hoc Request**:
     - Clarify the core requirement and success criteria directly.

2. **Summarize Scope**:
   - State the target feature or bug fix.
   - Identify affected layers/components (e.g. backend Go, web Next.js, database migrations, documentation).
   - Define observable completion criteria.

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

5. **Stop at Git Isolation**:
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

2. **Coding Discipline**:
   - **Think Before Coding**: Surface assumptions and verify existing patterns.
   - **Simplicity First**: Minimum code that solves the problem. No speculative abstractions.
   - **Surgical Changes**: Touch only necessary lines. Match existing codebase style.
   - **TDD / Regression Tests**: Add or update tests verifying the new behavior or reproduction of the fixed bug.

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

4. **Verification Guardrail**:
   - Require exit code 0 and confirm zero failure markers in test output.
   - Inspect `git diff` line-by-line to ensure no accidental changes, leftover debugging statements, or commented-out code.

---

## Phase 4: Autonomous Peer Review via Relay (`relay`)

Once local changes and tests pass, automatically invoke the peer-review gate with Qoder. Do not ask the user for permission to start the review — this is an integral part of `/go`.

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
   Send the structured review prompt:
   ```bash
   relay send <link-name> --to qoder -t review -m "工单: <工单标题/ID>\nURL: <工单URL>\nWorktree: <worktree_path>\n分支: <branch_name>\n【重点关注与改动说明】\n<简述改动核心逻辑与自测验证结论>"
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
   - **Self-Verification**: Exact test/typecheck commands executed and confirmed passing
   - **Qoder Peer Review**: `Verdict: APPROVED` (Transmission ID, round count, key review highlights)

2. **Iron Boundary (Safety Rule)**:
   - **DO NOT commit, push, create a pull request, or merge automatically.**
   - Developing in a worktree represents substantial feature work.
   - **STOP here** and hand control back to the user with actionable next options:
     - Preview testing in local environment (e.g. `make start` or preview harness)
     - Staging and committing changes (`/git-commit` or `git commit`)
     - Complete delivery pipeline (`/github-mopheus-dev-delivery` or `git-commit-and-push`)
