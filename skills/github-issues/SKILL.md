---
name: github-issues
description: 'Create, update, and manage GitHub issues using gh CLI. Use this skill when users want to create bug reports, feature requests, or task issues, update existing issues, add labels/assignees/milestones, or manage issue workflows. Triggers on requests like "create an issue", "file a bug", "request a feature", "update issue X", or any GitHub issue management task.'
---

# GitHub Issues

Manage GitHub issues using the `gh` CLI.

## Available gh Commands

| Command | Purpose |
|---------|---------|
| `gh issue create` | Create new issues |
| `gh issue edit` | Update existing issues |
| `gh issue view` | Fetch issue details |
| `gh issue list` | List repository issues |
| `gh issue comment` | Add comments |
| `gh issue close` | Close issues |
| `gh issue reopen` | Reopen issues |

## Workflow

1. **Determine action**: Create, update, or query?
2. **Gather context**: Get repo info, existing labels, milestones if needed
3. **Structure content**: Use appropriate template from [references/templates.md](references/templates.md)
4. **Execute**: Run the appropriate `gh` command
5. **Confirm**: Report the issue URL to user

## Creating Issues

### gh issue create Command

```bash
gh issue create --repo owner/repo --title "Title" --body "Body content" --label "bug,enhancement" --assignee "username1,username2" --milestone "v1.0"
```

### Required Parameters

- `--repo owner/repo` - Repository (owner/name format)
- `--title` - Clear, actionable title
- `--body` - Structured markdown content

### Requirement Clarity Rules

When creating an issue, write requirements and design decisions as a single settled specification. Do not leave ambiguity for the later implementer.

- Do not use vague wording that gives the implementer multiple choices, such as "suggest", "maybe", "could", "consider", "if possible", "preferably", "one option is", "A or B", "either", "or", "and/or", "etc.", or "whatever works".
- Do not describe several possible implementations and ask the implementer to choose.
- Do not write acceptance criteria that allow multiple interpretations.
- Convert user-approved decisions into definitive wording: "Do X", "Use Y", "Save is disabled when Z", "Show message M".
- If the user has not made a required product, UX, validation, data-model, or technical decision, stop before creating the issue and ask a direct clarification question.
- If the user asks for brainstorming or evaluation rather than issue creation, keep options in the conversation. Only create the issue after the final decision is unique and explicit.
- Use an "Alternatives Considered" section only to record rejected approaches. Each rejected approach must clearly say it is not part of the implementation.

### Optional Parameters

- `--label` - Comma-separated labels (e.g., "bug,high-priority")
- `--assignee` - Comma-separated assignees (e.g., "user1,user2")
- `--milestone` - Milestone title

### Title Guidelines

- Start with type prefix when useful: `[Bug]`, `[Feature]`, `[Docs]`
- Be specific and actionable
- Keep under 72 characters
- Examples:
  - `[Bug] Login fails with SSO enabled`
  - `[Feature] Add dark mode support`
  - `Add unit tests for auth module`

### Body Structure

Always use the templates in [references/templates.md](references/templates.md). Choose based on issue type:

| User Request | Template |
|--------------|----------|
| Bug, error, broken, not working | Bug Report |
| Feature, enhancement, add, new | Feature Request |
| Task, chore, refactor, update | Task |

## Updating Issues

### gh issue edit Command

```bash
gh issue edit <issue_number> --repo owner/repo --title "New title" --body "New body" --add-label "bug" --remove-label "enhancement" --add-assignee "user1" --remove-assignee "user2"
```

### Update Parameters

- `--title` - New title
- `--body` - New body
- `--add-label` - Add label(s)
- `--remove-label` - Remove label(s)
- `--add-assignee` - Add assignee(s)
- `--remove-assignee` - Remove assignee(s)
- `--milestone` - Set milestone

### State Changes

```bash
# Close an issue
gh issue close <issue_number> --repo owner/repo

# Reopen an issue
gh issue reopen <issue_number> --repo owner/repo
```

## Viewing Issues

### gh issue view Command

```bash
# View issue details
gh issue view <issue_number> --repo owner/repo

# View with specific fields
gh issue view <issue_number> --repo owner/repo --json title,body,state,labels,assignees
```

## Listing Issues

### gh issue list Command

```bash
# List all open issues
gh issue list --repo owner/repo

# List with filters
gh issue list --repo owner/repo --state open --label "bug" --assignee "username"

# Limit results
gh issue list --repo owner/repo --limit 10
```

## Adding Comments

### gh issue comment Command

```bash
gh issue comment <issue_number> --repo owner/repo --body "Comment text here"
```

## Examples

### Example 1: Bug Report

**User**: "Create a bug issue - the login page crashes when using SSO"

**Action**:
```bash
gh issue create --repo github/awesome-copilot \
  --title "[Bug] Login page crashes when using SSO" \
  --body "## Description
The login page crashes when users attempt to authenticate using SSO.

## Steps to Reproduce
1. Navigate to login page
2. Click 'Sign in with SSO'
3. Page crashes

## Expected Behavior
SSO authentication should complete and redirect to dashboard.

## Actual Behavior
Page becomes unresponsive and displays error.

## Environment
- Browser: [To be filled]
- OS: [To be filled]

## Additional Context
Reported by user." \
  --label "bug"
```

### Example 2: Feature Request

**User**: "Create a feature request for dark mode with high priority"

**Action**:
```bash
gh issue create --repo github/awesome-copilot \
  --title "[Feature] Add dark mode support" \
  --body "## Summary
Add dark mode theme option for improved user experience and accessibility.

## Motivation
- Reduces eye strain in low-light environments
- Increasingly expected by users
- Improves accessibility

## Proposed Solution
Implement theme toggle with system preference detection.

## Acceptance Criteria
- [ ] Toggle switch in settings
- [ ] Persists user preference
- [ ] Respects system preference by default
- [ ] All UI components support both themes

## Alternatives Considered
None specified.

## Additional Context
High priority request." \
  --label "enhancement,high-priority"
```

### Example 3: Update Issue

**User**: "Add bug label to issue #42"

**Action**:
```bash
gh issue edit 42 --repo owner/repo --add-label "bug"
```

### Example 4: Close Issue

**User**: "Close issue #42"

**Action**:
```bash
gh issue close 42 --repo owner/repo
```

## Common Labels

Use these standard labels when applicable:

| Label | Use For |
|-------|---------|
| `bug` | Something isn't working |
| `enhancement` | New feature or improvement |
| `documentation` | Documentation updates |
| `good first issue` | Good for newcomers |
| `help wanted` | Extra attention needed |
| `question` | Further information requested |
| `wontfix` | Will not be addressed |
| `duplicate` | Already exists |
| `high-priority` | Urgent issues |

## Tips

- Always confirm the repository context before creating issues
- Ask for missing critical information rather than guessing
- Resolve ambiguous requirements before creating the issue; never leave implementation choices in the issue body
- Link related issues when known: `Related to #123`
- For updates, fetch current issue first to preserve unchanged fields
- Use `gh issue view` to check existing issue state before modifying
