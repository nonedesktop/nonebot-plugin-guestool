from collections import deque
from typing import Deque, Optional
from nonebot import get_driver, logger
from nonebot.drivers.websockets import Driver as WSDriver
from websockets.client import connect, WebSocketClientProtocol

from .config import Config

driver = get_driver()
assert isinstance(driver, WSDriver)

lconfig = Config(**driver.config.dict())
"""本插件配置信息。"""
# 为避免检查器解析错误使用此变量名。

conn: Optional[WebSocketClientProtocol] = None
track: Deque[str] = deque()

@driver.on_startup
async def init_connection():
    global conn
    if not lconfig.guest_connection_hosturl:
        logger.info("[GuesTool] Not connecting to any management host as not configured")
        return
    conn = await connect(lconfig.guest_connection_hosturl)
    logger.info(f"[GuesTool] Connected to management host {lconfig.guest_connection_hosturl}")


@driver.on_shutdown
async def stop_connection():
    if conn is None:
        return
    await conn.close()
    logger.info(f"[GuesTool] Disconnected to management host {lconfig.guest_connection_hosturl}")