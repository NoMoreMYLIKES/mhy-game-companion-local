"""Start, stop and inspect the backend with exactly the configuration the backend uses.

Run with the virtual environment's Python (Start.ps1 / Stop.ps1, or start.sh / stop.sh on Linux, do this):

    python -m server.launcher start [--no-browser] [--timeout SECONDS]
    python -m server.launcher stop [--force]
    python -m server.launcher status [--json]
    python -m server.launcher set-port PORT
    python -m server.launcher check-deps

The runtime folder comes from GCL_HOME (default: data/ next to the app), the address from its
settings.json. A running backend counts as this installation's only when its health answer
carries this runtime folder's id, and it is stopped only after its process identity is checked.
Nothing else that uses the port is ever stopped.

Exit codes:
    0  ready, already running, stopped, or not running
    1  status: not running
    3  settings.json cannot be used
    4  the address is used by another program or installation
    5  the backend exited during startup
    6  the backend did not become ready in time (it was stopped)
    7  a batch is running; stop refused without --force
    8  the instance could not be stopped
    9  Python packages are missing
"""
from __future__ import annotations

import argparse
import http.client
import importlib.util
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

from . import core, procinfo

APP_ID = 'game-companion-local'
REQUIRED_MODULES = {'genshin': 'genshin', 'qrcode': 'qrcode', 'yaml': 'PyYAML'}
# Requests to our own backend must never go through a system or environment proxy.
_LOCAL = urllib.request.build_opener(urllib.request.ProxyHandler({}))
# What users type on this platform; messages name these.
START, STOP, PORT_OPTION, FORCE_OPTION = (('Start.bat', 'Stop.ps1', '-Port', '-Force') if procinfo.WINDOWS
                                          else ('./start.sh', './stop.sh', '--port', '--force'))


def say(text: str = '') -> None:
    print(text, flush=True)


# ---------------------------------------------------------------- facts about this installation

def runtime(strict: bool = True) -> dict:
    """Paths and address of this runtime folder. strict: a broken settings.json raises SettingsError."""
    if strict:
        core.check_settings_file()
    try:
        _, port = core.listen_address()
    except (KeyError, TypeError, ValueError):  # only reachable when not strict
        port = None
    data = core.DATA
    return {'data': data, 'port': port, 'url': url(port), 'log': data / 'logs' / 'app.log',
            'startup_log': data / 'logs' / 'startup.log', 'pid_file': data / 'server.pid',
            'error_file': data / 'startup-error.json', 'instance': core.instance_id()}


def url(port: int | None) -> str:
    return f'http://127.0.0.1:{port}/'


def health(port: int, timeout: float = 1.0):
    """The health answer at 127.0.0.1:port: a dict, 'silent' (something listens but gives no usable
    answer) or None (nothing listens)."""
    try:
        with _LOCAL.open(f'http://127.0.0.1:{port}/api/health', timeout=timeout) as resp:
            data = json.loads(resp.read(65536) or b'{}')
    except urllib.error.HTTPError:
        return 'silent'
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ConnectionRefusedError):
            return None
        return 'silent' if listening(port) else None
    except (OSError, ValueError, http.client.HTTPException):
        return 'silent' if listening(port) else None
    return data if isinstance(data, dict) else 'silent'


def listening(port: int) -> bool:
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=0.5):
            return True
    except OSError:
        return False


def ours(answer, rt: dict) -> bool:
    return isinstance(answer, dict) and answer.get('app') == APP_ID and answer.get('instance') == rt['instance']


def read_meta(rt: dict) -> dict | None:
    meta = core.read_json(rt['pid_file'], None)
    return meta if isinstance(meta, dict) and isinstance(meta.get('pid'), int) else None


def find_ours(rt: dict) -> tuple[dict | None, int | None]:
    """This installation's backend: on the configured port, or on the port it was started with
    (the setting may have changed since)."""
    ports = [rt['port']]
    meta = read_meta(rt)
    if meta and isinstance(meta.get('port'), int) and meta['port'] not in ports:
        ports.append(meta['port'])
    for port in ports:
        if port:
            answer = health(port)
            if ours(answer, rt):
                return answer, port
    return None, None


def older_version(meta: dict | None) -> bool:
    """The PID file was written by a version without instance ids, and its process still serves the recorded port."""
    port = (meta or {}).get('port')
    return bool(meta and 'instance' not in meta and isinstance(port, int) and procinfo.alive(meta['pid'])
                and procinfo.port_owner(port) == meta['pid'] and isinstance(health(port), dict))


def explain_busy_port(rt: dict, answer) -> list[str]:
    port = rt['port']
    owner = procinfo.describe(procinfo.port_owner(port))
    lines = [f'Cannot start Game Companion Local: 127.0.0.1:{port} is already in use.']
    if isinstance(answer, dict) and answer.get('app') == APP_ID:
        lines.append(f'It is used by another Game Companion Local installation (a different runtime folder): {owner}.')
    elif isinstance(answer, dict):
        lines.append(f'It is used by another web service: {owner}.')
    else:
        lines.append(f'It is used by {owner}.')
    return lines + port_advice(rt)


def port_advice(rt: dict) -> list[str]:
    return [f"To use another port, run: {START} {PORT_OPTION} {suggest_port(rt['port'])}",
            f"(it is saved in settings.json in the runtime folder: {rt['data']})"]


def suggest_port(busy: int) -> int:
    for port in range(busy + 10, busy + 200, 10):
        if port <= 65535 and not listening(port):
            return port
    return 18810


# ---------------------------------------------------------------- start

def spawn(rt: dict, token: str) -> subprocess.Popen:
    # PYTHONIOENCODING only affects the startup output; PYTHONUTF8 would also change how
    # the backend decodes Windows tool output, so it is not set.
    env = dict(os.environ, GCL_HOME=str(rt['data']), GCL_LAUNCH_TOKEN=token, PYTHONIOENCODING='utf-8')
    rt['startup_log'].parent.mkdir(parents=True, exist_ok=True)
    exe = Path(sys.executable)
    kwargs: dict = {}
    if procinfo.WINDOWS:
        windowless = exe.with_name('pythonw.exe')
        exe = windowless if windowless.is_file() else exe
        # no console, own process group, outlives this launcher; break away from its job when allowed
        kwargs['creationflags'] = 0x00000008 | 0x00000200 | 0x08000000 | 0x01000000
    else:
        kwargs['start_new_session'] = True
    cmd = [str(exe), '-m', 'server']
    with open(rt['startup_log'], 'w', encoding='utf-8') as out:
        common = dict(cwd=str(core.APP), env=env, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        try:
            return subprocess.Popen(cmd, **common, **kwargs)
        except OSError:
            if not procinfo.WINDOWS:
                raise
            kwargs['creationflags'] &= ~0x01000000  # the surrounding job does not allow breakaway
            return subprocess.Popen(cmd, **common, **kwargs)


def _tail(path: Path, count: int) -> list[str]:
    try:
        lines = path.read_text(encoding='utf-8', errors='replace').splitlines()
    except OSError:
        return []
    return [line for line in lines if line.strip()][-count:]


def startup_failure(rt: dict, code: int) -> list[str]:
    error = core.read_json(rt['error_file'], {}) or {}
    kind = error.get('kind')
    lines = [f'The backend exited with code {code} while starting.']
    if kind == 'bind':
        lines = [f"The backend exited with code {code}: it cannot listen on {error.get('host')}:{error.get('port')}.",
                 f"System error: {error.get('message')}"]
        owner = procinfo.port_owner(rt['port'])
        if owner:
            lines.append(f'The port is held by {procinfo.describe(owner)}.')
        elif procinfo.WINDOWS:
            lines.append('No program listens on it; Windows may reserve it. Reserved ranges are listed by: '
                         'netsh interface ipv4 show excludedportrange protocol=tcp')
        lines += port_advice(rt)
    elif kind in ('settings', 'exception'):
        lines.append(f"Cause: {error.get('message')}")
    else:
        tail = _tail(rt['startup_log'], 12)
        lines += ['Last output:'] + [f'  {x}' for x in tail] if tail else ['It wrote no output.']
    return lines + [f"Log: {rt['log']}", f"Startup output: {rt['startup_log']}"]


def start(no_browser: bool, timeout: float) -> int:
    rt = runtime()
    answer = health(rt['port'])
    if not ours(answer, rt):
        meta = read_meta(rt)
        started_on = meta.get('port') if meta and meta.get('instance') == rt['instance'] else None
        if isinstance(started_on, int) and started_on != rt['port'] and ours(previous := health(started_on), rt):
            say(f"Game Companion Local runs on port {started_on}; the port setting is now {rt['port']}. "
                f'Restart it ({STOP}, then {START}) to use the new port.')
            rt = dict(rt, port=started_on, url=url(started_on))
            answer = previous
    if ours(answer, rt) and answer.get('ready'):
        return ready(rt, no_browser, f"Game Companion Local is already running at {rt['url']} (PID {answer.get('pid')}).")
    if ours(answer, rt):
        say(f"Game Companion Local is already starting (PID {answer.get('pid')}); waiting for it.")
        return wait_ready(rt, None, answer.get('launch'), timeout, no_browser)
    meta = read_meta(rt)
    recorded = bool(meta and meta.get('instance') == rt['instance']
                    and procinfo.same_process(meta['pid'], meta.get('created'), meta.get('image')))
    if recorded and (answer is None or procinfo.port_owner(rt['port']) in (None, meta['pid'])):
        say(f"This installation's backend is running (PID {meta['pid']}) but does not answer on port {meta.get('port')}.")
        say(f'Stop it with {STOP}, then start again.')
        return 4
    if answer is not None and older_version(meta) and meta['port'] == rt['port']:
        say(f"An older version of Game Companion Local is running from this runtime folder (PID {meta['pid']}).")
        say(f'Stop it with {STOP}' + (' (from an administrator PowerShell if it runs as administrator)' if procinfo.WINDOWS else '')
            + ', then start again.')
        return 4
    if answer is not None:
        for line in explain_busy_port(rt, answer):
            say(line)
        return 4
    token = secrets.token_hex(8)
    say(f"Starting the backend on 127.0.0.1:{rt['port']} (runtime folder: {rt['data']})...")
    rt['error_file'].unlink(missing_ok=True)
    try:
        child = spawn(rt, token)
    except OSError as exc:
        say(f'Cannot launch the backend: {exc}')
        return 5
    return wait_ready(rt, child, token, timeout, no_browser)


def ready(rt: dict, no_browser: bool, message: str) -> int:
    say(message)
    say(f"Ready: {rt['url']}")  # Start.ps1 and other callers read this line
    if not no_browser:
        webbrowser.open(rt['url'])
    return 0


def wait_ready(rt: dict, child: subprocess.Popen | None, token: str | None, timeout: float, no_browser: bool) -> int:
    begin = time.monotonic()
    deadline = begin + timeout
    report = begin + 15
    while True:
        if child is not None and (code := child.poll()) is not None:
            for line in startup_failure(rt, code):
                say(line)
            return 5
        remaining = deadline - time.monotonic()
        answer = health(rt['port'], timeout=max(0.2, min(1.0, remaining)))
        if ours(answer, rt) and answer.get('launch') == token and answer.get('ready'):
            return ready(rt, no_browser, f"Game Companion Local is ready at {rt['url']} (PID {answer.get('pid')}).")
        if remaining <= 0:
            break
        if time.monotonic() >= report:
            say(f'Still starting ({time.monotonic() - begin:.0f} s)...')
            report += 15
        time.sleep(0.25)
    say(f'The backend did not become ready within {timeout:g} seconds.')
    if child is not None:
        meta = read_meta(rt)
        if meta and meta.get('launch') == token:
            procinfo.terminate(meta['pid'])
            if not procinfo.alive(meta['pid']):
                rt['pid_file'].unlink(missing_ok=True)
        if child.poll() is None:
            procinfo.terminate(child.pid)  # with its children: on Windows the venv's pythonw starts the interpreter
        try:
            child.wait(10)
        except subprocess.TimeoutExpired:
            pass
        say(f'The backend this launcher started (PID {child.pid}) was stopped.')
    tail = _tail(rt['startup_log'], 8)
    if tail:
        say('Last output:')
        for line in tail:
            say(f'  {line}')
    say(f"Log: {rt['log']}")
    return 6


# ---------------------------------------------------------------- stop

def stop(force: bool) -> int:
    rt = runtime(strict=False)  # a broken settings.json must not prevent stopping
    meta = read_meta(rt)
    if meta and meta.get('instance') not in (None, rt['instance']):
        meta = None
    target = answer = port = None
    if meta:
        verified = procinfo.same_process(meta['pid'], meta.get('created'), meta.get('image'))
        if verified is False:
            rt['pid_file'].unlink(missing_ok=True)
            say(f"Game Companion Local is not running (its PID file was out of date and has been removed; "
                f"process {meta['pid']} was not touched).")
            return 0
        port = meta.get('port')
        answer = health(port) if isinstance(port, int) else None
        confirmed = isinstance(answer, dict) and answer.get('pid') == meta['pid'] and answer.get('instance') == meta.get('instance')
        if not (verified or confirmed or older_version(meta)):
            say(f"Process {meta['pid']} from the PID file cannot be identified as Game Companion Local; it was not stopped.")
            say(f"PID file: {rt['pid_file']}")
            return 8
        target = {'pid': meta['pid'], 'created': meta.get('created'), 'token': meta.get('token')}
        if not confirmed:
            answer = None
    else:
        answer, port = find_ours(rt)
        if answer:  # running, but its PID file is gone: identify it by its creation time
            target = {'pid': answer.get('pid'), 'created': answer.get('created'), 'token': None}
            if not isinstance(target['pid'], int) or procinfo.same_process(target['pid'], target['created'], None) is not True:
                say(f'An instance answers on port {port}, but its process cannot be verified; it was not stopped.')
                return 8
    if target is None:
        say('Game Companion Local is not running.')
        return 0
    pid = target['pid']
    if isinstance(answer, dict) and answer.get('busy') and not force:
        return _busy()
    if target['token'] and isinstance(answer, dict):
        say(f'Stopping Game Companion Local (PID {pid})...')
        if force and answer.get('busy'):
            say('Stopping the running batch first; its tool settings are restored before the backend exits (up to 5 minutes).')
        refused = _request_shutdown(port, target['token'], force)
        if refused == 'busy':
            return _busy()
        if refused:
            say(f'The backend did not accept the stop request ({refused}); ending its process instead.')
        elif _wait_gone(pid, 330 if force else 20):
            return _stopped(rt, pid)
        else:
            say('It did not exit in time; ending its process instead.')
    if procinfo.same_process(pid, target['created'], None) is False:
        return _stopped(rt, pid)
    say(f'Ending process {pid}...')
    error = procinfo.terminate(pid)
    if error or not _wait_gone(pid, 10):
        say(f'Could not stop process {pid}: {error or "it is still running"}.')
        if procinfo.WINDOWS:
            say('If the backend runs as administrator, run Stop.ps1 from an administrator PowerShell.')
        return 8
    return _stopped(rt, pid)


def _request_shutdown(port: int, token: str, force: bool) -> str | None:
    """None when accepted; 'busy' when a batch started meanwhile; otherwise the reason it failed."""
    body = json.dumps({'token': token, 'force': force}).encode()
    request = urllib.request.Request(f'http://127.0.0.1:{port}/api/shutdown', data=body, method='POST',
                                     headers={'X-GC': '1', 'Content-Type': 'application/json'})
    try:
        _LOCAL.open(request, timeout=5).close()
        return None
    except urllib.error.HTTPError as exc:
        again = health(port)
        if not force and isinstance(again, dict) and again.get('busy'):
            return 'busy'
        return f'HTTP {exc.code}'
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        return str(getattr(exc, 'reason', exc))


def _busy() -> int:
    say(f'A batch is running. Stop it on the dashboard first, or run: {STOP} {FORCE_OPTION}')
    say(f'({FORCE_OPTION} stops the batch, waits for its tool settings to be restored, then stops the backend.)')
    return 7


def _wait_gone(pid: int, seconds: float) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not procinfo.alive(pid):
            return True
        time.sleep(0.2)
    return not procinfo.alive(pid)


def _stopped(rt: dict, pid: int) -> int:
    meta = read_meta(rt)
    if meta and meta.get('pid') == pid:
        rt['pid_file'].unlink(missing_ok=True)
    say(f'Game Companion Local stopped (PID {pid}).')
    return 0


# ---------------------------------------------------------------- status and setup helpers

def status(as_json: bool) -> int:
    rt = runtime()
    answer, port = find_ours(rt)
    port = port or rt['port']
    info = {'running': bool(answer and answer.get('ready')), 'starting': bool(answer) and not answer.get('ready'),
            'url': url(port), 'port': port, 'configured_port': rt['port'], 'pid': (answer or {}).get('pid'),
            'data': str(rt['data'])}
    if as_json:
        say(json.dumps(info, ensure_ascii=False))
    elif answer:
        say(f"{'Running' if info['running'] else 'Starting'} at {info['url']} (PID {info['pid']}), runtime folder {rt['data']}")
    else:
        say(f"Not running (address 127.0.0.1:{rt['port']}, runtime folder {rt['data']}).")
    return 0 if info['running'] else 1


def set_port(port: int) -> int:
    rt = runtime()
    if not 1 <= port <= 65535:
        say(f'Cannot set the port: {port} is not between 1 and 65535.')
        return 3
    core.save_settings({'server': {'port': port}})
    say(f"Port set to {port} for this installation (runtime folder {rt['data']}).")
    return 0


def check_deps() -> int:
    missing = [package for module, package in REQUIRED_MODULES.items() if importlib.util.find_spec(module) is None]
    if missing:
        say('Missing Python packages: ' + ', '.join(missing))
        return 9
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='python -m server.launcher', description=__doc__.split('\n\n')[0])
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('start')
    p.add_argument('--no-browser', action='store_true')
    p.add_argument('--timeout', type=float, default=60)
    sub.add_parser('stop').add_argument('--force', action='store_true')
    sub.add_parser('status').add_argument('--json', action='store_true')
    sub.add_parser('set-port').add_argument('port', type=int)
    sub.add_parser('check-deps')
    args = parser.parse_args(argv)
    try:
        if args.command == 'start':
            return start(args.no_browser, args.timeout)
        if args.command == 'stop':
            return stop(args.force)
        if args.command == 'status':
            return status(args.json)
        if args.command == 'set-port':
            return set_port(args.port)
        return check_deps()
    except core.SettingsError as exc:
        say(f'Cannot use the settings: {exc}')
        say('Fix the file, or move it away to use the defaults, then try again.')
        return 3


if __name__ == '__main__':
    sys.exit(main())
