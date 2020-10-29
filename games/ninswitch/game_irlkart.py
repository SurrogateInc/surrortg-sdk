import asyncio
import logging
import time
import cv2
from pathlib import Path
from surrortg import Game
from surrortg.image_recognition import AsyncVideoCapture, get_pixel_detector
from games.ninswitch.ns_gamepad_serial import NSGamepadSerial, NSButton, NSDPad
from games.ninswitch.ns_switch import NSSwitch
from games.ninswitch.ns_dpad_switch import NSDPadSwitch
from games.ninswitch.ns_joystick import NSJoystick


# image rec
SAVE_FRAMES = False
SAVE_FINISH_FRAMES = True
SAVE_DIR_PATH = "/opt/srtg-python/imgs"
SAVE_FINISH_DIR_PATH = "/opt/srtg-python/finish_imgs"

# settings
START_TIME_DELAY = 8.8  # start timer only after "go" text

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


class NinSwitchIRLKart(Game):
    async def on_init(self):
        self.start_time = time.time()
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
        # init image rec
        self.image_rec_task = asyncio.create_task(self.image_rec_main())
        self.image_rec_task.add_done_callback(self.image_rec_done_cb)
        self.image_rec_task_cancelled = False

        if SAVE_FRAMES:
            logging.info(f"SAVING FRAMES TO {SAVE_DIR_PATH}")
            Path(SAVE_DIR_PATH).mkdir(parents=True, exist_ok=True)

        if SAVE_FINISH_FRAMES:
            logging.info(f"SAVING SCORE FRAMES TO {SAVE_FINISH_DIR_PATH}")
            Path(SAVE_FINISH_DIR_PATH).mkdir(parents=True, exist_ok=True)

        self.has_started = False
        self.pre_game_ready_sent = False

    async def on_prepare(self):
        logging.info("self.driving...")
        self.nsg.press(NSButton.A)
        self.nsg.release(NSButton.A)
        await asyncio.sleep(4)
        self.nsg.press(NSButton.A)
        self.nsg.release(NSButton.A)
        await asyncio.sleep(4)
        self.nsg.press(NSButton.A)
        self.nsg.release(NSButton.A)
        await asyncio.sleep(4)
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
        await asyncio.sleep(START_TIME_DELAY)
        self.has_started = True
        self.start_time = time.time()

    async def on_finish(self):
        # this will trigger end_game even if image_rec_main fails
        self.end_game()

    async def on_exit(self, reason, exception):
        # end controls
        self.nsg.end()
        # end image rec task
        self.image_rec_task_cancelled = True
        await self.cap.release()
        self.image_rec_task.cancel()

    async def image_rec_main(self):
        self.cap = await AsyncVideoCapture.create("/dev/video21")

        # get detectors
        has_4_ready_to_start = get_pixel_detector(HAS_4_READY_PIXELS)
        has_flag = get_pixel_detector(FLAG_PIXELS)
        has_finish_text = get_pixel_detector(FINISH_TEXT_PIXELS)

        i = 0
        finish_i = 0
        async for frame in self.cap.frames():
            # on_pre_game
            if not self.has_started:
                if (
                    has_4_ready_to_start(frame) or has_flag(frame)
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
            # on_start
            else:
                if has_finish_text(frame):
                    score = int((time.time() - self.start_time) * 1000)
                    logging.info(
                        "FINISHED TEXT READ, SENDING SCORE "
                        f"{int(score/(1000*60))}:"
                        f"{int((score/1000)%60)}:"
                        f"{int((score/1000)%60%1*10)} SEAT {seat}"
                    )
                    for seat in self.io._message_router.get_all_seats():
                        self.io.send_score(
                            score=score, seat=seat, seat_final_score=True,
                        )
                    self.end_game()
                    if SAVE_FINISH_FRAMES:
                        cv2.imwrite(
                            f"{SAVE_FINISH_DIR_PATH}/{finish_i}.jpg", frame
                        )
                        logging.info(f"SAVED FINISH {finish_i}.jpg")
                    if not SAVE_FRAMES:
                        await asyncio.sleep(10)  # send results only once
                    finish_i += 1

            # generic
            if i % 100 == 0:
                logging.info("100 frames checked")
            if SAVE_FRAMES:
                cv2.imwrite(f"{SAVE_DIR_PATH}/{i}.jpg", frame)
                logging.info(f"SAVED {i}.jpg")
            i += 1

        if self.image_rec_task_cancelled:
            logging.info("Image rec task finished.")
        else:
            raise RuntimeError("Image rec task finished by itself")

    def image_rec_done_cb(self, fut):
        # make program end if image_rec_task raises error
        if not fut.cancelled() and fut.exception() is not None:
            import traceback, sys  # noqa: E401

            e = fut.exception()
            logging.error(
                "".join(traceback.format_exception(None, e, e.__traceback__))
            )
            sys.exit(1)

    def end_game(self):
        self.io.disable_inputs()
        self.nsg.releaseAll()


if __name__ == "__main__":
    NinSwitchIRLKart().run()
