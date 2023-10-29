from typing import Any, Literal
from pydantic import UUID4, BaseModel


class Message(BaseModel):
    opid: UUID4
    opnm: str
    opct: str | int | float | bool | list[Any] | dict[str, Any] | None


class GreetMessage(Message):
    opnm: Literal["/greet/hello", "/greet/bye"]


class InfoMessage(Message):
    opnm: Literal[
        "/info/python_version", "/info/cpu", "/info/memory",
        "/info/all_partitions", "/info/all_disk_io", "/info/all_network_io",
        "/info/processes", "/info/system_platform", "/info/time",
        "/info/bots", "/info/bots_connect_time", "/info/recv_events", "/info/apicall"
    ]