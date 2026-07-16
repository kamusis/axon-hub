---
name: moclaw-mes-ticket-bridge
description: Bridge MES service-request events into MoClaw tickets using the moclaw CLI. Use this skill whenever an MES ticket must be synchronized with a MoClaw workspace ticket, especially when deduplicating by mes_sr_id, storing db_type metadata, or appending follow-up webhook events as comments.
compatibility: Requires bash, jq, and an authenticated moclaw CLI.
---

# MES Ticket Upsert

Synchronize an MES webhook payload into the explicitly selected MoClaw workspace.

## Required behavior

1. Read the complete JSON payload from a file or stdin.
2. Accept any non-empty MES `event_type` as an input event, including `ticket.created`, `ticket.replied`, `ticket.state_changed`, `ticket.closed`, and `ticket.attachment_added`.
3. Extract when present:
   - `mes_sr_id` from the top-level payload.
   - `db_type` from `payload.dict.itemName`.
4. Search for existing tickets whose metadata contains the same numeric `mes_sr_id`.
5. If exactly one ticket matches, add one comment to that ticket and do not create another ticket.
6. If no ticket matches, create one ticket for the event, then set these metadata values:
   - `mes_sr_id` as a number.
   - `db_type` as a string.
7. If more than one ticket matches, stop and report the duplicate ticket IDs instead of guessing.
8. Preserve the raw payload in the new ticket description or update comment. Do not silently discard fields, nested objects, arrays, or HTML content.

## Workspace safety

The workspace ID is mandatory. Never rely on the CLI's active workspace and never hard-code a workspace name or ID. Before executing a write, show or log the exact `--workspace-id` being used. The caller must provide the intended workspace explicitly.

## Shell implementation

Use the bundled script:

```bash
scripts/upsert_mes_ticket.sh --workspace-id "$WORKSPACE_ID" payload.json
```

Use stdin when the payload is not stored in a file:

```bash
cat payload.json | scripts/upsert_mes_ticket.sh --workspace-id "$WORKSPACE_ID"
```

The script uses only `moclaw ticket` commands for MoClaw operations:

- `ticket list --metadata-json` to detect an existing ticket.
- `ticket create` to create a missing ticket.
- `ticket metadata set` to record `mes_sr_id` and `db_type`.
- `ticket comment add` to append an event to an existing ticket.

## Content rules

- New ticket title: `[MES SR#<mes_sr_id>] <payload.title>`; use `MES service request` when no title is present.
- New ticket description must include the MES SR ID, database type, and the complete raw JSON payload in a fenced `json` block.
- Existing-ticket comments must identify the event and MES SR ID, then include the complete raw JSON payload in a fenced `json` block.
- Do not create a child ticket, assign an agent, change status, or modify an existing description unless explicitly requested.
- Do not use raw HTTP requests or `curl`.

## Failure handling

- Stop before writing if the JSON is invalid, `event_type` is missing, or `mes_sr_id` is missing/non-numeric.
- When no existing ticket matches, stop if `db_type` is missing/empty because it is required for the new ticket metadata.
- If ticket creation succeeds but a metadata write fails, report the created ticket ID and the exact metadata command that must be retried.
- Return the resulting ticket ID and whether the operation was `created` or `commented`.
