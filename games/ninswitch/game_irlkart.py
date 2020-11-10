import asyncio
import logging
import cv2
from time import time
from pathlib import Path
from surrortg import Game
from surrortg.image_recognition import AsyncVideoCapture, get_pixel_detector
from games.ninswitch.ns_gamepad_serial import NSGamepadSerial, NSButton, NSDPad
from games.ninswitch.ns_switch import NSSwitch
from games.ninswitch.ns_dpad_switch import NSDPadSwitch
from games.ninswitch.ns_joystick import NSJoystick
from games.ninswitch.ocr import get_time_ms

# limit the processor use
cv2.setNumThreads(1)

# image rec
SAVE_FRAMES = False
SAVE_POS_FRAMES = True
SAVE_DIR_PATH = "/opt/srtg-python/imgs"
SAVE_POS_DIR_PATH = "/opt/srtg-python/pos_imgs"
MAX_FAILED_SCORE_READS = 10
FAILED_SCORE_READ_SCORE = 10 * 60 * 1000  # 10 min

# detectables
# ((x, y), (r, g, b))
FINISH_TEXT_PIXELS = [
    ((424, 315), (255, 194, 0)),
    ((366, 330), (255, 207, 0)),
    ((380, 403), (255, 207, 3)),
    ((470, 345), (255, 211, 0)),
    ((456, 402), (255, 198, 3)),
    ((528, 403), (254, 213, 1)),
    ((517, 345), (255, 200, 0)),
    ((544, 359), (254, 213, 1)),
    ((574, 373), (254, 203, 0)),
    ((590, 327), (255, 203, 1)),
    ((635, 342), (255, 205, 0)),
    ((636, 373), (255, 204, 0)),
    ((681, 388), (255, 205, 2)),
    ((726, 401), (255, 200, 0)),
    ((695, 345), (255, 202, 0)),
    ((741, 329), (255, 200, 1)),
    ((782, 330), (254, 210, 1)),
    ((801, 388), (254, 198, 1)),
    ((846, 344), (255, 197, 0)),
    ((859, 375), (254, 208, 0)),
    ((905, 329), (254, 206, 0)),
    ((907, 359), (254, 206, 0)),
    ((905, 404), (255, 192, 0)),
    ((611, 320), (115, 70, 2)),
    ((609, 356), (107, 74, 0)),
    ((610, 384), (116, 77, 2)),
]

HAS_4_READY_PIXELS = [
    ((394, 85), (4, 191, 26)),
    ((394, 93), (244, 255, 249)),
    ((404, 85), (247, 253, 251)),
    ((408, 94), (28, 179, 26)),
    ((393, 134), (8, 185, 32)),
    ((394, 144), (248, 255, 248)),
    ((403, 138), (248, 250, 247)),
    ((407, 146), (21, 190, 39)),
    ((394, 184), (9, 183, 26)),
    ((395, 195), (247, 255, 248)),
    ((402, 188), (251, 249, 250)),
    ((408, 195), (23, 175, 30)),
    ((394, 235), (2, 182, 25)),
    ((394, 242), (251, 255, 252)),
    ((403, 237), (247, 247, 247)),
    ((407, 245), (19, 182, 27)),
]

FLAG_PIXELS = [
    ((206, 654), (14, 14, 12)),
    ((215, 655), (254, 254, 254)),
    ((223, 654), (11, 11, 11)),
    ((222, 663), (252, 252, 252)),
    ((214, 662), (0, 0, 0)),
    ((206, 661), (253, 251, 252)),
    ((205, 670), (20, 18, 19)),
    ((213, 670), (252, 252, 252)),
    ((222, 669), (0, 0, 0)),
    ((201, 650), (2, 2, 4)),
]

POS_1_PIXELS = [
    ((722, 36), (8, 37, 45)),
    ((728, 36), (3, 38, 70)),
    ((729, 44), (26, 49, 67)),
    ((730, 57), (31, 47, 72)),
    ((697, 23), (253, 255, 254)),
    ((696, 70), (255, 254, 252)),
    ((821, 21), (254, 253, 251)),
    ((822, 71), (255, 255, 255)),
    ((1008, 21), (254, 254, 254)),
    ((1008, 71), (255, 254, 255)),
    ((1273, 22), (255, 253, 254)),
    ((1275, 72), (248, 250, 249)),
    ((1150, 21), (254, 252, 253)),
    ((1152, 72), (254, 254, 252)),
]

POS_2_PIXELS = [
    ((720, 128), (16, 46, 72)),
    ((729, 128), (16, 45, 75)),
    ((737, 128), (31, 45, 71)),
    ((728, 106), (11, 43, 68)),
    ((728, 119), (23, 48, 78)),
    ((696, 94), (254, 254, 254)),
    ((696, 141), (251, 255, 254)),
    ((819, 91), (253, 253, 255)),
    ((817, 141), (255, 255, 255)),
    ((974, 92), (254, 255, 255)),
    ((973, 141), (255, 255, 255)),
    ((1131, 92), (253, 254, 255)),
    ((1132, 141), (255, 255, 255)),
    ((1272, 92), (255, 252, 254)),
    ((1273, 142), (255, 255, 255)),
]

POS_3_PIXELS = [
    ((719, 181), (14, 33, 37)),
    ((724, 177), (18, 44, 59)),
    ((732, 188), (8, 29, 58)),
    ((719, 196), (42, 64, 77)),
    ((733, 200), (7, 35, 56)),
    ((694, 165), (255, 255, 253)),
    ((695, 212), (254, 253, 249)),
    ((849, 165), (255, 255, 255)),
    ((847, 213), (255, 255, 255)),
    ((990, 164), (255, 252, 249)),
    ((989, 211), (255, 255, 255)),
    ((1146, 164), (251, 255, 255)),
    ((1149, 212), (255, 255, 253)),
    ((1269, 164), (252, 253, 248)),
    ((1269, 212), (255, 255, 255)),
]

POS_4_PIXELS = [
    ((732, 249), (5, 32, 51)),
    ((718, 265), (22, 54, 67)),
    ((734, 270), (7, 31, 43)),
    ((734, 265), (4, 44, 79)),
    ((739, 266), (8, 21, 38)),
    ((694, 235), (254, 255, 250)),
    ((694, 284), (244, 242, 247)),
    ((832, 234), (255, 255, 255)),
    ((831, 282), (254, 254, 255)),
    ((1007, 234), (255, 255, 255)),
    ((1006, 283), (255, 254, 255)),
    ((1139, 233), (255, 255, 255)),
    ((1142, 283), (255, 254, 250)),
    ((1271, 234), (255, 255, 255)),
    ((1272, 282), (251, 255, 254)),
]


class NinSwitchIRLKart(Game):
    async def on_init(self):
        # init controls
        self.nsg = NSGamepadSerial()
        self.nsg.begin()
        self.io.register_inputs(
            {
                "left_joystick": NSJoystick(
                    self.nsg.leftXAxis, self.nsg.leftYAxis
                ),
                "dpad_up": NSDPadSwitch(self.nsg, NSDPad.UP),
                "dpad_left": NSDPadSwitch(self.nsg, NSDPad.LEFT),
                "dpad_right": NSDPadSwitch(self.nsg, NSDPad.RIGHT),
                "dpad_down": NSDPadSwitch(self.nsg, NSDPad.DOWN),
                "X": NSSwitch(self.nsg, NSButton.X),
                "A": NSSwitch(self.nsg, NSButton.A),
                "B": NSSwitch(self.nsg, NSButton.B),
                "left_throttle": NSSwitch(self.nsg, NSButton.LEFT_THROTTLE),
                "right_throttle": NSSwitch(self.nsg, NSButton.RIGHT_THROTTLE),
            }
        )
        self.io.register_inputs(
            {
                "right_joystick": NSJoystick(
                    self.nsg.rightXAxis, self.nsg.rightYAxis
                ),
                "Y": NSSwitch(self.nsg, NSButton.Y),
                "left_trigger": NSSwitch(self.nsg, NSButton.LEFT_TRIGGER),
                "right_trigger": NSSwitch(self.nsg, NSButton.RIGHT_TRIGGER),
                "minus": NSSwitch(self.nsg, NSButton.MINUS),
                "plus": NSSwitch(self.nsg, NSButton.PLUS),
                "left_stick": NSSwitch(self.nsg, NSButton.LEFT_STICK),
                "right_stick": NSSwitch(self.nsg, NSButton.RIGHT_STICK),
                "home": NSSwitch(self.nsg, NSButton.HOME),
                "capture": NSSwitch(self.nsg, NSButton.CAPTURE),
            },
            admin=True,
        )

        # get detectors
        self.has_4_ready_to_start = get_pixel_detector(HAS_4_READY_PIXELS)
        self.has_flag = get_pixel_detector(FLAG_PIXELS)
        self.has_finish_text = get_pixel_detector(FINISH_TEXT_PIXELS)
        self.position_detectors = {
            1: get_pixel_detector(POS_1_PIXELS),
            2: get_pixel_detector(POS_2_PIXELS),
            3: get_pixel_detector(POS_3_PIXELS),
            4: get_pixel_detector(POS_4_PIXELS),
        }

        # init image rec
        self.image_rec_task = asyncio.create_task(self.image_rec_main())
        self.image_rec_task.add_done_callback(self.image_rec_done_cb)
        self.image_rec_task_cancelled = False

        # frame saving
        if SAVE_FRAMES:
            logging.info(f"SAVING FRAMES TO {SAVE_DIR_PATH}")
            Path(SAVE_DIR_PATH).mkdir(parents=True, exist_ok=True)

        if SAVE_POS_FRAMES:
            logging.info(f"SAVING POS FRAMES TO {SAVE_POS_DIR_PATH}")
            Path(SAVE_POS_DIR_PATH).mkdir(parents=True, exist_ok=True)

        # game state
        self.has_started = False
        self.has_finished = False
        self.failed_score_reads = 0
        self.pre_game_ready_sent = False
        self.score_sent = False

    async def on_prepare(self):
        logging.info("self.driving...")
        for _ in range(4):
            self.nsg.press(NSButton.A)
            self.nsg.release(NSButton.A)
            await asyncio.sleep(4)
        self.nsg.press(NSButton.B)
        await asyncio.sleep(2.5)
        self.nsg.release(NSButton.B)
        self.nsg.releaseAll()
        logging.info("...self.driving finished")

    async def on_pre_game(self):
        self.io.enable_inputs()
        self.has_started = False
        self.pre_game_ready_sent = False
        return -1

    async def on_start(self):
        self.has_started = True
        self.has_finished = False
        self.failed_score_reads = 0
        self.score_sent = False

    async def on_finish(self):
        # this will trigger stop_controls even if image_rec_main fails
        self.stop_controls()

    async def on_exit(self, reason, exception):
        # end controls
        self.nsg.end()
        # end image rec task
        self.image_rec_task_cancelled = True
        await self.cap.release()
        self.image_rec_task.cancel()

    async def image_rec_main(self):
        self.cap = await AsyncVideoCapture.create("/dev/video21")

        frame_index = 0
        async for frame in self.cap.frames():
            # on_pre_game
            if not self.has_started:
                # send pre_game ready/not_ready based on frame
                self._handle_pre_game(frame)

            # on_start
            if self.has_started:
                # check for the finish text if not found already
                # stop the controls if found
                if not self.has_finished:
                    self._check_for_finish_text(frame)

                # try to read and send score if not already sent
                if not self.score_sent:
                    self._try_reading_score(frame)

            # generic
            if frame_index % 1000 == 0:
                logging.info("1000 frames checked")
            if SAVE_FRAMES:
                cv2.imwrite(f"{SAVE_DIR_PATH}/{frame_index}.jpg", frame)
                logging.info(f"SAVED {frame_index}.jpg")
            frame_index += 1

        if self.image_rec_task_cancelled:
            logging.info("Image rec task finished.")
        else:
            raise RuntimeError("Image rec task finished by itself")

    def _handle_pre_game(self, frame):
        if (
            self.has_4_ready_to_start(frame) or self.has_flag(frame)
        ) and not self.pre_game_ready_sent:
            logging.info("PRE_GAME READY")
            self.pre_game_ready_sent = True
            for seat in self.io._message_router.get_all_seats():
                self.io.send_pre_game_ready(seat=seat)
        elif self.pre_game_ready_sent:
            logging.info("PRE_GAME NOT READY")
            self.pre_game_ready_sent = False
            for seat in self.io._message_router.get_all_seats():
                self.io.send_pre_game_not_ready(seat=seat)

    def _check_for_finish_text(self, frame):
        if self.has_finish_text(frame):
            self.has_finished = True
            self.stop_controls()
            logging.info("FINISHED")

    def _get_position(self, frame):
        detected = None
        for position in self.position_detectors.keys():
            if self.position_detectors[position](frame):
                detected = position
                break
        return detected

    def _try_reading_score(self, frame):
        pos = self._get_position(frame)
        if pos is not None:
            # if position found, try reading the time
            time_ms, time_string = get_time_ms(frame, pos)
            cleaned_time = time_string.replace(":", "-").replace(".", "-")

            # if time_ms reading failed
            if time_ms is None:
                if SAVE_POS_FRAMES:
                    self._save_pos_frame(frame, pos, cleaned_time, failed=True)
                if self.has_finished and not self.score_sent:
                    self.failed_score_reads += 1
                    logging.info(
                        f"Score reading for pos {pos} failed "
                        f"{self.failed_score_reads}. time: "
                        f"{time_string}"
                    )
                    if self.failed_score_reads == MAX_FAILED_SCORE_READS:
                        logging.info(f"FAILED SCORE SENT")
                        self._send_score(FAILED_SCORE_READ_SCORE)
            else:  # if time reading succeeded
                if not self.has_finished:
                    self.stop_controls()
                    logging.info("STOPPED CONTROLS, FINISH WAS NOT READ")
                self.score_sent = True
                self._send_score(time_ms)
                logging.info(f"SCORE {time_string} SENT")
                if SAVE_POS_FRAMES:
                    self._save_pos_frame(frame, pos, cleaned_time)

    def _save_pos_frame(self, frame, pos, cleaned_time, failed=False):
        prefix = "FAILED_" if failed else ""
        timestamp = int(time() * 1000.0)
        filename = f"{prefix}{cleaned_time}_{pos}_{timestamp}.jpg"
        cv2.imwrite(
            f"{SAVE_POS_DIR_PATH}/{filename}", frame,
        )
        logging.info(f"SAVED {prefix}POS FRAME: {filename}")

    def _send_score(self, score):
        for seat in self.io._message_router.get_all_seats():
            self.io.send_score(
                score=score, seat=seat, seat_final_score=True,
            )

    def image_rec_done_cb(self, fut):
        # make program end if image_rec_task raises error
        if not fut.cancelled() and fut.exception() is not None:
            import traceback, sys  # noqa: E401

            e = fut.exception()
            logging.error(
                "".join(traceback.format_exception(None, e, e.__traceback__))
            )
            sys.exit(1)

    def stop_controls(self):
        self.io.disable_inputs()
        self.nsg.releaseAll()


if __name__ == "__main__":
    NinSwitchIRLKart().run()
