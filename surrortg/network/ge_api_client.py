import asyncio
import functools
import logging

import socketio

SOCKETIO_NAMESPACE = "/api"


class GEConnectionError(Exception):
    pass


class ApiClient(socketio.AsyncClientNamespace):
    def __init__(self, client_id, url, game_id, token, message_listener=None):
        query = {
            "clientType": "robot",
            "gameId": game_id,
            "token": token,
            "clientId": client_id,
        }

        url = (
            url[: -len(SOCKETIO_NAMESPACE)]
            if url.endswith(SOCKETIO_NAMESPACE)
            else url
        )
        self.socketio_logger = logging.getLogger("socketio")
        self.url = self._get_query_url(url, query)
        self.connected = False
        self.message_listener = message_listener

        super().__init__(SOCKETIO_NAMESPACE)

    def _get_query_url(self, url, query):
        url += "?"
        for key, value in query.items():
            url += f"{key}={value}&"
        return url[:-1]

    def on_connect(self):
        self.connected = True
        if self.connected_future is not None:
            self.connected_future.set_result(True)
            self.connected_future = None

    def on_disconnect(self):
        self.connected = False
        if self.connected_future is not None:
            self.connected_future.set_exception(GEConnectionError())
            self.connected_future = None

    @staticmethod
    def _resolve_future(future, data):
        future.set_result(data)

    async def request(self, event, data):
        future = asyncio.get_running_loop().create_future()
        await self.emit(
            "message",
            {"event": event, "payload": data},
            callback=functools.partial(self._resolve_future, future),
        )
        return await future

    async def send(self, event, data):
        await self.emit(
            "message",
            {"event": event, "payload": data, "dst": "gameEngine"},
        )

    async def on_message(self, data, *args):
        if self.message_listener is not None:
            asyncio.create_task(self.message_listener(data))
        pass

    async def connect(self):
        self.sio = socketio.AsyncClient(
            logger=self.socketio_logger, reconnection=False
        )

        @self.sio.event(namespace=SOCKETIO_NAMESPACE)
        def connect_error(msg):
            logging.error(f"GE socketio connection error: {msg}")
            self.connected = False
            if self.connected_future is not None:
                self.connected_future.set_exception(GEConnectionError(msg))
                self.connected_future = None
            if "Invalid robot token" in msg:
                raise GEConnectionError(msg)

        self.sio.register_namespace(self)

        logging.info(f"connecting to {self.url}")

        await self.sio.connect(self.url, transports="websocket")

        if self.connected is not True:
            self.connected_future = asyncio.get_running_loop().create_future()
            await self.connected_future

        logging.info("connected")

    async def set_local_url(self, url):
        res = await self.request("setLocalConfigUrl", {"url": url})
        logging.info(f"result {res}")

    async def run(self):
        while True:
            # check periodically if still connected
            while self.connected:
                await asyncio.sleep(0.5)

            await self.disconnect()


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    api_client = ApiClient(
        "insert_conroller_id",
        "https://ge.surrogate.tv/",
        "insert_game_id",
        "insert_token",
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(api_client.connect())
    loop.run_until_complete(api_client.set_local_url("http://localhost/"))
