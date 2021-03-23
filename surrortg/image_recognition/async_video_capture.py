import asyncio
import concurrent.futures
import logging
import multiprocessing
import time
from enum import Enum, auto

import cv2
import numpy as np

# VideoCaptureProcess
MAX_READ_FAILURES_PER_INIT = 3


class CapComm(Enum):
    """For communication between AsyncVideoCapture and VideoCaptureProcess"""

    INIT_SUCCESS = auto()
    INIT_FAILURE = auto()
    FRAME_REQUEST = auto()
    RELEASE_REQUEST = auto()
    RELEASED = auto()


class VideoCaptureProcess:
    """Separated cv2.VideoCapture process class

    Should be started with multiprocessing.Process(... daemon=True), so it
    won't block exit if the main process fails.

    Before usage: `pip install numpy opencv-contrib-python`

    :param source: Camera id or path
    :type source: String/Int
    :param conn: multiprocessing.connection.Pipe() one end of the connection
    :type conn: multiprocessing.connection.Connection
    """

    def __init__(self, source, conn, apiPreference):  # noqa: N803
        self._source = source
        self._conn = conn
        self._apiPreference = apiPreference

    def run(self):
        # initialize self._cap cv2.VideoCapture
        self._init_cap(True)

        while True:
            # wait until a new request
            req = self._conn.recv()

            # respond to the request
            if req == CapComm.FRAME_REQUEST:
                frame = self._read()
                self._conn.send(frame)
            elif req == CapComm.RELEASE_REQUEST:
                self._cap.release()
                self._conn.send(CapComm.RELEASED)
                break

    def _init_cap(self, send):
        # Get cv2.VideoCapture without a buffer
        self._cap = cv2.VideoCapture(self._source, cv2.CAP_V4L2)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # Makes sure that camera was actually opened
        if not self._cap.isOpened():
            if send:
                self._conn.send(CapComm.INIT_FAILURE)
            raise RuntimeError(f"Could not open camera '{self._source}'")
        self._conn.send(CapComm.INIT_SUCCESS)

    def _read(self):
        # Returns only after a successful frame read
        # Re-initializes VideoCapture every MAX_READ_FAILURES_PER_INIT
        # read failures
        success = False
        read_failures = 0
        reinits = 0

        while not success:
            success, frame = self._cap.read()
            if not success:
                read_failures += 1
                logging.warning(f"Capture read failure {read_failures}.")
                if read_failures >= MAX_READ_FAILURES_PER_INIT:
                    reinits += 1
                    logging.warning(f"Capture reinits {reinits}.")
                    self._cap.release()
                    # if init fails, AsyncVideoCapture will soon restart
                    # the process
                    self._init_cap(False)
                    read_failures = 0
        return frame


class AsyncVideoCapture:
    """Non-blocking video capture without an internal buffer

    Based on cv2.VideoCapture class. Does not handle video files. Use factory
    method 'await AsyncVideoCapture.create(source, ...)' instead of __init__
    """

    @classmethod
    async def create(
        cls,
        source,
        init_timeout=2,
        read_timeout=2,
        release_timeout=2,
        process_class=VideoCaptureProcess,
        apiPreference=cv2.CAP_V4L2,  # noqa: N803
    ):
        """Factory method for AsyncVideoCapture, use this instead of __init__

        :param source: Camera id or path
        :type source: String/Int
        :param init_timeout: Max time to wait for VideoCapture init,
            otherwise RuntimeError will be raised, defaults to 2
        :type release_timeout: int, optional
        :param read_timeout: Max time to wait for frame in seconds, after the
            timeout VideoCapture will be released and reinitialized, defaults
            to 2
        :type read_timeout: int, optional
        :param release_timeout: Max time to wait for VideoCapture release,
            otherwise SIGKILL will be sent, defaults to 2
        :type release_timeout: int, optional
        :param process_class: Video capture process class implementation,
            option mainly for easier testing
        :type process_class: VideoCaptureProcess, optional
        :param apiPreference: backend apiPreference for cv2.VideoCapture,
            defaults to cv2.CAP_V4L2
        :type apiPreference: cv2 VideoCaptureAPI, optional
        """
        self = cls()

        # save the correct state
        self._source = source
        self._init_timeout = init_timeout
        self._read_timeout = read_timeout
        self._release_timeout = release_timeout
        self._process_class = process_class
        self._apiPreference = apiPreference
        self._released = False
        self._start_time = None

        # initialize and start video_capture_process
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._loop = asyncio.get_event_loop()
        await self._start_process()

        return self

    async def _start_process(self):
        self._conn_main, self._conn_process = multiprocessing.Pipe()
        cap_process = self._process_class(
            self._source, self._conn_process, self._apiPreference
        )
        self._cap_process = multiprocessing.Process(
            target=cap_process.run,
            daemon=True,
        )
        self._cap_process.start()
        await self._verify_process_start()

    async def _verify_process_start(self):
        response = await self._get_response(self._init_timeout)
        if response is CapComm.INIT_SUCCESS:
            logging.info(f"Camera '{self._source}' opened successfully")
        elif response is CapComm.INIT_FAILURE:
            raise RuntimeError(
                f"Could not open camera '{self._source}' after initialization"
            )
        else:  # None
            raise RuntimeError(
                f"Camera '{self._source}' initialization took more than "
                f"init_timeout ({self._init_timeout}) seconds"
            )

    async def _restart_process(self):
        await self._release()
        await self._start_process()

    async def _get_response(self, timeout):
        """Gets response in timeout seconds or returns None"""
        if await self._loop.run_in_executor(
            self._executor, self._conn_main.poll, timeout
        ):
            return self._conn_main.recv()
        else:
            return None

    async def read(self):
        """Retries until able to return a new frame or released

        Returns None if released

        :return: the next frame or None
        :rtype: numpy.ndarray/None
        """
        while True:
            # return None if released
            if self._released:
                logging.info(
                    "AsyncVideoCapture has been released, returning None"
                )
                return None

            # send frame request
            self._conn_main.send(CapComm.FRAME_REQUEST)
            # get response
            frame = await self._get_response(self._read_timeout)
            if frame is None:
                # response timed out --> restart video_capture_process
                logging.warning(
                    f"No frame returned in {self._read_timeout} seconds, "
                    "restarting video_capture_process"
                )
                await self._restart_process()
            else:
                return frame

    async def frames(self):
        """Async generator method for getting frames

        :yield: next frame by using read()
        :rtype: async_generator
        """

        self._start_time = time.time()
        self._frame_count = 0

        while True:
            yield await self.read()
            self._frame_count += 1

    async def __aenter__(self):
        return self.frames()

    async def __aexit__(self, type, value, traceback):
        await self.release()

    async def release(self):
        """Release resources. If frames() generator was used, will log FPS"""
        if self._start_time is not None:
            logging.info(
                "FPS was: "
                f"{self._frame_count / (time.time() - self._start_time)}"
            )
        await self._release()
        self._released = True

        # release the executor
        self._executor.shutdown()

    async def _release(self):
        # send release request
        self._conn_main.send(CapComm.RELEASE_REQUEST)
        # wait for the response, measure the time it took
        start = time.time()
        response = await self._get_response(self._release_timeout)
        end = time.time()
        response_time = end - start

        # check if actually responded to old
        # CapComm.FRAME_REQUEST
        if (
            isinstance(response, np.ndarray)
            and response_time > self.release_timeout
        ):
            # if was frame, and still _release_time left,
            # wait a bit more for CapComm.RELEASED
            response = await self._get_response(
                response_time - self._release_timeout
            )

        if response == CapComm.RELEASED:
            logging.info(f"Camera '{self._source}' released")
            self._cap_process.join()  # should join immediately
        else:  # None
            logging.warning(
                f"VideoCapture did not release in {self._release_timeout} "
                "seconds, must be killed"
            )
            self._cap_process.kill()
            await self._loop.run_in_executor(
                self._executor, self._cap_process.join
            )


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    modes = ["with", "for", "read"]
    SOURCE = 0  # choose source
    MODE = 0  # choose example to execute

    async def main():
        # allow window resizing
        cv2.namedWindow("FRAME", cv2.WINDOW_NORMAL)

        # with + for loop example
        if modes[MODE] == "with":
            async with await AsyncVideoCapture.create(SOURCE) as frames:
                async for frame in frames:
                    cv2.imshow("FRAME", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

        # for loop + release() example
        elif modes[MODE] == "for":
            cap = await AsyncVideoCapture.create(SOURCE)
            async for frame in cap.frames():
                cv2.imshow("FRAME", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            await cap.release()

        # read() + release() example
        elif modes[MODE] == "read":
            cap = await AsyncVideoCapture.create(SOURCE)
            while True:
                cv2.imshow("FRAME", await cap.read())
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            await cap.release()

        # destroy FRAME window
        cv2.destroyAllWindows()

    asyncio.get_event_loop().run_until_complete(main())
