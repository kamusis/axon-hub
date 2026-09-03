# Mopheus Enums & Model Attributes Reference

Authoritative mapping of integer enums, string values, companion `*Name` fields, and CLI representations across all Mopheus entities.

In Mopheus, database entities store status and type attributes as compact integer values (`INT`). Recent releases (>= v2.2.4 / PR #817) automatically enrich API responses, WebSockets, and event trigger payloads with self-describing companion `*Name` fields (`statusName`, `priorityName`, `assigneeTypeName`, `typeName`, etc.) to provide human-readable values while maintaining zero-overhead backward compatibility.

---

## 1. Tickets

### Ticket Status (`ticket.status` / `statusName`)
CLI commands accept lowercase string names (e.g. `mop ticket status <id> in_progress`).
Database and raw JSON payloads return the integer value alongside `statusName`.

| Integer | Status Key / String | Name | Meaning & Lifecycle Stage |
| :---: | :--- | :--- | :--- |
| `0` | `backlog` | Backlog | Planned for future work; can have scheduled activation (`activateAt`) |
| `1` | `todo` | To Do | Queued and ready to be worked on |
| `2` | `in_progress` | In Progress | Active work currently underway |
| `3` | `in_review` | In Review | Under peer review, automated testing, or QA |
| `4` | `done` | Done | Successfully completed and closed |
| `5` | `blocked` | Blocked | Paused waiting on external dependency or blocker |
| `6` | `cancelled` | Cancelled | Abandoned or rejected without completion |
| `7` | `archived` | Archived | Historical record removed from active views |

**Uncompleted filter**: Statuses `0, 1, 2, 3, 5` are considered "uncompleted" (`mop_ticket.py list-mine`).

### Ticket Priority (`ticket.priority` / `priorityName`)
CLI commands accept string names: `low`, `normal`, `high`, `urgent`.

| Integer | Priority Key | Display Name | Meaning |
| :---: | :--- | :--- | :--- |
| `-1` | `low` | Low | Low-urgency, cosmetic, or housekeeping items |
| `0` | `normal` | Normal | Default baseline priority for general tasks |
| `1` | `high` | High | Elevated priority, next up in iteration cycle |
| `2` | `urgent` | Urgent | P0/Critical blocker requiring immediate triage |

> [!WARNING]
> Ticket priority uses `-1` for Low and `0` for Normal. Never assume 0-indexed positive numbers (e.g. `0=Low, 1=Normal, 2=High, 3=Urgent` is incorrect).

### Actor / Assignee Type (`assigneeType`, `creatorType`, `authorType`)
Polymorphic entity identifier for ticket assignees, creators, comment authors, and task requesters.

| Integer | Type Key | Companion Field | Description |
| :---: | :--- | :--- | :--- |
| `0` | `member` | `assigneeTypeName: "member"` | Human workspace member |
| `1` | `agent` | `assigneeTypeName: "agent"` | Autonomous AI agent |
| `2` | `system` | `creatorTypeName: "system"` | System automation / backend daemon |
| `3` | `team` | `assigneeTypeName: "team"` | Multi-agent collaborative team |

---

## 2. Comments

### Comment Type (`comment.type` / `typeName`)

| Integer | Type Key | Description |
| :---: | :--- | :--- |
| `0` | `regular` | Standard user or agent markdown discussion / comment |
| `1` | `status_change` | Automated record created when ticket status changes |
| `2` | `progress_update` | Milestone or progress report submitted by agent or member |
| `3` | `system` | System diagnostic, dispatch notification, or grill evaluation |

### Ticket Context Fields in Comments (>= v2.2.4)
Event payloads and comment webhooks include context fields reflecting the associated ticket:
- `ticketStatus` (`int`) & `ticketStatusName` (`string`)
- `ticketPriority` (`int`) & `ticketPriorityName` (`string`)
- `authorType` (`int`: `0`=member, `1`=agent) & `authorTypeName` (`string`)

---

## 3. Agent Tasks

### Task Status (`agent_task.status` / `statusName`)

| Integer | Status Key | Description |
| :---: | :--- | :--- |
| `0` / `1` | `deferred` / `pending` | Task registered, awaiting trigger or dispatch queue |
| `10` | `queued` | Queued in memory/broker waiting for available runtime |
| `20` | `dispatched` | Dispatched to a worker node / daemon runtime |
| `30` | `running` | Currently executing tool calls and thinking in runtime |
| `40` | `completed` | Successfully completed; result output available |
| `50` | `failed` | Terminated with error; check `failureReason` |
| `60` | `cancelled` | Manually cancelled by user or watchdog |
| `70` | `timeout` | Exceeded maximum configured run duration |

### Task Priority (`agent_task.priority` / `priorityName`)
Same as Ticket Priority: `-1`=low, `0`=normal, `1`=high, `2`=urgent.

---

## 4. Jobs & Triggers

### Job Status (`job.status`)
- `0`: `active` — Job is active and listening for trigger events.
- `1`: `paused` — Job triggers are suspended.

### Job Trigger Kind (`job_trigger.kind`)
- `0` / `schedule`: Time-based cron schedule (e.g. `0 9 * * 1-5`).
- `1` / `webhook`: Inbound webhook endpoint with token authentication.
- `2` / `event`: Real-time internal workspace domain event (`ticket`, `comment`, `agent_task`, `runtime`).

### Job Run Status (`job_run.status`)
- `0`: `pending` — Run initiated, waiting for execution slot.
- `1`: `success` — Workflow completed successfully.
- `2`: `failed` — Workflow encountered an unrecoverable failure.
- `3`: `running` — Workflow currently in progress.
- `4`: `skipped` — Causal loop detected or preconditions unmet.
- `5`: `cancelled` — Manually aborted.

---

## 5. Runtimes

### Runtime Status (`runtime.status` / `statusName`)
- `0`: `offline` — Runtime node disconnected.
- `1`: `online` — Heartbeat active and ready to accept tasks.
- `2`: `busy` — Max concurrent tasks reached.
- `3`: `error` — Heartbeat unhealthy or runtime failure.

---

## 6. Companion `*Name` Fields in Event Filters & Templates

When authoring Event-Driven Jobs (`mop job create --trigger-type event`) or processing JSON streams, you can match or interpolate both the integer enum and the companion string name:

### Template Interpolation
```markdown
Ticket #{{ticket.number}} status changed to {{ticket.statusName}} (Priority: {{ticket.priorityName}}).
Assigned to {{ticket.assigneeTypeName}}: {{ticket.assigneeId}}.
```

### Condition Matching
Both integer IDs and string names can be matched:
```json
{
  "event": "ticket",
  "actions": ["created", "updated"],
  "conditions": {
    "priority": [1, 2],
    "status": [1, 2]
  }
}
```
Or matching by self-describing names:
```json
{
  "event": "ticket",
  "actions": ["created"],
  "conditions": {
    "priorityName": ["high", "urgent"],
    "assigneeTypeName": "agent"
  }
}
```
