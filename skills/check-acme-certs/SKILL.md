---
name: check-acme-certs
description: "Check SSL certificate expiration for domains managed by acme.sh on Ubuntu servers. Probes certificate validity, warns if remaining days are below threshold (default 55 days), and detects missing, broken, or unrenewed certificates."
---

# Check ACME Certificates

## Overview

Inspect the health, expiration dates, and renewal status of SSL/TLS certificates issued and maintained by `acme.sh`.

`acme.sh` triggers automatic renewal 60 days before expiration for standard 90-day certificates (Let's Encrypt / ZeroSSL). When renewal succeeds, remaining validity resets to ~90 days. If a certificate drops below 55 days remaining, automatic renewal has failed or stalled, requiring investigation.

---

## Severity & Alert Criteria

- **CRITICAL** (Requires ticket creation or alert escalation):
  - Any domain certificate has **< 55 days** remaining validity.
  - Any domain certificate is **expired** (remaining days <= 0).
  - Any certificate file in `~/.acme.sh/` fails validation or is unparseable by `openssl`.
  - The `~/.acme.sh` directory does not exist or contains zero certificates.
- **NORMAL / HEALTHY**:
  - All discovered domain certificates have **>= 55 days** remaining validity.

---

## Execution Methods

### 1. Execute Script Directly
If running on the server host where `acme.sh` is installed:

```bash
bash scripts/check-certs.sh
```

Or execute the host installation:

```bash
~/.acme.sh/check-certs.sh
```

### 2. Custom Threshold (Optional)
Override the default threshold (55 days) via `CERT_CHECK_THRESHOLD`:

```bash
CERT_CHECK_THRESHOLD=30 bash scripts/check-certs.sh
```

### 3. Output Format and Exit Codes
- **Exit Code 0**: All certificates are healthy and valid (remaining days >= 55).
- **Exit Code 1**: One or more certificates are expiring soon (< 55 days), expired, missing, or corrupted.

Standard output example (healthy):
```text
[2026-09-07 12:00:00 +0900] ✅ dev.kamusis.me 剩余 63 天, 到期=Nov  9 09:25:39 2026 GMT
[2026-09-07 12:00:00 +0900] ✅ dev.mopheus.ai 剩余 63 天, 到期=Nov  9 09:25:39 2026 GMT
✅ 检查完成: 共 2 个证书，全部正常
```

Standard output example (CRITICAL alert):
```text
[2026-09-07 12:00:00 +0900] ❌ 证书剩余天数过低: dev.mopheus.ai 还有 42 天 (阈值=55) 到期=Oct 19 09:25:39 2026 GMT
[2026-09-07 12:00:00 +0900] ❌ 检查完成: 共 2 个证书, 存在异常 (exit=1)
```

### 4. Direct OpenSSL Fallback Verification
To manually inspect a specific domain certificate:

```bash
openssl x509 -in ~/.acme.sh/<domain>_ecc/<domain>.cer -noout -dates -subject
```
