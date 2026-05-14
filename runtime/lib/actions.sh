#!/usr/bin/env bash
set -Eeuo pipefail

: "${CDEV_RUNTIME_ROOT:=/workspace/.cdev}"

cdev_run_actions() {
  local plan="$1"
  python3 "$RUNTIME_LIB_DIR/run_actions.py" "$plan"
}
