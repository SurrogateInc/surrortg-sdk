import logging

import pigpio

from surrortg import Game
from surrortg.inputs import Switch

LED_PIN = 17


class LEDSwitch(Switch):
    def __init__(self, score_cb):
        # Connect to pigpio daemon
        self._pi = pigpio.pi()
        if not self._pi.connected:
            raise RuntimeError("Could not connect to pigpio daemon.")

        # Initialize LED pin
        self._pi.set_mode(LED_PIN, pigpio.OUTPUT)
        # Store reference to score callback function
        self.score_cb = score_cb

    async def on(self, seat=0):
        self._pi.write(LED_PIN, pigpio.HIGH)
        self.score_cb()
        logging.info("LED on")

    async def off(self, seat=0):
        self._pi.write(LED_PIN, pigpio.LOW)
        logging.info("LED off")

    async def shutdown(self, seat):
        # Set LED pin into safe state by setting it to input mode
        self._pi.set_mode(LED_PIN, pigpio.INPUT)
        # Close pigpio daemon connection
        self._pi.close()


class LedTestGame(Game):
    def update_score(self):
        self.score += 1
        logging.info(f"score: {self.score}")
        if self.score >= 10:
            # End game by sending final score to game engine.
            self.io.send_score(score=self.score, final_score=True)
            # Disable all registered inputs.
            self.io.disable_inputs()
        else:
            # Send updated scores to game engine.
            self.io.send_score(score=self.score)

    async def on_init(self):
        # Register LED input with update score callback function
        self.io.register_inputs({"switch": LEDSwitch(self.update_score)})

    async def on_prepare(self):
        # Set score to 0 before game starts
        self.score = 0


if __name__ == "__main__":
    # Start running the game
    LedTestGame().run()
