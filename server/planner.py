"""Part ② – stamina plan. One rule source for the preview, the calendar and execution.

Rule (per game, per batch, exactly one item):
  enabled goals in user order → category order → first item that is
  not collected, has an automatic route, is not paused, has a known finite
  unit count, is open today and still has allowance left.
  The account's stock serves the goals once, in that order: what an earlier
  goal needs is not counted again for a later one.
  A goal whose calculation is missing, older than its targets and levels, or
  of another game role is not farmed until it is calculated again.
  Otherwise the optional equipment continuation (artifact / drive disc)
  within its cumulative cap, granted for the selected role. Otherwise nothing:
  stamina is kept.
The tool stops by itself when the live stamina is insufficient, so the
issued unit count is an upper bound, never a promise.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta

from . import core, gear, inventory, materials
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

def items_by_goal(game: str, ctx: dict | None = None, override: dict | None = None, role=core.SELECTED) -> dict:
    """Every goal's collection items, with the account's stock handed out once in goal order. Enabled goals
    whose materials were read for the selected role share it; any other goal is measured against all of it.
    override: a goal record to use in place of the stored one (a sync about to store it)."""
    ctx = ctx or tool_context()
    role = core.account_key(game) if role is core.SELECTED else role
    goals = [override if override and g['id'] == override['id'] else g for g in core.goals(game)]
    sharing = [g for g in goals if g.get('enabled') and g.get('account') == role]
    book = materials.ledger(sharing)
    ids = {g['id'] for g in sharing}
    return {g['id']: materials.items_for_goal(g, ctx, book if g['id'] in ids else None) for g in goals}


def calc_block(goal: dict, role) -> str | None:
    """Why a goal's materials cannot be farmed now: no calculation, one older than the goal's targets and levels,
    or one of another game role. None when they can."""
    if goal.get('calc_error') and not goal.get('materials'):
        return goal['calc_error']
    if not goal.get('calc_at'):
        return tr('calc_pending')
    if goal.get('account') != role:
        return tr('calc_other_role')
    if goal.get('calc_stale'):
        return tr('calc_stale')
    return None


def goal_items(goal: dict, ctx: dict | None = None, items: list[dict] | None = None, role=core.SELECTED) -> list[dict]:
    """Collection items plus the stable-list allowance (issued units minus executed, never above today's gap)."""
    role = core.account_key(goal['game']) if role is core.SELECTED else role
    if items is None:
        items = items_by_goal(goal['game'], ctx, role=role).get(goal['id'], [])
    gate = calc_block(goal, role)
    result = []
    for item in items:
        entry = (goal.get('allowance') or {}).get(item['key'])
        if entry and entry.get('calc_at') == goal.get('calc_at') and item['units'] is not None:
            item['executed'] = int(entry.get('done', 0))
            item['available'] = max(0, min(item['units'], int(entry['units']) - item['executed']))
        else:
            item['executed'] = 0
            item['available'] = item['units']
        item['gate'] = gate
        item['cost'] = materials.COST.get(item['unit'])
        item['unit_label'] = materials.unit_label(item['unit'])
        item['progress'] = materials.item_progress(item)
        result.append(item)
    return result


def blocker(item: dict, weekday: int) -> str | None:
    """Why this item cannot run now; None means it can."""
    if item['done']:
        return tr('blk_done')
    if item.get('gate'):
        return item['gate']
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
    """Latest official/in-game reading of the selected role plus natural recovery; None is UNKNOWN."""
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
    return {'value': value, 'cap': cap, 'source': tr(source) if source in MESSAGES else source, 'seen': sample['at'],
            'reading': int(sample['current'])}


# ---------------------------------------------------------------- equipment continuation

def gear_queue(game: str) -> list[dict]:
    """Characters whose equipment target steers farming, in goal order, with what each would farm.

    A character is finished only when its read discs meet the target; unread or unscored discs
    are not finished, so farming continues for them within the cap."""
    stages = materials.gear_stages(game, core.settings()['paths']['onedragon'])
    owned_all = (inventory.arrange(game) or {}).get('goals', {})
    role = core.account_key(game)
    rows = []
    for goal in core.goals(game):
        target = gear.effective_target(goal)
        if not goal.get('enabled') or not target['farm']:
            continue
        if goal.get('account') != role:  # its equipment was read for another role
            rows.append({'goal_id': goal['id'], 'goal': goal['name'], 'score': None, 'target': target['score'],
                         'owned_score': None, 'done': False, 'set': None, 'stage': None, 'owned_only': False,
                         'why': tr('calc_other_role')})
            continue
        ev = gear.evaluate(goal)
        owned = owned_all.get(goal['id'])  # best arrangement of the pieces it owns (with an inventory scan)
        row = {'goal_id': goal['id'], 'goal': goal['name'], 'score': ev and ev['score'], 'target': target['score'],
               'owned_score': owned and owned['score'], 'done': bool(ev and ev['done']) or bool(owned and owned['done']),
               'set': None, 'stage': None, 'why': None}
        if owned:
            want = owned['next_set']
        else:
            want = ev['next_set'] if ev else gear.next_set([{**s, 'ok': False} for s in target['sets']])
        row['owned_only'] = row['done'] and not (ev and ev['done'])  # met by owned pieces it does not wear yet
        if row['done']:
            row['why'] = tr('gear_owned_meets') if row['owned_only'] else tr('gear_target_met')
        elif target['stage']:
            row.update(stage=target['stage'], set=want and want['name'])
        elif not want:
            row['why'] = tr('gear_unread') if ev is None else tr('gear_no_sets')
        else:
            row['set'] = want['name']
            row['stage'] = materials.stage_for_set(want, stages)
            if not row['stage']:
                row['why'] = tr('gear_no_stage' if game == 'zzz' else 'art_no_domain', set=want['name'])
        rows.append(row)
    return rows


def equipment(game: str, consumed: dict | None = None) -> dict:
    """Optional artifact / disc continuation; the cumulative cap is the authorization.

    When a character's equipment target steers farming, the first unfinished one in goal order
    decides the stage (ZZZ Area Patrol) or domain (Genshin Domain of Blessing) by the set it needs;
    while it has none, nothing is farmed for the characters after it. Otherwise the one set in Settings
    is farmed. The cap was granted for one game role and spends only that role's stamina."""
    p = core.settings()['planning']
    if game == 'genshin':
        conf, name, unit, label = p['artifact'], p['artifact'].get('domain'), 'claim20', tr('equip_artifact')
    else:
        conf, name, unit, label = p['disc'], p['disc'].get('mission'), 'disc', tr('equip_disc')
    used = int(core.get('equip_used:' + game, 0)) + int((consumed or {}).get('equip:' + game, 0))
    cap = int(conf.get('cap') or 0)
    queue = gear_queue(game)
    head = next((r for r in queue if not r['done']), None)
    pick = head if head and head['stage'] else None
    if queue:
        name = pick and pick['stage']
    result = {'enabled': bool(conf.get('enabled')), 'name': name or '', 'cap': cap, 'used': used,
              'left': max(0, cap - used), 'label': label, 'unit': unit, 'mode': 'character' if queue else 'fixed',
              'role_ok': core.allowance_role_ok(game, conf),
              'queue': queue, 'goal_id': pick and pick['goal_id'], 'goal': pick and pick['goal'], 'set': pick and pick['set']}
    if not result['enabled']:
        result['why'] = tr('equip_off', label=label)
    elif not result['role_ok']:
        result['why'] = tr('equip_other_role', label=label)
    elif queue and not pick:
        if head:  # the first unfinished character decides; the ones after it wait for it
            result['why'] = tr('gear_blocked', goal=head['goal'], why=head['why'])
        else:
            result['why'] = tr('gear_all_owned') if any(r['owned_only'] for r in queue) else tr('gear_all_met')
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
    goal = tr('gear_goal' if game == 'zzz' else 'art_goal', goal=eq['goal']) if eq.get('goal') else tr('equip_goal', label=eq['label'])
    return {'key': 'equip:' + game, 'goal_id': eq.get('goal_id'), 'goal': goal, 'game': game,
            'kind': 'domain' if game == 'genshin' else 'zzz', 'label': eq['name'], 'names': eq.get('set') or eq['label'],
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
    role = core.account_key(game)
    items = items_by_goal(game, ctx, role=role)
    for goal in core.goals(game):
        if not goal.get('enabled'):
            continue
        why = calc_block(goal, role)
        if why:
            waiting.append({'goal': goal['name'], 'label': tr('label_calc'), 'why': why})
            continue
        for item in goal_items(goal, ctx, items[goal['id']], role):
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
        if eq.get('why') and (eq['enabled'] or any(not r['done'] for r in eq['queue'])):
            # also when it is off, if a character asked for equipment: say why that does not happen
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
    """The day's slots, one per distinct time: the scheduler books each under one key (scheduler.slot_key)."""
    result = []
    for t in sorted(set(times)):
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
    return result[:days * max(1, len(set(s['times'])))]


def forecast(days: int = 3) -> dict:
    """Simulate the next batches with the same plan() rule (preview only)."""
    s = core.settings()
    slots = upcoming_slots(days)
    rows = []
    for game in s['schedule']['games']:
        consumed: dict = {}
        est = estimate(game)
        period = timedelta(minutes=RECOVERY_MINUTES[game])
        # Recovery counts from the reading itself, carrying the minutes toward the next point from slot to slot,
        # so every slot shows what estimate() says for that time.
        value, last_at, cap = (est['reading'], core.parse(est['seen']), est['cap']) if est else (None, None, DEFAULT_CAP[game])
        today = core.game_date()
        ran_today = any(any(g.get('game') == game for g in r.get('games') or [])
                        for r in core.runs(since=core.stamp(datetime.combine(today, datetime.min.time(), core.CN) + timedelta(hours=4))))
        coffee_days = {today} if ran_today else set()  # a batch of this game day already drank today's coffee
        coffee = 0  # forecast coffee inside the value: added at this slot, or still above the cap
        capped = None  # since when the value has been at or above the cap
        for slot in slots:
            full_at = None  # when natural recovery reached the cap before this slot
            full = False  # at or above the cap at this slot: recovery waits until stamina is spent below it
            if value is not None:
                if value >= cap:  # recovery stops at the cap; coffee above it stays
                    full_at = capped or last_at
                else:
                    gained = int((slot - last_at) / period)
                    if value + gained >= cap:
                        reached = last_at + period * (cap - value)
                        full_at = reached if reached < slot else None
                        value = cap
                    else:
                        value, last_at = value + gained, last_at + period * gained
                if game == 'zzz' and core.game_date(slot) not in coffee_days:
                    coffee_days.add(core.game_date(slot))
                    coffee += int(s['planning']['zzz_coffee_forecast'])
                    value += int(s['planning']['zzz_coffee_forecast'])
                full = value >= cap
            p = plan(game, slot, stamina=value, consumed=consumed)
            item = p['item']
            row = {'game': game, 'at': core.stamp(slot), 'stamina': value, 'reason': p['reason'],
                   'label': item and f"{item['goal']} · {item['label']}", 'unit_label': item and item['unit_label'],
                   'upper': item and item['upper'], 'expected': item and item['expected'], 'phase': p['phase'],
                   'goal': item and item['goal'], 'goal_id': item and item['goal_id'], 'task': item and item['label'],
                   'names': item and item['names'], 'cost': item and item['cost'], 'spend': None, 'left': value,
                   'cap': cap, 'full_at': full_at and core.stamp(full_at), 'coffee': coffee}
            if item:
                units = item['expected'] if item['expected'] is not None else 0
                consumed[item['key']] = consumed.get(item['key'], 0) + units
                if value is not None:
                    row['spend'] = units * item['cost']
                    value -= row['spend']
                    row['left'] = value
            if full and value is not None and value < cap:
                last_at = slot  # spent below the cap: the next point is a full period away
            coffee = min(coffee, value - cap) if value is not None and value > cap else 0
            capped = full_at if value is not None and value >= cap else None
            rows.append(row)
    rows.sort(key=lambda r: (r['at'], r['game']))
    return {'slots': [core.stamp(x) for x in slots], 'rows': rows, 'schedule_enabled': s['schedule']['enabled']}
