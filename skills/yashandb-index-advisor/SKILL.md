---
name: yashandb-index-advisor
description: Analyze SQL queries and recommend optimal indexes for YashanDB using the yasql CLI and AI reasoning. Use this skill when users want index recommendations for slow queries, want to optimize query performance, want to analyze workload for indexing opportunities, or provide specific SQL statements for index analysis. Triggers on requests like "recommend indexes for this query", "why is this SQL slow", "analyze workload indexes", "what indexes should I create", "optimize this query", or any YashanDB index tuning task.
---

# YashanDB Index Advisor

Analyze slow queries and recommend optimal indexes using `yasql` CLI + AI reasoning.

## Configuration

### YASQL_HOME (Server-side, pre-configured)

```bash
# Correct argument order: -S must come BEFORE the connection string
LD_LIBRARY_PATH=$YASQL_HOME/lib $YASQL_HOME/bin/yasql -S $YAS_DB_URI -c "<SQL>"
```

If `YASQL_HOME` is not set, try `which yasql`. If not found, stop and tell the user.

> 🔒 **Security Rule**: Never output plaintext passwords. Always mask: `user/****@host:port`

## Workflow

> ⚠️ **MANDATORY FIRST ACTION**: Execute **Step 0** before anything else. Do NOT query the database, run shell commands, or proceed to Step 1/2 until `YAS_DB_URI` is confirmed.

### Mode A: Workload Analysis (no SQL provided)

Step 0 → Step 1 → Step 2 → Step 3 → Step 4

### Mode B: Specific SQL Analysis (SQL provided by user)

Step 0 → Step 2 → Step 3 → Step 4

---

## Step 0: Confirm Target Database (MANDATORY — run THIS FIRST)

**Immediately route based on the inbound message content:**

```
IF   message contains "db=<VALUE>"  (button callback pattern)
     → parse alias from after "db="
     → go to Step 0-C

ELSE IF  message contains a known alias name OR "user/pass@host:port" pattern
     → resolve YAS_DB_URI directly
     → go to Step 1 (or Step 2 if SQL was provided)

ELSE
     → STOP. Go to Step 0-A immediately. Do NOT run any SQL or shell command.
```

### Step 0-A: Read available aliases

Run **only** this command (nothing else):

```bash
grep -E '^[[:space:]]*alias[[:space:]]+' ~/.yashandb_aliases 2>/dev/null \
  | sed 's/.*alias[[:space:]]\+\([A-Za-z0-9_-]\+\)=.*/\1/'
```

- Collect all alias names into a list.
- If the file does not exist or returns no output → skip to Step 0-A-fallback.
- Otherwise → go to Step 0-B.

**Step 0-A-fallback** (no aliases found): Reply with plain text:

> `"Which database? Please provide an alias (e.g. prod) or a connection string (user/pass@host:port)."`
> Then **WAIT**. Do NOT continue.

### Step 0-B: Show database selection buttons (Telegram inline keyboard)

Send **immediately** using the `message` tool:

- `action=send`
- `message="Which database would you like to analyze?"`
- `buttons` — one button per alias. Group up to 3 per row.

Button spec for each `<ALIAS>`:

- **label**: `<ALIAS>` (alias name only, no extra text)
- **callback_data**: `yashandb index advisor db=<ALIAS>`

Example output for aliases `prod`, `staging`, `dev`:

```
Row 1: [ prod ]    callback_data="yashandb index advisor db=prod"
Row 2: [ staging ] callback_data="yashandb index advisor db=staging"
Row 3: [ dev ]     callback_data="yashandb index advisor db=dev"
```

> **Prefix rule**: `callback_data` MUST start with `yashandb index advisor` — this re-triggers the skill on click.

After sending buttons, **STOP and WAIT** for the user's selection. Do NOT proceed.

### Step 0-C: Receive button callback — resolve database

Triggered when inbound message matches `yashandb index advisor db=<ALIAS>`.

- Extract `<ALIAS>` = value after `db=` (trim whitespace).
- Run:
  ```bash
  grep "alias ${ALIAS}=" ~/.yashandb_aliases
  ```
- Parse the connection string and set `YAS_DB_URI`.
- If alias not found → reply: `"Alias '<ALIAS>' not found in ~/.yashandb_aliases. Please type a connection string directly."` then STOP.
- If resolved successfully → **proceed to Step 1** (or Step 2 if SQL was already provided).

---

## Step 1: Get Top Slow Queries

```sql
SELECT * FROM (
    SELECT SQL_ID, PARSING_SCHEMA_NAME,
        ROUND(DECODE(EXECUTIONS,0,0,ELAPSED_TIME/EXECUTIONS)/1000, 3) AS AVG_ELAPSED_MS,
        EXECUTIONS, SQL_TEXT
    FROM V$SQLAREA
    WHERE PARSING_SCHEMA_NAME NOT IN ('SYS','SYSTEM','MDSYS','XA_SYS','DBSNMP','OUTLN')
    ORDER BY AVG_ELAPSED_MS DESC
) WHERE ROWNUM <= 5
```

## Step 2: For Each Target SQL — Gather Context

Run as a single `-f` file to keep one session:

```bash
cat > /tmp/yasql_index_ctx.sql << 'EOF'
-- 2a. Execution Plan
EXPLAIN PLAN FOR
<target SQL here>;

-- 2b. Tables involved: get columns + stats
SELECT C.COLUMN_NAME, C.DATA_TYPE, C.NULLABLE,
       CS.NUM_DISTINCT, CS.NUM_NULLS, CS.DENSITY, CS.AVG_COL_LEN
FROM ALL_TAB_COLS C, ALL_TAB_COL_STATISTICS CS
WHERE C.OWNER = CS.OWNER AND C.TABLE_NAME = CS.TABLE_NAME
  AND C.COLUMN_NAME = CS.COLUMN_NAME
  AND C.OWNER = 'SCHEMA' AND C.TABLE_NAME = 'TABLE_NAME'
ORDER BY C.COLUMN_ID;

-- 2c. Existing indexes
SELECT IND.INDEX_NAME, IND.INDEX_TYPE, IND.UNIQUENESS,
       COLS.COLUMN_NAME, COLS.COLUMN_POSITION,
       IND.BLEVEL, IND.DISTINCT_KEYS, IND.NUM_ROWS
FROM ALL_INDEXES IND, ALL_IND_COLUMNS COLS
WHERE IND.INDEX_NAME = COLS.INDEX_NAME AND IND.OWNER = COLS.INDEX_OWNER
  AND IND.TABLE_NAME = COLS.TABLE_NAME
  AND IND.TABLE_OWNER = 'SCHEMA' AND IND.TABLE_NAME = 'TABLE_NAME'
ORDER BY IND.INDEX_NAME, COLS.COLUMN_POSITION;

-- 2d. Table row count and stats freshness
SELECT NUM_ROWS, LAST_ANALYZED, BLOCKS
FROM ALL_TABLES
WHERE OWNER = 'SCHEMA' AND TABLE_NAME = 'TABLE_NAME';
EOF
LD_LIBRARY_PATH=$YASQL_HOME/lib $YASQL_HOME/bin/yasql -S $YAS_DB_URI -f /tmp/yasql_index_ctx.sql
```

Replace `SCHEMA` and `TABLE_NAME` with actual values extracted from the SQL.

## Step 3: AI Analysis & Recommendation

After gathering all context, reason through:

1. **Execution plan diagnosis**: Is it `TABLE ACCESS FULL` when it should use an index? Wrong join method?
2. **Column selectivity**: `NUM_DISTINCT / NUM_ROWS` — columns with high selectivity (close to 1.0) are best candidates
3. **WHERE clause columns**: columns in filters should be leading index columns
4. **JOIN columns**: foreign key / join columns benefit from indexes
5. **Existing index overlap**: avoid creating indexes that duplicate existing ones
6. **Stale stats**: if `LAST_ANALYZED` is NULL or >30 days old, recommend `DBMS_STATS.GATHER_TABLE_STATS` first

## Step 4: Output Recommendations

For each recommended index, provide:

```sql
-- Reason: <why this index helps>
CREATE INDEX idx_<table>_<cols> ON <schema>.<table> (<col1>, <col2>);
```

Also state:

- **Expected benefit**: which query operation it will change (e.g., full scan → index range scan)
- **Risk**: any rebuild/maintenance cost for large tables
- **Priority**: High / Medium / Low based on query frequency × time saved
