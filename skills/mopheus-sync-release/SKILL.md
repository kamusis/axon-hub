---
name: mopheus-sync-release
description: "Synchronize Mopheus release artifacts (multi-arch Docker images and CLI binaries) from GitHub (GHCR and GitHub Releases) to Huawei Cloud (SWR and OBS). Use whenever triggered by a release sync flow or asked to sync a nightly/stable release from GitHub to Huawei Cloud."
---

# Mopheus Sync Release

Synchronize Mopheus build artifacts (container images and CLI binaries) from GitHub to Huawei Cloud deterministically.

## Overview

This skill provides `scripts/sync-github-to-huawei.sh` to mirror multi-arch Docker images from GHCR to Huawei Cloud SWR, and download CLI release assets from GitHub Releases to upload them to Huawei Cloud OBS.

### Upload path

`crane copy` cannot be used for the image mirror: it streams every layer over a
single connection, and SWR aborts long-lived upload connections on this link,
so the 17-24 MiB binary layers always fail with
`PROTOCOL_ERROR / unexpected EOF`. The script therefore pushes the layers
itself:

- `scripts/swr_sync_image.sh` walks the manifest list, HEADs every layer on
  SWR, uploads only the missing ones and then pushes the manifests.
- `scripts/swr_push_blob.sh` uploads one blob. Blobs up to ~6 MiB use the
  chunked session flow; larger blobs use a single PUT, because an SWR upload
  session rejects more than ~6 MiB in total (`DIGEST_INVALID`).

Blobs are content-addressed, so a re-run only pushes what is still missing.

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

- `--tag <tag>`: GitHub release tag to sync (e.g. `nightly`, `v2.2.9-beta.20260929.04c3fab4`, or `v2.2.9`). Default: `nightly`.
- `--version <version>`: Exact version string for image tags and OBS directory (e.g. `v2.2.9-beta.20260929.04c3fab4`). Defaults to `--tag`.
- `--commit <sha>`: Git commit SHA (optional).
- `--skip-images`: Skip Docker image synchronization.
- `--skip-cli`: Skip CLI release assets synchronization.
- `--dry-run`: Test flow without pushing images to SWR or uploading assets to OBS.

### Environment & Prerequisites

- **Container Image Mirroring**: Requires `crane`, `skopeo`, or `docker` on the host, with push access to Huawei Cloud SWR (`swr.cn-north-4.myhuaweicloud.com`).
- **SWR Credentials**: `HUAWEICLOUD_SWR_USER` and `HUAWEICLOUD_SWR_PASSWORD` (or `SWR_USER` / `SWR_PASSWORD`). The upload sessions need a Bearer token from `/swr/auth/v2/registry/auth/`; Basic auth is not accepted on the blob upload path.
- **OBS Upload**: Requires `OBS_AK` and `OBS_SK` (or `OBS_ACCESS_KEY_ID` and `OBS_SECRET_ACCESS_KEY`).
- **CLI Download**: Uses `gh release download` (requires authenticated GitHub CLI access to `enmotech/mopheus`).

### Tunables

| Variable | Default | Meaning |
|---|---|---|
| `SWR_UPLOAD_JOBS` | `4` | Layers uploaded in parallel. Keep it low on a slow link. |
| `SWR_MONOLITHIC_THRESHOLD` | `6291456` | Blobs larger than this are uploaded with a single PUT. |
| `SWR_CHUNK_SIZE` | `262144` | Chunk size for the chunked path. |
| `SWR_UPLOAD_TIMEOUT` | `3600` | Per-blob upload timeout in seconds. |
| `OBS_UPLOAD_JOBS` | `4` | OBS assets uploaded in parallel. |
| `OBS_UPLOAD_TIMEOUT` | `1800` | Per-asset upload timeout in seconds. |
