import asyncio
import json
import logging
import os
import socket
import sys
import traceback
from dataclasses import asdict, dataclass, field
from signal import SIGINT
from typing import Any, Dict, Optional

import socketio

# Socketio sleep when connecting fails.
# Starting from MIN_SLEEP, sleep always doubles with a connection failure,
# but it does not get larger than MAX_SLEEP
SOCKETIO_CONNECTION_MIN_SLEEP = 1
SOCKETIO_CONNECTION_MAX_SLEEP = 60
SOCKETIO_WAIT_FOR_CONNECTED_TIMEOUT = 10

SOCKETIO_NAMESPACE = "/signaling"
LOCAL_SOCKET_NAME = "/tmp/.srtg-sock"

LOCAL_SOCKET_RECONNECT_TIMEOUT = 5


class MessageValidationError(Exception):
    pass


@dataclass
class Message:
    event: str
    dst: str
    src: Optional[str] = None
    seat: Optional[int] = 0
    payload: Optional[Dict[Any, Any]] = field(default_factory=dict)
    isAdmin: Optional[bool] = False  # noqa: N815

    def __post_init__(self):
        self._validate("event", self.event, str)
        self._validate("dst", self.dst, str)
        self._validate("src", self.src, type(None), str)
        self._validate("seat", self.seat, int)
        self._validate("payload", self.payload, dict, list)
        self._validate("isAdmin", self.isAdmin, bool)

    def _validate(self, name, value, *types):
        if not isinstance(value, types):
            raise MessageValidationError(
                f"Message.{name} has to be of type {types}. "
                f"Is now {type(value)} (value: {value})"
            )

    @classmethod
    def from_dict(cls, dictionary):
        return cls(
            dictionary.get("event"),
            dictionary.get("dst"),
            src=dictionary.get("src"),
            seat=dictionary.get("seat", 0),
            payload=dictionary.get("payload", {}),
            isAdmin=dictionary.get("isAdmin", False),
        )

    def to_dict(self):
        return asdict(self)


class SocketioNamespace(socketio.AsyncClientNamespace):
    def __init__(
        self,
        namespace,
        url,
        query,
        message_handler,
        on_connect_handler,
        socketio_logging_level,
        engineio_logging_level,
        *args,
        **kwargs,
    ):
        self.message_handler = message_handler
        self.on_connect_handler = on_connect_handler
        self.connected = False
        self.socketio_logger = self._get_logger(
            "socketio", socketio_logging_level
        )
        self.engineio_logger = self._get_logger(
            "engineio", engineio_logging_level
        )
        # remove the SOCKETIO_NAMESPACE from url, if there already
        url = (
            url[: -len(SOCKETIO_NAMESPACE)]
            if url.endswith(SOCKETIO_NAMESPACE)
            else url
        )
        self.url = self._get_query_url(url, query)
        self.sio = None
        super().__init__(namespace, *args, **kwargs)

    def _get_query_url(self, url, query):
        url += "?"
        for key, value in query.items():
            url += f"{key}={value}&"
        return url[:-1]

    def _get_logger(self, name, level):
        logger = logging.getLogger(name)
        if level is None:
            logger.addFilter(lambda record: False)
        else:
            logger.setLevel(level)
        return logger

    def on_connect(self):
        logging.info("socketio: connected")
        self.connected = True
        self.on_connect_handler()

    def on_disconnect(self):
        logging.info("socketio: disconnected")
        self.connected = False

    async def on_message(self, data, *args):
        msg = None
        try:
            msg = Message.from_dict(data)
            return await self.message_handler(msg)
        except MessageValidationError as e:
            logging.warning(f"Message validation failed: {e}")
        except Exception:
            # python-socketio does not know how to handle asyncio errors,
            # (ERROR:asyncio:Task exception was never retrieved)
            # so let's catch and handle them in here:
            #
            # These should not happen, and some message handler must be broken
            # --> kill the program with SIGINT after returning from
            #     'on_message'
            logging.error(
                f"Message handling failed for message {msg}:\n"
                f"\n{traceback.format_exc()}"
            )
            logging.info("Sending SIGINT to exit program.")
            asyncio.run_coroutine_threadsafe(
                self.send_sigint(),
                asyncio.get_event_loop(),
            )

    async def send_sigint(self):
        os.kill(os.getpid(), SIGINT)

    async def send_message(self, msg, callback=None):
        try:
            await self.emit("message", data=msg, callback=callback)
        except socketio.exceptions.BadNamespaceError:
            logging.warning(
                f"Sending message {msg} failed, "
                f"{SOCKETIO_NAMESPACE} not connected"
            )

    async def run(self):
        # manually reconnect every time the socketio gets disconnected
        # 'await self.sio.wait()' would work with reconnection=True,
        # but it cannot be interrupted or disconnected
        while True:
            await self._connect()

            # check periodically if still connected
            while self.connected:
                await asyncio.sleep(0.5)

            await self.shutdown()

    async def _connect(self):
        logging.info("socketio: connecting...")
        last_exception = None
        sleep = SOCKETIO_CONNECTION_MIN_SLEEP
        while True:
            try:
                # create client
                self.sio = socketio.AsyncClient(
                    logger=self.socketio_logger,
                    engineio_logger=self.engineio_logger,
                    reconnection=False,
                )
                # register connect_error handler

                @self.sio.event(namespace=SOCKETIO_NAMESPACE)
                def connect_error(msg):
                    logging.error(f"GE socketio connection error: {msg}")
                    self.connected = False
                    if "Invalid robot token" in msg:
                        sys.exit(2)

                # register namespace
                self.sio.register_namespace(self)
                # connect
                await self.sio.connect(self.url, transports="websocket")
                # wait that actually connects
                await asyncio.wait_for(
                    self._wait_for_connected(),
                    timeout=SOCKETIO_WAIT_FOR_CONNECTED_TIMEOUT,
                )
                return
            except asyncio.CancelledError:
                raise
            except Exception as e:
                if type(e) == asyncio.TimeoutError:
                    logging.info(
                        f"socketio: {SOCKETIO_NAMESPACE} did not connect"
                    )
                elif str(e) == last_exception:
                    logging.warning(
                        "socketio: did not connect, "
                        "same error as the previous"
                    )
                else:
                    logging.warning(f"socketio: did not connect, {e}")
                    last_exception = str(e)
                await asyncio.sleep(sleep)
                sleep = min(SOCKETIO_CONNECTION_MAX_SLEEP, sleep * 2)

    async def _wait_for_connected(self):
        logging.info("socketio waiting for connected...")
        while not self.connected:
            await asyncio.sleep(0.1)

    async def shutdown(self):
        logging.info("socketio shutting down...")
        if self.sio is not None:
            await self.disconnect()
            await self.sio.disconnect()


class LocalSocketHandler:
    """Handles sending and receiving messages from unix local socket.

    Messages are forwarded to the message router passed when constructing a
    LocalSocketHandler.
    """

    def __init__(self, socket_name, message_handler):
        self.socket_name = socket_name
        self.message_handler = message_handler
        self.sock = None
        self.connected = False
        self.message_id = 0

    async def run(self):
        self.event_loop = asyncio.get_event_loop()
        while True:
            await self.do_receive()

    async def do_receive(self):
        """Selects socket and reads it when ready"""
        if not self.connected:
            logging.info("Connecting..")
            await self.connect()
            logging.info("Connected: %s" % self.connected)

        try:
            data = await self.event_loop.sock_recv(self.sock, 65535)
            if len(data) == 0:
                logging.info("Local socket disconnected")
                self.connected = False
                return
        except asyncio.CancelledError:
            raise
        except Exception:
            logging.info(
                "Local socket disconnected unexpectedly:"
                f"\n{traceback.format_exc()}"
            )
            self.connected = False
            return

        msg = None
        try:
            parsed_data = self._parse_data(data)
            if parsed_data is not None:
                try:
                    msg = Message.from_dict(parsed_data)
                except MessageValidationError as e:
                    logging.warning(f"Message validation failed: {e}")
        except Exception:
            logging.warning(
                f"Failed to parse message: {data}\n\n{traceback.format_exc()}"
            )

        if msg is not None:
            msg_task = asyncio.create_task(self.message_handler(msg))
            msg_task.add_done_callback(self.msg_task_done_cb)

    def msg_task_done_cb(self, fut):
        if not fut.cancelled() and fut.exception() is not None:
            e = fut.exception()
            logging.error(
                "".join(traceback.format_exception(None, e, e.__traceback__))
            )
            sys.exit(1)

    async def connect(self):
        """Connects to the socket in an infinite loop with sleep"""
        logging.info("localsocket connect()")
        self.connected = False
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        self.sock.settimeout(1)
        self.sock.setblocking(0)
        while not self.connected:
            try:
                await self.event_loop.sock_connect(self.sock, self.socket_name)
                self.connected = True
                logging.info("Connected localsocket")
            except asyncio.CancelledError:
                raise
            except (ConnectionRefusedError, FileNotFoundError):
                await asyncio.sleep(LOCAL_SOCKET_RECONNECT_TIMEOUT)
            except Exception:
                logging.info(
                    f"Failed to connect localsocket: {traceback.format_exc()}"
                )
                await asyncio.sleep(LOCAL_SOCKET_RECONNECT_TIMEOUT)

    def _parse_data(self, data):
        try:
            return json.loads(data.decode("utf-8"))

        except json.JSONDecodeError:
            logging.warning(f"Received non-json message, discarding: {data}")
        except UnicodeDecodeError:
            logging.warning(
                f"Received a non-unicode message, discarding: {data}"
            )
        except KeyError:
            logging.warning(
                f"Received malformed LocalSocketMessage, discarding: {data}"
            )
        return None

    async def send(self, msg):
        await self.event_loop.sock_sendall(
            self.sock, str.encode(json.dumps(self._wrap_message(msg)))
        )

    def _wrap_message(self, msg):
        # increment message_id
        if self.message_id != 0xFFFFFFFF:
            self.message_id += 1
        else:
            self.message_id = 0

        return {
            "id": self.message_id,
            "response": False,
            "payload": msg,
        }

    def shutdown(self):
        if self.sock:
            self.sock.close()


class SocketHandler:
    """Handles messaging through socketio and optional local socket

    :param url: socketio connection url
    :type url: String
    :param query: socketio query parameters, defaults to {}
    :type query: Dict, optional
    :param socketio_logging_level: both socketio and engineio logging level,
        None disables all logging, defaults to logging.WARNING
    :type socketio_logging_level: Int/None, optional
    """

    def __init__(
        self,
        url,
        query={},
        message_callbacks=[],
        response_callbacks={},
        socketio_connect_callback=lambda: None,
        socketio_logging_level=logging.WARNING,
    ):
        self.message_callbacks = message_callbacks
        self.response_callbacks = response_callbacks
        self.socketio_namespace = SocketioNamespace(
            SOCKETIO_NAMESPACE,
            url,
            query,
            self._handle_message,
            socketio_connect_callback,
            socketio_logging_level,
            socketio_logging_level,
        )
        self.local_socket_handler = LocalSocketHandler(
            LOCAL_SOCKET_NAME, self._handle_message
        )

    async def run(self):
        self.event_loop = asyncio.get_event_loop()

        if self.local_socket_handler is None:
            await self.socketio_namespace.run()
        else:
            await asyncio.wait(
                [
                    self.socketio_namespace.run(),
                    self.local_socket_handler.run(),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )

    async def _handle_message(self, msg):
        # use the correct response callback if exists
        response_callback = self._get_response_callback(msg)
        if response_callback is not None:
            return await response_callback(msg)
        # otherwise use the regular callbacks
        await asyncio.gather(*[mcb(msg) for mcb in self.message_callbacks])

    def _get_response_callback(self, msg):
        for checker, cb in self.response_callbacks.items():
            if checker(msg):
                return cb

    def _create_message(self, event, dst, seat, src=None, payload={}):
        return Message(
            event, dst, src=src, seat=seat, payload=payload
        ).to_dict()

    async def send_socketio(
        self, event, dst, seat, src=None, payload={}, callback=None
    ):
        if self._socketio_ok():
            msg = self._create_message(
                event, dst, seat, src=src, payload=payload
            )
            await self.socketio_namespace.send_message(msg, callback=callback)
        else:
            return False

    def send_socketio_threadsafe(
        self, event, dst, seat, src=None, payload={}, callback=None
    ):
        if self._socketio_ok():
            asyncio.run_coroutine_threadsafe(
                self.send_socketio(
                    event,
                    dst,
                    seat,
                    src=src,
                    payload=payload,
                    callback=callback,
                ),
                self.event_loop,
            )
        else:
            return False

    async def send_local(self, event, dst, seat, src=None, payload={}):
        if self._local_socket_ok():
            msg = self._create_message(
                event, dst, seat, src=src, payload=payload
            )
            await self.local_socket_handler.send(msg)
        else:
            return False

    def send_local_threadsafe(self, event, dst, seat, src=None, payload={}):
        if self._local_socket_ok():
            asyncio.run_coroutine_threadsafe(
                self.send_local(event, dst, seat, src=src, payload=payload),
                self.event_loop,
            )
        else:
            return False

    def _socketio_ok(self):
        if not self.socketio_namespace.connected:
            logging.info("Did not send message: socketio not connected")
            return False

        return True

    def _local_socket_ok(self):
        if self.local_socket_handler is None:
            logging.info(
                "Did not send message: local_socket_handler not configured"
            )
            return False

        if not self.local_socket_handler.connected:
            logging.info(
                "Did not send message: local_socket_handler not connected"
            )
            return False

        return True

    async def shutdown(self):
        """Shuts down SocketHandler gracefully with logging"""
        await self.socketio_namespace.shutdown()
        if self.local_socket_handler is not None:
            self.local_socket_handler.shutdown()
        logging.info("SocketHandler shut down gracefully")


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    socket_handler = SocketHandler("http://localhost:5000")

    def is_config(msg):
        return msg.src == "gameEngine" and msg.event == "config"

    async def handle_ge_message(message):
        if message.src != "gameEngine":
            logging.info(f"Message not from GE, {message}")
        else:
            await asyncio.create_task(send_msg_and_request_event())
            if is_config(message):
                logging.info("Event: CONFIG")
                return "CONFIG"
            logging.info(f"Event: {message.event}")

    async def send_msg_and_request_event():
        await socket_handler.socketio_namespace.sio.sleep(1)
        await socket_handler.send_socketio("EVENT", "DST", {})
        await socket_handler.socketio_namespace.sio.sleep(1)
        await socket_handler.socketio_namespace.sio.emit(
            "game_event_request",
            callback=logging.info,
            namespace=SOCKETIO_NAMESPACE,
        )

    socket_handler.register_on_message_cb(handle_ge_message)
    socket_handler.register_on_message_response_cb(
        handle_ge_message, is_config
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(socket_handler.run())
