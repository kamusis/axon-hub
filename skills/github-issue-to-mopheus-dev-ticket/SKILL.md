---
name: github-issue-to-mopheus-dev-ticket
description: "Create a complete, detailed Chinese Mopheus dev ticket as the primary implementation entry and a paired concise English GitHub issue in the current repository's remote GitHub repository. Ensures the GitHub issue links to the Mopheus ticket using the full Ticket UUID. Strictly enforces single authoritative implementation design with zero ambiguity (strictly banning '或'/or/alternatives in design specifications), pre-creation user clarification for open design choices, and post-creation ambiguity verification."
---

# GitHub Issue to Mopheus Dev Ticket

This skill bridges user requests, bug reports, and feature specifications between the **Mopheus Dev Workspace** and the **current local Git repository's remote GitHub repository**.

## Core Philosophy & Weighting

- **Universal & Repository-Aware**: Automatically resolves the target GitHub repository from the current working directory's Git remote origin (`<owner>/<repo>`), and auto-associates the Mopheus ticket with the matching repository project.
- **Mopheus Dev Ticket (Primary & Authoritative)**: The Mopheus dev ticket is the **primary, authoritative internal implementation specification**. It must be written in **clear, natural, professional written Chinese** (avoiding awkward translationese, bureaucratic jargon, stacked pre-modifiers, and colloquial slang), covering the background, exact code locations/root cause, concrete changes, and acceptance criteria.
- **GitHub Issue (Concise & Linked)**: The GitHub issue is the **external tracking issue** written in **concise English**. It must capture the core summary, proposed change, and acceptance criteria, and **MUST include a direct link to the Mopheus Dev Ticket using the Ticket UUID**.
- **Writing Style & Scope Discipline (行文风格与按需裁剪规范)**:
  - **自然专业的工程书面语**: 用清晰、简练的中文工程书面语编写工单。严禁机器翻译腔、公文套话和多重前置定语堆叠（例如：写“使用 `tokenAlphabet` 构造的 Base64 编码器”，不写“由 `tokenAlphabet` 构造的无填充严格编码器”）；同时保持正式规范，不使用俚语口语（如“挂了”）。
  - **按需裁剪章节 (Omit Untouched Layers)**: 只写本次改动实际涉及的模块。如果不涉及 CLI、前端 UI、数据库迁移或 E2E 测试，**直接省略对应小节**，严禁保留空章节或编写免责套话段落去解释“为什么不改前端 / 为什么不写 E2E”。
- **Zero Ambiguity & Single Authoritative Design (严格禁止模棱两可与方案二选一)**:
  - **方案必须绝对唯一 (Single Concrete Design)**: 工单是具体的工程执行契约与验收基准，不是发散性设计讨论稿。每一个涉及架构设计、CLI 命令/参数名、HTTP API 契约、数据模型字段、状态流转逻辑、默认行为的环节，必须且只能给出**唯一确定**的实现方案。
  - **严禁模棱两可词汇 (Strict Ban on Ambiguous Phrasing)**: 工单正文严禁出现“方案 A 或 方案 B”、“可采用 X 或者 Y”、“使用 A 或 B”、“亦可考虑”、“也可以选择”、“备选方案”、“两种方式”等让实现者二次做选择题的推诿或未决措辞。
  - **不确定时前置追问，决策闭环 (Clarify Before Creation)**: 如果在分析过程中发现存在多种可行技术路线或权衡点（Trade-offs），且无法 100% 确定哪种更合适，**必须在生成工单前立即停止，并向用户提出明确追问**。待用户决策闭环并锁定唯一方案后，方可创建工单。绝对不可将“二选一/多选一”的未决设计直接写入工单或 Issue！

> [!IMPORTANT]
> **Ticket Link URL Rule (Mandatory Ticket UUID)**:
> The Mopheus ticket URL in the GitHub issue **MUST always use the 36-character Ticket UUID** (e.g. `https://dev.mopheus.ai/dev-space/tickets/16c95e02-ba4b-4e86-a06b-0de4b8bb4c5a`), **NOT** the short sequential integer number (e.g. NOT `/tickets/608` or `/tickets/#608`). The Mopheus Web UI router is keyed directly on the Ticket UUID; using an integer ID will cause the URL to fail to open or result in a 404 error.

---

## Supported Modes

1. **New-report mode (Default)**:
   - Detect current repository's remote origin and project name.
   - Create the comprehensive Chinese Mopheus ticket first to acquire the new **Ticket UUID** and number, associating it with the matching repository project.
   - Create the paired concise English GitHub issue in the target repository containing the Mopheus ticket UUID link.
   - Link the GitHub issue to the Mopheus ticket via `mopheus repo issue sync`.
2. **Existing-Ticket mode**:
   - When invoked within the context of an existing Mopheus ticket (e.g. agent task running under a ticket, or a ticket ID is provided), do NOT create a new child or separate ticket.
   - Do NOT overwrite the original ticket description (preserving history/audit trail).
   - Create the concise English GitHub issue containing the existing Mopheus ticket UUID link (`https://dev.mopheus.ai/<workspace-slug>/tickets/<ticket-uuid>`).
   - Post a structured Chinese reply comment on the existing ticket with the GitHub issue link and technical design/acceptance criteria.
   - Link the ticket to the GitHub issue via `mopheus repo issue sync` and verify project binding.
3. **Existing-Issue mode**:
   - Verify the supplied GitHub issue in the target repository and confirm it has no linked Mopheus ticket.
   - Create the comprehensive Chinese Mopheus ticket first, bound to the matching repository project.
   - Update the existing GitHub issue body (or post a comment) with the newly created Mopheus ticket UUID link.
   - Link the ticket to the GitHub issue via `mopheus repo issue sync`.

---

## Target Resolution: GitHub Repository & Mopheus Workspace

### 1. Resolve Target GitHub Repository (Dynamic)

Always resolve the target repository from the current Git directory:

1. Inspect remote origin:
   ```bash
   git remote get-url origin
   ```
2. Parse `<owner>/<repo>`:
   - SSH format (e.g. `git@github.com:enmotech/swissql-core.git`) -> `enmotech/swissql-core`
   - HTTPS format (e.g. `https://github.com/enmotech/swissql-core.git`) -> `enmotech/swissql-core`
3. Define variables:
   - `<target-github-repo>`: `<owner>/<repo>` (e.g. `enmotech/swissql-core`, `enmotech/mopheus`)
   - `<repo-name>`: `<repo>` (e.g. `swissql-core`, `mopheus`)
   - `<canonical-repo-url>`: `https://github.com/<owner>/<repo>.git`
4. **GitHub CLI**: use `gh-wrapper` when it is available in PATH; otherwise use `gh` directly.

### 2. Resolve Mopheus Target & Workspace

Require the host-installed `mopheus` executable from PATH in all modes. Never use `mop`, `go run ./cmd/mopheus`, `make mopheus`, a repository/worktree binary, or a temporary build.

#### Internal Mopheus-agent mode
Use this mode only when authoritative task/runtime context identifies the caller as a Mopheus agent task and supplies that task's workspace ID:
1. Read the task workspace ID from the trusted Mopheus task context.
2. Query workspace slug: `mopheus workspace get <task-workspace-id> --output json`.
3. Set `<target-workspace-id>` to `<task-workspace-id>`, `<target-workspace-slug>` to returned slug, and `<target-connection-args>` to runtime profile args.

#### External caller mode
Use this mode for Codex, Claude, Antigravity, or any invocation without trustworthy Mopheus task workspace context:
- Server URL: `https://dev.mopheus.ai`
- Profile: `default`
- Workspace Name: `dev`
- Workspace Slug: `dev-space`
- Workspace ID: `a43acd83-25f4-43ea-bdfd-d179fb272172`
- Command arguments: `--profile default --workspace-id a43acd83-25f4-43ea-bdfd-d179fb272172`

### 3. Auto-Resolve Project by Repository Name

In the target workspace, automatically find the project that corresponds to `<repo-name>`:
```bash
mopheus <target-connection-args> --workspace-id <target-workspace-id> project list --output json
```
Find the project where `name` equals `<repo-name>` (e.g. `swissql-core`, `mopheus`, `mes-cli`).
Capture `<project-id>`. If found, associate tickets with this project.

---

## Workflow Steps

### Step 0: Select the Mode

- **Existing-Ticket mode:** Check whether running under an existing Mopheus ticket.
  - Verify ticket: `mopheus <target-connection-args> --workspace-id <target-workspace-id> ticket get <ticket-id> --output json`.
  - Check existing links: `mopheus <target-connection-args> --workspace-id <target-workspace-id> repo links --ticket <ticket-id> --output json`.
  - If already linked, return existing records and stop.
  - If unlinked, proceed to Step 1 (extract evidence & ensure zero-ambiguity closure), Step 3 (create concise GitHub issue with ticket UUID URL), post structured Chinese reply comment on existing ticket with single concrete design, Step 4 (sync link & project binding), Step 5 (ambiguity audit), and Step 6 (reporting).
- **Existing-Issue mode:** Check if user supplies an existing GitHub issue URL or number.
  - Verify issue: `gh issue view <number> --repo <target-github-repo>`.
  - Check existing links: `mopheus <target-connection-args> --workspace-id <target-workspace-id> repo links --repo <canonical-repo-url> --type git_issue --number <n> --output json`.
  - If already linked, return and reuse it.
  - If unlinked, proceed to Step 1, Step 2 (create detailed Chinese ticket with single concrete design), Step 3 (update existing GitHub issue with ticket UUID URL), Step 4 (sync link & project binding), Step 5 (ambiguity audit), and Step 6 (reporting).
- **New-report mode:** Follow Steps 1 through 6.

---

### Step 1: Resolve Report Scope & Extract Evidence

- Extract exact reproduction steps, expected vs actual behavior, error messages, logs, IDs, and root cause analysis.
- If relevant screenshots are present in the conversation, upload them using the S.EE uploader skill/script to obtain public Markdown image URLs.
- Categorize as `bug` or `feature`.
- **Pre-Creation Design Decision Closure (方案决策闭环与零模棱两可自检)**:
  - 梳理拟定的技术实现方案。
  - 自查方案是否存在任何二选一、分支备选或不确定性设计（例如“可通过配置项或环境变量控制”、“方案 A 或 方案 B”、“返回格式 A 或 B”）。
  - **红线拦截门禁**: 若存在未决定的实现选项，**坚决不可假定或把选择题留进工单，必须立即停止创建流程，向用户明确提出追问**，待用户决策确认唯一方案后，方可继续推进。

---

### Step 2: Create the Detailed Chinese Mopheus Dev Ticket (Primary Entry)

In **New-report mode** (or Existing-Issue mode), create the **detailed Chinese Mopheus ticket first** so its UUID can be embedded into the GitHub issue:

```bash
mopheus <target-connection-args> --workspace-id <target-workspace-id> ticket create \
  --title "<清晰明确的中文标题>" \
  --priority high \
  --status todo \
  --project "<project-id>" \
  --description-stdin <<'EOF'
...
EOF
```

> [!CAUTION]
> **方案唯一性与零模棱两可红线 (Zero Ambiguity & Single Implementation Standard)**:
> - **严禁二选一措辞**: 技术方案中严禁出现“或”、“或者”、“亦可”、“也可考虑”、“方案 A 或 方案 B”等模棱两可的二选一措辞。
> - **必须提供唯一落地定义**: 所有的 CLI 命令名、参数名、返回值类型、HTTP Handler 路由、数据表字段名、类型定义、状态机转移逻辑，必须且只能给出**唯一确定的生产落地规范**。
> - **严禁推诿与猜测**: 绝不允许写出“可通过参数 --foo 或 --bar 控制”、“采用方案1或方案2”这类让下游实现者猜测的不确定设计。
> - 遇到任何未决设计，必须先追问用户决策闭环，严禁带入工单！

#### Chinese Ticket Structure:

按如下结构组织，仅保留本次改动实际触及的模块（非 Bug 工单直接省略“复现步骤与环境”；未涉及 CLI、前端或 E2E 时直接省略对应子项，严禁保留空章节或免责说明）：

```markdown
## 背景
[简明说明业务背景、问题现象或需求目标，1~2 段话讲清为什么要做]

## 复现步骤与环境（针对 Bug，非 Bug 省略本节）
1. [步骤 1]
2. [步骤 2]
- **环境信息**: [OS / 浏览器 / 数据库 / 组件版本]

## 验证证据与根因分析
- **现象截图 / 日志**: [嵌入 S.EE 截图链接或关键报错日志，无截图/日志时省略]
- **根因 / 问题位置**: [直接指明涉及的代码文件、行号、函数/结构体及具体原因]

## 修改方案
[按实际涉及的模块列出唯一确定的改法（不涉及的模块直接省略）：]
- **后端 / 数据模型**: [涉及的 struct、service、repo、migration 变更]
- **CLI**: [涉及的命令、flag 与输出格式]
- **前端 UI**: [涉及的组件、状态与交互]

## 验收标准
1. [具体功能或修复结果断言 1（确定性描述，无“或”选项）]
2. [具体功能或修复结果断言 2]
3. **测试验证**: [列出需要通过的具体单测包、E2E 用例或 `make check` 命令]
```

> **Note**: Capture the created `ticket.id` (UUID, e.g. `b2fa14d4-784b-46fa-b162-9c1517211317`) and `ticket.number` (e.g. `733`).

---

### Step 3: Create or Update the Concise English GitHub Issue

Create the GitHub issue in `<target-github-repo>`. The GitHub issue must stay **concise** (avoid repeating lengthy line-by-line code dumps), focusing on the background, proposed change, and acceptance criteria, and **MUST contain the Mopheus Dev Ticket link with the Ticket UUID**.

> [!IMPORTANT]
> The GitHub issue must strictly adhere to the **Zero Ambiguity & Single Concrete Design** rule: never specify alternative or undecided implementations (e.g. avoid "either X or Y", "option A or option B"). State only the single decided behavior and acceptance criteria.

```bash
gh issue create --repo <target-github-repo> \
  --title "[Bug] ... / [Feature] ..." \
  --label "bug" / --label "enhancement" \
  --body-file - <<'EOF'
...
EOF
```

#### Concise English GitHub Issue Structure:

```markdown
**Mopheus Dev Ticket**: [MOC-<number>](https://dev.mopheus.ai/<workspace-slug>/tickets/<ticket-uuid>) (`<ticket-uuid>`)

## Background
[Concise description of the problem, reproduction steps, or motivation]

## Proposed Change
- [Concrete change 1 with target file/module]
- [Concrete change 2 with target file/module]

## Acceptance Criteria
1. [Core requirement 1]
2. [Core requirement 2]
3. [Specific unit/integration/E2E verification commands that must pass]
```

> [!CAUTION]
> Double check that the Mopheus ticket URL uses `<ticket-uuid>` (36-character string), NOT the integer ID!
> Example of correct URL: `https://dev.mopheus.ai/dev-space/tickets/b2fa14d4-784b-46fa-b162-9c1517211317`
> Example of incorrect URL: `https://dev.mopheus.ai/dev-space/tickets/733` (DO NOT USE!)

---

### Step 4: Sync Structured GitHub Link & Project Affiliation

1. **Sync Structured Link (`git_issue`)**:
   ```bash
   mopheus <target-connection-args> --workspace-id <target-workspace-id> repo issue sync \
     --number <github-issue-number> \
     --repo <canonical-repo-url> \
     --ticket <ticket-uuid> \
     --state <actual-issue-state> \
     --output json
   ```
2. **Auto-bind Project by Repository Name**:
   - Check ticket `projectId`. If unset:
   - Query projects: `mopheus <target-connection-args> --workspace-id <target-workspace-id> project list --output json`.
   - Find project matching `<repo-name>`.
   - Update ticket:
     ```bash
     mopheus <target-connection-args> --workspace-id <target-workspace-id> ticket update <ticket-uuid> --project <project-id>
     ```

---

### Step 5: Post-Creation Ambiguity Verification & Audit (工单回览与零模棱两可终审门禁)

在工单与 Issue 创建及同步完成后，**必须立即执行回览自检（Review & Audit）**，严格确保落盘内容零模棱两可：

1. **回览工单正文与 Issue 内容**:
   ```bash
   mopheus <target-connection-args> --workspace-id <target-workspace-id> ticket get <ticket-uuid> --output json
   gh issue view <number> --repo <target-github-repo>
   ```
2. **执行模棱两可关键词自检 (Ambiguity Keyword Scan)**:
   - 逐段自检工单的“修改方案”与“验收标准”，排查是否存在以下词汇及其语境：
     - 中文关键词：`或`、`或者`、`亦可`、`也可以`、`备选`、`候选方案`、`两种方式`、`可采用...也可采用...`
     - 英文关键词：`or `、`either `、`optionally `、`alternative `
   - 严禁把方案选择权、二选一决策推诿给后续的实现者。
3. **发现模棱两可的处理流程 (Remediation)**:
   - 若发现上述词汇用于二选一未决设计（例如“使用 A 或 B”）：
     - **若属于措辞不够确定但方案已收敛**：**立即调用 `mopheus ticket update <ticket-uuid>` 重新更新工单正文**，消除模糊词汇，牢牢锁定唯一实现方案。
     - **若属于尚未决定的设计分歧/权衡点**：**立刻停止流程，向用户发出明确追问**，获得用户决策指令后，再行更新工单至唯一确定的方案。

---

### Step 6: Final Verification and Reporting

Verify the created records:

```bash
gh issue view <number> --repo <target-github-repo> --json number,title,url,state,labels
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
  - 方案设计审计: 已完成回览自检，设计方案唯一确定，无任何“或”等模棱两可二选一描述
- **GitHub Issue**：[<target-github-repo>#<number>](<github-issue-url>)
- **关联状态**：已建立双向 `git_issue` 结构化元数据绑定，并在 GitHub Issue 中包含了工单 UUID 直达链接。
```
