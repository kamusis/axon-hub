---
name: github-issue-to-mopheus-dev-ticket
description: "Create a Chinese Mopheus dev ticket that states confirmed user requirements, concrete scenarios, and observable acceptance criteria, plus a concise linked English GitHub issue in the current repository. Use when converting a user request, bug report, or existing GitHub issue into linked implementation work."
---

# GitHub Issue to Mopheus Dev Ticket

This skill bridges user requests, bug reports, and feature specifications between the **Mopheus Dev Workspace** and the **current local Git repository's remote GitHub repository**.

## Core Philosophy & Weighting

- **Universal & Repository-Aware**: Automatically resolves the target GitHub repository from the current working directory's Git remote origin (`<owner>/<repo>`), and auto-associates the Mopheus ticket with the matching repository project.
- **Mopheus Dev Ticket (Primary & Authoritative)**: The Mopheus dev ticket is the **primary, authoritative internal implementation specification**. It must be written in **clear, natural, professional written Chinese**. Put the user need and concrete scenario first; keep background to only the context needed to understand them. Include code locations/root cause only when verified, then state concrete changes and acceptance criteria.
- **GitHub Issue (Concise & Linked)**: The GitHub issue is the **external tracking issue** written in **concise English**. It must capture the core summary, proposed change, and acceptance criteria, and **MUST include a direct link to the Mopheus Dev Ticket using the Ticket UUID**.
- **Writing Style & Scope Discipline (行文风格与按需裁剪规范)**:
  - **人机兼顾的工程设计表达 (Human-Friendly Architecture & Agent-Precise Implementation)**: 工单既是 AI Agent 执行代码变更的严格契约，也是人类工程师与审查者理解系统演进的核心载体。严禁仅机械罗列干瘪的代码行级指令。在具体的模块改动前，必须包含《方案设计与机理推导》章节，通过清晰直观的心智模型、ASCII 拓扑/时序图解、物理机制阐述以及改造前后对比表，将“为什么从底层能根治”、“各层系统如何受力”以及“故障与防护边界如何改变”阐述透彻，使人类与 AI 均能建立完整、统一的架构心智。
  - **自然专业的工程书面语**: 用清晰、简练的中文工程书面语编写工单。严禁机器翻译腔、公文套话和多重前置定语堆叠（例如：写“使用 `tokenAlphabet` 构造的 Base64 编码器”，不写“由 `tokenAlphabet` 构造的无填充严格编码器”）；同时保持正式规范，不使用俚语口语（如“挂了”）。
  - **按需裁剪章节 (Omit Untouched Layers)**: 只写本次改动实际涉及的模块。如果不涉及 CLI、前端 UI、数据库迁移或 E2E 测试，**直接省略对应小节**，严禁保留空章节或编写免责套话段落去解释“为什么不改前端 / 为什么不写 E2E”。
  - **需求优先，背景从简 (Need Before Context)**: 工单首先回答“谁在什么场景下要完成什么事”或“用户做了什么、实际发生什么、预期是什么”。背景最多用 1 段或 3 个要点，只保留理解需求所必需的业务上下文；不复述项目介绍、问题分析过程、已有功能清单或用户原话中的铺垫。删掉不改变需求理解、实现边界或验收判断的信息。
  - **事实与推断分开 (Facts Before Assumptions)**: 不得用概括性背景代替需求。只记录输入、代码、日志或复现证据能够支持的事实；未知项明确标为待确认，不臆造用户、流程、影响范围、根因、代码位置或验收结果。若缺少的信息会改变需求范围或验收方式，创建前向用户追问；若不影响实现契约，则省略。
- **Zero Ambiguity & Single Authoritative Design (严格禁止模棱两可与方案二选一)**:
  - **方案必须绝对唯一 (Single Concrete Design)**: 工单是具体的工程执行契约与验收基准，不是发散性设计讨论稿。每一个涉及架构设计、CLI 命令/参数名、HTTP API 契约、数据模型字段、状态流转逻辑、默认行为的环节，必须且只能给出**唯一确定**的实现方案。
  - **严禁模棱两可词汇 (Strict Ban on Ambiguous Phrasing)**: 工单正文严禁出现“方案 A 或 方案 B”、“可采用 X 或者 Y”、“使用 A 或 B”、“亦可考虑”、“也可以选择”、“备选方案”、“两种方式”等让实现者二次做选择题的推诿或未决措辞。
  - **不确定时前置追问，决策闭环 (Clarify Before Creation)**: 如果实现路线会改变用户可见行为、兼容性、数据保留或验收边界，且请求、现有代码和仓库约定无法确定应采用的路线，**必须在生成工单前向用户追问并锁定行为契约**。若差异仅是内部实现细节，依据现有架构和代码约定选定一条路线，不把技术选择题交给用户。工单和 Issue 不得留下未决设计。

> [!IMPORTANT]
> **Ticket Link URL Rule (Mandatory Ticket UUID)**:
> The Mopheus ticket URL in the GitHub issue **MUST always use the 36-character Ticket UUID** (e.g. `https://dev.mopheus.ai/dev-space/tickets/16c95e02-ba4b-4e86-a06b-0de4b8bb4c5a`), **NOT** the short sequential integer number (e.g. NOT `/tickets/608` or `/tickets/#608`). The Mopheus Web UI router is keyed directly on the Ticket UUID; using an integer ID will cause the URL to fail to open or result in a 404 error.

---

## Supported Modes

1. **New-report mode (Default)**:
   - Detect current repository's remote origin and project name.
   - Create the Chinese Mopheus ticket from the confirmed requirements to acquire the new **Ticket UUID** and number, associating it with the matching repository project.
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
   - Create the Chinese Mopheus ticket from confirmed requirements, bound to the matching repository project.
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

Require a formally installed host Mopheus CLI binary (`mopheus` or its standard installed alias `mop`) in all modes. Never execute unreleased or local development builds (`go run ./cmd/mopheus`, `make mopheus`, `make cli`, `./server/bin/mopheus`, any binary inside a repository checkout or `.worktrees/` directory, or a temporary build).

Before running Mopheus commands, probe via a login shell when needed (non-login tool shells may omit `~/.local/bin` from `PATH`) and verify the resolved target path (`readlink -f`):
- Run `bash -lc 'command -v mopheus || command -v mop'` and check `readlink -f` on the candidate.
- The resolved path must point to a standard host installation location (such as `~/.local/bin/mopheus` or `/usr/local/bin/mopheus`), not inside any Git checkout or worktree.
- If the first `mopheus`/`mop` on `PATH` symlinks to a repository or worktree binary (such as a preview worktree), invoke the host-installed binary directly by path (e.g. `~/.local/bin/mopheus`) or stop and report the conflict—never fall back to the development build.

#### Internal Mopheus-agent mode
Use this mode only when authoritative task/runtime context identifies the caller as a Mopheus agent task and supplies that task's workspace ID:
1. Read the task workspace ID from the trusted Mopheus task context.
2. Query workspace slug: `mopheus workspace get <task-workspace-id> --output json`.
3. Set `<target-workspace-id>` to `<task-workspace-id>`, `<target-workspace-slug>` to returned slug, and `<target-connection-args>` to runtime profile args.

#### External caller mode
Use this mode for Codex, Claude, Antigravity, or any invocation without trustworthy Mopheus task workspace context:
- Server URL: `https://dev.mopheus.ai`
- **Resolve the formal dev profile (`<dev-profile>`)**:
  1. **Check `MOPHEUS_DEV_PROFILE`**: If `MOPHEUS_DEV_PROFILE` environment variable is set (e.g. `export MOPHEUS_DEV_PROFILE=dev`), use its value as `<dev-profile>`.
  2. **Dynamic URL probe**: If `MOPHEUS_DEV_PROFILE` is unset, run `mopheus profile list -o json` (or `mop profile list -o json`) and filter profiles matching `serverUrl == "https://dev.mopheus.ai"`:
     - Prioritize profiles with `hasToken: true`.
     - When multiple authenticated profiles match, prioritize exact `dev` > name containing `dev` (e.g. `mop-dev`) > `default` > first matching profile.
     - If all matching profiles have `hasToken: false`, pick the best candidate (e.g. `dev` or `default`) and instruct the user to run `mopheus --profile <name> login`.
     - If no profile points to `https://dev.mopheus.ai`, **do NOT overwrite the user's `default` profile**. Prompt the user to configure one:
       ```bash
       export MOPHEUS_DEV_PROFILE=dev
       mopheus profile create dev --server_url https://dev.mopheus.ai
       mopheus --profile dev login
       ```
  3. **Verify authentication**: Run `mopheus --profile <dev-profile> auth status` to ensure valid token status.
- Target connection arguments: `<target-connection-args>` = `--profile <dev-profile>`
- Workspace Name: `dev`
- Workspace Slug: `dev-space`
- Workspace ID: `a43acd83-25f4-43ea-bdfd-d179fb272172`
- Command arguments: `<target-connection-args> --workspace-id a43acd83-25f4-43ea-bdfd-d179fb272172`

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

- First turn the request into a compact requirement statement:
  - **Feature**: identify the target user, triggering scenario/task, current pain or behavior, requested capability/action, observable expected outcome, and any stated scope boundary. State user-visible behavior and constraints; do not replace these with a broad goal such as “improve efficiency” or “enhance experience.”
  - **Bug**: identify the actor/context, exact steps, actual result, expected result, and evidence. Preserve relevant error text, logs, IDs, and environment details.
- Separate confirmed facts from hypotheses. Verify code locations and root cause against the repository before stating them; when not established, omit the root-cause claim and describe the observed behavior instead.
- Keep only details that clarify the need, scenario, implementation boundary, or acceptance check. Do not pad the ticket with generic product background, repeated summaries, investigation narration, or speculative impact.
- If a feature's user, trigger, pain, or expected outcome is missing and cannot be inferred safely, ask only focused questions about missing product requirements that would change scope or acceptance. Bundle related questions concisely; do not turn clarification into a broad questionnaire. Do not ask the user to choose among technical approaches that can be resolved from repository evidence. Ask about a technical trade-off only when it materially changes the user-visible contract and repository evidence does not determine the choice. Do not create records while a requirement that changes scope or acceptance remains unknown.
- Do not invent a root cause, code location, implementation detail, or test command to make the ticket look complete. Include verified engineering details when useful; otherwise describe the required behavior and leave implementation analysis to the assignee.
- If relevant screenshots are present in the conversation, upload them using the S.EE uploader skill/script to obtain public Markdown image URLs.
- Categorize as `bug` or `feature`.
- **Pre-Creation Design Decision Closure (方案决策闭环与零模棱两可自检)**:
  - 梳理拟定的技术实现方案。
  - 自查方案是否存在任何二选一、分支备选或不确定性设计（例如“可通过配置项或环境变量控制”、“方案 A 或 方案 B”、“返回格式 A 或 B”）。
   - **红线拦截门禁**: 若存在会改变用户可见契约且无法从需求和仓库事实确定的未决选项，不得自行假定或把选择题留进工单；向用户澄清受影响的行为后再继续。内部实现细节按项目既有模式收敛，不因此中断需求澄清。

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
> - **必须提供唯一落地定义**: 工单涉及的 CLI 命令/参数、API 契约、数据模型和状态流转必须给出唯一确定的要求。内部实现细节遵循仓库既有模式；仅当其选择会改变用户可见契约且仓库事实无法确定时才向用户澄清。
> - **严禁推诿与猜测**: 绝不允许写出“可通过参数 --foo 或 --bar 控制”、“采用方案1或方案2”这类让下游实现者猜测的不确定设计。
> - 仅当未决选项会改变用户可见契约且无法从需求、代码和仓库约定确定时，先向用户澄清；内部实现选项由实现者依据既有模式收敛，严禁将未决选项带入工单。

#### Chinese Ticket Structure:

按如下结构组织，仅保留有事实内容且本次改动实际需要的章节（非 Bug 工单省略“复现步骤与环境”；未涉及 CLI、前端或 E2E 时省略对应子项，严禁保留空章节或免责说明）。工单以需求和可观察行为为主，背景简短；不要求为了显得“详细”而补齐无关背景、未验证根因或猜测的文件位置。Feature 的根因分析通常不适用，除非请求明确针对现有行为缺陷且根因已经验证：

```markdown
## 背景
[仅写理解需求必需的上下文，最多 1 段或 3 个要点；若无需额外背景则省略本节]

## 需求与场景
[Feature：谁在什么触发场景下需要完成什么操作/能力，系统应产生什么可观察结果及必要约束。Bug：用户在什么场景做了什么，实际结果与预期结果分别是什么。不得用抽象愿景代替具体行为]

## 复现步骤与环境（针对 Bug，非 Bug 省略本节）
1. [步骤 1]
2. [步骤 2]
- **环境信息**: [OS / 浏览器 / 数据库 / 组件版本]

## 验证证据与根因分析
- **现象截图 / 日志**: [嵌入 S.EE 截图链接或关键报错日志，无截图/日志时省略]
- **根因 / 问题位置**: [仅在已验证时指明代码文件、行号、函数/结构体及原因；未经验证时省略]

## 方案设计与机理推导（适合人类理解的架构剖析）
- **心智模型与机理图解**: [使用清晰直观的 ASCII 拓扑图、时序图或容器架构，可视化展示问题发生的传导路径与改造后防护边界]
- **核心设计论证**: [清晰阐明“为什么这样设计能从底层根除缺陷”，解释核心参数、内核机制或门禁策略的物理意义与推导逻辑]
- **改造前后对比**:
  | 机制 / 维度 | 改造前状态 | 改造后状态 |
  | --- | --- | --- |
  | [维度 1] | [现状问题与缺陷表现] | [解决后的预期效果与边界] |
  | [维度 2] | [现状问题与缺陷表现] | [解决后的预期效果与边界] |

## 修改方案
[按实际涉及的模块列出唯一确定的改法（不涉及的模块直接省略）：]
- **后端 / 数据模型**: [涉及的 struct、service、repo、migration 变更]
- **CLI**: [涉及的命令、flag 与输出格式]
- **前端 UI**: [涉及的组件、状态与交互]

## 验收标准
1. [从需求场景推导的可观察结果断言，给出触发条件和期望行为]
2. [必要的边界/失败行为；没有额外边界时删除此项]
3. **测试验证**: [仅列出由涉及模块和仓库测试布局确定的验证命令；无法确定时写应覆盖的测试层，不编造命令]
```

**质量门禁**: 阅读者应能仅凭“需求与场景”和“验收标准”判断本次要改变什么、如何证明完成。若只能看到背景/动机而无法说出触发场景和期望行为，先补充信息或向用户追问，不能直接创建。每个背景句都必须提供理解需求所需的信息；删除后不影响需求、范围或验收的句子一律删除。

**场景完整性检查**: Feature 至少写清目标用户、触发场景/任务、当前痛点、期望行为和可观察结果；用户未提供且不能从证据确认的关键项要先追问。用户没有提出的非目标不要自行扩写；若范围边界已明确，则用一句话记录。Bug 至少写清复现条件、实际结果和预期结果。技术方案的唯一性约束只针对已确认的实现契约，不得用它替代需求澄清或迫使用户替实现者做技术选择。

> **Note**: Capture the created `ticket.id` (UUID, e.g. `b2fa14d4-784b-46fa-b162-9c1517211317`) and `ticket.number` (e.g. `733`).

---

### Step 3: Create or Update the Concise English GitHub Issue

Create the GitHub issue in `<target-github-repo>`. The GitHub issue must stay **concise**, stating the concrete user need/scenario, the decided change, and observable acceptance criteria. Keep background to the minimum context needed; do not repeat investigation narration or copy the full ticket. It **MUST contain the Mopheus Dev Ticket link with the Ticket UUID**.

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
[One or two sentences of necessary context; omit if the scenario already makes the need clear]

## User Need / Scenario
[Who needs what in which situation, and what observable behavior is expected. For a bug, state actual versus expected behavior.]

## Proposed Change
- [Concrete behavior/change required by the ticket; name a file/module only when repository evidence confirms it]
- [Additional required behavior, if any]

## Acceptance Criteria
1. [Observable outcome tied to the stated scenario]
2. [Relevant boundary behavior, if any]
3. [Verification commands grounded in the affected code and repository test layout; if not yet known, state the test layer to cover without inventing a command]
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
