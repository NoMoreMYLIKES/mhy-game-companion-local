"""Process and socket facts used to verify an instance and to explain a busy port.

Windows uses the documented Win32 calls; the Linux branch exists so the launcher can be
tested on any machine. Every function returns None (or False) when a fact cannot be read,
so callers can say "unavailable" instead of guessing.
"""
from __future__ import annotations

import os
import struct
import subprocess
import sys
import time

WINDOWS = os.name == 'nt'

if WINDOWS:
    import ctypes
    from ctypes import wintypes

    _k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    _k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _k32.OpenProcess.restype = wintypes.HANDLE
    _k32.CloseHandle.argtypes = [wintypes.HANDLE]
    _k32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    _k32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    _k32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                                ctypes.POINTER(wintypes.DWORD)]
    _QUERY_LIMITED = 0x1000
    _STILL_ACTIVE = 259
    _ACCESS_DENIED = 5


def _open(pid: int):
    return _k32.OpenProcess(_QUERY_LIMITED, False, int(pid))


def alive(pid: int) -> bool:
    if not pid or pid <= 0:
        return False
    if WINDOWS:
        handle = _open(pid)
        if not handle:
            return ctypes.get_last_error() == _ACCESS_DENIED  # exists, but we may not look at it
        try:
            code = wintypes.DWORD()
            return bool(_k32.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == _STILL_ACTIVE
        finally:
            _k32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:  # a zombie is not running
        with open(f'/proc/{pid}/stat', encoding='ascii') as f:
            return f.read().rsplit(')', 1)[1].split()[0] != 'Z'
    except OSError:
        return True


def created(pid: int) -> float | None:
    """When the operating system created the process (epoch seconds); guards against PID reuse."""
    if WINDOWS:
        handle = _open(pid)
        if not handle:
            return None
        try:
            times = [wintypes.FILETIME() for _ in range(4)]
            if not _k32.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
                return None
            ticks = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime  # 100 ns since 1601
            return ticks / 1e7 - 11644473600
        finally:
            _k32.CloseHandle(handle)
    try:
        with open(f'/proc/{pid}/stat', encoding='ascii') as f:
            start_ticks = int(f.read().rsplit(')', 1)[1].split()[19])
        with open('/proc/stat', encoding='ascii') as f:
            boot = next(int(line.split()[1]) for line in f if line.startswith('btime'))
        return boot + start_ticks / os.sysconf('SC_CLK_TCK')
    except (OSError, ValueError, StopIteration):
        return None


def image(pid: int) -> str | None:
    """Full path of the process executable."""
    if WINDOWS:
        handle = _open(pid)
        if not handle:
            return None
        try:
            size = wintypes.DWORD(1024)
            buffer = ctypes.create_unicode_buffer(size.value)
            if _k32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                return buffer.value
            return None
        finally:
            _k32.CloseHandle(handle)
    try:
        return os.readlink(f'/proc/{pid}/exe')
    except OSError:
        return None


def same_process(pid: int, created_at: float | None, image_path: str | None) -> bool | None:
    """True when ``pid`` is still the process that was recorded, False when it is not, None when unknown."""
    if not alive(pid):
        return False
    now_created = created(pid)
    if created_at is not None and now_created is not None and abs(now_created - created_at) > 2:
        return False
    now_image = image(pid)
    if image_path and now_image and os.path.normcase(now_image) != os.path.normcase(image_path):
        return False
    if created_at is None or now_created is None:
        return None
    return True


def terminate(pid: int) -> str | None:
    """Force-stop one process (and its children on Windows); returns an error message or None."""
    if WINDOWS:
        try:
            out = subprocess.run(['taskkill', '/PID', str(pid), '/T', '/F'], capture_output=True, text=True,
                                 errors='replace', timeout=30, creationflags=0x08000000)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return str(exc)
        return None if out.returncode == 0 else (out.stderr or out.stdout).strip() or f'taskkill exit {out.returncode}'
    try:
        os.kill(pid, 15)
    except ProcessLookupError:
        return None
    except PermissionError as exc:
        return str(exc)
    for _ in range(50):
        if not alive(pid):
            return None
        time.sleep(0.1)
    try:
        os.kill(pid, 9)
    except ProcessLookupError:
        return None
    except PermissionError as exc:
        return str(exc)
    return None


def port_from_dword(value: int) -> int:
    """MIB_TCPROW ports are stored in network byte order in the low 16 bits."""
    return ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)


def port_owner(port: int) -> int | None:
    """PID of the process listening on a local TCP port, if the system will tell us."""
    if WINDOWS:
        return _windows_listener(port)
    return _linux_listener(port)


def _windows_listener(port: int) -> int | None:
    iphlpapi = ctypes.WinDLL('iphlpapi')
    # (address family, row size, offset of the port DWORD, offset of the owning PID DWORD)
    for family, row, port_at, pid_at in ((2, 24, 8, 20), (23, 56, 20, 52)):
        size = wintypes.DWORD(0)
        iphlpapi.GetExtendedTcpTable(None, ctypes.byref(size), False, family, 3, 0)  # 3: listeners with PIDs
        for _ in range(3):  # the table may grow between the size query and the read
            buffer = ctypes.create_string_buffer(size.value + 4096)
            size = wintypes.DWORD(len(buffer))
            result = iphlpapi.GetExtendedTcpTable(buffer, ctypes.byref(size), False, family, 3, 0)
            if result != 122:  # ERROR_INSUFFICIENT_BUFFER
                break
        if result != 0:
            continue
        raw = buffer.raw
        count = struct.unpack_from('<I', raw, 0)[0]
        for i in range(count):
            base = 4 + i * row
            if port_from_dword(struct.unpack_from('<I', raw, base + port_at)[0]) == port:
                return struct.unpack_from('<I', raw, base + pid_at)[0]
    return None


def _linux_listener(port: int) -> int | None:
    inodes = set()
    for table in ('/proc/net/tcp', '/proc/net/tcp6'):
        try:
            with open(table, encoding='ascii') as f:
                next(f)
                for line in f:
                    parts = line.split()
                    if parts[3] == '0A' and int(parts[1].rsplit(':', 1)[1], 16) == port:
                        inodes.add(parts[9])
        except (OSError, ValueError, IndexError):
            continue
    if not inodes:
        return None
    for pid in (p for p in os.listdir('/proc') if p.isdigit()):
        try:
            for fd in os.listdir(f'/proc/{pid}/fd'):
                link = os.readlink(f'/proc/{pid}/fd/{fd}')
                if link.startswith('socket:[') and link[8:-1] in inodes:
                    return int(pid)
        except OSError:
            continue
    return None


def describe(pid: int | None) -> str:
    """'name.exe (PID 123)', or a note that the owner could not be read."""
    if not pid:
        return 'an unknown process (the system did not report its owner)'
    path = image(pid)
    return f'{os.path.basename(path)} (PID {pid})' if path else f'PID {pid} (its name is unavailable to this account)'


if __name__ == '__main__':  # pragma: no cover - manual diagnostics
    print(describe(port_owner(int(sys.argv[1]))))
