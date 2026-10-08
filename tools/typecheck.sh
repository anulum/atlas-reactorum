#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# Atlas Reactorum — tools/typecheck.sh
#
# Runs strict mypy across the repository and exits non-zero if anything fails.
#
# The import directories are self-contained, per-round deliverables: several
# legitimately share a script basename (validate.py, build_dataset.py,
# generate_gap_report.py). Checking the tree in one pass makes mypy treat those
# as duplicate modules and abort before checking anything. Adding __init__.py
# would misrepresent standalone scripts as packages, and --exclude would leave
# them unchecked. Checking each directory separately keeps every file covered
# with no such distortion.
#
# Pass --summary to print only the totals.

set -uo pipefail
root_dir="$(cd "$(dirname "$0")/.." && pwd)"
summary_only=0
[ "${1:-}" = "--summary" ] && summary_only=1

# ATLAS_MYPY selects the executable for an explicitly chosen environment.
# Prefer the project virtualenv otherwise: it carries the test dependencies, so mypy
# can resolve pytest and jsonschema instead of reporting them as missing.
if [ -n "${ATLAS_MYPY:-}" ]; then
    mypy_bin="$ATLAS_MYPY"
    if [ ! -x "$mypy_bin" ]; then
        echo "typecheck: ATLAS_MYPY is not executable: $mypy_bin" >&2
        exit 1
    fi
elif [ -x "$root_dir/.venv/bin/mypy" ]; then
    mypy_bin="$root_dir/.venv/bin/mypy"
elif command -v mypy >/dev/null 2>&1; then
    mypy_bin="mypy"
else
    echo "typecheck: mypy not found" >&2
    exit 1
fi

for tool in git sort; do
    command -v "$tool" >/dev/null || exit 1
done
log="$(mktemp)"
sources="$(mktemp)"
trap 'rm -f "$log" "$sources"' EXIT
git -C "$root_dir" ls-files --cached --others --exclude-standard --deduplicate -z -- '*.py' '*.pyi' >"$sources" || exit 1
[[ -s "$sources" ]] || {
    echo 'typecheck: no Python source' >&2
    exit 1
}
declare -A directories=()
while IFS= read -r -d '' relative; do
    file="$root_dir/$relative"
    if [[ ! -f "$file" || ! -r "$file" || -L "$file" ]]; then
        echo "typecheck: native source unavailable or symlink: $relative" >&2
        exit 1
    fi
    directories["${file%/*}"]=1
done <"$sources"

dirs_checked=0
dirs_failed=0

while IFS= read -r dir; do
    dirs_checked=$((dirs_checked + 1))
    # mypy's exit status is the authority: 0 clean, non-zero means findings.
    directory_failed=0
    for suffix in py pyi; do
        files=()
        while IFS= read -r -d '' relative; do
            file="$root_dir/$relative"
            [[ "${file%/*}" == "$dir" && "${file##*.}" == "$suffix" ]] && files+=("$file")
        done <"$sources"
        if [[ ${#files[@]} -gt 0 ]]; then
            if ! "$mypy_bin" --strict --config-file "$root_dir/pyproject.toml" "${files[@]}" >>"$log" 2>&1; then
                directory_failed=1
            fi
        fi
    done
    dirs_failed=$((dirs_failed + directory_failed))
done < <(printf '%s\n' "${!directories[@]}" | LC_ALL=C sort)

error_count=$(grep -c ' error: ' "$log" || true)

if [ "$summary_only" -eq 0 ] && [ "$error_count" -gt 0 ]; then
    grep ' error: ' "$log" || true
fi

echo "typecheck: ${dirs_checked} directories, ${dirs_failed} with findings, ${error_count} errors"
[ "$dirs_failed" -eq 0 ]
