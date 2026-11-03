#!/usr/bin/env bash
# doctor.sh — Read-only health and readiness probe for Mopheus preview instance.
# Exit code 0: Healthy and ready to drive.
# Exit code 1: Not ready or component degraded.

set -euo pipefail

BACKEND_URL="${MOPHEUS_BACKEND_URL:-http://localhost:8230}"
FRONTEND_URL="${MOPHEUS_FRONTEND_URL:-http://localhost:3230}"
TEST_EMAIL="${MOPHEUS_TEST_EMAIL:-alice@mopheus.dev}"
TEST_PASSWORD="${MOPHEUS_TEST_PASSWORD:-Mopheus@123}"

echo "==> [verify-mopheus] Running doctor check against preview environment..."

# 1. Backend Health Check
if curl -sf --max-time 3 "${BACKEND_URL}/api/v1/health" >/dev/null 2>&1; then
  echo "[✓] Backend API: ${BACKEND_URL} (HTTP 200)"
else
  echo "[✗] Backend API: ${BACKEND_URL} unreachable or unhealthy" >&2
  exit 1
fi

# 2. Frontend Health Check
if curl -sf --max-time 3 "${FRONTEND_URL}/login" >/dev/null 2>&1; then
  echo "[✓] Frontend Web: ${FRONTEND_URL} (HTTP 200)"
else
  echo "[✗] Frontend Web: ${FRONTEND_URL} unreachable" >&2
  exit 1
fi

# 3. Auth Check
LOGIN_RESP=$(curl -sf --max-time 5 -X POST "${BACKEND_URL}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${TEST_EMAIL}\",\"password\":\"${TEST_PASSWORD}\"}" 2>/dev/null || true)

SUCCESS=$(echo "${LOGIN_RESP}" | jq -r '.success // false' 2>/dev/null || echo "false")
TOKEN=$(echo "${LOGIN_RESP}" | jq -r '.data.accessToken // .data.token // empty' 2>/dev/null || true)

if [ "${SUCCESS}" = "true" ] && [ -n "${TOKEN}" ]; then
  echo "[✓] Auth Service: Authenticated as ${TEST_EMAIL}"
else
  echo "[✗] Auth Service: Failed to authenticate as ${TEST_EMAIL}" >&2
  exit 1
fi

# 4. Workspace Check (dev-space scopes)
SCOPES_RESP=$(curl -sf --max-time 5 "${BACKEND_URL}/api/v1/workspaces/dev-space/my-scopes" \
  -H "Authorization: Bearer ${TOKEN}" 2>/dev/null || true)
SCOPES_OK=$(echo "${SCOPES_RESP}" | jq -r '.success // false' 2>/dev/null || echo "false")

if [ "${SCOPES_OK}" = "true" ]; then
  echo "[✓] Workspace Check: Resolved 'dev-space' and verified member scopes"
else
  echo "[✗] Workspace Check: Could not resolve 'dev-space' workspace" >&2
  exit 1
fi

# 5. Playwright Screenshot Driver Check
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREVIEW_SCREENSHOT_TOOL="${HOME}/.gemini/config/skills/mopheus-integration-preview/scripts/preview_screenshot.js"

if [ -f "${PREVIEW_SCREENSHOT_TOOL}" ] && command -v node >/dev/null 2>&1; then
  echo "[✓] Browser Driver: preview_screenshot.js available"
else
  echo "[✗] Browser Driver: preview_screenshot.js or node missing" >&2
  exit 1
fi

echo "==> [verify-mopheus] Preview instance is HEALTHY and ready to be driven."
exit 0
