import asyncio
import logging
import cv2
from pathlib import Path
from surrortg import Game
from surrortg.inputs import Switch
from surrortg.image_recognition import AsyncVideoCapture, get_pixel_detector
from games.ninswitch.ns_gamepad_serial import NSGamepadSerial, NSButton, NSDPad
from games.ninswitch.ns_switch import NSSwitch
from games.ninswitch.ns_dpad_switch import NSDPadSwitch
from games.ninswitch.ns_joystick import NSJoystick

# limit the processor use
cv2.setNumThreads(1)

# image rec
SAVE_ALL_FRAMES = False
SAVE_DIR_PATH = "/opt/srtg-python/imgs"
global save_individual_fame
save_individual_fame = False

# sample detectable
# ((x, y), (r, g, b))
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


class CaptureScreen(Switch):
    async def on(self, seat=0):
        global save_individual_fame
        save_individual_fame = True
        logging.info(f"\t{seat} | Capturing_Frames down")

    async def off(self, seat=0):
        global save_individual_fame
        save_individual_fame = False
        logging.info(f"\t{seat} | Capturing_Frames up")


class NinSwitchImageRecGame(Game):
    async def on_init(self):
        # init controls
        self.nsg = NSGamepadSerial()
        self.nsg.begin()
        self.io.register_inputs(
            {
                "left_joystick": NSJoystick(
                    self.nsg.leftXAxis, self.nsg.leftYAxis
                ),
                "right_joystick": NSJoystick(
                    self.nsg.rightXAxis, self.nsg.rightYAxis
                ),
                "dpad_up": NSDPadSwitch(self.nsg, NSDPad.UP),
                "dpad_left": NSDPadSwitch(self.nsg, NSDPad.LEFT),
                "dpad_right": NSDPadSwitch(self.nsg, NSDPad.RIGHT),
                "dpad_down": NSDPadSwitch(self.nsg, NSDPad.DOWN),
                "Y": NSSwitch(self.nsg, NSButton.Y),
                "X": NSSwitch(self.nsg, NSButton.X),
                "A": NSSwitch(self.nsg, NSButton.A),
                "B": NSSwitch(self.nsg, NSButton.B),
                "left_throttle": NSSwitch(self.nsg, NSButton.LEFT_THROTTLE),
                "left_trigger": NSSwitch(self.nsg, NSButton.LEFT_TRIGGER),
                "right_throttle": NSSwitch(self.nsg, NSButton.RIGHT_THROTTLE),
                "right_trigger": NSSwitch(self.nsg, NSButton.RIGHT_TRIGGER),
                "minus": NSSwitch(self.nsg, NSButton.MINUS),
                "plus": NSSwitch(self.nsg, NSButton.PLUS),
                "left_stick": NSSwitch(self.nsg, NSButton.LEFT_STICK),
                "right_stick": NSSwitch(self.nsg, NSButton.RIGHT_STICK),
                "home": NSSwitch(self.nsg, NSButton.HOME),
                "capture": NSSwitch(self.nsg, NSButton.CAPTURE),
                "capture_frame": CaptureScreen(),
            },
        )
        # init image rec
        self.image_rec_task = asyncio.create_task(self.image_rec_main())
        self.image_rec_task.add_done_callback(self.image_rec_done_cb)

        # init frame saving
        logging.info(f"SAVING FRAMES TO {SAVE_DIR_PATH}")
        Path(SAVE_DIR_PATH).mkdir(parents=True, exist_ok=True)

    """
    here you could do something with
    on_config, on_prepare, on_pre_game, on_countdown, on_start...
    """

    async def on_finish(self):
        self.io.disable_inputs()
        self.nsg.releaseAll()

    async def on_exit(self, reason, exception):
        # end controls
        self.nsg.end()
        # end image rec task
        await self.cap.release()
        self.image_rec_task.cancel()

    async def image_rec_main(self):
        # create capture
        self.cap = await AsyncVideoCapture.create("/dev/video21")

        # get detector
        has_flag = get_pixel_detector(FLAG_PIXELS)

        # loop through frames
        i = 0
        async for frame in self.cap.frames():
            # detect
            if has_flag(frame):
                logging.info("Has flag!")
            else:
                logging.info("Doesn't have flag")

            # generic
            if i % 100 == 0:
                logging.info("100 frames checked")
            if SAVE_ALL_FRAMES or save_individual_fame:
                cv2.imwrite(f"{SAVE_DIR_PATH}/{i}.jpg", frame)
                logging.info(f"SAVED {i}.jpg")
            i += 1

    def image_rec_done_cb(self, fut):
        # make program end if image_rec_task raises error
        if not fut.cancelled() and fut.exception() is not None:
            import traceback, sys  # noqa: E401

            e = fut.exception()
            logging.error(
                "".join(traceback.format_exception(None, e, e.__traceback__))
            )
            sys.exit(1)


if __name__ == "__main__":
    NinSwitchImageRecGame().run()
