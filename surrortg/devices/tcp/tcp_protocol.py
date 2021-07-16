import asyncio
import logging
from enum import IntEnum


class TcpCommandId(IntEnum):
    """Emun for 8-bit command identifiers of TCP-controlled bots"""

    THROTTLE = 1
    THROTTLE_CAL = 2
    STEER = 3
    STEER_CAL = 4
    CUSTOM_1 = 5
    CUSTOM_1_CAL = 6
    CUSTOM_2 = 7
    CUSTOM_2_CAL = 8
    CUSTOM_3 = 9
    CUSTOM_3_CAL = 10
    CUSTOM_4 = 11
    CUSTOM_4_CAL = 12
    BATTERY_STATUS = 100
    PING = 200
    STOP = 0xFF


class TcpEndpoint:
    """High-level interface for TCP endpoints

    :param reader: asyncio connection reader
    :type reader: asyncio.StreamReader
    :param writer: asyncio connection writer
    :type writer: asyncio.StreamWriter
    :param host: Tcp host address
    :type host: String
    :param port: Tcp host port
    :type port: int
    """

    def __init__(self, reader, writer, host, port):
        self._closed = False
        self._reader = reader
        self._writer = writer
        self._address = host
        self._port = port

    async def close(self):
        """Close the endpoint"""
        if self._closed:
            return
        self._closed = True
        self._writer.close()
        await self._writer.wait_closed()

    async def send(self, data):
        """Send data to the endpoint

        :param data: Data to send
        :type data: bytes
        """
        if self._closed:
            logging.error(f"Endpoint to {self._address} is closed")
            return
        try:
            self._writer.write(data)
            await self._writer.drain()
        except:  # noqa E722
            logging.error(
                f"Could not send data to {self._address}, connection down!"
            )

    async def receive(self, n=100):
        """Receive up to n bytes of data from endpoint

        :param n: Maximum amount of bytes to receive, defaults to 100
        :type n: int, optional
        :return: Data read from the endpoint
        :rtype: bytes
        """
        if self._closed:
            logging.error(f"Endpoint to {self._address} is closed")
            return
        return await self._reader.read(n)

    async def receive_exactly(self, n):
        """Receive exactly n bytes of data from the endpoint

        :param n: Amount of bytes to receive
        :type n: int
        :return: Data read from the endpoint
        :rtype: bytes
        """
        if self._closed:
            logging.error(f"Endpoint to {self._address} is closed")
            return
        return await self._reader.readexactly(n)

    @property
    def address(self):
        """The endpoint address as a (host, port) tuple

        :return: Endpoint address and port
        :rtype: (string, int)
        """
        return (self._address, self._port)

    @property
    def closed(self):
        """Indicates whether the endpoint is closed or not

        :return: True if endpoint is closed
        :rtype: bool
        """
        return self._closed


async def open_tcp_endpoint(host, port, timeout=5):
    """Open TCP remote endpoint to host

    :param host: Host address
    :type host: String
    :param port: Host port
    :type port: int
    :param timeout: Time to wait for the connection in seconds, defaults to 5
    :type timeout: float or int
    :return: TCP remote endpoint or None if connection failed
    :rtype: TCPEndpoint
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout
        )
        return TcpEndpoint(reader, writer, host, port)
    except asyncio.TimeoutError:
        logging.error(f"Connection to {host}:{port} timeouted")
        return None
    except OSError:
        logging.error(f"No route to host {host}")
        return None
