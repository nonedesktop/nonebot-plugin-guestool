import asyncio
import os
from pathlib import Path
import platform
import shlex
import sys
import time
from typing import TYPE_CHECKING, List, Optional, Union

import psutil

from .typing import (
    CPUInfoDict,
    DiskIODict,
    MemoryInfoDict,
    NetworkIODict,
    PartitionInfoDict,
    PlatformInfoDict,
    ProcessInfoDict,
    PythonVersionDict,
    TimeInfoDict
)

if TYPE_CHECKING:
    import psutil._common

sysboot_ts = psutil.boot_time()
current_ts = psutil.Process().create_time()


def info_python_version() -> PythonVersionDict:
    ver = sys.version_info
    return {
        "version_string": sys.version,
        "version_info": {
            "major": ver.major,
            "minor": ver.minor,
            "micro": ver.micro,
            "release_level": ver.releaselevel,
            "serial": ver.serial
        }
    }


async def info_cpu(smptime: float = .1) -> CPUInfoDict:
    """CPU usage info
    
    Args:
    - smptime: sample time for `psutil.cpu_percent()`, values <= 0 will use the last\
      sampling time.
    """
    if smptime > 0:
        psutil.cpu_percent()
    await asyncio.sleep(max(0, smptime))
    cpu_percent = psutil.cpu_percent()

    cpu_count = psutil.cpu_count(logical=False)
    cpu_count_logical = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    cpu_load = psutil.getloadavg()

    return {
        "cpu_percent": cpu_percent,
        "cpu_ncores": {
            "physical": cpu_count,
            "logical": cpu_count_logical
        },
        "cpu_freq": {
            "current": cpu_freq.current,
            "min": cpu_freq.min,
            "max": cpu_freq.max
        },
        "cpu_load": {
            "last1m": cpu_load[0],
            "last5m": cpu_load[1],
            "last15m": cpu_load[2]
        }
    }


def info_memory() -> MemoryInfoDict:
    mem_stat = psutil.virtual_memory()
    swap_stat = psutil.swap_memory()

    return {
        "mem": {
            "total": mem_stat.total,
            "available": mem_stat.available,
            "used": mem_stat.used,
            "percent": mem_stat.percent
        },
        "swap": {
            "total": swap_stat.total,
            "available": swap_stat.free,
            "used": swap_stat.used,
            "percent": swap_stat.percent
        }
    }


def _info_partition(part: "psutil._common.sdiskpart") -> PartitionInfoDict:
    mnt = part.mountpoint
    fs = part.fstype
    dev = part.device
    try:
        usage = psutil.disk_usage(mnt)
    except Exception as e:
        return {
            "device": dev,
            "mountpoint": mnt,
            "filesystem": fs,
            "usage": None,
            "error": str(e)
        }
    return {
        "device": dev,
        "mountpoint": mnt,
        "filesystem": fs,
        "usage": {
            "total": usage.total,
            "available": usage.free,
            "used": usage.used,
            "percent": usage.percent
        },
        "error": None
    }


def info_all_partition(physical_only: bool = True) -> List[PartitionInfoDict]:
    return [_info_partition(x) for x in psutil.disk_partitions(not physical_only)]


def _info_disk_io(
    device: str, ref: "psutil._common.sdiskio", cur: "psutil._common.sdiskio"
) -> DiskIODict:
    return {
        "device": device,
        "read_bytes": cur.read_bytes - ref.read_bytes,
        "write_bytes": cur.write_bytes - ref.write_bytes
    }


async def info_all_disk_io(smptime: float = 1.) -> List[DiskIODict]:
    ref = psutil.disk_io_counters(True)
    await asyncio.sleep(smptime)
    cur = psutil.disk_io_counters(True)

    return [_info_disk_io(dev, ref[dev], cur[dev]) for dev in ref if dev in cur]


def _info_network_io(
    device: str, ref: "psutil._common.snetio", cur: "psutil._common.snetio"
) -> NetworkIODict:
    return {
        "device": device,
        "sent_bytes": cur.bytes_sent - ref.bytes_sent,
        "recv_bytes": cur.bytes_recv - ref.bytes_recv
    }


async def info_all_network_io(smptime: float = 1.) -> List[NetworkIODict]:
    ref = psutil.net_io_counters(True)
    await asyncio.sleep(smptime)
    cur = psutil.net_io_counters(True)

    return [_info_network_io(dev, ref[dev], cur[dev]) for dev in ref if dev in cur]


async def _info_process(proc: psutil.Process, smptime: float = .1) -> ProcessInfoDict:
    proc.cpu_percent()
    await asyncio.sleep(smptime)
    with proc.oneshot():
        name = proc.name()
        age = time.time() - proc.create_time()
        cpu = proc.cpu_percent()
        pid = proc.pid
        mem: int = proc.memory_info().rss
    normalized = cpu / psutil.cpu_count()
    return {
        "pid": pid,
        "name": name,
        "age": age,
        "cpu_stdperc": cpu,
        "cpu_normalized": normalized,
        "mem": mem
    }


async def info_processes(smptime: float = .1) -> List[ProcessInfoDict]:
    return [await _info_process(p, smptime) for p in psutil.process_iter()]


def _linux_name_envlike_parse(
    path: Union[str, Path],
    distid_key: str,
    distrel_key: str,
    distrel_alt_key: Optional[str] = None,
    keep_linux_name: bool = False
) -> Optional[str]:
    relpath = Path(path)
    if not relpath.is_file():
        return
    try:
        rel = relpath.read_text().strip()
    except Exception:
        return

    class _Distro:
        id: str = ""
        rel: str = ""
        rel1: str = ""

    _distro = _Distro()

    for lns in rel.splitlines():
        try:
            if lns.startswith(f"{distid_key}="):
                _distro.id, = shlex.split(lns[len(distid_key) + 1:])
            elif lns.startswith(f"{distrel_key}="):
                _distro.rel, = shlex.split(lns[len(distrel_key) + 1:])
            elif distrel_alt_key and lns.startswith(f"{distrel_alt_key}="):
                _distro.rel1, = shlex.split(lns[len(distrel_alt_key) + 1:])
        except Exception:
            return

    if not any((_distro.id, _distro.rel, _distro.rel1)):
        return
    
    _distro.rel = _distro.rel or _distro.rel1
    
    if keep_linux_name and not _distro.id.endswith("Linux"):
        _distro.id += " Linux"

    return f"{_distro.id} {_distro.rel}".strip()


def _linux_name_osrelease() -> Optional[str]:
    return _linux_name_envlike_parse(
        "/etc/os-release", "NAME", "VERSION", "BUILD_ID", True
    )


def _linux_name_lsbrelease() -> Optional[str]:
    return _linux_name_envlike_parse(
        "/etc/lsb-release",
        "DISTRIB_ID",
        "DISTRIB_RELEASE",
        keep_linux_name=True
    )


# def _linux_name_issue() -> Optional[str]:
#     # [!!] Not reliable
#     relpath = Path("/etc/issue")
#     if not relpath.is_file():
#         return
#     try:
#         rel = relpath.read_text().strip()
#     except Exception:
#         return
#     return (
#         rel
#         .replace(r"\l", "")
#         .replace(r"\n", "")
#         .replace(r"\r", "{release}")
#         .replace("()", "")
#         .strip()
#     )


def info_system_platform() -> PlatformInfoDict:
    system, _, release, version, machine, _ = platform.uname()
    system, release, version = platform.system_alias(system, release, version)

    if system == "Java":
        _, _, _, (system, release, machine) = platform.java_ver()

    if system == "Darwin":
        system, release = "MacOS", platform.mac_ver()[0]
    elif system == "Windows":
        release = f"{release} {platform.win32_edition()}"
    elif system == "Linux":
        if os.getenv("PREFIX") == "/data/data/com.termux/files/usr":
            # a strange platform
            system = "Termux (Android)"
        elif os.getenv("ANDROID_ROOT") == "/system":
            system = "Linux (Android)"
        elif distro := _linux_name_osrelease() or _linux_name_lsbrelease():
            system = distro
        # _issue = _linux_name_issue() or "Linux {release}"
        # return f"{_issue.format(release=release)} {machine}"

    return {
        "summary": f"{system} {release} {machine}",
        "system": system,
        "release": release,
        "cpuarch": machine
    }


def info_time() -> TimeInfoDict:
    now = time.time()
    return {
        "system": now - sysboot_ts,
        "nonebot": now - current_ts,
        "system_ts": sysboot_ts,
        "nonebot_ts": current_ts
    }