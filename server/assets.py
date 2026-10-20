"""Local image cache: character portraits, material icons and Drive Disc / artifact set icons, keyed by stable game IDs.

Image URLs come only from official API responses the app already requests (roster,
goal sync, calculators), or for ZZZ portraits, which the upgrade guide does not return, from
the official square-avatar address of an agent id such a response named (mihoyo.zzz_portrait).
Each image is saved once, in the background, as soon as its
URL is known; pages are served from data/assets and never trigger a download. A failed
download is remembered and retried only on request or after a week.
"""
from __future__ import annotations

import logging
import os
import re
import struct
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
KEY = re.compile(r'(genshin|zzz)/(character|material|disc|artifact)/[0-9A-Za-z_-]{1,40}')  # disc / artifact: a set's icon
MAX_BYTES = 2_000_000
RETRY_AFTER = timedelta(days=7)
_LOCK = threading.Lock()
_PENDING: set[str] = set()
_STATE = {'running': False}
_CHECKED: dict[str, tuple] = {}  # path -> (inode, mtime, size, complete) of its last check
EDGE = 32  # bytes read from each end of a saved image to check it


def root() -> Path:
    return core.DATA / 'assets'


def key(game: str, kind: str, ident) -> str:
    return f'{game}/{kind}/{ident}'


def complete(head: bytes, tail: bytes, size: int, ext: str) -> bool:
    """Whether bytes are a whole image of the type: its header with a non-zero picture size and its end marker.
    A response cut short, or one that only starts like an image, has no end marker."""
    if ext == '.png':
        return (len(head) >= 24 and head[:8] == b'\x89PNG\r\n\x1a\n' and head[12:16] == b'IHDR'
                and min(struct.unpack('>II', head[16:24])) > 0 and tail[-8:-4] == b'IEND')
    if ext == '.jpg':
        return size > 4 and head[:3] == b'\xff\xd8\xff' and b'\xff\xd9' in tail  # some encoders pad after it
    if ext == '.webp':
        return (len(head) >= 12 and head[:4] == b'RIFF' and head[8:12] == b'WEBP'
                and int.from_bytes(head[4:8], 'little') + 8 in (size, size - 1))
    if ext == '.gif':
        return (len(head) >= 10 and head[:6] in (b'GIF87a', b'GIF89a')
                and min(struct.unpack('<HH', head[6:10])) > 0 and tail.endswith(b';'))
    return False


def _whole(path: Path) -> bool:
    """A saved image is used only while it is complete; a damaged one counts as missing and is downloaded again."""
    try:
        info = path.stat()
    except OSError:
        return False
    version = (info.st_ino, info.st_mtime_ns, info.st_size)
    seen = _CHECKED.get(str(path))
    if seen and seen[:3] == version:
        return seen[3]
    try:
        with open(path, 'rb') as f:
            head = f.read(EDGE)
            f.seek(max(0, info.st_size - EDGE))
            tail = f.read(EDGE)
    except OSError:
        return False
    ok = complete(head, tail, info.st_size, path.suffix)
    _CHECKED[str(path)] = (*version, ok)
    return ok


def file(k: str) -> Path | None:
    """The saved image for a key, or None."""
    if not KEY.fullmatch(k):
        return None
    base = root() / k
    return next((p for p in (base.with_suffix(ext) for ext in TYPES.values()) if p.is_file() and _whole(p)), None)


def cached() -> list[str]:
    folder = root()
    if not folder.is_dir():
        return []
    return sorted(p.relative_to(folder).with_suffix('').as_posix() for p in folder.glob('*/*/*')
                  if p.suffix in MAGIC and _whole(p))


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
    if not ext or len(data) > MAX_BYTES or not complete(data[:EDGE], data[-EDGE:], len(data), ext):
        raise ValueError('not a whole image of an accepted type and size')
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
