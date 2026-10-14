"""Equipment: read, score and target a character's equipped Drive Discs (ZZZ) or Artifacts (Genshin).

ZZZ: the observation comes from the official upgrade-guide response that goal sync already reads
(mihoyo.observe): the equipped discs, the agent's base stats and the build the account follows
on Miyoushe (its own plan or the recommended one). Genshin: Miyoushe's character detail, requested
for the goal's character only: the equipped artifacts, base stats and the recommended (or the
account's own) sands / goblet / circlet main stats and substats.

A disc's score measures the substat rolls already on it, weighted per character, against the
best rolls a disc in that slot could hold: four different substats plus five upgrades of the
most valuable one. Nothing here predicts future upgrades, and the main stat earns no points
(it is a separate check). Unknown stays None, never 0.
"""
from __future__ import annotations

import re

from .i18n import tr

# Per game: the substats a piece can roll with the size of one top-rarity roll ("step"; percentage
# points for percent stats), the main stats each slot can carry, and the % stat behind each flat stat.
# Lower rarities roll smaller steps, so their rolls count as fractions. Genshin rolls vary between
# 70 % and 100 % of the step, so a Genshin roll counts its share of a maximum roll.
RULES = {
    'zzz': {  # Drive Discs: six slots, S rank up to level 15 (five upgrades)
        'slots': 6, 'upgrades': 5, 'configurable': (4, 5, 6),
        'step': {11103: 112, 11102: 3.0, 12103: 19, 12102: 3.0, 13103: 15, 13102: 4.8,
                 20103: 2.4, 21103: 4.8, 23203: 9, 31203: 9},  # HP, HP%, ATK, ATK%, DEF, DEF%, CR, CD, PEN, AP
        'percent': {11102, 12102, 13102, 20103, 21103},
        'flat_of': {11102: (11103, 'hp'), 12102: (12103, 'atk'), 13102: (13103, 'def')},
        'mains': {1: [11103], 2: [12103], 3: [13103],
                  4: [11102, 12102, 13102, 20103, 21103, 31203],
                  5: [11102, 12102, 13102, 23103, 31503, 31603, 31703, 31803, 31903, 32303],
                  6: [11102, 12102, 13102, 30502, 31402, 12202]},
        'set_pieces': 6,
    },
    'genshin': {  # Artifacts: flower, plume, sands, goblet, circlet; 5-star up to level 20 (five upgrades)
        'slots': 5, 'upgrades': 5, 'configurable': (3, 4, 5),
        'step': {2: 298.75, 3: 5.83, 5: 19.45, 6: 5.83, 8: 23.15, 9: 7.29,
                 20: 3.89, 22: 7.77, 23: 6.48, 28: 23.31},  # HP, HP%, ATK, ATK%, DEF, DEF%, CR, CD, ER, EM
        'percent': {3, 6, 9, 20, 22, 23},
        'flat_of': {3: (2, 'hp'), 6: (5, 'atk'), 9: (8, 'def')},
        'mains': {1: [2], 2: [5], 3: [3, 6, 9, 23, 28],
                  4: [3, 6, 9, 28, 30, 40, 41, 42, 43, 44, 45, 46],
                  5: [3, 6, 9, 28, 20, 22, 26]},
        'set_pieces': 5,
    },
}
DEFAULT_SCORE = 50     # whole-set target; an average fully upgraded top-rarity piece lands near 40
NUMBER = re.compile(r'-?\d+(?:\.\d+)?')


def number(text) -> float | None:
    match = NUMBER.search(str(text or '').replace(',', ''))
    return float(match.group()) if match else None


# ---------------------------------------------------------------- observation

def _prop(p) -> dict:
    value = str(getattr(p, 'value', '') or '')
    return {'id': int(p.type), 'name': str(getattr(p, 'name', '')), 'value': value, 'number': number(value),
            'percent': value.strip().endswith('%'), 'level': getattr(p, 'level', None), 'valid': getattr(p, 'valid', None)}


def observe_zzz(guide) -> dict:
    """Normalize the upgrade-guide response: equipped discs, base stats and the followed build."""
    discs = []
    for d in getattr(guide, 'discs', None) or []:
        mains = list(getattr(d, 'main_properties', None) or [])
        suit = d.set_effect
        discs.append({'slot': int(d.position), 'level': int(d.level), 'rarity': str(d.rarity),
                      'set_id': int(suit.id), 'set': str(suit.name), 'icon': getattr(suit, 'icon', '') or getattr(d, 'icon', ''),
                      'main': _prop(mains[0]) if mains else None,
                      'subs': [_prop(p) for p in getattr(d, 'properties', None) or []]})
    base = {}
    for p in getattr(guide.avatar, 'properties', None) or []:  # agent stats 1, 2, 3: HP, ATK, DEF
        key = {1: 'hp', 2: 'atk', 3: 'def'}.get(int(p.type))
        if key:
            base[key] = number(getattr(p, 'value', None))
    plan = None
    detail = getattr(getattr(guide, 'plan', None), 'detail', None)
    rec = getattr(detail, 'discs', None)
    if rec is not None:
        plan = {'name': str(getattr(guide.plan, 'name', '')), 'mine': bool(getattr(guide, 'from_my_plan', False)),
                'sets': [{'id': int(s.id), 'name': str(s.name), 'icon': getattr(s, 'icon', ''), 'count': int(getattr(s, 'count', 0) or 0)}
                         for s in getattr(rec, 'sets', None) or []],
                'set_kind': getattr(rec, 'set_kind', None),
                'main': {str(slot): [int(p.type) for p in getattr(rec, f'slot_{slot}_main_stats', None) or []] for slot in (4, 5, 6)},
                'subs': [int(p.type) for p in getattr(rec, 'sub_stats', None) or []],
                'names': {str(int(p.type)): str(getattr(p, 'name', '')) for p in
                          [*(getattr(rec, 'sub_stats', None) or [])] + [q for slot in (4, 5, 6) for q in
                                                                       getattr(rec, f'slot_{slot}_main_stats', None) or []]}}
    return {'discs': discs, 'base': base, 'plan': plan}


def _raw_prop(p: dict, names: dict) -> dict:
    """A Genshin artifact stat from the raw character detail: ``times`` counts upgrades into it."""
    pid = int(p.get('property_type') or (p.get('info') or {}).get('property_type') or 0)
    value = str(p.get('value') or '')
    times = p.get('times')
    return {'id': pid, 'name': str((names.get(str(pid)) or {}).get('name') or ''), 'value': value, 'number': number(value),
            'percent': value.strip().endswith('%'), 'level': times + 1 if type(times) is int and times >= 0 else None,
            'valid': None}


def observe_genshin(data: dict, cid: int) -> dict:
    """Normalize Miyoushe's character detail (raw) for one character: artifacts, base stats, recommended stats."""
    row = next((c for c in data.get('list') or [] if int((c.get('base') or c).get('id') or 0) == int(cid)), None)
    if row is None:
        raise ValueError(tr('char_not_owned'))
    names = data.get('property_map') or {}
    pieces = []
    for r in row.get('relics') or []:
        suit = r.get('set') or {}
        pieces.append({'slot': int(r['pos']), 'level': int(r.get('level') or 0), 'rarity': str(r.get('rarity') or ''),
                       'set_id': int(suit.get('id') or 0), 'set': str(suit.get('name') or ''), 'icon': r.get('icon') or '',
                       'main': _raw_prop(r['main_property'], names) if r.get('main_property') else None,
                       'subs': [_raw_prop(p, names) for p in r.get('sub_property_list') or []]})
    base = {}
    for p in row.get('base_properties') or []:  # 2000, 2001, 2002: HP, ATK, DEF; "base" is character + weapon
        key = {2000: 'hp', 2001: 'atk', 2002: 'def'}.get(int(p.get('property_type') or 0))
        if key:
            base[key] = number(p.get('base'))
    plan = None
    rec = row.get('recommend_relic_property') or {}
    own, given = rec.get('custom_properties') or {}, rec.get('recommend_properties') or {}
    keys = ('sand_main_property_list', 'goblet_main_property_list', 'circlet_main_property_list', 'sub_property_list')
    mine = any(own.get(k) for k in keys)
    props = own if mine else given
    if any(props.get(k) for k in keys):
        ids = lambda k: [int(i) for i in props.get(k) or []]
        plan = {'name': '', 'mine': mine, 'sets': [], 'set_kind': None,
                'main': {'3': ids(keys[0]), '4': ids(keys[1]), '5': ids(keys[2])}, 'subs': ids(keys[3]),
                'names': {str(k): str(v.get('name') or '') for k, v in names.items() if isinstance(v, dict)}}
    return {'discs': pieces, 'base': base, 'plan': plan}


def icons(gear: dict, game: str = 'zzz') -> dict:
    """Image URL per set key (ZZZ: the set's icon; Genshin: one of its artifacts), for the local image cache."""
    kind = 'disc' if game == 'zzz' else 'artifact'
    found = {}
    for d in gear.get('discs', []):
        found.setdefault(f"{game}/{kind}/{d['set_id']}", d.get('icon'))
    for s in (gear.get('plan') or {}).get('sets', []):
        found.setdefault(f"{game}/{kind}/{s['id']}", s.get('icon'))
    return found


# ---------------------------------------------------------------- weights

def family(game: str, pid: int) -> int:
    """Miyoushe builds name a stat, not its variant: ATK may come as flat ATK (12103) for slot 5
    or 6, where only ATK% (12102) exists. A flat HP/ATK/DEF stat and its % stat are one family, keyed by the %."""
    for pct, (flat, _) in RULES[game]['flat_of'].items():
        if pid in (pct, flat):
            return pct
    return pid


def legal_main(game: str, slot, pid: int) -> int:
    """The variant of a recommended main stat that the slot can carry (flat ATK on slot 5 → ATK%)."""
    legal = RULES[game]['mains'].get(int(slot), [])
    if pid in legal:
        return pid
    return next((m for m in legal if family(game, m) == family(game, pid)), pid)


def official_weights(gear: dict, game: str) -> dict[int, float] | None:
    """1 for each substat the followed build recommends, 0 otherwise. The build names stat families, so flat
    HP/ATK/DEF count as their share of the % roll on the base stat, whichever variant the build listed."""
    rules = RULES[game]
    families = {family(game, i) for i in ((gear.get('plan') or {}).get('subs') or []) if i in rules['step']}
    if not families:
        return None
    flats = {flat for flat, _ in rules['flat_of'].values()}
    return derive_flat({i: (1.0 if family(game, i) in families and i not in flats else 0.0) for i in rules['step']},
                       gear, game)


def derive_flat(weights: dict[int, float], gear: dict, game: str) -> dict[int, float]:
    """A flat roll is worth its share of the % roll on the character's base stat (ZZZ base ATK 900: 19 / 27 of an ATK% roll)."""
    rules = RULES[game]
    result = dict(weights)
    base = (gear or {}).get('base') or {}
    for pct, (flat, stat) in rules['flat_of'].items():
        if not result.get(pct):
            continue
        value = base.get(stat)
        if value and value > 0:
            result[flat] = round(min(1.0, rules['step'][flat] * 100 / (rules['step'][pct] * value) * result[pct]), 2)
    return result


def weights(goal: dict) -> tuple[dict[int, float] | None, str]:
    """The weights in force and where they come from: 'custom', 'official' or 'none'."""
    step = RULES[goal['game']]['step']
    custom = ((goal.get('gear_target') or {}).get('weights'))
    if custom:
        return {int(k): float(v) for k, v in custom.items() if int(k) in step}, 'custom'
    found = official_weights(goal.get('gear') or {}, goal['game'])
    return (found, 'official') if found else (None, 'none')


def clean_weights(raw, game: str) -> dict[str, float] | None:
    """Validate weights sent by the dashboard: all ten substats, each 0–1, not all 0."""
    if raw in (None, {}):
        return None
    if not isinstance(raw, dict) or {int(k) for k in raw} != set(RULES[game]['step']):
        raise ValueError(tr('gear_weights_incomplete'))
    result = {}
    for k, v in raw.items():
        value = float(v)
        if not 0 <= value <= 1:
            raise ValueError(tr('gear_weight_range'))
        result[str(int(k))] = round(value, 2)
    if not any(result.values()):
        raise ValueError(tr('gear_weights_zero'))
    return result


# ---------------------------------------------------------------- scores

def rolls(sub: dict, game: str) -> float | None:
    """The substat's value in top-rarity rolls (2.0 for an S disc rolled twice; fractions on A/B discs
    and for Genshin rolls below the maximum)."""
    rules = RULES[game]
    step = rules['step'].get(sub['id'])
    if step is None or sub.get('number') is None or sub.get('percent') != (sub['id'] in rules['percent']):
        return None
    return sub['number'] / step


def shown_rolls(sub: dict, game: str) -> float | None:
    """Rolls as the game counts them: the API's count (initial roll included), else the top-rarity equivalent."""
    level = sub.get('level')
    if type(level) is int and level > 0:
        return level
    r = rolls(sub, game)
    return None if r is None else round(r, 2)


def piece_score(piece: dict, w: dict[int, float], game: str) -> float | None:
    """0–100: the piece's weighted rolls against four different weighted substats plus five upgrades of
    the best one, among those its main stat allows."""
    main = (piece.get('main') or {}).get('id')
    ids = [s['id'] for s in piece.get('subs', [])]
    if main in ids or len(set(ids)) != len(ids) or len(ids) > 4:  # impossible on a real piece: bad data
        return None
    legal = sorted((v for k, v in w.items() if k != main and v > 0), reverse=True)
    if not legal:
        return None
    best = sum(legal[:4]) + RULES[game]['upgrades'] * legal[0]
    got = 0.0
    for sub in piece.get('subs', []):
        r = rolls(sub, game)
        if r is None:
            if w.get(sub['id']):  # a counted substat we cannot read: no honest score
                return None
            continue
        got += r * w.get(sub['id'], 0)
    return round(min(100.0, 100 * got / best), 1)


def evaluate(goal: dict) -> dict | None:
    """Scores, target checks and the next set to farm; None when the discs were never read."""
    gear = goal.get('gear')
    if not gear:
        return None
    game = goal['game']
    rules = RULES[game]
    w, source = weights(goal)
    target = effective_target(goal)
    by_slot = {d['slot']: d for d in gear.get('discs', []) if d.get('slot') in rules['mains']}
    slots = []
    for slot in rules['mains']:
        d = by_slot.get(slot)
        score = piece_score(d, w, game) if d and w else None
        allowed = target['main'].get(str(slot)) or []
        # an empty slot fails the "filled" check, not the main-stat check
        main_ok = None if slot not in rules['configurable'] or not allowed or not d else \
            family(game, (d.get('main') or {}).get('id')) in {family(game, a) for a in allowed}
        subs = [{**s, 'rolls': shown_rolls(s, game), 'weight': (w or {}).get(s['id'], 0)} for s in (d or {}).get('subs', [])]
        # upgrades that went into substats that do not count (known only when the API reports roll counts)
        wasted = None if not d or not w or any(type(s.get('level')) is not int for s in subs) else \
            sum(s['level'] - 1 for s in subs if not s['weight'])
        slots.append({'slot': slot, 'disc': d, 'score': score, 'main_ok': main_ok, 'subs': subs, 'wasted': wasted})
    scores = [s['score'] if s['disc'] else 0.0 for s in slots]
    total = None if not w or any(v is None for v in scores) else round(sum(scores) / len(slots), 1)
    counts: dict[int, int] = {}
    for d in by_slot.values():
        counts[d['set_id']] = counts.get(d['set_id'], 0) + 1
    sets = [{**s, 'have': counts.get(s['id'], 0), 'ok': counts.get(s['id'], 0) >= s['count']} for s in target['sets']]
    checks = {'filled': len(by_slot) == rules['slots'], 'sets': all(s['ok'] for s in sets),
              'main': all(s['main_ok'] is not False for s in slots),
              'score': None if total is None else total >= target['score']}
    done = None if checks['score'] is None else all(checks.values())
    official = official_weights(gear, game)
    totals: dict[str, float] = {}
    for s in slots:
        for sub in s['subs']:
            if sub['weight'] and sub['rolls'] is not None:
                totals[str(sub['id'])] = round(totals.get(str(sub['id']), 0) + sub['rolls'], 2)
    return {'at': gear.get('at'), 'slots': slots, 'score': total, 'weights': {str(k): v for k, v in (w or {}).items()},
            'source': source, 'target': target, 'sets': sets, 'checks': checks, 'done': done,
            'next_set': next_set(sets), 'plan': gear.get('plan'), 'build': build_defaults(goal),
            'official': official and {str(k): v for k, v in official.items()}, 'totals': totals}


# ---------------------------------------------------------------- targets

def build_defaults(goal: dict) -> dict:
    """Sets and configurable main stats of the followed build; its first set is the 4-piece set."""
    plan = (goal.get('gear') or {}).get('plan') or {}
    sets = [{'id': s['id'], 'name': s['name'], 'count': c} for s, c in zip(plan.get('sets') or [], (4, 2)) if s.get('id')]
    return {'sets': sets, 'main': {str(k): list(dict.fromkeys(legal_main(goal['game'], k, int(i)) for i in v))
                                   for k, v in (plan.get('main') or {}).items()}}


def effective_target(goal: dict) -> dict:
    """The user's target; sets, main stats and weights left out follow the build."""
    own = goal.get('gear_target') or {}
    build = build_defaults(goal)
    sets = own['sets'] if own.get('sets') is not None else build['sets']
    plan = (goal.get('gear') or {}).get('plan') or {}
    names = {s['id']: s['name'] for s in plan.get('sets') or []}
    names.update({d['set_id']: d['set'] for d in (goal.get('gear') or {}).get('discs', [])})
    main = own['main'] if own.get('main') is not None else build['main']
    return {'farm': bool(own.get('farm')), 'score': int(own.get('score', DEFAULT_SCORE)),
            'sets': [{'id': int(s['id']), 'name': s.get('name') or names.get(int(s['id']), ''), 'count': int(s['count'])} for s in sets],
            'main': {str(k): [int(i) for i in v] for k, v in main.items()}, 'stage': own.get('stage') or ''}


def next_set(sets: list[dict]) -> dict | None:
    """The set to farm: the first unmet set in target order, else the first (usually the 4-piece) set."""
    if not sets:
        return None
    return next((s for s in sets if not s['ok']), sets[0])


def clean_target(raw: dict, game: str, build_main: dict | None = None) -> dict:
    """Validate an equipment target sent by the dashboard; fields left out keep following the build.
    ``build_main`` adds the main stats the followed build recommends (a newer stat this table lacks)."""
    if game not in RULES:
        raise ValueError(tr('invalid_game'))
    rules = RULES[game]
    result: dict = {'farm': bool(raw.get('farm'))}
    if raw.get('score') is not None:
        score = int(raw['score'])
        if not 0 <= score <= 100:
            raise ValueError(tr('gear_score_range'))
        result['score'] = score
    if raw.get('sets') is not None:
        sets, seen = [], set()
        for s in raw['sets'][:3]:
            sid, count = int(s['id']), int(s['count'])
            if count not in (2, 4) or sid in seen:
                raise ValueError(tr('gear_bad_sets'))
            seen.add(sid)
            sets.append({'id': sid, 'name': str(s.get('name') or '')[:40], 'count': count})
        if sum(s['count'] for s in sets) > rules['set_pieces']:
            raise ValueError(tr('gear_bad_sets'))
        result['sets'] = sets
    if raw.get('main') is not None:
        main = {}
        for slot in map(str, rules['configurable']):
            ids = [int(i) for i in (raw['main'].get(slot) or [])]
            if any(i not in rules['mains'][int(slot)] and i not in ((build_main or {}).get(slot) or []) for i in ids):
                raise ValueError(tr('gear_bad_main', slot=slot))
            main[slot] = ids
        result['main'] = main
    weights_ = clean_weights(raw.get('weights'), game)
    if weights_:
        result['weights'] = weights_
    if raw.get('stage'):
        result['stage'] = str(raw['stage'])[:60]
    return result
