"""Official stamina widgets, read with the shared Miyoushe app grant."""
from __future__ import annotations

import asyncio
import time

import genshin
from genshin.utility.ds import get_ds_headers

from . import auth, mihoyo
from .auth import exchange
from .i18n import tr

ROLE_CHECK_SECONDS = 6 * 3600
ROLE_CHECKS: dict = {}  # game -> (login binding, monotonic time) of the last live role lookup that matched


async def note(game: str = 'genshin') -> tuple[int, int]:
    """Stamina of the selected role. The caller discards it if the login or role changes meanwhile."""
    if game not in auth.WIDGETS:
        raise ValueError(tr('unknown_api'))
    login = auth.binding(game)  # read first, so a check cached under it covers only what is read next
    saved = auth.credentials()
    selected = mihoyo.accounts().get(game)
    if not saved or not selected:
        raise ValueError(tr('login_first'))
    headers = {**get_ds_headers(genshin.Region.CHINESE), **saved['identity'], 'x-rpc-client_type': '5'}
    value = await exchange(auth.WIDGETS[game], headers, cookies={k: saved[v] for k, v in
                           (('stuid', 'aid'), ('stoken', 'stoken'), ('mid', 'mid'))})
    uid, region = value.get('uid') or value.get('role_id'), value.get('server') or value.get('region')
    if uid is not None:
        if str(uid) != str(selected['uid']) or region != selected['server']:
            raise ValueError(tr('widget_role'))
    else:
        await check_role(game, selected, login)
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


async def check_role(game: str, selected: dict, login: str) -> None:
    """Widgets can ignore role parameters, so an unlabelled value is the selected role's only when the account
    has exactly one role in this game. A match holds for a few hours, until the login or the selection changes."""
    checked = ROLE_CHECKS.get(game)
    if checked and checked[0] == login and time.monotonic() - checked[1] < ROLE_CHECK_SECONDS:
        return
    roles = await asyncio.wait_for(mihoyo.client(game).get_game_accounts(), 20)
    choices = [r for r in roles if r.game == mihoyo.GAMES[game]]
    if (len(choices) != 1 or str(choices[0].uid) != str(selected['uid'])
            or choices[0].server != selected['server']):
        raise ValueError(tr('widget_role'))
    ROLE_CHECKS[game] = (login, time.monotonic())
