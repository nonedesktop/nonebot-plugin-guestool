from typing import Dict, List

from . import runtime


def info_bots() -> List[str]:
    from nonebot import get_bots
    return [bot for bot in get_bots()]


def info_bots_connect_time() -> Dict[str, float]:
    return runtime.bot_connect_time


def info_recv_events() -> Dict[str, Dict[str, int]]:
    return runtime.recv_num


def info_apicall() -> Dict[str, Dict[str, int]]:
    return runtime.apicall_num