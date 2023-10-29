import asyncio
import json
import shlex
from uuid import uuid4
from pydantic import ValidationError
import websockets
from websockets.server import WebSocketServerProtocol
from models import GreetMessage, Message


async def input_loop(ws: WebSocketServerProtocol):
    cmd = ""
    while not ws.closed:
        c, param = "", []
        spl = shlex.split(cmd)
        if spl:
            c, *param = spl

        if not c:
            pass
        elif c == "q":
            break
        elif len(param) != 2:
            print("[INPUTLOOP] Not enough params")
        else:
            onm, prm = param
            if c == "info":
                await ws.send(json.dumps(dict(opid=str(uuid4()), opnm=f"/info/{onm}", opct=json.loads(prm))))  # type: ignore
        cmd = await asyncio.to_thread(input, "HOST>>> ")
    await ws.send(json.dumps(dict(opid=str(uuid4()), opnm="/greet/bye", opct={})))


async def server_loop(websocket: WebSocketServerProtocol):
    data = await websocket.recv()
    try:
        xdata = Message(**json.loads(data))
        xdata = GreetMessage.parse_obj(xdata)
        assert xdata.opnm == "/greet/hello"
    except (ValidationError, AssertionError):
        print(f"[GREET] Not a greet packet, closing... (received {data!r})")
        await websocket.close()
        return

    await websocket.send(data)

    task = asyncio.create_task(input_loop(websocket))

    while websocket.open:
        data = await websocket.recv()
        xdata = Message(**json.loads(data))
        print(f"[SERVERLOOP] Received data {xdata!r}")
        if xdata.opnm == "/greet/bye":
            await websocket.close()
        # resp = ""
        # await websocket.send(resp)

    await task


async def run(host: str, port: int):
    async with websockets.serve(server_loop, host, port):  # type: ignore
        await asyncio.Future()  # run forever