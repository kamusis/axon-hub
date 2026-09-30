---
name: github-issues
description: 'Create, update, and manage GitHub issues using gh CLI. Strictly enforces single authoritative implementation design with zero ambiguity (strictly banning "or", "either", "或", alternatives, or undecided options), pre-creation user clarification for open design choices, and mandatory post-creation ambiguity verification.'
---

# GitHub Issues

Manage GitHub issues using the `gh` CLI.

## Invariants: Zero Ambiguity & Single Authoritative Design (方案唯一性与零模棱两可红线)

- **Single Settled Specification (设计方案务必绝对唯一)**: Every issue must describe exactly one concrete implementation. Issues are engineering execution contracts, not open design polls or brainstorming drafts.
- **Strict Ban on Ambiguous & Alternative Phrasing (严禁模棱两可与二选一措辞)**: The issue body strictly forbids wording that pushes decision-making to the implementer, such as "A or B", "either X or Y", "or", "and/or", "could", "maybe", "consider", "suggest", "optionally", "etc.", "或", "或者", "亦可", "备选方案".
- **Clarify Before Creating (未决设计前置追问，决策闭环)**: If multiple technical approaches or trade-offs exist and the preferred path is not 100% determined, **STOP immediately before creating the issue**. Ask the user direct clarifying questions to close the decision loop. Never create an issue containing an undecided choice or alternatives.
- **Mandatory Post-Creation Audit Step (创建后强制回览审计)**: After issue creation, always view the issue and scan for ambiguity markers. If any ambiguity is detected, remediate immediately via `gh issue edit` or user clarification.

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
2. **Gather context & Close Design Decisions**: Get repo info, resolve any open questions with the user, ensuring the design is 100% settled, concrete, and singular.
3. **Structure content**: Use appropriate template from [references/templates.md](references/templates.md), ensuring zero ambiguity.
4. **Execute**: Run the appropriate `gh` command (`gh issue create` or `gh issue edit`).
5. **Post-Creation Ambiguity Audit (Mandatory Check Step)**: Fetch the created/edited issue via `gh issue view`, verify content, and scan for any ambiguous phrasing (`or `, `either `, `或`, etc.). Remediate immediately if found.
6. **Confirm**: Report the issue URL and verified single-design audit status to user.

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

> [!CAUTION]
> **Zero Ambiguity & Single Implementation Standard**:
> - Never write "X or Y", "use A or B", "support either foo or bar", "参数 A 或 B". Every flag, parameter, data schema, route, and UI flow must have exactly one determined definition.
> - An issue must never ask the implementer to make product, UX, architecture, or data model choices.
> - If you feel the urge to write "or" / "或", STOP and ask the user to choose before creating the issue.

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

## Post-Creation Ambiguity Verification & Audit (强制回览审计)

After running `gh issue create`, you MUST execute a verification check to ensure zero ambiguity:

```bash
gh issue view <issue_number> --repo owner/repo
```

1. **Scan for ambiguity keywords**:
   - English: `or `, `either `, `optionally `, `alternative `, `maybe `, `could `, `etc.`
   - Chinese: `或`、`或者`、`亦可`、`也可以`、`备选`、`两种方式`
2. **Remediation**:
   - If imprecise phrasing is found but the intended solution is settled: immediately run `gh issue edit <issue_number> --repo owner/repo --body "..."` to remove ambiguity and lock in the single solution.
   - If an undecided architectural or product choice was inadvertently included: stop and ask the user for clarification, then update the issue with the user's decision.

## Tips

- Always confirm the repository context before creating issues
- Ask for missing critical information rather than guessing
- Resolve ambiguous requirements before creating the issue; never leave implementation choices in the issue body
- Link related issues when known: `Related to #123`
- For updates, fetch current issue first to preserve unchanged fields
- Use `gh issue view` to check existing issue state before modifying
- Always complete the post-creation ambiguity audit before confirming to the user
