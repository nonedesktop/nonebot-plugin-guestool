from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    "Guest Runtime 工具",
    "NoneBot2 Guest Runtime 的集成工具，用于向外部管理程序暴露接口",
    "[无]",
    "library",
    "https://github.com/nonedesktop/nonebot-plugin-guestool",
    Config
)

from . import (  # noqa: E402
    info as info, runtime as runtime, connection as connection
)