---
name: github-pr-merge
description: 'Merge a GitHub Pull Request using squash merge with clean Conventional Commits message. Analyzes PR content, validates/fixes title format, and generates structured commit message body from PR description.'
---

# GitHub PR Merge

Merge a GitHub Pull Request using squash merge with a clean, well-structured Conventional Commits message.

## What I Do

1. **Fetch PR details** - Get PR title, body, commits, and diff
2. **Validate PR title** - Check if it follows Conventional Commits format
3. **Fix title if needed** - Convert to `type(scope): description` if non-compliant
4. **Generate commit body** - Clean up and structure PR body into proper commit message
5. **Execute squash merge** - Prefer `gh pr merge --squash --subject --body-file --delete-branch` when supported; fall back to amend-based cleanup only on older `gh` versions that cannot set the squash commit message directly

## When to Use Me

Triggers on requests like:
- "Merge this PR"
- "Squash merge PR #123"
- "Merge the current PR"
- "Merge PR with clean commit message"

## Workflow

### Step 1: Identify PR to Merge

Determine which PR to merge:
- If PR number provided: `gh pr view <number>`
- If on PR branch: `gh pr view`

Get PR details:
```bash
# Get PR title, body, and state
gh pr view <number> --json title,body,state,headRefName,baseRefName

# Get PR commits
gh pr view <number> --json commits

# Get PR diff stats
gh diff <base>..<head> --stat
```

### Step 2: Validate PR Title (Conventional Commits)

Check if PR title follows Conventional Commits format:

**Valid format:** `type(scope): description` or `type: description`

**Valid types:**
- `feat` - New feature
- `fix` - Bug fix
- `refactor` - Code restructuring
- `docs` - Documentation
- `test` - Tests
- `chore` - Maintenance
- `perf` - Performance
- `ci` - CI/CD
- `build` - Build system
- `style` - Code style

**Validation regex:**
```
^(feat|fix|refactor|docs|test|chore|perf|ci|build|style)(\([a-z0-9-]+\))?: .+$
```

### Step 3: Fix PR Title if Non-Compliant

If PR title does NOT match Conventional Commits format:

1. **Analyze PR content** to determine appropriate type:
   - Look at changed files (feature files? bug fixes? docs?)
   - Look at PR body for keywords (fix, feature, refactor, etc.)
   - Look at commit messages in the PR

2. **Infer scope** from:
   - Changed file paths (e.g., `cmd/` → `cli`, `internal/auth/` → `auth`)
   - PR body mentions
   - Common scopes: `cli`, `api`, `auth`, `db`, `ui`, `config`

3. **Generate new title:**
   - Use imperative mood (add, fix, update, refactor)
   - Keep under 72 characters
   - Format: `type(scope): description`

**Example conversions:**
- `Add user authentication` → `feat(auth): add user authentication`
- `Bug fix for login` → `fix(auth): resolve login validation error`
- `Update README` → `docs: update README with installation instructions`

### Step 4: Generate Commit Message Body

Analyze PR body and generate clean, structured commit message body.

**Strategy:**
1. If PR body is already well-structured (follows Conventional Commits body format):
   - Use as-is or with minor cleanup

2. If PR body is messy/verbose:
   - Extract key changes from PR body
   - Extract from commit messages in PR
   - Analyze actual diff for significant changes
   - Structure into:

```text
Major changes:
- Key change 1
- Key change 2

Minor improvements:
- Minor change 1
- Minor change 2
```

**Extraction rules:**
- Include: functional changes, new features, breaking changes, bug fixes
- Exclude: file paths, raw URLs, code snippets, trivial formatting, noise
- Group related changes together
- Use present tense imperative mood
- **Do NOT hard-wrap lines.** Each bullet point must be a single unbroken line — never insert manual line breaks to fit a width. The terminal/editor handles soft-wrapping; hard newlines create malformed commit messages when consumed by tools.

### Step 5: Present Merge Plan

Show user the complete merge plan:

First detect whether the installed `gh` supports direct custom squash commit messages:

```bash
gh pr merge --help | grep -E -- '--subject|--body-file'
```

If both `--subject` and `--body-file` are supported, prefer the direct merge plan:

```markdown
## PR Merge Plan

**PR:** #<number> - <title>

**Commit message:**
```
<type>(<scope>): <description>

<body - structured changes>
```

**Commands (will execute in order):**
1. `git checkout <base-branch>`
2. `git pull origin <base-branch>`
3. `gh pr merge <number> --squash --delete-branch --subject "<subject>" --body-file <body-file>`

> Note: This `gh` version supports direct squash commit subject/body customization.
> Use that path because `gh pr merge` performs the merge on GitHub; local `git commit --amend` may not target the merge commit.

Do you want to proceed?
```

If direct custom messages are not supported, present the fallback amend plan:

```markdown
## PR Merge Plan

**PR:** #<number> - <title>

**Commit message:**
```
<type>(<scope>): <description>

<body - structured changes>
```

**Commands (will execute in order):**
1. `git checkout <base-branch>`
2. `git pull origin <base-branch>`
3. `gh pr merge <number> --squash --delete-branch`
4. `git pull origin <base-branch>`
5. `git commit --amend -m "<type>(<scope>): <description>\n\n<body>"`

> Note: This fallback is only for older `gh` versions without `--subject` and `--body-file`.
> Pull after merge before amending so local `HEAD` is the actual squash merge commit.

Do you want to proceed?
```

### Step 6: Execute Merge

If user approves, execute the following steps **in strict order**. Do NOT skip any step.

**Step 6a: Detect merge-message support**
```bash
gh pr merge --help | grep -E -- '--subject|--body-file'
```

If the installed `gh` supports both `--subject` and `--body-file`, use the preferred direct path.

**Preferred path: direct custom squash message**
```bash
git checkout <base-branch>
git pull origin <base-branch>
printf '%s\n' "<clean commit message body from Step 4>" > /tmp/pr-<number>-merge-body.txt
gh pr merge <number> --squash --delete-branch \
  --subject "<type>(<scope>): <description>" \
  --body-file /tmp/pr-<number>-merge-body.txt
```

If `--subject` or `--body-file` is not supported, use the fallback path.

**Fallback path: amend after remote merge**
```bash
git checkout <base-branch>
git pull origin <base-branch>
gh pr merge <number> --squash --delete-branch
git pull origin <base-branch>
git commit --amend -m "<clean commit message from Step 4>"
```

Only use the fallback amend path when direct custom commit message flags are unavailable. On current `gh` versions, direct `--subject`/`--body-file` is safer because the squash merge is created by GitHub and local `HEAD` may not be the merge commit until after a pull.

**Step 6b: Verify**
```bash
# Confirm the commit message is correct
gh api repos/<owner>/<repo>/commits/<merge-sha> --jq '.commit.message'
```

If the message is still the default concatenated format, something went wrong. If direct flags were used, stop and report the mismatch. If the fallback path was used and the branch has not been pushed, re-run the amend step against the actual merge commit.

## Examples

### Example 1: PR with good title

**PR Title:** `feat(auth): add OAuth2 support`
**PR Body:** Long description with multiple fixes and changes...

**Action:**
- Title: Valid, use as-is
- Body: Clean up into structured format

**Commit message:**
```
feat(auth): add OAuth2 support

Major changes:
- Implement OAuth2 authentication flow
- Add support for Google and GitHub providers

Minor improvements:
- Update error handling for auth failures
- Add auth configuration validation
```

### Example 2: PR with bad title

**PR Title:** `Fixed the login bug and added some features`
**PR Body:** Details about changes...

**Action:**
- Title: Invalid, needs conversion
- Analyze changes → primarily fixes
- Infer scope → `auth`

**New title:** `fix(auth): resolve login validation and add features`

**Commit message:**
```
fix(auth): resolve login validation and add features

Major changes:
- Fix login form validation errors
- Add password strength indicator

Minor improvements:
- Update login error messages
- Add input sanitization
```

## Important Notes

- **Always validate title** before merging
- **Clean up messy bodies** - don't just concatenate all commits
- **Use imperative mood** in descriptions
- **Keep subject under 72 characters**
- **Separate subject from body with blank line**
- **Use bullet points** for multiple changes
- **Ask for approval** before executing merge
- **Prefer direct custom squash messages** — If `gh pr merge` supports `--subject` and `--body-file`, use those flags and do not amend.
- **Fallback amend only for older `gh` versions** — If direct custom message flags are unavailable, amend only after pulling the merge commit locally, then verify the remote commit message.

## Error Handling

- PR not found: Verify PR number and repository
- PR not mergeable: Check for conflicts, approvals, status checks
- Non-Compliant title: Auto-fix or ask user for type/scope
- Empty body: Generate body from commits and diff
- Merge conflicts: Inform user, suggest rebase first

## Related Skills

- `github-pr-creator` - Creates PRs with Conventional Commits format
- `git-commit-message` - Generates commit messages from staged changes
