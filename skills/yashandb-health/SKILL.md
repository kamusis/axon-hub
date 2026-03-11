---
name: yashandb-health
description: Analyze YashanDB database health and identify performance bottlenecks using the yasql CLI. Use this skill when users want to check database health, find slow or resource-intensive SQL queries, inspect connection usage, detect unusable/duplicate indexes, check sequences nearing limits, review constraint issues, or evaluate SGA buffer usage. Triggers on requests like "check database health", "find slow queries", "top SQL by CPU", "are there any bad indexes", "check connection pool", "any sequences about to overflow", or any YashanDB/Oracle DBA diagnostic task.
---

# YashanDB Health & Performance Analyzer

Diagnose YashanDB database health and identify top SQL using `yasql` CLI.

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
> ✅ `user/****@localhost:1688`
> ❌ `user/real_password@localhost:1688`

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

For multi-statement analysis, write to `/tmp/yasql_health.sql` and use:

```bash
LD_LIBRARY_PATH=$YASQL_HOME/lib $YASQL_HOME/bin/yasql -S $YAS_DB_URI -f /tmp/yasql_health.sql
```

## Health Check Menu

Run checks based on user request. For "all", run every section below.

| Check                            | When to Run                                   |
| -------------------------------- | --------------------------------------------- |
| [Top SQL](#top-sql-performance)  | slow queries, performance issues, high CPU/IO |
| [Connection](#connection-health) | connection pool, session count                |
| [Index](#index-health)           | bad indexes, duplicate indexes, bloat         |
| [Sequence](#sequence-health)     | sequences nearing max value                   |
| [Constraint](#constraint-health) | disabled or invalid constraints               |
| [Buffer/SGA](#buffer--sga)       | memory usage, SGA sizing                      |

---

## Top SQL Performance

Sort options: `AVG_ELAPSED_MS`, `TOTAL_ELAPSED_MS`, `AVG_CPU_MS`, `TOTAL_CPU_MS`, `AVG_BUFFER_GETS`, `TOTAL_BUFFER_GETS`, `AVG_DISK_READS`, `TOTAL_DISK_READS`

```sql
SELECT * FROM (
    SELECT SQL_ID,
        TO_CHAR(LAST_ACTIVE_TIME, 'YYYY-MM-DD HH24:MI:SS') AS LAST_ACTIVE_TIME,
        PARSING_SCHEMA_NAME, MODULE, EXECUTIONS,
        ROUND(ELAPSED_TIME/1000, 2)                                        AS TOTAL_ELAPSED_MS,
        ROUND(CPU_TIME/1000, 2)                                            AS TOTAL_CPU_MS,
        BUFFER_GETS                                                        AS TOTAL_BUFFER_GETS,
        DISK_READS                                                         AS TOTAL_DISK_READS,
        ROUND(DECODE(EXECUTIONS,0,0,ELAPSED_TIME/EXECUTIONS)/1000, 3)     AS AVG_ELAPSED_MS,
        ROUND(DECODE(EXECUTIONS,0,0,CPU_TIME/EXECUTIONS)/1000, 3)         AS AVG_CPU_MS,
        ROUND(DECODE(EXECUTIONS,0,0,BUFFER_GETS/EXECUTIONS), 2)           AS AVG_BUFFER_GETS,
        ROUND(DECODE(EXECUTIONS,0,0,DISK_READS/EXECUTIONS), 2)            AS AVG_DISK_READS,
        SQL_TEXT
    FROM V$SQLAREA
    WHERE PARSING_SCHEMA_NAME NOT IN ('SYS','SYSTEM','MDSYS','XA_SYS','DBSNMP','OUTLN')
    ORDER BY AVG_ELAPSED_MS DESC
) WHERE ROWNUM <= 10
```

After retrieving results, summarize: SQL_ID, schema, execution count, key metric value, and first 120 chars of SQL_TEXT.

---

## Connection Health

```sql
-- Total user sessions
SELECT COUNT(*) AS TOTAL_SESSIONS FROM V$SESSION WHERE TYPE = 'USER';

-- Inactive sessions
SELECT COUNT(*) AS INACTIVE_SESSIONS FROM V$SESSION WHERE TYPE = 'USER' AND STATUS = 'INACTIVE';

-- Sessions by status breakdown
SELECT STATUS, COUNT(*) AS CNT FROM V$SESSION WHERE TYPE = 'USER' GROUP BY STATUS ORDER BY CNT DESC
```

Flag: total > 500 or inactive > 100 as potentially problematic.

---

## Index Health

### Unusable indexes

```sql
SELECT OWNER, INDEX_NAME, TABLE_NAME, STATUS
FROM DBA_INDEXES
WHERE STATUS = 'UNUSABLE'
  AND OWNER NOT IN ('SYS','SYSTEM','MDSYS','XA_SYS','DBSNMP','OUTLN')
ORDER BY OWNER, TABLE_NAME
```

### Large indexes (potential bloat, BLEVEL > 3)

```sql
SELECT i.OWNER, i.TABLE_NAME, i.INDEX_NAME,
       s.BYTES/1048576 AS SIZE_MB,
       i.BLEVEL, i.LEAF_BLOCKS, i.LAST_ANALYZED
FROM DBA_INDEXES i
JOIN DBA_SEGMENTS s ON i.OWNER = s.OWNER AND i.INDEX_NAME = s.SEGMENT_NAME
WHERE s.BYTES >= 104857600
  AND i.INDEX_TYPE = 'NORMAL'
  AND i.OWNER NOT IN ('SYS','MDSYS','XA_SYS')
ORDER BY s.BYTES DESC
```

### Potentially unused indexes (no analysis in 90+ days, non-unique)

```sql
SELECT i.OWNER, i.TABLE_NAME, i.INDEX_NAME,
       NVL(s.BYTES/1048576, 0) AS SIZE_MB, i.LAST_ANALYZED
FROM DBA_INDEXES i
LEFT JOIN DBA_SEGMENTS s ON i.OWNER = s.OWNER AND i.INDEX_NAME = s.SEGMENT_NAME
WHERE i.OWNER NOT IN ('SYS','SYSTEM','OUTLN','DBSNMP','APPQOSSYS','WMSYS','XDB','CTXSYS')
  AND i.UNIQUENESS = 'NONUNIQUE'
  AND i.STATUS = 'VALID'
  AND (i.LAST_ANALYZED IS NULL OR i.LAST_ANALYZED < SYSDATE - 90)
ORDER BY SIZE_MB DESC
```

---

## Sequence Health

```sql
SELECT SEQUENCE_OWNER, SEQUENCE_NAME, LAST_NUMBER, MAX_VALUE,
       ROUND(LAST_NUMBER / NULLIF(MAX_VALUE, 0) * 100, 2) AS PCT_USED
FROM DBA_SEQUENCES
WHERE SEQUENCE_OWNER NOT IN ('SYS','SYSTEM','MDSYS','XA_SYS','DBSNMP','OUTLN')
  AND CYCLE_FLAG = 'N'
  AND MAX_VALUE < 9999999999999999999
  AND (LAST_NUMBER / NULLIF(MAX_VALUE, 0)) > 0.8
ORDER BY PCT_USED DESC
```

Flag sequences where `PCT_USED > 80%` as approaching limit.

---

## Constraint Health

```sql
SELECT OWNER, TABLE_NAME, CONSTRAINT_NAME, CONSTRAINT_TYPE, STATUS, VALIDATED
FROM DBA_CONSTRAINTS
WHERE OWNER NOT IN ('SYS','SYSTEM','MDSYS','XA_SYS','DBSNMP','OUTLN')
  AND (STATUS = 'DISABLED' OR VALIDATED = 'NOT VALIDATED')
ORDER BY OWNER, TABLE_NAME
```

---

## Buffer / SGA

```sql
SELECT POOL, NAME, BYTES/1048576 AS SIZE_MB
FROM V$SGASTAT
ORDER BY BYTES DESC
```

Summarize SGA component sizes and flag any anomalies.

---

## Reporting Guidelines

After running checks, provide a structured summary:

1. **Overall status**: Healthy / Warning / Critical
2. **Findings per check**: bullet points with severity
3. **Recommendations**: actionable next steps (rebuild index, alter sequence, kill idle sessions, etc.)
