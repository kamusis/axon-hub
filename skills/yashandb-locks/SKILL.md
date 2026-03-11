---
name: yashandb-locks
description: Detect, diagnose, and resolve lock contention in YashanDB using the yasql CLI. Use this skill in urgent lock/blocking situations, when operations are hanging, when users report timeouts or deadlocks, or for routine lock monitoring. Triggers on requests like "find blocking sessions", "who is holding the lock", "kill blocking session", "deadlock analysis", "session is waiting", "lock contention", "hung query", or any YashanDB locking or blocking incident.
---

# YashanDB Lock Detector

Diagnose and resolve lock contention in YashanDB using `yasql` CLI.

> ⚠️ **YashanDB vs Oracle differences (verified)**:
>
> - `V$SESSION` has no `BLOCKING_SESSION`, `SECONDS_IN_WAIT`, `EVENT`, or `STATE` columns
> - Use `LOCKWAIT` (not null = session is waiting for a lock) and `WAIT_EVENT` instead
> - `V$LOCK` has no `BLOCK` column — use `LMODE > 0` (holding) and `REQUEST > 0` (waiting)
> - `ALTER SYSTEM KILL SESSION` requires `SID` + `SERIAL#` from `V$SESSION`

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

## ⚡ Urgency Protocol

Lock incidents are **time-sensitive**. Run Step 1 immediately upon receiving a lock report, before asking any clarifying questions.

---

## Step 1: Find Blocking Chain

Sessions with `LOCKWAIT IS NOT NULL` are waiting for a lock. Cross-reference with `V$LOCK` to find the holders.

```sql
-- Find holder-waiter pairs
SELECT
    l2.SID                                          AS WAITING_SID,
    s2.USERNAME                                     AS WAITING_USER,
    s2.STATUS                                       AS WAITING_STATUS,
    s2.WAIT_EVENT                                   AS WAIT_EVENT,
    l1.SID                                          AS HOLDING_SID,
    s1.USERNAME                                     AS HOLDING_USER,
    s1.STATUS                                       AS HOLDING_STATUS,
    s1.SQL_ID                                       AS HOLDING_SQL_ID,
    s1.MACHINE                                      AS HOLDING_MACHINE,
    TO_CHAR(s1.LOGON_TIME, 'HH24:MI:SS')           AS HOLDING_LOGON_TIME
FROM V$LOCK l1, V$LOCK l2, V$SESSION s1, V$SESSION s2
WHERE l1.LMODE > 0
  AND l2.REQUEST > 0
  AND l1.ID1 = l2.ID1
  AND l1.ID2 = l2.ID2
  AND l1.SID != l2.SID
  AND l1.SID = s1.SID
  AND l2.SID = s2.SID
ORDER BY l1.SID
```

If result is empty → use Step 5 (session wait overview) to check other wait events.

---

## Step 2: Identify Locked Objects

```sql
SELECT
    l.SID, s.USERNAME, s.STATUS,
    o.OBJECT_NAME, o.OBJECT_TYPE, o.OWNER,
    l.LMODE, l.REQUEST,
    DECODE(l.LMODE,
        0,'None', 1,'Null', 2,'Row-S(SS)', 3,'Row-X(SX)',
        4,'Share(S)', 5,'S/Row-X(SSX)', 6,'Exclusive(X)', 'Unknown') AS LOCK_MODE
FROM V$LOCK l
JOIN V$SESSION s ON l.SID = s.SID
LEFT JOIN DBA_OBJECTS o ON l.ID1 = o.OBJECT_ID
WHERE l.LMODE > 0
  AND s.USERNAME NOT IN ('SYS','SYSTEM')
ORDER BY s.SID
```

---

## Step 3: Get a Session's Current SQL

```sql
SELECT s.SID, s.SERIAL#, s.USERNAME, s.SQL_ID, sq.SQL_TEXT,
       s.STATUS, s.WAIT_EVENT, s.MODULE
FROM V$SESSION s
LEFT JOIN V$SQLAREA sq ON s.SQL_ID = sq.SQL_ID
WHERE s.SID = <TARGET_SID>
```

Replace `<TARGET_SID>` with SID from Step 1.

---

## Step 4: Deadlock Detection

```sql
SELECT
    l1.SID AS HOLDER_SID, s1.USERNAME AS HOLDER_USER,
    l1.ID1, l1.ID2, l1.LMODE,
    l2.SID AS WAITER_SID, s2.USERNAME AS WAITER_USER,
    l2.REQUEST
FROM V$LOCK l1, V$LOCK l2, V$SESSION s1, V$SESSION s2
WHERE l1.LMODE > 0
  AND l2.REQUEST > 0
  AND l1.ID1 = l2.ID1
  AND l1.ID2 = l2.ID2
  AND l1.SID != l2.SID
  AND l1.SID = s1.SID
  AND l2.SID = s2.SID
ORDER BY l1.ID1
```

A deadlock (A→B→A cycle) shows the same pair appearing in opposite roles. YashanDB will automatically abort one side to resolve true deadlocks.

---

## Step 5: All User Session Wait Overview

```sql
SELECT SID, SERIAL#, USERNAME, STATUS, WAIT_EVENT, WAIT_CLASS,
       LOCKWAIT, SQL_ID, MODULE, MACHINE
FROM V$SESSION
WHERE TYPE = 'USER'
ORDER BY STATUS DESC, WAIT_CLASS, SID
```

Focus on sessions where `LOCKWAIT IS NOT NULL` or `WAIT_CLASS` is `Concurrency` / `Application`.

---

## Step 6: Kill Blocking Session (if authorized)

> ⚠️ **Always confirm with user before killing a session.**
> Show: who is being killed, what they were doing, how long they have been blocking.

First get `SERIAL#`:

```sql
SELECT SID, SERIAL#, USERNAME, STATUS, SQL_ID, WAIT_EVENT
FROM V$SESSION WHERE SID = <HOLDING_SID>
```

Then kill:

```sql
ALTER SYSTEM KILL SESSION '<SID>,<SERIAL#>' IMMEDIATE;
```

---

## Reporting Guidelines

1. **State the severity**: number of waiting sessions, object being locked
2. **Show the full blocking chain** (A → B → C if cascading)
3. **Identify root cause**: long-running uncommitted transaction, missing COMMIT, application bug
4. **Recommended action**: kill session (with exact command) OR wait (if nearly done)
5. **Prevention advice**: shorter transactions, explicit COMMIT after DML, connection pool tuning
