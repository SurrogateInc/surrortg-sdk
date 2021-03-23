import asyncio  # noqa:F401
import time  # noqa:F401
import unittest  # noqa:F401

# Run `pip install numpy opencv-contrib-python` tests can be run
# for AsyncioVideoCapture
"""
from surrortg.devices import AsyncVideoCapture, CapComm, VideoCaptureProcess


# logging.getLogger().setLevel(logging.INFO)
# logging.disable(logging.WARNING)

SAMPLE_FRAME = 1


# Modified process classes
class VideoCaptureProcessReturn(VideoCaptureProcess):
    def run(self):
        self._conn.send(CapComm.INIT_SUCCESS)

        while True:
            # wait until a new request
            req = self._conn.recv()
            # respond to the request
            if req == CapComm.FRAME_REQUEST:
                self._conn.send(SAMPLE_FRAME)
            elif req == CapComm.RELEASE_REQUEST:
                self._conn.send(CapComm.RELEASED)
                break


class VideoCaptureProcessNeverReturn(VideoCaptureProcess):
    def run(self):
        self._conn.send(CapComm.INIT_SUCCESS)

        while True:
            # wait until a new request
            req = self._conn.recv()
            # respond to the request
            if req == CapComm.FRAME_REQUEST:
                pass
            elif req == CapComm.RELEASE_REQUEST:
                self._conn.send(CapComm.RELEASED)
                break


class VideoCaptureProcessInitFailure(VideoCaptureProcess):
    def run(self):
        self._conn.send(CapComm.INIT_FAILURE)


class VideoCaptureProcessNeverInit(VideoCaptureProcess):
    def run(self):
        pass


class VideoCaptureProcessReleaseBlock(VideoCaptureProcess):
    def run(self):
        self._conn.send(CapComm.INIT_SUCCESS)

        while True:
            # wait until a new request
            req = self._conn.recv()

            # respond to the request
            if req == CapComm.FRAME_REQUEST:
                self._conn.send(SAMPLE_FRAME)
            elif req == CapComm.RELEASE_REQUEST:
                time.sleep(15)
                self._conn.send(CapComm.RELEASED)
                break


class GameTest(unittest.TestCase):
    def test_read_frame(self):
        async def _test_read_frame():
            async with await AsyncVideoCapture.create(
                None, process_class=VideoCaptureProcessReturn,
            ) as frames:
                async for frame in frames:
                    self.assertEqual(frame, SAMPLE_FRAME)
                    break

        asyncio.get_event_loop().run_until_complete(_test_read_frame())

    def test_never_reads(self):
        def raise_error():
            raise RuntimeError("read failed")

        async def _test_never_reads():
            cap = await AsyncVideoCapture.create(
                None,
                read_timeout=0.01,
                release_timeout=0.01,
                process_class=VideoCaptureProcessNeverReturn,
            )
            cap._release = raise_error
            with self.assertRaises(RuntimeError):
                await cap.read()

        asyncio.get_event_loop().run_until_complete(_test_never_reads())

    def test_init_failure(self):
        async def _test_init_failure():
            with self.assertRaises(RuntimeError):
                cap = await AsyncVideoCapture.create(
                    None, process_class=VideoCaptureProcessInitFailure
                )
                await cap.read()

        asyncio.get_event_loop().run_until_complete(_test_init_failure())

    def test_never_init(self):
        async def _test_never_init():
            with self.assertRaises(RuntimeError):
                await AsyncVideoCapture.create(
                    None,
                    init_timeout=0.01,
                    process_class=VideoCaptureProcessNeverInit,
                )

        asyncio.get_event_loop().run_until_complete(_test_never_init())

    def test_release_blocking_process(self):
        async def main():
            cap = await AsyncVideoCapture.create(
                None,
                release_timeout=0.01,
                process_class=VideoCaptureProcessReleaseBlock,
            )
            await cap.read()
            await cap.release()

        start = time.time()
        asyncio.get_event_loop().run_until_complete(main())
        end = time.time()
        self.assertLess(end - start, 1)
"""
