import pigpio

from games.ninswitch.config import RESET_TRINKET_EACH_LOOP
from games.ninswitch.ns_dpad_switch import NSDPadSwitch
from games.ninswitch.ns_gamepad_serial import NSButton, NSDPad, NSGamepadSerial
from games.ninswitch.ns_joystick import NSJoystick
from games.ninswitch.ns_switch import NSSwitch
from games.ninswitch.trinket_reset_switch import TrinketResetSwitch
from surrortg import Game


class NinSwitchSimpleGame(Game):
    async def on_init(self):
        # connect to pigpio daemon
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Could not connect to pigpio daemon")

        # init controls
        self.nsg = NSGamepadSerial()
        self.nsg.begin()
        self.trinket_reset_switch = TrinketResetSwitch(self.pi)

        # register player controls
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

        # register admin controls
        self.io.register_inputs(
            {"trinket_reset": self.trinket_reset_switch},
            admin=True,
        )

    """
    here you could do something with
    on_config, on_prepare, on_pre_game, on_countdown, on_start...
    """

    async def on_prepare(self):
        if RESET_TRINKET_EACH_LOOP:
            await self.trinket_reset_switch.reset_trinket()

    async def on_finish(self):
        self.io.disable_inputs()
        self.nsg.releaseAll()

    async def on_exit(self, reason, exception):
        # close controls
        self.nsg.end()
        self.trinket_reset_switch.close()
        # close the connection to pigpio daemon
        self.pi.stop()


if __name__ == "__main__":
    NinSwitchSimpleGame().run()
