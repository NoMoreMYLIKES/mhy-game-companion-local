"""Part ③/④ helpers – tool configs, processes and logs for BetterGI and ZZZ OneDragon.

Every user-owned config field we change is journaled (original value) before the
write and restored after the batch; our own BetterGI profile is regenerated each time.
"""
from __future__ import annotations

import copy
import ctypes
import hashlib
import json
import os
import re
import subprocess
import time
import uuid
from ctypes import wintypes
from pathlib import Path

import yaml

from . import core
from .i18n import tr

# Chinese strings below are identifiers of the automation tools (task names, config
# values, log lines) and must match BetterGI / OneDragon exactly; they are not UI text.
# BetterGI One Dragon tasks: auto Domain, auto Boss, auto Ley Line Outcrop, craft Condensed Resin, Stygian Onslaught.
BGI_RESIN_TASKS = ('自动秘境', '自动首领讨伐', '自动地脉花', '合成树脂', '自动幽境危战')
# Claim Mail, Serenitea Pot rewards, Daily Commission Rewards.
BGI_FREE_TASKS = {'genshin_mail': '领取邮件', 'genshin_teapot': '领取尘歌壶奖励', 'genshin_daily_reward': '领取每日奖励'}
BGI_TERMINAL = '一条龙和配置组任务结束'  # BetterGI log line: OneDragon and config group tasks finished
# Neutral morning One Dragon config (legacy task-name format, read by every BetterGI version).
BGI_TEMPLATE = Path(__file__).resolve().parent / 'templates' / 'bettergi_morning.json'
# Installer / Full packages ship the first, WithRuntime packages the second.
ZZZ_LAUNCHERS = ('OneDragon-Launcher.exe', 'OneDragon-RuntimeLauncher.exe')
ZZZ_REWARD_APPS = ('engagement_reward', 'city_fund')
ZZZ_INSTANCE = '01'
ZZZ_PATCH_MARKERS = ('game-companion collection adapter v2', 'game-companion live energy v1')
GAME_ARGS = '-screen-width {w} -screen-height {h} -screen-fullscreen 0'
NO_WINDOW = 0x08000000


def automation() -> bool:
    """Runs drive BetterGI, ZZZ OneDragon and the games, which are Windows programs. On other systems (a Linux
    host) the backend still plans, reads Miyoushe data and serves the dashboard."""
    return os.name == 'nt'


# ---------------------------------------------------------------- paths

def bgi_root() -> Path:
    return Path(core.settings()['paths']['bettergi'])


def zzz_root() -> Path:
    return Path(core.settings()['paths']['onedragon'])


def bgi_template() -> Path:
    """The BetterGI One Dragon config named in settings, else the bundled neutral template."""
    name = core.settings()['execution']['bgi_template']
    return bgi_root() / 'User/OneDragon' / (name + '.json') if name else BGI_TEMPLATE


def read_any(path: Path):
    text = Path(path).read_text(encoding='utf-8-sig')
    return json.loads(text) if Path(path).suffix == '.json' else (yaml.safe_load(text) or {})


def write_any(path: Path, value) -> None:
    path = Path(path)
    if path.suffix == '.json':
        text = json.dumps(value, ensure_ascii=False, indent=2)
    else:
        text = yaml.safe_dump(value, allow_unicode=True, sort_keys=False, default_flow_style=False)
    temp = path.with_name(path.name + '.gcl.tmp')
    temp.write_text(text, encoding='utf-8')
    os.replace(temp, path)


def ci_key(data: dict, name: str) -> str:
    """BetterGI key casing varies between versions; match case-insensitively."""
    return next((k for k in data if k.lower() == name.lower()), name)


def genshin_exe() -> Path | None:
    custom = core.settings()['paths']['genshin_exe']
    if custom:
        return Path(custom)
    try:
        config = read_any(bgi_root() / 'User/config.json')
        start = config.get(ci_key(config, 'genshinStartConfig')) or {}
        folder = start.get(ci_key(start, 'installPath')) or ''
    except (OSError, ValueError):
        return None
    if not folder:
        return None
    folder = Path(folder)
    return folder if folder.suffix.lower() == '.exe' else folder / 'YuanShen.exe'


def zzz_exe() -> Path | None:
    custom = core.settings()['paths']['zzz_exe']
    if custom:
        return Path(custom)
    try:
        data = read_any(zzz_root() / f'config/{ZZZ_INSTANCE}/game_account.yml')
    except (OSError, ValueError, yaml.YAMLError):
        return None
    folder = (data or {}).get('game_path') or ''
    if not folder:
        return None
    folder = Path(folder)
    return folder if folder.suffix.lower() == '.exe' else folder / 'ZenlessZoneZero.exe'


def game_exe(game: str) -> Path | None:
    return genshin_exe() if game == 'genshin' else zzz_exe()


def tool_exe(game: str) -> Path:
    if game == 'genshin':
        return bgi_root() / 'BetterGI.exe'
    root = zzz_root()
    return next((root / n for n in ZZZ_LAUNCHERS if (root / n).is_file()), root / ZZZ_LAUNCHERS[0])


def zzz_patch_ok() -> bool:
    try:
        source = (zzz_root() / 'src/zzz_od/application/charge_plan/charge_plan_app.py').read_text(encoding='utf-8-sig')
    except OSError:
        return False
    return all(m in source for m in ZZZ_PATCH_MARKERS)


def check() -> dict:
    """Environment check shown in settings; never raises."""
    result = {}
    for game in ('genshin', 'zzz'):
        exe, tool = game_exe(game), tool_exe(game)
        result[game] = {'game_exe': str(exe or ''), 'game_ok': bool(exe and exe.is_file()),
                        'tool_exe': str(tool), 'tool_ok': tool.is_file()}
    result['zzz']['patch_ok'] = zzz_patch_ok()
    result['genshin']['template_ok'] = bgi_template().is_file()
    result['admin'] = core.is_admin()
    return result


# ---------------------------------------------------------------- journaled field patches

def _walk(data: dict, dotted: str, create: bool = False):
    parts = dotted.split('.')
    node = data
    for part in parts[:-1]:
        key = ci_key(node, part)
        if key not in node:
            if not create:
                return None, None
            node[key] = {}
        node = node[key]
        if not isinstance(node, dict):
            return None, None
    return node, ci_key(node, parts[-1])


def patch_fields(path: Path, fields: dict) -> None:
    """Record original values in the journal, then write the new ones."""
    path = Path(path)
    data = read_any(path)
    journal = core.get('patch_journal', [])
    entry = next((e for e in journal if e['path'] == str(path)), None)
    if entry is None:
        entry = {'path': str(path), 'fields': {}}
        journal.append(entry)
    for dotted, value in fields.items():
        node, key = _walk(data, dotted, create=True)
        if node is None:
            raise ValueError(tr('patch_bad_structure', file=path.name, field=dotted))
        if dotted not in entry['fields']:  # keep the very first original
            entry['fields'][dotted] = {'existed': key in node, 'value': copy.deepcopy(node.get(key))}
        node[key] = value
    core.put('patch_journal', journal)  # journal first, then the file
    write_any(path, data)


def restore_all() -> list[str]:
    """Put every journaled field back; returns errors (journal kept on error)."""
    journal = core.get('patch_journal', [])
    errors, left = [], []
    for entry in journal:
        try:
            path = Path(entry['path'])
            data = read_any(path)
            for dotted, original in entry['fields'].items():
                node, key = _walk(data, dotted)
                if node is None:
                    continue
                if original['existed']:
                    node[key] = original['value']
                else:
                    node.pop(key, None)
            write_any(path, data)
        except Exception as exc:  # keep the entry for the next attempt
            errors.append(tr('restore_failed', file=Path(entry['path']).name, error=exc))
            left.append(entry)
    if left:
        core.put('patch_journal', left)
    else:
        core.delete('patch_journal')
    return errors


# ---------------------------------------------------------------- BetterGI

def bgi_prepare(item: dict | None) -> str:
    """Regenerate our own profile from the template; returns the profile name."""
    s = core.settings()
    folder = bgi_root() / 'User/OneDragon'
    template = bgi_template()
    name = s['execution']['bgi_profile']
    if not template.is_file():
        raise ValueError(tr('bgi_template_missing', name=template.stem))
    data = read_any(template)
    definitions = dict(data.get('TaskDefinitions') or {})
    enabled = dict(data.get('TaskEnabledList') or {})
    order = list(data.get('TaskOrder') or [])
    legacy = not definitions
    if legacy:  # old files key tasks by name and order by TaskEnabledList
        definitions = {k: k for k in enabled}
        order = list(enabled)

    def task_id(task: str) -> str:
        key = next((k for k, v in definitions.items() if v == task), None)
        if key is None:
            key = task if legacy else str(uuid.uuid4())
            definitions[key] = task
        if key not in order:
            order.append(key)
        return key

    selected = None
    if item:
        selected = task_id('自动秘境' if item['route']['kind'] == 'domain' else '自动首领讨伐')
    for key, task in definitions.items():
        if task in BGI_RESIN_TASKS:
            enabled[key] = key == selected
    free_ids = []
    for feature, task in BGI_FREE_TASKS.items():
        key = task_id(task)
        enabled[key] = bool(s['features'][feature])
        free_ids.append(key)
    # resin task first, free claims last (the daily reward after everything else)
    order = ([selected] if selected else []) + [k for k in order if k != selected and k not in free_ids] + free_ids
    order = list(dict.fromkeys(order + [k for k in definitions if k not in order]))
    data.update(Name=name, TaskDefinitions=definitions, TaskOrder=order, NextTaskId='',
                TaskEnabledList={k: bool(enabled.get(k)) for k in order}, WeeklyDomainEnabled=False)
    if legacy:
        data.pop('TaskDefinitions')
        data.pop('TaskOrder')
    if item and item['route']['kind'] == 'domain':
        claims = item['claims']
        data['DomainName'] = item['route']['name']
        if item.get('sunday'):
            data['SundayEverySelectedValue'] = item['sunday']
        priority = [f'原粹树脂{c}' for c in (40, 20) if claims['o' + str(c)]]  # Original Resin 40 / 20
        # config.json is camelCase (System.Text.Json); BetterGI ignores keys in any other case.
        patch_fields(bgi_root() / 'User/config.json', {
            'autoDomainConfig.specifyResinUse': True, 'autoDomainConfig.resinPriorityList': priority,
            'autoDomainConfig.originalResinUseCount': 0, 'autoDomainConfig.originalResin20UseCount': claims['o20'],
            'autoDomainConfig.originalResin40UseCount': claims['o40'], 'autoDomainConfig.condensedResinUseCount': 0,
            'autoDomainConfig.transientResinUseCount': 0, 'autoDomainConfig.fragileResinUseCount': 0,
            'autoDomainConfig.rewardRecognitionEnabled': True})
    elif item:
        data.update(AutoBossName=item['route']['name'], AutoBossSpecifyRunCount=True, AutoBossRunCount=item['upper'],
                    AutoBossUseTransientResin=False, AutoBossUseFragileResin=False)
    write_any(folder / (name + '.json'), data)
    return name


# BetterGI log: 'use "<resin>", amount: N' for Original / Condensed / Transient / Fragile Resin.
CLAIM = re.compile(r'使用\s*["“]?(原粹树脂|浓缩树脂|须臾树脂|脆弱树脂)["”]?\s*,?\s*数量[：:]\s*(\d+)')


def parse_bgi(text: str) -> dict:
    used = {20: 0, 40: 0}
    extra = []
    for kind, amount in CLAIM.findall(text):
        if kind == '原粹树脂' and int(amount) in used:
            used[int(amount)] += 1
        elif kind != '原粹树脂':
            extra.append(f'{kind}×{amount}')
    errors = [line.strip()[:200] for line in text.splitlines()
              if re.search(r'\[ERR|异常|失败|找不到|未解锁|传送失败', line)][-6:]
    logged = [line.strip()[:200] for line in text.splitlines() if '[ERR]' in line][-6:]  # BetterGI's error level
    return {'claims20': used[20], 'claims40': used[40], 'resin': used[20] * 20 + used[40] * 40,
            'extra': extra, 'terminal': BGI_TERMINAL in text,
            'insufficient': bool(re.search(r'树脂不足|当前可用树脂选项无法满足', text)), 'errors': errors,
            'tool_errors': logged}


# ---------------------------------------------------------------- ZZZ OneDragon

def zzz_paths() -> dict:
    cfg = zzz_root() / f'config/{ZZZ_INSTANCE}/one_dragon'
    return {'charge': cfg / 'charge_plan.yml', 'group': cfg / '_group.yml', 'env': zzz_root() / 'config/env.yml'}


def zzz_rows(run_id: str, item: dict, template: dict) -> list[dict]:
    route = item['route']
    upper = int(item['upper'])
    sizes = ([5] * (upper // 5) + ([upper % 5] if upper % 5 else [])) if item['unit'] == 'card' else [1] * upper
    token = hashlib.sha256(f"{run_id}|{item['key']}".encode()).hexdigest()[:24]
    rows = []
    for i, n in enumerate(sizes[:40]):
        # OneDragon defaults: default level, team config usable by all squads.
        rows.append({'tab_name': '训练', 'category_name': route['category'], 'mission_type_name': route['mission_type'],
                     'mission_name': route.get('mission'), 'level': template.get('level', '默认等级'),
                     'auto_battle_config': template.get('auto_battle_config', '全配队通用'),
                     'run_times': 0, 'plan_times': 1, 'card_num': str(n),
                     'predefined_team_idx': template.get('predefined_team_idx', -1),
                     'notorious_hunt_buff_num': 1, 'plan_id': f'companion-q2-{token}-{i}-c{n}'})
    return rows


def zzz_prepare(run_id: str, item: dict | None) -> list[str]:
    s = core.settings()
    p = zzz_paths()
    group = read_any(p['group'])
    apps = copy.deepcopy(group.get('app_list') or [])
    by_id = {a.get('app_id'): a for a in apps}
    if 'charge_plan' not in by_id:
        raise ValueError(tr('zzz_charge_missing'))
    by_id['charge_plan']['enabled'] = bool(item)
    fields = {'app_list': apps}
    if s['features']['zzz_rewards'] and all(k in by_id for k in ZZZ_REWARD_APPS):
        rest = [a for a in apps if a.get('app_id') not in ZZZ_REWARD_APPS]
        at = rest.index(by_id['charge_plan']) + 1
        for k in ZZZ_REWARD_APPS:
            by_id[k]['enabled'] = True
        apps[:] = rest[:at] + [by_id[k] for k in ZZZ_REWARD_APPS] + rest[at:]
        fields['companion_manual_rewards'] = True
    patch_fields(p['group'], fields)
    if not item:
        return []
    existing = read_any(p['charge'])
    template = (existing.get('plan_list') or [{}])[0] or {}
    rows = zzz_rows(run_id, item, template)
    # Disable restore_charge: never restore Battery Charge with consumables.
    patch_fields(p['charge'], {'plan_list': rows, 'loop': False, 'double_reward': False, 'restore_charge': '不使用',
                               'skip_plan': True, 'daily_reset_plan_times': False, 'companion_started': [],
                               'companion_live_energy': True, 'companion_energy_stop': None})
    if p['env'].is_file():
        patch_fields(p['env'], {'auto_update_code': False})  # keep the installed adapter for this batch
    return [r['plan_id'] for r in rows]


def zzz_receipt(plan_ids: list[str]) -> dict:
    """Completed units from the native per-row counters (read before restoring)."""
    try:
        data = read_any(zzz_paths()['charge'])
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return {'completed': None, 'reason': tr('plan_unreadable', error=exc)}
    rows = {r.get('plan_id'): r for r in data.get('plan_list') or [] if isinstance(r, dict)}
    completed = battles = 0
    for pid in plan_ids:
        row = rows.get(pid)
        if row is None or type(row.get('run_times')) is not int:
            return {'completed': None, 'reason': tr('plan_missing')}
        if row['run_times'] >= 1:
            battles += 1
            # Combat Simulation runs count their cards; other battles count once.
            completed += int(row.get('card_num') or 1) if row.get('category_name') == '实战模拟室' else 1
    stop = data.get('companion_energy_stop')
    return {'completed': completed, 'battles': battles, 'energy_stop': stop if isinstance(stop, dict) else None}


def _last_outcome(text: str, command: str) -> str | None:
    """How a OneDragon command ended: its last 'succeeded' / 'failed' line (a retry can follow a failure,
    a failure can follow an earlier success). None without one."""
    found = re.findall(r'指令\[\s*' + command + r'\s*\]\s*执行(成功|失败)', text)
    return None if not found else 'success' if found[-1] == '成功' else 'failed'


def parse_zzz(text: str) -> dict:
    # OneDragon log lines: command [OneDragon] / [Charge Plan] succeeded or failed, remaining
    # battery, battle node finished, cards used by the plan this battle.
    one = _last_outcome(text, '一条龙')
    charge = _last_outcome(text, '体力刷本')
    remaining = [int(x) for x in re.findall(r'剩余电量\s*[:：]?\s*(\d+)', text)]
    errors = [line.strip()[:200] for line in text.splitlines()
              if re.search(r'\[ERR|执行失败|找不到|未解锁|Traceback', line)][-6:]
    return {'one_dragon': one, 'charge': charge, 'battles': len(re.findall(r'节点\s*战斗结束\s*->', text)),
            'cards_logged': sum(int(x) for x in re.findall(r'养成清单 本场 (\d+) 张卡', text)),
            'last_energy': remaining[-1] if remaining else None, 'errors': errors}


# ---------------------------------------------------------------- logs

def log_files(game: str) -> list[Path]:
    if game == 'genshin':
        return sorted((bgi_root() / 'log').glob('better-genshin-impact*.log'))
    return sorted((zzz_root() / '.log').glob('log.txt*'))


def _prefix(path: Path, size: int) -> str:
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read(min(size, 4096))).hexdigest()


def log_baseline(game: str) -> dict:
    result = {}
    for p in log_files(game):
        try:
            size = p.stat().st_size
            result[str(p)] = [size, _prefix(p, size)]
        except OSError:
            continue
    return result


def read_new(game: str, baseline: dict) -> str:
    """Bytes appended since the baseline; a rotated/replaced file is read whole."""
    parts = []
    for p in log_files(game):
        try:
            size = p.stat().st_size
            offset = 0
            old = baseline.get(str(p))
            if old and size >= old[0] and _prefix(p, old[0]) == old[1]:
                offset = old[0]
            if size > offset:
                with open(p, 'rb') as f:
                    f.seek(offset)
                    parts.append(f.read(8_000_000).decode('utf-8', errors='replace'))
        except OSError:
            continue
    return '\n'.join(parts)


# ---------------------------------------------------------------- processes

def _pids() -> list[int]:
    arr = (wintypes.DWORD * 4096)()
    needed = wintypes.DWORD()
    if not ctypes.windll.psapi.EnumProcesses(arr, ctypes.sizeof(arr), ctypes.byref(needed)):
        return []
    return [arr[i] for i in range(needed.value // ctypes.sizeof(wintypes.DWORD)) if arr[i]]


def _image(pid: int) -> str | None:
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(1024)
        if ctypes.windll.kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
            return buf.value
        return None
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def pids_by_path(path: Path | str | None) -> list[int]:
    if not path or os.name != 'nt':
        return []
    want = os.path.normcase(str(path))
    return [pid for pid in _pids() if (_image(pid) and os.path.normcase(_image(pid)) == want)]


def running(path) -> bool:
    return bool(pids_by_path(path))


def kill_tree(pid: int) -> None:
    subprocess.run(['taskkill', '/PID', str(pid), '/T', '/F'], capture_output=True, creationflags=NO_WINDOW, timeout=30)


def kill_path(path) -> None:
    for pid in pids_by_path(path):
        kill_tree(pid)


def start(path: Path, args: list[str], cwd: Path | None = None, hidden: bool = False) -> subprocess.Popen:
    info = subprocess.STARTUPINFO()
    if hidden:
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = 0
    return subprocess.Popen([str(path), *args], cwd=str(cwd or Path(path).parent), startupinfo=info,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)


def launch_game(game: str) -> subprocess.Popen:
    exe = game_exe(game)
    if not exe or not exe.is_file():
        raise ValueError(tr('game_missing', path=exe or tr('not_configured')))
    e = core.settings()['execution']
    return start(exe, GAME_ARGS.format(w=e['window_width'], h=e['window_height']).split())


# ---------------------------------------------------------------- game window input (inventory scans)
# Scanners need their screen opened first: a key press and a few clicks at 1920×1080 positions, scaled
# to the game's client area. SendInput with scan codes, which games read as raw input.

KEYEVENTF_KEYUP, KEYEVENTF_SCANCODE = 0x0002, 0x0008
MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0002, 0x0004
VK = {'B': 0x42, 'ALT': 0x12, 'ESC': 0x1B}


class _KeyInput(ctypes.Structure):
    _fields_ = [('wVk', wintypes.WORD), ('wScan', wintypes.WORD), ('dwFlags', wintypes.DWORD),
                ('time', wintypes.DWORD), ('dwExtraInfo', ctypes.c_size_t)]


class _MouseInput(ctypes.Structure):
    _fields_ = [('dx', wintypes.LONG), ('dy', wintypes.LONG), ('mouseData', wintypes.DWORD),
                ('dwFlags', wintypes.DWORD), ('time', wintypes.DWORD), ('dwExtraInfo', ctypes.c_size_t)]


class _InputUnion(ctypes.Union):
    _fields_ = [('ki', _KeyInput), ('mi', _MouseInput)]


class _Input(ctypes.Structure):
    _fields_ = [('type', wintypes.DWORD), ('u', _InputUnion)]


def _send(*events: _Input) -> None:
    ctypes.windll.user32.SendInput(len(events), (_Input * len(events))(*events), ctypes.sizeof(_Input))


def _key_event(vk: int, up: bool = False) -> _Input:
    scan = ctypes.windll.user32.MapVirtualKeyW(vk, 0)
    return _Input(type=1, u=_InputUnion(ki=_KeyInput(0, scan, KEYEVENTF_SCANCODE | (KEYEVENTF_KEYUP if up else 0), 0, 0)))


def _mouse_event(flags: int) -> _Input:
    return _Input(type=0, u=_InputUnion(mi=_MouseInput(0, 0, 0, flags, 0, 0)))


def key(name: str, hold: float = 0.08) -> None:
    _send(_key_event(VK[name]))
    time.sleep(hold)
    _send(_key_event(VK[name], up=True))


def game_window(path) -> int | None:
    """The visible top-level window of the game process, or None."""
    user32 = ctypes.windll.user32
    try:  # physical pixels for window sizes and cursor positions
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        pass
    pids = set(pids_by_path(path))
    found: list[int] = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def each(hwnd, _):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in pids and user32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    user32.EnumWindows(each, 0)
    return found[0] if found else None


def focus(hwnd: int) -> None:
    """Bring the game to the front (an Alt tap lets a background process take the foreground)."""
    ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    _send(_key_event(VK['ALT']), _key_event(VK['ALT'], up=True))
    ctypes.windll.user32.SetForegroundWindow(hwnd)


def click(hwnd: int, x: int, y: int, alt: bool = False) -> None:
    """Left click at a 1920×1080 position, scaled to the window's client area; ``alt`` holds Alt (ZZZ frees the cursor)."""
    user32 = ctypes.windll.user32
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    point = wintypes.POINT(int(x * rect.right / 1920), int(y * rect.bottom / 1080))
    user32.ClientToScreen(hwnd, ctypes.byref(point))
    if alt:
        _send(_key_event(VK['ALT']))
        time.sleep(0.3)
    user32.SetCursorPos(point.x, point.y)
    time.sleep(0.15)
    _send(_mouse_event(MOUSEEVENTF_LEFTDOWN))
    time.sleep(0.08)
    _send(_mouse_event(MOUSEEVENTF_LEFTUP))
    if alt:
        time.sleep(0.2)
        _send(_key_event(VK['ALT'], up=True))


# ---------------------------------------------------------------- audio (PowerShell 7 only)

PWSH = r'C:\Program Files\PowerShell\7\pwsh.exe'


def audio(action: str, endpoint: str = '', muted: bool = False) -> dict:
    script = core.APP / 'tools/audio.ps1'
    if not Path(PWSH).is_file():
        raise ValueError(tr('mute_pwsh_missing'))
    args = [PWSH, '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script), '-Action', action]
    if endpoint:
        args += ['-Endpoint', endpoint, '-Muted', 'true' if muted else 'false']
    out = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', creationflags=NO_WINDOW, timeout=60)
    if out.returncode != 0:
        raise ValueError((out.stderr or out.stdout or tr('mute_script_failed')).strip()[:200])
    return json.loads(out.stdout.strip().splitlines()[-1])
