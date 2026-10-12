"""Part ① – official data: QR login, accounts, stamina notes, character state, calculators.

Only official Miyoushe (米游社, CN-server HoYoLAB) endpoints through genshin.py. Credentials are DPAPI-encrypted.
A failed read never becomes 0: callers receive an error and keep the previous value.
"""
from __future__ import annotations

import asyncio
import io
import logging
import random
import threading
import time
import uuid
from datetime import timedelta

import genshin

from . import core
from .i18n import MESSAGES, tr

log = logging.getLogger('gcl.mihoyo')
GAMES = {'genshin': genshin.Game.GENSHIN, 'zzz': genshin.Game.ZZZ}
SKILLS = {'attack': 0, 'special': 1, 'dodge': 2, 'chain': 3, 'core': 5, 'assist': 6}
QR: dict = {'status': 'idle'}
QR_LOCK = threading.Lock()


def run(coro, timeout: float = 60):
    return asyncio.run(asyncio.wait_for(coro, timeout))


def cookies() -> dict:
    return core.load_secret('mihoyo').get('cookies', {})


def accounts() -> dict:
    return core.get('accounts', {})


def logged_in() -> bool:
    return bool(cookies())


def describe_error(exc: Exception) -> str:
    code = getattr(exc, 'retcode', None)
    name = type(exc).__name__
    if code in (-100, 10001, -10001) or 'Cookie' in name:
        return tr('err_login_expired')
    if code in (1034, 10035, 5003, 10041) or 'Geetest' in name:
        return tr('err_captcha', code=code)
    if code in (10102, 10103) or 'Private' in name:
        return tr('err_private')
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError, OSError)) or 'Timeout' in name or 'Connect' in name:
        return tr('err_network')
    if isinstance(exc, ValueError):
        return str(exc)[:200]
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
    for name, account in accounts().items():
        if name in GAMES and account:
            c.uids[GAMES[name]] = int(account['uid'])
    return c


# ---------------------------------------------------------------- QR login

def qr_state() -> dict:
    with QR_LOCK:
        return dict(QR)


def start_login() -> dict:
    with QR_LOCK:
        if QR.get('status') in ('creating', 'waiting', 'scanned'):
            return dict(QR)
        QR.clear()
        QR.update(status='creating', at=core.stamp())
    threading.Thread(target=_login_worker, daemon=True, name='qr-login').start()
    return qr_state()


def _login_worker() -> None:
    import qrcode
    import qrcode.image.svg

    async def flow():
        await _ensure_fp()
        c = genshin.Client(region=genshin.Region.CHINESE, lang='zh-cn')
        creation = await asyncio.wait_for(c._create_qrcode(), 20)
        out = io.BytesIO()
        qrcode.make(creation.url, image_factory=qrcode.image.svg.SvgPathImage, box_size=8, border=2).save(out)
        with QR_LOCK:
            QR.update(status='waiting', svg=out.getvalue().decode(), reason=tr('qr_scan'))
        deadline = time.monotonic() + 170
        while time.monotonic() < deadline:
            state, jar = await asyncio.wait_for(c._check_qrcode(creation.ticket), 15)
            if state.value == 'Confirmed':
                values = {k: v.value for k, v in jar.items()}
                if not values:
                    raise ValueError(tr('qr_no_cookies'))
                core.save_secret('mihoyo', {'cookies': values, 'at': core.stamp()})
                with QR_LOCK:
                    QR.update(status='confirmed', reason=tr('qr_confirmed'))
                    QR.pop('svg', None)
                await discover_accounts()
                with QR_LOCK:
                    QR['reason'] = tr('qr_done')
                return
            if state.value == 'Scanned':
                with QR_LOCK:
                    QR.update(status='scanned', reason=tr('qr_scanned'))
            await asyncio.sleep(3)
        with QR_LOCK:
            QR.update(status='expired', reason=tr('qr_expired'))
            QR.pop('svg', None)

    try:
        asyncio.run(flow())
    except Exception as exc:
        log.exception('QR login failed')
        with QR_LOCK:
            QR.update(status='error', reason=describe_error(exc))
            QR.pop('svg', None)


async def discover_accounts() -> dict:
    c = client()
    found = await asyncio.wait_for(c.get_game_accounts(), 20)
    candidates = {g: [{'uid': str(a.uid), 'server': a.server, 'name': a.nickname, 'server_name': a.server_name}
                      for a in found if a.game == kind] for g, kind in GAMES.items()}
    core.put('account_candidates', candidates)
    selected = accounts()
    for g, choices in candidates.items():
        if len(choices) == 1:
            selected[g] = choices[0]
        elif not any(a['uid'] == (selected.get(g) or {}).get('uid') for a in choices):
            selected.pop(g, None)
    core.put('accounts', selected)
    return candidates


def select_account(game: str, uid: str) -> None:
    choice = next((a for a in core.get('account_candidates', {}).get(game, []) if a['uid'] == str(uid)), None)
    if not choice:
        raise ValueError(tr('account_not_listed'))
    value = accounts()
    value[game] = choice
    core.put('accounts', value)


def logout() -> None:
    core.save_secret('mihoyo', {})
    core.put('accounts', {})


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
             'retry_at': core.stamp(core.now() + timedelta(seconds=delay))}
        if reason in MESSAGES['err_login_expired'] and failures == 1:  # either language
            from . import notify
            notify.event('login', tr('login_expired_title'), [reason])
    core.put('health:' + key, h)


# ---------------------------------------------------------------- stamina notes

def refresh_notes(game: str, force: bool = False) -> dict:
    key = 'notes-' + game
    account = accounts().get(game)
    if not account or not logged_in():
        return {'error': tr('not_logged_in')}
    if not allowed(key, force):
        return {'error': health(key).get('reason', tr('backing_off')), 'deferred': True}

    async def read():
        await _ensure_fp()
        c = client(game)
        uid = int(account['uid'])
        if game == 'genshin':
            n = await c.get_genshin_notes(uid, autoauth=False)
            return n.current_resin, n.max_resin
        n = await c.get_zzz_notes(uid, autoauth=False)
        return n.battery_charge.current, n.battery_charge.max

    try:
        current, cap = run(read(), 40)
        if type(current) is not int or type(cap) is not int or not 0 <= current <= 10000:
            raise ValueError(tr('bad_notes'))
        core.add_sample(game, current, cap, tr('source_notes'))
        record(key, True, tr('notes_ok'))
        return {'current': current, 'cap': cap}
    except Exception as exc:
        reason = describe_error(exc)
        record(key, False, reason)
        return {'error': reason}


# ---------------------------------------------------------------- roster and character state

def roster(game: str) -> list[dict]:
    async def read():
        c = client(game)
        if game == 'genshin':
            chars = await c.get_calculator_characters(sync=True)
            return [{'id': str(x.id), 'name': x.name, 'level': x.level, 'owned': True, 'icon': x.icon,
                     'element': x.element, 'rarity': x.rarity} for x in chars if x.level > 0]
        await c._login_upgrade_guide(int(accounts()['zzz']['uid']))
        agents = await c.get_zzz_upgrade_guide_agents()
        return [{'id': str(x.id), 'name': x.name, 'owned': bool(getattr(x, 'unlocked', True)),
                 'icon': getattr(x, 'square_icon', ''), 'element': str(getattr(x, 'element', '')),
                 'rarity': str(getattr(x, 'rarity', ''))} for x in agents if not getattr(x, 'is_teaser', False)]

    if not accounts().get(game):
        raise ValueError(tr('login_first'))
    return run(read(), 60)


def observe(goal: dict) -> dict:
    """Current levels from the official cultivation tools (never guessed)."""
    game, cid = goal['game'], int(goal['character_id'])

    async def read():
        await _ensure_fp()
        c = client(game)
        if game == 'genshin':
            chars = await c.get_calculator_characters(sync=True)
            char = next((x for x in chars if x.id == cid and x.level > 0), None)
            if char is None:
                raise ValueError(tr('char_not_owned'))
            detail = await c.get_character_details(cid)
            current = {'level': char.level, 'weapon': detail.weapon.level}
            current.update({t.type: t.level for t in detail.talents if t.type in ('attack', 'skill', 'burst')})
            return {'current': current, 'weapon_id': str(detail.weapon.id), 'weapon_name': getattr(detail.weapon, 'name', '')}
        await c._login_upgrade_guide(int(accounts()['zzz']['uid']))
        guide = (await c.get_zzz_agent_upgrade_guide(cid))[0]
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
        return result

    return run(read(), 60)


# ---------------------------------------------------------------- calculators

def calculate(goal: dict) -> list[dict]:
    """Official requirement rows: need, owned (ZZZ) and remaining (official gap)."""
    game, cid = goal['game'], int(goal['character_id'])
    cur, tgt = goal.get('current', {}), goal.get('target', {})

    async def genshin_calc():
        c = client(game)
        b = c.calculator().set_character(cid, int(cur.get('level', 1)), int(tgt.get('level', 1)))
        if int(tgt.get('weapon', 0)) > int(cur.get('weapon', 0)):
            if not goal.get('weapon_id'):
                raise ValueError(tr('weapon_needed'))
            b.set_weapon(int(goal['weapon_id']), int(cur.get('weapon', 1)), int(tgt['weapon']))
        talents = {k: int(tgt.get(k, 1)) for k in ('attack', 'skill', 'burst')}
        if any(talents[k] > int(cur.get(k, 1)) for k in talents):
            detail = await c.get_character_details(cid)
            for t in detail.talents:
                if t.type in talents and talents[t.type] > int(cur.get(t.type, 1)):
                    b.add_talent(t.group_id, int(cur.get(t.type, 1)), talents[t.type])
        result = await c.batch_calculator().add_character(b).calculate()
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
        rows = []
        for item in result.total_materials:
            extra = info.get(str(item.id), {'categories': ['level']})
            rows.append({'id': str(item.id), 'name': item.name, 'need': int(item.amount), 'owned': None,
                         'remaining': int(item.lacking) if result.has_user_info else None,
                         'category': extra['categories'][0], **extra})
        return rows

    async def zzz_calc():
        c = client(game)
        uid = accounts()['zzz']['uid']
        await c._login_upgrade_guide(int(uid))
        skills = [{'skill_type': kind, 'level': int(tgt.get(k, 1)), 'init_level': int(cur.get(k, 1))}
                  for k, kind in SKILLS.items()]
        bounds = [10, 20, 30, 40, 50]
        wlevel = int(cur.get('weapon', 0))
        body = {'avatar_id': cid, 'avatar_level': int(tgt.get('level', 1)),
                'avatar_current_level': int(cur.get('level', 1)),
                'avatar_current_promotes': int(cur.get('promotion', 1 + sum(int(cur.get('level', 1)) > b for b in bounds))),
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
                mid = str(item['id'])
                row = merged.setdefault(mid, {'id': mid, 'name': item.get('name', mid), 'need': 0, 'categories': []})
                row['need'] += int(item.get('num', item.get('amount', 0)))
                if category not in row['categories']:
                    row['categories'].append(category)
        rows = []
        for mid, row in merged.items():
            owned = int(owns[mid]) if mid in owns else None
            rows.append({**row, 'category': row['categories'][0], 'owned': owned,
                         'remaining': max(0, row['need'] - owned) if owned is not None else None})
        return rows

    if not accounts().get(game):
        raise ValueError(tr('login_first'))
    return run(genshin_calc() if game == 'genshin' else zzz_calc(), 90)
