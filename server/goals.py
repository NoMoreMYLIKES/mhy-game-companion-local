"""Goals: create, edit, order and synchronise with the official calculators."""
from __future__ import annotations

import copy
import logging
import threading
import uuid

from . import auth, core, gear, mihoyo
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
RESYNC_OTHER_ROLE = 900  # seconds between syncs of a goal whose data belongs to a role no longer selected


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


def basis(goal: dict) -> dict:
    """What a material calculation answers: once any of it changes, the materials answer an old question."""
    return {'current': goal.get('current') or {}, 'target': goal.get('target') or {}, 'weapon_id': goal.get('weapon_id')}


def create(game: str, character_id: str, name: str, target: dict | None = None, current: dict | None = None) -> dict:
    if game not in ('genshin', 'zzz'):
        raise ValueError(tr('invalid_game'))
    with core.LOCK:
        if any(g['game'] == game and g['character_id'] == str(character_id) for g in core.goals()):
            raise ValueError(tr('goal_exists'))
        same = core.goals(game)
        goal = {'id': uuid.uuid4().hex, 'game': game, 'character_id': str(character_id), 'name': name,
                'enabled': True, 'position': max([g.get('position', 0) for g in same], default=0) + 1,
                'created': core.stamp(), 'current': _levels(game, current),
                'target': {**DEFAULT_TARGET[game], **_levels(game, target)},
                'category_order': list(CATEGORIES), 'paused': [], 'materials': [], 'allowance': {},
                'account': core.account_key(game)}  # levels entered now are the selected role's
        core.save_goal(goal)
    queue_sync(goal['id'])
    return goal


def update(goal_id: str, patch: dict) -> dict:
    with core.LOCK:  # a sync merges its answers into the newest record under the same lock
        goal = core.goal(goal_id)
        if not goal:
            raise ValueError(tr('goal_missing'))
        before = copy.deepcopy(basis(goal))
        if 'enabled' in patch:
            goal['enabled'] = bool(patch['enabled'])
        if 'name' in patch and str(patch['name']).strip():
            goal['name'] = str(patch['name']).strip()[:30]
        for key in ('target', 'current'):
            if key in patch:
                goal[key] = {**goal.get(key, {}), **_levels(goal['game'], patch[key])}
        if 'weapon_id' in patch:
            goal['weapon_id'] = str(patch['weapon_id'] or '') or None
        if 'category_order' in patch:
            order = [c for c in patch['category_order'] if c in CATEGORIES]
            goal['category_order'] = order + [c for c in CATEGORIES if c not in order]
        if 'paused' in patch:
            goal['paused'] = [str(k) for k in patch['paused']][:100]
        if 'gear_target' in patch:  # None returns the target to the followed build's defaults
            goal['gear_target'] = (gear.clean_target(patch['gear_target'], goal['game'], gear.build_defaults(goal)['main'])
                                   if patch['gear_target'] else None)
        recalc = basis(goal) != before
        if recalc:
            goal['calc_stale'] = True  # nothing of the old answer runs until the new calculation lands
        core.save_goal(goal)
    if recalc:
        queue_sync(goal_id, observe=False)
    return goal


def remove(goal_id: str) -> None:
    core.delete_goal(goal_id)


def set_order(game: str, ids: list[str]) -> None:
    with core.LOCK:
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


def _observed(goal: dict, seen: dict, asked: dict | None = None) -> None:
    """Put an official reading into a goal. asked: the record the reading was requested for; current levels or a
    W-Engine the user changed since then are the user's and stay."""
    before = copy.deepcopy(basis(goal))
    if asked is None or goal.get('current') == asked.get('current'):
        goal['current'] = {**goal.get('current', {}), **seen['current']}
    if seen.get('weapon_id') and (asked is None or goal.get('weapon_id') == asked.get('weapon_id')):
        goal['weapon_id'], goal['weapon_name'] = seen['weapon_id'], seen.get('weapon_name', '')
    if seen.get('talent_groups'):  # lets the calculation skip a second read
        goal['talent_groups'] = seen['talent_groups']
    goal['observe_at'], goal['observe_error'] = core.stamp(), None
    if 'gear' in seen:
        goal['gear'] = {**seen['gear'], 'at': goal['observe_at']}
    goal['gear_error'] = seen.get('gear_error')
    if basis(goal) != before:
        goal['calc_stale'] = True


def sync(goal_id: str, observe: bool = True, force: bool = False) -> dict | None:
    """Read the goal's character and calculate its materials. force: the user asked for it (mihoyo.observe).

    The official answers take a while; meanwhile the goal may be edited, canceled or deleted, or another role
    selected. The answers are merged into the record as it is then: a deleted goal stays deleted, the user's edits
    win, a calculation for inputs that changed meanwhile is dropped, and so is everything read for a role that is
    no longer selected. Returns None when the goal was deleted meanwhile."""
    with SYNC_LOCK:
        goal = core.goal(goal_id)
        if not goal:
            raise ValueError(tr('goal_missing'))
        game = goal['game']
        login, role = auth.binding(game), core.account_key(game)
        seen, errors = None, {}
        if observe:
            try:
                seen = mihoyo.observe(goal, force=force)
            except Exception as exc:
                errors['observe_error'] = mihoyo.describe_error(exc)
        asked = copy.deepcopy(goal)  # what is calculated
        if seen is not None:
            _observed(asked, seen)
        rows = None
        if seen is None and goal.get('account') != role:
            errors['calc_error'] = tr('calc_needs_reading')  # its levels were read for another role
        else:
            try:
                rows = mihoyo.calculate(asked)
            except Exception as exc:
                errors['calc_error'] = mihoyo.describe_error(exc)
        with core.LOCK:
            fresh = core.goal(goal_id)
            if fresh is None:
                return None
            fresh['sync_at'] = core.stamp()
            if login != auth.binding(game):
                fresh['calc_error'] = tr('login_changed')
                if observe:
                    fresh['observe_error'] = tr('login_changed')
                core.save_goal(fresh)
                return fresh
            if seen is not None:
                _observed(fresh, seen, goal)
                fresh['account'] = role
            elif observe:
                fresh['observe_error'] = errors['observe_error']
            if rows is None:
                fresh['calc_error'] = errors['calc_error']
            elif basis(fresh) == basis(asked):
                was_done = bool(fresh.get('materials')) and all(m.get('remaining') == 0 for m in fresh['materials'])
                fresh['materials'], fresh['calc_at'], fresh['calc_error'] = rows, core.stamp(), None
                fresh['calc_stale'], fresh['account'] = False, role
                refresh_allowance(fresh)
                done = all(m.get('remaining') == 0 for m in rows)
                if done and not was_done and fresh.get('enabled'):
                    from . import notify
                    notify.event('goal_done', tr('goal_done_title', name=fresh['name']), [tr('goal_done_body')])
            # else the goal changed while this was calculated; the edit queued its own calculation
            core.save_goal(fresh)
        return fresh


def refresh_allowance(goal: dict) -> None:
    """A new calculation starts a new stable list; executed units are counted against it."""
    from .planner import items_by_goal
    old = goal.get('allowance') or {}
    allowance = {}
    for item in items_by_goal(goal['game'], override=goal).get(goal['id'], []):
        if item['units'] is None:
            continue
        prev = old.get(item['key'])
        # Official inventory not updated yet (gap did not shrink): keep what was already executed.
        done = int(prev.get('done', 0)) if prev and item['units'] >= int(prev.get('units', 0)) else 0
        allowance[item['key']] = {'calc_at': goal['calc_at'], 'units': item['units'], 'done': done}
    goal['allowance'] = allowance


def record_done(item_key: str, units: int) -> None:
    goal_id = item_key.split(':', 1)[0]
    with core.LOCK:
        goal = core.goal(goal_id)
        if not goal or units <= 0:
            return
        entry = goal.setdefault('allowance', {}).get(item_key)
        if entry:
            entry['done'] = int(entry.get('done', 0)) + int(units)
            core.save_goal(goal)


def record_gear_runs(goal_id: str, runs: int) -> None:
    """Equipment battles fought for this character (shown on its card; the cap itself counts reward units)."""
    with core.LOCK:
        goal = core.goal(goal_id)
        if goal and runs > 0:
            goal['gear_runs'] = int(goal.get('gear_runs', 0)) + int(runs)
            core.save_goal(goal)


def due_for_sync(hours: float) -> list[dict]:
    """Enabled goals to sync, the longest unsynced first: every ``hours``, and soon after another role is
    selected, since their levels and materials belong to the role read before."""
    roles = {game: core.account_key(game) for game in ('genshin', 'zzz')}
    result = []
    for goal in core.goals():
        if not goal.get('enabled'):
            continue
        last = core.parse(goal.get('sync_at'))
        age = None if last is None else (core.now() - last).total_seconds()
        role = roles.get(goal['game'])
        other = role is not None and goal.get('account') != role
        if age is None or age >= hours * 3600 or (other and age >= RESYNC_OTHER_ROLE):
            result.append(goal)
    return sorted(result, key=lambda g: g.get('sync_at') or '')
