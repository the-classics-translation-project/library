#!/bin/sh
# Run manually on the owner's Mac; cloning, building and tests never call this.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
LABEL=org.classics-translation-project.source-worker
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_DIR="$HOME/Library/Logs/CTP/source-worker"
DOMAIN="gui/$(id -u)"
ACTION=${1:-help}

render_plist() {
  REPO_DIR="$REPO_DIR" LOG_DIR="$LOG_DIR" LABEL="$LABEL" python3 - <<'PY'
import os
import plistlib
from pathlib import Path
root=Path(os.environ['REPO_DIR'])
logs=Path(os.environ['LOG_DIR'])
job={
    'Label': os.environ['LABEL'],
    'ProgramArguments': [str(root/'tools/run-source-worker.sh'), 'run-once'],
    'WorkingDirectory': str(root),
    'EnvironmentVariables': {'PATH': '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin'},
    'RunAtLoad': True,
    'StartInterval': 1800,
    'StandardOutPath': str(logs/'stdout.log'),
    'StandardErrorPath': str(logs/'stderr.log'),
}
os.write(1, plistlib.dumps(job))
PY
}

case "$ACTION" in
  print-plist)
    render_plist
    ;;
  install)
    [ "$(uname -s)" = Darwin ] || { echo 'This installer requires macOS' >&2; exit 2; }
    [ ! -e "$PLIST" ] || { echo "Already installed: $PLIST" >&2; exit 2; }
    command -v launchctl >/dev/null 2>&1 || { echo 'launchctl is unavailable' >&2; exit 2; }
    mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"
    render_plist > "$PLIST"
    chmod 600 "$PLIST"
    if ! launchctl bootstrap "$DOMAIN" "$PLIST"; then
      rm -f "$PLIST"
      echo 'LaunchAgent bootstrap failed; the plist was removed' >&2
      exit 1
    fi
    echo "Installed $PLIST. Check $LOG_DIR and run the status command."
    ;;
  uninstall)
    if [ -e "$PLIST" ]; then
      launchctl bootout "$DOMAIN" "$PLIST" || true
      rm -f "$PLIST"
    fi
    echo 'Source-preparation LaunchAgent is disabled and removed.'
    ;;
  run-once)
    exec "$SCRIPT_DIR/run-source-worker.sh" run-once
    ;;
  dry-run)
    exec "$SCRIPT_DIR/run-source-worker.sh" run-once --dry-run
    ;;
  status)
    exec "$SCRIPT_DIR/run-source-worker.sh" status --json
    ;;
  logs)
    mkdir -p "$LOG_DIR"
    tail -n 80 "$LOG_DIR/stdout.log" "$LOG_DIR/stderr.log" 2>/dev/null || true
    ;;
  *)
    echo 'Usage: install-source-launch-agent.sh {print-plist|install|uninstall|run-once|dry-run|status|logs}' >&2
    exit 2
    ;;
esac
