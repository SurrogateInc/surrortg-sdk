from gpiozero import LED
from surrortg import Game
from surrortg.inputs import Switch


class LEDSwitch(Switch):
    def __init__(self):
        self.led = LED(17)

    async def on(self, seat=0):
        print("LED on")
        self.led.on()

    async def off(self, seat=0):
        print("LED off")
        self.led.off()


class LedTestGame(Game):
    async def on_init(self):
        self.io.register_inputs({"switch": LEDSwitch()})


LedTestGame().run()
