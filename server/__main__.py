"""Entry point: ``python -m server`` (headless with pythonw).

Exit codes: 0 stopped normally, 1 startup exception, 2 cannot listen on the address,
3 invalid settings.json. Every failure is written to logs/app.log and to
startup-error.json in the runtime folder, which the launcher reads to explain it.
"""
from __future__ import annotations

import atexit
import logging
import os
import secrets
import signal
import sys
import traceback

from . import core, procinfo


def _fail(kind: str, message: str, code: int, **extra) -> int:
    core.write_json(core.DATA / 'startup-error.json', {'kind': kind, 'message': message, 'code': code,
                                                       'at': core.stamp(), 'pid': os.getpid(), **extra})
    return code


def _remove_pid_file() -> None:
    path = core.DATA / 'server.pid'
    if (core.read_json(path, {}) or {}).get('pid') == os.getpid():
        path.unlink(missing_ok=True)


def main() -> int:
    core.setup_logging()
    log = logging.getLogger('gcl')
    (core.DATA / 'startup-error.json').unlink(missing_ok=True)
    try:
        core.check_settings_file()
    except core.SettingsError as exc:
        log.error('Invalid settings: %s', exc)
        return _fail('settings', str(exc), 3)
    host, port = core.listen_address()
    try:
        from . import runner, scheduler, web
    except Exception as exc:
        log.exception('Startup failed while loading the backend')
        return _fail('exception', f'{type(exc).__name__}: {exc}', 1, trace=traceback.format_exc(limit=8))
    try:
        httpd = web.serve()
    except OSError as exc:  # the original error is kept: a busy port, missing permission, a bad address...
        log.error('Cannot listen on %s:%s: %s', host, port, exc)
        return _fail('bind', str(exc), 2, host=host, port=port, errno=getattr(exc, 'winerror', None) or exc.errno)
    try:
        identity = {'instance': core.instance_id(), 'launch': os.environ.get('GCL_LAUNCH_TOKEN') or None,
                    'token': secrets.token_hex(16), 'created': procinfo.created(os.getpid())}
        web.IDENTITY.update(identity)
        core.write_json(core.DATA / 'server.pid', {
            'app': web.APP_ID, 'pid': os.getpid(), 'host': host, 'port': httpd.server_port, 'version': core.VERSION,
            'started': core.stamp(), 'image': procinfo.image(os.getpid()), 'exe': sys.executable, **identity})
        atexit.register(_remove_pid_file)
        web.run_forever(httpd)  # health answers from here on; other API calls wait for READY
        if os.name != 'nt':  # systemd and kill send SIGTERM: leave the way Stop does
            signal.signal(signal.SIGTERM, lambda *_: web.stop_soon())
        for note in runner.recover():
            log.warning(note)
        if not web.SHUTDOWN.is_set():  # a stop that arrived during recovery skips the scheduler
            scheduler.start()
            web.READY.set()
    except Exception as exc:
        log.exception('Startup failed')
        return _fail('exception', f'{type(exc).__name__}: {exc}', 1, trace=traceback.format_exc(limit=8))
    if web.READY.is_set():
        log.info('Game Companion Local %s started on %s:%s (admin: %s)', core.VERSION, host, httpd.server_port, core.is_admin())
    try:
        while not web.SHUTDOWN.wait(1):
            pass
        log.info('Stopping on request')
    except KeyboardInterrupt:
        pass
    httpd.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
