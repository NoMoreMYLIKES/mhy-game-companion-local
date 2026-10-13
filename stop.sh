#!/usr/bin/env bash
# Stops Game Companion Local on Linux.
#
# Stops this installation's backend: the one using the runtime folder in GCL_HOME (default: data
# next to this script), after checking that the process really is that backend. Programs that
# merely use the same port are never touched. A running batch is not interrupted unless --force
# is given.
#
# A backend run by the systemd service (./start.sh --service) stops as well and stays stopped
# until the service starts again (./start.sh --service, or the next boot). To remove the service:
#   systemctl --user disable --now game-companion-local
#
# Usage: ./stop.sh [--force]
#   --force  also stop a running batch: it is stopped first, its tool settings are restored,
#            then the backend exits
#
# Exit codes (as Stop.ps1):
#   0  stopped, or not running
#   7  a batch is running (use --force)
#   8  the backend could not be stopped
set -u
cd "$(dirname "$(readlink -f "$0")")" || exit 1
export PYTHONIOENCODING=utf-8
if [ ! -x .venv/bin/python ]; then
  echo 'Game Companion Local is not set up in this folder (.venv is missing), so it is not running.'
  exit 0
fi
exec .venv/bin/python -m server.launcher stop "$@"
