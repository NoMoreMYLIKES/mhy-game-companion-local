"""Material metadata, farming routes and unit conversion.

Inputs are the per-goal material rows produced by the official calculators:
``{'id','name','need','owned','remaining','category', 'domain','weekdays','monster'}``.
``remaining`` is the official net gap (Genshin) or need-owned (ZZZ); None means UNKNOWN.
Outputs are *collection items*: one farmable target with a finite unit count.
Expected yields are planning estimates only; they never become inventory.
"""
from __future__ import annotations

import functools
import math
from pathlib import Path

import yaml

from . import core
from .i18n import tr

# Chinese strings in this module are data identifiers, not UI text: material names and
# type labels come from the CN (zh-cn) API and datasets, mission names from the
# BetterGI / OneDragon catalogs. They must match those sources exactly.

# SEELIE published highest-difficulty expectations (basic-tier equivalents).
GENSHIN_RATES = {'MasteryDomain': [2.21, 8.06, 10.22], 'ForgeryDomain': [2.2, 9.4, 14.8, 16.69]}
# Dataset typeText: Talent Level-Up Material, Weapon Ascension Material.
GENSHIN_KIND = {'角色天赋素材': 'MasteryDomain', '武器突破素材': 'ForgeryDomain'}
# Top-tier EXP material -> (OneDragon Combat Simulation mission, SEELIE drop key).
ZZZ_EXP_TOP = {'资深调查员记录': ('调查专项', 'c_xp'), '音擎能源模块': ('音擎专项', 'w_xp')}
ZZZ_EXP_VALUE = 3000
ZZZ_LOWER_EXP = ('见习调查员记录', '正式调查员记录', '音擎蓄电池', '音擎电源')
COST = {'card': 20, 'claim20': 20, 'boss': 40, 'zzz_boss': 40, 'disc': 60}
# Dataset typeText of Genshin series that convert 3:1 (talent books, weapon ascension, enemy drops, gems).
GENSHIN_FAMILY_TYPES = ('角色天赋素材', '武器突破素材', '角色与武器培养素材', '角色突破素材')


def tint(game: str, material: dict) -> str | None:
    """UI category of a material: 'exp', 'family' (convertible series), 'core' (ZZZ core skill) or None."""
    row = meta(game, material.get('id'))
    if game == 'genshin':
        kind = row.get('typeText') or ''
        return 'exp' if '经验' in kind else 'family' if kind in GENSHIN_FAMILY_TYPES else None
    kind = row.get('kind')
    if kind == 'xp' or material.get('name') in ZZZ_EXP_TOP:
        return 'exp'
    return {'chip': 'family', 'seal_c': 'family', 'seal_w': 'family', 'boss': 'core', 'boss_weekly': 'core'}.get(kind)


def unit_label(unit: str | None) -> str:
    return tr('unit_' + unit) if unit in COST else ''


@functools.lru_cache(maxsize=2)
def dataset(game: str) -> dict:
    return core.read_json(core.DATASETS / f'{game}.json', {})


def meta(game: str, material_id) -> dict:
    return dataset(game).get('materials', {}).get(str(material_id), {})


def characters(game: str) -> list[dict]:
    rows = dataset(game).get('characters', {})
    return sorted(({'id': str(c['id']), 'name': c['name'], 'element': c.get('element', ''),
                    'rarity': c.get('rarity'), 'weapon_type': c.get('weapon_type', '')} for c in rows.values()),
                  key=lambda c: c['name'])


# ---------------------------------------------------------------- tool catalogs

def bgi_bosses(root: str) -> list[str]:
    """Boss names from BetterGI's '<boss>前往' (go-to) pathing files, minus helper variants."""
    folder = Path(root) / 'GameTask/AutoBoss/Assets/Pathing'
    try:
        names = [p.stem.removesuffix('前往') for p in folder.glob('*前往.json')]
    except OSError:
        return []
    return sorted(n for n in names if not any(x in n for x in ('战斗后', '强制', '键鼠')))


def bgi_domains(root: str) -> list[dict]:
    data = core.read_json(Path(root) / 'GameTask/AutoTrackPath/Assets/tp.json', {}) or {}
    result = []
    for world in data.get('data', []):
        for p in world.get('points', []):
            if p.get('type') in ('BlessDomain', 'ForgeryDomain', 'MasteryDomain'):
                result.append({'name': p['name'], 'type': p['type']})
    return result


@functools.lru_cache(maxsize=4)
def _compendium(root: str, mtime: float) -> dict:
    data = yaml.safe_load((Path(root) / 'assets/game_data/compendium_data.yml').read_text(encoding='utf-8-sig')) or []
    result = {}
    for tab in data:
        if tab.get('tab_name') != '训练':  # the "Training" tab
            continue
        for category in tab.get('category_list', []):
            types = {}
            for kind in category.get('mission_type_list', []):
                types[kind['mission_type_name']] = [m.get('mission_name') for m in (kind.get('mission_list') or [])]
            result[category['category_name']] = types
    return result


def zzz_compendium(root: str) -> dict:
    path = Path(root) / 'assets/game_data/compendium_data.yml'
    try:
        return _compendium(str(root), path.stat().st_mtime)
    except (OSError, ValueError, yaml.YAMLError):
        return {}


def zzz_disc_missions(root: str) -> list[str]:
    """Area Patrol (区域巡防) entries except the agent-plan pseudo entry."""
    return [k for k in zzz_compendium(root).get('区域巡防', {}) if k != '代理人方案培养']


def _strip(name: str) -> str:
    return str(name or '').replace('「', '').replace('」', '').strip()


# ---------------------------------------------------------------- routes

def zzz_route(material: dict, compendium: dict) -> dict | None:
    name = material['name']
    row = meta('zzz', material['id'])
    kind = row.get('kind')
    source = (row.get('sources') or [None])[0]
    if name in ZZZ_EXP_TOP:
        return {'category': '实战模拟室', 'mission_type': '基础材料', 'mission': ZZZ_EXP_TOP[name][0], 'unit': 'card'}
    if name == '丁尼' or kind == 'currency':
        return {'category': '实战模拟室', 'mission_type': '基础材料', 'mission': '赏金专项', 'unit': 'card'}
    mission_type = {'chip': '代理人技能', 'seal_c': '代理人晋升', 'seal_w': '音擎改装'}.get(kind)
    if mission_type and source:
        return {'category': '实战模拟室', 'mission_type': mission_type, 'mission': source, 'unit': 'card'}
    if kind == 'boss' and source:
        names = compendium.get('专业挑战室', {})
        exact = next((k for k in names if _strip(k) == _strip(source)), source)
        return {'category': '专业挑战室', 'mission_type': exact, 'mission': None, 'unit': 'zzz_boss'}
    return None


def genshin_family(material_id) -> dict | None:
    row = meta('genshin', material_id)
    kind = GENSHIN_KIND.get(row.get('typeText'))
    if not kind or not row.get('domain'):
        return None
    ids = sorted(int(k) for k, v in dataset('genshin')['materials'].items()
                 if v.get('typeText') == row['typeText'] and v.get('domain') == row['domain']
                 and v.get('weekdays') == row.get('weekdays') and str(k).isdigit())
    # Same domain/day hosts exactly one series per type; ids are consecutive tiers.
    if len(ids) != len(GENSHIN_RATES[kind]) or ids != list(range(ids[0], ids[0] + len(ids))):
        return None
    return {'kind': kind, 'domain': row['domain'], 'weekdays': row.get('weekdays') or list(range(7)),
            'ids': [str(i) for i in ids], 'base': str(ids[0])}


# ---------------------------------------------------------------- collection items

def _ceil(value: float) -> int:
    return int(math.ceil(round(value, 6)))


def items_for_goal(goal: dict, ctx: dict) -> list[dict]:
    """Group a goal's materials into farmable items in the goal's category order.

    ``ctx`` carries tool catalogs: ``bosses`` (Genshin) and ``compendium`` (ZZZ).
    Each item has ``units`` (int, or None for UNKNOWN) and an explanatory ``note``.
    """
    rows = [m for m in goal.get('materials', []) if (m.get('need') or 0) > 0]
    paused = set(goal.get('paused', []))
    order = goal.get('category_order') or ['level', 'talents', 'weapon']
    rank = lambda m: min((order.index(c) for c in m.get('categories', [m.get('category')]) if c in order), default=len(order))
    items: dict[str, dict] = {}

    def add(key, **fields):
        item = items.setdefault(key, {'key': f"{goal['id']}:{key}", 'goal_id': goal['id'], 'goal': goal['name'],
                                      'game': goal['game'], 'materials': [], 'rank': 99, **fields})
        return item

    for m in rows:
        if goal['game'] == 'genshin':
            family = genshin_family(m['id'])
            if family:
                item = add('family:' + family['base'], kind='domain', label=family['domain'], unit='claim20',
                           route={'kind': 'domain', 'name': family['domain'], 'domain_type': family['kind']},
                           weekdays=family['weekdays'], family=family)
            elif m.get('monster') and m['monster'] in ctx.get('bosses', []):
                item = add('boss:' + str(m['id']), kind='boss', label=m['monster'], unit='boss',
                           route={'kind': 'boss', 'name': m['monster']}, weekdays=list(range(7)))
            else:
                item = add('manual:' + str(m['id']), kind='manual', label=m['name'], unit=None, route=None,
                           weekdays=list(range(7)))
        else:
            row = meta('zzz', m['id'])
            route = zzz_route(m, ctx.get('compendium', {}))
            if m['name'] in ZZZ_LOWER_EXP:
                continue  # planned through the top tier only; lower tiers stay informational
            if route and row.get('group') and row.get('kind') in ('chip', 'seal_c', 'seal_w'):
                key = 'group:' + row['group']
            elif route:
                key = 'mat:' + str(m['id'])
            else:
                key = 'manual:' + str(m['id'])
            label = (route or {}).get('mission') or (route or {}).get('mission_type') or m['name']
            item = add(key, kind='zzz' if route else 'manual', label=label,
                       unit=(route or {}).get('unit'), route=route, weekdays=list(range(7)))
        item['materials'].append(m)
        item['rank'] = min(item['rank'], rank(m))

    result = []
    for key, item in items.items():
        item['paused'] = item['key'] in paused or key in paused  # full item key (UI) or legacy short key
        item['units'], item['note'] = _units(goal, item)
        item['names'] = tr('sep').join(dict.fromkeys(m['name'] for m in item['materials']))
        item['done'] = item['units'] == 0
        item['tint'] = tint(goal['game'], item['materials'][0])
        result.append(item)
    return sorted(result, key=lambda i: (i['rank'], i['kind'] == 'manual', i['key']))


def _units(goal: dict, item: dict) -> tuple[int | None, str]:
    mats = item['materials']
    if item['kind'] == 'manual':
        left = [m['remaining'] for m in mats]
        if all(v == 0 for v in left):
            return 0, tr('note_enough')
        return None, tr('note_no_route')
    if any(m.get('remaining') is None for m in mats):
        return None, tr('note_owned_unknown')
    if item['kind'] == 'domain':
        f = item['family']
        rates = GENSHIN_RATES[f['kind']]
        gaps = [next((m['remaining'] for m in mats if str(m['id']) == mid), 0) for mid in f['ids']]
        prefix = [sum(gaps[t] * 3 ** t for t in range(i + 1)) for i in range(len(gaps))]
        claims = max(_ceil(n / r) for n, r in zip(prefix, rates))
        return claims, tr('note_domain', claims=claims)
    if item['kind'] == 'boss':
        left = sum(m['remaining'] for m in mats)
        rate = float(core.settings()['planning']['genshin_boss_yield'])
        runs = _ceil(left / rate) if left else 0
        return runs, tr('note_runs', left=left, rate=f'{rate:g}', runs=runs)
    drops = dataset('zzz').get('farming', {}).get('drops', {}).get('4', {})
    row = meta('zzz', mats[0]['id'])
    kind = row.get('kind')
    if kind in ('chip', 'seal_c', 'seal_w'):
        need = sum(m['need'] * 3 ** int(meta('zzz', m['id']).get('tier') or 0) for m in mats)
        owned = sum((m.get('owned') or 0) * 3 ** int(meta('zzz', m['id']).get('tier') or 0) for m in mats)
        if any(m.get('owned') is None for m in mats):
            left = sum(m['remaining'] * 3 ** int(meta('zzz', m['id']).get('tier') or 0) for m in mats)
        else:
            left = max(0, need - owned)  # 3:1 synthesis and 1:3 split make the series one pool
        rate = drops.get(kind) or {'chip': 15.3, 'seal_c': 12.5, 'seal_w': 18.6}[kind]
        cards = _ceil(left / rate) if left else 0
        return cards, tr('note_series', left=left, rate=f'{rate:g}', cards=cards)
    name = mats[0]['name']
    left = sum(m['remaining'] for m in mats)
    if name in ZZZ_EXP_TOP:
        rate = drops.get(ZZZ_EXP_TOP[name][1]) or 11272
        cards = _ceil(left * ZZZ_EXP_VALUE / rate) if left else 0
        return cards, tr('note_exp', left=left, name=name, rate=f'{rate:g}', cards=cards)
    if name == '丁尼':  # Dennies
        rate = drops.get('denny') or 25000
        cards = _ceil(left / rate) if left else 0
        return cards, tr('note_denny', left=left, rate=f'{rate:g}', cards=cards)
    if kind == 'boss':
        rate = drops.get('boss') or 5
        runs = _ceil(left / rate) if left else 0
        return runs, tr('note_runs', left=left, rate=f'{rate:g}', runs=runs)
    return None, tr('note_no_rule')


def item_progress(item: dict) -> str:
    parts = []
    for m in item['materials']:
        have = '?' if m.get('owned') is None else m['owned']
        left = '?' if m.get('remaining') is None else m['remaining']
        parts.append(tr('progress', name=m['name'], need=m['need'], have=have, left=left))
    return tr('sep_strong').join(parts)
