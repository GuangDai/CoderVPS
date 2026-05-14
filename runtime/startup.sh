#!/usr/bin/env bash
set -Eeuo pipefail

# CoderVPS workspace startup entrypoint.
#
# This script is sourced by the Coder agent.  It:
#   1. Initialises /workspace/.cdev (configurable via CDEV_RUNTIME_ROOT).
#   2. Acquires an exclusive startup lock (flock).
#   3. Validates immutable selection hashes.
#   4. Delegates to the Python action runner for plan execution.

# ---- Configurable root ----
: "${CDEV_RUNTIME_ROOT:=/workspace/.cdev}"

_CDEV="$CDEV_RUNTIME_ROOT"

mkdir -p \
  "$_CDEV/downloads" \
  "$_CDEV/toolchains" \
  "$_CDEV/cache" \
  "$_CDEV/logs" \
  "$_CDEV/tmp" \
  "$_CDEV/locks" \
  "$_CDEV/state" \
  "$_CDEV/bin"

# ---- Exclusive startup lock ----
exec 9>"$_CDEV/locks/startup.lock"
if ! flock -n 9; then
  echo "CoderVPS: another startup is already running" >&2
  exit 1
fi

# Clean up temp selection files on exit
trap 'rm -f "$_CDEV/selection.new.json" "$_CDEV/selection.new.sha256"' EXIT

# ---- Immutable selection check ----
if [[ -n "${CDEV_SELECTION_JSON:-}" ]]; then
  printf '%s\n' "$CDEV_SELECTION_JSON" > "$_CDEV/selection.new.json"
  sha256sum "$_CDEV/selection.new.json" | awk '{print $1}' > "$_CDEV/selection.new.sha256"
  if [[ -f "$_CDEV/selection.sha256" ]]; then
    if ! cmp -s "$_CDEV/selection.new.sha256" "$_CDEV/selection.sha256"; then
      echo "CoderVPS: immutable workspace selection changed; refusing startup" >&2
      exit 1
    fi
  fi
  mv "$_CDEV/selection.new.json" "$_CDEV/selection.json"
  mv "$_CDEV/selection.new.sha256" "$_CDEV/selection.sha256"
fi

# ---- Source the action library (provides cdev_run_actions) ----
# The runtime lib files are mounted read-only at /opt/cde/runtime.
if [[ -f /opt/cde/runtime/lib/actions.sh ]]; then
  # shellcheck source=/dev/null
  source /opt/cde/runtime/lib/actions.sh
fi

# ---- Execute the runtime plan ----
if [[ -f "$_CDEV/runtime-plan.json" ]]; then
  cdev_run_actions "$_CDEV/runtime-plan.json"
fi

# ---- Write env activation snippet ----
cat > "$_CDEV/env.sh" <<'ENVEOF'
#!/usr/bin/env bash
# Source this file to activate workspace toolchains.
export PATH="/workspace/.cdev/bin:$PATH"
ENVEOF
chmod +x "$_CDEV/env.sh"
