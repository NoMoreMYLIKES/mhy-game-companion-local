"""Official data: accounts, stamina, character state, calculators.

Only official Miyoushe (CN-server HoYoLAB) endpoints. Credentials are DPAPI-encrypted
on Windows; on Linux only file permissions protect them.
A failed read never becomes 0: callers receive an error and keep the previous value.
"""
from __future__ import annotations

import asyncio
import logging
import random
import uuid
from datetime import timedelta

import genshin
from genshin.models.genshin.calculator import CalculatorBatchResult

from . import assets, auth, core, gear
from .i18n import MESSAGES, tr

log = logging.getLogger('gcl.mihoyo')
GAMES = {'genshin': genshin.Game.GENSHIN, 'zzz': genshin.Game.ZZZ}
SKILLS = {'attack': 0, 'special': 1, 'dodge': 2, 'chain': 3, 'core': 5, 'assist': 6}
LOGIN_EXPIRED = (-100, 10001, -1071)  # genshin.py's InvalidCookies codes for a login that lapsed


def run(read, timeout: float = 60):
    """Run read(), an official request. The website cookies can lapse while the app grant stays valid:
    on such an answer they are renewed from the grant and read() runs once more."""
    try:
        return asyncio.run(asyncio.wait_for(read(), timeout))
    except genshin.GenshinException as exc:
        if exc.retcode not in LOGIN_EXPIRED or not auth.renew():
            raise
    return asyncio.run(asyncio.wait_for(read(), timeout))


def cookies() -> dict:
    return core.load_secret('mihoyo').get('cookies', {})


def accounts() -> dict:
    return core.load_secret('mihoyo').get('accounts', {})


def account_candidates() -> dict:
    return core.load_secret('mihoyo').get('candidates', {})


def logged_in() -> bool:
    return bool(auth.credentials())


def describe_error(exc: Exception) -> str:
    code = getattr(exc, 'retcode', None)
    name = type(exc).__name__
    if code in LOGIN_EXPIRED or 'Cookie' in name:
        return tr('err_login_expired')
    if code in (1034, 10035, 5003, 10041) or 'Geetest' in name:
        return tr('err_captcha', code=code)
    if code in (10102, 10103) or 'Private' in name:
        return tr('err_private')
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError, OSError)) or 'Timeout' in name or 'Connect' in name:
        return tr('err_network')
    if type(exc) is ValueError:
        return str(exc)[:200]
    if code is None:  # a fault here or in genshin.py, not an API answer: the class name alone cannot be diagnosed
        log.error('Unexpected %s in a Miyoushe request\n%s', name, core.stack(exc))
    return tr('err_api', name=name) + (tr('err_code', code=code) if code is not None else '')


# ---------------------------------------------------------------- device identity

def device() -> dict:
    value = core.get('device')
    if not value:
        value = {'id': str(uuid.uuid4()), 'board': random.choice(['sdm845', 'kona', 'lahaina', 'taro']),
                 'oaid': uuid.uuid4().hex, 'fp': None}
        core.put('device', value)
    return value


async def _ensure_fp() -> dict:
    value = device()
    if not value.get('fp'):
        try:
            c = genshin.Client(region=genshin.Region.CHINESE, lang='zh-cn')
            value['fp'] = await c.generate_fp(device_id=value['id'], device_board=value['board'], oaid=value['oaid'])
            core.put('device', value)
        except Exception as exc:  # fingerprint is best-effort; requests still work without it
            log.warning('Device fingerprint request failed: %s', describe_error(exc))
    return value


def client(game: str | None = None) -> genshin.Client:
    d = device()
    c = genshin.Client(cookies=cookies(), region=genshin.Region.CHINESE, lang='zh-cn', game=GAMES.get(game),
                       device_id=d['id'], device_fp=d.get('fp') or None)
    app = auth.credentials()
    if app:
        c.custom_headers.update(app['identity'])
    for name, account in accounts().items():
        if name in GAMES and account:
            c.uids[GAMES[name]] = int(account['uid'])
    return c


# ---------------------------------------------------------------- accounts

def select_account(game: str, uid: str) -> None:
    with core.LOCK:
        choice = next((a for a in account_candidates().get(game, []) if a['uid'] == str(uid)), None)
        if not choice:
            raise ValueError(tr('account_not_listed'))
        saved = core.load_secret('mihoyo')
        core.save_secret('mihoyo', {**saved, 'accounts': {**saved.get('accounts', {}), game: choice}})


def logout() -> None:
    with core.LOCK:
        auth.cancel()
        core.save_secret('mihoyo', {})


# ---------------------------------------------------------------- source health / backoff

def health(key: str) -> dict:
    return core.get('health:' + key, {})


def allowed(key: str, force: bool = False) -> bool:
    h = health(key)
    if force or not h.get('retry_at'):
        return True
    retry = core.parse(h['retry_at'])
    return retry is None or core.now() >= retry


def record(key: str, ok: bool, reason: str = '') -> None:
    h = health(key)
    if ok:
        h = {'ok': True, 'at': core.stamp(), 'reason': reason, 'failures': 0}
    else:
        failures = int(h.get('failures', 0)) + 1
        delay = min(6 * 3600, 900 * 2 ** min(failures - 1, 5))
        h = {'ok': False, 'at': core.stamp(), 'reason': reason, 'failures': failures,
             'retry_at': core.stamp(core.now() + timedelta(seconds=delay)),
             'expired': reason in MESSAGES['err_login_expired']}  # either language
        if h['expired'] and failures == 1:
            from . import notify
            notify.event('login', tr('login_expired_title'), [reason])
    core.put('health:' + key, h)


# ---------------------------------------------------------------- stamina

def refresh_notes(game: str, force: bool = False) -> dict:
    """Read the stamina from the official widget; a failure keeps the previous sample."""
    from . import widget
    key = 'stamina-' + game
    login = auth.binding(game)
    if not accounts().get(game) or not logged_in():
        return {'error': tr('not_logged_in')}
    if not allowed(key, force):
        return {'error': health(key).get('reason', tr('backing_off')), 'deferred': True}
    try:
        current, cap = run(lambda: widget.note(game), 40)
        with core.LOCK:
            if login != auth.binding(game):
                raise ValueError(tr('login_changed'))
            core.add_sample(game, current, cap, 'source_widget')
            record(key, True, tr('notes_ok'))
        return {'current': current, 'cap': cap}
    except Exception as exc:
        reason = describe_error(exc)
        with core.LOCK:
            if login == auth.binding(game):
                record(key, False, reason)
        return {'error': reason}


# ---------------------------------------------------------------- roster and character state

async def _genshin_avatars(c: genshin.Client) -> list[dict]:
    """The calculator's synced characters as the official API returns them: level, equipped weapon,
    talents and the official icon, in one request. genshin.py's character model is avoided on purpose:
    it needs a name table downloaded from third-party sites, fails without it, and swaps the official
    icon for an Enka one."""
    uid = int(accounts()['genshin']['uid'])
    payload = {'page': 1, 'size': 200, 'element_attr_ids': [], 'weapon_cat_ids': [], 'uid': uid,
               'region': genshin.utility.recognize_genshin_server(uid)}
    try:
        data = await c.request_calculator('sync/avatar/list', data=payload)
    except genshin.GenshinException as exc:
        if exc.retcode != -502002:  # character sync not enabled in the calculator yet
            raise
        await c.request_calculator('avatar/auth', data={'avatar_auth': 1})
        data = await c.request_calculator('sync/avatar/list', data=payload)
    if not isinstance(data.get('list'), list):
        raise ValueError(tr('calc_format'))
    return data['list']


def _talents(row: dict) -> dict:
    """Normal attack, skill and burst of a character row: level and calculator group id."""
    found: dict[str, dict] = {}
    for raw in row.get('skill_list') or []:
        talent = genshin.models.CalculatorTalent(**raw)  # its .type holds genshin.py's rules for the special cases
        if talent.type in ('attack', 'skill', 'burst'):
            found.setdefault(talent.type, {'level': talent.level, 'group': talent.group_id})
    return found


# The upgrade guide does not return role_square_url (genshin.py leaves square_icon None), so ZZZ portraits
# were never saved. The battle chronicle serves the same square avatar at a fixed official address per agent id.
ZZZ_SQUARE_AVATAR = 'https://act-webstatic.mihoyo.com/game_record/zzzv2/role_square_avatar/role_square_avatar_{id}.png'


def zzz_portrait(agent) -> str:
    return getattr(agent, 'square_icon', None) or ZZZ_SQUARE_AVATAR.format(id=int(agent.id))


def roster(game: str) -> list[dict]:
    async def read():
        c = client(game)
        if game == 'genshin':
            return [{'id': str(x['id']), 'name': x.get('name', ''), 'level': int(x.get('level_current') or 0),
                     'owned': True, 'icon': x.get('icon', ''), 'rarity': x.get('avatar_level'),
                     'element': genshin.models.CALCULATOR_ELEMENTS.get(x.get('element_attr_id'), '')}
                    for x in await _genshin_avatars(c) if int(x.get('level_current') or 0) > 0]
        agents = await c.get_zzz_upgrade_guide_agents()
        return [{'id': str(x.id), 'name': x.name, 'owned': bool(getattr(x, 'unlocked', True)),
                 'icon': zzz_portrait(x), 'element': str(getattr(x, 'element', '')),
                 'rarity': str(getattr(x, 'rarity', ''))} for x in agents if not getattr(x, 'is_teaser', False)]

    if not accounts().get(game):
        raise ValueError(tr('login_first'))
    rows = run(read, 60)
    _collect_icons({assets.key(game, 'character', r['id']): r.get('icon') for r in rows})
    return rows


def _collect_icons(sources: dict) -> None:
    """Images are a convenience: never let them break the official data flow."""
    try:
        assets.collect(sources)
    except Exception:
        log.exception('Image cache update failed')


GEAR_REREAD = timedelta(seconds=60)


async def _genshin_gear(c: genshin.Client, goal: dict, result: dict, force: bool = False) -> None:
    """Artifacts of this goal's character only: one extra request (character detail), never for the whole roster.
    Skipped right after a read, and backed off after failures (captchas) unless forced by a sync the user asked
    for; levels are read either way."""
    last = core.parse((goal.get('gear') or {}).get('at'))
    if last and core.now() - last < GEAR_REREAD:
        return
    if not allowed('detail', force):
        result['gear_error'] = health('detail').get('reason') or tr('backing_off')
        return
    try:
        uid = int(accounts()['genshin']['uid'])
        raw = await c.get_genshin_detailed_characters(uid, characters=[int(goal['character_id'])], return_raw_data=True)
        result['gear'] = gear.observe_genshin(raw, int(goal['character_id']))
        _collect_icons(gear.icons(result['gear'], 'genshin'))
        record('detail', True)
    except Exception as exc:
        reason = describe_error(exc)
        record('detail', False, reason)
        result['gear_error'] = reason


def observe(goal: dict, force: bool = False) -> dict:
    """Current levels from the official cultivation tools (never guessed). force: the user asked for this sync,
    so a backed-off equipment read is tried again."""
    game, cid = goal['game'], int(goal['character_id'])

    async def read():
        await _ensure_fp()
        c = client(game)
        if game == 'genshin':
            row = next((x for x in await _genshin_avatars(c)
                        if x.get('id') == cid and int(x.get('level_current') or 0) > 0), None)
            if row is None:
                raise ValueError(tr('char_not_owned'))
            _collect_icons({assets.key(game, 'character', cid): row.get('icon')})
            talents = _talents(row)
            current = {'level': int(row['level_current']), **{k: t['level'] for k, t in talents.items()}}
            result = {'current': current, 'talent_groups': {k: t['group'] for k, t in talents.items()},
                      'weapon_id': None, 'weapon_name': ''}
            weapon = row.get('weapon') or {}
            if weapon.get('id'):
                current['weapon'] = int(weapon.get('level_current') or 1)
                result.update(weapon_id=str(weapon['id']), weapon_name=weapon.get('name', ''))
            await _genshin_gear(c, goal, result, force)
            return result
        guide = (await c.get_zzz_agent_upgrade_guide(cid))[0]
        _collect_icons({assets.key(game, 'character', cid): zzz_portrait(guide.avatar)})
        rank = int(getattr(guide.avatar, 'rank', 0) or 0)
        bonus = 4 if rank >= 5 else 2 if rank >= 3 else 0
        skills = {int(s.type): (s.level - 1 if int(s.type) == 5 else s.level - bonus) for s in guide.avatar.skills}
        current = {'level': guide.avatar.level, 'promotion': guide.avatar.promotes}
        current.update({k: skills[v] for k, v in SKILLS.items() if v in skills})
        result = {'current': current, 'weapon_id': None, 'weapon_name': ''}
        weapon = guide.weapon
        if weapon and getattr(weapon, 'refinement', 0) > 0 and type(weapon.level) is int:
            current['weapon'] = weapon.level
            result.update(weapon_id=str(weapon.id), weapon_name=getattr(weapon, 'name', ''))
        try:  # the same response carries the equipped Drive Discs; a format change must not stop the level read
            result['gear'] = gear.observe_zzz(guide)
            _collect_icons(gear.icons(result['gear'], 'zzz'))
        except Exception:
            log.exception('Drive Disc read failed')
            result['gear_error'] = tr('gear_read_failed')
        return result

    if not accounts().get(game):
        raise ValueError(tr('login_first'))
    return run(read, 60)


# ---------------------------------------------------------------- calculators

def _count(value) -> int:
    """A non-negative whole amount from a calculator answer; anything else means its format changed."""
    if isinstance(value, str) and value.isdigit():
        value = int(value)
    if type(value) is not int or value < 0:
        raise ValueError(tr('calc_format'))
    return value


def _quantity(item: dict) -> int:
    """How many of a material a calculator row asks for. Rows have been seen naming it num or cnt; a row with
    neither (or with disagreeing ones) is a format change, never 'nothing needed'."""
    found = {_count(item[k]) for k in ('num', 'cnt', 'amount') if k in item}
    if len(found) != 1:
        raise ValueError(tr('calc_format'))
    return found.pop()


def calculate(goal: dict) -> list[dict]:
    """Official requirement rows: need, owned (ZZZ) and remaining (official gap).

    Every current level the request needs must have been read or entered: an unknown one is never taken as
    level 1. A saved target below the current level asks for nothing; the target itself stays as saved."""
    from . import materials
    game, cid = goal['game'], int(goal['character_id'])
    cur = goal.get('current') or {}
    tgt = {k: max(v, cur[k]) if cur.get(k) is not None and k != 'promotion' else v
           for k, v in (goal.get('target') or {}).items()}
    talents = ('attack', 'skill', 'burst') if game == 'genshin' else tuple(SKILLS)
    needed = ['level'] + [k for k in talents if k in tgt]
    if goal.get('weapon_id') and 'weapon' in tgt:
        needed.append('weapon')
    missing = [k for k in needed if cur.get(k) is None]
    if missing:
        raise ValueError(tr('calc_current_unknown', fields=tr('sep').join(missing)))

    async def genshin_calc():
        c = client(game)
        b = c.calculator().set_character(cid, int(cur['level']), int(tgt.get('level', cur['level'])))
        if 'weapon' in tgt and (cur.get('weapon') is None or tgt['weapon'] > cur['weapon']):
            if not goal.get('weapon_id'):
                raise ValueError(tr('weapon_needed'))
            b.set_weapon(int(goal['weapon_id']), int(cur['weapon']), int(tgt['weapon']))
        levels = {k: int(tgt[k]) for k in talents if k in tgt}
        wanted = [k for k in levels if levels[k] > int(cur[k])]
        group_ids = goal.get('talent_groups') or {}
        if any(k not in group_ids for k in wanted):  # goals observed before the group ids were kept
            row = next((x for x in await _genshin_avatars(c) if x.get('id') == cid), None)
            if row is None:
                raise ValueError(tr('char_not_owned'))
            group_ids = {k: t['group'] for k, t in _talents(row).items()}
        for k in wanted:
            if k not in group_ids:
                raise ValueError(tr('calc_format'))
            b.add_talent(group_ids[k], int(cur[k]), levels[k])
        # With the account's uid and server the calculator also returns what the backpack lacks
        # (has_user_info); genshin.py's batch_calculator() leaves them out, so every gap was unknown.
        uid = int(accounts()['genshin']['uid'])
        body = {'items': [await b.build()], 'uid': uid, 'region': genshin.utility.recognize_genshin_server(uid)}
        result = CalculatorBatchResult(**await c.request_calculator('batch_compute', data=body, api_version=3))
        info: dict[str, dict] = {}
        for category, groups in (('level', result.total_material_details.characters),
                                 ('weapon', result.total_material_details.weapon),
                                 ('talents', result.total_material_details.talents)):
            for group in groups:
                for item in group.materials:
                    row = info.setdefault(str(item.id), {'categories': []})
                    if category not in row['categories']:
                        row['categories'].append(category)
                    if group.domain:
                        row.update(domain=group.domain.name, weekdays=list(group.domain.weekdays))
                    if group.monster:
                        row['monster'] = group.monster.name
        _collect_icons({assets.key(game, 'material', item.id): getattr(item, 'icon', None)
                        for item in result.total_materials})
        rows = []
        for item in result.total_materials:
            extra = info.get(str(item.id), {'categories': ['level']})
            rows.append({'id': str(item.id), 'name': item.name, 'need': int(item.amount), 'owned': None,
                         'remaining': int(item.lacking) if result.has_user_info else None,
                         'category': extra['categories'][0], **extra})
        return rows

    async def zzz_calc():
        c = client(game)
        uid = int(accounts()['zzz']['uid'])  # genshin.py logs in to the cultivation tool on its own
        skills = [{'skill_type': kind, 'level': int(tgt.get(k, cur[k])), 'init_level': int(cur[k])}
                  for k, kind in SKILLS.items() if k in tgt or cur.get(k) is not None]  # targeted ones are known
        bounds = [10, 20, 30, 40, 50]
        level = int(cur['level'])
        wlevel = int(cur.get('weapon') or 0)  # 0 is a real W-Engine level; unknown only without a W-Engine id
        body = {'avatar_id': cid, 'avatar_level': int(tgt.get('level', level)), 'avatar_current_level': level,
                'avatar_current_promotes': int(cur.get('promotion', 1 + sum(level > b for b in bounds))),
                'skills': skills,
                'weapon_info': {'weapon_id': int(goal.get('weapon_id') or 0), 'weapon_level': int(tgt.get('weapon', wlevel)),
                                'weapon_init_level': wlevel, 'weapon_promotes': sum(wlevel > b for b in bounds)}}
        if int(tgt.get('weapon', 0)) > wlevel and not goal.get('weapon_id'):
            raise ValueError(tr('wengine_needed'))
        raw = await c._request_upgrade_guide('user/avatar_calc', uid, body=body)
        owns = raw.get('user_owns_materials') if isinstance(raw.get('user_owns_materials'), dict) else {}
        merged: dict[str, dict] = {}
        for field, category in (('avatar_consume', 'level'), ('skill_consume', 'talents'), ('weapon_consume', 'weapon')):
            if not isinstance(raw.get(field), list):
                raise ValueError(tr('calc_format'))
            for item in raw[field]:
                if not isinstance(item, dict) or 'id' not in item:
                    raise ValueError(tr('calc_format'))
                mid = str(item['id'])
                if isinstance(item.get('icon'), str):
                    _collect_icons({assets.key(game, 'material', mid): item['icon']})
                row = merged.setdefault(mid, {'id': mid, 'name': item.get('name', mid), 'need': 0, 'categories': []})
                row['need'] += _quantity(item)
                if category not in row['categories']:
                    row['categories'].append(category)
        # A series converts 3:1 and 1:3, so stock of its other tiers counts too: keep what the answer reports of them.
        series = {}
        for mid, row in merged.items():
            info = materials.meta('zzz', mid)
            if info.get('kind') in materials.ZZZ_SERIES and info.get('group'):
                series.setdefault(info['group'], row['categories'])
        for mid, info in materials.dataset('zzz').get('materials', {}).items():
            if info.get('group') in series and info.get('kind') in materials.ZZZ_SERIES and mid in owns and mid not in merged:
                merged[mid] = {'id': mid, 'name': info.get('name', mid), 'need': 0, 'categories': list(series[info['group']])}
        rows = []
        for mid, row in merged.items():
            owned = _count(owns[mid]) if mid in owns else None
            rows.append({**row, 'category': row['categories'][0], 'owned': owned,
                         'remaining': max(0, row['need'] - owned) if owned is not None else None})
        return rows

    if not accounts().get(game):
        raise ValueError(tr('login_first'))
    return run(genshin_calc if game == 'genshin' else zzz_calc, 90)
