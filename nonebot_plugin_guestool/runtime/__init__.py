from typing import Dict, List

from . import runtime
from .matcher import extract_matcher_info_by_id, matcher_ids
from .matcher import hack_matcher_by_id as hack_matcher_by_id
from .matcher import remove_matcher_by_id as remove_matcher_by_id


def info_bots() -> List[str]:
    from nonebot import get_bots
    return [bot for bot in get_bots()]


def info_bots_connect_time() -> Dict[str, float]:
    return runtime.bot_connect_time


def info_recv_events() -> Dict[str, Dict[str, int]]:
    return runtime.recv_num


def info_apicall() -> Dict[str, Dict[str, int]]:
    return runtime.apicall_num


def list_all_matchers() -> List[str]:
    return list(matcher_ids.keys())


def get_matcher_data(id: str):
    return extract_matcher_info_by_id(id).dict()