from gpiozero import LED
from surrortg import Game
from surrortg.inputs import Switch
import logging


class LEDSwitch(Switch):
    def __init__(self, score_cb):
        self.led = LED(17)
        self.score_cb = score_cb

    async def on(self, seat=0):
        logging.info("LED on")
        self.led.on()
        self.score_cb()

    async def off(self, seat=0):
        logging.info("LED off")
        self.led.off()


class LedTestGame(Game):
    def update_score(self):
        self.score += 1
        logging.info(f"score: {self.score}")
        if self.score >= 10:
            self.io.send_score(score=self.score, final_score=True)
        else:
            self.io.send_score(score=self.score)

    async def on_init(self):
        self.io.register_inputs({"switch": LEDSwitch(self.update_score)})

    async def on_prepare(self):
        self.score = 0


LedTestGame().run()
