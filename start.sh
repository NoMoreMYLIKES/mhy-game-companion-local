#!/usr/bin/env bash
# Starts Game Companion Local on Linux, in the background.
#
# On Linux the backend plans, reads Miyoushe data and serves the dashboard. Runs need Windows:
# BetterGI, ZZZ OneDragon and the games are Windows programs.
#
# Sets up .venv on first use, then starts the backend with server.launcher, which waits until it
# answers and explains any failure. Runtime folder: GCL_HOME (default: data next to this script);
# the port is the one in its settings.json.
#
# Usage: ./start.sh [--port N] [--timeout SECONDS] [--open] [--service]
#   --port N     save this port for this installation, then start
#   --timeout S  seconds to wait until the backend answers (default 60)
#   --open       open the dashboard in a browser when it is ready
#   --service    run it as a systemd user service instead: restarted after a crash, and started
#                with the machine once lingering is on (sudo loginctl enable-linger "$USER")
#
# Exit codes (as Start.ps1):
#    0  ready, or already running
#    3  settings.json cannot be used
#    4  the address is used by another program or installation
#    5  the backend exited while starting
#    6  the backend was not ready in time (it was stopped)
#   10  Python 3.10 or newer was not found
#   11  .venv cannot be created or does not run
#   12  the Python packages cannot be installed
#   15  the systemd service cannot be installed or started
set -u
cd "$(dirname "$(readlink -f "$0")")" || exit 1
export PYTHONIOENCODING=utf-8
venv=.venv
python=$venv/bin/python
service_name=game-companion-local
port='' timeout=60 open=0 service=0

while [ $# -gt 0 ]; do
  case "$1" in
    --port|--timeout)
      [ $# -ge 2 ] || { echo "$1 needs a value (see ./start.sh --help)."; exit 2; }
      if [ "$1" = --port ]; then port=$2; else timeout=$2; fi
      shift 2 ;;
    --open) open=1; shift ;;
    --service) service=1; shift ;;
    -h|--help) sed -n '2,/^set -u/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1 (see ./start.sh --help)."; exit 2 ;;
  esac
done

find_python() {
  local candidate
  for candidate in "${PYTHON:-}" python3 python; do
    [ -n "$candidate" ] && command -v "$candidate" >/dev/null 2>&1 || continue
    if "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
      command -v "$candidate"
      return 0
    fi
  done
  return 1
}

# ------------------------------------------------------------- 1. Python environment
if [ ! -x "$python" ]; then
  base=$(find_python) || {
    echo 'Python 3.10 or newer was not found. Install it (for example: sudo apt install python3 python3-venv),'
    echo 'then run ./start.sh again.'
    exit 10
  }
  echo "Creating the virtual environment in $venv with $base..."
  if ! "$base" -m venv "$venv" 2>/dev/null; then
    rm -rf "$venv"
    # Some distributions ship Python without venv/ensurepip; uv can still make the environment.
    if command -v uv >/dev/null 2>&1; then
      uv venv --quiet --python "$base" "$venv" || { echo "Could not create $venv."; exit 11; }
    else
      echo "Could not create $venv: this Python has no venv module. Install it (for example:"
      echo 'sudo apt install python3-venv) or uv, then run ./start.sh again.'
      exit 11
    fi
  fi
fi
if ! "$python" -c 'import sys' 2>/dev/null; then
  echo "The Python in $venv does not run; the Python it was made from may have been removed or upgraded."
  echo 'Delete the .venv folder and run ./start.sh again.'
  exit 11
fi

# ------------------------------------------------------------- 2. Packages: install when requirements.txt changed or one is missing
stamp=$venv/gcl-requirements.sha256
wanted=$("$python" -c 'import hashlib; print(hashlib.sha256(open("requirements.txt", "rb").read()).hexdigest())')
installed=$(cat "$stamp" 2>/dev/null || true)
if ! "$python" -m server.launcher check-deps >/dev/null 2>&1 || [ "$wanted" != "$installed" ]; then
  echo 'Installing the Python packages from requirements.txt...'
  if "$python" -m pip --version >/dev/null 2>&1; then
    "$python" -m pip install --disable-pip-version-check -r requirements.txt
  else  # an environment made by uv has no pip
    uv pip install --python "$python" -r requirements.txt
  fi || {
    echo 'Installing the packages failed. Check the network connection, then run ./start.sh again.'
    exit 12
  }
  "$python" -m server.launcher check-deps || exit 12
  printf '%s' "$wanted" > "$stamp"
fi

# ------------------------------------------------------------- 3. Port, when given
if [ -n "$port" ]; then
  "$python" -m server.launcher set-port "$port" || exit $?
fi

# ------------------------------------------------------------- 4a. Start through the systemd user service
unit_value() {  # a path inside a unit file: % starts a specifier there
  printf '%s' "$1" | sed 's/%/%%/g'
}

run_service() {
  command -v systemctl >/dev/null 2>&1 || { echo 'systemd was not found; run ./start.sh without --service.'; return 15; }
  local dir=${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user here waited=0
  here=$(pwd)
  mkdir -p "$dir" || return 15
  {
    echo '[Unit]'
    echo 'Description=Game Companion Local'
    echo 'After=network-online.target'
    echo
    echo '[Service]'
    echo "WorkingDirectory=$(unit_value "$here")"
    [ -n "${GCL_HOME:-}" ] && echo "Environment=\"GCL_HOME=$(unit_value "$(readlink -f "$GCL_HOME")")\""
    echo 'Environment=PYTHONIOENCODING=utf-8'
    echo "ExecStart=\"$(unit_value "$here/$python")\" -m server"
    echo 'Restart=on-failure'
    echo 'RestartSec=10'
    echo '# A busy port (2) or unusable settings (3) do not fix themselves.'
    echo 'RestartPreventExitStatus=2 3'
    echo
    echo '[Install]'
    echo 'WantedBy=default.target'
  } > "$dir/$service_name.service" || return 15
  systemctl --user daemon-reload || return 15
  # A backend started without the service would hold the port: stop it first (it refuses while a batch runs).
  if ! systemctl --user is-active --quiet "$service_name"; then
    "$python" -m server.launcher stop || return $?
  fi
  systemctl --user enable --quiet "$service_name" && systemctl --user restart "$service_name" || {
    echo "The service did not start. Details: journalctl --user -u $service_name"
    return 15
  }
  until "$python" -m server.launcher status >/dev/null 2>&1; do
    if ! systemctl --user is-active --quiet "$service_name"; then
      echo "The backend exited while starting. Details: journalctl --user -u $service_name"
      return 5
    fi
    if [ "$waited" -ge "$timeout" ]; then
      echo "The backend did not answer within $timeout seconds. Details: journalctl --user -u $service_name"
      return 6
    fi
    sleep 1
    waited=$((waited + 1))
  done
  "$python" -m server.launcher status
  echo "It runs as the systemd user service $service_name: systemctl --user status|restart|stop $service_name"
  if [ "$(loginctl show-user "$USER" --property=Linger --value 2>/dev/null)" != yes ]; then
    echo "To start it with the machine without logging in, run once: sudo loginctl enable-linger $USER"
  fi
}

if [ "$service" = 1 ]; then
  run_service
  exit $?
fi

# ------------------------------------------------------------- 4b. Start in the background
if [ "$open" = 1 ]; then
  exec "$python" -m server.launcher start --timeout "$timeout"
fi
exec "$python" -m server.launcher start --no-browser --timeout "$timeout"
