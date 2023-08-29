from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    guest_connection_hosturl: str = ""
    """主机侧 WebSocket 连接地址，只应由主机侧通过环境变量设置。"""