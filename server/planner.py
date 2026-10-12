"""Part ② – stamina plan. One rule source for the preview, the calendar and execution.

Rule (per game, per batch, exactly one item):
  enabled goals in user order → category order → first item that is
  not collected, has an automatic route, is not paused, has a known finite
  unit count, is open today and still has allowance left.
  Otherwise the optional equipment continuation (artifact / drive disc)
  within its cumulative cap. Otherwise nothing: stamina is kept.
The tool stops by itself when the live stamina is insufficient, so the
issued unit count is an upper bound, never a promise.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta

from . import core, materials
from .i18n import MESSAGES, tr

RECOVERY_MINUTES = {'genshin': 8, 'zzz': 6}
DEFAULT_CAP = {'genshin': 200, 'zzz': 240}
_CTX: dict = {}


def tool_context() -> dict:
    """Tool catalogs, re-read at most every 10 minutes."""
    s = core.settings()['paths']
    key = (s['bettergi'], s['onedragon'])
    if _CTX.get('key') != key or time.monotonic() - _CTX.get('at', 0) > 600:
        _CTX.update(key=key, at=time.monotonic(), value={
            'bosses': materials.bgi_bosses(s['bettergi']),
            'domains': materials.bgi_domains(s['bettergi']),
            'compendium': materials.zzz_compendium(s['onedragon'])})
    return _CTX['value']


def days_text(weekdays: list[int]) -> str:
    if sorted(weekdays) == list(range(7)):
        return tr('every_day')
    names = tr('weekday_names').split(',')
    return tr('on_days', days=tr('sep').join(names[d] for d in sorted(weekdays)))


# ---------------------------------------------------------------- items with allowance

def goal_items(goal: dict, ctx: dict | None = None) -> list[dict]:
    """Collection items plus the stable-list allowance (issued units minus executed)."""
    ctx = ctx or tool_context()
    result = []
    for item in materials.items_for_goal(goal, ctx):
        entry = (goal.get('allowance') or {}).get(item['key'])
        if entry and entry.get('calc_at') == goal.get('calc_at') and item['units'] is not None:
            item['executed'] = int(entry.get('done', 0))
            item['available'] = max(0, int(entry['units']) - item['executed'])
        else:
            item['executed'] = 0
            item['available'] = item['units']
        item['cost'] = materials.COST.get(item['unit'])
        item['unit_label'] = materials.unit_label(item['unit'])
        item['progress'] = materials.item_progress(item)
        result.append(item)
    return result


def blocker(item: dict, weekday: int) -> str | None:
    """Why this item cannot run now; None means it can."""
    if item['done']:
        return tr('blk_done')
    if item['kind'] == 'manual':
        return item['note']
    if item['paused']:
        return tr('blk_paused')
    if item['units'] is None:
        return item['note']
    if weekday not in item['weekdays']:
        return tr('blk_closed', days=days_text(item['weekdays']))
    if not item['available']:
        return tr('blk_exhausted')
    return None


# ---------------------------------------------------------------- stamina

def estimate(game: str, at: datetime | None = None) -> dict | None:
    """Latest official/in-game reading plus natural recovery; None is UNKNOWN."""
    sample = core.latest_sample(game)
    if not sample:
        return None
    seen = core.parse(sample['at'])
    at = at or core.now()
    cap = sample.get('cap') or DEFAULT_CAP[game]
    value = int(sample['current'])
    if value < cap and at > seen:
        value = min(cap, value + int((at - seen).total_seconds() // (RECOVERY_MINUTES[game] * 60)))
    source = sample['source']  # a message key; older rows hold already translated text
    return {'value': value, 'cap': cap, 'source': tr(source) if source in MESSAGES else source, 'seen': sample['at']}


# ---------------------------------------------------------------- equipment continuation

def equipment(game: str, consumed: dict | None = None) -> dict:
    """Optional artifact / disc continuation; the cumulative cap is the authorization."""
    p = core.settings()['planning']
    if game == 'genshin':
        conf, name, unit, label = p['artifact'], p['artifact'].get('domain'), 'claim20', tr('equip_artifact')
    else:
        conf, name, unit, label = p['disc'], p['disc'].get('mission'), 'disc', tr('equip_disc')
    used = int(core.get('equip_used:' + game, 0)) + int((consumed or {}).get('equip:' + game, 0))
    cap = int(conf.get('cap') or 0)
    result = {'enabled': bool(conf.get('enabled')), 'name': name or '', 'cap': cap, 'used': used,
              'left': max(0, cap - used), 'label': label, 'unit': unit}
    if not result['enabled']:
        result['why'] = tr('equip_off', label=label)
    elif not name:
        result['why'] = tr('equip_no_target', label=label)
    elif cap <= 0:
        result['why'] = tr('equip_zero_cap', label=label)
    elif result['left'] <= 0:
        result['why'] = tr('equip_cap_reached', label=label, cap=cap)
    return result


def _equip_item(game: str, eq: dict) -> dict:
    if game == 'genshin':
        route = {'kind': 'domain', 'name': eq['name'], 'domain_type': 'BlessDomain'}
    else:
        # OneDragon category "Area Patrol" (data identifier)
        route = {'category': '区域巡防', 'mission_type': eq['name'], 'mission': None, 'unit': 'disc'}
    return {'key': 'equip:' + game, 'goal_id': None, 'goal': tr('equip_goal', label=eq['label']), 'game': game,
            'kind': 'domain' if game == 'genshin' else 'zzz', 'label': eq['name'], 'names': eq['label'],
            'unit': eq['unit'], 'unit_label': materials.unit_label(eq['unit']), 'cost': materials.COST[eq['unit']],
            'route': route, 'weekdays': list(range(7)), 'units': eq['left'], 'available': eq['left'],
            'executed': eq['used'], 'note': tr('equip_note', cap=eq['cap'], used=eq['used']), 'progress': '',
            'materials': [], 'equipment': True}


# ---------------------------------------------------------------- the plan

def plan(game: str, at: datetime | None = None, stamina: int | None | str = 'estimate',
         consumed: dict | None = None) -> dict:
    """What this game would farm in a batch at ``at``.

    ``consumed`` maps item keys to units already assumed by earlier simulated
    batches (forecast only). ``stamina='estimate'`` uses the latest reading.
    """
    at = at or core.now()
    weekday = core.game_date(at).weekday()
    consumed = consumed or {}
    ctx = tool_context()
    est = estimate(game, at) if stamina == 'estimate' else (
        None if stamina is None else {'value': int(stamina), 'cap': DEFAULT_CAP[game], 'source': tr('source_forecast')})
    waiting, chosen = [], None
    for goal in core.goals(game):
        if not goal.get('enabled'):
            continue
        if goal.get('calc_error') and not goal.get('materials'):
            waiting.append({'goal': goal['name'], 'label': tr('label_calc'), 'why': goal['calc_error']})
            continue
        if not goal.get('calc_at'):
            waiting.append({'goal': goal['name'], 'label': tr('label_calc'), 'why': tr('calc_pending')})
            continue
        for item in goal_items(goal, ctx):
            if item['available'] is not None:
                item['available'] = max(0, item['available'] - int(consumed.get(item['key'], 0)))
            why = blocker(item, weekday)
            if why:
                if not item['done']:
                    waiting.append({'goal': goal['name'], 'label': item['label'], 'key': item['key'], 'why': why})
                continue
            if chosen is None:
                chosen = item
        if chosen:
            break
    phase = 'goal' if chosen else None
    eq = equipment(game, consumed)
    if not chosen and not eq.get('why'):
        chosen, phase = _equip_item(game, eq), 'equipment'
    daily = daily_tasks(game)
    result = {'game': game, 'at': core.stamp(at), 'weekday': weekday, 'stamina': est, 'phase': phase,
              'item': None, 'waiting': waiting[:12], 'equipment': eq,
              'daily': [tr(k) for k in daily], 'daily_keys': daily}
    stamina_name = tr('stamina_' + game)
    if not chosen:
        result['reason'] = tr('reason_idle', stamina=stamina_name)
        if eq.get('why') and eq['enabled']:
            result['reason'] += tr('sentence', text=eq['why'])
        return result
    cost = chosen['cost']
    expected = None if est is None else min(chosen['available'], est['value'] // cost)
    item = {k: chosen.get(k) for k in ('key', 'goal_id', 'goal', 'label', 'names', 'kind', 'unit', 'unit_label',
                                       'route', 'available', 'executed', 'units', 'note', 'progress', 'weekdays')}
    item.update(cost=cost, upper=chosen['available'], expected=expected)
    if game == 'genshin' and chosen['unit'] == 'claim20':
        item['claims'] = claims_split(chosen['available'])
        if weekday == 6 and phase == 'goal':
            item['sunday'] = str(min(chosen['weekdays']) + 1)
    result['item'] = item
    exp = tr('exp_unknown') if expected is None else tr('exp_known', value=est['value'], stamina=stamina_name,
                                                          expected=expected, unit=item['unit_label'])
    result['reason'] = tr('reason_plan', lead=tr('lead_goal' if phase == 'goal' else 'lead_equip'),
                          goal=item['goal'], label=item['label'], names=item['names'], upper=item['upper'],
                          unit=item['unit_label'], cost=cost, stamina=stamina_name, exp=exp)
    return result


def claims_split(units: int) -> dict:
    """20-resin reward units → 40-resin double claims first (settings), remainder single."""
    double = units // 2 if core.settings()['planning']['genshin_claim_mode'] == 'double' else 0
    return {'o40': double, 'o20': units - 2 * double}


def daily_tasks(game: str) -> list[str]:
    """Message keys of the free daily tasks that run with every batch."""
    f = core.settings()['features']
    if game == 'genshin':
        keys = [('genshin_mail', 'daily_mail'), ('genshin_teapot', 'daily_teapot'),
                ('genshin_daily_reward', 'daily_commission')]
        return [key for feature, key in keys if f[feature]]
    return ['daily_onedragon'] + (['daily_zzz_rewards'] if f['zzz_rewards'] else [])


# ---------------------------------------------------------------- schedule & forecast

def slot_times(day, times: list[str]) -> list[datetime]:
    result = []
    for t in sorted(times):
        h, m = (int(x) for x in t.split(':'))
        result.append(datetime(day.year, day.month, day.day, h, m, tzinfo=core.CN))
    return result


def upcoming_slots(days: int = 3, start: datetime | None = None) -> list[datetime]:
    s = core.settings()['schedule']
    start = start or core.now()
    result = []
    for offset in range(days + 1):
        day = (start + timedelta(days=offset)).date()
        result.extend(t for t in slot_times(day, s['times']) if t > start)
    return result[:days * max(1, len(s['times']))]


def forecast(days: int = 3) -> dict:
    """Simulate the next batches with the same plan() rule (preview only)."""
    s = core.settings()
    slots = upcoming_slots(days)
    rows = []
    for game in s['schedule']['games']:
        consumed: dict = {}
        est = estimate(game)
        value, last_at, cap = (est['value'], core.now(), est['cap']) if est else (None, None, DEFAULT_CAP[game])
        coffee_days = set()
        for slot in slots:
            if value is not None:
                value = min(cap, value + int((slot - last_at).total_seconds() // (RECOVERY_MINUTES[game] * 60)))
                if game == 'zzz' and core.game_date(slot) != core.game_date() and core.game_date(slot) not in coffee_days:
                    coffee_days.add(core.game_date(slot))
                    value += int(s['planning']['zzz_coffee_forecast'])
                last_at = slot
            p = plan(game, slot, stamina=value, consumed=consumed)
            item = p['item']
            row = {'game': game, 'at': core.stamp(slot), 'stamina': value, 'reason': p['reason'],
                   'label': item and f"{item['goal']} · {item['label']}", 'unit_label': item and item['unit_label'],
                   'upper': item and item['upper'], 'expected': item and item['expected'], 'phase': p['phase'],
                   'goal': item and item['goal'], 'goal_id': item and item['goal_id'], 'task': item and item['label'],
                   'names': item and item['names'], 'cost': item and item['cost'], 'spend': None, 'left': value}
            if item:
                units = item['expected'] if item['expected'] is not None else 0
                consumed[item['key']] = consumed.get(item['key'], 0) + units
                if value is not None:
                    row['spend'] = units * item['cost']
                    value -= row['spend']
                    row['left'] = value
            rows.append(row)
    rows.sort(key=lambda r: (r['at'], r['game']))
    return {'slots': [core.stamp(x) for x in slots], 'rows': rows, 'schedule_enabled': s['schedule']['enabled']}
