---
name: mopheus-sync-release
description: "Synchronize Mopheus release artifacts (multi-arch Docker images and CLI binaries) from GitHub (GHCR and GitHub Releases) to Huawei Cloud (SWR and OBS). Use whenever triggered by a release webhook or asked to sync a nightly/stable release from GitHub to Huawei Cloud."
---

# Mopheus Sync Release

Synchronize Mopheus build artifacts (container images and CLI binaries) from GitHub to Huawei Cloud deterministically.

## Overview

This skill provides `scripts/sync-github-to-huawei.sh` to mirror multi-arch Docker images from GHCR to Huawei Cloud SWR, and download CLI release assets from GitHub Releases to upload them to Huawei Cloud OBS.

## Execution

Locate and execute `sync-github-to-huawei.sh` provided in this skill's `scripts/` directory:

```bash
# Locate sync-github-to-huawei.sh from skill directory or search path
SCRIPT_PATH="$(find . "$HOME" -name "sync-github-to-huawei.sh" 2>/dev/null | head -n 1)"
if [[ -z "$SCRIPT_PATH" || ! -f "$SCRIPT_PATH" ]]; then
  SCRIPT_PATH="scripts/sync-github-to-huawei.sh"
fi

bash "$SCRIPT_PATH" \
  --tag "<tag>" \
  --version "<version>" \
  --commit "<commit_sha>"
```

### Options

- `--tag <tag>`: GitHub release tag to sync (e.g. `nightly`, `v2.2.9-beta.20260929.04c3fab4`, or `v2.2.6`). Default: `nightly`.
- `--version <version>`: Exact version string for image tags and OBS directory (e.g. `v2.2.9-beta.20260929.04c3fab4`). Defaults to `--tag`.
- `--commit <sha>`: Git commit SHA (optional).
- `--wecom-webhook <url>`: Optional WeCom webhook URL for success notification.
- `--skip-images`: Skip Docker image synchronization.
- `--skip-cli`: Skip CLI release assets synchronization.
- `--dry-run`: Test flow without pushing images to SWR or uploading assets to OBS.

### Environment & Prerequisites

- **Container Image Mirroring**: Requires `crane`, `skopeo`, or `docker` on the host, with push access to Huawei Cloud SWR (`swr.cn-north-4.myhuaweicloud.com`).
- **OBS Upload**: Requires `OBS_AK` and `OBS_SK` (or `OBS_ACCESS_KEY_ID` and `OBS_SECRET_ACCESS_KEY`).
- **CLI Download**: Uses `gh release download` (requires authenticated GitHub CLI access to `enmotech/mopheus`).
