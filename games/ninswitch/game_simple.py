from surrortg import Game
from games.ninswitch.ns_gamepad_serial import NSGamepadSerial, NSButton, NSDPad
from games.ninswitch.ns_switch import NSSwitch
from games.ninswitch.ns_dpad_switch import NSDPadSwitch
from games.ninswitch.ns_joystick import NSJoystick
from surrortg.image_recognition import AsyncVideoCapture, get_pixel_detector
from pathlib import Path
import logging
import pigpio
import asyncio
import cv2


# limit the processor use
cv2.setNumThreads(1)

# image rec
SAVE_FRAMES = False
SAVE_DIR_PATH = "/opt/srtg-python/imgs"

# ((x, y), (r, g, b))
HOME_CURRENT_GAME_SELECTED_PIXELS = [
    ((22, 697), (52, 52, 52)),
    ((25, 17), (52, 52, 52)),
    ((1261, 16), (52, 52, 52)),
    ((1258, 695), (52, 52, 52)),
    ((288, 543), (252, 1, 16)),
    ((344, 543), (255, 1, 12)),
    ((164, 482), (17, 202, 255)),
    ((173, 483), (4, 208, 255)),
    ((169, 474), (7, 202, 255)),
    ((427, 577), (87, 87, 87)),
]


class NinSwitchSimpleGame(Game):
    async def on_init(self):
        # init controls
        # connect to pigpio daemon

        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Could not connect to pigpio")

        # init joystick splitter, enable physical joystick by default
        self.pi.set_mode(20, pigpio.OUTPUT)
        self.pi.set_mode(21, pigpio.OUTPUT)
        self.pi.write(20, 1)
        self.pi.write(21, 1)
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
            },
        )

        # init image rec
        self.is_home_current_selected = False
        self.image_rec_task = asyncio.create_task(self.image_rec_main())
        self.image_rec_task.add_done_callback(self.image_rec_done_cb)

        # init frame saving
        if SAVE_FRAMES:
            logging.info(f"SAVING FRAMES TO {SAVE_DIR_PATH}")
            Path(SAVE_DIR_PATH).mkdir(parents=True, exist_ok=True)

    """
    here you could do something with
    on_config, on_prepare, on_pre_game, on_countdown, on_start...
    """

    async def on_config(self):
        self.pi.write(20, 0)
        self.pi.write(21, 0)
        await asyncio.sleep(0.1)
        self.pi.write(20, 1)
        self.pi.write(21, 1)

    async def on_pre_game(self):
        self.nsg.press(NSButton.A)
        self.nsg.release(NSButton.A)
        self.nsg.press(NSButton.A)
        self.nsg.release(NSButton.A)

    async def on_finish(self):
        self.io.disable_inputs()
        self.nsg.releaseAll()
        self.nsg.press(NSButton.HOME)
        self.nsg.release(NSButton.HOME)

    async def on_exit(self, reason, exception):
        # end controls
        self.nsg.end()
        self.pi.stop()

        self.image_rec_task.cancel()

    async def image_rec_main(self):
        # create capture
        self.cap = await AsyncVideoCapture.create("/dev/video21")

        # get detector
        has_home_current_game_selected = get_pixel_detector(
            HOME_CURRENT_GAME_SELECTED_PIXELS
        )

        # loop through frames
        i = 0
        async for frame in self.cap.frames():
            # detect
            if has_home_current_game_selected(frame):
                logging.info("is home, the current game selected")
                self.is_home_current_selected = True
            else:
                self.is_home_current_selected = False

            # generic
            if i % 1000 == 0:
                logging.info("1000 frames checked")
            if SAVE_FRAMES:
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
    NinSwitchSimpleGame().run()
