"""Notifications: one concise message per event, delivered per channel with retries."""
from __future__ import annotations

import base64
import json
import logging
import subprocess
import urllib.request
import uuid
from datetime import timedelta
from pathlib import Path

from . import core
from .i18n import tr

log = logging.getLogger('gcl.notify')
CHANNELS = ('relay', 'telegram', 'webhook', 'toast')
ATTEMPTS = 6  # a message is given up after this many tries


def event(kind: str, title: str, lines: list[str], ok: bool = False) -> None:
    n = core.settings()['notify']
    if not n['events'].get(kind, False):
        return
    if kind == 'batch' and ok and n.get('quiet_success'):
        return
    payload = {'kind': kind, 'title': title, 'text': '\n'.join(x for x in lines if x)[:1500]}
    with core.db() as con:
        for channel in CHANNELS:
            if n['channels'][channel].get('enabled'):
                con.execute('INSERT INTO outbox(id,created,payload,attempts,next_at) VALUES (?,?,?,0,?)',
                            (uuid.uuid4().hex, core.stamp(), json.dumps({**payload, 'channel': channel}, ensure_ascii=False),
                             core.stamp()))


def _post(url: str, body: dict, timeout: float = 15) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode(),
                                 headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read(65536).decode('utf-8', errors='replace')
    try:
        return json.loads(raw)
    except ValueError:
        return {'raw': raw[:200]}


def send(channel: str, title: str, text: str) -> None:
    """Deliver now; raises with a readable reason on failure."""
    secrets = core.secrets_store()
    conf = core.settings()['notify']['channels'][channel]
    if channel == 'relay':
        if not secrets.get('relay_url'):
            raise ValueError(tr('relay_missing'))
        result = _post(secrets['relay_url'], {'source': tr('brand'), 'title': title, 'content': text})
        if result.get('ok') is False:
            raise ValueError(tr('relay_unconfirmed'))
    elif channel == 'telegram':
        if not secrets.get('telegram_token') or not conf.get('chat_id'):
            raise ValueError(tr('tg_missing'))
        base = (conf.get('api_base') or 'https://api.telegram.org').rstrip('/')
        result = _post(f"{base}/bot{secrets['telegram_token']}/sendMessage", {'chat_id': conf['chat_id'], 'text': f'{title}\n{text}'})
        if not result.get('ok'):
            raise ValueError(tr('tg_rejected', reason=result.get('description') or tr('unknown')))
    elif channel == 'webhook':
        if not secrets.get('webhook_url'):
            raise ValueError(tr('webhook_missing'))
        _post(secrets['webhook_url'], {'title': title, 'content': text, 'text': f'{title}\n{text}'})
    elif channel == 'toast':
        toast(title, text)
    else:
        raise ValueError(tr('unknown_channel'))


def toast(title: str, text: str) -> None:
    pwsh = Path(r'C:\Program Files\PowerShell\7\pwsh.exe')
    if not pwsh.is_file():
        raise ValueError(tr('pwsh_missing'))
    t = title.replace("'", "''")[:60]
    b = text.replace("'", "''")[:240] or ' '
    script = ("Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing;"
              "$n = New-Object System.Windows.Forms.NotifyIcon; $n.Icon = [System.Drawing.SystemIcons]::Information;"
              f"$n.BalloonTipTitle = '{t}'; $n.BalloonTipText = '{b}'; $n.Visible = $true;"
              "$n.ShowBalloonTip(8000); Start-Sleep -Seconds 9; $n.Dispose()")
    encoded = base64.b64encode(script.encode('utf-16-le')).decode()
    subprocess.Popen([str(pwsh), '-NoLogo', '-NoProfile', '-WindowStyle', 'Hidden', '-EncodedCommand', encoded],
                     creationflags=0x08000000, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def drain(limit: int = 10) -> None:
    with core.db() as con:
        rows = [dict(r) for r in con.execute(
            'SELECT * FROM outbox WHERE sent_at IS NULL AND attempts < ? AND next_at <= ? ORDER BY created LIMIT ?',
            (ATTEMPTS, core.stamp(), limit))]
    channels = core.settings()['notify']['channels']
    for row in rows:
        p = json.loads(row['payload'])
        if not channels.get(p['channel'], {}).get('enabled'):
            # turned off after it was queued: it is not sent, and the list says so
            with core.db() as con:
                con.execute('UPDATE outbox SET attempts=?, error=? WHERE id=?', (ATTEMPTS, tr('channel_off'), row['id']))
            continue
        try:
            send(p['channel'], p['title'], p['text'])
            update = ('UPDATE outbox SET sent_at=?, error=NULL, attempts=attempts+1 WHERE id=?', (core.stamp(), row['id']))
        except Exception as exc:
            delay = timedelta(minutes=2 ** min(row['attempts'], 6))
            update = ('UPDATE outbox SET attempts=attempts+1, error=?, next_at=? WHERE id=?',
                      (str(exc)[:200], core.stamp(core.now() + delay), row['id']))
            log.warning('Notification via %s failed: %s', p['channel'], exc)
        with core.db() as con:
            con.execute(*update)
            con.execute("DELETE FROM outbox WHERE created < ?", (core.stamp(core.now() - timedelta(days=14)),))


def recent(limit: int = 20) -> list[dict]:
    with core.db() as con:
        rows = [dict(r) for r in con.execute('SELECT * FROM outbox ORDER BY created DESC LIMIT ?', (limit,))]
    result = []
    for r in rows:
        p = json.loads(r['payload'])
        result.append({'at': r['created'], 'channel': p['channel'], 'title': p['title'], 'sent': bool(r['sent_at']),
                       'attempts': r['attempts'], 'error': r['error']})
    return result
