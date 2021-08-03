import asyncio
import concurrent.futures
import logging
import multiprocessing
import time
from enum import Enum, auto

import cv2

from .aruco_marker import ArucoMarker

MAX_READ_FAILURES_PER_INIT = 3
LOOPBACK_DEV_PATH = "/dev/video21"


class CapComm(Enum):
    """For communication between ArucoDetectionProcess and ArucoDetect"""

    INIT_SUCCESS = auto()
    INIT_FAILURE = auto()
    ARUCO_REQUEST = auto()
    CROP_REQUEST = auto()
    RELEASE_REQUEST = auto()
    RELEASED = auto()


class ArucoDetectionProcess:
    """Separated cv2.VideoCapture process class with aruco marker detection

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
        self.arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_5X5_50)
        self.arucoParams = cv2.aruco.DetectorParameters_create()
        self.crop_params = (0, 0, 0, 0)

    def run(self):
        # initialize self._cap cv2.VideoCapture
        self._init_cap(True)

        while True:
            # wait until a new request
            req = self._conn.recv()

            # respond to the request
            if req == CapComm.ARUCO_REQUEST:
                frame = self._read()
                self._conn.send(frame)
            if req == CapComm.CROP_REQUEST:
                self.crop_params = self._conn.recv()
                self.patch_size = (
                    int(self.crop_params[0] - self.crop_params[1]),
                    int(self.crop_params[2] - self.crop_params[3]),
                )
                self.center = (
                    self.crop_params[1]
                    + (self.crop_params[0] - self.crop_params[1]) / 2,
                    self.crop_params[3]
                    + (self.crop_params[2] - self.crop_params[3]) / 2,
                )
            elif req == CapComm.RELEASE_REQUEST:
                self._cap.release()
                self._conn.send(CapComm.RELEASED)
                break

    def _create_cap(self):
        self._cap = cv2.VideoCapture(self._source, cv2.CAP_V4L2)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # When not using loopback device, default resolution can be 1080p
        # which is too much for raspi to handle with streamer also running
        if self._source != LOOPBACK_DEV_PATH:
            self._cap.set(
                cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc("M", "J", "P", "G")
            )
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.resolution = (
            self._cap.get(cv2.CAP_PROP_FRAME_WIDTH),
            self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
        )

    def _init_cap(self, send):
        self._create_cap()
        if not self._cap.isOpened():
            if send:
                self._conn.send(CapComm.INIT_FAILURE)
            raise RuntimeError(f"Could not open camera '{self._source}'")
        self._conn.send(CapComm.INIT_SUCCESS)

    def _read(self):
        # TODO: handle same ID appearing multiple times
        success = False
        markers = []

        success, frame = self._cap.read()
        if not success or len(frame) == 0:
            return markers
        if any(self.crop_params):
            frame = cv2.getRectSubPix(frame, self.patch_size, self.center)
        (corners, ids, rejected) = cv2.aruco.detectMarkers(
            frame, self.arucoDict, parameters=self.arucoParams
        )
        if len(corners) == 0:
            return markers

        ids = ids.flatten()
        markers = [
            ArucoMarker(ids[i], corners[i][0], self.resolution)
            for i in range(len(ids))
        ]
        return markers


class ArucoDetect:
    """Non-blocking aruco detector

    Only one ArucoDetect instance can exist per camera. If aruco markers are
    used in more than one location, subscribe the users to the same ArucoDetect
    instance. Use factory method 'await ArucoDetect.create(source, ...)'
    instead of __init__.
    """

    @classmethod
    async def create(
        cls,
        source=LOOPBACK_DEV_PATH,
        init_timeout=2,
        read_timeout=2,
        release_timeout=2,
        process_class=ArucoDetectionProcess,
        apiPreference=cv2.CAP_V4L2,  # noqa: N803
    ):
        """Factory method for ArucoDetect, use this instead of __init__

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
        self.callbacks = []

        # initialize and start video_capture_process
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._loop = asyncio.get_event_loop()
        await self._start_process()

        return self

    def register_observer(self, callback):
        """Register to receive all found aruco markers.

        :param callback: Function that will do something with the markers
        :type callback: Function that takes a list of aruco markers
        """
        logging.info("aruco detect registering observer")
        self.callbacks.append(callback)

    def unregister_observer(self, callback):
        """Unregister from receiving aruco markers

        :param callback: Function that will do something with the markers
        :type callback: Function that takes a list of aruco markers
        """
        try:
            self.callbacks.remove(callback)
        except ValueError as e:
            logging.info(f"error while removing aruco callback: {e}")
            pass

    def set_crop(self, crop_params):
        """Set cropping for frames used for aruco detection. Useful for
            increasing performance.

        :param crop_params: Tuple of pixel coordinates:
            (max_x, min_x, max_y, min_y), representing the area of the frame
            left after cropping.
        :type crop_params: Tuple of four floats
        """
        if len(self.callbacks) != 0:
            logging.error("Unable to set aruco cropping while reading frames")
            return
        self._conn_main.send(CapComm.CROP_REQUEST)
        self._conn_main.send(crop_params)

    def _detect_cb(self, found_markers):
        for callback in self.callbacks:
            callback(found_markers)

    async def _start_process(self):
        self._conn_main, self._conn_process = multiprocessing.Pipe()
        cap_process = self._process_class(
            self._source, self._conn_process, self._apiPreference
        )
        self._cap_process = multiprocessing.Process(
            target=cap_process.run,
            daemon=True,
            name="SRTG Controller video capture",
        )
        self._cap_process.start()
        await self._verify_process_start()
        self._image_rec_task = asyncio.create_task(self._read())

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

    async def _read(self):
        """Keeps requesting aruco markers until released"""
        while not self._released:
            if self._released:
                logging.info(
                    "ArucoDetect has been released, stopping detection"
                )
                break
            # TODO: This isn't efficient. Fix the system to safely create and
            #       cancel this task as needed.
            if len(self.callbacks) > 0:
                # send aruco request
                self._conn_main.send(CapComm.ARUCO_REQUEST)
                # get response
                markers = await self._get_response(self._read_timeout)
                if markers is not None and len(markers):
                    self._detect_cb(markers)
            await asyncio.sleep(0.1)

    async def __aenter__(self):
        return self.frames()

    async def __aexit__(self, type, value, traceback):
        await self.release()

    async def release(self):
        """Release resources"""
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
        logging.info(response)

        # check if actually responded to old
        # CapComm.ARUCO_REQUEST
        if (
            isinstance(response, list)
            and isinstance(response[0], ArucoMarker)
            and response_time > self.release_timeout
        ):
            # if was aruco marker, and still _release_time left,
            # wait a bit more for CapComm.RELEASED
            logging.info("got resp to old frame")
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
