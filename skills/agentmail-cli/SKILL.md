---
name: agentmail-cli
description: Send and receive emails programmatically using the AgentMail CLI. Use when agents need to manage inboxes, send/receive emails, handle threads, drafts, webhooks, and domains via command line.
---

# AgentMail CLI

Use the `agentmail` CLI to send and receive emails programmatically. Requires `AGENTMAIL_API_KEY` environment variable.

## Install

```bash
npm install -g agentmail-cli
```

## Core Commands

### Inboxes

```bash
# Create an inbox (defaults to @agentmail.to;
# pass --domain only if you have verified a custom domain)
agentmail inboxes create --display-name "My Agent" --username myagent

# List inboxes
agentmail inboxes list

# Get an inbox
agentmail inboxes retrieve --inbox-id <inbox_id>

# Delete an inbox
agentmail inboxes delete --inbox-id <inbox_id>
```

### Send Email

```bash
# Send a message from an inbox
agentmail inboxes:messages send --inbox-id <inbox_id> \
  --to "recipient@example.com" \
  --subject "Hello" \
  --text "Message body"

# Send with HTML
agentmail inboxes:messages send --inbox-id <inbox_id> \
  --to "recipient@example.com" \
  --subject "Hello" \
  --html "<h1>Hello</h1>"

# Reply to a message
agentmail inboxes:messages reply --inbox-id <inbox_id> --message-id <message_id> \
  --text "Reply body"

# Forward a message
agentmail inboxes:messages forward --inbox-id <inbox_id> --message-id <message_id> \
  --to "someone@example.com"
```

### Attachments

> **Known CLI bug:** `--attachment` currently sends a string instead of an array to the API, causing a 400 error.
> Use the REST API directly for attachments (see below).

**CLI workaround (subject to bug — use REST API for attachments):**

```bash
# Note: the --attachment flag has a known bug; for files, use the REST API directly
agentmail inboxes:messages send --inbox-id <inbox_id> \
  --to "recipient@example.com" \
  --subject "With Attachment" \
  --text "See attached file." \
  --attachment "/path/to/file.pdf"   # ← buggy, use REST API below instead
```

**REST API (recommended for attachments):**

```bash
# Send with file attachment via curl
curl -s -X POST \
  "https://api.agentmail.to/v0/inboxes/${INBOX_ID}/messages/send" \
  -H "Authorization: Bearer ${AGENTMAIL_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["recipient@example.com"],
    "subject": "Subject",
    "text": "Body text",
    "attachments": [
      {
        "filename": "report.pdf",
        "content": "'"$(base64 < /path/to/file.pdf)"'",
        "content_type": "application/pdf"
      }
    ]
  }'
```

**Python (recommended for attachments):**

```python
import urllib.request, json, base64

with open("/path/to/file.pdf", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

payload = {
    "to": ["recipient@example.com"],
    "subject": "Subject",
    "text": "Body text",
    "attachments": [{"filename": "report.pdf", "content": b64, "content_type": "application/pdf"}]
}

req = urllib.request.Request(
    f"https://api.agentmail.to/v0/inboxes/{INBOX_ID}/messages/send",
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {AGENTMAIL_API_KEY}", "Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req) as resp:
    print(json.loads(resp.read()))
```

### Read Email

```bash
# List messages in an inbox
agentmail inboxes:messages list --inbox-id <inbox_id>

# Get a specific message
agentmail inboxes:messages retrieve --inbox-id <inbox_id> --message-id <message_id>

# List threads
agentmail inboxes:threads list --inbox-id <inbox_id>

# Get a thread
agentmail inboxes:threads retrieve --inbox-id <inbox_id> --thread-id <thread_id>
```

### Drafts

```bash
# Create a draft
agentmail inboxes:drafts create --inbox-id <inbox_id> \
  --to "recipient@example.com" \
  --subject "Draft" \
  --text "Draft body"

# Send a draft
agentmail inboxes:drafts send --inbox-id <inbox_id> --draft-id <draft_id>
```

### Pods

Pods group inboxes together.

```bash
# Create a pod
agentmail pods create --name "My Pod"

# Create an inbox in a pod
agentmail pods:inboxes create --pod-id <pod_id> --display-name "Pod Inbox"

# List threads in a pod
agentmail pods:threads list --pod-id <pod_id>
```

### Webhooks

```bash
# Create a webhook for new messages
agentmail webhooks create --url "https://example.com/webhook" --event-type message.received

# List webhooks
agentmail webhooks list
```

### Domains

```bash
# Add a custom domain. --feedback-enabled is REQUIRED:
# pass the flag to route bounce/complaint notifications to your inboxes.
# The CLI has no way to create a domain without this flag.
agentmail domains create --domain example.com --feedback-enabled

# Verify domain DNS
agentmail domains verify --domain-id <domain_id>

# Get DNS records to configure
agentmail domains get-zone-file --domain-id <domain_id>
```

## Global Flags

All commands support: `--api-key`, `--base-url`, `--environment`, `--format`, `--format-error`, `--transform`, `--transform-error`, `--debug`.

## Output Formats

Use `--format` to control output: `auto` (default), `pretty`, `json`, `jsonl`, `yaml`, `raw`, `explore`.
