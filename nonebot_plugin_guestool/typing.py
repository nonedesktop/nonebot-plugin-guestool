from typing import Any, Dict, Literal, TypedDict, Union


class _PythonVersionInfoDict(TypedDict):
    major: int
    minor: int
    micro: int
    release_level: str
    serial: int


class PythonVersionDict(TypedDict):
    version_string: str
    version_info: _PythonVersionInfoDict


class _CPUNCoreDict(TypedDict):
    physical: int
    logical: int


class _CPUFreqDict(TypedDict):
    current: float
    min: float
    max: float


class _CPULoadDict(TypedDict):
    last1m: float
    last5m: float
    last15m: float


class CPUInfoDict(TypedDict):
    cpu_percent: float
    cpu_ncores: _CPUNCoreDict
    cpu_freq: _CPUFreqDict
    cpu_load: _CPULoadDict


class _StorageStatDict(TypedDict):
    total: int
    available: int
    used: int
    percent: float


class MemoryInfoDict(TypedDict):
    mem: _StorageStatDict
    swap: _StorageStatDict


class PartitionNormalInfoDict(TypedDict):
    device: str
    mountpoint: str
    filesystem: str
    usage: _StorageStatDict
    error: Literal[None]


class PartitionErrorInfoDict(TypedDict):
    device: str
    mountpoint: str
    filesystem: str
    usage: Literal[None]
    error: str


PartitionInfoDict = Union[PartitionNormalInfoDict, PartitionErrorInfoDict]


class DiskIODict(TypedDict):
    device: str
    read_bytes: int
    write_bytes: int


class NetworkIODict(TypedDict):
    device: str
    sent_bytes: int
    recv_bytes: int


class ProcessInfoDict(TypedDict):
    pid: int
    name: str
    age: float
    cpu_stdperc: float
    cpu_normalized: float
    mem: int


class PlatformInfoDict(TypedDict):
    summary: str
    system: str
    release: str
    cpuarch: str


class TimeInfoDict(TypedDict):
    system: float
    nonebot: float
    system_ts: float
    nonebot_ts: float


class ConnectionMessageDict(TypedDict):
    opid: str
    opnm: str
    opct: Dict[str, Any]