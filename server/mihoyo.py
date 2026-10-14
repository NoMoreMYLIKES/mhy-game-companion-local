"""Official data: QR login, accounts, stamina notes, character state, calculators.

Only official Miyoushe (CN-server HoYoLAB) endpoints. Credentials are DPAPI-encrypted
on Windows; on Linux only file permissions protect them.
A failed read never becomes 0: callers receive an error and keep the previous value.
"""
from __future__ import annotations

import asyncio
import logging
import random
import re
import secrets
import uuid
from datetime import timedelta

import genshin
from genshin.models.genshin.calculator import CalculatorBatchResult

from . import assets, auth, core, gear
from .i18n import MESSAGES, tr

log = logging.getLogger('gcl.mihoyo')
GAMES = {'genshin': genshin.Game.GENSHIN, 'zzz': genshin.Game.ZZZ}
SKILLS = {'attack': 0, 'special': 1, 'dodge': 2, 'chain': 3, 'core': 5, 'assist': 6}


def run(coro, timeout: float = 60):
    return asyncio.run(asyncio.wait_for(coro, timeout))


def cookies() -> dict:
    return core.load_secret('mihoyo').get('cookies', {})


def accounts() -> dict:
    return core.load_secret('mihoyo').get('accounts', core.get('accounts', {}))


def account_candidates() -> dict:
    return core.load_secret('mihoyo').get('candidates', core.get('account_candidates', {}))


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
    if type(exc) is ValueError:
        return str(exc)[:200]
    if code is None:  # a fault here or in genshin.py, not an API answer: the class name alone cannot be diagnosed
        log.error('Unexpected %s in a Miyoushe request', name)
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


# ---------------------------------------------------------------- QR login

def qr_state() -> dict:
    return auth.state()


def start_login() -> dict:
    return auth.start()


async def discover_accounts() -> dict:
    before = auth.binding()
    c = client()
    found = await asyncio.wait_for(c.get_game_accounts(), 20)
    candidates = {g: [{'uid': str(a.uid), 'server': a.server, 'name': a.nickname, 'server_name': a.server_name}
                      for a in found if a.game == kind] for g, kind in GAMES.items()}
    with core.LOCK:
        if before != auth.binding():
            raise ValueError(tr('login_changed'))
        selected = accounts()
        for g, choices in candidates.items():
            if len(choices) == 1:
                selected[g] = choices[0]
            elif not any((a['uid'], a['server']) == ((selected.get(g) or {}).get('uid'),
                                                    (selected.get(g) or {}).get('server')) for a in choices):
                selected.pop(g, None)
        saved = core.load_secret('mihoyo')
        if saved.get('app'):
            core.save_secret('mihoyo', {**saved, 'accounts': selected, 'candidates': candidates})
        else:
            core.put('account_candidates', candidates)
            core.put('accounts', selected)
    return candidates


def select_account(game: str, uid: str) -> None:
    with core.LOCK:
        choice = next((a for a in account_candidates().get(game, []) if a['uid'] == str(uid)), None)
        if not choice:
            raise ValueError(tr('account_not_listed'))
        value = accounts()
        if value.get(game) != choice:
            PENDING.pop(game, None)
            core.save_secret('verification', {})
        value[game] = choice
        saved = core.load_secret('mihoyo')
        if saved.get('app'):
            core.save_secret('mihoyo', {**saved, 'accounts': value})
        else:
            core.put('accounts', value)


def logout() -> None:
    from . import widget
    with core.LOCK:
        auth.cancel()
        PENDING.clear()
        widget.clear()
        core.save_secret('verification', {})
        core.save_secret('mihoyo', {})
        core.put('accounts', {})
        core.put('account_candidates', {})


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

def notes_key(game: str) -> str:
    from . import widget
    return ('widget-' if widget.available() else 'notes-') + game


def refresh_notes(game: str, force: bool = False, challenge: str | None = None) -> dict:
    """Read the stamina from Real-Time Notes; challenge is the token of a solved captcha (finish_verification)."""
    from . import widget
    key = notes_key(game)
    use_widget = key == 'widget-' + game
    login_binding = auth.binding(game)
    account = accounts().get(game)
    if not account or not logged_in():
        return {'error': tr('not_logged_in')}
    if not allowed(key, force):
        return {'error': health(key).get('reason', tr('backing_off')), 'deferred': True}

    async def read():
        if use_widget:
            return await widget.note(game)
        await _ensure_fp()
        c = _verification_client(game, challenge or _proof(game))
        uid = int(account['uid'])
        if game == 'genshin':
            n = await c.get_genshin_notes(uid, autoauth=False)
            return n.current_resin, n.max_resin
        n = await c.get_zzz_notes(uid, autoauth=False)
        return n.battery_charge.current, n.battery_charge.max

    try:
        current, cap = run(read(), 40)
        if type(current) is not int or type(cap) is not int or not 0 <= current <= cap <= 10000 or cap <= 0:
            raise ValueError(tr('bad_notes'))
        with core.LOCK:
            if login_binding != auth.binding(game) or key != notes_key(game):
                raise ValueError(tr('widget_changed'))
            core.add_sample(game, current, cap, 'source_widget' if use_widget else 'source_notes')
            record(key, True, tr('notes_ok'))
        return {'current': current, 'cap': cap}
    except Exception as exc:
        reason = describe_error(exc)
        with core.LOCK:
            if login_binding == auth.binding(game) and key == notes_key(game):
                record(key, False, reason, captcha=not use_widget and getattr(exc, 'retcode', None) in CAPTCHA_CODES)
        return {'error': reason}


# ---------------------------------------------------------------- human verification
# Real-Time Notes answers 1034 (or another Geetest code) when Miyoushe wants a person to confirm the request.
# The dashboard then shows Miyoushe's own Geetest captcha; the person solves it, the answer goes back to
# Miyoushe, and the notes are read again with the token it returns. Nothing is solved automatically.
# These requests identify as Miyoushe's game-record page. Verification can still be refused
# with 10306; the response does not establish the server-side cause.
# Both games use official widgets when the unified app grant is available.

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


PENDING: dict = {}


def _proof(game: str) -> str | None:
    row = core.load_secret('verification').get(game, {})
    return row.get('challenge') if row.get('binding') == auth.binding(game) else None


def start_verification(game: str) -> dict:
    """Create a challenge bound to this account, role and client cookie jar."""
    if game not in CHALLENGE or not accounts().get(game) or not logged_in():
        raise ValueError(tr('login_first'))
    if notes_key(game) == 'widget-' + game:
        raise ValueError(tr('widget_active'))
    before = auth.binding(game)
    nonce = uuid.uuid4().hex
    with core.LOCK:
        old = PENDING.get(game)
        if old and old['binding'] == before and core.now() < core.parse(old['expires']):
            if 'gt' not in old:
                raise ValueError(tr('captcha_wait'))
            return {k: old[k] for k in ('id', 'gt', 'challenge', 'expires', 'new_captcha')}
        PENDING[game] = {'id': nonce, 'binding': before,
                         'expires': core.stamp(core.now() + timedelta(minutes=5))}

    async def create():
        await _ensure_fp()
        c = _verification_client(game)
        try:
            data = await c.request_hoyolab(CARD_WAPI + 'createVerification', params={'is_high': 'true'})
        except genshin.errors.DailyGeetestTriggered as exc:
            if exc.retcode != 0:
                raise
            data = {'gt': exc.gt, 'challenge': exc.challenge, 'new_captcha': True}
        return c, data

    try:
        c, data = run(create(), 30)
        if not all(isinstance(data.get(k), str) and re.fullmatch(r'[A-Za-z0-9_-]{16,200}', data[k])
                   for k in ('gt', 'challenge')):
            raise ValueError(tr('captcha_unavailable'))
        with core.LOCK:
            if before != auth.binding(game) or (PENDING.get(game) or {}).get('id') != nonce:
                raise ValueError(tr('login_changed'))
            row = PENDING[game]
            row.update(gt=data['gt'], challenge=data['challenge'], client=c, new_captcha=bool(data.get('new_captcha', True)))
            return {k: row[k] for k in ('id', 'gt', 'challenge', 'expires', 'new_captcha')}
    except Exception:
        with core.LOCK:
            if (PENDING.get(game) or {}).get('id') == nonce:
                PENDING.pop(game)
        raise


def finish_verification(game: str, answer: dict) -> dict:
    """Consume a human answer once and persist only the server-issued access proof."""
    if game in GAMES and notes_key(game) == 'widget-' + game:
        return refresh_notes(game, force=True)
    fields = {k: answer.get(k) for k in ('geetest_challenge', 'geetest_validate', 'geetest_seccode')}
    if game not in CHALLENGE or not all(isinstance(v, str) and re.fullmatch(r'[A-Za-z0-9_|-]{1,300}', v)
                                       for v in fields.values()):
        raise ValueError(tr('captcha_incomplete'))
    with core.LOCK:
        row = PENDING.get(game)
        if row and (row['binding'] != auth.binding(game) or core.now() >= core.parse(row['expires'])):
            PENDING.pop(game)
            row = None
        if (not row or row.get('binding') != auth.binding(game) or 'client' not in row
                or not secrets.compare_digest(str(answer.get('id') or ''), row['id'])
                or core.now() >= core.parse(row['expires'])
                or not fields['geetest_challenge'].startswith(row['challenge'][:32])):
            raise ValueError(tr('captcha_session'))
        PENDING.pop(game)
    c = row['client']

    async def verify():
        return await c.request_hoyolab(CARD_WAPI + 'verifyVerification', method='POST', data=fields)

    try:
        token = run(verify(), 30).get('challenge')
    except genshin.GenshinException as exc:
        log.warning('Miyoushe refused a captcha answer: retcode %s', exc.retcode)
        raise ValueError(tr('captcha_refused', code=exc.retcode)) from None
    if not isinstance(token, str) or not re.fullmatch(r'[!-~]{16,4096}', token):
        raise ValueError(tr('captcha_rejected'))
    with core.LOCK:
        if row['binding'] != auth.binding(game):
            raise ValueError(tr('login_changed'))
        updated = dict(c.cookie_manager.cookies)
        # Official risk-control cookies can be necessary for the accepted proof.
        # Preserve this client jar, but never accept a different account owner.
        ids = {str(updated[k]) for k in ('ltuid', 'ltuid_v2', 'account_id', 'account_id_v2') if updated.get(k)}
        previous_ids = {str(cookies()[k]) for k in ('ltuid', 'ltuid_v2', 'account_id', 'account_id_v2') if cookies().get(k)}
        if ids != previous_ids or not all(isinstance(k, str) and isinstance(v, str) for k, v in updated.items()):
            raise ValueError(tr('login_changed'))
        saved = core.load_secret('mihoyo')
        if updated != saved.get('cookies'):
            saved['cookies'] = updated
            core.save_secret('mihoyo', saved)
        proofs = core.load_secret('verification')
        proofs[game] = {'challenge': token, 'binding': auth.binding(game), 'at': core.stamp()}
        core.save_secret('verification', proofs)
    log.info('Miyoushe accepted a captcha answer for %s', game)
    return refresh_notes(game, force=True)


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
    rows = run(read(), 60)
    _collect_icons({assets.key(game, 'character', r['id']): r.get('icon') for r in rows})
    return rows


def _collect_icons(sources: dict) -> None:
    """Images are a convenience: never let them break the official data flow."""
    try:
        assets.collect(sources)
    except Exception:
        log.exception('Image cache update failed')


GEAR_REREAD = timedelta(seconds=60)


async def _genshin_gear(c: genshin.Client, goal: dict, result: dict) -> None:
    """Artifacts of this goal's character only: one extra request (character detail), never for the whole roster.
    Skipped right after a read, and backed off after failures (captchas); levels are read either way."""
    last = core.parse((goal.get('gear') or {}).get('at'))
    if last and core.now() - last < GEAR_REREAD:
        return
    if not allowed('detail'):
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
        record('detail', False, reason, captcha=getattr(exc, 'retcode', None) in CAPTCHA_CODES)
        result['gear_error'] = reason


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
            await _genshin_gear(c, goal, result)
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
