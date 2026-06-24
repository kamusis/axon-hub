---
name: swissql-release
description: Prepare and execute SwissQL Core releases with paired CLI/backend tags, capability-oriented release notes, and GitHub Actions handoff. Use whenever releasing SwissQL Core, creating cli-v*/backend-v* tags, updating SwissQL release notes, or preparing release notes for the automated GitHub release workflow.
---

# SwissQL Release

Prepare a SwissQL Core release with paired component tags:

- `cli-vX.Y.Z`
- `backend-vX.Y.Z`

This skill is project-specific. Prefer it over the generic `github-release` skill for this repository.

## Core Principle

GitHub Actions is the release executor. The agent is the release editor.

Do not rely on GitHub auto-generated release notes as the preferred final release body. They often list internal commit titles and miss the user-facing capabilities. Prepare component-specific notes before tags are pushed whenever possible. If prepared notes are missing, do not block artifact publication: let GitHub Actions publish with generated notes, then replace the release body afterward.

## Required Release Shape

SwissQL uses paired release tags for the same version:

```text
cli-vX.Y.Z
backend-vX.Y.Z
```

Both tags normally point to the same `main` commit, but each GitHub Release must describe only its own component.

## Non-Negotiable Notes Separation

Write separate release notes for CLI and backend.

### CLI notes must include only CLI-facing content

Include:

- CLI commands, flags, output, config, rendering, validation, and client behavior
- CLI fixes and user-visible CLI behavior
- CLI tests only when useful as confidence notes
- CLI changelog link

Do not include backend-only implementation details in CLI notes. If a feature spans backend and CLI, explain only the CLI side in the CLI release.

Example:

```markdown
## Highlights

- Added `--ticket-id` to send request correlation IDs.
- Added `--executor` to identify the caller in audit-aware requests.
```

Do not write backend details such as servlet filters, MDC keys, controller audit logs, or Docker images in CLI notes.

### Backend notes must include only backend-facing content

Include:

- REST/API behavior, request headers, audit logs, config, Docker image, validation, persistence, SQL/rules behavior, driver behavior
- Backend fixes and operator-visible backend behavior
- Backend tests only when useful as confidence notes
- Backend changelog link

Do not include CLI-only implementation details in backend notes. If a feature spans backend and CLI, explain only the backend side in the backend release.

Example:

```markdown
Docker image: `ghcr.io/kamusis/swissql-core:X.Y.Z`

## Highlights

- Added `X-Ticket-Id` request correlation support.
- SQL execution audit logs now include `ticket_id=...`.
```

Do not write CLI flags or CLI command examples in backend notes unless they are necessary operator context. Prefer pointing to the CLI release for CLI usage.

## Workflow

### 1. Verify Release Preconditions

Run these checks before creating tags or editing releases:

```bash
git status --short --branch
git fetch origin main --tags --prune
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
```

Proceed only if:

- Current branch is `main`
- Working tree is clean
- Local `main` is aligned with `origin/main`
- The target tags do not already exist locally or remotely

Check tags:

```bash
git rev-parse -q --verify refs/tags/cli-vX.Y.Z
git rev-parse -q --verify refs/tags/backend-vX.Y.Z
git ls-remote --tags origin cli-vX.Y.Z backend-vX.Y.Z
```

### 2. Determine Release Range

For paired releases, compare each component against its previous component tag:

```bash
git log --oneline cli-vPREV..HEAD
git log --oneline backend-vPREV..HEAD
```

Collect PR context:

```bash
gh pr list --repo kamusis/swissql-core --state merged --limit 100 \
  --json number,title,body,mergedAt,url
```

Also inspect squash commit bodies in the range; they are usually cleaner than GitHub auto notes:

```bash
git log --pretty='%h%n%s%n%b%n---END---' backend-vPREV..HEAD
```

### 3. Classify Changes By Component

For each merged PR or commit, classify effects into:

- `cli`
- `backend`
- `both`
- `tests`
- `docs`
- `internal-only`

When a change is `both`, split it into two component-specific descriptions.

Example:

- Combined feature: executor identity for audit logs
- CLI release wording: "Added `--executor` to send caller identity on requests."
- Backend release wording: "Added `X-Executor` request handling and executor attribution in audit logs."

Avoid copying the same full paragraph into both releases.

### 4. Draft CLI Release Notes

Use this template:

```markdown
## Highlights

- <CLI-facing capability 1>
- <CLI-facing capability 2>

## Added

- <new CLI flags, commands, output, config, or client behavior>

## Fixed

- <CLI-visible bug fixes>

## Testing

- <CLI-specific confidence notes, if relevant>

## Related PRs

- #<number> — <CLI-specific summary>

**Full Changelog**: https://github.com/kamusis/swissql-core/compare/cli-vPREV...cli-vX.Y.Z
```

Omit empty sections. Keep highlights short and capability-oriented.

### 5. Draft Backend Release Notes

Use this template:

```markdown
Docker image: `ghcr.io/kamusis/swissql-core:X.Y.Z`

## Highlights

- <backend/API/operator-facing capability 1>
- <backend/API/operator-facing capability 2>

## Added

- <new REST/API, audit log, config, driver, rules, storage, or backend behavior>

## Fixed

- <backend-visible bug fixes>

## Testing

- <backend-specific confidence notes, if relevant>

## Related PRs

- #<number> — <backend-specific summary>

**Full Changelog**: https://github.com/kamusis/swissql-core/compare/backend-vPREV...backend-vX.Y.Z
```

Omit empty sections. Keep backend notes operator-facing and API-facing.

### 6. Prepare Repository Release Notes

SwissQL has an established repository convention. Write both release notes using filenames that exactly match the planned tags:

```text
release-notes/cli-vX.Y.Z.md
release-notes/backend-vX.Y.Z.md
```

Read `release-notes/README.md` and follow its templates and component boundaries. Do not ask whether to use this convention during a normal release.

Prepared notes are strongly preferred but are not an artifact-publication gate. If notes cannot be committed before tags are pushed, or the tag workflows are already running, allow GitHub Actions to complete with generated notes. Prepare temporary component-specific files and update the GitHub Releases afterward.

### 7. Commit Release Notes Before Tagging

For the normal release path:

```bash
git add release-notes/cli-vX.Y.Z.md release-notes/backend-vX.Y.Z.md
git commit -m "docs: add release notes for vX.Y.Z"
git push origin main
```

Only commit release note files. Do not mix code or unrelated docs into the release-notes commit. Push the commit to `main`, verify `HEAD` matches `origin/main`, and create both tags on that release-preparation commit.

If this step cannot be completed, do not treat missing notes alone as a release blocker. Continue the requested release and use the post-release correction path in step 9.

### 8. Create Annotated Tags

Use annotated tags matching existing project style:

```bash
git tag -a cli-vX.Y.Z -m "CLI vX.Y.Z"
git tag -a backend-vX.Y.Z -m "Backend vX.Y.Z"
git push origin cli-vX.Y.Z backend-vX.Y.Z
```

Wait for both workflows to finish. Release notes must never prevent CLI binaries, OSS uploads, backend images, GHCR manifests, or SWR manifests from being published.

### 9. Update GitHub Releases If Needed

If Actions used generated notes, generated weak notes, or did not pick up the prepared files, update manually:

```bash
gh release edit cli-vX.Y.Z \
  --repo kamusis/swissql-core \
  --notes-file release-notes/cli-vX.Y.Z.md

gh release edit backend-vX.Y.Z \
  --repo kamusis/swissql-core \
  --notes-file release-notes/backend-vX.Y.Z.md
```

For temporary notes files, use the temporary paths instead. A successful post-release edit is an acceptable completion path when artifacts were published without prepared repository notes.

### 10. Verify

Read both releases back:

```bash
gh release view cli-vX.Y.Z --repo kamusis/swissql-core --json body,url
gh release view backend-vX.Y.Z --repo kamusis/swissql-core --json body,url
```

Confirm:

- CLI release contains only CLI-facing content
- Backend release contains only backend-facing content
- Backend release includes the Docker image line
- Full changelog links use matching component tags
- Tags point to the intended commit

## GitHub Actions Contract

Required workflow behavior:

- Actions may create releases and upload artifacts.
- Actions should not be trusted to generate final human-facing notes.
- If `release-notes/${TAG}.md` exists, Actions should use it as the release body.
- If the file is missing, Actions should emit a warning and continue with GitHub-generated notes.
- Missing release notes must not fail or skip binary, OSS, container-image, GHCR, or SWR publication.
- The agent should replace generated notes before considering the release fully documented.

Suggested Actions logic:

```yaml
- name: Locate release notes
  id: notes
  run: |
    NOTES="release-notes/${GITHUB_REF_NAME}.md"
    if [[ -f "${NOTES}" ]]; then
      echo "available=true" >> "$GITHUB_OUTPUT"
      echo "path=${NOTES}" >> "$GITHUB_OUTPUT"
    else
      echo "available=false" >> "$GITHUB_OUTPUT"
      echo "::warning::Missing ${NOTES}; publishing with generated notes."
    fi

- name: Release from prepared notes
  if: steps.notes.outputs.available == 'true'
  uses: softprops/action-gh-release@v2
  with:
    body_path: ${{ steps.notes.outputs.path }}

- name: Release with generated notes
  if: steps.notes.outputs.available != 'true'
  uses: softprops/action-gh-release@v2
  with:
    generate_release_notes: true
```

## Final Report

When done, report:

- Tags created and pushed
- Commit SHA released
- CLI release URL
- Backend release URL
- Whether release notes were committed before tagging or edited directly on GitHub afterward
- Release-notes commit SHA when the repository-note path was used
- Any GitHub Actions jobs still running or failed

## Safety Rules

- Do not publish artifacts to registries manually unless the user explicitly asks.
- Do not force-push tags unless the user explicitly approves a tag rewrite.
- Do not create tags from a dirty worktree.
- Do not mix CLI-only and backend-only notes.
- Do not treat GitHub auto notes as sufficient when they obscure user-facing capabilities.
- Do not fail or cancel artifact publication solely because prepared release notes are missing.
