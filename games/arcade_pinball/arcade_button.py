import asyncio
import logging

import pigpio

from games.arcade_pinball.config import (
    BUTTON_PRESS_TIME,
    MAX_HOLD_TIME,
    MAX_INPUTS_PER_INPUT,
    PER_SECONDS,
)
from surrortg.inputs import Switch
from surrortg.inputs.input_filters import SpamFilter


class ArcadeMultiButton(Switch):
    def __init__(
        self,
        pi,
        pins,
        name,
        abuse_function=None,
        button_press_time=BUTTON_PRESS_TIME,
    ):
        self.pi = pi
        self.pins = pins
        self.name = name
        self.button_press_time = button_press_time
        self.abuse_callback = abuse_function
        self.task = None
        self.spam_filter = SpamFilter(MAX_INPUTS_PER_INPUT, PER_SECONDS)

        for pin in self.pins:
            self.pi.set_mode(pin, pigpio.OUTPUT)

    async def on(self, seat=0):
        if not self.spam_filter.too_much_spam():
            logging.debug(f"{self.name} on")
            for pin in self.pins:
                self.pi.write(pin, 0)
            self._reset_timer(True)
        else:
            logging.info(f"Too much spam for {self.name}")
            await self.off()

    async def off(self, seat=0):
        logging.debug(f"{self.name} off")
        for pin in self.pins:
            self.pi.write(pin, 1)
        self._reset_timer(False)

    async def shutdown(self, seat=0):
        # ArcadePinballGame handles stopping pigpio
        if self.pi.connected:
            await self.off()

    async def single_press(self):
        await self.on()
        await asyncio.sleep(self.button_press_time)
        await self.off()

    def _reset_timer(self, start_new):
        if self.task is not None and not self.task.cancelled():
            self.task.cancel()
        if start_new:
            self.task = asyncio.create_task(self._lock_controls())

    async def _lock_controls(self):
        await asyncio.sleep(MAX_HOLD_TIME)
        logging.info("Locking controls due to abuse")
        if self.abuse_callback is not None:
            await self.abuse_callback()


class ArcadeButton(ArcadeMultiButton):
    def __init__(
        self,
        pi,
        pin,
        name,
        abuse_function=None,
        button_press_time=BUTTON_PRESS_TIME,
    ):
        super().__init__(
            pi,
            [pin],
            name,
            abuse_function=abuse_function,
            button_press_time=button_press_time,
        )


if __name__ == "__main__":
    from games.arcade_pinball.config import (
        LEFT_FLIPPER_PIN,
        MAGNET_BUTTON_PIN,
        RIGHT_FLIPPER_PINS,
        SERVICE_BUTTON_PIN,
        START_BUTTON_PIN,
    )

    async def test_buttons():
        pi = pigpio.pi()
        if not pi.connected:
            raise RuntimeError("Could not connect to pigpio")

        left_flipper = ArcadeButton(pi, LEFT_FLIPPER_PIN, "left")
        right_flipper = ArcadeMultiButton(pi, RIGHT_FLIPPER_PINS, "right")
        magnet_button = ArcadeButton(pi, MAGNET_BUTTON_PIN, "magnet")
        start_button = ArcadeButton(pi, START_BUTTON_PIN, "start")
        service_menu_button = ArcadeButton(pi, SERVICE_BUTTON_PIN, "service")

        try:
            while True:
                await left_flipper.on()
                await right_flipper.on()
                await magnet_button.on()
                await start_button.on()
                await service_menu_button.on()
                asyncio.sleep(5)
                await left_flipper.off()
                await right_flipper.off()
                await magnet_button.off()
                await start_button.off()
                await service_menu_button.off()
                asyncio.sleep(5)
        except KeyboardInterrupt:
            await left_flipper.off()
            await right_flipper.off()
            await magnet_button.off()
            await start_button.off()
            await service_menu_button.off()

        pi.stop()

    asyncio.run(test_buttons())
