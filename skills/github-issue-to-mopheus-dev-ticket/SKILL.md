---
name: github-issue-to-mopheus-dev-ticket
description: "Create a complete Mopheus bug or feature report from the current conversation, or create only the missing Chinese Mopheus ticket for an already-existing enmotech/mopheus GitHub issue. Use when the user wants both an English GitHub issue and linked Mopheus ticket, or explicitly has a Mopheus GitHub issue but no corresponding Mopheus ticket. Always use the fixed enmotech/mopheus GitHub repository; target the task workspace for an internal Mopheus agent and otherwise fall back to the formal dev workspace; never duplicate an existing issue or ticket."
---

# GitHub Issue to Mopheus Dev Ticket

Support two modes:

1. **New-report mode:** create an English GitHub issue, then a linked Chinese Mopheus ticket.
2. **Existing-Issue mode:** verify a supplied GitHub issue, confirm it has no linked Mopheus ticket, then create and link only the ticket.

The GitHub issue is the canonical external report. The Mopheus ticket is the internal implementation entry and must link to the GitHub issue URL.

## Fixed GitHub target and external fallback

The GitHub target is always fixed. The Mopheus target depends on the caller:

- GitHub CLI: use `gh-wrapper` when it is available; otherwise use `gh`
- GitHub repository: `enmotech/mopheus`
- Canonical GitHub repository URL for Mopheus repo operations: `https://github.com/enmotech/mopheus.git`
- External fallback server: `https://dev.mopheus.ai`
- External fallback profile: `default`
- External fallback workspace name: `dev`
- External fallback workspace ID: `a43acd83-25f4-43ea-bdfd-d179fb272172`

The GitHub repository is fixed because this skill is specific to Mopheus. Do not derive or override it from the current directory, local Git remotes, active GitHub repository, Mopheus workspace, or prior conversation.

## Resolve the Mopheus target

Require the host-installed `mopheus` executable from PATH in both modes. Never use `mop`, `go run ./cmd/mopheus`, `make mopheus`, a repository/worktree binary, or a temporary build.

### Internal Mopheus-agent mode

Use this mode only when authoritative task/runtime context identifies the caller as a Mopheus agent task and supplies that task's workspace ID. The task workspace has highest priority and cannot be overridden by the user, active CLI workspace, fallback ID, or prior conversation.

1. Read the task workspace ID from the trusted Mopheus task context. A bare environment variable in an otherwise external session is not sufficient to classify the caller as internal.
2. Preserve the runtime-provided Mopheus server, authentication, and profile context. Do not run `connect`, repoint a profile, source `.env.worktree`, or replace runtime credentials.
3. Verify authentication, then run `mopheus workspace get <task-workspace-id> --output json` using the runtime connection.
4. Require the returned workspace ID to equal the task workspace ID. Stop on missing access, authentication failure, server ambiguity, or mismatch.
5. Pass `--workspace-id <task-workspace-id>` explicitly on every workspace-scoped command. Pass the runtime profile explicitly when the task context provides one.

Set `<target-workspace-id>` to the verified task workspace ID and `<target-connection-args>` to the runtime-provided profile arguments, or to no profile flag when the runtime connection is environment-backed.

### External caller mode

Use this mode for Codex, another external agent, or any invocation without trustworthy Mopheus task workspace context. Retain the formal fixed fallback:

1. Use only the `default` profile. Never use or repoint `local`, `wt-*`, or another preview/test profile.
2. Do not source `.env.worktree`. Remove `MOPHEUS_PROFILE`, `MOPHEUS_SERVER_URL`, `MOPHEUS_WORKSPACE_ID`, `MOPHEUS_TOKEN`, `MOPHEUS_AGENT_ID`, and `MOPHEUS_DAEMON_ID` preview overrides from the command environment.
3. Bind and verify the formal profile. Use `connect` when the installed version supports it:
   ```bash
   mopheus --profile default connect --server_url https://dev.mopheus.ai
   ```
   Current releases without `connect` must use:
   ```bash
   mopheus --profile default config set server-url https://dev.mopheus.ai
   ```
   Then run:
   ```bash
   mopheus --profile default config show --output json
   mopheus --profile default auth status
   ```
   Require the configured server URL to be exactly `https://dev.mopheus.ai`. Stop if the installed CLI is unavailable, connection/authentication fails, or the URL differs; never fall back to a preview profile.
4. Run `mopheus --profile default workspace get a43acd83-25f4-43ea-bdfd-d179fb272172 --output json` and require its name to be exactly `dev`.
5. Pass `--profile default` on every Mopheus command and `--workspace-id a43acd83-25f4-43ea-bdfd-d179fb272172` on every workspace-scoped command.

Set `<target-workspace-id>` to `a43acd83-25f4-43ea-bdfd-d179fb272172` and `<target-connection-args>` to `--profile default`.

After either mode resolves, use `<target-connection-args>` and `<target-workspace-id>` consistently for the entire workflow. Never switch modes or workspaces mid-run.

## Fixed GitHub repository

Use `--repo enmotech/mopheus` on every `gh-wrapper` or `gh` issue command, including lookup, duplicate detection, creation, and verification. Use `https://github.com/enmotech/mopheus.git` as the `--repo` value for every Mopheus repository-link command.

Do not inspect or depend on the current local Git repository. A caller may invoke this skill outside a checkout or from an unrelated checkout; that must not change the target. If the user supplies an issue URL from another repository, stop and report the repository mismatch instead of creating or linking a ticket.

Never select a workspace by name search, current active workspace, or a previous command. The internal task workspace ID or external fallback ID must always be explicit.

## Workflow

### 0. Select the mode

- Use **Existing-Issue mode** only when the user or calling skill supplies one unambiguous GitHub issue URL or number and states that its Mopheus ticket is missing.
- Verify the issue with `gh-wrapper issue view <number> --repo enmotech/mopheus`. Stop on a repository mismatch or missing issue.
- Query `mopheus <target-connection-args> --workspace-id <target-workspace-id> repo links --repo https://github.com/enmotech/mopheus.git --type git_issue --number <n> --output json`.
- If a linked ticket already exists, return and reuse it; do not create another ticket.
- In Existing-Issue mode, never run `gh issue create`. Treat the verified issue title, body, labels, state, URL, and relevant conversation evidence as the canonical report.
- Otherwise use **New-report mode** and retain the issue-first workflow below.

### 1. Resolve the report scope

Before extracting evidence or performing any external write, determine which single bug or feature the user wants to turn into records.

- Treat the user's latest explicit scope, named topic, issue, PR, job, task ID, or screenshot context as authoritative.
- Use earlier conversation content only when it directly supports that selected scope.
- Do not merge independent bugs or features into one GitHub issue or one Mopheus ticket.
- If the conversation contains multiple independent candidate topics and the user's instruction does not identify one, stop and ask which topic to process. Do not run `gh issue create`, `mopheus ticket create`, or `mopheus repo issue sync` while the scope is ambiguous.
- If the user explicitly requests separate records for multiple topics, process each topic independently, creating one GitHub issue and one linked Mopheus ticket per topic.

For example, a conversation that contains both a coverage-job failure and an RBAC authorization bug requires a scope clarification unless the user names one of them.

### 2. Extract and verify evidence

Read the full conversation context and collect:

- User action sequence and exact reproduction steps.
- Expected and actual behavior.
- Error messages, IDs, logs, API responses, and relevant environment details.
- Root cause analysis supported by repository code or live read-only checks.
- Workarounds and their side effects.
- Attached screenshots or files, when present.

Do not invent missing evidence. If the cause is uncertain, describe it as a hypothesis and do not present it as confirmed.

Classify the report as `bug` or `feature` from the user's request. For a bug, include reproduction, expected behavior, actual behavior, root cause, workaround, and acceptance criteria. For a feature, include objective, motivation, definitive behavior, acceptance criteria, and dependencies.

### 3. Prepare screenshots

In New-report mode, if the conversation includes screenshots relevant to the report, the GitHub issue body must contain the screenshots as rendered Markdown images. Do not merely mention that screenshots exist or leave them as local file paths. Existing-Issue mode does not rewrite the issue solely to rehost old evidence.

- Use the provided absolute attachment paths.
- Use the S.EE uploader skill/script to obtain public Markdown image links, then place every relevant image link directly in the GitHub issue body under `## Evidence` or `## Screenshots`.
- Preserve the order and explain what each screenshot demonstrates.
- Do not upload credentials, tokens, private keys, or unrelated sensitive data. If a screenshot contains secrets, omit it and describe the evidence in text.

In New-report mode, if screenshot upload or safe hosting is unavailable, stop before creating the GitHub issue and report the blocker. A new report with available screenshots must not be created without embedding those screenshots.

### 4. Create or verify the GitHub issue

In Existing-Issue mode, skip creation and use the issue verified in Step 0. Preserve its exact URL and current state for ticket creation and structured linking.

In New-report mode, create the issue first:

Use the GitHub issue workflow and write all GitHub content in English. Use a clear title under 72 characters, normally with `[Bug]` or `[Feature]`.

For a bug, use this structure:

```markdown
## Description
## Steps to Reproduce
## Expected Behavior
## Actual Behavior
## Environment
## Evidence
## Root Cause
## Workaround
## Required Fix
## Acceptance Criteria
## Additional Context
```

For a feature, use this structure:

```markdown
## Summary
## Motivation
## Proposed Behavior
## Acceptance Criteria
## Dependencies
## Additional Context
```

### Requirement Clarity Rules

When creating an issue, write requirements and design decisions as a single settled, definitive specification. Do not leave ambiguity or open choices for the later implementer.

- Do not use vague wording that gives the implementer multiple choices, such as "suggest", "maybe", "could", "consider", "if possible", "preferably", "one option is", "A or B", "either", "or", "and/or", "etc.", or "whatever works".
- Do not describe several possible implementations or flag names and ask the implementer to choose (e.g. avoid "Support --clear-runtime or --unbind-runtime"; choose one definitive flag like "Support --clear-runtime").
- Do not write acceptance criteria that allow multiple interpretations.
- Convert user-approved decisions into definitive wording: "Do X", "Use Y", "Save is disabled when Z", "Show message M".
- If the user has not made a required product, UX, validation, data-model, or technical decision, stop before creating the issue and ask a direct clarification question.
- If the user asks for brainstorming or evaluation rather than issue creation, keep options in the conversation. Only create the issue after the final decision is unique and explicit.
- Use an "Alternatives Considered" section only to record rejected approaches. Each rejected approach must clearly say it is not part of the implementation.

### CLI-First Architecture Principle (CLI 优先设计原则)

When designing and specifying requirements for new features or capabilities:

- **CLI First (CLI 优先)**: All features and capabilities MUST be designed and implemented with CLI support first.
- **Unified API Contract (统一 API 契约)**: The Web UI and CLI must invoke the same underlying backend REST/GraphQL/HTTP APIs and data models. Never create UI-only backend endpoints or bifurcated execution paths.
- **Exceptions (唯一例外)**: The only exceptions are requirements that are purely Web UI interactive behaviors (e.g. drag-and-drop animation, responsive layouts, rich text editor styling) or capabilities inherently unsuitable for a command-line interface.
- **Explicit Scope in Tickets & Issues**: Both the English GitHub issue and Chinese Mopheus dev ticket must explicitly specify the CLI command interface (flags, subcommands, inputs, and outputs) in the technical design and acceptance criteria, unless explicitly exempt under the rule above.

### Mandatory Comprehensive Test Deliverables in Acceptance Criteria (验收标准必须包含全层级测试要求)

Every created GitHub Issue and Mopheus Dev Ticket **MUST explicitly specify and enumerate test deliverables across all applicable testing tiers** in the `## Acceptance Criteria` (验收标准) section. Never write a vague "add tests" bullet point.

The `Acceptance Criteria` must explicitly break down test requirements into:

1. **Unit Tests (单元测试)**:
   - Backend: models, repo queries/cascades, service logic/permissions/error codes, HTTP handlers/validation, CLI flags/subcommands parsing and execution.
   - Frontend: Zod schemas, React query hooks/mutations, Zustand stores, UI component states and interactions.
2. **Integration Tests (集成测试)**:
   - Specification: update/create scenario markdown specifications in `tests/integration/` (e.g., `03-cli-core-lifecycle.md`, `04-comments-and-pins-advanced.md`, `14-daemon-lifecycle-and-tasks.md`) to document new CLI commands, flags, API routes, cross-resource side effects, and boundary rejection rules.
   - Automation: update/create automated shell test scripts under `tests/integration/scripts/` (e.g. `it-test-stage2-group03-cli.sh`, `it-test-stage3-groups-04-15-api.sh`) to assert positive workflows and boundary rejection.
3. **E2E / Playwright Tests (端到端/Playwright 测试)**:
   - For all user-visible capabilities, interactive UI behaviors, new pages, dialogs, or dropdown actions, explicitly specify creating/updating Playwright specs in `tests/e2e/*.spec.ts` covering browser-driven user journeys, UI component visibility, form submissions, and real-time state updates.

Example of mandatory Acceptance Criteria test section:
```markdown
## Acceptance Criteria
1. Feature requirement 1...
2. Feature requirement 2...
...
N. Testing & Quality Assurance Deliverables:
   - **Unit Tests**: Full unit test coverage across repo, service, HTTP, CLI, and web hooks/components.
   - **Integration Tests**: Update `tests/integration/<group>.md` specification and `tests/integration/scripts/<script>.sh` runner script with new CLI/API regression tests.
   - **E2E Tests**: Add/update Playwright specs in `tests/e2e/<feature>.spec.ts` covering browser user flow and interactive behaviors.
```

Create the issue in `enmotech/mopheus` by passing `--repo enmotech/mopheus`, with the `bug` label for bugs and `enhancement` for features. Add other existing repository labels only when supported by the evidence. Capture and verify the returned GitHub issue URL before continuing.

Do not create the Mopheus ticket if GitHub issue creation fails or no issue URL is returned.

### 5. Create the Chinese Mopheus ticket

After GitHub creation or existing-Issue verification succeeds, create the internal ticket in the resolved target workspace:

```bash
mopheus <target-connection-args> --workspace-id <target-workspace-id> ticket create \
  --title "<Chinese title>" \
  --priority high \
  --status todo \
  --description-stdin
```

Write the ticket in Chinese. Include:

- A concise explanation of the problem / 需求背景与目标.
- The user reproduction flow / 复现步骤.
- Verified evidence and root cause / 验证证据与根因分析.
- The required implementation behavior / 详细功能设计（严格遵循 CLI 优先原则，明确 CLI 命令、参数、输入输出与 Web UI 交互）.
- The workaround, if any / 规避方案.
- **完备的验收标准（必须明确包含全层级测试交付要求）**：
  - **单元测试**：覆盖 Models、Repo、Service 逻辑/权限/错误码、HTTP Handler、CLI 参数解析与 Frontend Hooks/Components/Stores。
  - **集成测试**：明确更新或新增 `tests/integration/` 场景说明规范（Markdown）及 `tests/integration/scripts/` 自动化测试脚本。
  - **E2E / Playwright 测试**：对所有用户可见功能及交互行为，明确更新或新增 `tests/e2e/*.spec.ts` 浏览器端到端交互用例。
- The exact GitHub issue URL near the top and again in the closing context when useful.

Use `high` priority only when the conversation indicates meaningful user impact; otherwise use `normal`. Do not assign a project, assignee, or due date unless the user asks.

### 6. Create the structured Mopheus GitHub link

After the ticket exists, sync the GitHub issue into the Mopheus repository mirror and link it to the ticket:

```bash
mopheus <target-connection-args> --workspace-id <target-workspace-id> repo issue sync \
  --number <github-issue-number> \
  --repo https://github.com/enmotech/mopheus.git \
  --ticket <ticket-id> \
  --state <actual-issue-state> \
  --output json
```

This structured `git_issue` link is required in addition to the clickable GitHub URL in the ticket description. If syncing or linking fails, report the failure and do not claim that the records are fully linked.

### 7. Verify and report

Read both records after creation:

```bash
gh-wrapper issue view <number> --repo enmotech/mopheus --json number,title,url,state,labels
mopheus <target-connection-args> --workspace-id <target-workspace-id> ticket get <ticket-id> --output json
mopheus <target-connection-args> --workspace-id <target-workspace-id> repo links --ticket <ticket-id> --output json
```

Confirm:

- GitHub issue is in `enmotech/mopheus`. In New-report mode, confirm it contains the English analysis; in Existing-Issue mode, confirm no duplicate issue was created.
- Mopheus ticket belongs to `<target-workspace-id>` resolved at the start of the run.
- The ticket description contains the exact GitHub URL.
- Mopheus structured links include the synced `git_issue` entity for the GitHub issue number and repository.
- No record was created in another workspace.

If an incorrect ticket was accidentally created in another workspace, cancel it, then create the correct ticket in `<target-workspace-id>`; report both IDs and statuses.

## Final response

Report only verified results:

- GitHub issue URL and number.
- Mopheus ticket number, ID, and workspace ID.
- Ticket status and priority.
- Any screenshot hosting limitation or corrected accidental record.

Use Chinese in the final response unless the user requests another language.
