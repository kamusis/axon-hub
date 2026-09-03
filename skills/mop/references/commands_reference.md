# Mopheus CLI Comprehensive Command Reference

Complete guide for managing Mopheus resources via `mop` (or `mopheus`) CLI.

---

## 1. Workspace & Search

### `mop workspace`
Manage workspace context and multi-tenancy.
- `mop workspace list` - List accessible workspaces with slug, ID, and active marker `*`.
- `mop workspace switch <slug-or-id>` - Switch current active workspace.
- `mop workspace get <id>` - Inspect detailed workspace settings and metadata.

### `mop search`
Global full-text search across all workspace entities.
- `mop search "<query>"` - Search across tickets, agents, skills, and projects.
- `mop search "<query>" --type ticket` - Restrict search to tickets.
- `mop search "<query>" --type agent` - Restrict search to agents.
- `mop search "<query>" --type skill` - Restrict search to skills.
- `mop search "<query>" --limit 50` - Control result limit (1-100, default 20).

---

## 2. Tickets & Workflows (`mop ticket`)

### Querying & Viewing
- `mop ticket list` - List open tickets in active workspace.
- `mop ticket list --status open --priority urgent` - Filter by status and priority.
- `mop ticket list --assignee <id> --page 1 --per-page 20` - Filter by assignee with pagination.
- `mop ticket get <id-or-num>` - Get full ticket details by UUID or ticket sequence number.

### Creation & Updates (Native File First)
- `mop ticket create --title "Title" --description-file spec.md` - Create ticket using Markdown file.
- `mop ticket update <id> --priority urgent --tags "backend,p0"` - Update priority and tags.
- `mop ticket status <id> <open|in_progress|resolved|closed>` - Transition ticket status.
- `mop ticket assign <id> --assignee <user-or-agent-id>` - Assign ticket to a member or agent.

### Comments & Collaboration
- `mop ticket comment list <id>` - List all comments on a ticket.
- `mop ticket comment add <id> --content-file note.md` - Post comment from Markdown file.

### Execution Lifecycle & Diagnostics
- `mop ticket rerun <id>` - Re-enqueue agent task execution on a ticket.
- `mop ticket grill <id>` - Trigger self-Q&A review on a ticket.
- `mop ticket runs <id>` - List all agent task runs for a ticket.
- `mop ticket run-messages <ticket-id> --run <run-id>` - List messages for a specific run.
- `mop ticket transcript <id> --out ./transcripts/` - Export complete task execution transcript.

---

## 3. Agents & Teams

### `mop agent`
Manage AI agents and configurations.
- `mop agent list` - List all agents with role, model, and provider.
- `mop agent get <id-or-name>` - Inspect agent system instructions, prompt, and parameters.
- `mop agent create --name "Dev" --role "Developer" --instructions-file prompt.md` - Create agent.
- `mop agent update <id> --instructions-file prompt.md --model gpt-4o` - Update instructions/model.
- `mop agent skills list <agent-id>` - List skills assigned to agent.
- `mop agent skills add <agent-id> --skill <skill-id>` - Bind skill to agent.
- `mop agent skills remove <agent-id> --skill <skill-id>` - Unbind skill from agent.
- `mop agent tasks <agent-id>` - List recent tasks dispatched to this agent.
- `mop agent env list <agent-id>` / `set` / `unset` - Manage agent-scoped environment variables.

### `mop team`
Manage multi-agent team hierarchies.
- `mop team list` - List workspace teams.
- `mop team get <id>` - View team roster and leader configuration.
- `mop team update <id> --instructions-file leader_prompt.md` - Update leader instructions.
- `mop team member add <id> --member <agent-id>` - Add agent to team.
- `mop team member remove <id> --member <agent-id>` - Remove agent from team.

---

## 4. Tasks, Shortcuts & Chat

### `mop agent-task`
Direct execution monitoring and troubleshooting.
- `mop agent-task get <task-id>` - Inspect status, runtime duration, and error messages.
- `mop agent-task messages <task-id>` - Stream recent task dialogue messages.
- `mop agent-task cancel <task-id>` - Terminate a running or queued task run.
- `python <skill-dir>/scripts/mop_task.py transcript <task-id>` - Reconstruct formatted transcript.
- `python <skill-dir>/scripts/mop_task.py transcript <task-id> --tools-only` - Filter tool executions.

### `mop shortcut`
Execute skills with shortcut capability on tickets.
- `mop shortcut list` - List available shortcuts.
- `mop shortcut run <shortcut-name> -t <ticket-id>` - Run shortcut on specified ticket.

### `mop chat`
Inspect channel and chat context.
- `mop chat history` - Read recent messages from bound channel.
- `mop chat message <session-id>` - List messages in a chat session.
- `mop chat thread <thread-id>` - Read a specific channel thread.

---

## 5. Skills, Jobs & Triggers

### `mop skill`
Workspace skill management.
- `mop skill list` - List installed skills.
- `mop skill get <id>` - Inspect skill YAML frontmatter and body.
- `mop skill import --path <dir> --update` - Import local SKILL.md folder into workspace.
- `mop skill export --all --output-dir <dir>` - Export workspace skills to local directory.

### `mop job`
Automation jobs, schedules, and event-driven triggers.
- `mop job list` - List jobs and their trigger types.
- `mop job get <id>` - Inspect job details.
- `mop job runs <id> --limit 10` - View execution history.
- `mop job trigger <id>` - Manually fire a job run.
- `mop job trigger-add <id> --kind schedule --cron "0 9 * * *"` - Add cron schedule.
- `mop job trigger-add <id> --kind event --event-filter-file filter.json` - Add event trigger (v2.2.5+).
- `mop job event-list` - List supported domain event types.
- `mop job event-schema [type]` - Inspect event payload schema and condition variables.

---

## 6. Projects, Repos & Knowledge Base

### `mop project`
- `mop project list` - List projects in workspace.
- `mop project get <id>` - Inspect project details.

### `mop repo`
- `mop repo links --ticket <id>` - List linked GitHub/GitLab PRs and issues.
- `mop repo issue sync --number <n> --ticket <id>` - Associate issue with ticket.
- `mop repo pr sync --number <n> --ticket <id>` - Associate pull request with ticket.

### `mop memory`
- `mop memory list [--per-page <n>]` - List stored memories.
- `mop memory retrieve "<query>"` - Semantic vector / full-text search across memories.
- `mop memory get <memory-id>` - Inspect specific memory details.
- `mop memory store --type <type> --content-file note.md` - Store new memory item.


---

## 7. Runtimes, Daemon & Authentication

### `mop runtime` & `daemon`
- `mop runtime list` - List connected daemon runtimes and worker status.
- `mop daemon status` - Check local daemon status (requires daemon node).
- `mop daemon start / stop` - Manage background service (requires daemon node).

### `mop auth` & `token`
- `mop auth status` - Inspect current authenticated user and session validity.
- `mop login` - Interactive login.
- `mop token list` - List user API access tokens (`moc_...`).
