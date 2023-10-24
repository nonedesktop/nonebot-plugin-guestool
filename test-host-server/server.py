import asyncio
import json
import shlex
from uuid import uuid4
from pydantic import ValidationError
import websockets
from websockets.server import WebSocketServerProtocol
from models import GreetMessage, InfoMessage, Message


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
        elif len(param) != 3:
            print("[INPUTLOOP] Not enough params")
        else:
            ct, onm, prm = param
            if ct == "info":
                await ws.send(json.dumps(InfoMessage(opid=uuid4(), opnm=f"/info/{onm}", opct=json.loads(prm))))  # type: ignore
        cmd = await asyncio.to_thread(input, "HOST>>> ")
    await ws.send(json.dumps(GreetMessage(opid=uuid4(), opnm="/greet/bye", opct={})))


async def server_loop(websocket: WebSocketServerProtocol):
    data = await websocket.recv()
    try:
        data = Message(**json.loads(data))
        data = GreetMessage.parse_obj(data)
        assert data.opnm == "/greet/hello"
    except (ValidationError, AssertionError):
        print(f"[GREET] Not a greet packet, closing... (received {data!r})")
        await websocket.close()
        return

    await websocket.send(json.dumps(data.dict()))

    task = asyncio.create_task(input_loop(websocket))

    while websocket.open:
        data = await websocket.recv()
        data = Message(**json.loads(data))
        print(f"[SERVERLOOP] Received data {data!r}")
        if data.opnm == "/greet/bye":
            await websocket.close()
        # resp = ""
        # await websocket.send(resp)

    await task


async def run(host: str, port: int):
    async with websockets.serve(server_loop, host, port):  # type: ignore
        await asyncio.Future()  # run forever