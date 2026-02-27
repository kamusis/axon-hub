---
name: git-release
description: Create consistent releases and changelogs
license: MIT
compatibility: opencode
metadata:

  audience: maintainers

  workflow: github
---
## What I do

- Draft release notes from merged PRs
- Propose a version bump
- Provide a copy-pasteable `gh release create` command

## What I need from you

### Required

- Repo and target branch (usually `main` or `master`)
- The release scope
  - New release from the latest state of the target branch, or
  - Release from a specific commit / tag range

### Optional (but recommended)

- Versioning scheme
  - SemVer (`vMAJOR.MINOR.PATCH`) with a required `v` prefix (example: `v0.2.0`)
  - Pre-releases use SemVer prerelease suffixes: `-rc.1`, `-beta.1`, `-alpha.1` (example: `v0.2.0-rc.1`)
- Release target
  - GitHub Release only, or also:
    - NPM / PyPI / container images
    - a `CHANGELOG.md` update in-repo

## Questions I will ask (if unclear)

- What is the current latest released version tag (example: `v0.2.0`)?
- What version bump do you want: **major**, **minor**, or **patch**?
- Should this be a pre-release (example: `v0.2.0-rc.1`)?
- Any sections you want in notes (example: Breaking Changes / Security / Migration)?

## Workflow

### 1) Identify the candidate range

- Determine the previous release tag (the most recent version tag)
- Determine the head commit to release (usually the latest on the target branch)
- Collect merged PRs and notable commits in that range

### 2) Draft release notes

I will produce release notes in a structured format you can paste into GitHub.

Default sections:

- **Highlights**
- **Added**
- **Changed**
- **Fixed**
- **Dependencies** (if relevant)
- **Breaking Changes** (only if applicable)
- **Upgrade Notes** (only if applicable)

### 3) Propose a version bump

If you use SemVer, I will propose:

- **Major**: breaking API changes
- **Minor**: new features, backwards compatible
- **Patch**: bug fixes and small changes

If I cannot infer the bump safely from the PR titles, I will ask you to choose.

### 4) Provide commands to create the release

I will output a copy-pasteable `gh` command (and optional helper commands) based on your choices.

## Output format (what you will get)

- Proposed version tag (example: `v1.5.0`)
- Release title (example: `v1.5.0`)
- Release notes markdown
- Copy-pasteable commands

## Command templates

You can use these directly, or I will tailor them for your repo.

### List tags (find latest)

```bash
git tag --list
git tag --list "v*" --sort=-version:refname | head -n 20
```

### Generate notes from GitHub (auto)

```bash
gh release create <tag> \
  --target <branch-or-sha> \
  --generate-notes
```

### Create release with custom notes

```bash
gh release create <tag> \
  --target <branch-or-sha> \
  --title "<title>" \
  --notes "<notes>"
```

### Pre-release

```bash
gh release create <tag> \
  --target <branch-or-sha> \
  --title "<title>" \
  --notes "<notes>" \
  --prerelease
```

### Attach assets (optional)

```bash
gh release create <tag> \
  --target <branch-or-sha> \
  --title "<title>" \
  --notes "<notes>" \
  dist/*
```

## When to use me
Use this when you are preparing a tagged release.

Ask clarifying questions if the target versioning scheme is unclear.

## What I will not do

- I will not publish artifacts to registries (NPM/PyPI/Docker) unless you explicitly ask.
- I will not mutate your repo history; I will only suggest commands and release text.
