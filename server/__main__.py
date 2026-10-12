"""Entry point: ``python -m server`` (headless with pythonw)."""
from __future__ import annotations

import logging
import os
import sys
import time

from . import core


def main() -> int:
    core.setup_logging()
    log = logging.getLogger('gcl')
    from . import runner, scheduler, web
    try:
        httpd = web.serve()
    except OSError as exc:
        log.error('Port in use; another backend may already be running: %s', exc)
        return 2
    core.write_json(core.DATA / 'server.pid', {'pid': os.getpid(), 'port': httpd.server_port, 'started': core.stamp(),
                                                'exe': sys.executable})
    for note in runner.recover():
        log.warning(note)
    web.run_forever(httpd)
    scheduler.start()
    log.info('Game Companion Local %s started on %s:%s (admin: %s)', core.VERSION, *httpd.server_address[:2], core.is_admin())
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    sys.exit(main())
