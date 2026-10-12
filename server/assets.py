"""Local image cache: character portraits and material icons, keyed by stable game IDs.

Image URLs come only from official API responses the app already requests (roster,
goal sync, calculators). Each image is saved once, in the background, as soon as its
URL is known; pages are served from data/assets and never trigger a download. A failed
download is remembered and retried only on request or after a week.
"""
from __future__ import annotations

import logging
import os
import re
import threading
import urllib.request
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

from . import core

log = logging.getLogger('gcl.assets')
TYPES = {'image/png': '.png', 'image/jpeg': '.jpg', 'image/webp': '.webp', 'image/gif': '.gif'}
MAGIC = {'.png': (b'\x89PNG',), '.jpg': (b'\xff\xd8\xff',), '.webp': (b'RIFF',), '.gif': (b'GIF8',)}
HOSTS = ('mihoyo.com', 'miyoushe.com', 'mihoyocdn.com', 'hoyoverse.com', 'hoyolab.com')
KEY = re.compile(r'(genshin|zzz)/(character|material)/[0-9A-Za-z_-]{1,40}')
MAX_BYTES = 2_000_000
RETRY_AFTER = timedelta(days=7)
_LOCK = threading.Lock()
_PENDING: set[str] = set()
_STATE = {'running': False}


def root() -> Path:
    return core.DATA / 'assets'


def key(game: str, kind: str, ident) -> str:
    return f'{game}/{kind}/{ident}'


def file(k: str) -> Path | None:
    """The saved image for a key, or None."""
    if not KEY.fullmatch(k):
        return None
    base = root() / k
    return next((p for p in (base.with_suffix(ext) for ext in TYPES.values()) if p.is_file()), None)


def cached() -> list[str]:
    folder = root()
    if not folder.is_dir():
        return []
    return sorted(p.relative_to(folder).with_suffix('').as_posix() for p in folder.glob('*/*/*')
                  if p.suffix in MAGIC)


def allowed(url: str) -> bool:
    try:
        parsed = urlparse(str(url))
    except ValueError:
        return False
    host = (parsed.hostname or '').lower()
    return parsed.scheme == 'https' and any(host == h or host.endswith('.' + h) for h in HOSTS)


def collect(sources: dict) -> None:
    """Remember image URLs from an API response and save the images not cached yet."""
    fresh = {k: str(u) for k, u in sources.items() if u and KEY.fullmatch(k) and allowed(u)}
    if not fresh:
        return
    with _LOCK:
        known = core.get('asset_sources', {})
        if any(known.get(k) != u for k, u in fresh.items()):
            known.update(fresh)
            core.put('asset_sources', known)
    queue(fresh)


def queue(keys, retry: bool = False) -> int:
    """Download missing images in one background worker; returns how many were queued."""
    failed = core.get('asset_failed', {})
    now = core.now()
    todo = []
    for k in keys:
        if file(k):
            continue
        last = core.parse(failed.get(k))
        if last and not retry and now - last < RETRY_AFTER:
            continue
        todo.append(k)
    if not todo:
        return 0
    with _LOCK:
        _PENDING.update(todo)
        if not _STATE['running']:
            _STATE['running'] = True
            threading.Thread(target=_work, daemon=True, name='assets').start()
    return len(todo)


def sync(retry: bool = True) -> dict:
    """Queue every known image that is not saved yet (Settings → Download missing images)."""
    queue(list(core.get('asset_sources', {})), retry=retry)
    return status()


def _work() -> None:
    while True:
        with _LOCK:
            if not _PENDING:
                _STATE['running'] = False
                return
            k = _PENDING.pop()
        try:
            _download(k)
        except Exception as exc:  # one bad image must not stop the others
            failed = core.get('asset_failed', {})
            failed[k] = core.stamp()
            core.put('asset_failed', failed)
            log.warning('Image %s not saved: %s', k, exc)


def _download(k: str) -> None:
    url = core.get('asset_sources', {}).get(k)
    if not url or file(k):
        return
    if not allowed(url):
        raise ValueError('host not allowed')
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 GameCompanionLocal'})
    with urllib.request.urlopen(request, timeout=20) as resp:
        if not allowed(resp.geturl()):
            raise ValueError('redirected to a host that is not allowed')
        ext = TYPES.get(resp.headers.get_content_type())
        data = resp.read(MAX_BYTES + 1)
    if not ext or len(data) > MAX_BYTES or not data.startswith(MAGIC[ext]):
        raise ValueError('not an image of an accepted type and size')
    target = (root() / k).with_suffix(ext)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + '.tmp')
    temp.write_bytes(data)
    os.replace(temp, target)
    failed = core.get('asset_failed', {})
    if failed.pop(k, None):
        core.put('asset_failed', failed)


def status() -> dict:
    sources = core.get('asset_sources', {})
    have = set(cached())
    failed = core.get('asset_failed', {})
    return {'cached': len(have), 'known': len(sources), 'missing': sum(k not in have for k in sources),
            'failed': sum(k not in have for k in failed), 'busy': _STATE['running']}
