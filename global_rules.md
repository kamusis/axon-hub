# Coding guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

# Language rules
- When asked questions in a specific language, respond in the same language. All code-related output must remain in English.
- If explicitly requested to translate or generate text in non-English and the file is markdown, proceed. Any text inside code must still be English; this typically applies to source files (e.g., `.py`, `.ts`) rather than markdown.
- Always use English in source code, including:
  - Code comments and documentation
  - User interface messages
  - Error messages and warnings
  - Log messages
  - Debug information
  - Console output
  - Configuration files
  - API responses
  - Status messages
  - Prompts and confirmations

# Community platform language rules
- Always use English for any content posted to international community platforms, including:
  - GitHub: issues, pull requests, comments, reviews, commit messages, release notes
  - Reddit: posts and replies (any subreddit)
  - Any other English-speaking communities (Hacker News, Discord public servers, Stack Overflow, etc.)

# Code quality
- Always include docstrings for functions and classes.
- Add meaningful comments for complex logic.
- Always use context7 when I need code generation, setup or configuration steps, or library/API documentation. This means you should automatically use the Context7 MCP tools to resolve library id and get library docs without me having to explicitly ask.

# Git hygiene
- When asked to initializing a repo (`git init`), always create a `.gitignore` at the same time.
- Always add standard recommended items to `.gitignore` based on the project's programming language.

<!-- swissql-guide:begin -->
# SwissQL CLI Reference

Backend-first REST service for database connection management and SQL execution.

## Global Flags

| Flag | Default | Description |
|------|---------|-------------|
| `-s, --server` | `http://localhost:8080` | Backend URL |
| `--output-format` | `table` | `table`, `csv`, `tsv`, `json` |
| `--plain` | `false` | ASCII instead of Unicode borders |
| `--connection-timeout` | `5000` | ms |

## Status

```bash
swissql status
swissql capabilities
```

## Connections

```bash
# List (all filters optional, ANDed)
swissql connections list
swissql connections list --db-type postgres --enabled=true --name-contains primary
swissql connections list --label env:prod --label role:primary   # note: colon separator

# Get
swissql connections get <profile-id>

# Add (--name, --db-type, --dsn required)
swissql connections add \
  --profile-id pg-primary --name "PG Primary" \
  --db-type postgres --dsn postgres://host:5432/mydb \
  --username postgres --password secret --save-password=true \
  --label env=prod --label role=primary   # note: equals separator

# Update (only provided flags are sent)
swissql connections update <profile-id> --name "New Name" --enabled=true
swissql connections update <profile-id> --label env=staging   # replaces all labels
swissql connections update <profile-id> --clear-labels

# Delete
swissql connections delete <profile-id>

# Test existing profile
swissql connections test <profile-id>

# Test without creating a profile
swissql connections test-draft --db-type postgres --dsn postgres://host:5432/mydb --password secret

# Import from DBeaver .dbp archive
swissql connections import dbeaver <file> [--dry-run] [--on-conflict fail|skip|overwrite] [--name-prefix "imported-"]
```

> **Label separator difference:** `--label` on `list` uses `:` (key:value); on `add`/`update` uses `=` (key=value).

## Execute SQL

```bash
swissql exec --profile-id <id> "<sql>"
swissql exec --profile-id <id> -f /tmp/query.sql   # preferred for long/complex SQL
```

| Flag | Default | Description |
|------|---------|-------------|
| `--profile-id` | required | Connection profile ID |
| `--allow-write` | `false` | Required for DML/DDL — omitting blocks write statements |
| `--limit` | `1000` | Max rows |
| `--query-timeout` | `30000` | ms |
| `--fetch-size` | `500` | JDBC fetch size |
| `-f, --file` | — | SQL file path (mutually exclusive with positional arg) |

## SQL Rule Engine

Rules are stored in `sql-rules.yaml` on the **backend machine** (`SWISSQL_DATA_DIR`).

```bash
swissql rules list
swissql rules reload
swissql rules validate "<sql>" [--profile-id <id>] [--allow-write]
```

`validate` output columns: `allowed`, `action`, `matched_rule_id`, `matched_rule_description`, `default_action_used`, `write_like`, `request_allow_write_required`, `profile_id`, `labels`.

Label-scoped rules only fire when `--profile-id` is provided and the profile's labels match.

## Setup

```bash
swissql setup agents                          # inject CLI guide into agent system prompt
swissql setup rules --mode blacklist|whitelist [--force]
```

`setup rules` writes `sql-rules.yaml` to the **backend's** `SWISSQL_DATA_DIR` and hot-reloads. Fails with `FILE_EXISTS` if the file already exists — use `--force` to overwrite.

- **blacklist**: default `allow`, add deny rules for dangerous statements
- **whitelist**: default `deny`, add allow rules for permitted statements

## Drivers

```bash
swissql drivers list
swissql drivers reload
```

## DSN Format

- PostgreSQL: `postgres://host:5432/database`
- MySQL: `mysql://host:3306/database`
- Oracle: `oracle://host:1521/serviceName`

## Credential References

- `env:VAR_NAME` — read from environment variable at execution time
- `local:<profile-id>` — read from backend's encrypted credential store
<!-- swissql-guide:end -->
