"""Official stamina widgets sharing one Miyoushe app authorization."""
from __future__ import annotations

import asyncio
import hashlib
import json

import genshin
from genshin.utility.ds import get_ds_headers

from . import auth, core, mihoyo
from .auth import exchange
from .i18n import tr

WIDGET = auth.WIDGETS['genshin']


def legacy_credentials() -> dict:
    """Read the previous separate grant only while its exact login and role still match."""
    saved = core.load_secret('widget')
    account = mihoyo.accounts().get('genshin') or {}
    cookies = mihoyo.cookies()
    raw = {'cookies': cookies, 'uid': str(account.get('uid')), 'server': account.get('server')}
    binding = hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()
    ids = {str(cookies[k]) for k in ('ltuid_v2', 'account_id_v2', 'ltuid', 'account_id') if cookies.get(k)}
    valid = (saved.get('binding') == binding and ids == {saved.get('aid')}
             and isinstance(saved.get('stoken'), str) and saved['stoken'].startswith('v2_')
             and isinstance(saved.get('mid'), str) and isinstance(saved.get('identity'), dict)
             and saved['identity'].get('x-rpc-device_id'))
    return saved if valid else {}


def credentials() -> dict:
    return auth.credentials() or legacy_credentials()


def available() -> bool:
    return bool(credentials())


def state() -> dict:
    return {'connected': available(), 'unified': bool(auth.credentials())}


def clear() -> None:
    """Remove only the obsolete separate grant; unified credentials belong to login."""
    core.save_secret('widget', {})


async def note(game: str = 'genshin') -> tuple[int, int]:
    if game not in auth.WIDGETS:
        raise ValueError(tr('unknown_api'))
    saved = credentials()
    selected = mihoyo.accounts().get(game)
    before = auth.binding(game)
    if not saved or not selected:
        raise ValueError(tr('widget_needed'))
    headers = {**get_ds_headers(genshin.Region.CHINESE), **saved['identity'], 'x-rpc-client_type': '5'}
    value = await exchange(auth.WIDGETS[game], headers, cookies={k: saved[v] for k, v in
                           (('stuid', 'aid'), ('stoken', 'stoken'), ('mid', 'mid'))})
    uid, region = value.get('uid') or value.get('role_id'), value.get('server') or value.get('region')
    if uid is not None:
        if str(uid) != str(selected['uid']) or region != selected['server']:
            raise ValueError(tr('widget_role'))
    else:
        # Widgets can ignore role parameters. An unlabelled value is safe only when
        # the grant has exactly one bound role for this game, verified live.
        roles = await asyncio.wait_for(mihoyo.client(game).get_game_accounts(), 20)
        choices = [r for r in roles if r.game == mihoyo.GAMES[game]]
        if (len(choices) != 1 or str(choices[0].uid) != str(selected['uid'])
                or choices[0].server != selected['server']):
            raise ValueError(tr('widget_role'))
    if saved != credentials() or before != auth.binding(game):
        raise ValueError(tr('login_changed'))
    if game == 'genshin':
        current, cap = value.get('current_resin'), value.get('max_resin')
    else:
        energy = value.get('energy')
        progress = energy.get('progress') if isinstance(energy, dict) else None
        if not isinstance(progress, dict):
            raise ValueError(tr('bad_notes'))
        current, cap = progress.get('current'), progress.get('max')
    if type(current) is not int or type(cap) is not int or not 0 <= current <= cap <= 10000 or cap <= 0:
        raise ValueError(tr('bad_notes'))
    return current, cap
