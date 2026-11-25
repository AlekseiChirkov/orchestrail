#!/bin/bash
# Validate and deploy declared harnesses; --stage exports into an isolated directory.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${ORCHESTRAIL_HOME:-$SCRIPT_DIR/..}"
STAGE_ROOT=""
FORCE=()
while [ $# -gt 0 ]; do
  case "$1" in
    --from)
      ROOT="${2:-}"
      [ -n "$ROOT" ] || { echo "ERROR: --from needs a directory"; exit 1; }
      shift 2 ;;
    --from=*)
      ROOT="${1#--from=}"; shift ;;
    --stage|--stage=*)
      [ -z "$STAGE_ROOT" ] || { echo "ERROR: duplicate --stage" >&2; exit 1; }
      if [ "$1" = --stage ]; then
        STAGE_ROOT="${2:-}"
        [ -n "$STAGE_ROOT" ] || { echo "ERROR: --stage needs a directory" >&2; exit 1; }
        shift 2
      else
        STAGE_ROOT="${1#--stage=}"
        [ -n "$STAGE_ROOT" ] || { echo "ERROR: --stage needs a directory" >&2; exit 1; }
        shift
      fi ;;
    --force)
      FORCE=(--force); shift ;;
    -h|--help)
      echo "Usage: scripts/sync.sh [--from <source-tree>] [--force] [--stage <output-directory>]"
      echo "  --from <dir>  deploy from <dir> instead of the repository root (or ORCHESTRAIL_HOME)"
      exit 0 ;;
    *) echo "ERROR: unknown argument: $1" >&2; exit 1 ;;
  esac
done

SELECTED_ROOT="$ROOT"
ROOT="$(cd -- "$SELECTED_ROOT" 2>/dev/null && pwd -P)" || {
  echo "ERROR: source directory not found: $SELECTED_ROOT" >&2
  exit 1
}

for d in workflows rules principles templates scripts harness; do
  [ -d "$ROOT/$d" ] || { echo "ERROR: $ROOT is not an Orchestrail checkout (missing $d/)"; exit 1; }
done

require_python() {
  if ! python3 -I -c 'import sys; sys.exit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
    echo "ERROR: Python 3.11 or newer is required for deployment" >&2
    exit 1
  fi
}

ENGINE="$ROOT/scripts/deploy-skills.py"
require_python
if [ -n "$STAGE_ROOT" ]; then
  STAGE_ROOT="$(python3 -I "$ENGINE" stage-target --from "$ROOT" --stage "$STAGE_ROOT")" || exit 1
fi

echo "=== Contract validation ==="
bash "$ROOT/scripts/validate-contracts.sh" || {
  echo "ERROR: Contract validation failed. Fix errors before syncing."
  exit 1
}
for acceptance in check-phase-finalize.py check-finalization-safety.py check-finalization-workflow.py; do
  [ -f "$ROOT/scripts/$acceptance" ] || { echo "ERROR: required acceptance check missing: $acceptance" >&2; exit 1; }
  python3 "$ROOT/scripts/$acceptance" || { echo "ERROR: acceptance check failed: $acceptance" >&2; exit 1; }
done

HOOK_INSTALL_RESULT='{"reason":"installer-unavailable","status":"unavailable"}'
if [ -n "$STAGE_ROOT" ]; then
  # Recheck the destination after preflight, before deployment can create anything.
  python3 -I "$ENGINE" stage-target --from "$ROOT" --stage "$STAGE_ROOT" >/dev/null || exit 1
  stage_state="$(mktemp -d /tmp/orchestrail-stage.XXXXXX)" || exit 1
  trap 'rm -rf -- "$stage_state"' EXIT
  export HOME="$STAGE_ROOT" XDG_CONFIG_HOME="$stage_state/config" XDG_STATE_HOME="$stage_state/state"
else
  if [ -f "$ROOT/scripts/install-hooks.sh" ]; then
    HOOK_INSTALL_RESULT="$(bash "$ROOT/scripts/install-hooks.sh" install --from "$ROOT")" || \
      HOOK_INSTALL_RESULT='{"reason":"installer-failed","status":"unavailable"}'
  fi
  REPORTER="$ROOT/scripts/report-legacy-artifacts.sh"
  bash "$REPORTER" global || exit 1
  python3 -I "$ENGINE" list-projects | while IFS= read -r -d '' project; do
    bash "$REPORTER" project "$project" || exit 1
  done || exit 1
fi

status=0
python3 -I "$ENGINE" deploy --from "$ROOT" --hook-result "$HOOK_INSTALL_RESULT" "${FORCE[@]}" || status=$?
case "$status" in
  0) ;;
  3) exit 3 ;;
  *) exit 1 ;;
esac

if [ -n "$STAGE_ROOT" ]; then
  echo "=== Staged harness outputs in $STAGE_ROOT ==="
else
  echo "=== Sync complete ==="
fi
python3 -I "$ENGINE" targets --from "$ROOT" || exit 1
