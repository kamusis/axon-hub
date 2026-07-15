---
name: github-issue-to-dev-ticket
description: "Create a complete cross-platform bug or feature report from the current conversation: first create an English GitHub issue in the remote repository for the current local git repository, then create a Chinese ticket in the MoClaw dev workspace that explains the problem and links to the GitHub issue. Use this skill whenever the user asks to turn a bug, feature, investigation, screenshots, or conversation findings into both a GitHub issue and a MoClaw ticket. Always resolve the repository from the current local git remote, use the fixed dev workspace ID, and verify its name before creating the ticket; never use the active workspace or dev-v2 by inference."
---

# GitHub Issue and MoClaw Dev Ticket

Turn the conversation's evidence into two linked records in a fixed order:

1. An English GitHub issue in the current local repository's resolved GitHub remote.
2. A Chinese MoClaw ticket in the `dev` workspace.

The GitHub issue is the canonical external report. The MoClaw ticket is the internal implementation entry and must link to the GitHub issue URL.

## Fixed internal target

The MoClaw internal target is fixed:

- GitHub CLI: use `gh-wrapper` when it is available; otherwise use `gh`
- MoClaw workspace name: `dev`
- MoClaw workspace ID: `a43acd83-25f4-43ea-bdfd-d179fb272172`

The GitHub repository is not fixed. Resolve it from the local repository where the task is being performed.

## Resolve the GitHub repository

Run these checks before creating the GitHub issue:

```bash
git rev-parse --show-toplevel
git remote get-url origin
```

Keep the original remote URL for MoClaw repository operations, and normalize it separately to the GitHub `owner/repo` form accepted by `gh`, supporting both HTTPS and SSH forms. If `origin` is missing, points to a non-GitHub host, or cannot be resolved unambiguously, stop and ask for the repository instead of guessing. Use the resolved `owner/repo` for GitHub commands and the original remote URL for MoClaw repository commands.

Do not infer the GitHub repository from the MoClaw workspace name, prior conversation, or a previous task.

Never use the current active workspace, `dev-v2`, or a workspace selected by a prior command for the internal ticket. Always pass the fixed workspace ID explicitly with `moclaw --workspace-id a43acd83-25f4-43ea-bdfd-d179fb272172 ...`.

Before creating the internal ticket, run:

```bash
moclaw workspace list --output json
```

Verify that the fixed ID exists and its `name` is exactly `dev`. If the ID is missing or maps to another name, stop before creating either record and report the mismatch.

## Workflow

### 0. Resolve the report scope

Before extracting evidence or performing any external write, determine which single bug or feature the user wants to turn into records.

- Treat the user's latest explicit scope, named topic, issue, PR, job, task ID, or screenshot context as authoritative.
- Use earlier conversation content only when it directly supports that selected scope.
- Do not merge independent bugs or features into one GitHub issue or one MoClaw ticket.
- If the conversation contains multiple independent candidate topics and the user's instruction does not identify one, stop and ask which topic to process. Do not run `gh issue create`, `moclaw ticket create`, or `moclaw repo issue sync` while the scope is ambiguous.
- If the user explicitly requests separate records for multiple topics, process each topic independently, creating one GitHub issue and one linked MoClaw ticket per topic.

For example, a conversation that contains both a coverage-job failure and an RBAC authorization bug requires a scope clarification unless the user names one of them.

### 1. Extract and verify evidence

Read the full conversation context and collect:

- User action sequence and exact reproduction steps.
- Expected and actual behavior.
- Error messages, IDs, logs, API responses, and relevant environment details.
- Root cause analysis supported by repository code or live read-only checks.
- Workarounds and their side effects.
- Attached screenshots or files, when present.

Do not invent missing evidence. If the cause is uncertain, describe it as a hypothesis and do not present it as confirmed.

Classify the report as `bug` or `feature` from the user's request. For a bug, include reproduction, expected behavior, actual behavior, root cause, workaround, and acceptance criteria. For a feature, include objective, motivation, definitive behavior, acceptance criteria, and dependencies.

### 2. Prepare screenshots

If the conversation includes screenshots relevant to the report, the GitHub issue body must contain the screenshots as rendered Markdown images. Do not merely mention that screenshots exist or leave them as local file paths.

- Use the provided absolute attachment paths.
- Use the S.EE uploader skill/script to obtain public Markdown image links, then place every relevant image link directly in the GitHub issue body under `## Evidence` or `## Screenshots`.
- Preserve the order and explain what each screenshot demonstrates.
- Do not upload credentials, tokens, private keys, or unrelated sensitive data. If a screenshot contains secrets, omit it and describe the evidence in text.

If screenshot upload or safe hosting is unavailable, stop before creating the GitHub issue and report the blocker. A report with available screenshots must not be created without embedding those screenshots.

### 3. Create the GitHub issue first

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

Create the issue in the resolved current repository with the `bug` label for bugs and `enhancement` for features. Add other existing repository labels only when supported by the evidence. Capture and verify the returned GitHub issue URL before continuing.

Do not create the MoClaw ticket if GitHub issue creation fails or no issue URL is returned.

### 4. Create the Chinese `dev` ticket

After GitHub creation succeeds, create the internal ticket with the explicit fixed workspace ID:

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

### 5. Create the structured MoClaw GitHub link

After the ticket exists, sync the GitHub issue into the MoClaw repository mirror and link it to the ticket:

```bash
moclaw --workspace-id a43acd83-25f4-43ea-bdfd-d179fb272172 repo issue sync \
  --number <github-issue-number> \
  --repo <original-git-remote-url> \
  --ticket <ticket-id> \
  --state open \
  --output json
```

This structured `git_issue` link is required in addition to the clickable GitHub URL in the ticket description. If syncing or linking fails, report the failure and do not claim that the records are fully linked.

### 6. Verify and report

Read both newly created records after creation:

```bash
gh-wrapper issue view <number> --repo <resolved-owner/repo> --json number,title,url,state,labels
moclaw --workspace-id a43acd83-25f4-43ea-bdfd-d179fb272172 ticket get <ticket-id> --output json
moclaw --workspace-id a43acd83-25f4-43ea-bdfd-d179fb272172 repo links --ticket <ticket-id> --output json
```

Confirm:

- GitHub issue is in the resolved remote repository for the current local git repository and contains the English analysis.
- MoClaw ticket belongs to workspace ID `a43acd83-25f4-43ea-bdfd-d179fb272172`.
- The ticket description contains the exact GitHub URL.
- MoClaw structured links include the synced `git_issue` entity for the GitHub issue number and repository.
- No record was created in `dev-v2`.

If an incorrect ticket was accidentally created in another workspace, cancel it, then create the correct ticket in `dev`; report both IDs and statuses.

## Final response

Report only verified results:

- GitHub issue URL and number.
- `dev` ticket number and ID.
- Ticket status and priority.
- Any screenshot hosting limitation or corrected accidental record.

Use Chinese in the final response unless the user requests another language.
