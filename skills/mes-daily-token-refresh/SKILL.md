---
name: mes-daily-token-refresh
description: Refresh the MES CLI token by logging into support.enmotech.com with stored user/password credentials and persisting the Bearer token into mes-cli configuration. Use when setting up or running automated daily token refresh jobs, renewing expired MES CLI sessions, or fixing 401 unauthorized errors in automated environments.
---

# MES Daily Token Refresh

## Overview

Automate the scheduled or on-demand renewal of the `mes-cli` Bearer authentication token by logging into the MES backend (`support.enmotech.com`) with user and password credentials, and writing the returned Bearer token into the target `mes-cli` profile.

This ensures downstream automated tasks, reports, and agent operations do not fail due to session expiration.

---

## Directory Structure

```text
mes-daily-token-refresh/
├── SKILL.md
└── scripts/
    └── refresh_mes_token.sh    # Executable shell script for token login & verification
```

---

## Prerequisites & Dependencies

1. **`mes-cli`**: Installed and accessible on `$PATH` (e.g., in `~/.local/bin/mes`).
2. **System tools**: `curl`, `awk`, `bash`.
3. **Credentials file**: Stored securely with permissions `600`.

---

## Credential Configuration

The script resolves credentials in the following order:

1. Environment variables (`MES_USER` and `MES_PASSWORD`). *(For backward compatibility, `MES_PHONE` is also accepted as an alias for `MES_USER`).*
2. Custom file path passed via `MES_ENV_FILE`.
3. Default path: `~/.mes/token.env`.

### Setting Up the Credentials File

Create `~/.mes/token.env` with restricted permissions:

```bash
cat <<'EOF' > ~/.mes/token.env
MES_USER="<your-user-account-or-phone>"
MES_PASSWORD="<your-password>"
EOF
chmod 600 ~/.mes/token.env
```

---

## How to Use

### 1. Manual Execution

Run the script directly from the skill directory:

```bash
bash scripts/refresh_mes_token.sh
```

Or execute with explicit environment variables:

```bash
MES_USER="<user>" MES_PASSWORD="<password>" bash scripts/refresh_mes_token.sh
```

### 2. Optional Environment Overrides

- `MES_PROFILE`: Target profile in `~/.mes/config.yaml` (default: `kamus`).
- `MES_HOST_BASE`: Base URL for login (default: `https://support.enmotech.com`).
- `MES_ENV_FILE`: Custom path to the `.env` credentials file.

Example with custom profile:
```bash
MES_PROFILE="dev" bash scripts/refresh_mes_token.sh
```

### 3. Automated Scheduled Task (Cron)

To refresh the token automatically every day at 09:00:

```bash
crontab -e
```

Add the entry:

```cron
# Refresh MES CLI token daily at 09:00
0 9 * * * /path/to/mes-daily-token-refresh/scripts/refresh_mes_token.sh >> ~/.mes/logs/token_refresh.log 2>&1
```

*(The script automatically detects `~/.mes/token.env` if present).*

---

## Verification

Check that the token was written and is recognized by `mes-cli`:

```bash
mes auth status
```

Expected output:
```text
Active profile: kamus
Host: https://support.enmotech.com/esapi
Status: Logged in (token saved).
```

Or in JSON format:
```bash
mes -o json auth status
```

Verify that `"tokenValid": true` is returned.

---

## Exit Codes & Diagnostics

| Exit Code | Meaning | Troubleshooting |
|:---:|:---|:---|
| `0` | Success | Token refreshed and verified via `mes auth status`. |
| `1` | Login HTTP error | Backend returned non-200. Check user credentials in `~/.mes/token.env`. |
| `2` | Missing Bearer token | Response header did not contain a valid `Authorization: Bearer <JWT>`. |
| `3` | Verification failure | Token was saved to profile, but `mes auth status` reported `tokenValid: false`. |
| `4` | Dependency / Credential missing | `mes`, `curl`, `awk` not on PATH, or credentials unset / unreadable. |
