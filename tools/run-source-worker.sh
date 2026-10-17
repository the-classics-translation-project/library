#!/bin/sh
# Stable launchd entry point. Installation is a separate explicit owner action.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin${PATH:+:$PATH}"
export PATH

if ! command -v python3 >/dev/null 2>&1; then
  echo 'source worker: python3 is unavailable' >&2
  exit 2
fi

cd "$REPO_DIR"
if [ "$#" -eq 0 ]; then set -- run-once; fi
exec python3 "$SCRIPT_DIR/source_worker.py" "$@"
