---
name: mopheus-release
description: Release Mopheus from its long-lived release branch by validating a user-supplied SemVer tag, compiling complete English release notes from all important changes since the prior release, tagging the selected release commit from main history, triggering and monitoring the repository release workflow, and replacing workflow-generated notes after the workflow finishes. Use whenever the user asks to release, publish, tag, prepare release notes for, or finalize a Mopheus version, including when they explicitly mention mopheus-release. The GitHub repository or local folder may still be named moclaw; product naming must remain Mopheus.
compatibility: Requires git, Python 3, GitHub CLI access, and a repository with origin/main, origin/release, and .github/workflows/release.yml.
---

# Mopheus Release

Release Mopheus by creating one validated tag on the selected `release` commit. The tag wakes the repository's GitHub Actions workflow. Treat the workflow as opaque; observe only its run state and the GitHub Release it creates.

## Responsibilities

This skill owns only:

- validating an explicit release version;
- verifying the `release` commit belongs to `main` history;
- finding the correct previous release boundary;
- inventorying every change in the release range;
- drafting accurate, useful release notes in English;
- creating and pushing the annotated tag on the verified release commit;
- waiting for the tag-triggered workflow to finish;
- replacing the workflow-generated GitHub Release notes after the workflow succeeds;
- verifying that the final GitHub Release contains the prepared notes.

Do not run `gh release create`; the workflow creates the GitHub Release.

## Product and repository naming

Use **Mopheus** in release titles and prose. Do not infer the product name from the repository directory or GitHub repository name. The repository may still be named `moclaw`, and a future repository rename must not change this workflow.

Derive the GitHub owner/repository from the current checkout rather than hard-coding it.

## Required input

Require an explicit version such as `v2.2.0` or `v2.2.0-rc.1`.

- If the user did not provide a version, ask for it and stop.
- Do not recommend, infer, or increment a version.
- Reject malformed SemVer, an existing tag, a version that is not newer than the latest reachable release tag, or a version that disagrees with the repository's base version.
- Never move, recreate, or overwrite an existing tag.

Run the bundled validator before preparing the release and again immediately before tagging:

```bash
python3 <skill-directory>/scripts/validate_release.py <version>
```

The validator prints JSON containing `version`, `releaseSha`, `previousTag`, `latestTag`, and `sourceVersion`. Treat any nonzero exit as a hard stop.

## Release branch invariant

Fetch current remote state before every decision. A release is eligible only when:

```text
git merge-base --is-ancestor origin/release origin/main
```

`release` may equal `main` or intentionally lag behind it. This supports selecting a known-good commit from an earlier `main` state while newer commits continue to drive nightly builds.

If `release` is not an ancestor of `main`, stop and report both SHAs. The branches have diverged, so release boundaries are ambiguous. Synchronizing for a release means fast-forwarding `release` to an explicitly selected commit from `main`; never squash `main` into `release`, because squash creates a different commit history. Do not merge branches, rebase branches, reset branches, or force-push as part of this skill.

Tag the exact `releaseSha` returned by the final validator run. Do not rely on whichever branch happens to be checked out.

## Previous release boundary

Only consider valid `v`-prefixed SemVer tags reachable from `releaseSha`.

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

Save the final notes outside the repository worktree, preferably in a directory created with `mktemp -d`. Preserve that file until final verification succeeds.

## Execution workflow

### 1. Preflight

- Confirm the worktree is clean.
- Confirm `origin`, `main`, `release`, and `.github/workflows/release.yml` exist.
- Determine the repository identity from the checkout.
- Verify the GitHub CLI identity has access to the repository without printing credentials.
- Run the validator and capture its JSON output.

If the user asked only to prepare or draft release notes, stop after presenting the notes and validation summary. Do not create or push a tag.

An explicit request to release, publish, or tag the supplied version authorizes the tag push. Do not ask for redundant confirmation after all preflight checks pass.

### 2. Verify

Run the repository's complete required check from the verified release source:

```bash
make check
```

Do not tag if verification fails. Report the exact failing command and preserve the prepared notes.

### 3. Revalidate and tag

Remote branches may move while notes and checks are prepared. Run the validator again and require the same `releaseSha` used for the notes and verification.

Create an annotated tag on that explicit SHA, then push only the tag:

```bash
git tag -a <version> <releaseSha> -m "<version>"
git push origin refs/tags/<version>
```

Never push a branch, use force, or change the version file as part of release execution.

### 4. Wait for the workflow

Find the run from `.github/workflows/release.yml` whose event is `push`, tag ref is `<version>`, and `headSha` equals `releaseSha`. Do not select a run by recency alone.

Wait for the matching run with `gh run watch <run-id> --exit-status`. If the run fails, stop without creating or editing a GitHub Release. Report the run URL and keep the notes file for recovery.

If multiple attempts exist for the same tag and SHA, wait until no matching run is queued or in progress, then require the latest attempt to have conclusion `success`.

Provide concise progress updates while a long workflow is running.

### 5. Replace workflow-generated notes

The workflow owns initial GitHub Release creation, so wait for the workflow to succeed before touching release notes. Then:

1. Poll `gh release view <version>` with a bounded timeout until the release exists.
2. Run `gh release edit <version> --title <version> --notes-file <notes-file> --verify-tag`.
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
- Source version mismatch: report the requested version and `server/pkg/version/version.go` value; do not edit either.
- Verification failure: report the failing check; do not tag.
- Tag push succeeds but workflow fails: report the tag and failed run; do not create or rewrite a release.
- Workflow succeeds but release is delayed: retry bounded polling, then report a timeout with the notes file preserved.
- Notes verification fails: report the actual release URL and missing marker; do not claim completion.

## Command reference

Read [references/command-templates.md](references/command-templates.md) before executing a release. Use the templates as patterns, substituting values only after validation.
