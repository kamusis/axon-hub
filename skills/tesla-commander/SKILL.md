---
name: tesla-commander
description: Comprehensive vehicle control, state monitoring, AI-powered navigation (Vertex AI + OpenStreetMap fallback), charging management, and live Fleet Telemetry streaming for Tesla vehicles via Tessie API. Use when user wants to check Tesla status (battery, range, tire pressure, location), control vehicle functions (lock/unlock, honk, flash, frunk/trunk, windows, climate, seat heating, sentry mode), set navigation destinations from natural language in Japan or globally, manage charging (current, limit, start/stop), stream live telemetry data, or inspect driving/charging analytics.
---

# Tesla Commander Skill

## Overview

Tesla Commander connects directly to Tesla vehicles via the Tessie platform (REST API + WebSocket Fleet Telemetry) and Google Vertex AI (`gemini-3.8-flash`) for natural-language spatial reasoning and direct in-car navigation.

The skill provides:
1. **Instant Vehicle Status**: Battery SOC, rated range, cabin/ambient temperature, tire pressures (bar), lock & sentry state, odometer.
2. **AI-Powered Japanese / Global Navigation**: Resolves colloquial or multi-language destination queries (Chinese, Japanese, English) into exact physical coordinates and Japanese addresses using Vertex AI `gemini-3.8-flash` (with automatic fallback to OpenStreetMap Nominatim), and pushes directly to Tesla navigation (`locale=ja-JP`).
3. **Smart Climate & Comfort**: Cabin preconditioning, target temperature adjustment, seat heating/cooling, defrost, and steering wheel heater.
4. **Charging Management**: Charge limit adjustment, current (amps) regulation, charging start/stop, and charge port control.
5. **Hardware Controls & Guardrails**: Horn, headlights flash, door locks, front trunk (Frunk), rear trunk, windows venting/closing, sentry mode toggle.
6. **Live Telemetry Stream**: WebSocket listener for real-time battery voltage, charging power, speed, GPS coordinates, and vehicle alert events.
7. **Analytics**: Driving logs, charging sessions, and battery health degradation curves.

---

## Environment Variables

The CLI automatically resolves the following environment variables across all environments (from the active process environment, local `.env` file, or user shell configuration files such as `~/.zshenv`, `~/.zshrc`, `~/.bashrc`, `~/.bash_profile`, `~/.profile`, or `~/.config/fish/config.fish`):
- `TESSIE_ACCESS_TOKEN` (Required): Tessie developer access token.
- `VERTEX_API_KEY` (Optional): Google Vertex AI API Key for `gemini-3.8-flash` destination extraction. If missing or encountering errors, the system automatically falls back to OpenStreetMap Nominatim.
- `MY_TESLA_VIN` (Optional): Specific default VIN to skip vehicle auto-discovery.

---

## CLI Location & Usage

The executable is located in the skill's `scripts/` directory:
- When running from inside this skill directory: `python3 scripts/tesla_cli.py <command>`
- When running from a standalone project clone: `python3 tesla_cli.py <command>`

### 1. Status & Location

```bash
# Complete summary (Battery, Range, HVAC, Locks, Sentry, TPMS, Odometer)
python3 scripts/tesla_cli.py status

# Output raw JSON
python3 scripts/tesla_cli.py status --json

# Current GPS position and address
python3 scripts/tesla_cli.py location
```

### 2. AI-Powered Navigation (Japan / Global)

Takes arbitrary natural language, extracts coordinates via Vertex AI `gemini-3.8-flash` (or OpenStreetMap fallback), and pushes coordinates to vehicle:

```bash
# By POI name or colloquial query
python3 scripts/tesla_cli.py nav "名古屋市科学馆"
python3 scripts/tesla_cli.py nav "成田机场T1"
python3 scripts/tesla_cli.py nav "附近的特斯拉超充"
```

> **Fallback Caution**: If Vertex AI fails or is unconfigured, the CLI automatically falls back to OpenStreetMap Nominatim and emits a prominent `[CAUTION]` banner warning the user to verify the route on their Tesla center screen, since open-source mapping has lower precision for branch distances and colloquial phrasing.

### 3. Climate & Cabin Comfort

```bash
# Start / Stop HVAC
python3 scripts/tesla_cli.py climate on
python3 scripts/tesla_cli.py climate off

# Set cabin temperature (Celsius)
python3 scripts/tesla_cli.py climate temp 22.0

# Set seat heating (driver/passenger/rear_left/rear_center/rear_right, level 0-3)
python3 scripts/tesla_cli.py climate seat driver 2

# Defrost & Steering Wheel Heater
python3 scripts/tesla_cli.py climate defrost on
python3 scripts/tesla_cli.py climate steering on
```

### 4. Vehicle Control & Safety Guardrails

> **Safety Guardrail**: Commands that actuate moving parts or unlock doors (`unlock`, `frunk`, `trunk`) require confirmation or the `--force` flag.

```bash
# Harmless controls (execute directly)
python3 scripts/tesla_cli.py control honk
python3 scripts/tesla_cli.py control flash
python3 scripts/tesla_cli.py control lock
python3 scripts/tesla_cli.py control vent
python3 scripts/tesla_cli.py control close_windows
python3 scripts/tesla_cli.py control sentry_on

# Critical physical controls (must confirm with user before using --force)
python3 scripts/tesla_cli.py control unlock --force
python3 scripts/tesla_cli.py control frunk --force
python3 scripts/tesla_cli.py control trunk --force
```

### 5. Charging Management

```bash
# Query battery and charger status
python3 scripts/tesla_cli.py charge status

# Start / Stop charging
python3 scripts/tesla_cli.py charge start
python3 scripts/tesla_cli.py charge stop

# Adjust charge limit (e.g. 80% or 100%)
python3 scripts/tesla_cli.py charge limit 80

# Adjust charging current limit (amps)
python3 scripts/tesla_cli.py charge amps 16

# Open / Close charge port
python3 scripts/tesla_cli.py charge open
python3 scripts/tesla_cli.py charge close
```

### 6. Live Fleet Telemetry Stream

Establishes a WebSocket connection to `wss://streaming.tessie.com/<vin>` and streams live events:

```bash
# Listen for 15 seconds (default)
python3 scripts/tesla_cli.py stream

# Custom duration
python3 scripts/tesla_cli.py stream --duration 30
```

### 7. Historical Analytics

```bash
# View recent driving trips
python3 scripts/tesla_cli.py analytics drives --limit 5

# View recent charging sessions
python3 scripts/tesla_cli.py analytics charges --limit 5

# View battery health assessment
python3 scripts/tesla_cli.py analytics battery
```

---

## Agent Guidelines & Interaction Rules

1. **Auto Vehicle Selection**:
   The CLI automatically detects the active vehicle associated with the account (`Moomin Y`). You do not need to prompt the user for a VIN unless they have multiple active cars.
2. **Physical Action Confirmation (Guardrails)**:
   Never execute `unlock`, `frunk`, or `trunk` silently. Ask the user for confirmation first (e.g., *"即将为您开启 Moomin Y 的后备箱，是否确认？"*). Once confirmed, pass `--force`.
3. **Navigation Execution**:
   When the user mentions navigation or setting in-car destination, directly execute `tesla_cli.py nav "<user query>"`. The script will automatically handle Vertex AI geolocation, fallback to OSM if needed, and push the coordinates to Tesla.
4. **Directness**:
   Keep responses concise, clear, and high-signal (Caveman Lite). Present key status numbers in a structured, readable format.

---

## References for Full API Coverage

For specialized or niche operations not yet wrapped by `tesla_cli.py` (e.g. cabin overheat temp threshold, setting license plates, boombox sounds, or driver invitation management):
- **[`references/api_reference.md`](references/api_reference.md)**: Structured reference of all Tessie REST endpoints (paths, query parameters, payload schemas).
- **[`references/telemetry_proto_fields.md`](references/telemetry_proto_fields.md)**: All data metrics and alert codes emitted by Tesla Fleet Telemetry.
- **[`references/openapi.yaml`](references/openapi.yaml)**: Official OpenAPI 3.0 specification for the entire Tessie platform.
Agents can read these references via `view_file` to formulate exact `curl` calls or extend client methods when users request advanced operations.
