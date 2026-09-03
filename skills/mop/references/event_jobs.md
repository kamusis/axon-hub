# Mopheus Event-Type Jobs & `event-filter` Reference

This document provides the complete reference for creating, configuring, and maintaining event-driven automated jobs and writing `event-filter` JSON payloads in Mopheus.

---

## 1. Overview & Architecture

Event-type jobs trigger automatically in real time whenever workspace domain lifecycle events occur (such as a ticket being created/updated, a comment posted, an agent task failing, or a daemon node disconnecting).

### Key Parameters:
- **`--trigger-type event`** (or `--kind event` when adding a trigger)
- **`--action-type`**: `create_ticket`, `assign_agent`, `send_notification`
- **`--action-config`**: JSON payload configuring the action (e.g. `{"agentId":"<uuid>"}`)
- **`--instruction`**: Agent prompt / goal supporting dynamic template placeholders (`{{event.variable}}`)
- **`--event-filter`** / **`--event-filter-file`** / **`--event-filter-stdin`**: JSON criteria determining when the trigger fires

---

## 2. Writing `event-filter`

An `event-filter` defines the exact filter criteria. It can be supplied as a **single JSON object** or a **JSON array of objects** (array acts as **logical OR** across multiple rules).

### 2.1 JSON Schema

```json
[
  {
    "event": "<event_type>",
    "actions": ["<action1>", "<action2>"],
    "conditions": {
      "<variable_name>": "<scalar_or_array_match>"
    }
  }
]
```

### 2.2 Top-Level Fields

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| **`event`** | string | **Yes** | Domain event identifier: `ticket`, `comment`, `agent_task`, or `runtime`. |
| **`actions`** | string[] | No | Event actions to match. If omitted or `[]`, matches **all actions** for this event. |
| **`conditions`** | object | No | Key-value mapping of payload variable names to match criteria. **All conditions in the map must match (logical AND)**. |

---

## 3. Condition Matching Rules & Semantics

The Mopheus Job Engine evaluates `conditions` against the incoming event payload using smart matching rules:

1. **Exact Scalar Match**:
   - Compares strings (case-insensitive), numbers, booleans, or UUIDs.
   - Example: `"status": 1` matches when payload `status == 1`.
   - Example: `"authorType": 0` matches when comment author is a human member (`0`).
2. **Multi-Value (OR) Match (Slice values)**:
   - Provide an array of acceptable scalar values. Matches if the payload value equals **any** item in the array.
   - Example: `"status": [1, 2, 3]` matches if payload `status` is `1`, `2`, or `3`.
   - Example: `"priority": [1, 2]` matches High (`1`) or Urgent (`2`) tickets.
3. **Array / Tag Containment**:
   - When matching against array fields (like `ticket.labels` or `comment.ticketLabels`), matches if there is any intersection between filter tags and payload tags.
   - Example: `"labels": ["bug", "urgent"]` matches if the ticket has either `"bug"` or `"urgent"` label.
4. **Nested Object Resolution**:
   - If the payload contains an object with `id` or `name` (e.g. a Project or Member object), the condition can match directly against the string ID or name.

---

## 4. Supported Domain Events, Actions & Whitelist Variables

Use `mop job event-schema [event]` for live CLI introspection.

### 4.1 `ticket` (Ticket Lifecycle)
- **Supported Actions**: `created`, `updated`, `deleted`
- **Condition Keys & Payload Variables**:

| Variable Name | Type | Description | Enum / Values Reference |
| :--- | :--- | :--- | :--- |
| `id` | `uuid` | Ticket UUID | |
| `workspaceId` | `uuid` | Workspace UUID | |
| `number` | `int` | Human-readable ticket sequence number | e.g. `597` |
| `title` | `string` | Ticket title | |
| `description` | `string` | Ticket description body | |
| `status` | `int` | Ticket lifecycle status | `0`=backlog, `1`=todo, `2`=in_progress, `3`=in_review, `4`=done, `5`=blocked, `6`=cancelled, `7`=archived |
| `statusName` | `string` | Human-readable status string | `backlog`, `todo`, `in_progress`, `in_review`, `done`, `blocked`, `cancelled`, `archived` |
| `priority` | `int` | Ticket priority | `-1`=low, `0`=normal, `1`=high, `2`=urgent |
| `priorityName` | `string` | Human-readable priority string | `low`, `normal`, `high`, `urgent` |
| `assigneeType` | `int` | Assignee entity type | `0`=member, `1`=agent, `3`=team |
| `assigneeTypeName` | `string` | Assignee entity string | `member`, `agent`, `team` |
| `assigneeId` | `uuid` | Assignee UUID | |
| `creatorType` | `int` | Creator entity type | `0`=member, `1`=agent |
| `creatorTypeName` | `string` | Creator entity string | `member`, `agent`, `system` |
| `creatorId` | `uuid` | Creator UUID | |
| `projectId` | `uuid` | Associated project UUID | |
| `parentTicketId`| `uuid` | Parent ticket UUID (if sub-ticket) | |
| `labels` | `[]string`| Array of label names | e.g. `["bug", "backend"]` |


### 4.2 `comment` (Ticket Comments & Activity)
- **Supported Actions**: `created`, `updated`, `deleted`
- **Condition Keys & Payload Variables**:

| Variable Name | Type | Description | Enum / Values Reference |
| :--- | :--- | :--- | :--- |
| `id` | `uuid` | Comment UUID | |
| `ticketId` | `uuid` | Associated ticket UUID | |
| `ticketTitle` | `string` | Associated ticket title | |
| `ticketNumber` | `int` | Associated ticket sequence number | |
| `ticketStatus` | `int` | Associated ticket status enum | (See ticket status enum above) |
| `ticketPriority` | `int` | Associated ticket priority enum | (See ticket priority enum above) |
| `ticketProjectId`| `uuid` | Associated ticket project UUID | |
| `ticketLabels` | `[]string`| Associated ticket label names | |
| `parentCommentId`| `uuid` | Parent comment UUID (if thread reply) | |
| `authorType` | `int` | Author entity type | `0`=member, `1`=agent |
| `authorId` | `uuid` | Author UUID | |
| `content` | `string` | Comment Markdown content text | |
| `type` | `int` | Comment type | `0`=regular, `1`=status_change, `2`=progress_update, `3`=system |
| `agentTaskId` | `uuid` | Associated agent task UUID (if generated by task)| |

### 4.3 `agent_task` (Agent Task Executions)
- **Supported Actions**: `completed`, `failed`, `interaction`, `created`, `updated`
- **Condition Keys & Payload Variables**:

| Variable Name | Type | Description | Enum / Values Reference |
| :--- | :--- | :--- | :--- |
| `id` | `uuid` | Agent task execution UUID | |
| `ticketId` | `uuid` | Associated ticket UUID | |
| `agentId` | `uuid` | Executing agent UUID | |
| `runtimeId` | `uuid` | Runtime node UUID | |
| `status` | `int` | Task status enum | `10`=pending, `20`=queued, `30`=running, `40`=completed, `50`=failed, `60`=cancelled |
| `priority` | `int` | Task priority | `-1`=low, `0`=normal, `1`=high, `2`=urgent |
| `instruction` | `string` | Input instruction / prompt | |
| `failureReason` | `string` | Error code on failure | `run_timeout`, `agent_error`, `cancelled`, etc. |
| `startedAt` | `time` | Execution start timestamp (RFC3339) | |
| `completedAt` | `time` | Completion timestamp (RFC3339) | |

### 4.4 `runtime` (Daemon Node Lifecycle)
- **Supported Actions**: `offline`, `register`, `updated`
- **Condition Keys & Payload Variables**:

| Variable Name | Type | Description | Enum / Values Reference |
| :--- | :--- | :--- | :--- |
| `id` | `uuid` | Runtime node UUID | |
| `workspaceId` | `uuid` | Workspace UUID | |
| `daemonId` | `string` | Daemon host machine identifier | |
| `name` | `string` | Runtime display name | |
| `provider` | `string` | CLI provider | `claude`, `kimi`, `codex`, `local`, etc. |
| `status` | `int` | Runtime status enum | `0`=offline, `1`=online, `2`=busy, `3`=error |
| `enabled` | `bool` | Activation status | `true`, `false` |
| `lastHeartbeatAt`| `time` | Last heartbeat timestamp | |

---

## 5. Instruction Dynamic Template Placeholders

In `--instruction`, use `{{<event_type>.<variable_name>}}` placeholders to inject live payload data into the dispatched agent prompt:

- `{{ticket.number}}`, `{{ticket.title}}`, `{{ticket.description}}`, `{{ticket.labels}}`
- `{{comment.content}}`, `{{comment.ticketTitle}}`, `{{comment.ticketNumber}}`
- `{{agent_task.failureReason}}`, `{{agent_task.id}}`, `{{agent_task.instruction}}`
- `{{runtime.name}}`, `{{runtime.daemonId}}`, `{{runtime.provider}}`

*Note: If a referenced variable is missing in the payload, the template engine fails safely with `MISSING_TEMPLATE_VARIABLE`.*

---

## 6. CLI Command Examples

### 6.1 Create an Event Job (Single Command)

```bash
# 1. Inline JSON filter
mop job create \
  --name "Bug Ticket Auto-Triage" \
  --trigger-type event \
  --action-type assign_agent \
  --action-config '{"agentId":"<agent-uuid>"}' \
  --instruction "A new bug ticket #{{ticket.number}} ({{ticket.title}}) was created. Description: {{ticket.description}}. Triage and reproduce." \
  --event-filter '{"event":"ticket","actions":["created"],"conditions":{"labels":["bug"]}}'

# 2. Filter from JSON file
mop job create \
  --name "Task Failure Watchdog" \
  --trigger-type event \
  --action-type send_notification \
  --instruction "Task {{agent_task.id}} failed with reason {{agent_task.failureReason}}." \
  --event-filter-file path/to/filter.json

# 3. Filter via stdin
cat << 'EOF' | mop job create --name "Urgent Review" --trigger-type event --action-type assign_agent --action-config '{"agentId":"<uuid>"}' --event-filter-stdin
[
  {
    "event": "ticket",
    "actions": ["created", "updated"],
    "conditions": {
      "priority": [1, 2],
      "status": 1
    }
  }
]
EOF
```

### 6.2 Add or Update Event Trigger on Existing Job

```bash
# Add trigger
mop job trigger-add <job-id> \
  --kind event \
  --label "Human comments on active tickets" \
  --event-filter '{"event":"comment","actions":["created"],"conditions":{"authorType":0,"type":0,"ticketStatus":[1,2,3]}}'

# Update trigger filter
mop job trigger-update <job-id> <trigger-id> \
  --event-filter '[{"event":"ticket","actions":["created"],"conditions":{"priority":[1,2]}}]' \
  --enabled true
```

### 6.3 Introspect Event Schemas

```bash
# List all registered domain events and actions
mop job event-list

# View detailed schema and sample payload
mop job event-schema ticket
mop job event-schema comment
mop job event-schema agent_task
mop job event-schema runtime
```

---

## 7. Practical Recipes

### Recipe 1: Auto-Triage New High-Priority Bug Tickets
```json
{
  "event": "ticket",
  "actions": ["created"],
  "conditions": {
    "labels": ["bug", "regression"],
    "priority": [1, 2]
  }
}
```


### Recipe 2: AI Responder for Human Comments on Active Tickets
```json
{
  "event": "comment",
  "actions": ["created"],
  "conditions": {
    "authorType": 0,
    "type": 0,
    "ticketStatus": [1, 2, 3]
  }
}
```

### Recipe 3: Task Failure Diagnostic Watchdog
```json
{
  "event": "agent_task",
  "actions": ["failed"],
  "conditions": {
    "failureReason": ["run_timeout", "agent_error"]
  }
}
```

### Recipe 4: Runtime Offline Alert
```json
{
  "event": "runtime",
  "actions": ["offline"],
  "conditions": {
    "enabled": true
  }
}
```
