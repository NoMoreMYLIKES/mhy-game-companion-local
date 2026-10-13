"""Parts ③④ – run one batch: plan → configure tool → launch → wait → receipt → restore."""
from __future__ import annotations

import logging
import threading
import time
import uuid

from . import core, goals, mihoyo, notify, planner, tools
from .i18n import tr

log = logging.getLogger('gcl.runner')
LOCK = threading.Lock()
STOP = threading.Event()
STATE: dict = {'running': False}
STATUSES = ('SUCCESS', 'PARTIAL', 'FAILED', 'SKIPPED', 'STOPPED')


def state() -> dict:
    return dict(STATE)


def busy() -> bool:
    return bool(STATE.get('running'))


def start_batch(games: list[str], slot: str = 'manual', source: str = 'manual') -> str:
    if not tools.automation():
        raise ValueError(tr('runs_need_windows'))
    games = [g for g in ('zzz', 'genshin') if g in games]
    if not games:
        raise ValueError(tr('select_game'))
    with LOCK:
        if STATE.get('running'):
            raise ValueError(tr('batch_running'))
        if core.get('patch_journal'):
            errors = tools.restore_all()
            if errors:
                raise ValueError(tr('restore_pending', errors=tr('sep_strong').join(errors)))
        run_id = core.now().strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:6]
        STOP.clear()
        STATE.clear()
        STATE.update(running=True, run_id=run_id, slot=slot, source=source, games=games, game=None,
                     stage=tr('stage_prepare'), stage_key='stage_prepare', started=core.stamp())
        core.put('current_run', {'id': run_id, 'started': STATE['started'], 'slot': slot, 'source': source, 'games': games})
    threading.Thread(target=_batch, args=(run_id, games, slot, source), daemon=True, name='batch').start()
    return run_id


def request_stop() -> None:
    if STATE.get('running'):
        STOP.set()
        _stage('stage_stopping')


def _stage(key: str) -> None:
    """Current stage: translated text for display, stable key for the UI stepper."""
    STATE.update(stage=tr(key), stage_key=key)


def _sleep(seconds: float) -> bool:
    """Interruptible wait; True when a stop was requested."""
    return STOP.wait(seconds)


def _morning(slot: str) -> bool:
    return len(slot) >= 5 and slot[2] == ':' and slot[:2].isdigit() and int(slot[:2]) < 12


def _batch(run_id: str, games: list[str], slot: str, source: str) -> None:
    run = {'id': run_id, 'started': STATE['started'], 'slot': slot, 'source': source, 'games': [], 'status': 'RUNNING'}
    core.save_run(run)
    muted = None
    try:
        if source == 'schedule' and _morning(slot) and core.settings()['features']['mute_morning']:
            try:
                muted = tools.audio('mute')
                core.put('mute_journal', muted)
            except Exception as exc:
                run.setdefault('notes', []).append(tr('mute_failed', error=exc))
        for game in games:
            if STOP.is_set():
                break
            STATE['game'] = game
            try:
                result = _run_game(run_id, game)
            except Exception as exc:  # never leave the batch without a receipt
                log.exception('Game run failed')
                result = {'game': game, 'status': 'FAILED', 'summary': tr('run_exception', error=exc), 'errors': [str(exc)]}
            run['games'].append(result)
            core.save_run(run)
    finally:
        if muted:
            _unmute(muted)
        statuses = [g['status'] for g in run['games']]
        run['status'] = ('STOPPED' if STOP.is_set() else 'FAILED' if 'FAILED' in statuses else
                         'PARTIAL' if 'PARTIAL' in statuses else 'SUCCESS' if statuses else 'SKIPPED')
        run['ended'] = core.stamp()
        core.save_run(run)
        core.delete('current_run')
        STATE.clear()
        STATE['running'] = False
        _after(run)


def _unmute(muted: dict) -> None:
    try:
        tools.audio('set', muted['endpoint'], bool(muted['before']))
        core.delete('mute_journal')
    except Exception:
        log.exception('Failed to restore the mute state')


def _after(run: dict) -> None:
    lines = [tr('game_line', game=tr('game_' + g['game']), text=g.get('summary', '')) for g in run['games']]
    slot = tr('slot_manual') if run['slot'] == 'manual' else run['slot']
    status = tr('status_' + run['status']) if run['status'] in STATUSES else run['status']
    title = tr('batch_title', slot=slot, status=status)
    notify.event('batch', title, lines + run.get('notes', []), ok=run['status'] in ('SUCCESS', 'SKIPPED'))
    if run['status'] in ('FAILED', 'PARTIAL') and not core.settings()['notify']['events'].get('batch'):
        notify.event('failure', title, lines)
    # Official inventory needs a moment; correct the stable list at +60 s and +180 s.
    for g in run['games']:
        if g.get('goal_id') and g.get('completed'):
            goals.queue_sync(g['goal_id'], observe=False, delay=60)
            goals.queue_sync(g['goal_id'], observe=False, delay=180)
        if g.get('started_tool'):
            threading.Timer(60, lambda game=g['game']: mihoyo.refresh_notes(game, force=True)).start()


def _run_game(run_id: str, game: str) -> dict:
    s = core.settings()
    try:
        mihoyo.refresh_notes(game)  # best effort; the tool reads the real stamina anyway
    except Exception:
        pass
    p = planner.plan(game)
    item = p['item']
    result = {'game': game, 'status': 'FAILED', 'reason': p['reason'], 'phase': p['phase'],
              'item': item and {k: item[k] for k in ('key', 'goal', 'label', 'names', 'unit_label', 'upper', 'expected')},
              'goal_id': item and item.get('goal_id'), 'completed': None, 'errors': [], 'notes': [],
              'started': core.stamp()}
    game_exe, tool_exe = tools.game_exe(game), tools.tool_exe(game)
    if not tool_exe.is_file():
        tool = 'BetterGI' if game == 'genshin' else tr('tool_onedragon')
        return _finish(result, 'FAILED', tr('tool_missing', tool=tool, path=tool_exe))
    if game_exe and tools.running(game_exe):
        if s['execution']['if_game_running'] == 'skip':
            return _finish(result, 'SKIPPED', tr('skip_game_running'))
        tools.kill_path(game_exe)
    tools.kill_path(tool_exe)
    proc = None
    plan_ids: list[str] = []
    baseline: dict = {}
    timed_out = False
    try:
        _stage('stage_config')
        if game == 'genshin':
            profile = tools.bgi_prepare(item)
        else:
            plan_ids = tools.zzz_prepare(run_id, item)
            if item and not tools.zzz_patch_ok():
                result['notes'].append(tr('zzz_no_patch'))
        baseline = tools.log_baseline(game)
        _stage('stage_launch')
        tools.launch_game(game)
        if _sleep(5):
            raise InterruptedError
        _stage('stage_running')
        if game == 'genshin':
            proc = tools.start(tool_exe, ['startOneDragon', profile], hidden=True)
        else:
            proc = tools.start(tool_exe, ['-o', '-c'], cwd=tools.zzz_root(), hidden=True)
        result['started_tool'] = True
        deadline = time.monotonic() + int(s['execution']['timeout_minutes']) * 60
        terminal_at = None
        while proc.poll() is None:
            if _sleep(5):
                raise InterruptedError
            if time.monotonic() > deadline:
                timed_out = True
                break
            if game == 'genshin' and terminal_at is None and tools.BGI_TERMINAL in tools.read_new(game, baseline):
                terminal_at = time.monotonic()
            if terminal_at and time.monotonic() - terminal_at > 30:
                break  # BetterGI finished its list; it may stay open
    except InterruptedError:
        result['status'] = 'STOPPED'
    except Exception as exc:
        result['errors'].append(str(exc))
    finally:
        _stage('stage_collect')
        for path in (tool_exe, game_exe):
            try:
                tools.kill_path(path)
            except Exception as exc:
                result['errors'].append(tr('kill_failed', error=exc))
        if proc and proc.poll() is None:
            tools.kill_tree(proc.pid)
        time.sleep(2)
        text = tools.read_new(game, baseline) if baseline is not None else ''
        receipt = tools.zzz_receipt(plan_ids) if game == 'zzz' and plan_ids else None
        result['errors'] += tools.restore_all()
    return _receipt(result, game, item, text, receipt, timed_out)


def _receipt(result: dict, game: str, item: dict | None, text: str, receipt: dict | None, timed_out: bool) -> dict:
    stopped = result['status'] == 'STOPPED'
    if game == 'genshin':
        log_ = tools.parse_bgi(text)
        result['log'] = log_
        if item:
            units = log_['claims20'] + 2 * log_['claims40'] if item['unit'] == 'claim20' else log_['claims40']
            result['completed'] = min(units, item['upper'])
        if log_['extra']:
            result['notes'].append(tr('extra_resin', items=tr('sep').join(log_['extra'])))
        ok = log_['terminal']
        result['errors'] += log_['errors'][-3:] if not ok else []
    else:
        log_ = tools.parse_zzz(text)
        result['log'] = log_
        if item:
            result['completed'] = (receipt or {}).get('completed')
            if result['completed'] is None and receipt:
                result['notes'].append(receipt.get('reason', tr('amount_unverified')))
        stop = (receipt or {}).get('energy_stop')
        energy = stop.get('current') if stop else log_['last_energy']
        if type(energy) is int:
            core.add_sample('zzz', energy, None, 'source_onedragon')  # message key, translated when shown
        ok = log_['one_dragon'] == 'success' and log_['charge'] != 'failed'
        if not ok:
            result['errors'] += log_['errors'][-3:]
    done = result['completed'] or 0
    if item and done > 0:
        if result['phase'] == 'equipment':
            core.put('equip_used:' + game, int(core.get('equip_used:' + game, 0)) + done)
        else:
            goals.record_done(item['key'], done)
    if stopped:
        status, why = 'STOPPED', tr('user_stopped')
    elif timed_out:
        status, why = 'FAILED', tr('timed_out')
    elif result['errors'] and not ok:
        status, why = 'FAILED', result['errors'][0]
    elif not ok:
        status, why = 'PARTIAL', tr('no_terminal')
    else:
        status, why = 'SUCCESS', ''
    if item:
        amount = tr('qty_unverified') if result['completed'] is None else f"{result['completed']}{item['unit_label']}"
        summary = tr('summary_item', goal=item['goal'], label=item['label'], amount=amount, upper=item['upper'])
    else:
        summary = tr('summary_idle')
    return _finish(result, status, summary + (tr('sep_strong') + why if why else ''))


def _finish(result: dict, status: str, summary: str) -> dict:
    result.update(status=status, summary=summary, ended=core.stamp())
    return result


def recover() -> list[str]:
    """Startup: restore configs/mute left by a crash and close the interrupted run record."""
    notes = []
    if core.get('patch_journal'):
        errors = tools.restore_all()
        notes.append(tr('recovered_configs') if not errors else tr('sep_strong').join(errors))
    muted = core.get('mute_journal')
    if muted:
        _unmute(muted)
        notes.append(tr('recovered_mute'))
    current = core.get('current_run')
    if current:
        run = next((r for r in core.runs(50) if r['id'] == current['id']), None) or {**current, 'games': []}
        run.update(status='FAILED', ended=core.stamp(), notes=run.get('notes', []) + [tr('run_interrupted_note')])
        core.save_run(run)
        core.delete('current_run')
        notes.append(tr('run_interrupted'))
    return notes
