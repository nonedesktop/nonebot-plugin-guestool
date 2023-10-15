import time
from typing import Dict, Optional

from nonebot import get_driver, on
from nonebot.adapters import Bot, Event

bot_connect_time: Dict[str, float] = {}
recv_num: Dict[str, Dict[str, int]] = {}
apicall_num: Dict[str, Dict[str, int]] = {}

driver = get_driver()


async def called_api(bot: Bot, exc: Optional[Exception], api: str, _, __):
    if exc:
        return

    apicall_num.setdefault(bot.self_id, {})
    apicall_num[bot.self_id].setdefault(api, 0)
    apicall_num[bot.self_id][api] += 1


@driver.on_bot_connect
async def _(bot: Bot):
    bot_id = bot.self_id
    bot_connect_time[bot_id] = time.time()

    if bot_id not in apicall_num:
        apicall_num[bot_id] = {}

    if bot_id not in recv_num:
        recv_num[bot_id] = {"metaevent": 0, "message": 0, "notice": 0, "request": 0}

    bot.on_called_api(called_api)


def add_recv(bot: Bot, event: Event):
    name = event.__class__.__qualname__

    recv_num.setdefault(bot.self_id, {})
    recv_num[bot.self_id].setdefault(name, 0)
    recv_num[bot.self_id][name] += 1


recv_matcher = on(handlers=[add_recv], priority=0, block=False)