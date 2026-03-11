---
name: yashandb-exp
description: Export data from YashanDB using the exp CLI tool. Supports three export formats (binary metadata dump, SQL DDL, CSV data) and three scope modes (full database, schema/owner, specific tables). Use this skill when users want to back up a schema, export table data as CSV, generate DDL scripts, or migrate data between environments. Triggers on requests like "export KAMUS schema", "backup the database", "export table data as CSV", "generate DDL for these tables", "dump the schema", or any YashanDB data export task.
---

# YashanDB Data Export (exp)

Export data from YashanDB using the `exp` CLI tool via a managed shell script.

> **Design principle**: The `exp` command syntax differs significantly between formats. This skill uses `scripts/yashandb_exp.sh` to encapsulate all command construction — the agent only needs to determine parameters, never construct raw `exp` commands.

## Configuration

### YASQL_HOME (Server-side, pre-configured)

`YASQL_HOME` must be set on the agent server. The script uses `$YASQL_HOME/bin/exp` and `$YASQL_HOME/lib`.

> If `YASQL_HOME` is not set, the script falls back to `which exp`. If neither works, it exits with an error.

### Database Connection (Per-task, provided by DBA)

Resolve `YAS_DB_URI` in this order:

1. **Named alias** → look up `~/.yashandb_aliases`
2. **Inline** `user/password@host:port` → use as-is
3. **Not found** → ask the user

> 🔒 **Security Rule**: Never output plaintext passwords. Always mask: `user/****@host:port`

---

## Export Formats

| Format   | Flag     | Exports                        | Use case                        |
| -------- | -------- | ------------------------------ | ------------------------------- |
| **meta** | _(none)_ | Binary dump: DDL + data        | Full backup, imp/imp migration  |
| **sql**  | `--sql`  | Plain SQL DDL only (no data)   | Schema recreation, code review  |
| **csv**  | `--csv`  | CSV data files (one per table) | Data analysis, ETL, spreadsheet |

## Export Modes

| Mode       | Scope              | Permission required                       |
| ---------- | ------------------ | ----------------------------------------- |
| **full**   | Entire database    | DBA role                                  |
| **owner**  | Specific schema(s) | DBA role (if exporting other user's data) |
| **tables** | Specific tables    | Owner or DBA                              |

---

## How to Run

Invoke the script from the skill's `scripts/` directory:

```bash
bash <skill_dir>/scripts/yashandb_exp.sh <format> <mode> <output_dir> [mode_value]
```

The `YAS_DB_URI` and `YASQL_HOME` environment variables must be set before calling.

### Parameter Reference

| Parameter    | Values                        | Notes                 |
| ------------ | ----------------------------- | --------------------- |
| `format`     | `meta` \| `sql` \| `csv`      | Export type           |
| `mode`       | `full` \| `owner` \| `tables` | Scope of export       |
| `output_dir` | Any writable path             | Created if not exists |
| `mode_value` | Comma-separated names         | Skip for `full` mode  |

### Optional Environment Variables

| Variable               | Default | Effect                                                  |
| ---------------------- | ------- | ------------------------------------------------------- |
| `ROWS`                 | `Y`     | `meta` only: include table data (`Y`) or DDL only (`N`) |
| `FIELDS_TERMINATED_BY` | `,`     | `csv` only: field separator                             |
| `FIELDS_ENCLOSED_BY`   | `"`     | `csv` only: quote character                             |

---

## Usage Examples

### 1. Export full database (binary dump, with data)

```bash
export YAS_DB_URI=sys/****@localhost:1688
bash scripts/yashandb_exp.sh meta full /backup/$(date +%Y%m%d)
```

### 2. Export a schema as binary dump (DDL only, no data)

```bash
ROWS=N bash scripts/yashandb_exp.sh meta owner /backup/schema_ddl KAMUS
```

### 3. Export schema DDL as readable SQL script

```bash
bash scripts/yashandb_exp.sh sql owner /backup/ddl_scripts KAMUS
```

> Note: `sql` format is DDL only — it never exports row data regardless of `ROWS` setting.

### 4. Export specific tables DDL as SQL

```bash
bash scripts/yashandb_exp.sh sql tables /backup/ddl_scripts ECOM_ORDER,PRODUCT
```

### 5. Export schema data as CSV (standard comma-quoted format)

```bash
bash scripts/yashandb_exp.sh csv owner /data/csv_export KAMUS
```

Output: one CSV file per table in `/data/csv_export/`, named by table name.

### 6. Export specific tables as CSV with custom delimiter

```bash
FIELDS_TERMINATED_BY='|' FIELDS_ENCLOSED_BY='' \
  bash scripts/yashandb_exp.sh csv tables /data/csv_export KAMUS ECOM_ORDER,PRODUCT
```

> Setting `FIELDS_ENCLOSED_BY` to empty removes quoting. Use this only if data contains no delimiter characters.

### 7. Export tables with schema prefix

```bash
bash scripts/yashandb_exp.sh csv tables /data/csv_export KAMUS.ECOM_ORDER,PRODUCT
# Script auto-extracts schema "KAMUS" and strips prefix from table list
```

---

## Workflow: What the Agent Should Do

1. **Understand the request**: identify format, mode, and target (schema or tables)
2. **Resolve connection**: get `YAS_DB_URI` from alias or user input
3. **Confirm output directory**: ask user if not specified, suggest `/tmp/yasdb_exp_<date>`
4. **Confirm destructive scope** (for `full` mode): ask before running
5. **Run the script**: construct the exact call with resolved parameters
6. **Report results**: show output file path, size, any errors from stdout

---

## Format Decision Guide

Ask the user which export format they need if not specified:

- **"I need to restore this to another database"** → `meta` (binary imp-compatible)
- **"I need the CREATE TABLE statements"** → `sql`
- **"I need the data in a spreadsheet / pipeline"** → `csv`
- **"I need a full backup"** → `meta full`

---

## Important Notes

- **Existing files are overwritten**: exp overwrites `FILE` if it already exists. The script uses timestamped filenames to avoid this.
- **CSV output is one file per table**, placed in `output_dir`, named by table name **with no `.csv` extension** — this is `exp --csv` CLI behavior by design, not a script issue. Example: exporting `ECOM_ORDER` and `PRODUCT` produces files named `ECOM_ORDER` and `PRODUCT` (not `ECOM_ORDER.csv`).
- **SQL mode never exports data** — it is DDL only. Use `meta` with `ROWS=Y` for data + schema.
- **Cross-schema dependency**: if exporting `OWNER=A` but A's objects depend on schema B, import may fail if B doesn't exist in the target DB.
- **`meta` dump is not human-readable** — it can only be loaded with the `imp` tool.
