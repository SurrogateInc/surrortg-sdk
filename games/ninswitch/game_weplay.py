from surrortg import Game
from surrortg.inputs import Switch
from games.ninswitch.ns_gamepad_serial import NSGamepadSerial, NSButton, NSDPad
from games.ninswitch.ns_switch import NSSwitch
from games.ninswitch.ns_dpad_switch import NSDPadSwitch
from games.ninswitch.ns_joystick import NSJoystick
from surrortg.image_recognition import AsyncVideoCapture, get_pixel_detector
from pathlib import Path
from enum import Enum, auto
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

# auto button presses
PRESS_TIME = 0.1
POST_PRESS_TIME = 0.5

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
    ((447, 291), (252, 253, 222)),
    ((525, 311), (251, 252, 221)),
    ((736, 283), (245, 244, 216)),
    ((821, 311), (249, 251, 214)),
    ((368, 438), (255, 255, 119)),
    ((353, 453), (252, 251, 125)),
    ((353, 475), (249, 244, 116)),
    ((368, 489), (255, 254, 128)),
    ((913, 438), (253, 248, 118)),
    ((927, 451), (255, 250, 130)),
    ((927, 474), (255, 255, 141)),
    ((913, 489), (252, 249, 120)),
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


class GameStates(Enum):
    """
    These states with custom Switches allows access to MAP_MENU and
    ITEMS_MENU, but do not allow accessing save files menu.
    """

    PLAYING = auto()
    MAP_MENU = auto()
    ITEMS_MENU = auto()


game_state = GameStates.PLAYING  # assume no menu open at the start
ongoing_game_state_transition = False  # allow only one transition at once


class MinusSwitch(Switch):
    """
    Allow pressing minus/menu button only when PLAYING,
    and only allow pressing a certain time.
    """

    def __init__(self, nsg, minus_button):
        self.nsg = nsg
        self.minus_button = minus_button

    async def on(self, seat=0):
        await asyncio.shield(self._on())

    async def _on(self):
        global game_state, ongoing_game_state_transition

        if ongoing_game_state_transition or game_state != GameStates.PLAYING:
            logging.info("minus: blocked")
        else:
            ongoing_game_state_transition = True
            game_state = GameStates.MAP_MENU
            logging.info("minus: game_state MAP_MENU")
            await self.single_press()
            ongoing_game_state_transition = False

    async def off(self, seat=0):
        pass

    async def single_press(self):
        self.nsg.press(self.minus_button)
        await asyncio.sleep(PRESS_TIME)
        self.nsg.release(self.minus_button)
        await asyncio.sleep(POST_PRESS_TIME)


class BSwitch(Switch):
    """
    A normal B button, except when on menus, where B press
    changes the state to PLAYING
    """

    def __init__(self, nsg, b_button):
        self.nsg = nsg
        self.b_button = b_button

    async def on(self, seat=0):
        await asyncio.shield(self._on())

    async def _on(self):
        global game_state, ongoing_game_state_transition

        if ongoing_game_state_transition:
            logging.info("b: blocked")
        elif game_state in [GameStates.MAP_MENU, GameStates.ITEMS_MENU]:
            game_state = GameStates.PLAYING
            ongoing_game_state_transition = True
            logging.info("b: game_state PLAYING")
            self.nsg.press(self.b_button)
            await asyncio.sleep(PRESS_TIME)
            self.nsg.release(self.b_button)
            await asyncio.sleep(POST_PRESS_TIME)
            ongoing_game_state_transition = False
        else:
            self.nsg.press(self.b_button)

    async def off(self, seat=0):
        global ongoing_game_state_transition

        if not ongoing_game_state_transition:
            self.nsg.release(self.b_button)


class XSwitch(Switch):
    """
    A normal X button, except when on MAP_MENU, where X press
    is programmatically pressed twice instead of one.

    This flashes the memories menu, which allows seeing where you
    should be heading.

    This simplifies game_state handling, but blocks old conversations.
    There does not seem to be a simple way to handle this menu without
    image recognition, as the conversation length is not constant, and
    B button does not exit the conversation if one is open --> no way of
    knowing which B press leads back to the MAP_MENU, which would lead to
    unknown game_state.
    """

    def __init__(self, nsg, x_button):
        self.nsg = nsg
        self.x_button = x_button

    async def on(self, seat=0):
        await asyncio.shield(self._on())

    async def _on(self):
        global game_state, ongoing_game_state_transition

        if ongoing_game_state_transition:
            logging.info("x: blocked")
        elif game_state == GameStates.MAP_MENU:
            ongoing_game_state_transition = True
            logging.info("x: game_state visiting MEMORIES...")
            self.nsg.press(self.x_button)
            await asyncio.sleep(PRESS_TIME)
            self.nsg.release(self.x_button)
            await asyncio.sleep(2.5)
            self.nsg.press(NSButton.B)
            await asyncio.sleep(PRESS_TIME)
            self.nsg.release(NSButton.B)
            await asyncio.sleep(POST_PRESS_TIME)
            logging.info("x: game_state back to MAP_MENU")
            ongoing_game_state_transition = False
        else:
            self.nsg.press(self.x_button)

    async def off(self, seat=0):
        global ongoing_game_state_transition

        if not ongoing_game_state_transition:
            self.nsg.release(self.x_button)


class ASwitch(Switch):
    """
    A normal A button, except when on MAP_MENU, where A press
    is blocked. This simplifies game_state handling.
    (Pin menu is blocked, which is not necessary for the game)
    """

    def __init__(self, nsg, a_button):
        self.nsg = nsg
        self.a_button = a_button

    async def on(self, seat=0):
        await asyncio.shield(self._on())

    async def _on(self):
        global game_state, ongoing_game_state_transition

        if ongoing_game_state_transition or game_state == GameStates.MAP_MENU:
            logging.info("a: blocked")
        else:
            self.nsg.press(self.a_button)

    async def off(self, seat=0):
        global ongoing_game_state_transition

        if not ongoing_game_state_transition:
            self.nsg.release(self.a_button)


class TriggerSwitch(Switch):
    """
    A normal trigger button, except when on the menus, where a trigger press
    might be different one than the one pressed.

    This forbits entering the save menu page, where someone could delete
    the game file.
    """

    def __init__(self, nsg, trigger_button):
        self.nsg = nsg
        self.trigger_button = trigger_button

    async def on(self, seat=0):
        await asyncio.shield(self._on())

    async def _on(self):
        global game_state, ongoing_game_state_transition

        if ongoing_game_state_transition:
            logging.info("menu_trigger: blocked")

        elif game_state == GameStates.MAP_MENU:
            game_state = GameStates.ITEMS_MENU
            logging.info("menu_trigger: game_state ITEMS_MENU")

            ongoing_game_state_transition = True
            self.nsg.press(NSButton.RIGHT_TRIGGER)
            await asyncio.sleep(PRESS_TIME)
            self.nsg.release(NSButton.RIGHT_TRIGGER)
            await asyncio.sleep(POST_PRESS_TIME)
            ongoing_game_state_transition = False

        elif game_state == GameStates.ITEMS_MENU:
            game_state = GameStates.MAP_MENU
            logging.info("menu_trigger: game_state MAP_MENU")

            ongoing_game_state_transition = True
            self.nsg.press(NSButton.LEFT_TRIGGER)
            await asyncio.sleep(PRESS_TIME)
            self.nsg.release(NSButton.LEFT_TRIGGER)
            await asyncio.sleep(POST_PRESS_TIME)
            ongoing_game_state_transition = False
        else:
            self.nsg.press(self.trigger_button)

    async def off(self, seat=0):
        global ongoing_game_state_transition

        if not ongoing_game_state_transition:
            self.nsg.release(self.trigger_button)


class NinSwitchWePlayGame(Game):
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
                "X": XSwitch(self.nsg, NSButton.X),
                "A": ASwitch(self.nsg, NSButton.A),
                "B": BSwitch(self.nsg, NSButton.B),
                "left_throttle": NSSwitch(self.nsg, NSButton.LEFT_THROTTLE),
                "left_trigger": TriggerSwitch(self.nsg, NSButton.LEFT_TRIGGER),
                "right_throttle": NSSwitch(self.nsg, NSButton.RIGHT_THROTTLE),
                "right_trigger": TriggerSwitch(
                    self.nsg, NSButton.RIGHT_TRIGGER
                ),
                "minus": MinusSwitch(self.nsg, NSButton.MINUS),
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
                    f"on_config: Not on Home, current game selected {i}."
                )
                if i >= 10:
                    logging.info("on_config: single pressing Home")
                    await self.single_press(NSButton.HOME)
                await asyncio.sleep(1)
                i += 1
            logging.info("on_config: On Home, current game selected")

        # reset the board
        self.pi.write(20, 0)
        self.pi.write(21, 0)
        await asyncio.sleep(PRESS_TIME)
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

        # give image rec some time to press retry from the game over screen
        await asyncio.sleep(0.4)

        # make sure game over is away
        # (three times because of failing frame reads...)
        while (
            await self.is_maybe_game_over()
            or await self.is_maybe_game_over()
            or await self.is_maybe_game_over()
        ):
            logging.info("Waiting for Game Over to go away...")

        # enable playing
        async with self.lock:
            self.inputs_can_be_enabled = True
            self.io.enable_inputs()
            logging.info("Inputs enabled")

    async def on_finish(self):
        self.inputs_can_be_enabled = False
        self.io.disable_inputs()
        logging.info("on_finish: resetting inputs")
        self.nsg.releaseAll()

        async with self.lock:
            # why the first press does not work?
            await self.single_press(NSButton.HOME)
            # the workaround...
            i = 0
            while not await self.is_home_current_selected():
                logging.info(
                    f"on_finish: Not on Home, current game selected {i}."
                )
                if i % 3 == 0:  # take failed frames into account
                    logging.info("on_finish: single pressing Home")
                    await self.single_press(NSButton.HOME)
                await asyncio.sleep(POST_PRESS_TIME)
                i += 1
            logging.info("on_finish: On Home, current game selected")

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
            await asyncio.sleep(PRESS_TIME)
            self.nsg.release(pressable)
        elif type(pressable) == NSDPad:
            self.nsg.dPad(pressable)
            await asyncio.sleep(PRESS_TIME)
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
    NinSwitchWePlayGame().run(start_games_inputs_enabled=False)
