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
ACTION_STOP_FRAMES_REQUIRED = 5  # compensate failing frames

# ((x, y), (r, g, b))
HOME_CURRENT_GAME_SELECTED_PIXELS = [
    ((162, 483), (0, 201, 252)),
    ((289, 541), (253, 1, 14)),
    ((412, 684), (52, 52, 52)),
    ((621, 686), (253, 253, 253)),
    ((816, 684), (52, 52, 52)),
    ((1062, 684), (52, 52, 52)),
    ((1102, 682), (255, 255, 255)),
]

MAYBE_GAME_OVER_PIXELS = [
    ((446, 290), (253, 254, 220)),
    ((469, 265), (251, 250, 219)),
    ((483, 308), (252, 251, 221)),
    ((502, 306), (253, 255, 213)),
    ((568, 302), (252, 253, 222)),
    ((610, 296), (250, 254, 221)),
    ((675, 290), (255, 255, 225)),
    ((696, 265), (253, 255, 224)),
    ((712, 307), (252, 252, 218)),
    ((750, 310), (252, 251, 220)),
    ((776, 297), (255, 252, 223)),
    ((835, 282), (244, 243, 215)),
    ((821, 311), (247, 250, 219)),
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
    get_pixel_detector(
        MAYBE_GAME_OVER_PIXELS
    ): [],  # this just blocks the controls
    get_pixel_detector(GAME_OVER_RETRY_PIXELS): [NSButton.A],  # press retry
    get_pixel_detector(GAME_OVER_SAVE_AND_QUIT_PIXELS): [
        NSDPad.UP
    ],  # move up to retry
    get_pixel_detector(SAVE_TO_WHICH_FILE_PIXELS): [
        NSButton.B
    ],  # move back to retry screen
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
        self.lock = asyncio.Lock()

        # create capture
        self.cap = await AsyncVideoCapture.create("/dev/video21")
        # get home current detector
        self.has_home_current_game_selected = get_pixel_detector(
            HOME_CURRENT_GAME_SELECTED_PIXELS
        )
        self.has_maybe_game_over = get_pixel_detector(MAYBE_GAME_OVER_PIXELS)

        self.image_rec_task = asyncio.create_task(self.image_rec_main())
        self.image_rec_task.add_done_callback(self.image_rec_done_cb)
        self.inputs_can_be_enabled = False

        if SAVE_FRAMES:
            logging.info(f"SAVING FRAMES TO {SAVE_DIR_PATH}")
            Path(SAVE_DIR_PATH).mkdir(parents=True, exist_ok=True)

    """
    here you could do something with
    on_config, on_prepare, on_pre_game, on_countdown, on_start...
    """

    async def on_config(self):
        async with self.lock:
            i = 0
            while not await self.is_home_current_selected():
                logging.info(
                    f"[on_config]: Not on Home, current game selected {i}."
                )
                if i >= 10:
                    logging.info("[on_config]: single pressing Home")
                    await self.single_press(NSButton.HOME)
                await asyncio.sleep(1)
                i += 1
            logging.info("[on_config]: On Home, current game selected")

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
        await self.single_press(NSButton.A)

        # make sure home is away
        # (three times because of failing frame reads...)
        while (
            await self.is_home_current_selected()
            or await self.is_home_current_selected()
            or await self.is_home_current_selected()
        ):
            logging.info("Waiting for home to go away...")
        logging.info("Not Home")

        # give image rec some time to press retry from the game over screen
        await asyncio.sleep(0.4)
        logging.info("Slept")

        # make sure game over is away
        # (three times because of failing frame reads...)
        while (
            await self.is_maybe_game_over()
            or await self.is_maybe_game_over()
            or await self.is_maybe_game_over()
        ):
            logging.info("Waiting for Game Over to go away...")
        logging.info("Not Game Over")

        # enable playing
        async with self.lock:
            self.inputs_can_be_enabled = True
            self.io.enable_inputs()

    async def on_finish(self):
        self.inputs_can_be_enabled = False
        self.io.disable_inputs()
        logging.info("[on_finish]: resetting inputs")
        self.nsg.releaseAll()

        async with self.lock:
            # why the first press does not work?
            await self.single_press(NSButton.HOME)
            # the workaround...
            i = 0
            while not await self.is_home_current_selected():
                logging.info(
                    f"[on_finish]: Not on Home, current game selected {i}."
                )
                if i % 3 == 0:  # take failed frames into account
                    logging.info("[on_finish]: single pressing Home")
                    await self.single_press(NSButton.HOME)
                await asyncio.sleep(0.5)
                i += 1
            logging.info("[on_finish]: On Home, current game selected")

    async def on_exit(self, reason, exception):
        # end controls
        self.nsg.end()
        self.pi.stop()
        # end image rec task
        await self.cap.release()
        self.image_rec_task.cancel()

    async def single_press(self, pressable):
        if type(pressable) == NSButton:
            self.nsg.press(pressable)
            await asyncio.sleep(0.1)
            self.nsg.release(pressable)
        elif type(pressable) == NSDPad:
            self.nsg.dPad(pressable)
            await asyncio.sleep(0.1)
            self.nsg.dPad(NSDPad.CENTERED)
        else:
            raise RuntimeError(f"Cannot press {pressable}")

    async def is_home_current_selected(self):
        return self.has_home_current_game_selected(await self.cap.read())

    async def is_maybe_game_over(self):
        return self.has_maybe_game_over(await self.cap.read())

    async def image_rec_main(self):
        i = 0
        stop_frames = 0
        ongoing_auto_action = False
        async for frame in self.cap.frames():
            async with self.lock:
                detected = False
                for detector, actions in AUTO_ACTIONS.items():
                    if detector(frame):
                        detected = True
                        stop_frames = 0
                        if not ongoing_auto_action:
                            logging.info("Auto action started")
                            self.io.disable_inputs()
                            self.nsg.releaseAll()
                            ongoing_auto_action = True

                        for action in actions:
                            logging.info(f"pressing: {action}")
                            await self.single_press(action)

                if not detected and ongoing_auto_action:
                    stop_frames += 1
                    if stop_frames > ACTION_STOP_FRAMES_REQUIRED:
                        logging.info("Auto action stopped")
                        ongoing_auto_action = False
                        stop_frames = 0
                        if self.inputs_can_be_enabled:
                            logging.info("enabling inputs")
                            self.io.enable_inputs()
                    else:
                        logging.info(f"Action stop frame {stop_frames}.")

                if SAVE_FRAMES:
                    cv2.imwrite(f"{SAVE_DIR_PATH}/{i}.jpg", frame)
                    logging.info(f"SAVED {i}.jpg")
                i += 1

            await asyncio.sleep(0)  # might be redundant?

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
