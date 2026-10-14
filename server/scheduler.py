"""Built-in scheduler: batch slots with catch-up, stamina polling, goal sync, notification outbox."""
from __future__ import annotations

import logging
import subprocess
import sys
import threading
import time
from datetime import timedelta
from pathlib import Path

from . import core, goals, mihoyo, notify, planner, runner, tools
from .i18n import tr

log = logging.getLogger('gcl.scheduler')
# Windows Task Scheduler name ("Game Companion Local"). Kept as is: renaming it would
# orphan the logon task of existing installs.
TASK_NAME = '养成中枢本地版'


def slot_key(at) -> str:
    return 'slot_done:' + at.strftime('%Y-%m-%d@%H:%M')


def mark_past_slots_done() -> None:
    """Enabling the schedule must not trigger a surprise catch-up of earlier slots."""
    s = core.settings()['schedule']
    today = core.now().date()
    for day in (today - timedelta(days=1), today):
        for at in planner.slot_times(day, s['times']):
            if at <= core.now():
                core.put(slot_key(at), {'skipped': tr('slot_before_enable')})


def due_slot():
    s = core.settings()['schedule']
    if not s['enabled']:
        return None
    current = core.now()
    for day in (current.date() - timedelta(days=1), current.date()):
        for at in planner.slot_times(day, s['times']):
            if at <= current and core.get(slot_key(at)) is None:
                if (current - at).total_seconds() <= float(s['catchup_hours']) * 3600:
                    return at
                core.put(slot_key(at), {'skipped': tr('slot_missed', hours=s['catchup_hours'])})
    return None


def next_slot():
    s = core.settings()['schedule']
    if not s['enabled']:
        return None
    slots = planner.upcoming_slots(2)
    return core.stamp(slots[0]) if slots else None


def tick() -> None:
    s = core.settings()
    at = due_slot()
    if at and not tools.automation():  # a host that cannot run (Linux) lets the slot pass
        core.put(slot_key(at), {'skipped': tr('runs_need_windows')})
    elif at and not runner.busy():
        core.put(slot_key(at), {'started': core.stamp()})
        try:
            runner.start_batch(s['schedule']['games'], at.strftime('%H:%M'), 'schedule')
        except Exception as exc:
            core.put(slot_key(at), {'error': str(exc)})
            notify.event('failure', tr('slot_failed_title', slot=at.strftime('%H:%M')), [str(exc)])
    # stamina (refresh_notes skips a source that is backing off)
    for game in ('genshin', 'zzz'):
        last = core.latest_sample(game)
        seen = core.parse(last['at']) if last else None
        if mihoyo.accounts().get(game) and (seen is None or core.now() - seen >= timedelta(minutes=int(s['sync']['notes_minutes']))):
            mihoyo.refresh_notes(game)
    # goal sync (one per tick keeps request bursts small)
    if mihoyo.logged_in() and not runner.busy():
        due = goals.due_for_sync(float(s['sync']['goals_hours']))
        if due and mihoyo.allowed('calc'):
            goal = goals.sync(due[0]['id'])
            mihoyo.record('calc', not goal.get('calc_error'), goal.get('calc_error') or '')
    notify.drain()


def loop() -> None:
    while True:
        try:
            tick()
        except Exception:
            log.exception('Scheduler loop error')
        time.sleep(20)


def start() -> None:
    threading.Thread(target=loop, daemon=True, name='scheduler').start()


# ---------------------------------------------------------------- logon autostart (the only Task Scheduler job)

def autostart_command() -> str:
    pythonw = Path(sys.executable).with_name('pythonw.exe')
    exe = pythonw if pythonw.is_file() else Path(sys.executable)
    return f'"{exe}" -m server'


def set_autostart(enabled: bool) -> str:
    if not tools.automation():  # Task Scheduler is Windows-only; Linux has start.sh --service
        if enabled:
            raise ValueError(tr('autostart_windows'))
        return ''
    if enabled:
        # the task must use this runtime folder too; the default one needs no variable
        home = '' if core.DATA == core.APP / 'data' else f'set "GCL_HOME={core.DATA}" && '
        cmd = ['schtasks', '/Create', '/F', '/SC', 'ONLOGON', '/RL', 'HIGHEST', '/TN', TASK_NAME,
               '/TR', f'cmd /c cd /d "{core.APP}" && {home}{autostart_command()}']
    else:
        cmd = ['schtasks', '/Delete', '/F', '/TN', TASK_NAME]
    out = subprocess.run(cmd, capture_output=True, text=True, creationflags=0x08000000)
    if out.returncode != 0 and enabled:
        raise ValueError(tr('autostart_failed', detail=(out.stderr or out.stdout).strip()[:200]))
    return (out.stdout or '').strip()


def autostart_installed() -> bool:
    if not tools.automation():
        return False
    out = subprocess.run(['schtasks', '/Query', '/TN', TASK_NAME], capture_output=True, text=True, creationflags=0x08000000)
    return out.returncode == 0
