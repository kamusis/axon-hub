# Ticket Lifecycle

Ticket lifecycle enables creating, viewing, assigning, and transitioning status for work tickets within a workspace, with end-to-end consistency across Web UI, REST API, and PostgreSQL storage.

## Sub-features

- `ticket-list`: Display paginated ticket list with filters, sort order, and status tabs.
- `ticket-create`: Create a new ticket with title, description, priority, and optional assignee.
- `ticket-detail`: Render full ticket details, Markdown description, metadata sidebar, and activity timeline.
- `ticket-status-change`: Transition status across lifecycle stages (Backlog -> Todo -> In Progress -> In Review -> Done).
- `ticket-db-persistence`: Verify database row integrity and foreign key relationships in PostgreSQL.

## How to get to it (user POV)

- Navigate to `/dev-space/tickets` in the browser.
- Click the `New ticket` button in the top-right toolbar or press keyboard shortcut `c`.
- Click any ticket row in the table to open its detail view at `/dev-space/tickets/<ticket-id>`.
- In CLI: run `mopheus ticket list` or `mopheus ticket create --title <title>`.

## Driving it with verify-mopheus

Preconditions:
- Preview harness is healthy (`~/.gemini/config/skills/verify-mopheus/scripts/doctor.sh` passes).
- Authenticated user is `alice@mopheus.dev` in workspace `dev-space` (`bb08a9c4-9f3f-414d-8632-d23909bada79`).

### Step 1: Capture Baseline Ticket List
```bash
node ~/.gemini/config/skills/mopheus-integration-preview/scripts/preview_screenshot.js \
  --url "/dev-space/tickets" \
  --output "/tmp/verify-tickets-list.png"
```
*Observable Result*: Generates `/tmp/verify-tickets-list.png` showing the ticket list view with PageHeader and filters.

### Step 2: Create a Deterministic Test Ticket
```bash
# Obtain auth token
TOKEN=$(curl -s -X POST http://localhost:8230/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@mopheus.dev","password":"Mopheus@123"}' | jq -r .data.accessToken)

# Create ticket via REST API
CREATE_RESP=$(curl -s -X POST http://localhost:8230/api/v1/tickets \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Workspace-Id: bb08a9c4-9f3f-414d-8632-d23909bada79" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Verify Ticket Flow Test",
    "description": "Automated verification test ticket created by verify-mopheus.",
    "priority": 1,
    "status": 1
  }')

TICKET_ID=$(echo "${CREATE_RESP}" | jq -r .data.id)
echo "Created ticket: ${TICKET_ID}"
```
*Observable Result*: API returns HTTP 200 with `success: true` and UUID `TICKET_ID`.

### Step 3: Verify Ticket Detail View
```bash
node ~/.gemini/config/skills/mopheus-integration-preview/scripts/preview_screenshot.js \
  --url "/dev-space/tickets/${TICKET_ID}" \
  --output "/tmp/verify-ticket-detail-${TICKET_ID}.png"
```
*Observable Result*: Screenshot captures the ticket detail page rendering the title, description, and status badge (`Todo`).

### Step 4: Verify Database Persistence (Observable Proof)
```bash
docker exec mopheus-postgres-1 psql -U mopheus -d mopheus_wt_preview_test -c \
  "SELECT id, number, title, status, priority, workspace_id FROM ticket WHERE id = '${TICKET_ID}';"
```
*Observable Result*: Database returns exactly 1 row matching `title = 'Verify Ticket Flow Test'`, `status = 1` (Todo), and `workspace_id = 'bb08a9c4-9f3f-414d-8632-d23909bada79'`.

## Gotchas

- **Numeric Status Enums**: In models and DB, `status` is an integer: `0=backlog, 1=todo, 2=in_progress, 3=in_review, 4=done, 5=blocked, 6=cancelled, 7=archived`.
- **Assignee Polymorphism**: `assignee_type` supports `0=member, 1=agent, 3=team`. Do not set `assignee_type=1` with a member UUID.
- **Owner Restriction**: `owner_id` must strictly reference a human workspace member, never an agent.
- **Cache Invalidation**: The Web UI uses TanStack Query; status changes dispatched via API will reflect in the UI upon window focus or query invalidation.
