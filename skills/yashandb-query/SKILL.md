---
name: yashandb-query
description: Execute SQL statements and analyze query execution plans against YashanDB using the yasql CLI. Use this skill when users want to run SQL queries, insert/update/delete data, create/alter/drop objects, or inspect how a query will be executed (EXPLAIN PLAN). Triggers on requests like "run this SQL", "execute query", "show execution plan", "explain this query", "how will this SQL run", or any ad-hoc SQL execution task on YashanDB.
---

# YashanDB Query Runner

Execute SQL and analyze execution plans against YashanDB using `yasql` CLI.

## Configuration

### YASQL_HOME (Server-side, pre-configured)

`YASQL_HOME` is set once on the AI agent server by the administrator. The skill always uses:

```bash
# Correct argument order: -S must come BEFORE the connection string
LD_LIBRARY_PATH=$YASQL_HOME/lib $YASQL_HOME/bin/yasql -S $YAS_DB_URI -c "<SQL>"
```

If `YASQL_HOME` is not set, try `which yasql`. If not found, stop and tell the user: `"yasql not found. Please ensure YASQL_HOME is configured on this server."`

### Database Connection (Per-task, provided by DBA)

The DBA specifies the target database in natural language. **Never hardcode credentials in this skill.**

**Resolve the connection string (`YAS_DB_URI`) in this order:**

1. **Named alias**: User mentions a name (e.g. "prod", "testdb") → look up `~/.yashandb_aliases`
2. **Inline in message**: User provides `user/password@host:port` directly → use as-is
3. **Not found**: Ask the user: `"Which database should I connect to? Please provide a named alias or connection string (user/password@host:port)."`

> 🔒 **Security Rule**: Never include plaintext passwords in any response or confirmation message.
> Always mask the password portion when referencing a connection:
> ✅ `kamus/****@localhost:1688`
> ❌ `kamus/Enmo_123@localhost:1688`

**Aliases file** (`~/.yashandb_aliases`) format:

```ini
[prod]
uri = sys/password@10.0.1.100:1688

[staging]
uri = appuser/pass@10.0.2.100:1688
```

Read an alias:

```bash
awk -F'=' '/\[TARGET\]/{found=1} found && /^uri/{print $2; exit}' ~/.yashandb_aliases
```

## Semicolon Rules (Critical)

| Statement Type                     | Semicolon                   |
| ---------------------------------- | --------------------------- |
| SELECT / INSERT / UPDATE / DELETE  | **No semicolon** (omit `;`) |
| DDL: CREATE / ALTER / DROP / GRANT | **With semicolon**          |
| PL/SQL block / Stored procedure    | **With semicolon**          |

## Executing User SQL

1. Identify the statement type (SELECT, DML, DDL, PL/SQL)
2. Apply semicolon rules above
3. For simple single statements, use `-c`; for multi-line or PL/SQL, use `-f` with a temp file

## Explaining Query Execution Plans

> ⚠️ YashanDB does NOT support `DBMS_XPLAN.DISPLAY`. Use `EXPLAIN PLAN FOR` directly — it returns the full plan in its own output.

```bash
cat > /tmp/yasql_explain.sql << 'EOF'
EXPLAIN PLAN FOR
<user SQL here>;
EOF
LD_LIBRARY_PATH=$YASQL_HOME/lib $YASQL_HOME/bin/yasql -S $YAS_DB_URI -f /tmp/yasql_explain.sql
```

The output already contains the full plan. After retrieving it, interpret for the user:

- **Operation type**: `TABLE ACCESS FULL` (full scan), `INDEX RANGE SCAN` (uses index), `HASH JOIN` vs `NESTED LOOPS`
- **Rows / Cost(%CPU)**: optimizer estimates — large discrepancy hints at stale stats
- **Predicate / Operation Information**: access conditions at the bottom of the output

## Transactions (DML requiring COMMIT)

Write all statements including `COMMIT` to a single file — one `yasql` session handles it atomically:

```bash
cat > /tmp/yasql_txn.sql << 'EOF'
INSERT INTO orders (id, status) VALUES (1001, 'NEW');
UPDATE inventory SET qty = qty - 1 WHERE item_id = 99;
COMMIT;
EOF
LD_LIBRARY_PATH=$YASQL_HOME/lib $YASQL_HOME/bin/yasql -S $YAS_DB_URI -f /tmp/yasql_txn.sql
```

## Invoking yasql

**Scope `LD_LIBRARY_PATH` to each command only — never export globally.**

```bash
# Single SQL statement
LD_LIBRARY_PATH=$YASQL_HOME/lib $YASQL_HOME/bin/yasql -S $YAS_DB_URI -c "<SQL>"

# Multi-statement or complex SQL via file
cat > /tmp/yasql_query.sql << 'EOF'
<SQL statements here>
EOF
LD_LIBRARY_PATH=$YASQL_HOME/lib $YASQL_HOME/bin/yasql -S $YAS_DB_URI -f /tmp/yasql_query.sql
```

## Oracle Syntax Reminders

- Current time: `SYSDATE`
- Null handling: `NVL(col, default)` (not `COALESCE` if single arg)
- Single-row selects: `SELECT ... FROM DUAL`
- String type: `VARCHAR2` (not `VARCHAR` / `TEXT`)
