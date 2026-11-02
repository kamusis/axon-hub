#!/usr/bin/env bash
# start_detached.sh — Launch a preview service in the background and record its PID.
set -eo pipefail

CWD=""
LOG=""
PID_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --cwd) CWD="$2"; shift 2 ;;
        --log) LOG="$2"; shift 2 ;;
        --pid-file) PID_FILE="$2"; shift 2 ;;
        --) shift; break ;;
        *) break ;;
    esac
done

if [ -z "$CWD" ] || [ -z "$LOG" ] || [ -z "$PID_FILE" ] || [ $# -eq 0 ]; then
    echo "Usage: $0 --cwd <dir> --log <log-file> --pid-file <pid-file> <cmd...>" >&2
    exit 1
fi

mkdir -p "$(dirname "$LOG")" "$(dirname "$PID_FILE")"

(
    cd "$CWD"
    # Auto-discover and source workspace environment variables so port/API never drifts
    if [ -f .env.worktree ]; then
        set -a; source .env.worktree; set +a
    elif [ -f .env.local ]; then
        set -a; source .env.local; set +a
    elif [ -f .env ]; then
        set -a; source .env; set +a
    fi

    nohup "$@" > "$LOG" 2>&1 &
    echo $! > "$PID_FILE"
)
