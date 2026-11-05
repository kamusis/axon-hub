# Agent Tasks & Execution

Agent Tasks represent automated execution jobs triggered on tickets or standalone workspaces, driven by local or cloud daemons, with full thinking duration and tool invocation transcripts.

## Sub-features

- `task-dispatch`: Queue a new task for an agent on a specific ticket or workspace.
- `task-lifecycle`: Transition status through `queued` (10) -> `dispatched` (20) -> `running` (30) -> `completed` (40) or `failed` (50).
- `task-transcript`: Display streaming thoughts, tool calls (Bash, TaskCreate, etc.), and step outputs in the Web UI.
- `task-comment-linkage`: Automatically post or associate task completion comments in the ticket discussion timeline.
- `task-run-history`: Render the run history drawer with duration, token counts, and trigger summaries.

## How to get to it (user POV)

- Open a ticket at `/dev-space/tickets/<ticket-id>`, click `Run Agent` or assign an Agent (`assignee_type=1`).
- Mention an agent in a comment (`@AgentName <instruction>`) to trigger a task.
- View task details directly at `/dev-space/agents/tasks/<task-id>` or via the Run History drawer in the ticket timeline.

## Driving it with verify-mopheus

Preconditions:
- Preview harness is healthy (`~/.gemini/config/skills/verify-mopheus/scripts/doctor.sh` passes).
- Target ticket exists (e.g. from `ticket-lifecycle.md`).

### Step 1: Query Available Agents in dev-space
```bash
TOKEN=$(curl -s -X POST http://localhost:8230/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"alice@mopheus.dev\",\"password\":\"\${MOPHEUS_TEST_PASSWORD:-\${ADMIN_PASSWORD}}\"}" | jq -r .data.accessToken)

AGENTS_RESP=$(curl -s http://localhost:8230/api/v1/workspaces/bb08a9c4-9f3f-414d-8632-d23909bada79/agents \
  -H "Authorization: Bearer ${TOKEN}")

AGENT_ID=$(echo "${AGENTS_RESP}" | jq -r '.data[0].id // .data.agents[0].id // empty')
echo "Target Agent ID: ${AGENT_ID}"
```
*Observable Result*: Returns active agent ID (e.g. default assistant or code writer agent).

### Step 2: Inspect Agent Task Records in Database
```bash
docker exec mopheus-postgres-1 psql -U mopheus -d mopheus_wt_preview_test -c \
  "SELECT id, agent_id, status, trigger_type, created_at FROM agent_task WHERE workspace_id = 'bb08a9c4-9f3f-414d-8632-d23909bada79' ORDER BY created_at DESC LIMIT 5;"
```
*Observable Result*: Displays recent tasks with integer statuses (10=queued, 30=running, 40=completed, 50=failed).

### Step 3: Capture Ticket Activity & Agent Timeline in Web UI
```bash
node ~/.gemini/config/skills/mopheus-integration-preview/scripts/preview_screenshot.js \
  --url "/dev-space/tickets" \
  --output "/tmp/verify-agent-tasks-view.png"
```
*Observable Result*: Produces screenshot displaying agent activity and status indicators.

## Gotchas

- **Daemon Execution State**: If the preview daemon is stopped, newly dispatched tasks will remain in status `10 (queued)`. Restart daemon with `bash ~/.gemini/config/skills/mopheus-integration-preview/scripts/restart_service.sh daemon`.
- **Status Constants**: In Go and PostgreSQL, `AgentTaskStatus` is typed int: `1=deferred, 10=queued, 20=dispatched, 30=running, 40=completed, 50=failed, 60=cancelled`.
- **SafeGo Panic Guard**: Background task workers run under `util.SafeGo` to isolate panics per task.
