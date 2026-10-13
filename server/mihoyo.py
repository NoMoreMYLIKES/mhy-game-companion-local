"""Part ① – official data: QR login, accounts, stamina notes, character state, calculators.

Only official Miyoushe (米游社, CN-server HoYoLAB) endpoints through genshin.py. Credentials are DPAPI-encrypted
on Windows; on Linux only file permissions protect them.
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
from genshin.models.genshin.calculator import CalculatorBatchResult

from . import assets, core
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
    if code is None:  # a fault here or in genshin.py, not an API answer: the class name alone cannot be diagnosed
        log.error('Unexpected %s in a Miyoushe request', name, exc_info=exc)
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
            try:
                state, jar = await asyncio.wait_for(c._check_qrcode(creation.ticket), 15)
            except genshin.GenshinException as exc:
                if exc.retcode == -3501:  # the code expired on Miyoushe's side first
                    break
                raise
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


def record(key: str, ok: bool, reason: str = '', captcha: bool = False) -> None:
    h = health(key)
    if ok:
        h = {'ok': True, 'at': core.stamp(), 'reason': reason, 'failures': 0}
    else:
        failures = int(h.get('failures', 0)) + 1
        delay = min(6 * 3600, 900 * 2 ** min(failures - 1, 5))
        h = {'ok': False, 'at': core.stamp(), 'reason': reason, 'failures': failures, 'captcha': captcha,
             'retry_at': core.stamp(core.now() + timedelta(seconds=delay))}
        if reason in MESSAGES['err_login_expired'] and failures == 1:  # either language
            from . import notify
            notify.event('login', tr('login_expired_title'), [reason])
    core.put('health:' + key, h)


# ---------------------------------------------------------------- stamina notes

def refresh_notes(game: str, force: bool = False, challenge: str | None = None) -> dict:
    """Read the stamina from Real-Time Notes; challenge is the token of a solved captcha (finish_verification)."""
    key = 'notes-' + game
    account = accounts().get(game)
    if not account or not logged_in():
        return {'error': tr('not_logged_in')}
    if not allowed(key, force):
        return {'error': health(key).get('reason', tr('backing_off')), 'deferred': True}

    async def read():
        await _ensure_fp()
        c = _verification_client(game, challenge) if challenge else client(game)
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
        core.add_sample(game, current, cap, 'source_notes')  # message key, translated when shown
        record(key, True, tr('notes_ok'))
        return {'current': current, 'cap': cap}
    except Exception as exc:
        reason = describe_error(exc)
        record(key, False, reason, captcha=getattr(exc, 'retcode', None) in CAPTCHA_CODES)
        return {'error': reason}


# ---------------------------------------------------------------- human verification
# Real-Time Notes answers 1034 (or another Geetest code) when Miyoushe wants a person to confirm the request.
# The dashboard then shows Miyoushe's own Geetest captcha; the person solves it, the answer goes back to
# Miyoushe, and the notes are read again with the token it returns. Nothing is solved automatically.
# These three requests identify as the game-record page of the current Miyoushe app, the page that shows
# this captcha, as gsuid_core and Snap Hutao send them. Sent from a VPS, solved answers were refused with
# 10306 both with genshin.py's defaults (app version 2.11.1 from 2021, a desktop browser) and with these.

CAPTCHA_CODES = genshin.constants.GEETEST_RETCODES
CARD_WAPI = 'https://api-takumi-record.mihoyo.com/game_record/app/card/wapi/'
APP_VERSION = '2.115.0'  # current Miyoushe app (Snap Hutao Remastered and TeyvatGuide, October 2026)
VERIFY_HEADERS = {
    'User-Agent': ('Mozilla/5.0 (Linux; Android 13; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 '
                   f'Chrome/126.0.0.0 Mobile Safari/537.36 miHoYoBBS/{APP_VERSION}'),
    'x-rpc-app_version': APP_VERSION, 'X-Requested-With': 'com.mihoyo.hyperion',
    'Referer': 'https://webstatic.mihoyo.com/', 'Origin': 'https://webstatic.mihoyo.com',
}
CHALLENGE = {  # each game's record page and the request its verification is for
    'genshin': {'x-rpc-challenge_game': '2', 'x-rpc-page': 'v4.1.5-ys_#ys', 'x-rpc-tool-verison': 'v4.1.5-ys',
                'x-rpc-challenge_path': 'https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/dailyNote'},
    'zzz': {'x-rpc-challenge_game': '8', 'x-rpc-page': 'v1.0.14_#/zzz', 'x-rpc-tool-verison': 'v1.0.14-zzz',
            'x-rpc-challenge_path': 'https://api-takumi-record.mihoyo.com/event/game_record_zzz/api/zzz/note'},
}  # "verison" (sic) is how the page spells it


def _verification_client(game: str, challenge: str | None = None) -> genshin.Client:
    """A client for the verification requests; with challenge, for the request the solved captcha unlocks."""
    c = client(game)
    c.custom_headers.update({**VERIFY_HEADERS, **CHALLENGE[game]})  # custom headers win over genshin.py's
    if challenge:
        c.custom_headers['x-rpc-challenge'] = challenge
    return c


def start_verification(game: str) -> dict:
    """A captcha for this account, created by Miyoushe, for the dashboard to show."""
    if game not in CHALLENGE or not accounts().get(game) or not logged_in():
        raise ValueError(tr('login_first'))

    async def create():
        await _ensure_fp()
        try:
            return await _verification_client(game).request_hoyolab(CARD_WAPI + 'createVerification',
                                                                    params={'is_high': 'false'})
        except genshin.errors.DailyGeetestTriggered as exc:  # genshin.py raises on any answer that holds a captcha
            return {'gt': exc.gt, 'challenge': exc.challenge, 'new_captcha': True}

    data = run(create(), 30)
    if not data.get('gt') or not data.get('challenge'):
        raise ValueError(tr('captcha_unavailable'))
    return {'gt': str(data['gt']), 'challenge': str(data['challenge']), 'new_captcha': bool(data.get('new_captcha', True))}


def finish_verification(game: str, answer: dict) -> dict:
    """Send the person's captcha answer to Miyoushe, then read the notes again with the token it returns."""
    fields = {k: answer.get(k) for k in ('geetest_challenge', 'geetest_validate', 'geetest_seccode')}
    if game not in CHALLENGE or not all(isinstance(v, str) and 0 < len(v) <= 200 for v in fields.values()):
        raise ValueError(tr('captcha_incomplete'))

    async def verify():
        return await _verification_client(game).request_hoyolab(CARD_WAPI + 'verifyVerification', method='POST',
                                                                data=fields)

    try:
        token = run(verify(), 30).get('challenge')
    except genshin.GenshinException as exc:
        log.warning('Miyoushe refused a captcha answer: retcode %s, message %r', exc.retcode, exc.original)
        raise ValueError(tr('captcha_refused', code=exc.retcode)) from exc
    if not token:
        raise ValueError(tr('captcha_rejected'))
    log.info('Miyoushe accepted a captcha answer for %s', game)
    return refresh_notes(game, force=True, challenge=str(token))


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
                 'icon': getattr(x, 'square_icon', ''), 'element': str(getattr(x, 'element', '')),
                 'rarity': str(getattr(x, 'rarity', ''))} for x in agents if not getattr(x, 'is_teaser', False)]

    if not accounts().get(game):
        raise ValueError(tr('login_first'))
    rows = run(read(), 60)
    _collect_icons({assets.key(game, 'character', r['id']): r.get('icon') for r in rows})
    return rows


def _collect_icons(sources: dict) -> None:
    """Images are a convenience: never let them break the official data flow."""
    try:
        assets.collect(sources)
    except Exception:
        log.exception('Image cache update failed')


def observe(goal: dict) -> dict:
    """Current levels from the official cultivation tools (never guessed)."""
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
            return result
        guide = (await c.get_zzz_agent_upgrade_guide(cid))[0]
        _collect_icons({assets.key(game, 'character', cid): getattr(guide.avatar, 'square_icon', None)})
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
        wanted = [k for k in talents if talents[k] > int(cur.get(k, 1))]
        group_ids = goal.get('talent_groups') or {}
        if any(k not in group_ids for k in wanted):  # goals observed before the group ids were kept
            row = next((x for x in await _genshin_avatars(c) if x.get('id') == cid), None)
            if row is None:
                raise ValueError(tr('char_not_owned'))
            group_ids = {k: t['group'] for k, t in _talents(row).items()}
        for k in wanted:
            if k not in group_ids:
                raise ValueError(tr('calc_format'))
            b.add_talent(group_ids[k], int(cur.get(k, 1)), talents[k])
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
                if isinstance(item.get('icon'), str):
                    _collect_icons({assets.key(game, 'material', mid): item['icon']})
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
