"""Inventory scanners the app runs after farming, and their output formats.

Both scanners read the game screen (OCR, Simplified Chinese UI, 16:9 window); neither reads game
memory, and neither is part of this repository: their programs are set in Settings.

- Genshin: yas (a maintained fork, ``yas_artifact.exe``) writes ``good.json`` in GOOD, Genshin
  Optimizer's format, once the bag is open on the artifact tab. It needs administrator rights (the
  backend has them on Windows), waits for a key press at the end and exits 0 even after a failure,
  so success is judged by a fresh ``good.json``.
- ZZZ: ZZZ-Scanner.Next (``--scan-once``) writes ``export.json`` (Chinese keys) once the Drive Disc
  storage is open; exit code 0 means success. Its export has no lock state and no wearer.

The app opens those screens itself with key presses and clicks at 1920×1080 positions, scaled to the
game window. A scan never locks, salvages or equips anything.
"""
from __future__ import annotations

import functools
import json
import logging
import time
from pathlib import Path

from . import core, gear, inventory, materials, tools
from .i18n import tr

log = logging.getLogger('gcl.scanners')

# GOOD stat keys → Genshin property ids (FightProp); a key ending in "_" is a percentage.
GOOD_STATS = {'hp': 2, 'hp_': 3, 'atk': 5, 'atk_': 6, 'def': 8, 'def_': 9, 'critRate_': 20, 'critDMG_': 22,
              'enerRech_': 23, 'heal_': 26, 'eleMas': 28, 'physical_dmg_': 30, 'pyro_dmg_': 40, 'electro_dmg_': 41,
              'hydro_dmg_': 42, 'dendro_dmg_': 43, 'anemo_dmg_': 44, 'geo_dmg_': 45, 'cryo_dmg_': 46}
GOOD_SLOTS = {'flower': 1, 'plume': 2, 'sands': 3, 'goblet': 4, 'circlet': 5}
# ZZZ-Scanner.Next stat names → (flat id, percent id); the value tells which: "9.6%" or 19.
ZZZ_STATS = {'生命值': (11103, 11102), '攻击力': (12103, 12102), '防御力': (13103, 13102), '穿透值': (23203, None),
             '异常精通': (31203, None), '暴击率': (None, 20103), '暴击伤害': (None, 21103), '穿透率': (None, 23103),
             '物理伤害加成': (None, 31503), '火属性伤害加成': (None, 31603), '冰属性伤害加成': (None, 31703),
             '电属性伤害加成': (None, 31803), '以太伤害加成': (None, 31903), '风属性伤害加成': (None, 32303),
             '能量自动回复': (None, 30502), '异常掌控': (None, 31402), '冲击力': (None, 12202)}
ZZZ_RARITY = {'S': 1.0, 'A': 2 / 3, 'B': 1 / 3}  # roll size relative to an S-rank roll
SCAN_TIMEOUT = 40 * 60
RESCAN_AFTER = 24 * 3600  # without an equipment batch, scan at most once a day


# ---------------------------------------------------------------- formats

def _stat(pid: int, value, percent: bool, level: int | None = None) -> dict:
    number = float(str(value).rstrip('%'))
    return {'id': pid, 'name': '', 'value': f'{number:g}%' if percent else f'{number:g}', 'number': number,
            'percent': percent, 'level': level, 'valid': None}


@functools.lru_cache(maxsize=1)
def _artifact_sets() -> dict[str, dict]:
    rows = core.read_json(core.DATASETS / 'genshin_artifact_sets.json', {}).get('sets', [])
    return {r['key']: r for r in rows}


def from_good(data: dict) -> list[dict]:
    """GOOD (yas, Genshin Optimizer) → pieces in the observation's format, plus wearer and lock."""
    if not isinstance(data, dict) or data.get('format') != 'GOOD':
        raise ValueError(tr('scan_bad_file'))
    sets = _artifact_sets()
    pieces = []
    for a in data.get('artifacts') or []:
        slot, main = GOOD_SLOTS.get(a.get('slotKey')), GOOD_STATS.get(a.get('mainStatKey'))
        if not slot or not main:
            continue  # a slot or stat this table does not know
        known = sets.get(a.get('setKey')) or {}
        subs = [_stat(GOOD_STATS[s['key']], s['value'], s['key'].endswith('_'))
                for s in a.get('substats') or [] if s.get('key') in GOOD_STATS and s.get('value')]
        pieces.append({'slot': slot, 'level': int(a.get('level') or 0), 'rarity': str(a.get('rarity') or ''),
                       'set_id': int(known.get('id') or 0), 'set': known.get('name') or str(a.get('setKey') or ''),
                       'icon': '', 'main': {'id': main, 'name': '', 'value': '', 'number': None,
                                            'percent': a['mainStatKey'].endswith('_'), 'level': None, 'valid': None},
                       'subs': subs, 'location': a.get('location') or None, 'lock': bool(a.get('lock'))})
    return pieces


def _zzz_set_ids() -> dict[str, int]:
    """Set name → suit id: the stage snapshot, then any set Miyoushe named on a goal."""
    ids = {materials.set_key(s['name']): s['id'] for st in materials.gear_stages('zzz') for s in st['sets'] if s.get('id')}
    for goal in core.goals('zzz'):
        g = goal.get('gear') or {}
        for d in g.get('discs', []):
            ids.setdefault(materials.set_key(d['set']), d['set_id'])
        for s in (g.get('plan') or {}).get('sets', []):
            ids.setdefault(materials.set_key(s['name']), s['id'])
    return ids


def _zzz_stat(name: str, value, rarity: str, main: bool) -> dict | None:
    ids = ZZZ_STATS.get(name)
    if not ids:
        return None
    percent = isinstance(value, str) and value.strip().endswith('%')
    pid = ids[1] if percent else ids[0]
    if pid is None:
        return None
    stat = _stat(pid, value, percent)
    step = gear.RULES['zzz']['step'].get(pid)
    if not main and step:
        stat['level'] = max(1, round(stat['number'] / (step * ZZZ_RARITY.get(rarity, 1.0))))
    return stat


def from_zzz_scanner(records: list) -> list[dict]:
    """ZZZ-Scanner.Next's export.json → pieces. Its export names no wearer and no lock state."""
    if not isinstance(records, list):
        raise ValueError(tr('scan_bad_file'))
    ids = _zzz_set_ids()
    pieces = []
    for r in records:
        rarity = str(r.get('品质') or '')
        mains = [_zzz_stat(k, v, rarity, True) for k, v in (r.get('主属性') or {}).items()]
        subs = [_zzz_stat(k, v, rarity, False) for d in r.get('副属性') or [] for k, v in d.items()]
        if not mains or mains[0] is None or not r.get('槽位'):
            continue
        name = str(r.get('名称') or '')
        pieces.append({'slot': int(r['槽位']), 'level': int(r.get('等级') or 0), 'rarity': rarity,
                       'set_id': int(ids.get(materials.set_key(name), 0)), 'set': name, 'icon': '',
                       'main': mains[0], 'subs': [s for s in subs if s], 'location': None, 'lock': None})
    return pieces


# ---------------------------------------------------------------- when and how

def due(game: str, phase: str | None) -> bool:
    """Scan after an equipment batch, or when the last scan is older than a day."""
    s = core.settings()
    if not s['features']['scan_inventory'] or not scanner_exe(game):
        return False
    last = core.parse(core.get('inventory_at:' + game))
    return phase == 'equipment' or last is None or (core.now() - last).total_seconds() >= RESCAN_AFTER


def scanner_exe(game: str) -> Path | None:
    path = core.settings()['paths']['yas' if game == 'genshin' else 'zzz_scanner']
    return Path(path) if path and Path(path).is_file() else None


def _open_screen(game: str, hwnd: int) -> None:
    """From the open world to the scanner's screen (1920×1080 positions)."""
    tools.focus(hwnd)
    time.sleep(1)
    if game == 'genshin':
        tools.key('B')                       # bag
        time.sleep(2)
        tools.click(hwnd, 675, 50)           # artifact tab
        time.sleep(2)
        return
    tools.click(hwnd, 130, 71, alt=True)     # menu button (Alt frees the cursor)
    time.sleep(2.5)
    tools.click(hwnd, *ZZZ_MENU_STORAGE)     # 仓库 (storage) in the menu's bottom bar
    time.sleep(3)
    tools.click(hwnd, 1549, 168)             # Drive Disc tab
    time.sleep(2.5)


# The storage button in ZZZ's menu bar (1920×1080). OneDragon finds it by its text; its position here
# was read from a screenshot of the CN client.
ZZZ_MENU_STORAGE = (0, 0)


def run(game: str, game_exe: Path, stop) -> dict:
    """Open the screen, run the scanner, store the inventory. Returns {'count'} or {'error'}."""
    exe = scanner_exe(game)
    hwnd = tools.game_window(game_exe)
    if not exe or not hwnd:
        return {'error': tr('scan_no_window') if exe else tr('scan_no_scanner')}
    if game == 'zzz' and ZZZ_MENU_STORAGE == (0, 0):
        return {'error': tr('scan_zzz_position')}
    out = core.DATA / 'scans' / game
    out.mkdir(parents=True, exist_ok=True)
    _open_screen(game, hwnd)
    started = time.time()
    if game == 'genshin':
        args = ['-f', 'good', '--output-dir', str(out)]
    else:
        args = ['--scan-once', '--include-non15', '--output-root', str(out)]
    proc = tools.start(exe, args, hidden=True)
    deadline = time.monotonic() + SCAN_TIMEOUT
    while proc.poll() is None:
        if stop.wait(3) or time.monotonic() > deadline:
            tools.kill_tree(proc.pid)
            return {'error': tr('scan_stopped') if stop.is_set() else tr('scan_timeout')}
    if game == 'zzz' and proc.returncode != 0:
        return {'error': tr('scan_failed', code=proc.returncode)}
    found = sorted((p for p in out.rglob('good.json' if game == 'genshin' else 'export.json')
                    if p.stat().st_mtime >= started - 1), key=lambda p: p.stat().st_mtime)
    if not found:
        return {'error': tr('scan_no_output')}
    data = json.loads(found[-1].read_text(encoding='utf-8-sig'))
    pieces = from_good(data) if game == 'genshin' else from_zzz_scanner(data)
    if not pieces:
        return {'error': tr('scan_empty')}
    inventory.save(game, pieces, 'yas' if game == 'genshin' else 'ZZZ-Scanner.Next', located=game == 'genshin')
    return {'count': len(pieces)}
