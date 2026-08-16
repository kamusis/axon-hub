---
name: github-issue-to-mopheus-dev-ticket
description: "Create a complete cross-platform bug or feature report from the current conversation, or create only the missing Chinese Mopheus dev ticket for an already-existing GitHub issue. Use when the user wants both an English GitHub issue and linked Mopheus ticket, or explicitly has a GitHub issue but no corresponding Mopheus ticket. Always resolve the repository from the current local git remote, use the fixed dev workspace ID, verify its name, and never duplicate an existing issue or ticket."
---

# GitHub Issue to Mopheus Dev Ticket

Support two modes:

1. **New-report mode:** create an English GitHub issue, then a linked Chinese Mopheus ticket.
2. **Existing-Issue mode:** verify a supplied GitHub issue, confirm it has no linked Mopheus ticket, then create and link only the ticket.

The GitHub issue is the canonical external report. The Mopheus ticket is the internal implementation entry and must link to the GitHub issue URL.

## Fixed internal target

The Mopheus internal target is fixed:

- GitHub CLI: use `gh-wrapper` when it is available; otherwise use `gh`
- Mopheus workspace name: `dev`
- Mopheus workspace ID: `a43acd83-25f4-43ea-bdfd-d179fb272172`

The GitHub repository is not fixed. Resolve it from the local repository where the task is being performed.

## Resolve the GitHub repository

Run these checks before creating or verifying the GitHub issue:

```bash
git rev-parse --show-toplevel
git remote get-url origin
```

Keep the original remote URL for Mopheus repository operations, and normalize it separately to the GitHub `owner/repo` form accepted by `gh`, supporting both HTTPS and SSH forms. If `origin` is missing, points to a non-GitHub host, or cannot be resolved unambiguously, stop and ask for the repository instead of guessing. Use the resolved `owner/repo` for GitHub commands and the original remote URL for Mopheus repository commands.

Do not infer the GitHub repository from the Mopheus workspace name, prior conversation, or a previous task.

Never use the current active workspace, `dev-v2`, or a workspace selected by a prior command for the internal ticket. Always pass the fixed workspace ID explicitly with `moclaw --workspace-id a43acd83-25f4-43ea-bdfd-d179fb272172 ...`.

Before creating the internal ticket, run:

```bash
moclaw workspace list --output json
```

Verify that the fixed ID exists and its `name` is exactly `dev`. If the ID is missing or maps to another name, stop before creating any record and report the mismatch.

## Workflow

### 0. Select the mode

- Use **Existing-Issue mode** only when the user or calling skill supplies one unambiguous GitHub issue URL or number and states that its Mopheus ticket is missing.
- Verify the issue with `gh-wrapper issue view` in the repository resolved from the current local `origin`. Stop on a repository mismatch or missing issue.
- Query `moclaw --workspace-id a43acd83-25f4-43ea-bdfd-d179fb272172 repo links --repo <original-git-remote-url> --type git_issue --number <n> --output json`.
- If a linked ticket already exists, return and reuse it; do not create another ticket.
- In Existing-Issue mode, never run `gh issue create`. Treat the verified issue title, body, labels, state, URL, and relevant conversation evidence as the canonical report.
- Otherwise use **New-report mode** and retain the issue-first workflow below.

### 1. Resolve the report scope

Before extracting evidence or performing any external write, determine which single bug or feature the user wants to turn into records.

- Treat the user's latest explicit scope, named topic, issue, PR, job, task ID, or screenshot context as authoritative.
- Use earlier conversation content only when it directly supports that selected scope.
- Do not merge independent bugs or features into one GitHub issue or one Mopheus ticket.
- If the conversation contains multiple independent candidate topics and the user's instruction does not identify one, stop and ask which topic to process. Do not run `gh issue create`, `moclaw ticket create`, or `moclaw repo issue sync` while the scope is ambiguous.
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

Create the issue in the resolved current repository with the `bug` label for bugs and `enhancement` for features. Add other existing repository labels only when supported by the evidence. Capture and verify the returned GitHub issue URL before continuing.

Do not create the Mopheus ticket if GitHub issue creation fails or no issue URL is returned.

### 5. Create the Chinese `dev` ticket

After GitHub creation or existing-Issue verification succeeds, create the internal ticket with the explicit fixed workspace ID:

```bash
moclaw --workspace-id a43acd83-25f4-43ea-bdfd-d179fb272172 ticket create \
  --title "<Chinese title>" \
  --priority high \
  --status todo \
  --description-stdin
```

Write the ticket in Chinese. Include:

- A concise explanation of the problem.
- The user reproduction flow.
- Verified evidence and root cause.
- The required implementation behavior.
- The workaround, if any.
- The exact GitHub issue URL near the top and again in the closing context when useful.

Use `high` priority only when the conversation indicates meaningful user impact; otherwise use `normal`. Do not assign a project, assignee, or due date unless the user asks.

### 6. Create the structured Mopheus GitHub link

After the ticket exists, sync the GitHub issue into the Mopheus repository mirror and link it to the ticket:

```bash
moclaw --workspace-id a43acd83-25f4-43ea-bdfd-d179fb272172 repo issue sync \
  --number <github-issue-number> \
  --repo <original-git-remote-url> \
  --ticket <ticket-id> \
  --state <actual-issue-state> \
  --output json
```

This structured `git_issue` link is required in addition to the clickable GitHub URL in the ticket description. If syncing or linking fails, report the failure and do not claim that the records are fully linked.

### 7. Verify and report

Read both records after creation:

```bash
gh-wrapper issue view <number> --repo <resolved-owner/repo> --json number,title,url,state,labels
moclaw --workspace-id a43acd83-25f4-43ea-bdfd-d179fb272172 ticket get <ticket-id> --output json
moclaw --workspace-id a43acd83-25f4-43ea-bdfd-d179fb272172 repo links --ticket <ticket-id> --output json
```

Confirm:

- GitHub issue is in the resolved remote repository for the current local git repository. In New-report mode, confirm it contains the English analysis; in Existing-Issue mode, confirm no duplicate issue was created.
- Mopheus ticket belongs to workspace ID `a43acd83-25f4-43ea-bdfd-d179fb272172`.
- The ticket description contains the exact GitHub URL.
- Mopheus structured links include the synced `git_issue` entity for the GitHub issue number and repository.
- No record was created in `dev-v2`.

If an incorrect ticket was accidentally created in another workspace, cancel it, then create the correct ticket in `dev`; report both IDs and statuses.

## Final response

Report only verified results:

- GitHub issue URL and number.
- `dev` ticket number and ID.
- Ticket status and priority.
- Any screenshot hosting limitation or corrected accidental record.

Use Chinese in the final response unless the user requests another language.
