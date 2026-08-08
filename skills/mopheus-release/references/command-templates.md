# Mopheus release command templates

Use these as patterns after `scripts/validate_release.py` succeeds. Prefer `gh-wrapper` when repository instructions require it and it selects the authorized repository credential; otherwise use an explicitly authenticated `gh` command without exposing token values.

## Resolve repository identity

```bash
gh repo view --json nameWithOwner --jq .nameWithOwner
gh api user --jq .login
```

## Validate the requested version

```bash
python3 <skill-directory>/scripts/validate_release.py <version>
```

## Inspect the release range

```bash
git log --first-parent --format='%H%x09%s' <previous-tag>..<release-sha>
git log --format='%H%x09%s' <previous-tag>..<release-sha>
git diff --stat <previous-tag>..<release-sha>
git diff --name-status <previous-tag>..<release-sha>
```

For a first release, omit `<previous-tag>..` and inspect the full history reachable from `<release-sha>`.

## Verify release ancestry

```bash
git merge-base --is-ancestor origin/release origin/main
```

Exit status `0` means `release` is a valid commit in `main` history. `main` may be ahead. Any nonzero result blocks the release until the histories are reconciled without squash merging.

## Create and push the tag

```bash
git tag -a <version> <release-sha> -m "<version>"
git push origin refs/tags/<version>
```

## Locate the exact workflow run

```bash
gh run list \
  --workflow release.yml \
  --branch <version> \
  --commit <release-sha> \
  --event push \
  --limit 10 \
  --json databaseId,headBranch,headSha,status,conclusion,url,createdAt
```

Select a run only when both `headBranch == <version>` and `headSha == <release-sha>`.

## Wait for workflow completion

```bash
gh run watch <run-id> --compact --exit-status
```

After it exits, list matching runs again. Do not write release notes while another matching attempt is queued or in progress.

## Wait for the workflow-created release

```bash
gh release view <version> --json tagName,url,body
```

Retry with a short bounded interval only after the workflow has completed successfully.

## Replace and verify release notes

```bash
gh release edit <version> \
  --title <version> \
  --notes-file <notes-file> \
  --verify-tag

gh release view <version> --json body,url
```

Verify that the returned body contains:

```text
<!-- mopheus-release-notes:<version> -->
```

## Commands intentionally excluded

Do not use these in this skill:

```text
gh release create
git push --force
git tag --force
git push origin main
git push origin release
```
