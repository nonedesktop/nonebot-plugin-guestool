import asyncio
from collections import deque
from inspect import isawaitable
import json
from typing import Deque, Optional
from uuid import uuid4
from nonebot import get_driver, logger
from websockets.client import connect, WebSocketClientProtocol

from .config import Config
from .info import (
    info_all_disk_io,
    info_all_network_io,
    info_all_partition,
    info_cpu,
    info_memory,
    info_processes,
    info_python_version,
    info_system_platform,
    info_time
)
from .runtime import (
    info_apicall, info_bots, info_bots_connect_time, info_recv_events
)
from .typing import ConnectionMessageDict

driver = get_driver()

lconfig = Config(**driver.config.dict())
"""本插件配置信息。"""
# 为避免检查器解析错误使用此变量名。

conn: Optional[WebSocketClientProtocol] = None
conn_task: asyncio.Task
track: Deque[str] = deque()

info_funcs = {
    "python_version": info_python_version,
    "cpu": info_cpu,
    "memory": info_memory,
    "all_partitions": info_all_partition,
    "all_disk_io": info_all_disk_io,
    "all_network_io": info_all_network_io,
    "processes": info_processes,
    "system_platform": info_system_platform,
    "time": info_time,
    "bots": info_bots,
    "bots_connect_time": info_bots_connect_time,
    "recv_events": info_recv_events,
    "apicall": info_apicall,
}


async def conn_loop():
    assert conn
    hello = json.dumps({"opid": str(uuid4()), "opnm": "/greet/hello", "opct": {}})
    await conn.send(hello)
    try:
        async with asyncio.timeout(60):
            assert await conn.recv() == hello
    except asyncio.TimeoutError:
        logger.error("Connection timed out after 1 minute, disconnecting...")
        await conn.close()
    except AssertionError:
        logger.error("Unexpected response, disconnecting...")
        await conn.close()

    while conn.open:
        data: ConnectionMessageDict = json.loads(await conn.recv())
        logger.trace(f"Received {data!r}")
        if data["opnm"].startswith("/info"):
            res = info_funcs[data["opnm"][6:]](**data["opct"])
            if isawaitable(res):
                res = await res
            await conn.send(
                json.dumps(
                    ConnectionMessageDict(
                        opid=data["opid"], opnm="/event/report/info", opct=res
                    )
                )
            )


@driver.on_startup
async def init_connection():
    global conn, conn_task
    if not lconfig.guest_connection_hosturl:
        logger.info("[GuesTool] Not connecting to any management host as not configured")
        return
    conn = await connect(lconfig.guest_connection_hosturl)
    logger.info(f"[GuesTool] Connected to management host {lconfig.guest_connection_hosturl}")
    conn_task = asyncio.create_task(conn_loop())


@driver.on_shutdown
async def stop_connection():
    if conn is None:
        return
    conn_task.cancel()
    await conn.close()
    logger.info(f"[GuesTool] Disconnected to management host {lconfig.guest_connection_hosturl}")