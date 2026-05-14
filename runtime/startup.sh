#!/usr/bin/env bash
set -Eeuo pipefail

# CDEV_RUNTIME_ROOT is configurable for tests, defaults to /workspace/.cdev
export CDEV_RUNTIME_ROOT="${CDEV_RUNTIME_ROOT:-/workspace/.cdev}"

mkdir -p \
  "$CDEV_RUNTIME_ROOT/downloads" \
  "$CDEV_RUNTIME_ROOT/toolchains" \
  "$CDEV_RUNTIME_ROOT/cache" \
  "$CDEV_RUNTIME_ROOT/logs" \
  "$CDEV_RUNTIME_ROOT/tmp" \
  "$CDEV_RUNTIME_ROOT/locks" \
  "$CDEV_RUNTIME_ROOT/state" \
  "$CDEV_RUNTIME_ROOT/bin"

exec 9>"$CDEV_RUNTIME_ROOT/locks/startup.lock"
flock -n 9 || {
  echo "another CoderVPS startup is already running" >&2
  exit 1
}

# Cleanup temp files on exit
trap 'rm -f "$CDEV_RUNTIME_ROOT/selection.new.json" "$CDEV_RUNTIME_ROOT/selection.new.sha256"' EXIT

# Verify immutable workspace selections if provided
if [[ -n "${CDEV_SELECTION_JSON:-}" ]]; then
  printf '%s\n' "$CDEV_SELECTION_JSON" > "$CDEV_RUNTIME_ROOT/selection.new.json"
  sha256sum "$CDEV_RUNTIME_ROOT/selection.new.json" | awk '{print $1}' > "$CDEV_RUNTIME_ROOT/selection.new.sha256"
  if [[ -f "$CDEV_RUNTIME_ROOT/selection.sha256" ]]; then
    if ! cmp -s "$CDEV_RUNTIME_ROOT/selection.new.sha256" "$CDEV_RUNTIME_ROOT/selection.sha256"; then
      echo "immutable workspace selection changed; refusing startup" >&2
      exit 1
    fi
  fi
  mv "$CDEV_RUNTIME_ROOT/selection.new.json" "$CDEV_RUNTIME_ROOT/selection.json"
  mv "$CDEV_RUNTIME_ROOT/selection.new.sha256" "$CDEV_RUNTIME_ROOT/selection.sha256"
fi

# Load the actions library
RUNTIME_LIB_DIR="${RUNTIME_LIB_DIR:-/opt/cde/runtime/lib}"
# shellcheck source=/dev/null
source "$RUNTIME_LIB_DIR/actions.sh"

# Execute runtime plan if it exists
if [[ -f "$CDEV_RUNTIME_ROOT/runtime-plan.json" ]]; then
  cdev_run_actions "$CDEV_RUNTIME_ROOT/runtime-plan.json"
fi

# Write env.sh for future sourcing
cat > "$CDEV_RUNTIME_ROOT/env.sh" <<'ENVEOF'
export PATH="$CDEV_RUNTIME_ROOT/bin:$PATH"
ENVEOF
