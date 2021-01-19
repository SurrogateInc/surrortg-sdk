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

GAME_OVER_RETRY_PIXELS = [
    ((448, 292), (250, 249, 218)),
    ((591, 293), (244, 245, 214)),
    ((678, 288), (255, 255, 225)),
    ((821, 294), (253, 254, 223)),
    ((640, 450), (156, 149, 45)),
    ((664, 449), (157, 150, 46)),
    ((635, 481), (144, 139, 35)),
    ((648, 481), (146, 139, 33)),
    ((664, 470), (255, 254, 218)),
    ((620, 464), (255, 253, 213)),
]

GAME_OVER_SAVE_AND_QUIT_PIXELS = [
    ((447, 293), (252, 251, 221)),
    ((569, 298), (245, 246, 215)),
    ((677, 294), (255, 254, 226)),
    ((801, 293), (249, 250, 218)),
    ((743, 299), (255, 254, 226)),
    ((618, 515), (147, 141, 31)),
    ((619, 545), (147, 143, 36)),
    ((672, 546), (145, 142, 35)),
    ((696, 513), (150, 142, 35)),
    ((704, 533), (255, 255, 206)),
    ((586, 529), (255, 255, 219)),
]

SAVE_TO_WHICH_FILE_PIXELS = [
    ((1149, 681), (226, 231, 164)),
    ((1165, 681), (224, 227, 158)),
    ((1218, 682), (250, 249, 201)),
    ((547, 39), (255, 255, 226)),
    ((609, 38), (25, 28, 0)),
    ((238, 244), (94, 79, 46)),
    ((235, 470), (97, 84, 49)),
    ((1047, 246), (91, 82, 43)),
    ((1047, 413), (97, 84, 49)),
    ((650, 286), (245, 224, 167)),
    ((649, 434), (255, 226, 175)),
]

# when detected, disable inputs and do actions until not detected
AUTO_ACTIONS = {
    get_pixel_detector(GAME_OVER_RETRY_PIXELS): NSButton.A,
    get_pixel_detector(GAME_OVER_SAVE_AND_QUIT_PIXELS): NSDPad.UP,
    get_pixel_detector(SAVE_TO_WHICH_FILE_PIXELS): NSButton.B,
}


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

        # create capture
        self.cap = await AsyncVideoCapture.create("/dev/video21")
        # get home current detector
        self.has_home_current_game_selected = get_pixel_detector(
            HOME_CURRENT_GAME_SELECTED_PIXELS
        )

        self.image_rec_task = asyncio.create_task(self.image_rec_main())
        self.image_rec_task.add_done_callback(self.image_rec_done_cb)

        if SAVE_FRAMES:
            logging.info(f"SAVING FRAMES TO {SAVE_DIR_PATH}")
            Path(SAVE_DIR_PATH).mkdir(parents=True, exist_ok=True)

    """
    here you could do something with
    on_config, on_prepare, on_pre_game, on_countdown, on_start...
    """

    async def on_config(self):
        i = 0
        while not await self.is_home_current_selected():
            logging.info("Not on Home, current game selected...")
            if i >= 5:
                logging.info("single pressing Home")
                await self.single_press_button(NSButton.HOME)
            await asyncio.sleep(1)
            i += 1
            # TODO notify stuck somehow? Or do something more complicated?
        logging.info("On Home, current game selected")

        # reset the board
        self.pi.write(20, 0)
        self.pi.write(21, 0)
        await asyncio.sleep(0.1)
        self.pi.write(20, 1)
        self.pi.write(21, 1)

    async def on_start(self):
        # this somehow enables the board after the reset?
        self.nsg.press(NSButton.A)
        self.nsg.release(NSButton.A)

        # exit home to the game
        logging.info("single pressing A")
        await self.single_press_button(NSButton.A)
        await asyncio.sleep(1)

        # enable playing
        self.io.enable_inputs()

    async def on_finish(self):
        self.io.disable_inputs()
        self.nsg.releaseAll()
        logging.info("single pressing Home")
        await self.single_press_button(NSButton.HOME)

    async def on_exit(self, reason, exception):
        # end controls
        self.nsg.end()
        self.pi.stop()
        # end image rec task
        await self.cap.release()
        self.image_rec_task.cancel()

    async def single_press_button(self, button):
        self.nsg.press(button)
        await asyncio.sleep(0.5)
        self.nsg.release(button)

    async def single_press_dpad(self, dpad):
        self.nsg.dPad(dpad)
        await asyncio.sleep(0.5)
        self.nsg.dPad(NSDPad.CENTERED)

    async def is_home_current_selected(self):
        return self.has_home_current_game_selected(await self.cap.read())

    async def image_rec_main(self):
        i = 0
        ongoing_auto_action = False
        async for frame in self.cap.frames():
            detected = False
            for detector, action in AUTO_ACTIONS.items():
                if detector(frame):
                    detected = True
                    if not ongoing_auto_action:
                        logging.info("Auto action started")
                        self.io.disable_inputs()
                        ongoing_auto_action = True

                    if type(action) == NSButton:
                        logging.info("button")
                        await self.single_press_button(action)
                    elif type(action) == NSDPad:
                        logging.info("dpad")
                        await self.single_press_dpad(action)
                    break

            if not detected and ongoing_auto_action:
                logging.info("Auto action stopped")
                ongoing_auto_action = False
                self.io.enable_inputs()

            if SAVE_FRAMES:
                cv2.imwrite(f"{SAVE_DIR_PATH}/{i}.jpg", frame)
                logging.info(f"SAVED {i}.jpg")
            i += 1
            await asyncio.sleep(0)

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
    NinSwitchSimpleGame().run(start_games_inputs_enabled=False)
