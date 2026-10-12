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
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .i18n import LANGS, tr

APP = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get('GCL_HOME') or APP / 'data')
WEB = APP / 'web'
DATASETS = Path(__file__).resolve().parent / 'datasets'
CN = timezone(timedelta(hours=8))
LOCK = threading.RLock()
VERSION = '1.0.0'

log = logging.getLogger('gcl')


def setup_logging() -> None:
    (DATA / 'logs').mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(DATA / 'logs' / 'app.log', maxBytes=2_000_000, backupCount=3, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


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


def write_json(path: Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f'{path.name}.{os.getpid()}.{threading.get_ident()}.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp, path)


# ---------------------------------------------------------------- sqlite

SCHEMA = (
    'CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS goals (id TEXT PRIMARY KEY, data TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, started TEXT NOT NULL, data TEXT NOT NULL)',
    'CREATE TABLE IF NOT EXISTS samples (id INTEGER PRIMARY KEY AUTOINCREMENT, game TEXT, at TEXT, current INTEGER, cap INTEGER, source TEXT)',
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


def save_goal(value: dict) -> None:
    value['updated'] = stamp()
    with db() as con:
        con.execute('INSERT OR REPLACE INTO goals VALUES (?,?)', (value['id'], json.dumps(value, ensure_ascii=False)))


def delete_goal(goal_id: str) -> None:
    with db() as con:
        con.execute('DELETE FROM goals WHERE id=?', (goal_id,))


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


def add_sample(game: str, current: int, cap: int | None, source: str, at: str | None = None) -> None:
    with db() as con:
        con.execute('INSERT INTO samples(game,at,current,cap,source) VALUES (?,?,?,?,?)', (game, at or stamp(), current, cap, source))
        con.execute('DELETE FROM samples WHERE id NOT IN (SELECT id FROM samples ORDER BY id DESC LIMIT 2000)')


def latest_sample(game: str) -> dict | None:
    with db() as con:
        row = con.execute('SELECT * FROM samples WHERE game=? ORDER BY at DESC, id DESC LIMIT 1', (game,)).fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------- credentials (DPAPI)

class _Blob(ctypes.Structure):
    _fields_ = [('size', ctypes.c_ulong), ('data', ctypes.POINTER(ctypes.c_ubyte))]


def _dpapi(raw: bytes, decrypt: bool) -> bytes:
    if os.name != 'nt':  # development fallback only; the app targets Windows
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
    write_json(DATA / f'{name}.dpapi.json', {'encrypted': base64.b64encode(raw).decode()})


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
                 'genshin_mail': True, 'genshin_teapot': False},
    'notify': {
        'events': {'batch': True, 'failure': True, 'login': True, 'goal_done': True},
        'quiet_success': False,
        'channels': {
            'relay': {'enabled': False},
            'telegram': {'enabled': False, 'chat_id': '', 'api_base': 'https://api.telegram.org'},
            'webhook': {'enabled': False},
            'toast': {'enabled': True},
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
    return _merge(DEFAULTS, read_json(DATA / 'settings.json', {}))


def save_settings(patch: dict) -> dict:
    with LOCK:
        current = read_json(DATA / 'settings.json', {})
        merged = _merge(current, patch)
        validate_settings(_merge(DEFAULTS, merged))
        write_json(DATA / 'settings.json', merged)
    return settings()


def validate_settings(value: dict) -> None:
    import re
    times = value['schedule']['times']
    if not isinstance(times, list) or not all(isinstance(t, str) and re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d', t) for t in times):
        raise ValueError(tr('bad_times'))
    if not 1 <= int(value['server']['port']) <= 65535:
        raise ValueError(tr('bad_port'))
    if value['execution']['if_game_running'] not in ('restart', 'skip'):
        raise ValueError(tr('bad_if_running'))
    if value['planning']['genshin_claim_mode'] not in ('double', 'single'):
        raise ValueError(tr('bad_claim_mode'))
    if not 10 <= int(value['execution']['timeout_minutes']) <= 480:
        raise ValueError(tr('bad_timeout'))
    for game in value['schedule']['games']:
        if game not in ('genshin', 'zzz'):
            raise ValueError(tr('bad_game'))
    for key in ('artifact', 'disc'):
        if int(value['planning'][key]['cap']) < 0:
            raise ValueError(tr('bad_cap'))
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
