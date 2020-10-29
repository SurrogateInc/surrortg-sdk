from surrortg.inputs import Switch
from games.ninswitch.ns_gamepad_serial import NSDPad


class NSDPadSwitch(Switch):
    def __init__(self, nsg, dpad_dir):
        self.nsg = nsg
        self.dpad_dir = dpad_dir

    async def on(self, seat=0):
        self.nsg.dPad(self.dpad_dir)

    async def off(self, seat=0):
        self.nsg.dPad(NSDPad.CENTERED)
