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
5. **Execute squash merge** - Merge with `--squash --delete-branch`

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

### Step 5: Present Merge Plan

Show user the complete merge plan:

```markdown
## PR Merge Plan

**PR:** #<number> - <title>

**Commit message:**
```
<type>(<scope>): <description>

<body - structured changes>
```

**Command:**
```bash
gh pr merge <number> --squash --delete-branch
```

Do you want to proceed?
```

### Step 6: Execute Merge

If user approves:

```bash
# Ensure we're on the base branch
git checkout <base-branch>
git pull origin <base-branch>

# Execute squash merge
gh pr merge <number> --squash --delete-branch

# Amend commit message if needed
git commit --amend -m "<clean commit message>"

# Push if needed (usually not required with gh)
# git push origin <base-branch>
```

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

## Error Handling

- PR not found: Verify PR number and repository
- PR not mergeable: Check for conflicts, approvals, status checks
- Non-Compliant title: Auto-fix or ask user for type/scope
- Empty body: Generate body from commits and diff
- Merge conflicts: Inform user, suggest rebase first

## Related Skills

- `github-pr-creator` - Creates PRs with Conventional Commits format
- `git-commit-message` - Generates commit messages from staged changes
