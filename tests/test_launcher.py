"""Launcher tests: start, stop and status against real backend processes.

Every test uses its own runtime folder (GCL_HOME, with a space and non-ASCII characters in its
path) and a free port, so an installation in use is never touched. Nothing here contacts the
official API: a fresh runtime folder has no accounts, and the schedule is off.

Test doubles are loaded through PYTHONPATH only: a fake ``genshin`` package that fails or hangs
on import, and a ``sitecustomize`` that changes ``server.runner`` after it is imported.
"""
from __future__ import annotations

import http.server
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server import procinfo  # noqa: E402  (standard library only; reads no runtime folder)

# What the launcher tells users to type on this platform.
START, STOP = ('Start.bat -Port', 'Stop.ps1 -Force') if procinfo.WINDOWS else ('./start.sh --port', './stop.sh --force')

LOCAL = urllib.request.build_opener(urllib.request.ProxyHandler({}))
HOOK = '''
import importlib.abc, importlib.util, os, sys, time

MODE = os.environ.get('GCL_TEST_HOOK')


class _Patch(importlib.abc.MetaPathFinder):
    """Changes server.runner right after it is imported."""

    def find_spec(self, name, path=None, target=None):
        if name != 'server.runner':
            return None
        sys.meta_path.remove(self)
        spec = importlib.util.find_spec(name)
        load = spec.loader.exec_module

        def exec_module(module):
            load(module)
            if MODE == 'hang-recover':      # listens and answers health, never becomes ready
                module.recover = lambda: time.sleep(3600) or []
            elif MODE == 'busy':            # a batch "runs" until a stop is requested
                module.STATE['running'] = True
                module.request_stop = lambda: module.STATE.update(running=False)
        spec.loader.exec_module = exec_module
        return spec


if MODE:
    sys.meta_path.insert(0, _Patch())
'''


def free_port() -> int:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def get(port: int, path: str = '/api/health'):
    """(status, JSON body) of a GET to 127.0.0.1:port."""
    try:
        with LOCAL.open(f'http://127.0.0.1:{port}{path}', timeout=5) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b'{}')


def pid_in(text: str) -> int:
    return int(re.search(r'PID (\d+)', text).group(1))


class Installation:
    """One isolated installation: a runtime folder and a port of its own."""

    def __init__(self, test: unittest.TestCase, port: int | None = None, home: Path | None = None):
        self.test = test
        self.home = home or Path(tempfile.mkdtemp(prefix='gcl 运行 '))
        test.addCleanup(shutil.rmtree, self.home, True)
        self.port = port or free_port()
        if not (self.home / 'settings.json').exists():
            self.settings({'server': {'port': self.port}})
        self.env = {**os.environ, 'GCL_HOME': str(self.home), 'PYTHONIOENCODING': 'utf-8'}
        self.env.pop('GCL_LAUNCH_TOKEN', None)
        test.addCleanup(self.cleanup)

    def settings(self, value) -> None:
        text = value if isinstance(value, str) else json.dumps(value)
        (self.home / 'settings.json').write_text(text, encoding='utf-8')

    def command(self, *args) -> list[str]:
        return [sys.executable, '-m', 'server.launcher', *args]

    def run(self, *args, env: dict | None = None, timeout: float = 120) -> tuple[int, str]:
        out = subprocess.run(self.command(*args), cwd=ROOT, env={**self.env, **(env or {})}, capture_output=True,
                             text=True, encoding='utf-8', errors='replace', timeout=timeout)
        return out.returncode, out.stdout + out.stderr

    def start(self, *args, env: dict | None = None) -> tuple[int, str]:
        return self.run('start', '--no-browser', '--timeout', '30', *args, env=env)

    def meta(self) -> dict:
        return json.loads((self.home / 'server.pid').read_text(encoding='utf-8'))

    def instance(self) -> str:
        return json.loads((self.home / 'instance.json').read_text(encoding='utf-8'))['id']

    def cleanup(self) -> None:
        if (self.home / 'server.pid').exists():
            self.run('stop', '--force', timeout=90)

    def doubles(self, genshin: str | None = None, hook: str | None = None) -> dict:
        """Environment that loads the test doubles."""
        folder = Path(tempfile.mkdtemp(prefix='gcl-doubles-'))
        self.test.addCleanup(shutil.rmtree, folder, True)
        (folder / 'sitecustomize.py').write_text(HOOK, encoding='utf-8')
        if genshin:
            (folder / 'genshin').mkdir()
            (folder / 'genshin' / '__init__.py').write_text(genshin, encoding='utf-8')
        path = os.pathsep.join(filter(None, [str(folder), os.environ.get('PYTHONPATH')]))
        return {'PYTHONPATH': path, 'GCL_TEST_HOOK': hook or ''}


class ForeignHttp(http.server.ThreadingHTTPServer):
    """Another web service that also answers /api/health with {"ok": true}."""

    def __init__(self, port: int):
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                body = b'{"ok": true}'
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass
        super().__init__(('127.0.0.1', port), Handler)
        threading.Thread(target=self.serve_forever, daemon=True).start()


class LauncherTest(unittest.TestCase):
    def listener(self, host: str = '127.0.0.1', port: int | None = None) -> socket.socket:
        """A program that holds the port and never answers."""
        s = socket.socket()
        s.bind((host, port or 0))
        s.listen(5)
        self.addCleanup(s.close)
        return s

    def assertGone(self, pid: int) -> None:
        deadline = time.monotonic() + 10
        while procinfo.alive(pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        self.assertFalse(procinfo.alive(pid), f'process {pid} is still running')

    # ------------------------------------------------------------ the normal cycle

    def test_start_reuse_status_stop(self):
        app = Installation(self)
        code, out = app.run('status', '--json')
        self.assertEqual(code, 1, out)
        self.assertFalse(json.loads(out)['running'])

        code, out = app.start()
        self.assertEqual(code, 0, out)
        self.assertIn(f'Ready: http://127.0.0.1:{app.port}/', out)
        status, health = get(app.port)
        self.assertEqual((status, health['app'], health['ready']), (200, 'game-companion-local', True))
        self.assertEqual(health['instance'], app.instance())
        meta = app.meta()
        self.assertEqual((meta['pid'], meta['port']), (health['pid'], app.port))
        self.assertTrue(Path(app.home / 'logs' / 'startup.log').exists())

        code, out = app.start()
        self.assertEqual(code, 0, out)
        self.assertIn('already running', out)
        self.assertEqual(get(app.port)[1]['pid'], meta['pid'])

        code, out = app.run('status', '--json')
        info = json.loads(out)
        self.assertEqual((code, info['running'], info['port'], info['pid']), (0, True, app.port, meta['pid']))
        self.assertEqual(Path(info['data']), app.home)

        code, out = app.run('stop')
        self.assertEqual(code, 0, out)
        self.assertIn('stopped', out)
        self.assertGone(meta['pid'])
        self.assertFalse((app.home / 'server.pid').exists())

        code, out = app.run('stop')
        self.assertEqual(code, 0, out)
        self.assertIn('not running', out)

    def test_port_change_while_running(self):
        app = Installation(self)
        self.assertEqual(app.start()[0], 0)
        new_port = free_port()
        code, out = app.run('set-port', str(new_port))
        self.assertEqual(code, 0, out)
        code, out = app.start()
        self.assertEqual(code, 0, out)
        self.assertIn(f'runs on port {app.port}; the port setting is now {new_port}', out)
        info = json.loads(app.run('status', '--json')[1])
        self.assertEqual((info['port'], info['configured_port']), (app.port, new_port))
        code, out = app.run('stop')
        self.assertEqual(code, 0, out)
        self.assertGone(pid_in(out))
        self.assertEqual(app.start()[0], 0)
        self.assertEqual(get(new_port)[0], 200)

    # ------------------------------------------------------------ the port is used by something else

    def test_port_used_by_silent_program(self):
        s = self.listener()
        app = Installation(self, port=s.getsockname()[1])
        code, out = app.start()
        self.assertEqual(code, 4, out)
        self.assertIn(f'127.0.0.1:{app.port} is already in use', out)
        self.assertIn(f'PID {os.getpid()}', out)  # the owner, read from the system
        self.assertIn(START, out)
        self.assertFalse((app.home / 'server.pid').exists())
        code, out = app.run('stop')
        self.assertEqual(code, 0, out)
        self.assertIn('not running', out)
        socket.create_connection(('127.0.0.1', app.port), timeout=2).close()  # Stop never touches other programs

    def test_port_used_by_other_web_service(self):
        port = free_port()
        foreign = ForeignHttp(port)
        self.addCleanup(foreign.server_close)
        self.addCleanup(foreign.shutdown)
        app = Installation(self, port=port)
        code, out = app.start()
        self.assertEqual(code, 4, out)
        self.assertIn('another web service', out)
        self.assertEqual(app.run('stop')[0], 0)
        self.assertEqual(get(port), (200, {'ok': True}))

    def test_port_used_by_other_installation(self):
        first = Installation(self)
        self.assertEqual(first.start()[0], 0)
        pid = first.meta()['pid']
        second = Installation(self, port=first.port)
        code, out = second.start()
        self.assertEqual(code, 4, out)
        self.assertIn('another Game Companion Local installation', out)
        code, out = second.run('stop')
        self.assertEqual(code, 0, out)
        self.assertTrue(procinfo.alive(pid))

    def test_copied_runtime_folder_is_another_installation(self):
        first = Installation(self)
        self.assertEqual(first.start()[0], 0)
        pid = first.meta()['pid']
        copy = Path(tempfile.mkdtemp(prefix='gcl 副本 ')) / 'data'
        shutil.copytree(first.home, copy)  # includes server.pid and instance.json
        second = Installation(self, port=first.port, home=copy)
        self.addCleanup(shutil.rmtree, copy.parent, True)
        code, out = second.start()
        self.assertEqual(code, 4, out)
        code, out = second.run('stop')
        self.assertEqual(code, 0, out)
        self.assertTrue(procinfo.alive(pid))
        self.assertNotEqual(second.instance(), first.instance())

    @unittest.skipUnless(sys.platform.startswith('linux'), 'needs a listener on 127.0.0.2 that blocks 0.0.0.0')
    def test_bind_failure_is_explained(self):
        s = self.listener('127.0.0.2')
        app = Installation(self, port=s.getsockname()[1])
        app.settings({'server': {'port': app.port, 'lan': True}})
        code, out = app.start()
        self.assertEqual(code, 5, out)
        self.assertIn(f'cannot listen on 0.0.0.0:{app.port}', out)
        self.assertIn('The port is held by', out)
        error = json.loads((app.home / 'startup-error.json').read_text(encoding='utf-8'))
        self.assertEqual((error['kind'], error['code']), ('bind', 2))

    # ------------------------------------------------------------ the backend fails or hangs while starting

    def test_import_failure_exits_promptly(self):
        app = Installation(self)
        env = app.doubles(genshin='raise RuntimeError("simulated import failure")\n')
        began = time.monotonic()
        code, out = app.start(env=env)
        self.assertEqual(code, 5, out)
        self.assertLess(time.monotonic() - began, 25)
        self.assertIn('exited with code 1', out)
        self.assertIn('RuntimeError: simulated import failure', out)
        self.assertIn(str(app.home / 'logs' / 'app.log'), out)

    def test_hang_before_listening_is_stopped(self):
        app = Installation(self)
        env = app.doubles(genshin='import time\ntime.sleep(3600)\n')
        code, out = app.run('start', '--no-browser', '--timeout', '6', env=env)
        self.assertEqual(code, 6, out)
        self.assertIn('did not become ready within 6 seconds', out)
        self.assertGone(pid_in(out.split('did not become ready')[1]))

    def test_never_ready_is_stopped_and_api_waits(self):
        app = Installation(self)
        env = {**app.env, **app.doubles(hook='hang-recover')}
        proc = subprocess.Popen(app.command('start', '--no-browser', '--timeout', '15'), cwd=ROOT, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
        self.addCleanup(proc.kill)
        deadline = time.monotonic() + 15
        health = None
        while time.monotonic() < deadline:
            try:
                health = get(app.port)[1]
                break
            except OSError:
                time.sleep(0.2)
        self.assertIsNotNone(health, 'the backend never answered')
        self.assertFalse(health['ready'])
        status, body = get(app.port, '/api/state')
        self.assertEqual(status, 503)
        self.assertIn('still starting', body['error'])
        out = proc.communicate(timeout=60)[0]
        self.assertEqual(proc.returncode, 6, out)
        self.assertGone(health['pid'])

    # ------------------------------------------------------------ stopping only what is ours

    @unittest.skipIf(procinfo.WINDOWS, 'systemd and kill stop the backend with SIGTERM on Linux')
    def test_sigterm_stops_like_stop(self):
        app = Installation(self)
        self.assertEqual(app.start()[0], 0)
        pid = app.meta()['pid']
        os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + 15
        while procinfo.alive(pid) and time.monotonic() < deadline:
            time.sleep(0.2)
        self.assertFalse(procinfo.alive(pid))
        self.assertFalse((app.home / 'server.pid').exists())  # a clean exit removes it; a killed process would not
        self.assertIn('Stopping on request', (app.home / 'logs' / 'app.log').read_text(encoding='utf-8'))

    def test_running_batch_needs_force(self):
        app = Installation(self)
        env = app.doubles(hook='busy')
        self.assertEqual(app.start(env=env)[0], 0)
        pid = app.meta()['pid']
        code, out = app.run('stop')
        self.assertEqual(code, 7, out)
        self.assertIn(STOP, out)
        self.assertTrue(procinfo.alive(pid))
        code, out = app.run('stop', '--force')
        self.assertEqual(code, 0, out)
        self.assertGone(pid)

    def test_stale_pid_file(self):
        app = Installation(self)
        app.run('status')
        ended = subprocess.Popen([sys.executable, '-c', 'pass'])
        ended.wait()
        (app.home / 'server.pid').write_text(json.dumps({'pid': ended.pid, 'port': app.port, 'instance': app.instance(),
                                                         'created': time.time() - 60}), encoding='utf-8')
        code, out = app.run('stop')
        self.assertEqual(code, 0, out)
        self.assertIn('not running', out)
        self.assertFalse((app.home / 'server.pid').exists())

    def test_reused_pid_is_not_stopped(self):
        app = Installation(self)
        app.run('status')
        other = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])
        self.addCleanup(other.wait)
        self.addCleanup(other.kill)
        created = procinfo.created(other.pid)
        self.assertIsNotNone(created)
        record = {'pid': other.pid, 'port': app.port, 'instance': app.instance(), 'created': created - 3600}
        (app.home / 'server.pid').write_text(json.dumps(record), encoding='utf-8')
        code, out = app.run('stop')
        self.assertEqual(code, 0, out)
        self.assertTrue(procinfo.alive(other.pid))

        record['created'] = None  # cannot be verified at all: refuse, keep the file
        (app.home / 'server.pid').write_text(json.dumps(record), encoding='utf-8')
        code, out = app.run('stop')
        self.assertEqual(code, 8, out)
        self.assertIn('cannot be identified', out)
        self.assertTrue(procinfo.alive(other.pid))
        self.assertTrue((app.home / 'server.pid').exists())
        (app.home / 'server.pid').unlink()

    def test_backend_of_an_older_version(self):
        """Started before instance ids existed: its PID file is {pid, port, started, exe}."""
        app = Installation(self)
        self.assertEqual(app.start()[0], 0)
        meta = app.meta()
        legacy = {'pid': meta['pid'], 'port': meta['port'], 'started': meta['started'], 'exe': meta['exe']}
        (app.home / 'server.pid').write_text(json.dumps(legacy), encoding='utf-8')
        code, out = app.run('stop')
        self.assertEqual(code, 0, out)
        self.assertGone(meta['pid'])

    def test_older_version_is_named_on_start(self):
        port = free_port()
        foreign = ForeignHttp(port)  # answers like an older backend: {"ok": true}, no instance id
        self.addCleanup(foreign.server_close)
        self.addCleanup(foreign.shutdown)
        app = Installation(self, port=port)
        pid_file = app.home / 'server.pid'
        pid_file.write_text(json.dumps({'pid': os.getpid(), 'port': port, 'started': '', 'exe': ''}), encoding='utf-8')
        self.addCleanup(pid_file.unlink, missing_ok=True)  # runs first: cleanup must never stop this test process
        code, out = app.start()
        self.assertEqual(code, 4, out)
        self.assertIn(f'An older version of Game Companion Local is running from this runtime folder (PID {os.getpid()})', out)

    # ------------------------------------------------------------ configuration

    def test_unusable_settings_fail_clearly(self):
        app = Installation(self)
        for value in ('{broken', '[1, 2]', {'server': {'port': '18800'}}, {'server': {'port': 70000}},
                      {'server': {'lan': 'false'}}):
            with self.subTest(value=value):
                app.settings(value)
                code, out = app.start()
                self.assertEqual(code, 3, out)
                self.assertIn('settings.json', out)
                self.assertEqual(app.run('status')[0], 3)
                self.assertEqual(app.run('stop')[0], 0)
                self.assertFalse((app.home / 'server.pid').exists())
        app.settings({'server': {'port': app.port}})
        self.assertEqual(app.run('set-port', '0')[0], 3)
        self.assertEqual(app.run('set-port', str(app.port + 1))[0], 0)
        self.assertEqual(json.loads((app.home / 'settings.json').read_text(encoding='utf-8'))['server']['port'], app.port + 1)

    def test_check_deps(self):
        app = Installation(self)
        self.assertEqual(app.run('check-deps')[0], 0)
        # -S leaves out site-packages, so the required packages are missing
        out = subprocess.run([sys.executable, '-S', '-m', 'server.launcher', 'check-deps'], cwd=ROOT, env=app.env,
                             capture_output=True, text=True, encoding='utf-8', errors='replace')
        self.assertEqual(out.returncode, 9, out.stdout + out.stderr)
        self.assertIn('Missing Python packages: genshin, qrcode, PyYAML', out.stdout)


class ProcInfoTest(unittest.TestCase):
    def test_port_from_dword(self):
        self.assertEqual(procinfo.port_from_dword(0x7049), 18800)  # network byte order in the low word

    def test_identity_of_this_process(self):
        pid = os.getpid()
        created = procinfo.created(pid)
        self.assertIsNotNone(created)
        self.assertTrue(procinfo.same_process(pid, created, procinfo.image(pid)))
        self.assertFalse(procinfo.same_process(pid, created - 100, None))
        self.assertFalse(procinfo.same_process(pid, created, os.path.join('elsewhere', 'other.exe')))

    def test_ended_process(self):
        ended = subprocess.Popen([sys.executable, '-c', 'pass'])
        ended.wait()
        self.assertFalse(procinfo.alive(ended.pid))
        self.assertFalse(procinfo.same_process(ended.pid, None, None))

    def test_port_owner(self):
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0))
            s.listen(1)
            self.assertEqual(procinfo.port_owner(s.getsockname()[1]), os.getpid())
        self.assertIsNone(procinfo.port_owner(free_port()))


if __name__ == '__main__':
    unittest.main()
