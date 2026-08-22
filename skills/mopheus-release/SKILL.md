---
name: mopheus-release
description: Release Mopheus from the fixed enmotech/mopheus GitHub repository and its long-lived release branch by validating a user-supplied SemVer tag, compiling complete release notes, updating the source version and bilingual documentation changelog in one verified preparation commit, tagging that commit, monitoring the release workflow, and replacing workflow-generated GitHub notes. Use whenever the user asks to release, publish, tag, prepare release notes for, or finalize a Mopheus version, including when they explicitly mention mopheus-release.
compatibility: Requires git, Python 3, GitHub CLI access, and a repository with origin/main, origin/release, and .github/workflows/release.yml.
---

# Mopheus Release

Release Mopheus by preparing one versioned commit on `main`, fast-forwarding `release` to that exact commit, and creating one validated tag there. The preparation commit owns both the source version and the bilingual documentation changelog. The tag wakes the repository's GitHub Actions workflow. Treat the workflow as opaque; observe only its run state and the GitHub Release it creates.

## Responsibilities

This skill owns only:

- validating an explicit release version;
- updating `server/pkg/version/version.go` to the requested SemVer core version;
- updating `install/env.example` so `MOPHEUS_IMAGE_TAG` equals that version;
- verifying the `release` commit belongs to `main` history;
- finding the correct previous release boundary;
- inventorying every change in the release range;
- drafting accurate, useful release notes in English;
- updating `packages/docs-content/en/releases/changelog.md` and `packages/docs-content/zh-Hans/releases/changelog.md` from the same release inventory;
- creating and pushing one `chore(release): prepare <version>` commit on `main`;
- fast-forwarding `release` to that exact commit without merging, rebasing, resetting, or force-pushing;
- creating and pushing the annotated tag on the verified release commit;
- waiting for the tag-triggered workflow to finish;
- replacing the workflow-generated GitHub Release notes after the workflow succeeds;
- verifying that the final GitHub Release contains the prepared notes.

Do not run `gh release create`; the workflow creates the GitHub Release.

## Product and repository naming

Use **Mopheus** in release titles and prose. Do not infer the product name from the local repository directory.

The GitHub repository is fixed to `enmotech/mopheus`; its canonical repository URL is `https://github.com/enmotech/mopheus.git`. Pass `--repo enmotech/mopheus` to every GitHub CLI command. Require `origin` to identify that repository through an accepted HTTPS or SSH URL before any write. The checkout and `origin` are validation and Git transport inputs only; never derive or override the GitHub operation target from them.

## Required input

Require an explicit version such as `v2.2.0` or `v2.2.0-rc.1`.

- If the user did not provide a version, ask for it and stop.
- Do not recommend, infer, or increment a version.
- Reject malformed SemVer, an existing tag, or a version that is not newer than the latest reachable release tag.
- Never move, recreate, or overwrite an existing tag.

The bundled validator requires both the repository base version and install image tag to already equal the requested version. Run it after the preparation commit has updated them, and again immediately before tagging:

```bash
python3 <skill-directory>/scripts/validate_release.py <version>
```

The validator prints JSON containing `version`, `releaseSha`, `previousTag`, `latestTag`, `sourceVersion`, and `installImageTag`. Treat any nonzero exit after the preparation commit as a hard stop. Before modifying files, perform equivalent read-only preflight checks for SemVer syntax, tag absence, version ordering, branch ancestry, and repository identity; expected source-version or install-image-tag mismatches are not blockers because this skill now owns those updates.

## Release branch invariant

Fetch current remote state before every decision. A release is eligible only when:

```text
git merge-base --is-ancestor origin/release origin/main
```

At preflight, `release` may equal `main` or lag behind it, but it must be an ancestor of `main`. The release preparation commit is created on the current clean `main`, then `release` is fast-forwarded to that exact commit.

If `release` is not an ancestor of `main`, stop and report both SHAs. The branches have diverged, so release boundaries are ambiguous. Synchronizing for a release means fast-forwarding `release` to an explicitly selected commit from `main`; never squash `main` into `release`, because squash creates a different commit history. Do not merge branches, rebase branches, reset branches, or force-push as part of this skill.

Tag the exact `releaseSha` returned by the final validator run. Do not rely on whichever branch happens to be checked out.

## Previous release boundary

Only consider valid `v`-prefixed SemVer tags reachable from the selected pre-preparation `main` commit and, after preparation, from `releaseSha`.

- For a stable target such as `v2.2.0`, use the newest reachable stable tag as `previousTag`.
- For a prerelease target such as `v2.2.0-rc.2`, use the newest reachable prerelease with the same `v2.2.0` core. If none exists, use the newest reachable stable tag.
- For the first release, use the repository root as the range start.

The bundled validator applies these rules. Do not replace its result with a globally newest tag that is not reachable from `release`.

## Build a complete change inventory

Release notes are the primary human-facing output. Build them before creating the tag.

1. Inspect every commit in `previousTag..releaseSha`, or every commit reachable from `releaseSha` for the first release.
2. Inspect first-parent history to identify merged change units while retaining the full commit list as the completeness check.
3. Retrieve associated GitHub PR titles, bodies, labels, and issue links where available.
4. Inspect the actual diff for ambiguous, security-sensitive, migration-related, or user-visible changes. Do not rely only on commit titles.
5. Create an internal coverage ledger mapping every commit or PR to either:
   - a published release-note section; or
   - an explicit exclusion reason such as test-only, internal refactor, release plumbing, or duplicate merge metadata.
6. Reconcile the ledger before finalizing the notes. No important change may be silently omitted.

Treat fixes, features, security changes, compatibility changes, migrations, operational changes, and meaningful performance work as important. Include documentation or test work only when it changes user expectations, prevents a regression worth calling out, or explains a release risk.

## Release note format

GitHub is an international community platform, so write release notes in English.

Start every notes file with an invisible ownership marker:

```markdown
<!-- mopheus-release-notes:<version> -->
```

Then use the smallest relevant subset of these sections:

```markdown
## Highlights

## Added

## Changed

## Fixed

## Security

## Breaking Changes

## Upgrade Notes

## Full Changelog
```

Guidelines:

- Lead with user impact, not implementation mechanics.
- Group duplicate commits and follow-up fixes into one accurate item.
- Link PRs or issues when verified; never invent identifiers.
- Include breaking changes and required operator actions prominently.
- Omit empty sections.
- End with a compare link from `previousTag` to `<version>` when a previous tag exists.
- Do not publish the internal coverage ledger unless the user requests it.

Save the final GitHub notes outside the repository worktree, preferably in a directory created with `mktemp -d`. Preserve that file until final verification succeeds.

## Documentation changelog

The documentation changelog is part of the release artifact, not a follow-up task.

- Update both `packages/docs-content/en/releases/changelog.md` and `packages/docs-content/zh-Hans/releases/changelog.md` in the preparation commit.
- Insert the new release first, immediately below each changelog introduction, using the release date in `YYYY-MM-DD` form.
- Derive both entries from the same complete inventory and coverage ledger as the GitHub notes. Keep scope and facts aligned, while writing natural English and Simplified Chinese rather than mechanically copying one language.
- Preserve each page's established headings and compact product-facing style. The changelog may be more concise than the GitHub Release, but every GitHub Highlight and every upgrade action must be represented in both locale entries.
- Link verified PRs where helpful and do not include the invisible GitHub ownership marker in documentation.
- Treat a missing locale update, mismatched version/date, or omitted upgrade requirement as a release blocker.

## Execution workflow

### 1. Preflight and inventory

- Confirm the worktree is clean.
- Confirm `origin`, `main`, `release`, and `.github/workflows/release.yml` exist.
- Require the checkout and `origin` to identify `enmotech/mopheus`.
- Verify the GitHub CLI identity has access to the repository without printing credentials.
- Validate the requested SemVer syntax, confirm the tag does not exist locally or remotely, and confirm it is newer than the latest reachable stable/prerelease boundary using the same rules as the validator.
- Record the current source version; it is expected to differ before a new release and will be updated by this workflow.
- Select the current `origin/main` as the preparation base, determine the previous release boundary reachable from it, and build the complete change inventory and coverage ledger before changing files.
- Draft the final English GitHub Release Notes in a temporary directory.

If the user asked only to prepare or draft release notes, stop after presenting the notes and validation summary. Do not create or push a tag.

An explicit request to release, publish, or tag the supplied version authorizes the preparation commit, pushes to `main` and `release`, and the tag push. Do not ask for redundant confirmation after all preflight checks pass.

### 2. Prepare the release commit

1. Update `server/pkg/version/version.go` to the requested base version and `install/env.example` so `MOPHEUS_IMAGE_TAG` equals the complete requested version, including any prerelease suffix.
2. Add the new version entry to both documentation changelog locales from the same inventory used for the temporary GitHub notes.
3. Confirm only the source version, install environment example, and two changelog files changed unless another repository-defined release metadata file is explicitly required.
4. Run the repository's complete required check from this final working tree:

```bash
make check
```

5. Do not commit or tag if verification fails. Report the exact failing command and preserve the prepared notes.
6. Create one commit named `chore(release): prepare <version>` and push it to `main` without force.
7. Verify local `main` and `origin/main` resolve to the same preparation commit.

### 3. Fast-forward release, revalidate, and tag

Fetch again and stop if `origin/main` moved away from the verified preparation commit. Require the old `origin/release` to remain an ancestor of that commit, then fast-forward it by pushing the explicit preparation SHA to `refs/heads/release`. Verify `origin/main` and `origin/release` now equal the same SHA.

Run the bundled validator and require `releaseSha` to equal the preparation commit, `sourceVersion` to equal the requested SemVer core, `installImageTag` to equal the complete requested version, and `previousTag` to equal the boundary used for the notes. Fetch once more and repeat the validator immediately before tagging; every value must remain unchanged.

Create an annotated tag on that explicit SHA, then push only the tag:

```bash
git tag -a <version> <releaseSha> -m "<version>"
git push origin refs/tags/<version>
```

After the verified preparation commit has been pushed to `main` and fast-forwarded to `release`, do not push any additional branch, use force, or change release files. Push only the new tag.

### 4. Wait for the workflow

Find the run from `.github/workflows/release.yml` whose event is `push`, tag ref is `<version>`, and `headSha` equals `releaseSha`. Do not select a run by recency alone.

Wait for the matching run with `gh run watch <run-id> --repo enmotech/mopheus --exit-status`. If the run fails, stop without creating or editing a GitHub Release. Report the run URL and keep the notes file for recovery.

If multiple attempts exist for the same tag and SHA, wait until no matching run is queued or in progress, then require the latest attempt to have conclusion `success`.

Provide concise progress updates while a long workflow is running.

### 5. Replace workflow-generated notes

The workflow owns initial GitHub Release creation, so wait for the workflow to succeed before touching release notes. Then:

1. Poll `gh release view <version> --repo enmotech/mopheus` with a bounded timeout until the release exists.
2. Run `gh release edit <version> --repo enmotech/mopheus --title <version> --notes-file <notes-file> --verify-tag`.
3. Read the release body back from GitHub.
4. Require the exact `<!-- mopheus-release-notes:<version> -->` marker and the expected section content.
5. Check once more that no matching workflow attempt is still active.

This ordering prevents GoReleaser's initial simple notes from overwriting the curated notes. Never edit the notes before the workflow finishes, and never race `gh release create` against the workflow.

If final verification does not find the marker, retry `gh release edit` only after confirming all matching workflow attempts are complete. If the marker is still absent, stop and report the mismatch rather than claiming success.

## Completion report

Report:

- version;
- previous release tag or first-release status;
- tagged commit SHA;
- workflow run URL and successful conclusion;
- GitHub Release URL;
- confirmation that the curated-notes marker was verified;
- the release note text or a concise section summary.

Do not report release success merely because the tag push succeeded.

## Failure handling

- Missing version: ask for an explicit `v`-prefixed SemVer.
- Existing version: report the existing tag and release URL when available; do not mutate it.
- Diverged branches: report both remote SHAs and stop when `release` is not an ancestor of `main`.
- Source version mismatch after the preparation commit: report the requested version and `server/pkg/version/version.go` value; do not tag.
- Install image tag mismatch after the preparation commit: report the requested version and `install/env.example` value; do not tag.
- Changelog mismatch: report the missing locale, version, date, highlight, or upgrade note; do not commit or tag.
- Main moved after verification: report the verified preparation SHA and current `origin/main`; do not advance `release` or tag.
- Verification failure: report the failing check; do not tag.
- Tag push succeeds but workflow fails: report the tag and failed run; do not create or rewrite a release.
- Workflow succeeds but release is delayed: retry bounded polling, then report a timeout with the notes file preserved.
- Notes verification fails: report the actual release URL and missing marker; do not claim completion.

## Command reference

Read [references/command-templates.md](references/command-templates.md) before executing a release. Use the templates as patterns, substituting values only after validation.
