from surrortg.inputs import Switch


class NSSwitch(Switch):
    def __init__(self, nsg, button):
        self.nsg = nsg
        self.button = button

    async def on(self, seat=0):
        self.nsg.press(self.button)

    async def off(self, seat=0):
        self.nsg.release(self.button)
