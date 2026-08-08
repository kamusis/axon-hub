#!/usr/bin/env bash

set -euo pipefail

skill_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
script_path="$skill_dir/scripts/detect-merged-worktrees.sh"
test_root=$(mktemp -d "${TMPDIR:-/tmp}/detect-merged-worktrees-test.XXXXXX")
trap 'rm -rf -- "$test_root"' EXIT

seed_repo="$test_root/seed"
bare_repo="$test_root/repository.git"
active_worktree="$test_root/active-worktree"
output_file="$test_root/output.txt"

git init -q --initial-branch=main "$seed_repo"
git -C "$seed_repo" config user.name "Test User"
git -C "$seed_repo" config user.email "test@example.com"
printf 'initial\n' > "$seed_repo/README.md"
git -C "$seed_repo" add README.md
git -C "$seed_repo" commit -q -m "Initial commit"

git clone -q --bare "$seed_repo" "$bare_repo"
git --git-dir="$bare_repo" worktree add -q -b feature/active "$active_worktree" main

if ! (
    cd "$active_worktree"
    bash "$script_path" main --all
) >"$output_file" 2>&1; then
    cat "$output_file"
    exit 1
fi

if grep -Fq "bad array subscript" "$output_file"; then
    echo "FAIL: bare repository entry caused an associative-array error"
    cat "$output_file"
    exit 1
fi

if grep -Fxq -- "--- feature/active ---" "$output_file"; then
    echo "FAIL: checked-out branch was also scanned as a local branch"
    cat "$output_file"
    exit 1
fi

echo "PASS: bare repository entries are skipped and linked worktrees are tracked"
