"""Equipment inventory: every Drive Disc / Artifact the account owns, read by an in-game scanner.

Miyoushe shows only equipped pieces. With a scan of the whole inventory, each character whose
equipment target steers farming gets its best arrangement of the pieces it may use (unequipped
ones and its own, never another character's), in goal order, each character taking its pieces off
the table. Farming for a character stops once that arrangement meets its target: the user equips
the pieces in the game. The app never equips, locks or salvages; pieces no target uses are only
listed.
"""
from __future__ import annotations

import itertools

from . import core, gear

SPARE_SCORE = 30   # an unused, unlocked, unequipped piece below this score for every farming character is spare
_CACHE: dict = {}


# ---------------------------------------------------------------- storage

def save(game: str, pieces: list[dict], source: str, located: bool = True) -> dict:
    """Store a scan; pieces use the observation's format plus ``location`` (equipped on someone) and ``lock``.
    ``located`` is False when the scanner does not report who wears a piece or whether it is locked."""
    for i, p in enumerate(pieces):
        p['uid'] = str(i)
    value = {'at': core.stamp(), 'source': source, 'pieces': pieces, 'located': located}
    core.put('inventory:' + game, value)
    core.put('inventory_at:' + game, value['at'])
    _CACHE.pop(game, None)
    return value


def load(game: str) -> dict | None:
    """The last scan (cached while its time stamp is unchanged)."""
    at = core.get('inventory_at:' + game)
    if not at:
        return None
    cached = _CACHE.get(game)
    if not cached or cached['at'] != at:
        cached = {'at': at, 'value': core.get('inventory:' + game), 'arranged': None}
        _CACHE[game] = cached
    return cached['value']


def summary(game: str) -> dict | None:
    inv = load(game)
    if not inv:
        return None
    return {'at': inv['at'], 'source': inv['source'], 'count': len(inv['pieces'])}


# ---------------------------------------------------------------- matching

def _signature(p: dict) -> tuple:
    """What identifies a physical piece across the scan and Miyoushe's equipped list."""
    subs = []
    for s in p.get('subs', []):
        n = s.get('number')
        subs.append((s['id'], round(n, 1) if n is not None else ('rolls', s.get('level'))))
    return p['slot'], p['set_id'], p.get('level'), (p.get('main') or {}).get('id'), tuple(sorted(subs, key=str))


def available_to(goal: dict, piece: dict, worn_by_others: set | None = None) -> bool:
    """Unequipped pieces, and the ones this character wears now; never a piece another character wears.
    Without wearers in the scan, ``worn_by_others`` (what the other goal characters wear, from Miyoushe)
    keeps their pieces out; a piece of a character that is not a goal cannot be told apart."""
    if worn_by_others is not None:
        return _signature(piece) not in worn_by_others
    if not piece.get('location'):
        return True
    own = (goal.get('gear') or {}).get('discs') or []
    return any(_signature(piece) == _signature(e) for e in own)


# ---------------------------------------------------------------- arrangement

def best(goal: dict, pool: list[dict]) -> dict | None:
    """The arrangement of pool pieces that meets most of the target's set counts, then scores highest.

    Per slot only the best piece of each target set (and the best of any other set) can be part of the
    best arrangement, so the search runs over set choices per slot: a few thousand combinations."""
    game = goal['game']
    rules = gear.RULES[game]
    w, _ = gear.weights(goal)
    if not w:
        return None
    target = gear.effective_target(goal)
    set_ids = [s['id'] for s in target['sets']]
    top: dict[tuple, tuple[float, dict]] = {}
    for p in pool:
        slot = p['slot']
        allowed = target['main'].get(str(slot)) or []
        main = (p.get('main') or {}).get('id')
        if slot in rules['configurable'] and allowed and \
                gear.family(game, main) not in {gear.family(game, a) for a in allowed}:
            continue
        score = gear.piece_score(p, w, game)
        if score is None:
            continue
        kind = p['set_id'] if p['set_id'] in set_ids else 'other'
        if score > top.get((slot, kind), (-1.0, None))[0]:
            top[(slot, kind)] = (score, p)
    slots = list(rules['mains'])
    choices = [[k for k in set_ids + ['other'] if (slot, k) in top] or [None] for slot in slots]
    best_key, best_combo = None, None
    for combo in itertools.product(*choices):
        met = sum(min(sum(1 for k in combo if k == s['id']), s['count']) for s in target['sets'])
        total = sum(top[(slot, k)][0] for slot, k in zip(slots, combo) if k is not None)
        if best_key is None or (met, total) > best_key:
            best_key, best_combo = (met, total), combo
    picks = {slot: top[(slot, k)][1] for slot, k in zip(slots, best_combo) if k is not None}
    counts: dict[int, int] = {}
    for p in picks.values():
        counts[p['set_id']] = counts.get(p['set_id'], 0) + 1
    sets = [{**s, 'have': counts.get(s['id'], 0), 'ok': counts.get(s['id'], 0) >= s['count']} for s in target['sets']]
    score = round(sum(top[(slot, k)][0] for slot, k in zip(slots, best_combo) if k is not None) / len(slots), 1)
    checks = {'filled': len(picks) == len(slots), 'sets': all(s['ok'] for s in sets), 'main': True,
              'score': score >= target['score']}
    own = (goal.get('gear') or {}).get('discs') or []
    changes = []
    for slot, p in sorted(picks.items()):
        worn = next((e for e in own if e['slot'] == slot), None)
        if worn is None or _signature(worn) != _signature(p):
            changes.append({'slot': slot, 'uid': p['uid'], 'set': p['set'], 'set_id': p['set_id'],
                            'main': p.get('main'), 'level': p.get('level'), 'rarity': p.get('rarity'),
                            'score': round(gear.piece_score(p, w, game) or 0, 1),
                            'was': None if worn is None else gear.piece_score(worn, w, game)})
    return {'picks': {str(k): v['uid'] for k, v in picks.items()}, 'score': score, 'sets': sets, 'checks': checks,
            'done': all(checks.values()), 'next_set': gear.next_set(sets), 'changes': changes}


def arrange(game: str) -> dict | None:
    """Best arrangements in goal order for the characters that steer farming, plus the spare pieces.
    Cached until the scan or any goal of the game changes."""
    inv = load(game)
    if not inv:
        return None
    goals = [g for g in core.goals(game) if g.get('enabled') and gear.effective_target(g)['farm']]
    key = tuple((g['id'], g.get('updated')) for g in goals)
    cached = _CACHE[game]
    if cached['arranged'] and cached['arranged'][0] == key:
        return cached['arranged'][1]
    located = inv.get('located', True)
    worn = {g['id']: {_signature(d) for d in (g.get('gear') or {}).get('discs') or []} for g in core.goals(game)}
    used: set[str] = set()
    result = {}
    for goal in goals:
        others = None if located else set().union(*(v for k, v in worn.items() if k != goal['id']))
        pool = [p for p in inv['pieces'] if p['uid'] not in used and available_to(goal, p, others)]
        found = best(goal, pool)
        if found:
            used.update(found['picks'].values())
            result[goal['id']] = found
    # spare only with wearers and locks known, and measured against some character's target
    weights = [(g, w) for g in goals for w in [gear.weights(g)[0]] if w] if located else []
    spare = []
    for p in inv['pieces'] if weights else []:  # spare only measured against some character's target
        if p['uid'] in used or p.get('location') or p.get('lock'):
            continue
        scores = [gear.piece_score(p, w, game) for _, w in weights]
        if all(s is not None and s < SPARE_SCORE for s in scores):
            spare.append(p['uid'])
    value = {'at': inv['at'], 'goals': result, 'spare': spare, 'count': len(inv['pieces']), 'located': located}
    cached['arranged'] = (key, value)
    return value
