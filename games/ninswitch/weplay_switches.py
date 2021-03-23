import asyncio
import logging
from enum import Enum, auto

from games.ninswitch.ns_gamepad_serial import NSButton, NSDPad
from surrortg.inputs import Switch

# auto button presses
PRESS_TIME = 0.1
POST_PRESS_TIME = 0.5


async def single_press(pressable, nsg, post_press_sleep=True):
    if type(pressable) == NSButton:
        nsg.press(pressable)
        await asyncio.sleep(PRESS_TIME)
        nsg.release(pressable)
    elif type(pressable) == NSDPad:
        nsg.dPad(pressable)
        await asyncio.sleep(PRESS_TIME)
        nsg.dPad(NSDPad.CENTERED)
    else:
        raise RuntimeError(f"Cannot press {pressable}")

    if post_press_sleep:
        await asyncio.sleep(POST_PRESS_TIME)


class GameStates(Enum):
    """
    These states with custom Switches allows access to MAP_MENU and
    ITEMS_MENU, but do not allow accessing save files menu.
    """

    PLAYING = auto()
    MAP_MENU = auto()
    ITEMS_MENU = auto()


# on_init does one B press, so this initial state should be correct
game_state = GameStates.PLAYING
# allow only one transition at once
ongoing_game_state_transition = False


class WeplayMinusSwitch(Switch):
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
            await single_press(self.minus_button, self.nsg)
            ongoing_game_state_transition = False

    async def off(self, seat=0):
        pass


class WeplayBSwitch(Switch):
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
            ongoing_game_state_transition = True
            game_state = GameStates.PLAYING
            logging.info("b: game_state PLAYING")
            await single_press(self.b_button, self.nsg)
            ongoing_game_state_transition = False
        else:
            self.nsg.press(self.b_button)

    async def off(self, seat=0):
        global ongoing_game_state_transition

        if not ongoing_game_state_transition:
            self.nsg.release(self.b_button)


class WeplayXSwitch(Switch):
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
            await single_press(self.x_button, self.nsg)
            await asyncio.sleep(2)
            await single_press(NSButton.B, self.nsg)
            logging.info("x: game_state back to MAP_MENU")
            ongoing_game_state_transition = False
        else:
            self.nsg.press(self.x_button)

    async def off(self, seat=0):
        global ongoing_game_state_transition

        if not ongoing_game_state_transition:
            self.nsg.release(self.x_button)


class WeplayASwitch(Switch):
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


class WeplayTriggerSwitch(Switch):
    """
    A normal trigger button, except when on the menus, where a trigger press
    might be different one than the one pressed.

    This forbids entering the save menu page, where someone could delete
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
            ongoing_game_state_transition = True

            game_state = GameStates.ITEMS_MENU
            logging.info("menu_trigger: game_state ITEMS_MENU")
            await single_press(NSButton.RIGHT_TRIGGER, self.nsg)

            ongoing_game_state_transition = False

        elif game_state == GameStates.ITEMS_MENU:
            ongoing_game_state_transition = True

            game_state = GameStates.MAP_MENU
            logging.info("menu_trigger: game_state MAP_MENU")
            await single_press(NSButton.LEFT_TRIGGER, self.nsg)

            ongoing_game_state_transition = False
        else:
            self.nsg.press(self.trigger_button)

    async def off(self, seat=0):
        global ongoing_game_state_transition

        if not ongoing_game_state_transition:
            self.nsg.release(self.trigger_button)
