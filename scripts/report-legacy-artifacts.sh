#!/bin/bash
# Report existing legacy deployment objects without modifying them.
# Usage: report-legacy-artifacts.sh global | report-legacy-artifacts.sh project <dir>
# Exit 0 after reporting and 2 for invalid usage.

set -uo pipefail

usage() {
    printf 'Usage: report-legacy-artifacts.sh global | report-legacy-artifacts.sh project <dir>\n' >&2
    exit 2
}

report() {
    local path="$1"
    # Use a single observation of the object, including dangling links.
    if stat -c '%f' -- "$path" >/dev/null 2>&1; then
        printf 'legacy: %q — created by an earlier Orchestrail version; review it, then remove it manually if unused: rm -r -- %q\n' \
            "$path" "$path"
    fi
}

case "${1:-}" in
    global)
        [[ $# -eq 1 && -n "${HOME:-}" ]] || usage
        legacy_root="${HOME%/}/.codeium/windsurf"
        report "$legacy_root/global_workflows"
        report "$legacy_root/global_rules"
        ;;
    project)
        [[ $# -eq 2 && -n "${2:-}" ]] || usage
        project_root="${2%/}"
        report "$project_root/.windsurf"
        report "$project_root/.devin"
        ;;
    *)
        usage
        ;;
esac
