---
name: swissql-release
description: Prepare and execute SwissQL Core releases with single-component (cli-v* or backend-v*) or paired (cli-v*/backend-v*) tags, capability-oriented release notes, and GitHub Actions handoff. Use whenever releasing SwissQL Core, creating release tags, updating SwissQL release notes, or preparing release notes for the automated GitHub release workflow.
---

# SwissQL Release

Prepare and execute SwissQL Core releases with component-specific tags:

- `cli-vX.Y.Z` (CLI release)
- `backend-vX.Y.Z` (Backend container image & API release)

This skill is project-specific to `enmotech/swissql-core`. Prefer it over the generic `github-release` skill for this repository.

## Core Principle

GitHub Actions is the release executor. The agent is the release editor.

- `release-cli.yml` executes on `cli-v*` tags: compiles cross-platform CLI binaries, uploads archives to OSS, and creates the GitHub Release with attachments.
- `release-backend-image.yml` executes on `backend-v*` tags: builds multi-architecture Docker images, pushes to Huawei Cloud SWR and GHCR, and creates the GitHub Release.

Do not rely on GitHub auto-generated release notes as the preferred final release body. They often list internal commit titles and miss user-facing capabilities. Prepare component-specific notes before tags are pushed whenever possible. If prepared notes are missing, do not block artifact publication: let GitHub Actions publish with generated notes, then replace the release body afterward.

## Supported Release Shapes

SwissQL components are decoupled and support both single-component and paired releases:

### 1. Single Component Release (Recommended for targeted changes)
- **CLI-only (`cli-vX.Y.Z`)**: When changes affect only `swissql-cli/` (e.g. AI-actionable error hints, table rendering, new subcommands). Backend tag is NOT created and backend version remains unchanged.
- **Backend-only (`backend-vX.Y.Z`)**: When changes affect only `swissql-backend/` (e.g. SQL rule engine, JDBC driver loader, security filters). CLI tag is NOT created and CLI version remains unchanged.

### 2. Paired Release (Recommended for cross-cutting milestones)
- Both `cli-vX.Y.Z` and `backend-vX.Y.Z` pointing to the same `main` commit when releasing joint features (e.g. new protocol headers, isolation domain integration).
- Each GitHub Release must describe only its own component.

## Non-Negotiable Notes Separation

Write separate release notes for CLI and backend.

### CLI notes must include only CLI-facing content

Include:
- CLI commands, flags, output formatting, config (`~/.swissql/config.json`), rendering, error hints, and client behavior
- CLI fixes and user-visible CLI behavior
- CLI tests only when useful as confidence notes
- CLI full changelog link

Do not include backend-only implementation details in CLI notes (no servlet filters, Spring configuration, MDC keys, controller audit logs, or Docker images).

Example:
```markdown
## Highlights

- Added `--ticket-id` to send request correlation IDs.
- Added `--executor` to identify the caller in audit-aware requests.
```

### Backend notes must include only backend-facing content

Include:
- Docker image paths (Huawei Cloud SWR & GHCR)
- REST/API behavior, request headers, audit logs, configuration properties, persistence, SQL rules, driver management
- Backend fixes and operator-visible behavior
- Backend tests only when useful as confidence notes
- Backend full changelog link

Do not include CLI-only implementation details in backend notes. Prefer pointing to the CLI release for CLI usage.

Example:
```markdown
Docker images:
- Huawei Cloud SWR: `swr.cn-north-4.myhuaweicloud.com/mopheus/swissql-core:X.Y.Z`
- GitHub Packages (GHCR): `ghcr.io/enmotech/swissql-core:X.Y.Z`

## Highlights

- Added `X-Ticket-Id` request correlation support.
- SQL execution audit logs now include `ticket_id=...`.
```

---

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
- Target tag(s) do not already exist locally or remotely

Check tags:
```bash
# For single CLI release
git rev-parse -q --verify refs/tags/cli-vX.Y.Z
git ls-remote --tags origin cli-vX.Y.Z

# For single Backend release
git rev-parse -q --verify refs/tags/backend-vX.Y.Z
git ls-remote --tags origin backend-vX.Y.Z

# For paired release
git rev-parse -q --verify refs/tags/cli-vX.Y.Z refs/tags/backend-vX.Y.Z
git ls-remote --tags origin cli-vX.Y.Z backend-vX.Y.Z
```

### 2. Determine Release Range

Compare each component being released against its previous component tag:

```bash
# CLI range
git log --oneline cli-vPREV..HEAD

# Backend range
git log --oneline backend-vPREV..HEAD
```

Collect PR context:

```bash
gh pr list --repo enmotech/swissql-core --state merged --limit 100 \
  --json number,title,body,mergedAt,url
```

Also inspect squash commit bodies in the range:

```bash
git log --pretty='%h%n%s%n%b%n---END---' <component>-vPREV..HEAD
```

### 3. Classify Changes By Component

For each merged PR or commit, classify effects into:
- `cli`
- `backend`
- `both`
- `tests`
- `docs`
- `internal-only`

When a change is `both`, split it into component-specific descriptions.

### 4. Draft CLI Release Notes

When releasing CLI (`cli-vX.Y.Z`), use this template:

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

**Full Changelog**: https://github.com/enmotech/swissql-core/compare/cli-vPREV...cli-vX.Y.Z
```

### 5. Draft Backend Release Notes

When releasing Backend (`backend-vX.Y.Z`), use this template:

```markdown
Docker images:
- Huawei Cloud SWR: `swr.cn-north-4.myhuaweicloud.com/mopheus/swissql-core:X.Y.Z`
- GitHub Packages (GHCR): `ghcr.io/enmotech/swissql-core:X.Y.Z`

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

**Full Changelog**: https://github.com/enmotech/swissql-core/compare/backend-vPREV...backend-vX.Y.Z
```

### 6. Prepare Repository Release Notes

SwissQL has an established repository convention. Write release notes using filenames that exactly match the planned tags:

```text
release-notes/cli-vX.Y.Z.md
release-notes/backend-vX.Y.Z.md
```

Read `release-notes/README.md` and follow its conventions.
When doing a single-component release, only create the file for that component.

### 7. Commit Release Notes Before Tagging

Commit release note files to `main` before tagging:

```bash
# For CLI release only
git add release-notes/cli-vX.Y.Z.md
git commit -m "docs: add release notes for cli-vX.Y.Z"
git push origin main

# For Backend release only
git add release-notes/backend-vX.Y.Z.md
git commit -m "docs: add release notes for backend-vX.Y.Z"
git push origin main

# For Paired release
git add release-notes/cli-vX.Y.Z.md release-notes/backend-vX.Y.Z.md
git commit -m "docs: add release notes for vX.Y.Z"
git push origin main
```

Only commit release note files. Do not mix code or unrelated docs into the release-notes commit. Verify `HEAD` matches `origin/main` before creating tags.

### 8. Create Annotated Tags

Use annotated tags matching existing project style:

```bash
# For CLI release only
git tag -a cli-vX.Y.Z -m "CLI vX.Y.Z"
git push origin cli-vX.Y.Z

# For Backend release only
git tag -a backend-vX.Y.Z -m "Backend vX.Y.Z"
git push origin backend-vX.Y.Z

# For Paired release
git tag -a cli-vX.Y.Z -m "CLI vX.Y.Z"
git tag -a backend-vX.Y.Z -m "Backend vX.Y.Z"
git push origin cli-vX.Y.Z backend-vX.Y.Z
```

Wait for GitHub Actions workflows to finish:
- `Release CLI` (`.github/workflows/release-cli.yml`)
- `Release Backend Docker Image` (`.github/workflows/release-backend-image.yml`)

### 9. Update GitHub Releases If Needed

If Actions used generated notes or did not pick up the prepared files, update manually:

```bash
gh release edit cli-vX.Y.Z \
  --repo enmotech/swissql-core \
  --notes-file release-notes/cli-vX.Y.Z.md

gh release edit backend-vX.Y.Z \
  --repo enmotech/swissql-core \
  --notes-file release-notes/backend-vX.Y.Z.md
```

### 10. Verify

Read releases back:

```bash
gh release view <tag> --repo enmotech/swissql-core --json body,url
```

Confirm:
- CLI release contains only CLI-facing content
- Backend release contains only backend-facing content
- Backend release includes the SWR and GHCR Docker image references
- Full changelog links use matching component tags
- Tag points to the intended `main` commit

---

## GitHub Actions Contract

- Actions create releases and upload artifacts.
- Both workflows inspect `release-notes/${GITHUB_REF_NAME}.md`.
- If the file exists, Actions uses it as the release body (`body_path`).
- If missing, Actions publishes with generated notes and emits a warning.
- Missing release notes must not fail or skip binary, OSS, container-image, GHCR, or SWR publication.
- Release tags must be on the `origin/main` branch or the workflow will abort.

---

## Final Report

When done, report:
- Tag(s) created and pushed
- Commit SHA released
- Release URL(s)
- Whether release notes were committed before tagging or edited directly on GitHub afterward
- Any GitHub Actions jobs still running or completed
- SWR & GHCR image pull tags (for Backend releases)
