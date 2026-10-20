"""Goals: create, edit, order and synchronise with the official calculators."""
from __future__ import annotations

import logging
import threading
import uuid

from . import core, gear, materials, mihoyo
from .i18n import tr

log = logging.getLogger('gcl.goals')
SYNC_LOCK = threading.Lock()
DEFAULT_TARGET = {
    'genshin': {'level': 90, 'weapon': 90, 'attack': 1, 'skill': 9, 'burst': 9},
    'zzz': {'level': 60, 'weapon': 60, 'attack': 12, 'special': 12, 'chain': 12, 'dodge': 9, 'assist': 9, 'core': 6},
}
LIMITS = {
    'genshin': {'level': (1, 90), 'weapon': (1, 90), 'attack': (1, 10), 'skill': (1, 10), 'burst': (1, 10)},
    'zzz': {'level': (1, 60), 'weapon': (0, 60), 'attack': (1, 12), 'special': (1, 12), 'chain': (1, 12),
            'dodge': (1, 12), 'assist': (1, 12), 'core': (0, 6), 'promotion': (0, 6)},
}
CATEGORIES = ['level', 'talents', 'weapon']


def _levels(game: str, value: dict | None) -> dict:
    result = {}
    for key, raw in (value or {}).items():
        if key not in LIMITS[game] or raw in (None, ''):
            continue
        number = int(raw)
        low, high = LIMITS[game][key]
        if not low <= number <= high:
            raise ValueError(tr('out_of_range', key=key, low=low, high=high))
        result[key] = number
    return result


def create(game: str, character_id: str, name: str, target: dict | None = None, current: dict | None = None) -> dict:
    if game not in ('genshin', 'zzz'):
        raise ValueError(tr('invalid_game'))
    if any(g['game'] == game and g['character_id'] == str(character_id) for g in core.goals()):
        raise ValueError(tr('goal_exists'))
    same = core.goals(game)
    goal = {'id': uuid.uuid4().hex, 'game': game, 'character_id': str(character_id), 'name': name,
            'enabled': True, 'position': max([g.get('position', 0) for g in same], default=0) + 1,
            'created': core.stamp(), 'current': _levels(game, current),
            'target': {**DEFAULT_TARGET[game], **_levels(game, target)},
            'category_order': list(CATEGORIES), 'paused': [], 'materials': [], 'allowance': {}}
    core.save_goal(goal)
    queue_sync(goal['id'])
    return goal


def update(goal_id: str, patch: dict) -> dict:
    goal = core.goal(goal_id)
    if not goal:
        raise ValueError(tr('goal_missing'))
    recalc = False
    if 'enabled' in patch:
        goal['enabled'] = bool(patch['enabled'])
    if 'name' in patch and str(patch['name']).strip():
        goal['name'] = str(patch['name']).strip()[:30]
    for key in ('target', 'current'):
        if key in patch:
            goal[key] = {**goal.get(key, {}), **_levels(goal['game'], patch[key])}
            recalc = True
    if 'weapon_id' in patch:
        goal['weapon_id'] = str(patch['weapon_id'] or '') or None
        recalc = True
    if 'category_order' in patch:
        order = [c for c in patch['category_order'] if c in CATEGORIES]
        goal['category_order'] = order + [c for c in CATEGORIES if c not in order]
    if 'paused' in patch:
        goal['paused'] = [str(k) for k in patch['paused']][:100]
    if 'gear_target' in patch:  # None returns the target to the followed build's defaults
        goal['gear_target'] = (gear.clean_target(patch['gear_target'], goal['game'], gear.build_defaults(goal)['main'])
                               if patch['gear_target'] else None)
    core.save_goal(goal)
    if recalc:
        queue_sync(goal_id, observe=False)
    return goal


def remove(goal_id: str) -> None:
    core.delete_goal(goal_id)


def set_order(game: str, ids: list[str]) -> None:
    rows = {g['id']: g for g in core.goals(game)}
    ordered = [i for i in ids if i in rows] + [i for i in rows if i not in ids]
    for position, gid in enumerate(ordered, 1):
        goal = rows[gid]
        if goal.get('position') != position:
            goal['position'] = position
            core.save_goal(goal)


def queue_sync(goal_id: str, observe: bool = True, delay: float = 0) -> None:
    def worker():
        try:
            sync(goal_id, observe=observe)
        except Exception:
            log.exception('Goal sync failed')
    timer = threading.Timer(delay, worker)
    timer.daemon = True
    timer.start()


def sync(goal_id: str, observe: bool = True, force: bool = False) -> dict:
    """Read the goal's character and calculate its materials. force: the user asked for it (mihoyo.observe)."""
    with SYNC_LOCK:
        goal = core.goal(goal_id)
        if not goal:
            raise ValueError(tr('goal_missing'))
        goal['sync_at'] = core.stamp()
        if observe:
            try:
                seen = mihoyo.observe(goal, force=force)
                goal['current'] = {**goal.get('current', {}), **seen['current']}
                if seen.get('weapon_id'):
                    goal['weapon_id'], goal['weapon_name'] = seen['weapon_id'], seen.get('weapon_name', '')
                if seen.get('talent_groups'):  # lets the calculation skip a second read
                    goal['talent_groups'] = seen['talent_groups']
                goal['observe_at'], goal['observe_error'] = core.stamp(), None
                if 'gear' in seen:
                    goal['gear'] = {**seen['gear'], 'at': goal['observe_at']}
                goal['gear_error'] = seen.get('gear_error')
            except Exception as exc:
                goal['observe_error'] = mihoyo.describe_error(exc)
        # A target below the current level means nothing to farm, not a negative need.
        goal['target'] = {k: max(v, goal['current'].get(k, v)) if k != 'promotion' else v
                          for k, v in goal.get('target', {}).items()}
        try:
            rows = mihoyo.calculate(goal)
            was_done = bool(goal.get('materials')) and all(m.get('remaining') == 0 for m in goal['materials'])
            goal['materials'], goal['calc_at'], goal['calc_error'] = rows, core.stamp(), None
            refresh_allowance(goal)
            done = all(m.get('remaining') == 0 for m in rows)
            if done and not was_done and goal.get('enabled'):
                from . import notify
                notify.event('goal_done', tr('goal_done_title', name=goal['name']), [tr('goal_done_body')])
        except Exception as exc:
            goal['calc_error'] = mihoyo.describe_error(exc)
        core.save_goal(goal)
        return goal


def refresh_allowance(goal: dict) -> None:
    """A new calculation starts a new stable list; executed units are counted against it."""
    from .planner import tool_context
    old = goal.get('allowance') or {}
    allowance = {}
    for item in materials.items_for_goal(goal, tool_context()):
        if item['units'] is None:
            continue
        prev = old.get(item['key'])
        # Official inventory not updated yet (gap did not shrink): keep what was already executed.
        done = int(prev.get('done', 0)) if prev and item['units'] >= int(prev.get('units', 0)) else 0
        allowance[item['key']] = {'calc_at': goal['calc_at'], 'units': item['units'], 'done': done}
    goal['allowance'] = allowance


def record_done(item_key: str, units: int) -> None:
    goal_id = item_key.split(':', 1)[0]
    goal = core.goal(goal_id)
    if not goal or units <= 0:
        return
    entry = goal.setdefault('allowance', {}).get(item_key)
    if entry:
        entry['done'] = int(entry.get('done', 0)) + int(units)
        core.save_goal(goal)


def record_gear_runs(goal_id: str, runs: int) -> None:
    """Equipment runs farmed for this character (shown on its card; the cap itself is per game)."""
    goal = core.goal(goal_id)
    if goal and runs > 0:
        goal['gear_runs'] = int(goal.get('gear_runs', 0)) + int(runs)
        core.save_goal(goal)


def due_for_sync(hours: float) -> list[dict]:
    result = []
    for goal in core.goals():
        if not goal.get('enabled'):
            continue
        last = core.parse(goal.get('sync_at'))
        if last is None or (core.now() - last).total_seconds() >= hours * 3600:
            result.append(goal)
    return result
