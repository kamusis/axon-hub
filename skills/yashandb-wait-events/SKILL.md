---
name: yashandb-wait-events
description: Analyze YashanDB wait events and session performance using the yasql CLI. Use this skill for deep performance diagnosis when queries are slow without obvious cause, to identify system-wide bottlenecks (I/O, locking, CPU, network), or to correlate wait events with specific sessions and SQL. Triggers on requests like "what is the database waiting on", "why is performance slow", "analyze wait events", "what are the top waits", "session wait analysis", "I/O bottleneck", "latch contention", or any YashanDB performance root-cause diagnosis.
---

# YashanDB Wait Events Analyzer

Deep performance diagnosis using wait event data from `yasql` CLI.

> ⚠️ **YashanDB vs Oracle differences (verified)**:
>
> - Use `WAIT_EVENT` in `V$SESSION` (not `EVENT`)
> - `V$SESSION` has no `SECONDS_IN_WAIT` or `P1/P2/P3` columns
> - `V$SESSION_WAIT` has only `SID` and `WAIT_EVENT` columns
> - `V$WAIT_CLASS` does **not** exist — use `WAIT_CLASS` column in `V$SYSTEM_EVENT`

## Configuration

### YASQL_HOME (Server-side, pre-configured)

```bash
# Correct argument order: -S before connection string
LD_LIBRARY_PATH=$YASQL_HOME/lib $YASQL_HOME/bin/yasql -S $YAS_DB_URI -c "<SQL>"
```

If `YASQL_HOME` is not set, try `which yasql`. If not found, stop and tell the user.

### Database Connection (Per-task, provided by DBA)

Resolve `YAS_DB_URI` in this order:

1. **Named alias** → look up `~/.yashandb_aliases`
2. **Inline** `user/password@host:port` → use as-is
3. **Not found** → ask the user

> 🔒 **Security Rule**: Never output plaintext passwords. Always mask: `user/****@host:port`

---

## Step 1: System-Wide Wait Summary (Start Here)

This gives the overall performance picture. Run first.

```sql
-- Top wait events by total time (non-idle)
SELECT EVENT, WAIT_CLASS, TOTAL_WAITS,
       ROUND(TIME_WAITED / 100, 2)                                        AS TIME_WAITED_SEC,
       ROUND(AVERAGE_WAIT / 100, 4)                                       AS AVG_WAIT_SEC,
       TOTAL_TIMEOUTS
FROM V$SYSTEM_EVENT
WHERE WAIT_CLASS != 'Idle'
ORDER BY TIME_WAITED DESC
```

```sql
-- Wait class summary (group by class)
SELECT WAIT_CLASS,
       SUM(TOTAL_WAITS)                                                   AS TOTAL_WAITS,
       ROUND(SUM(TIME_WAITED) / 100, 2)                                   AS TOTAL_TIME_SEC,
       ROUND(SUM(TIME_WAITED) / NULLIF(SUM(TOTAL_WAITS), 0) / 100, 4)   AS AVG_WAIT_SEC
FROM V$SYSTEM_EVENT
WHERE WAIT_CLASS != 'Idle'
GROUP BY WAIT_CLASS
ORDER BY TOTAL_TIME_SEC DESC
```

**Wait class interpretation**:

| Wait Class      | Meaning                         | Typical cause                     |
| --------------- | ------------------------------- | --------------------------------- |
| `Commit`        | Redo log sync on commit         | High DML frequency, slow disk     |
| `User I/O`      | Data file reads                 | Missing indexes, full table scans |
| `System I/O`    | Log file writes                 | Redo log I/O bottleneck           |
| `Concurrency`   | Internal latch/lock waits       | Hot blocks, shared pool pressure  |
| `Application`   | Row-level lock waits (row lock) | Application lock contention       |
| `Network`       | SQL\*Net / client communication | Network latency, slow client      |
| `Configuration` | Log switch waits                | Redo log too small                |

---

## Step 2: Current Session Wait State

```sql
SELECT SID, SERIAL#, USERNAME, STATUS, WAIT_EVENT, WAIT_CLASS,
       SQL_ID, MODULE, MACHINE, LOGON_TIME
FROM V$SESSION
WHERE TYPE = 'USER'
ORDER BY STATUS DESC, WAIT_CLASS, SID
```

Focus on sessions where:

- `WAIT_EVENT` is not empty and `WAIT_CLASS != 'Idle'` → actively waiting
- `STATUS = 'ACTIVE'` with a non-null `WAIT_EVENT` → currently in a wait

---

## Step 3: Correlate Wait Sessions with SQL

When a session is found waiting in Step 2, get its SQL text:

```sql
SELECT s.SID, s.USERNAME, s.WAIT_EVENT, s.WAIT_CLASS, s.SQL_ID,
       sq.SQL_TEXT, sq.EXECUTIONS,
       ROUND(sq.ELAPSED_TIME / 1000, 2) AS TOTAL_ELAPSED_MS
FROM V$SESSION s
LEFT JOIN V$SQLAREA sq ON s.SQL_ID = sq.SQL_ID
WHERE s.TYPE = 'USER'
  AND s.WAIT_EVENT IS NOT NULL
  AND s.WAIT_EVENT != ''
ORDER BY s.WAIT_CLASS, s.SID
```

---

## Step 4: Top SQL by Elapsed Time (Hotspot SQL)

```sql
SELECT SQL_ID, PARSING_SCHEMA_NAME,
       ROUND(ELAPSED_TIME / 1000, 2)                                              AS TOTAL_ELAPSED_MS,
       EXECUTIONS,
       ROUND(DECODE(EXECUTIONS, 0, 0, ELAPSED_TIME / EXECUTIONS) / 1000, 3)     AS AVG_ELAPSED_MS,
       ROUND(DECODE(EXECUTIONS, 0, 0, BUFFER_GETS / EXECUTIONS), 1)             AS AVG_BUFFER_GETS,
       ROUND(DECODE(EXECUTIONS, 0, 0, DISK_READS / EXECUTIONS), 1)              AS AVG_DISK_READS,
       SUBSTR(SQL_TEXT, 1, 100) AS SQL_PREVIEW
FROM V$SQLAREA
WHERE PARSING_SCHEMA_NAME NOT IN ('SYS','SYSTEM','MDSYS','XA_SYS','DBSNMP','OUTLN')
  AND ELAPSED_TIME > 0
ORDER BY ELAPSED_TIME DESC
```

---

## Step 5: Blocking Sessions (Lock Waits)

```sql
SELECT SID, SERIAL#, USERNAME, STATUS, WAIT_EVENT, LOCKWAIT, SQL_ID, MACHINE
FROM V$SESSION
WHERE TYPE = 'USER'
  AND LOCKWAIT IS NOT NULL
ORDER BY SID
```

If results found → escalate to the `yashandb-locks` skill for full lock analysis.

---

## Diagnosis Guide

### High `Commit` wait time

→ Too many small commits. Recommend batch commits or async commit.

### High `User I/O` (db file sequential / scattered read)

→ Missing indexes or full table scans. Use `EXPLAIN PLAN FOR` on top SQL. Escalate to `yashandb-index-advisor`.

### High `System I/O` (log file parallel write / sync)

→ Redo log bottleneck. Check redo log file location (should be on fast disk, separate from data files).

### High `Concurrency` (exclusive lock wait / buffer busy)

→ Hot block contention or shared pool issues. Check top SQL for repeated access to same blocks.

### High `Configuration` (log file switch)

→ Redo log groups too small, causing frequent switches. Recommend increasing log file size.

### High `Application` wait

→ Row-level locking between sessions. Use `yashandb-locks` skill to identify blocking chain.
