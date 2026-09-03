---
name: github-issue-to-mopheus-dev-ticket
description: "Create a complete, detailed Chinese Mopheus dev ticket as the primary implementation entry and a paired concise English GitHub issue in enmotech/mopheus. Ensures the GitHub issue links to the Mopheus ticket using the full Ticket UUID. Supports existing-ticket, existing-issue, and new-report modes, auto-assigns tickets to the matching repository project, and enforces CLI-first design and comprehensive multi-tier testing acceptance criteria."
---

# GitHub Issue to Mopheus Dev Ticket

This skill bridges user requests, bug reports, and feature specifications between the **Mopheus Dev Workspace** and the **`enmotech/mopheus` GitHub repository**.

## Core Philosophy & Weighting

- **Mopheus Dev Ticket (Primary & Comprehensive)**: The Mopheus dev ticket is the **primary, authoritative internal implementation specification**. It must be written in **detailed Chinese**, containing the complete reproduction steps, detailed root cause analysis, exhaustive technical architecture (strictly following CLI-first design), and multi-tier acceptance criteria.
- **GitHub Issue (Concise & Linked)**: The GitHub issue is the **external tracking issue** written in **concise English**. It must capture the core summary, key reproduction/motivation points, and acceptance criteria, and **MUST include a direct link to the Mopheus Dev Ticket using the Ticket UUID**.

> [!IMPORTANT]
> **Ticket Link URL Rule (Mandatory Ticket UUID)**:
> The Mopheus ticket URL in the GitHub issue **MUST always use the 36-character Ticket UUID** (e.g. `https://dev.mopheus.ai/dev-space/tickets/16c95e02-ba4b-4e86-a06b-0de4b8bb4c5a`), **NOT** the short sequential integer number (e.g. NOT `/tickets/608` or `/tickets/#608`). The Mopheus Web UI router is keyed directly on the Ticket UUID; using an integer ID will cause the URL to fail to open or result in a 404 error.

---

## Supported Modes

1. **New-report mode (Default)**:
   - Create the comprehensive Chinese Mopheus ticket first to acquire the new **Ticket UUID** and number.
   - Create the paired concise English GitHub issue containing the Mopheus ticket UUID link.
   - Link the GitHub issue to the Mopheus ticket via `mopheus repo issue sync` and bind to the matching project.
2. **Existing-Ticket mode**:
   - When invoked within the context of an existing Mopheus ticket (e.g. agent task running under a ticket, or a ticket ID is provided), do NOT create a new child or separate ticket.
   - Do NOT overwrite the original ticket description (preserving history/audit trail).
   - Create the concise English GitHub issue containing the existing Mopheus ticket UUID link (`https://dev.mopheus.ai/<workspace-slug>/tickets/<ticket-uuid>`).
   - Post a structured Chinese reply comment on the existing ticket with the GitHub issue link and technical design/acceptance criteria.
   - Link the ticket to the GitHub issue via `mopheus repo issue sync` and bind to the matching project.
3. **Existing-Issue mode**:
   - Verify the supplied GitHub issue and confirm it has no linked Mopheus ticket.
   - Create the comprehensive Chinese Mopheus ticket first.
   - Update the existing GitHub issue body (or post a comment) with the newly created Mopheus ticket UUID link.
   - Link the ticket to the GitHub issue via `mopheus repo issue sync` and bind to the matching project.

---

## Fixed GitHub Target and External Fallback

The GitHub target is always fixed. The Mopheus target depends on the caller:

- **GitHub CLI**: use `gh-wrapper` when it is available; otherwise use `gh`
- **GitHub repository**: `enmotech/mopheus`
- **Canonical GitHub repository URL for Mopheus repo operations**: `https://github.com/enmotech/mopheus.git`
- **External fallback server**: `https://dev.mopheus.ai`
- **External fallback profile**: `default`
- **External fallback workspace name**: `dev`
- **External fallback workspace slug**: `dev-space`
- **External fallback workspace ID**: `a43acd83-25f4-43ea-bdfd-d179fb272172`

The GitHub repository is fixed because this skill is specific to Mopheus. Do not derive or override it from the current directory, local Git remotes, active GitHub repository, Mopheus workspace, or prior conversation.

---

## Resolve the Mopheus Target

Require the host-installed `mopheus` executable from PATH in all modes. Never use `mop`, `go run ./cmd/mopheus`, `make mopheus`, a repository/worktree binary, or a temporary build.

### Internal Mopheus-agent mode

Use this mode only when authoritative task/runtime context identifies the caller as a Mopheus agent task and supplies that task's workspace ID. The task workspace has highest priority and cannot be overridden by the user, active CLI workspace, fallback ID, or prior conversation.

1. Read the task workspace ID from the trusted Mopheus task context.
2. Preserve runtime-provided Mopheus server, authentication, and profile context.
3. Verify authentication, then run `mopheus workspace get <task-workspace-id> --output json` to retrieve the workspace `slug`.
4. Require the returned workspace ID to equal the task workspace ID. Stop on missing access, authentication failure, server ambiguity, or mismatch.
5. Pass `--workspace-id <task-workspace-id>` explicitly on every workspace-scoped command.

Set `<target-workspace-id>` to the verified task workspace ID, `<target-workspace-slug>` to the workspace slug, and `<target-connection-args>` to the runtime-provided profile arguments.

### External caller mode

Use this mode for Codex, Claude, Antigravity, or any invocation without trustworthy Mopheus task workspace context:

1. Use only the `default` profile. Never use or repoint `local`, `wt-*`, or another preview/test profile.
2. Do not source `.env.worktree`. Remove preview environment overrides (`MOPHEUS_PROFILE`, `MOPHEUS_SERVER_URL`, `MOPHEUS_WORKSPACE_ID`, `MOPHEUS_TOKEN`, etc.).
3. Verify the formal profile and ensure server URL is `https://dev.mopheus.ai`:
   ```bash
   mopheus --profile default auth status
   ```
4. Query workspace details:
   ```bash
   mopheus --profile default workspace get a43acd83-25f4-43ea-bdfd-d179fb272172 --output json
   ```
   Confirm workspace name is `dev` and slug is `dev-space`.
5. Pass `--profile default` on every command and `--workspace-id a43acd83-25f4-43ea-bdfd-d179fb272172` on every workspace-scoped command.

Set `<target-workspace-id>` to `a43acd83-25f4-43ea-bdfd-d179fb272172`, `<target-workspace-slug>` to `dev-space`, and `<target-connection-args>` to `--profile default`.

---

## Workflow Steps

### Step 0: Select the Mode

- **Existing-Ticket mode:** Check whether running under an existing Mopheus ticket (associated `ticketId` or explicit ticket ID provided).
  - Verify ticket: `mopheus <target-connection-args> --workspace-id <target-workspace-id> ticket get <ticket-id> --output json`.
  - Check existing links: `mopheus <target-connection-args> --workspace-id <target-workspace-id> repo links --ticket <ticket-id> --output json`.
  - If already linked, return existing records and stop.
  - If unlinked, proceed to Step 1 & 2 (extract evidence), Step 3 (screenshots), Step 4 (create concise GitHub issue with ticket UUID URL), Step 5 Path B (post detailed reply comment on ticket), Step 6 (sync link), Step 7 (project binding).
- **Existing-Issue mode:** Check if user supplies an existing GitHub issue URL or number.
  - Verify issue: `gh-wrapper issue view <number> --repo enmotech/mopheus`.
  - Check existing links: `mopheus <target-connection-args> --workspace-id <target-workspace-id> repo links --repo https://github.com/enmotech/mopheus.git --type git_issue --number <n> --output json`.
  - If already linked, return and reuse it.
  - If unlinked, proceed to Step 1 & 2, Step 5 Path A (create detailed Chinese ticket), Step 4 (update existing GitHub issue with ticket UUID URL), Step 6 (sync link), Step 7 (project binding).
- **New-report mode:** Follow Steps 1 through 8.

---

### Step 1: Resolve Report Scope & Extract Evidence

- Extract exact reproduction steps, expected vs actual behavior, error messages, logs, IDs, and root cause analysis.
- If relevant screenshots are present in the conversation, upload them using the S.EE uploader skill/script to obtain public Markdown image URLs.
- Categorize as `bug` or `feature`.

---

### Step 2: Create the Detailed Chinese Mopheus Dev Ticket (Primary Entry)

In **New-report mode** (or Existing-Issue mode), create the **detailed Chinese Mopheus ticket first** so its UUID can be embedded into the GitHub issue:

```bash
mopheus <target-connection-args> --workspace-id <target-workspace-id> ticket create \
  --title "<清晰明确的中文标题>" \
  --priority high \
  --status todo \
  --description-stdin <<'EOF'
...
EOF
```

#### Detailed Chinese Ticket Structure:

```markdown
## 需求背景与目标 / 问题背景
[详尽阐述业务背景、用户需求、触发场景或缺陷影响]

## 复现步骤与环境（针对 Bug）
1. [步骤 1]
2. [步骤 2]
- **环境信息**: [OS / 浏览器 / 数据库 / 组件版本]

## 验证证据与根因分析
- **现象截图 / 日志**: [嵌入 S.EE 截图链接或详细错误调用栈]
- **根因分析**: [代码层面的根本原因剖析，指明涉及的 package / file / struct / handler]

## 详细功能设计与技术方案（严格遵循 CLI 优先原则）
- **架构设计**: [前后端交互流与数据契约]
- **CLI 命令与参数设计**:
  - `mop <domain> <subcommand> [flags]`
  - 参数说明表与输入/输出示例（支持 `--*-file` / `--*-stdin` / `--output json`）
- **后端 API & 数据模型**: [HTTP Handler 路由、Service 方法、SQL/Repo 变更]
- **前端 Web UI 交互设计**: [页面布局、组件复用、交互状态与 i18n 键名]

## 完备的验收标准（必须包含全层级测试交付要求）
1. [业务功能要求 1]
2. [业务功能要求 2]
3. **全层级质量与测试交付要求**:
   - **单元测试 (Unit Tests)**: 覆盖后端 Repo、Service 逻辑/权限/错误码、HTTP Handler、CLI 参数解析与 Frontend Hooks/Components/Stores。
   - **集成测试 (Integration Tests)**: 明确更新或新增 `tests/integration/` 场景说明规范（Markdown）及 `tests/integration/scripts/` 自动化测试脚本。
   - **E2E / Playwright 测试**: 对所有用户可见功能及交互行为，明确更新或新增 `tests/e2e/*.spec.ts` 浏览器端到端交互用例。
```

> **Note**: Capture the created `ticket.id` (UUID, e.g. `16c95e02-ba4b-4e86-a06b-0de4b8bb4c5a`) and `ticket.number` (e.g. `608`).

---

### Step 3: Create or Update the Concise English GitHub Issue

Create the GitHub issue in `enmotech/mopheus`. The GitHub issue should be **concise**, focusing on the high-level summary, key problem/requirement, acceptance criteria, and **MUST contain the Mopheus Dev Ticket link with the Ticket UUID**.

```bash
gh-wrapper issue create --repo enmotech/mopheus \
  --title "[Bug] ... / [Feature] ..." \
  --label "bug" / --label "enhancement" \
  --body-file - <<'EOF'
...
EOF
```

#### Concise English GitHub Issue Structure:

```markdown
**Mopheus Dev Ticket**: [MOC-<number>](https://dev.mopheus.ai/<workspace-slug>/tickets/<ticket-uuid>) (`<ticket-uuid>`)

## Description / Summary
[Concise description of the problem or feature]

## Steps to Reproduce / Motivation
- [Key step or motivation point 1]
- [Key step or motivation point 2]

## Expected vs Actual Behavior / Proposed Behavior
- **Expected / Proposed**: [What should happen]
- **Actual**: [What happens currently, if bug]

## Evidence / Screenshots
[Rendered S.EE Markdown image embeds if applicable]

## Acceptance Criteria
1. [Core capability requirement 1]
2. [Core capability requirement 2]
3. **Testing & QA Deliverables**:
   - Unit tests covering backend and frontend modules.
   - Integration tests in `tests/integration/`.
   - E2E Playwright tests in `tests/e2e/` for user-visible interactions.
```

> [!CAUTION]
> Double check that the Mopheus ticket URL uses `<ticket-uuid>` (36-character string), NOT the integer ID!
> Example of correct URL: `https://dev.mopheus.ai/dev-space/tickets/16c95e02-ba4b-4e86-a06b-0de4b8bb4c5a`
> Example of incorrect URL: `https://dev.mopheus.ai/dev-space/tickets/608` (DO NOT USE!)

---

### Step 4: Sync Structured GitHub Link & Project Affiliation

1. **Sync Structured Link (`git_issue`)**:
   ```bash
   mopheus <target-connection-args> --workspace-id <target-workspace-id> repo issue sync \
     --number <github-issue-number> \
     --repo https://github.com/enmotech/mopheus.git \
     --ticket <ticket-uuid> \
     --state <actual-issue-state> \
     --output json
   ```
2. **Auto-bind Project by Repository Name**:
   - Check ticket `projectId`. If unset:
   - Query projects: `mopheus <target-connection-args> --workspace-id <target-workspace-id> project list --output json`.
   - Find project matching `mopheus` (e.g. ID `31875816-a035-48dc-a296-740d03adc7bb`).
   - Update ticket:
     ```bash
     mopheus <target-connection-args> --workspace-id <target-workspace-id> ticket update <ticket-uuid> --project <project-id>
     ```

---

### Step 5: Verification and Reporting

Verify the created records:

```bash
gh-wrapper issue view <number> --repo enmotech/mopheus --json number,title,url,state,labels
mopheus <target-connection-args> --workspace-id <target-workspace-id> ticket get <ticket-uuid> --output json
mopheus <target-connection-args> --workspace-id <target-workspace-id> repo links --ticket <ticket-uuid> --output json
```

#### Final Response Format (in Chinese):

```markdown
已完成工单与 Issue 的创建与双向关联：

- **Mopheus 开发工单**：[#<number> (<title>)](https://dev.mopheus.ai/<workspace-slug>/tickets/<ticket-uuid>)
  - 工单 UUID: `<ticket-uuid>`
  - 所属工作区: `<workspace-name>` (`<target-workspace-id>`)
  - 绑定项目: `<project-name>` (`<project-id>`)
  - 优先级 / 状态: `High` / `Todo`
- **GitHub Issue**：[enmotech/mopheus#<number>](<github-issue-url>)
- **关联状态**：已建立双向 `git_issue` 结构化元数据绑定，并在 GitHub Issue 中包含了工单 UUID 直达链接。
```
