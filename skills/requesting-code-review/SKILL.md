---
name: requesting-code-review
description: Use when finishing an issue to run an optional pre-commit readiness gate, and when completing tasks or before merging to request code review to verify work meets requirements
---

# Requesting Code Review

Request code review early to catch issues before they cascade.

**Core principle:** Review early, review often.

## Step 0 (Optional): Pre-Commit Readiness Gate

Use this when you finished implementing an issue and want to confirm you're ready to create commits.

**Goal:** Decide whether the work is complete enough (against the issue requirements) to start committing.

**Do not discuss PR strategy** in this step.

### 0.1 Collect Issue Requirements

Ask for:

```
- Issue link or identifier (e.g. #123)
- Acceptance criteria / requirements (paste or summarize)
- Any explicit out-of-scope notes
```

If acceptance criteria are unclear, ask:

```
What behaviors should change from the user's perspective?
What are the "done" conditions?
```

### 0.2 Run Tests (Gate)

Before saying the work is ready to commit, require a test run appropriate for the project:

```bash
npm test / cargo test / pytest / go test ./...
```

If tests fail, stop and list the failures.

### 0.3 Check Local Git Hygiene (Pre-Commit)

```bash
git rev-parse --abbrev-ref HEAD
git status --porcelain
```

If there are unrelated/unexpected changes, ask whether to split them before committing.

### 0.4 Check README.md Coverage for User-Facing Changes (Pre-Commit)

1. Check whether `README.md` exists:

```bash
test -f README.md && echo "README exists" || echo "README missing"
```

If `README.md` is missing, remind the user to create it before committing if the change is user-facing.

2. Determine whether this change is user-facing.

Treat the changes as user-facing if any of the following are true:

- New or changed user-facing CLI commands/subcommands
- New or changed user-facing CLI flags/options/parameters
- New or changed public API endpoints, request/response schemas, auth requirements, or error codes
- New or changed integration surface (SDK usage, webhooks, message formats)
- New or changed configuration keys/files/environment variables or setup steps
- UI/UX changes (layout, navigation, permissions, settings, flows)

Suggested signals to detect user-facing changes:

```bash
# Changed files
git diff --name-only

# Search for common CLI/API/config/documentation signals in the diff
git diff | rg -n "(--[a-zA-Z0-9_-]+\b|\bUsage:\b|\bFlags:\b|\bOptions:\b|\bconfig\b|\benv\b|\bendpoint\b|\broute\b|\bauth\b|\bpermission\b)" || true
```

Also treat the changes as likely user-facing if modified paths include typical entrypoints, for example:

- `cmd/`, `src/cmd/`, `commands/`
- `api/`, `handlers/`, `controllers/`, `routes/`, `openapi`, `swagger`, `proto`, `graphql`
- `web/`, `ui/`, `frontend/`, `pages/`, `routes/`, `components/`
- `config/` or config-related files (`.env`, `*.yaml`, `*.toml`, `*.json`)

3. If user-facing changes are detected and `README.md` exists, verify README mentions the changes.

Search README for the inferred new commands/flags/config keys/URLs. Examples:

```bash
rg -n "\b<new_command>\b" README.md
rg -n "--<new_flag>\b" README.md
rg -n "\b<new_config_key>\b" README.md
```

If you detect user-facing changes but cannot find reasonable coverage in README, pause and prompt:

"This change appears user-facing, but README.md does not seem to document it yet. Do you want to update README before committing?"

### 0.5 Output a Readiness Decision

Return a short report in this exact structure:

```text
Pre-commit readiness

Decision: READY_TO_COMMIT | NOT_READY_TO_COMMIT

What looks done:
- ...

Missing / risks to address before committing:
- ...
```

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Request review using your available channel:**

Use one of the following (choose what your environment supports):

- GitHub UI: Open the PR and request reviewers.
- GitHub CLI: `gh pr create` (if needed) then `gh pr edit --add-reviewer <user>`.
- GitHub MCP (if available): Use the GitHub MCP tools to create/update the PR and request reviewers.

**Placeholders:**
- `{WHAT_WAS_IMPLEMENTED}` - What you just built
- `{PLAN_OR_REQUIREMENTS}` - What it should do
- `{BASE_SHA}` - Starting commit
- `{HEAD_SHA}` - Ending commit
- `{DESCRIPTION}` - Brief summary

**3. Act on feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if reviewer is wrong (with reasoning)

## Example

```
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch superpowers:code-reviewer subagent]
  WHAT_WAS_IMPLEMENTED: Verification and repair functions for conversation index
  PLAN_OR_REQUIREMENTS: Task 2 from docs/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types

[Subagent returns]:
  Strengths: Clean architecture, real tests
  Issues:
    Important: Missing progress indicators
    Minor: Magic number (100) for reporting interval
  Assessment: Ready to proceed

You: [Fix progress indicators]
[Continue to Task 3]
```

## Integration with Workflows

**Subagent-Driven Development:**
- Review after EACH task
- Catch issues before they compound
- Fix before moving to next task

**Executing Plans:**
- Review after each batch (3 tasks)
- Get feedback, apply, continue

**Ad-Hoc Development:**
- Review before merge
- Review when stuck

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification

See template at: requesting-code-review/code-reviewer.md
