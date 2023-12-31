import asyncio
import json
from contextlib import suppress
from inspect import isawaitable
from typing import Optional
from uuid import uuid4

from nonebot import get_driver, logger
from websockets.client import WebSocketClientProtocol, connect
from websockets.exceptions import ConnectionClosed

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
    info_time,
)
from .runtime import (
    get_matcher_data,
    hack_matcher_by_id,
    info_apicall,
    info_bots,
    info_bots_connect_time,
    info_recv_events,
    list_all_matchers,
    remove_matcher_by_id,
)
from .typing import ConnectionMessageDict

driver = get_driver()

lconfig = Config(**driver.config.dict())
"""本插件配置信息。"""
# 为避免检查器解析错误使用此变量名。

conn: Optional[WebSocketClientProtocol] = None
conn_task: Optional[asyncio.Task] = None
_conn_restart_task: Optional[asyncio.Task] = None
_conn_queue: asyncio.Queue[asyncio.Task] = asyncio.Queue()

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

action_funcs = {
    "matcher/list": list_all_matchers,
    "matcher/info": get_matcher_data,
    "matcher/hack": hack_matcher_by_id,
    "matcher/remove": remove_matcher_by_id
}


async def _loop_process(data: ConnectionMessageDict):
    assert conn
    if data["opnm"] == "/greet/bye":
        await conn.send(json.dumps(data))
        await conn.close()
    elif data["opnm"].startswith("/info"):
        try:
            res = info_funcs[data["opnm"][6:]](**data["opct"])
            if isawaitable(res):
                res = await res
        except KeyError as e:
            res = {"error": "unknown info type"}
            logger.opt(exception=e).warning("Received a wrong info type from server!")
        await conn.send(
            json.dumps(
                ConnectionMessageDict(
                    opid=data["opid"], opnm="/event/report/info", opct=res
                )
            )
        )
    elif data["opnm"].startswith("/action"):
        try:
            res = info_funcs[data["opnm"][8:]](**data["opct"])
            if isawaitable(res):
                res = await res
        except KeyError as e:
            res = {"error": "unknown action type"}
            logger.opt(exception=e).warning("Received a wrong action type from server!")
        await conn.send(
            json.dumps(
                ConnectionMessageDict(
                    opid=data["opid"], opnm="/event/report/action", opct=res
                )
            )
        )


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

    with suppress(ConnectionClosed):
        while conn.open:
            data: ConnectionMessageDict = json.loads(await conn.recv())
            logger.trace(f"Received {data!r}")
            await _conn_queue.put(asyncio.create_task(_loop_process(data)))

    while not _conn_queue.empty():
        (await _conn_queue.get()).cancel()

    logger.info(f"Disconnected to management host {lconfig.guest_connection_hosturl}")


@driver.on_startup
async def init_connection():
    global conn, conn_task, _conn_restart_task
    if not lconfig.guest_connection_hosturl:
        logger.info("Not connecting to any management host as not configured")
        return
    if _conn_restart_task:
        await asyncio.sleep(5)
    try:
        conn = await connect(lconfig.guest_connection_hosturl)
        logger.info(f"Connected to management host {lconfig.guest_connection_hosturl!r}")
        conn_task = asyncio.create_task(conn_loop())
    except ConnectionRefusedError:
        logger.warning(f"Failed to connect to host {lconfig.guest_connection_hosturl!r}, is your host accessible?")
        _conn_restart_task = asyncio.create_task(init_connection())


@driver.on_shutdown
async def stop_connection():
    if conn:
        await conn.close()
    if conn_task:
        conn_task.cancel()
    if _conn_restart_task:
        _conn_restart_task.cancel()