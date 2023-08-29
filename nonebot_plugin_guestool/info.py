import asyncio
import json
import os
from pathlib import Path
import platform
import sys
import time
from typing import TYPE_CHECKING, List, Optional

import psutil

from .typing import (
    CPUInfoDict,
    DiskIODict,
    MemoryInfoDict,
    NetworkIODict,
    PartitionInfoDict,
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
        "cpu_perc": {
            "std": cpu,
            "normalized": normalized
        },
        "mem": mem
    }


async def info_processes(smptime: float = .1) -> List[ProcessInfoDict]:
    return [await _info_process(p, smptime) for p in psutil.process_iter()]


def _linux_name_lsbrelease() -> Optional[str]:
    lsbpath = Path("/etc/lsb-release")
    if not lsbpath.is_file():
        return
    try:
        lsb = lsbpath.read_text().strip()
    except Exception:
        return

    class _Distro:
        id: str = ""
        rel: str = ""

    _distro = _Distro()

    for lns in lsb.splitlines():
        try:
            if lns.startswith("DISTRIB_ID="):
                _distro.id = json.loads(lns[10:])
            elif lns.startswith("DISTRIB_RELEASE="):
                _distro.rel = json.loads(lns[16:])
        except Exception:
            return

    if not any((_distro.id, _distro.rel)):
        return

    return f"{_distro.id} Linux {_distro.rel}".strip()


def info_system_name() -> str:
    system, _, release, version, machine, _ = platform.uname()
    system, release, version = platform.system_alias(system, release, version)

    if system == "Java":
        _, _, _, (system, release, machine) = platform.java_ver()
    elif system == "Darwin":
        return f"MacOS {platform.mac_ver()[0]} {machine}"
    elif system == "Windows":
        return f"Windows {release} {platform.win32_edition()} {machine}"
    elif system == "Linux":
        if os.getenv("PREFIX") == "/data/data/com.termux/files/usr":
            # a strange platform
            return f"Termux (Android) {release}"
        elif os.getenv("ANDROID_ROOT") == "/system":
            return f"Linux (Android) {release}"
        elif distro := _linux_name_lsbrelease():
            return f"{distro} {machine}"
        try:
            v = Path("/etc/issue").read_text()
        except Exception:
            v = f"Linux {release}"
        else:
            v = (
                v.strip()
                .replace(r"\l", "")
                .replace(r"\n", "")
                .replace(r"\r", release)
                .replace("()", "")
                .strip()
            )
        return f"{v} {machine}"
    # strange platforms
    return f"{system} {release}"


def info_time() -> TimeInfoDict:
    now = time.time()
    return {
        "system": now - sysboot_ts,
        "nonebot": now - current_ts
    }