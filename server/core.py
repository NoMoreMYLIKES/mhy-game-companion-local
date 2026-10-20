"""Paths, time, storage, settings and credentials shared by every module."""
from __future__ import annotations

import base64
import copy
import ctypes
import hashlib
import json
import logging
import logging.handlers
import os
import secrets
import sqlite3
import threading
import traceback
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .i18n import LANGS, tr

APP = Path(__file__).resolve().parent.parent
DATA = Path(os.path.abspath(os.environ.get('GCL_HOME') or APP / 'data'))  # absolute: child processes get it as-is
LOG = DATA / 'logs' / 'app.log'
WEB = APP / 'web'
DATASETS = Path(__file__).resolve().parent / 'datasets'
CN = timezone(timedelta(hours=8))
LOCK = threading.RLock()
VERSION = '1.0.0'

log = logging.getLogger('gcl')


def setup_logging() -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    if os.name != 'nt':  # it holds credentials that only file permissions protect here
        DATA.chmod(0o700)
        for secret in DATA.glob('*.dpapi.json'):  # files written before this rule
            secret.chmod(0o600)
    handler = logging.handlers.RotatingFileHandler(LOG, maxBytes=2_000_000, backupCount=3, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def stack(exc: BaseException) -> str:
    """Where an exception came from, without its message: messages can carry tokens or account data."""
    return ''.join(traceback.format_tb(exc.__traceback__)).rstrip()


# ---------------------------------------------------------------- time

def now() -> datetime:
    return datetime.now(CN)


def stamp(value: datetime | None = None) -> str:
    return (value or now()).astimezone(CN).isoformat(timespec='seconds')


def parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        d = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=CN)


def game_date(at: datetime | None = None):
    """Both games reset at 04:00 China time."""
    return ((at or now()).astimezone(CN) - timedelta(hours=4)).date()


# ---------------------------------------------------------------- json files

def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return default


def write_json(path: Path, value: Any, private: bool = False) -> None:
    """Atomic write; a private file is readable by this user only (outside Windows, where ACLs apply)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f'{path.name}.{os.getpid()}.{threading.get_ident()}.tmp')
    mode = 0o600 if private and os.name != 'nt' else 0o666
    with os.fdopen(os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode), 'w', encoding='utf-8') as out:
        out.write(json.dumps(value, ensure_ascii=False, indent=2))
    os.replace(temp, path)


# ---------------------------------------------------------------- sqlite

SCHEMA = (
    'CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS goals (id TEXT PRIMARY KEY, data TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, started TEXT NOT NULL, data TEXT NOT NULL)',
    # stamina readings, each of the game role it was read for (account_key); the older samples table named no role
    'CREATE TABLE IF NOT EXISTS stamina (id INTEGER PRIMARY KEY AUTOINCREMENT, game TEXT, account TEXT, at TEXT, current INTEGER, cap INTEGER, source TEXT)',
    'CREATE TABLE IF NOT EXISTS outbox (id TEXT PRIMARY KEY, created TEXT, payload TEXT, attempts INTEGER DEFAULT 0, next_at TEXT, sent_at TEXT, error TEXT)',
)


@contextmanager
def db():
    DATA.mkdir(parents=True, exist_ok=True)
    with LOCK:
        con = sqlite3.connect(DATA / 'app.db', timeout=15)
        con.row_factory = sqlite3.Row
        for statement in SCHEMA:
            con.execute(statement)
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()


def get(key: str, default: Any = None) -> Any:
    with db() as con:
        row = con.execute('SELECT value FROM kv WHERE key=?', (key,)).fetchone()
    return json.loads(row[0]) if row else copy.deepcopy(default)


def put(key: str, value: Any) -> None:
    with db() as con:
        con.execute('INSERT OR REPLACE INTO kv VALUES (?,?)', (key, json.dumps(value, ensure_ascii=False)))


def delete(key: str) -> None:
    with db() as con:
        con.execute('DELETE FROM kv WHERE key=?', (key,))


def goals(game: str | None = None) -> list[dict]:
    with db() as con:
        rows = [json.loads(r[0]) for r in con.execute('SELECT data FROM goals')]
    rows = [g for g in rows if game is None or g['game'] == game]
    return sorted(rows, key=lambda g: (g['game'], g.get('position', 0), g.get('created', ''), g['id']))


def goal(goal_id: str) -> dict | None:
    with db() as con:
        row = con.execute('SELECT data FROM goals WHERE id=?', (goal_id,)).fetchone()
    return json.loads(row[0]) if row else None


_GOALS = {'version': 0}


def goals_version() -> int:
    """Changes with every goal write in this process: a cache of anything derived from goals keys on it
    (``updated`` has whole seconds only, so two edits within one second look alike)."""
    return _GOALS['version']


def save_goal(value: dict) -> None:
    value['updated'] = stamp()
    with db() as con:
        con.execute('INSERT OR REPLACE INTO goals VALUES (?,?)', (value['id'], json.dumps(value, ensure_ascii=False)))
        _GOALS['version'] += 1


def delete_goal(goal_id: str) -> None:
    with db() as con:
        con.execute('DELETE FROM goals WHERE id=?', (goal_id,))
        _GOALS['version'] += 1


def save_run(run: dict) -> None:
    with db() as con:
        con.execute('INSERT OR REPLACE INTO runs VALUES (?,?,?)', (run['id'], run['started'], json.dumps(run, ensure_ascii=False)))


def runs(limit: int = 30, since: str | None = None) -> list[dict]:
    with db() as con:
        if since:
            rows = con.execute('SELECT data FROM runs WHERE started>=? ORDER BY started DESC', (since,))
        else:
            rows = con.execute('SELECT data FROM runs ORDER BY started DESC LIMIT ?', (limit,))
        return [json.loads(r[0]) for r in rows]


SELECTED = object()  # account argument: the game role selected now
_ROLES: dict = {}


def account_key(game: str) -> str | None:
    """The selected game role (uid@server) that readings, calculations and stamina allowances belong to.
    Read again whenever the login file is replaced (a new file has a new inode)."""
    path = DATA / 'mihoyo.dpapi.json'
    try:
        info = path.stat()
        version = (str(path), info.st_ino, info.st_mtime_ns, info.st_size)
    except OSError:
        version = (str(path), None)
    with LOCK:
        if _ROLES.get('version') != version:
            _ROLES.update(version=version, accounts=load_secret('mihoyo').get('accounts') or {})
        account = _ROLES['accounts'].get(game)
    return f"{account['uid']}@{account.get('server', '')}" if account else None


def add_sample(game: str, current: int, cap: int | None, source: str, at: str | None = None, account=SELECTED) -> None:
    account = account_key(game) if account is SELECTED else account
    with db() as con:
        con.execute('INSERT INTO stamina(game,account,at,current,cap,source) VALUES (?,?,?,?,?,?)',
                    (game, account, at or stamp(), current, cap, source))
        con.execute('DELETE FROM stamina WHERE id NOT IN (SELECT id FROM stamina ORDER BY id DESC LIMIT 2000)')


def latest_sample(game: str, account=SELECTED) -> dict | None:
    """The newest reading of the selected role; another role's stamina is never this one's."""
    account = account_key(game) if account is SELECTED else account
    with db() as con:
        row = con.execute('SELECT * FROM stamina WHERE game=? AND account IS ? ORDER BY at DESC, id DESC LIMIT 1',
                          (game, account)).fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------- credentials (DPAPI on Windows)

class _Blob(ctypes.Structure):
    _fields_ = [('size', ctypes.c_ulong), ('data', ctypes.POINTER(ctypes.c_ubyte))]


def _dpapi(raw: bytes, decrypt: bool) -> bytes:
    if os.name != 'nt':  # no DPAPI: stored as is, in a file only this user can read (write_json private)
        return raw
    buffer = ctypes.create_string_buffer(raw, len(raw))
    source = _Blob(len(raw), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = _Blob()
    call = ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    args = (ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)) if decrypt else \
        (ctypes.byref(source), 'game-companion-local', None, None, None, 1, ctypes.byref(target))
    if not call(*args):
        raise RuntimeError(tr('dpapi_failed'))
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        ctypes.windll.kernel32.LocalFree(target.data)


def save_secret(name: str, value: dict) -> None:
    raw = _dpapi(json.dumps(value).encode(), decrypt=False)
    write_json(DATA / f'{name}.dpapi.json', {'encrypted': base64.b64encode(raw).decode()}, private=True)


def load_secret(name: str) -> dict:
    wrapped = read_json(DATA / f'{name}.dpapi.json', {})
    if not wrapped:
        return {}
    try:
        return json.loads(_dpapi(base64.b64decode(wrapped['encrypted']), decrypt=True))
    except Exception:
        log.exception('Cannot decrypt %s', name)
        return {}


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 120_000).hex()
    return f'{salt}${digest}'


def check_password(password: str, stored: str) -> bool:
    if not stored or '$' not in stored:
        return False
    salt = stored.split('$', 1)[0]
    return secrets.compare_digest(hash_password(password, salt), stored)


# ---------------------------------------------------------------- settings

def _default_onedragon() -> str:
    """Newest extracted OneDragon release in Downloads (or one folder below), if any."""
    downloads = Path.home() / 'Downloads'
    try:
        found = [p for pattern in ('ZenlessZoneZero-OneDragon*', '*/ZenlessZoneZero-OneDragon*')
                 for p in downloads.glob(pattern) if p.is_dir()]
    except OSError:
        return ''
    return str(max(found, key=lambda p: p.stat().st_mtime)) if found else ''


DEFAULTS: dict = {
    'server': {'port': 18800, 'lan': False},
    'ui': {'lang': 'en'},
    'paths': {
        'bettergi': r'C:\Program Files\BetterGI\BetterGI',
        'onedragon': _default_onedragon(),
        'genshin_exe': '',
        'zzz_exe': '',
        'yas': '',          # Genshin artifact scanner (yas fork): yas_artifact.exe
        'zzz_scanner': '',  # ZZZ Drive Disc scanner: ZZZ-Scanner.Next.exe
    },
    'schedule': {'enabled': False, 'times': ['05:00', '18:00'], 'catchup_hours': 4, 'games': ['zzz', 'genshin'], 'autostart': False},
    # bgi_profile: the BetterGI One Dragon config this app generates before each run.
    # bgi_template: a BetterGI One Dragon config to copy it from; empty uses the bundled template.
    'execution': {'timeout_minutes': 90, 'window_width': 1920, 'window_height': 1080,
                  'if_game_running': 'restart', 'bgi_profile': 'GameCompanion', 'bgi_template': ''},
    'sync': {'notes_minutes': 60, 'goals_hours': 12},
    'planning': {
        'genshin_claim_mode': 'double',
        'genshin_boss_yield': 2.4,
        'zzz_coffee_forecast': 80,
        'artifact': {'enabled': False, 'domain': '', 'cap': 0},
        'disc': {'enabled': False, 'mission': '', 'cap': 0},
    },
    'features': {'mute_morning': True, 'zzz_rewards': True, 'genshin_daily_reward': True,
                 'genshin_mail': True, 'genshin_teapot': False, 'scan_inventory': False},
    'notify': {
        'events': {'batch': True, 'failure': True, 'login': True, 'goal_done': True},
        'quiet_success': False,
        'channels': {
            'relay': {'enabled': False},
            'telegram': {'enabled': False, 'chat_id': '', 'api_base': 'https://api.telegram.org'},
            'webhook': {'enabled': False},
            'toast': {'enabled': os.name == 'nt'},  # Windows balloon tips
        },
    },
}

# Sensitive values live in a DPAPI file, never in settings.json or API responses.
SECRET_FIELDS = ('password', 'relay_url', 'telegram_token', 'webhook_url')


def _merge(base: dict, patch: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in (patch or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def settings() -> dict:
    stored = read_json(DATA / 'settings.json', {})  # an unusable file is reported by check_settings_file()
    return _merge(DEFAULTS, stored if isinstance(stored, dict) else {})


class SettingsError(ValueError):
    """settings.json exists but cannot be used."""


def check_settings_file() -> None:
    """Fail clearly at startup instead of silently falling back to defaults for a broken file."""
    path = DATA / 'settings.json'
    if not path.exists():
        return
    try:
        raw = json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as exc:
        raise SettingsError(f'{path} is not valid JSON ({exc})') from None
    if not isinstance(raw, dict):
        raise SettingsError(f'{path} must contain a JSON object')
    try:
        validate_settings(_merge(DEFAULTS, raw))
    except (KeyError, TypeError, ValueError) as exc:
        raise SettingsError(f'{path} has an invalid value: {exc}') from None


def listen_address(value: dict | None = None) -> tuple[str, int]:
    """Host and port the backend binds; the launcher and Stop use the same answer."""
    server = (value or settings())['server']
    return ('0.0.0.0' if server['lan'] else '127.0.0.1'), int(server['port'])


def instance_id() -> str:
    """Opaque id of this runtime folder, so the launcher can tell installations apart. It belongs to the
    folder's location: a copy of the folder (with its PID file) gets an id of its own."""
    path = DATA / 'instance.json'
    where = os.path.normcase(os.path.realpath(DATA))
    data = read_json(path, {})
    if not isinstance(data, dict) or not data.get('id') or data.get('path') != where:
        data = {'id': secrets.token_hex(8), 'path': where, 'created': stamp()}
        write_json(path, data)
    return data['id']


# Equipment continuations: the game whose stamina each spends, and the field naming its stage.
ALLOWANCES = {'artifact': ('genshin', 'domain'), 'disc': ('zzz', 'mission')}


def prepare_settings(patch: dict) -> tuple[dict, list[str]]:
    """The settings file content a patch would leave, checked but not written, and the games whose equipment
    allowance it grants to a newly selected role. Nothing is stored when this raises."""
    patch = copy.deepcopy(patch or {})
    for key in ALLOWANCES:  # which role an allowance belongs to is recorded here, never taken from a request
        if isinstance((patch.get('planning') or {}).get(key), dict):
            patch['planning'][key].pop('account', None)
    current = read_json(DATA / 'settings.json', {})
    current = current if isinstance(current, dict) else {}
    merged = _merge(current, patch)
    before, after = _merge(DEFAULTS, current), _merge(DEFAULTS, merged)
    validate_settings(after)
    if isinstance(merged.get('schedule'), dict) and 'times' in merged['schedule']:
        merged['schedule']['times'] = sorted(set(merged['schedule']['times']))  # one slot per time
    if after['schedule']['enabled'] and not after['schedule']['times']:
        raise ValueError(tr('schedule_needs_times'))
    if after['schedule']['enabled'] and not after['schedule']['games']:
        raise ValueError(tr('schedule_needs_games'))
    moved = []
    for key, (game, field) in ALLOWANCES.items():
        old, new = before['planning'][key], after['planning'][key]
        if any(old.get(k) != new.get(k) for k in ('enabled', 'cap', field)):
            # changing an allowance grants it to the role selected now: it spends that role's stamina only
            role = account_key(game)
            merged.setdefault('planning', {}).setdefault(key, {})['account'] = role
            if role != old.get('account'):
                moved.append(game)
    return merged, moved


def save_settings(patch: dict) -> dict:
    with LOCK:
        merged, moved = prepare_settings(patch)
        write_json(DATA / 'settings.json', merged)
        for game in moved:  # a role's cumulative cap starts from nothing it did not use
            put('equip_used:' + game, 0)
    return settings()


def grant_allowance(game: str) -> None:
    """Grant the game's equipment allowance, unchanged, to the role selected now (it named another role or none)."""
    key = next((k for k, (g, _) in ALLOWANCES.items() if g == game), None)
    if key is None:
        raise ValueError(tr('invalid_game'))
    with LOCK:
        merged = read_json(DATA / 'settings.json', {})
        merged = merged if isinstance(merged, dict) else {}
        role = account_key(game)
        conf = merged.setdefault('planning', {}).setdefault(key, {})
        if conf.get('account', SELECTED) != role:
            conf['account'] = role
            write_json(DATA / 'settings.json', merged)
            put('equip_used:' + game, 0)


def allowance_role_ok(game: str, conf: dict) -> bool:
    """An equipment allowance spends stamina only of the role it was granted for."""
    return 'account' in conf and conf['account'] == account_key(game)


def _number(value, low, high, field: str, integer: bool = False) -> None:
    """A finite number within the business range; JSON booleans and text are not numbers."""
    import math
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
            or (integer and value != int(value)) or not low <= value <= high):
        raise ValueError(tr('bad_number', field=tr(field), low=low, high=high))


def validate_settings(value: dict) -> None:
    import re
    times = value['schedule']['times']
    if not isinstance(times, list) or not all(isinstance(t, str) and re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d', t) for t in times):
        raise ValueError(tr('bad_times'))
    port = value['server']['port']
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError(tr('bad_port'))
    if not isinstance(value['server']['lan'], bool):
        raise ValueError(tr('bad_lan'))
    if not isinstance(value['schedule']['enabled'], bool) or not isinstance(value['schedule']['autostart'], bool):
        raise ValueError(tr('bad_switch'))
    if value['execution']['if_game_running'] not in ('restart', 'skip'):
        raise ValueError(tr('bad_if_running'))
    if value['planning']['genshin_claim_mode'] not in ('double', 'single'):
        raise ValueError(tr('bad_claim_mode'))
    _number(value['execution']['timeout_minutes'], 10, 480, 'fld_timeout', integer=True)
    _number(value['execution']['window_width'], 640, 7680, 'fld_window', integer=True)
    _number(value['execution']['window_height'], 480, 4320, 'fld_window', integer=True)
    _number(value['schedule']['catchup_hours'], 0, 24, 'fld_catchup')
    _number(value['sync']['notes_minutes'], 5, 1440, 'fld_notes_minutes', integer=True)
    _number(value['sync']['goals_hours'], 1, 168, 'fld_goals_hours')
    _number(value['planning']['genshin_boss_yield'], 0.5, 10, 'fld_boss_yield')  # runs = shortfall / yield
    _number(value['planning']['zzz_coffee_forecast'], 0, 300, 'fld_coffee', integer=True)
    games = value['schedule']['games']
    if not isinstance(games, list) or any(game not in ('genshin', 'zzz') for game in games):
        raise ValueError(tr('bad_game'))
    for key in ALLOWANCES:
        _number(value['planning'][key]['cap'], 0, 100000, 'fld_cap', integer=True)
    if value['ui']['lang'] not in LANGS:
        raise ValueError(tr('bad_lang'))


def secrets_store() -> dict:
    return load_secret('settings-secrets')


def save_secrets(patch: dict) -> None:
    with LOCK:
        current = secrets_store()
        for key, value in patch.items():
            if key not in SECRET_FIELDS:
                continue
            if value is None or value == '':
                current.pop(key, None)
            elif key == 'password':
                current[key] = hash_password(str(value))
            else:
                current[key] = str(value)
        save_secret('settings-secrets', current)


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False
