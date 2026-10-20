"""HTTP server: static web UI + JSON API. Loopback by default; LAN needs a password."""
from __future__ import annotations

import base64
import ipaddress
import json
import logging
import mimetypes
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import assets, auth, core, gear, goals, i18n, inventory, materials, mihoyo, notify, planner, runner, scheduler, tools
from .i18n import tr

log = logging.getLogger('gcl.web')
_CHECK: dict = {}
APP_ID = 'game-companion-local'
READY = threading.Event()      # set once recovery and the scheduler have started; until then only health answers
SHUTDOWN = threading.Event()   # set by /api/shutdown; the main thread then exits cleanly
IDENTITY: dict = {}            # instance id, launch token, shutdown token, process creation time
# Python reads MIME types from the Windows registry, which some installs map wrongly
# (e.g. .js as text/plain, which browsers then refuse to run with nosniff).
for _ext, _type in (('.html', 'text/html'), ('.js', 'text/javascript'), ('.css', 'text/css'),
                    ('.svg', 'image/svg+xml'), ('.json', 'application/json'), ('.png', 'image/png'),
                    ('.jpg', 'image/jpeg'), ('.webp', 'image/webp'), ('.gif', 'image/gif'), ('.woff2', 'font/woff2')):
    mimetypes.add_type(_type, _ext)


def env_check() -> dict:
    if time.monotonic() - _CHECK.get('at', -999) > 60:
        _CHECK.update(at=time.monotonic(), value=tools.check())
    return _CHECK['value']


def public_settings() -> dict:
    s = core.settings()
    secrets = core.secrets_store()
    s['secrets_set'] = {k: bool(secrets.get(k)) for k in core.SECRET_FIELDS}
    return s


def goal_view(goal: dict, ctx: dict, weekday: int, shared: list[dict] | None = None) -> dict:
    """shared: the goal's collection items with the account's stock handed out (planner.items_by_goal)."""
    items = []
    for item in planner.goal_items(goal, ctx, shared):
        items.append({k: item.get(k) for k in ('key', 'label', 'names', 'kind', 'unit', 'unit_label', 'units', 'available',
                                               'executed', 'note', 'progress', 'paused', 'done', 'rank', 'weekdays',
                                               'tint', 'cost')}
                     | {'why': planner.blocker(item, weekday), 'days': planner.days_text(item['weekdays']),
                        'materials': [{k: m.get(k) for k in ('id', 'name', 'need', 'owned', 'remaining')}
                                      for m in item['materials']]})
    view = {k: v for k, v in goal.items() if k not in ('allowance', 'gear')}
    character = materials.dataset(goal['game']).get('characters', {}).get(str(goal['character_id']), {})
    view['rarity'], view['element'] = character.get('rarity'), character.get('element')  # offline dataset values
    view['items'] = items
    view['gear_eval'] = gear.evaluate(goal)
    view['gear_owned'] = ((inventory.arrange(goal['game']) or {}).get('goals') or {}).get(goal['id'])
    return view


def full_state() -> dict:
    ctx = planner.tool_context()
    weekday = core.game_date().weekday()
    s = core.settings()
    plans = {g: planner.plan(g) for g in ('zzz', 'genshin')}
    shared = {g: planner.items_by_goal(g, ctx) for g in ('zzz', 'genshin')}
    return {
        'version': core.VERSION, 'now': core.stamp(), 'game_date': str(core.game_date()), 'weekday': weekday,
        'admin': core.is_admin(), 'automation': tools.automation(), 'logged_in': mihoyo.logged_in(), 'accounts': mihoyo.accounts(),
        'login_expired': any(mihoyo.health(k).get('expired') for k in ('stamina-genshin', 'stamina-zzz', 'calc', 'detail')),
        'data_dir': str(core.DATA), 'log_file': str(core.LOG),
        'candidates': mihoyo.account_candidates(), 'qr': auth.state(),
        'runner': runner.state(), 'next_slot': scheduler.next_slot(),
        'plans': plans, 'stamina': {g: planner.estimate(g) for g in ('zzz', 'genshin')},
        'goals': {g: [goal_view(x, ctx, weekday, shared[g].get(x['id'])) for x in core.goals(g)] for g in ('zzz', 'genshin')},
        'forecast': planner.forecast(3), 'runs': core.runs(20),
        'health': {k: mihoyo.health(k) for k in ('stamina-genshin', 'stamina-zzz', 'calc')},
        'settings': public_settings(), 'check': env_check(), 'notifications': notify.recent(10),
        'assets': assets.cached(), 'assets_status': assets.status(),
        'inventory': {g: inventory_view(g) for g in ('zzz', 'genshin')},
        'catalog': {'bosses': ctx['bosses'],
                    'stages': {g: [{'name': st['name'], 'sets': [x['name'] for x in st['sets']]}
                                   for st in materials.gear_stages(g, s['paths']['onedragon'])] for g in ('zzz', 'genshin')},
                    'disc_sets': materials.gear_sets('zzz', s['paths']['onedragon']),
                    'artifact_sets': materials.gear_sets('genshin')},
    }


def inventory_view(game: str) -> dict | None:
    """The last inventory scan: when, how many pieces, and the spare ones grouped by set."""
    info = inventory.summary(game)
    if not info:
        return None
    arranged = inventory.arrange(game) or {}
    pieces = {p['uid']: p for p in inventory.load(game)['pieces']}
    spare: dict[str, int] = {}
    for uid in arranged.get('spare', []):
        spare[pieces[uid]['set']] = spare.get(pieces[uid]['set'], 0) + 1
    return {**info, 'spare': len(arranged.get('spare', [])),
            'spare_sets': sorted(spare.items(), key=lambda kv: -kv[1])}


def _is_loopback(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class Handler(BaseHTTPRequestHandler):
    server_version = 'GameCompanionLocal'

    def log_message(self, fmt, *args):  # quiet; errors still go to the app log
        pass

    # ------------------------------------------------ helpers
    def _send(self, code: int, body: bytes, kind: str, extra: dict | None = None) -> None:
        extra = dict(extra or {})
        self.send_response(code)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', extra.pop('Cache-Control', 'no-store'))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, value, code: int = 200) -> None:
        self._send(code, json.dumps(value, ensure_ascii=False, default=str).encode(), 'application/json; charset=utf-8')

    def _allowed(self) -> bool:
        host = self.client_address[0]
        if _is_loopback(host):
            return True
        if not core.settings()['server']['lan']:
            self._json({'error': tr('lan_off')}, 403)
            return False
        stored = core.secrets_store().get('password')
        if not stored:
            self._json({'error': tr('lan_no_password')}, 403)
            return False
        header = self.headers.get('Authorization', '')
        if header.startswith('Basic '):
            try:
                _, password = base64.b64decode(header[6:]).decode().split(':', 1)
                if core.check_password(password, stored):
                    return True
            except Exception:
                pass
        self._send(401, tr('password_required').encode(), 'text/plain; charset=utf-8',
                   {'WWW-Authenticate': 'Basic realm="game-companion", charset="UTF-8"'})
        return False

    def _page_lang(self) -> None:
        """Text written for this request follows the asking page's language (X-Lang), so pages in different
        languages never change each other's text; work outside requests uses the saved choice."""
        value = self.headers.get('X-Lang')
        i18n.REQUEST_LANG.set(value if value in i18n.LANGS else None)

    # ------------------------------------------------ GET
    def do_GET(self):
        self._page_lang()
        if not self._allowed():
            return
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        if not READY.is_set() and url.path.startswith('/api/') and url.path != '/api/health':
            return self._json({'error': tr('starting')}, 503)
        try:
            if url.path == '/api/state':
                return self._json(full_state())
            if url.path == '/api/roster':
                return self._json({'rows': mihoyo.roster(q.get('game', ''))})
            if url.path == '/api/characters':
                return self._json({'rows': materials.characters(q.get('game', ''))})
            if url.path == '/api/runs':
                return self._json({'rows': core.runs(int(q.get('limit', 50)))})
            if url.path == '/api/health':
                return self._json({'ok': True, 'app': APP_ID, 'version': core.VERSION, 'pid': os.getpid(),
                                   'instance': IDENTITY.get('instance'), 'launch': IDENTITY.get('launch'),
                                   'created': IDENTITY.get('created'), 'ready': READY.is_set(), 'busy': runner.busy()})
            if url.path.startswith('/assets/'):
                return self._asset(url.path[len('/assets/'):])
        except Exception as exc:
            return self._json({'error': mihoyo.describe_error(exc)}, 400)
        self._static(url.path)

    def _asset(self, name: str) -> None:
        """A cached game image; IDs never change their image, so browsers may keep it."""
        path = assets.file(name)
        if not path:
            return self._send(404, b'not found', 'text/plain')
        kind = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        self._send(200, path.read_bytes(), kind, {'Cache-Control': 'public, max-age=604800'})

    def _static(self, path: str) -> None:
        name = 'index.html' if path in ('', '/') else path.lstrip('/')
        target = (core.WEB / name).resolve()
        if core.WEB.resolve() not in target.parents or not target.is_file():
            return self._send(404, b'not found', 'text/plain')
        kind = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
        if kind.startswith('text/') or kind in ('application/javascript', 'application/json', 'image/svg+xml'):
            kind += '; charset=utf-8'
        self._send(200, target.read_bytes(), kind)

    # ------------------------------------------------ POST
    def do_POST(self):
        self._page_lang()
        if not self._allowed():
            return
        if self.headers.get('X-GC') != '1':  # custom header → cross-site forms cannot post
            return self._json({'error': tr('bad_origin')}, 403)
        if not READY.is_set() and urlparse(self.path).path != '/api/shutdown':
            return self._json({'error': tr('starting')}, 503)
        try:
            length = int(self.headers.get('Content-Length') or 0)
            body = json.loads(self.rfile.read(min(length, 1_000_000)) or b'{}')
            result = self.route(urlparse(self.path).path, body)
            return self._json(result if result is not None else {'ok': True})
        except ValueError as exc:
            return self._json({'error': str(exc)}, 400)
        except Exception as exc:
            code = getattr(exc, 'retcode', None)
            # A Miyoushe answer is explained by its code; anything else needs the place it failed.
            log.error('API error: %s (code %s)%s', type(exc).__name__, code, '' if code is not None else '\n' + core.stack(exc))
            return self._json({'error': mihoyo.describe_error(exc)}, 500)

    def route(self, path: str, b: dict):
        if path == '/api/login/start':
            return auth.start()
        if path == '/api/login/cancel':
            auth.cancel()
            return auth.state()
        if path == '/api/logout':
            return mihoyo.logout()
        if path == '/api/accounts/select':
            return mihoyo.select_account(b['game'], b['uid'])
        if path == '/api/goals/create':
            return goals.create(b['game'], b['character_id'], b['name'], b.get('target'), b.get('current'))
        if path == '/api/goals/update':
            return goals.update(b['id'], b.get('patch') or {})
        if path == '/api/goals/delete':
            return goals.remove(b['id'])
        if path == '/api/goals/order':
            return goals.set_order(b['game'], b['ids'])
        if path == '/api/goals/sync':
            return goals.sync(b['id'], observe=b.get('observe', True), force=True)  # the Sync button
        if path == '/api/run':
            if runner.busy():
                raise ValueError(tr('batch_running'))
            return {'run_id': runner.start_batch(b.get('games') or [], 'manual', 'manual')}
        if path == '/api/stop':
            return runner.request_stop()
        if path == '/api/settings':
            return save_settings(b.get('settings') or {}, b.get('secrets') or {})
        if path == '/api/notify/test':
            notify.send(b['channel'], tr('test_title'), tr('test_body'))
            return {'ok': True}
        if path == '/api/lang':  # the language chosen with the switch: for background text and pages without a choice
            core.save_settings({'ui': {'lang': b['lang']}})
            return {'ok': True}
        if path == '/api/notes/refresh':
            return mihoyo.refresh_notes(b['game'], force=True)
        if path == '/api/shutdown':
            return request_shutdown(b)
        if path == '/api/assets/sync':
            return assets.sync()
        if path == '/api/equip/reset':
            core.put('equip_used:' + b['game'], 0)
            return {'ok': True}
        if path == '/api/equip/grant':  # the allowance named another role: the user grants it to the selected one
            core.grant_allowance(b['game'])
            return {'ok': True}
        raise ValueError(tr('unknown_api'))


def save_settings(patch: dict, secrets: dict) -> dict:
    """All or nothing: the whole request is checked first, then the logon task (the step the system may refuse)
    changes, then the files. A refused request leaves the schedule, the task and the secrets as they were."""
    before = core.settings()
    merged, _ = core.prepare_settings(patch)
    after = core._merge(core.DEFAULTS, merged)
    password = secrets['password'] if 'password' in secrets else core.secrets_store().get('password')
    if after['server']['lan'] and not password:
        raise ValueError(tr('lan_needs_password'))
    autostart = after['schedule']['autostart'] != before['schedule']['autostart']
    if autostart:
        scheduler.set_autostart(after['schedule']['autostart'])
    try:
        if secrets:
            core.save_secrets(secrets)
        after = core.save_settings(patch)
    except Exception:
        if autostart:
            try:
                scheduler.set_autostart(before['schedule']['autostart'])
            except Exception:
                log.exception('Could not put the logon task back')
        raise
    if after['schedule']['enabled'] and not before['schedule']['enabled']:
        scheduler.mark_past_slots_done()
    _CHECK.clear()
    return {'ok': True, 'restart_needed': after['server'] != before['server']}


def request_shutdown(body: dict) -> dict:
    """Graceful stop for Stop.ps1 and stop.sh. The token is in this instance's PID file, so only a caller
    that can read the runtime folder can use it. A running batch is first stopped so its tool configs get restored."""
    if not IDENTITY.get('token') or body.get('token') != IDENTITY['token']:
        raise ValueError(tr('shutdown_mismatch'))
    if runner.busy() and not body.get('force'):
        raise ValueError(tr('shutdown_busy'))
    stop_soon()
    return {'ok': True}


def stop_soon() -> None:
    """Stop a running batch first, so its tool settings get restored, then let the main thread exit."""
    def finish():
        if runner.busy():
            runner.request_stop()
            deadline = time.monotonic() + 300
            while runner.busy() and time.monotonic() < deadline:
                time.sleep(0.5)
        SHUTDOWN.set()
    threading.Thread(target=finish, daemon=True, name='shutdown').start()


class Server(ThreadingHTTPServer):
    daemon_threads = True
    # On Windows SO_REUSEADDR would let this server bind a port another program already listens on,
    # and then either one may get the connections. Without it a used port fails to bind, as it should.
    allow_reuse_address = os.name != 'nt'


def serve() -> ThreadingHTTPServer:
    return Server(core.listen_address(), Handler)


def run_forever(httpd: ThreadingHTTPServer) -> None:
    threading.Thread(target=httpd.serve_forever, daemon=True, name='http').start()
