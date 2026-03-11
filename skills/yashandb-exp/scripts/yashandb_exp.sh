#!/usr/bin/env bash
# yashandb_exp.sh — YashanDB data export wrapper
#
# Usage:
#   yashandb_exp.sh <format> <mode> <output_dir> [mode_value]
#
# Arguments:
#   format      : meta | sql | csv
#   mode        : full | owner | tables
#   output_dir  : directory for output files (created if not exists)
#   mode_value  : required for owner/tables; comma-separated names
#                 For owner mode  : "SCHEMA1,SCHEMA2"
#                 For tables mode : "TABLE1,TABLE2" or "SCHEMA.TABLE1,TABLE2"
#
# Required environment variables:
#   YAS_DB_URI  : user/password@host:port
#   YASQL_HOME  : YashanDB client installation directory
#
# Optional environment variables:
#   ROWS                  : Y|N  — include table data in meta export (default: Y)
#   FIELDS_TERMINATED_BY  : CSV field separator            (default: ,)
#   FIELDS_ENCLOSED_BY    : CSV quote character            (default: ")
#
# Examples:
#   # Export full database as binary dump
#   yashandb_exp.sh meta full /backup/20250303
#
#   # Export KAMUS schema objects + data as binary dump
#   yashandb_exp.sh meta owner /backup/20250303 KAMUS
#
#   # Export specific tables as binary dump (schema-only, no data)
#   ROWS=N yashandb_exp.sh meta tables /backup/20250303 ECOM_ORDER,PRODUCT
#
#   # Export KAMUS schema DDL as SQL file
#   yashandb_exp.sh sql owner /backup/20250303 KAMUS
#
#   # Export tables as CSV into /data/csv_out/
#   yashandb_exp.sh csv tables /data/csv_out KAMUS ECOM_ORDER,PRODUCT

set -euo pipefail

# ─── Argument parsing ────────────────────────────────────────────────────────
FORMAT="${1:-}"       # meta | sql | csv
MODE="${2:-}"         # full | owner | tables
OUTPUT_DIR="${3:-}"   # output directory path
MODE_VALUE="${4:-}"   # user/table names (comma-separated)

if [[ -z "$FORMAT" || -z "$MODE" || -z "$OUTPUT_DIR" ]]; then
    echo "Usage: $0 <format> <mode> <output_dir> [mode_value]"
    echo ""
    echo "  format:     meta | sql | csv"
    echo "  mode:       full | owner | tables"
    echo "  output_dir: directory for output files"
    echo "  mode_value: required for owner/tables mode"
    echo ""
    echo "Environment: YAS_DB_URI=user/pass@host:port  YASQL_HOME=/path/to/yasql"
    exit 1
fi

# ─── Validate environment ────────────────────────────────────────────────────
if [[ -z "${YAS_DB_URI:-}" ]]; then
    echo "ERROR: YAS_DB_URI is not set. Example: export YAS_DB_URI=sys/pass@localhost:1688" >&2
    exit 1
fi

# Find exp binary: prefer $YASQL_HOME/bin/exp, fall back to PATH
EXP_BIN=""
if [[ -n "${YASQL_HOME:-}" && -x "$YASQL_HOME/bin/exp" ]]; then
    EXP_BIN="$YASQL_HOME/bin/exp"
elif command -v exp &>/dev/null; then
    EXP_BIN="$(command -v exp)"
else
    echo "ERROR: 'exp' binary not found." >&2
    echo "       Ensure YASQL_HOME is set correctly, or add exp to PATH." >&2
    exit 1
fi

# Set LD_LIBRARY_PATH scoped to this script only
if [[ -n "${YASQL_HOME:-}" ]]; then
    export LD_LIBRARY_PATH="$YASQL_HOME/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi

# ─── Parse connection string ─────────────────────────────────────────────────
# YAS_DB_URI format: user/password@host:port
DB_USER=$(echo "$YAS_DB_URI" | sed 's|/.*||')
DB_PASS=$(echo "$YAS_DB_URI" | sed 's|[^/]*/||; s|@.*||')
DB_HOST=$(echo "$YAS_DB_URI" | sed 's|.*@||')

# ─── Prepare output directory and timestamp ───────────────────────────────────
mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# ─── Helper: query all table names in a schema ───────────────────────────────
# exp --csv requires an explicit 'tables' list even in owner mode.
# This function auto-fetches the list from DBA_TABLES using yasql.
get_schema_tables() {
    local schema="$1"
    local result
    result=$("$YASQL_HOME/bin/yasql" -S "$YAS_DB_URI" \
        -c "SELECT TABLE_NAME FROM DBA_TABLES WHERE OWNER = UPPER('$schema') ORDER BY TABLE_NAME" 2>/dev/null \
        | grep -v '^TABLE_NAME\|^-\+\|^$\|rows fetched' \
        | awk '{gsub(/[[:space:]]/, ""); if (length($0)>0) print}' \
        | paste -sd ',')
    echo "$result"
}

# ─── Execute export ───────────────────────────────────────────────────────────
case "$FORMAT" in

  # ── Binary metadata dump ────────────────────────────────────────────────────
  meta)
    OUTPUT_FILE="$OUTPUT_DIR/export_meta_${MODE}_${TIMESTAMP}.dump"
    ROWS_OPT="${ROWS:-Y}"

    case "$MODE" in
      full)
        echo "[EXP] Starting full-database metadata export → $OUTPUT_FILE"
        "$EXP_BIN" "$YAS_DB_URI" \
            FILE="$OUTPUT_FILE" \
            FULL=Y \
            ROWS="$ROWS_OPT" \
            LOG_PATH="$OUTPUT_DIR" \
            LOG_LEVEL=INFO
        ;;
      owner)
        [[ -z "$MODE_VALUE" ]] && { echo "ERROR: owner mode requires mode_value (schema names)" >&2; exit 1; }
        echo "[EXP] Starting owner metadata export: schemas=$MODE_VALUE → $OUTPUT_FILE"
        "$EXP_BIN" "$YAS_DB_URI" \
            FILE="$OUTPUT_FILE" \
            OWNER="$MODE_VALUE" \
            ROWS="$ROWS_OPT" \
            LOG_PATH="$OUTPUT_DIR" \
            LOG_LEVEL=INFO
        ;;
      tables)
        [[ -z "$MODE_VALUE" ]] && { echo "ERROR: tables mode requires mode_value (table names)" >&2; exit 1; }
        echo "[EXP] Starting tables metadata export: tables=$MODE_VALUE → $OUTPUT_FILE"
        "$EXP_BIN" "$YAS_DB_URI" \
            FILE="$OUTPUT_FILE" \
            TABLES="$MODE_VALUE" \
            ROWS="$ROWS_OPT" \
            LOG_PATH="$OUTPUT_DIR" \
            LOG_LEVEL=INFO
        ;;
      *) echo "ERROR: Unknown mode '$MODE'. Use: full | owner | tables" >&2; exit 1 ;;
    esac
    echo "[EXP] Done. Output file : $OUTPUT_FILE"
    echo "[EXP] Log directory     : $OUTPUT_DIR"
    ;;

  # ── SQL DDL export ──────────────────────────────────────────────────────────
  sql)
    # Note: SQL mode exports DDL only — ROWS is always N (no data)
    OUTPUT_FILE="$OUTPUT_DIR/export_sql_${MODE}_${TIMESTAMP}.sql"

    case "$MODE" in
      full)
        echo "[EXP-SQL] Starting full-database SQL DDL export → $OUTPUT_FILE"
        "$EXP_BIN" --sql "$YAS_DB_URI" \
            FILE="$OUTPUT_FILE" \
            FULL=Y \
            ROWS=N \
            LOG_PATH="$OUTPUT_DIR" \
            LOG_LEVEL=INFO
        ;;
      owner)
        [[ -z "$MODE_VALUE" ]] && { echo "ERROR: owner mode requires mode_value (schema names)" >&2; exit 1; }
        echo "[EXP-SQL] Starting owner SQL DDL export: schemas=$MODE_VALUE → $OUTPUT_FILE"
        "$EXP_BIN" --sql "$YAS_DB_URI" \
            FILE="$OUTPUT_FILE" \
            OWNER="$MODE_VALUE" \
            ROWS=N \
            LOG_PATH="$OUTPUT_DIR" \
            LOG_LEVEL=INFO
        ;;
      tables)
        [[ -z "$MODE_VALUE" ]] && { echo "ERROR: tables mode requires mode_value (table names)" >&2; exit 1; }
        echo "[EXP-SQL] Starting tables SQL DDL export: tables=$MODE_VALUE → $OUTPUT_FILE"
        "$EXP_BIN" --sql "$YAS_DB_URI" \
            FILE="$OUTPUT_FILE" \
            TABLES="$MODE_VALUE" \
            ROWS=N \
            LOG_PATH="$OUTPUT_DIR" \
            LOG_LEVEL=INFO
        ;;
      *) echo "ERROR: Unknown mode '$MODE'. Use: full | owner | tables" >&2; exit 1 ;;
    esac
    echo "[EXP-SQL] Done. Output file : $OUTPUT_FILE"
    echo "[EXP-SQL] Log directory     : $OUTPUT_DIR"
    ;;

  # ── CSV data export ─────────────────────────────────────────────────────────
  # Uses config-file approach to avoid shell quoting complexity with delimiters.
  csv)
    FIELDS_SEP="${FIELDS_TERMINATED_BY:-,}"
    FIELDS_ENC="${FIELDS_ENCLOSED_BY:-\"}"
    CONF_FILE="/tmp/yasdb_exp_$$.ini"

    # Ensure config file is always cleaned up on exit
    trap 'rm -f "$CONF_FILE"' EXIT

    case "$MODE" in
      full|owner)
        OWNER_VAL="${MODE_VALUE:-$DB_USER}"
        echo "[EXP-CSV] Fetching table list for schema '$OWNER_VAL' from database..."
        TABLE_LIST=$(get_schema_tables "$OWNER_VAL")
        if [[ -z "$TABLE_LIST" ]]; then
            echo "ERROR: No tables found in schema '$OWNER_VAL'. Check the schema name and permissions." >&2
            exit 1
        fi
        echo "[EXP-CSV] Tables to export: $TABLE_LIST"
        echo "[EXP-CSV] Output directory: $OUTPUT_DIR"
        cat > "$CONF_FILE" <<INIEOF
format = csv
user = $DB_USER
password = $DB_PASS
server-host = $DB_HOST
owner = $OWNER_VAL
tables = $TABLE_LIST
file = $OUTPUT_DIR
logfile = $OUTPUT_DIR
loglevel = info
fields-enclosed-by = $FIELDS_ENC
fields-terminated-by = $FIELDS_SEP
INIEOF
        ;;
      tables)
        [[ -z "$MODE_VALUE" ]] && { echo "ERROR: tables mode requires mode_value (table names)" >&2; exit 1; }

        # Handle optional "SCHEMA.TABLE" prefix in mode_value
        # e.g. "KAMUS.ECOM_ORDER,KAMUS.PRODUCT" → owner=KAMUS, tables=ECOM_ORDER,PRODUCT
        if echo "$MODE_VALUE" | grep -q '\.'; then
            OWNER_VAL=$(echo "$MODE_VALUE" | cut -d'.' -f1 | cut -d',' -f1)
            # Strip "SCHEMA." prefix from every table name in the comma-separated list
            TABLE_LIST=$(echo "$MODE_VALUE" | tr ',' '\n' | sed 's/^[^.]*\.//; s/^[[:space:]]*//; s/[[:space:]]*$//' | paste -sd ',')
        else
            OWNER_VAL="$DB_USER"
            TABLE_LIST="$MODE_VALUE"
        fi

        echo "[EXP-CSV] Exporting tables '$TABLE_LIST' from schema '$OWNER_VAL' to $OUTPUT_DIR"
        cat > "$CONF_FILE" <<INIEOF
format = csv
user = $DB_USER
password = $DB_PASS
server-host = $DB_HOST
owner = $OWNER_VAL
tables = $TABLE_LIST
file = $OUTPUT_DIR
logfile = $OUTPUT_DIR
loglevel = info
fields-enclosed-by = $FIELDS_ENC
fields-terminated-by = $FIELDS_SEP
INIEOF
        ;;
      *) echo "ERROR: Unknown mode '$MODE'. Use: full | owner | tables" >&2; exit 1 ;;
    esac

    "$EXP_BIN" --csv --config-file "$CONF_FILE"
    echo "[EXP-CSV] Done. CSV files written to: $OUTPUT_DIR"
    ;;

  *)
    echo "ERROR: Unknown format '$FORMAT'. Use: meta | sql | csv" >&2
    exit 1
    ;;
esac
