from nonebot import get_driver
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    "Guest Runtime 工具",
    "NoneBot2 Guest Runtime 的集成工具，用于向外部管理程序暴露接口",
    "[无]",
    "library",
    "https://github.com/nonedesktop/nonebot-plugin-guestoole",
    Config
)

lconfig = Config.parse_obj(get_driver().config)
"""本插件配置信息。"""
# 为避免检查器解析错误使用此变量名。