---
name: yashandb-schema
description: Browse and explore YashanDB database schema objects using the yasql CLI. Use this skill when users want to list schemas/owners, list tables/views/sequences in a schema, inspect object details (columns, constraints, indexes), or explore database structure. Triggers on requests like "show me all tables in schema X", "describe table Y", "what columns does table Z have", "list all schemas", "show indexes on table", or any YashanDB/Oracle schema exploration task.
---

# YashanDB Schema Explorer

Explore YashanDB schema objects using the `yasql` CLI directly.

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

> 🔒 **Security Rule**: Never output plaintext passwords. Always mask: `user/****@host:port`

**Aliases file format** (`~/.yashandb_aliases`):

```ini
[prod]
uri = sys/password@10.0.1.100:1688

[staging]
uri = appuser/pass@10.0.2.100:1688
```

Read aliases with:

```bash
awk -F'=' '/\[TARGET\]/{found=1} found && /^uri/{print $2; exit}' ~/.yashandb_aliases
```

(Replace `TARGET` with the alias name from user's request.)

## Executing Multi-line SQL

Write SQL to a temp file and use `-f`:

```bash
cat > /tmp/yasql_query.sql << 'EOF'
<your SQL here>
EOF
LD_LIBRARY_PATH=$YASQL_HOME/lib $YASQL_HOME/bin/yasql -S $YAS_DB_URI -f /tmp/yasql_query.sql
```

## Key Queries

### List all schemas/owners

```sql
SELECT USERNAME FROM ALL_USERS ORDER BY USERNAME
```

### List objects in a schema

```sql
SELECT OWNER, OBJECT_NAME, OBJECT_TYPE
FROM ALL_OBJECTS
WHERE OWNER = 'SCHEMA_NAME' AND OBJECT_TYPE = 'TABLE'
ORDER BY OBJECT_NAME
```

Valid OBJECT_TYPE values: `TABLE`, `VIEW`, `SEQUENCE`, `INDEX`, `PROCEDURE`, `FUNCTION`, `PACKAGE`

### Table basic info

```sql
SELECT OWNER, TABLE_NAME, TABLE_TYPE, NUM_ROWS, BLOCKS, LAST_ANALYZED
FROM ALL_TABLES
WHERE OWNER = 'SCHEMA_NAME' AND TABLE_NAME = 'TABLE_NAME'
```

### Columns with statistics

```sql
SELECT C.COLUMN_NAME, C.DATA_TYPE, C.NULLABLE, C.DATA_DEFAULT,
       CS.NUM_DISTINCT, CS.NUM_NULLS, CS.AVG_COL_LEN
FROM ALL_TAB_COLS C, ALL_TAB_COL_STATISTICS CS
WHERE C.OWNER = CS.OWNER AND C.TABLE_NAME = CS.TABLE_NAME
  AND C.COLUMN_NAME = CS.COLUMN_NAME
  AND C.OWNER = 'SCHEMA_NAME' AND C.TABLE_NAME = 'TABLE_NAME'
ORDER BY C.COLUMN_ID
```

### Constraints

```sql
SELECT CONS.CONSTRAINT_NAME, CONS.CONSTRAINT_TYPE, COLS.COLUMN_NAME, COLS.POSITION
FROM ALL_CONSTRAINTS CONS, ALL_CONS_COLUMNS COLS
WHERE CONS.CONSTRAINT_NAME = COLS.CONSTRAINT_NAME
  AND CONS.OWNER = COLS.OWNER AND CONS.TABLE_NAME = COLS.TABLE_NAME
  AND CONS.OWNER = 'SCHEMA_NAME' AND CONS.TABLE_NAME = 'TABLE_NAME'
ORDER BY CONS.CONSTRAINT_NAME, COLS.POSITION
```

### Indexes on a table

```sql
SELECT IND.INDEX_NAME, IND.INDEX_TYPE, COLS.COLUMN_NAME, COLS.COLUMN_POSITION,
       IND.BLEVEL, IND.LEAF_BLOCKS, IND.DISTINCT_KEYS, IND.LAST_ANALYZED
FROM ALL_INDEXES IND, ALL_IND_COLUMNS COLS
WHERE IND.INDEX_NAME = COLS.INDEX_NAME AND IND.OWNER = COLS.INDEX_OWNER
  AND IND.TABLE_NAME = COLS.TABLE_NAME AND IND.TABLE_OWNER = COLS.TABLE_OWNER
  AND IND.TABLE_OWNER = 'SCHEMA_NAME' AND IND.TABLE_NAME = 'TABLE_NAME'
ORDER BY IND.INDEX_NAME, COLS.COLUMN_POSITION
```

### Sequence info

```sql
SELECT SEQUENCE_OWNER, SEQUENCE_NAME, MIN_VALUE, MAX_VALUE,
       INCREMENT_BY, CYCLE_FLAG, CACHE_SIZE, LAST_NUMBER
FROM ALL_SEQUENCES
WHERE SEQUENCE_OWNER = 'SCHEMA_NAME' AND SEQUENCE_NAME = 'SEQ_NAME'
```

## Notes

- All identifiers (schema names, table names) must be UPPERCASE in YashanDB/Oracle
- YashanDB uses Oracle SQL syntax; avoid PostgreSQL-style queries
- Use `-S` (silent) flag to suppress yasql banners in output
