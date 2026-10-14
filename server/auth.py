"""One Miyoushe app QR grant for every game and data source.

Web cookies are derived from the app grant before replacing a working login, and derived again
when they lapse. Only public QR progress leaves this module; tokens stay in encrypted storage.
"""
from __future__ import annotations

import asyncio
import hashlib
import io
import json
import logging
import re
import threading
import time
import uuid
from urllib.parse import urlsplit

import aiohttp
import genshin
from genshin.utility.ds import get_ds_headers

from . import core
from .i18n import tr

log = logging.getLogger('gcl.auth')
APP_VERSION = '2.115.0'  # current Miyoushe app (Snap Hutao Remastered and TeyvatGuide, October 2026)
CREATE = 'https://passport-api.mihoyo.com/account/ma-cn-passport/app/createQRLogin'
QUERY = 'https://passport-api.mihoyo.com/account/ma-cn-passport/app/queryQRLoginStatus'
LTOKEN = 'https://passport-api.mihoyo.com/account/auth/api/getLTokenBySToken'
COOKIE = 'https://passport-api.mihoyo.com/account/auth/api/getCookieAccountInfoBySToken'
WIDGETS = {
    'genshin': 'https://api-takumi-record.mihoyo.com/game_record/app/genshin/aapi/widget/v2',
    'zzz': 'https://api-takumi-record.mihoyo.com/event/game_record_zzz/api/zzz/widget',
}
QR: dict = {'status': 'idle'}
RENEW_SECONDS = 600
RENEW_LOCK = threading.Lock()
RENEWED: dict = {}  # login binding -> (monotonic time, success) of its last cookie renewal


def binding(game: str | None = None) -> str:
    """Bind asynchronous results to the installed login and, optionally, its selected role.
    Each QR login is a new generation; renewing its website cookies keeps it."""
    saved = core.load_secret('mihoyo')
    value = [(saved.get('app') or {}).get('aid'), saved.get('generation')]
    if game is not None:
        value.append(saved.get('accounts', {}).get(game))
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def credentials() -> dict:
    saved = core.load_secret('mihoyo')
    app = saved.get('app') or {}
    cookies = saved.get('cookies') or {}
    ids = {str(cookies[k]) for k in ('ltuid', 'ltuid_v2', 'account_id', 'account_id_v2') if cookies.get(k)}
    return app if app.get('stoken') and ids == {app.get('aid')} else {}


def state() -> dict:
    with core.LOCK:
        return {k: QR[k] for k in ('status', 'reason', 'svg', 'at') if k in QR}


def cancel() -> None:
    with core.LOCK:
        QR.clear()
        QR['status'] = 'idle'


def identity() -> dict:
    from . import mihoyo
    device = mihoyo.device()
    headers = {'User-Agent': genshin.Client.USER_AGENT, 'x-rpc-app_version': APP_VERSION,
               'x-rpc-device_id': device['id'], 'Referer': 'https://webstatic.mihoyo.com/',
               'Origin': 'https://webstatic.mihoyo.com'}
    if device.get('fp'):
        headers['x-rpc-device_fp'] = device['fp']
    return headers


async def exchange(url: str, headers: dict, *, body: dict | None = None,
                   cookies: dict | None = None, params: dict | None = None) -> dict:
    if url not in (CREATE, QUERY, LTOKEN, COOKIE, *WIDGETS.values()):
        raise ValueError(tr('unknown_api'))
    # Credentials may only reach these exact official endpoints, never a redirect.
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20),
                                     cookie_jar=aiohttp.DummyCookieJar()) as session:
        async with session.request('GET' if body is None else 'POST', url, headers=headers,
                                   json=body, params=params, cookies=cookies, allow_redirects=False) as response:
            if response.status != 200:
                raise OSError('Miyoushe HTTP ' + str(response.status))
            payload = await response.json()
    if not isinstance(payload, dict) or type(payload.get('retcode')) is not int:
        raise ValueError(tr('bad_response'))
    if payload['retcode'] != 0:
        # Response bodies and request URLs can contain tickets or account information.
        raise genshin.GenshinException({'retcode': payload['retcode'], 'message': ''})
    if not isinstance(payload.get('data'), dict):
        raise ValueError(tr('bad_response'))
    return payload['data']


def parse_grant(value: dict, headers: dict) -> dict:
    info, tokens = value.get('user_info'), value.get('tokens')
    if value.get('need_realperson'):
        raise ValueError(tr('login_realperson'))
    if not isinstance(info, dict) or not isinstance(tokens, list):
        raise ValueError(tr('bad_response'))
    aid = str(info.get('aid') or info.get('uid') or '')
    candidates = [v.get('token') for v in tokens if isinstance(v, dict)
                  and (str(v.get('token_type')) == '1' or v.get('name') in ('stoken', 'stoken_v2'))]
    mid = info.get('mid')
    if (not re.fullmatch(r'[0-9]{1,20}', aid) or len(candidates) != 1
            or not isinstance(candidates[0], str)
            or not re.fullmatch(r'v2_[A-Za-z0-9._~+/%=-]{20,8192}', candidates[0])
            or not isinstance(mid, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,100}', mid)):
        raise ValueError(tr('login_token'))
    return {'aid': aid, 'mid': mid, 'stoken': candidates[0], 'identity': dict(headers)}


async def derive_cookies(grant: dict) -> dict:
    """Use the CN Passport endpoints; the SDK's generic v2 exchange is overseas-only."""
    auth_cookies = {k: grant[v] for k, v in (('stuid', 'aid'), ('stoken', 'stoken'), ('mid', 'mid'))}
    params = {'stoken': grant['stoken']}
    results = []
    for url, client_type in ((LTOKEN, '5'), (COOKIE, '2')):
        headers = {**get_ds_headers(genshin.Region.CHINESE, params=params), **grant['identity'],
                   'x-rpc-app_id': 'bll8iq97cem8', 'x-rpc-client_type': client_type}
        results.append(await exchange(url, headers, cookies=auth_cookies, params=params))
    lt, ct = results
    # The LToken response normally has no UID; CookieToken must confirm the grant owner.
    if str(ct.get('uid')) != grant['aid'] or ('uid' in lt and str(lt['uid']) != grant['aid']):
        raise ValueError(tr('login_account'))
    for row, key in ((lt, 'ltoken'), (ct, 'cookie_token')):
        if not isinstance(row.get(key), str) or not re.fullmatch(r'[A-Za-z0-9._~+/%=-]{16,8192}', row[key]):
            raise ValueError(tr('qr_no_cookies'))
    cookies = {'ltoken': lt['ltoken'], 'ltuid': grant['aid'],
               'cookie_token': ct['cookie_token'], 'account_id': grant['aid']}
    for token, owner, mid in (('ltoken', 'ltuid', 'ltmid'), ('cookie_token', 'account_id', 'account_mid')):
        if cookies[token].startswith('v2_'):
            cookies.update({token + '_v2': cookies[token], owner + '_v2': grant['aid'], mid + '_v2': grant['mid']})
    return cookies


async def prepare(grant: dict) -> tuple[dict, dict]:
    from . import mihoyo
    cookies = await derive_cookies(grant)
    c = genshin.Client(cookies=cookies, region=genshin.Region.CHINESE, lang='zh-cn',
                       device_id=grant['identity']['x-rpc-device_id'],
                       device_fp=grant['identity'].get('x-rpc-device_fp'))
    c.custom_headers.update(grant['identity'])
    found = await asyncio.wait_for(c.get_game_accounts(), 20)
    candidates = {g: [{'uid': str(a.uid), 'server': a.server, 'name': a.nickname, 'server_name': a.server_name}
                      for a in found if a.game == kind] for g, kind in mihoyo.GAMES.items()}
    return cookies, candidates


def install(grant: dict, cookies: dict, candidates: dict, before: str, run_id: str | None = None) -> None:
    """Publish one complete credential bundle only after role discovery succeeds."""
    with core.LOCK:
        if before != binding() or (run_id is not None and QR.get('run') != run_id):
            raise ValueError(tr('login_changed'))
        from . import mihoyo
        old = mihoyo.accounts()
        selected = {}
        for game, choices in candidates.items():
            previous = old.get(game) or {}
            match = next((a for a in choices if (a['uid'], a['server']) ==
                          (previous.get('uid'), previous.get('server'))), None)
            if match or len(choices) == 1:
                selected[game] = match or choices[0]
        core.save_secret('mihoyo', {'cookies': cookies, 'app': grant, 'accounts': selected,
                                   'candidates': candidates, 'at': core.stamp(), 'generation': uuid.uuid4().hex})


def renew() -> bool:
    """Derive fresh website cookies from the app grant after Miyoushe reports them lapsed. True when they are
    fresh: renewed now or by another request within a few minutes. A failure is not retried for a few
    minutes either, so a revoked grant costs one request, not one per read."""
    with RENEW_LOCK:
        grant, before = credentials(), binding()
        if not grant:
            return False
        last = RENEWED.get(before)
        if last and time.monotonic() - last[0] < RENEW_SECONDS:
            return last[1]
        try:
            cookies = asyncio.run(asyncio.wait_for(derive_cookies(grant), 30))
        except Exception as exc:
            log.warning('Website cookie renewal failed: %s (code %s)', type(exc).__name__, getattr(exc, 'retcode', None))
            cookies = None
        with core.LOCK:
            ok = cookies is not None and before == binding()
            if ok:
                core.save_secret('mihoyo', {**core.load_secret('mihoyo'), 'cookies': cookies})
        RENEWED[before] = (time.monotonic(), ok)
        if ok:
            log.info('Renewed the website cookies from the app grant')
        return ok


def start() -> dict:
    with core.LOCK:
        if QR.get('status') in ('creating', 'waiting', 'scanned', 'reading'):
            return state()
        pending = {'run': uuid.uuid4().hex, 'binding': binding()}
        QR.clear()
        QR.update(status='creating', run=pending['run'], at=core.stamp(), reason=tr('login_creating'))
        threading.Thread(target=_worker, args=(pending,), daemon=True, name='qr-login').start()
        return state()


def _update(pending: dict, **values) -> bool:
    with core.LOCK:
        if QR.get('run') != pending['run']:
            return False
        if pending['binding'] != binding():
            QR.update(status='error', reason=tr('login_changed'))
            QR.pop('svg', None)
            return False
        QR.update(values)
        if 'status' in values and values['status'] not in ('waiting', 'scanned'):
            QR.pop('svg', None)
        return True


def _worker(pending: dict) -> None:
    from . import mihoyo
    import qrcode
    import qrcode.image.svg

    async def flow():
        await mihoyo._ensure_fp()
        base = identity()
        headers = {**base, 'x-rpc-app_id': 'bll8iq97cem8', 'x-rpc-game_biz': 'bbs_cn', 'x-rpc-client_type': '3'}
        value = await exchange(CREATE, headers, body={})
        url, ticket = value.get('url'), value.get('ticket')
        parsed = urlsplit(url) if isinstance(url, str) else None
        if (not parsed or parsed.scheme != 'https' or not parsed.hostname
                or not (parsed.hostname in ('mihoyo.com', 'miyoushe.com')
                        or parsed.hostname.endswith(('.mihoyo.com', '.miyoushe.com')))
                or not isinstance(ticket, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,500}', ticket)):
            raise ValueError(tr('bad_response'))
        out = io.BytesIO()
        qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=8, border=2).save(out)
        if not _update(pending, status='waiting', svg=out.getvalue().decode(), reason=tr('qr_scan')):
            return False
        deadline = time.monotonic() + 170
        while time.monotonic() < deadline:
            if not _update(pending):
                return False
            value = await exchange(QUERY, headers, body={'ticket': ticket})
            status = value.get('status')
            if status == 'Confirmed':
                if not _update(pending, status='reading', reason=tr('login_preparing')):
                    return False
                grant = parse_grant(value, base)
                cookies, candidates = await prepare(grant)
                with core.LOCK:
                    install(grant, cookies, candidates, pending['binding'], pending['run'])
                    pending['binding'] = binding()
                return True
            if status in ('Expired', 'Timeout'):
                break
            if status not in ('Created', 'Init', 'Scanned'):
                raise ValueError(tr('bad_response'))
            if status == 'Scanned':
                _update(pending, status='scanned', reason=tr('qr_scanned'))
            await asyncio.sleep(3)
        _update(pending, status='expired', reason=tr('qr_expired'))
        return False

    try:
        if asyncio.run(flow()):
            errors = []
            for game in mihoyo.accounts():
                if not _update(pending):
                    return
                result = mihoyo.refresh_notes(game, force=True)
                if result.get('error'):
                    errors.append(tr('game_' + game) + ': ' + result['error'])
            _update(pending, status='confirmed', reason=tr('login_ready') if not errors else
                    tr('login_partial', detail='; '.join(errors)))
    except Exception as exc:
        expired = getattr(exc, 'retcode', None) in (-3501, -106)
        _update(pending, status='expired' if expired else 'error',
                reason=tr('qr_expired') if expired else mihoyo.describe_error(exc))
