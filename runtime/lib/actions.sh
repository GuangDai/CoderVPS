#!/usr/bin/env bash
set -Eeuo pipefail

# CoderVPS action executor shell wrapper.
#
# This is a thin shim that delegates to the Python action runner.
# It uses CDEV_RUNTIME_ROOT to locate the plan file and state root.

: "${CDEV_RUNTIME_ROOT:=/workspace/.cdev}"

cdev_run_actions() {
  local plan="$1"
  if [[ ! -f "$plan" ]]; then
    echo "CoderVPS: runtime plan not found: $plan" >&2
    exit 1
  fi
  python3 /opt/cde/runtime/lib/run_actions.py "$plan"
}
