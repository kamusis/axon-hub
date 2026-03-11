---
name: yashandb-space
description: Analyze YashanDB tablespace and disk space usage using the yasql CLI. Use this skill for daily space monitoring, capacity planning, finding space-consuming objects, detecting tablespace near-full alerts, checking autoextend status, or identifying the largest tables and segments. Triggers on requests like "check tablespace usage", "which tablespace is almost full", "find the largest tables", "space usage report", "disk space analysis", "tablespace capacity", or any YashanDB storage/space management task.
---

# YashanDB Space Analyzer

Monitor tablespace usage and identify storage issues using `yasql` CLI.

## Configuration

### YASQL_HOME (Server-side, pre-configured)

```bash
LD_LIBRARY_PATH=$YASQL_HOME/lib $YASQL_HOME/bin/yasql -S $YAS_DB_URI -c "<SQL>"
```

If `YASQL_HOME` is not set, try `which yasql`. If not found, stop and tell the user.

### Database Connection (Per-task, provided by DBA)

Resolve `YAS_DB_URI` in this order:

1. **Named alias** → look up `~/.yashandb_aliases`
2. **Inline** `user/password@host:port` → use as-is
3. **Not found** → ask the user

> 🔒 **Security Rule**: Never output plaintext passwords. Always mask: `user/****@host:port`

## Space Checks

Run full analysis or individual sections based on user request.

---

### 1. Tablespace Usage Summary (run first, always)

```sql
SELECT
    t.TABLESPACE_NAME,
    ROUND(t.TOTAL_MB, 1)                              AS TOTAL_MB,
    ROUND(t.TOTAL_MB - NVL(f.FREE_MB, 0), 1)         AS USED_MB,
    ROUND(NVL(f.FREE_MB, 0), 1)                       AS FREE_MB,
    ROUND((t.TOTAL_MB - NVL(f.FREE_MB, 0)) / NULLIF(t.TOTAL_MB, 0) * 100, 1) AS PCT_USED
FROM (
    SELECT TABLESPACE_NAME, SUM(BYTES) / 1048576 AS TOTAL_MB
    FROM DBA_DATA_FILES
    GROUP BY TABLESPACE_NAME
) t
LEFT JOIN (
    SELECT TABLESPACE_NAME, SUM(BYTES) / 1048576 AS FREE_MB
    FROM DBA_FREE_SPACE
    GROUP BY TABLESPACE_NAME
) f ON t.TABLESPACE_NAME = f.TABLESPACE_NAME
ORDER BY PCT_USED DESC
```

**Alert thresholds**: `PCT_USED > 85%` → ⚠️ Warning, `PCT_USED > 95%` → 🔴 Critical

---

### 2. Datafiles with Autoextend Status

```sql
SELECT
    TABLESPACE_NAME,
    FILE_NAME,
    ROUND(BYTES / 1048576, 1)    AS SIZE_MB,
    ROUND(MAXBYTES / 1048576, 1) AS MAX_MB,
    AUTOEXTENSIBLE,
    INCREMENT_BY * 8 / 1024      AS INCREMENT_MB
FROM DBA_DATA_FILES
ORDER BY TABLESPACE_NAME, FILE_NAME
```

Flag: `AUTOEXTENSIBLE = 'NO'` on a tablespace with `PCT_USED > 80%` is high risk.

---

### 3. Top 20 Largest Segments (Tables, Indexes, LOBs)

```sql
SELECT OWNER, SEGMENT_NAME, SEGMENT_TYPE,
       TABLESPACE_NAME,
       ROUND(SUM(BYTES) / 1048576, 1) AS SIZE_MB
FROM DBA_SEGMENTS
WHERE OWNER NOT IN ('SYS','SYSTEM','MDSYS','XA_SYS','DBSNMP','OUTLN')
GROUP BY OWNER, SEGMENT_NAME, SEGMENT_TYPE, TABLESPACE_NAME
ORDER BY SIZE_MB DESC
FETCH FIRST 20 ROWS ONLY
```

---

### 4. Tables with High Empty Block Ratio (candidates for shrink/move)

```sql
SELECT OWNER, TABLE_NAME, TABLESPACE_NAME,
       NUM_ROWS, BLOCKS, EMPTY_BLOCKS,
       ROUND(EMPTY_BLOCKS / NULLIF(BLOCKS + EMPTY_BLOCKS, 0) * 100, 1) AS EMPTY_PCT,
       LAST_ANALYZED
FROM DBA_TABLES
WHERE OWNER NOT IN ('SYS','SYSTEM','MDSYS','XA_SYS','DBSNMP','OUTLN')
  AND BLOCKS > 100
  AND EMPTY_BLOCKS / NULLIF(BLOCKS + EMPTY_BLOCKS, 0) > 0.3
ORDER BY EMPTY_PCT DESC
```

---

### 5. Temp Tablespace Usage (for sort/hash operations)

```sql
SELECT TABLESPACE_NAME,
       ROUND(ALLOCATED_SPACE / 1048576, 1)  AS ALLOCATED_MB,
       ROUND(FREE_SPACE / 1048576, 1)        AS FREE_MB,
       ROUND((ALLOCATED_SPACE - FREE_SPACE) / NULLIF(ALLOCATED_SPACE, 0) * 100, 1) AS PCT_USED
FROM DBA_TEMP_FREE_SPACE
ORDER BY PCT_USED DESC
```

---

## Reporting Guidelines

After running checks, provide:

1. **Tablespace status table** with color-coded alerts (Critical/Warning/OK)
2. **Key findings**: any tablespace >85%, files without autoextend, top space consumers
3. **Recommended actions**:
   - Add datafile: `ALTER TABLESPACE <ts> ADD DATAFILE '<path>' SIZE 1G AUTOEXTEND ON NEXT 256M`
   - Enable autoextend: `ALTER DATABASE DATAFILE '<path>' AUTOEXTEND ON NEXT 256M MAXSIZE 10G`
   - Shrink table: `ALTER TABLE <schema>.<table> SHRINK SPACE`
