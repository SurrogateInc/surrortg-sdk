import asyncio
import socketio
from aiohttp import web


sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)
NAMESPACE = "/signaling"


def send_game_event(sid):
    msg = {
        "event": "config",
        "dst": "DST",
        "src": "gameEngine",
    }
    print(f"sending: {msg}")
    asyncio.run_coroutine_threadsafe(
        sio.emit("game", msg, namespace=NAMESPACE, room=sid, callback=print),
        asyncio.get_event_loop(),
    )


@sio.event(namespace=NAMESPACE)
def connect(sid, environ):
    print(f"connected: {sid}")
    send_game_event(sid)


@sio.event(namespace=NAMESPACE)
def disconnect(sid):
    print(f"disconnected: {sid}")


@sio.event(namespace=NAMESPACE)
async def game_event_request(sid):
    send_game_event(sid)
    return "SERVER OK"


@sio.event(namespace=NAMESPACE)
async def game(sid, data):
    print(f"received data :{data}")
    # send response to the client
    return "SERVER OK"


if __name__ == "__main__":
    web.run_app(app, port=5000)
