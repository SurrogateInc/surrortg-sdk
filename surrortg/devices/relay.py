import asyncio
import logging

import pigpio


class Relay:
    """Simple to use relay class implemented with pigpio

    :param pin: GPIO pin number
    :type pin: int
    :param on_level_low: Determines the logic level of the on-state.
        If set to True, the relay is on when the GPIO pin state is LOW.
        Defaults to True.
    :type on_level_low: bool, optional
    :param initial_state_off: Determines whether the relay should be
        set to off-state when initialized. If set to False, the relay is
        set to on-state at init. Defaults to True.
    :type initial_state_off: bool, optional
    :raises RuntimeError: If cannot connect to pigpio daemon
    :raises RuntimeError: If methods are called after calling stop
    """

    def __init__(self, pin, on_level_low=True, initial_state_off=True):
        self._pin = pin
        self._on_level_low = on_level_low
        self._stopped = False

        if on_level_low:
            self._on_level = pigpio.LOW
            self._off_level = pigpio.HIGH
        else:
            self._on_level = pigpio.HIGH
            self._off_level = pigpio.LOW

        self._pi = pigpio.pi()
        if not self._pi.connected:
            raise RuntimeError("Could not connect to pigpio daemon")
        self._pi.set_mode(self._pin, pigpio.OUTPUT)

        if initial_state_off:
            self.off()
        else:
            self.on()

    def on(self):
        """Turns the relay on"""
        self._check_if_stopped()

        self._pi.write(self._pin, self._on_level)

    def off(self):
        """Turns the relay off"""
        self._check_if_stopped()

        self._pi.write(self._pin, self._off_level)

    def toggle(self):
        """Toggles the relay's state

        Turns the relay on if the state was previously off, and vice versa.
        """
        self._check_if_stopped()

        if self.is_on():
            self.off()
        else:
            self.on()

    async def press_once(self, press_time):
        """Turns the relay on and off, waiting press_time seconds in between

        :param press_time: Time in seconds to wait between turning the relay
            on and off
        :type press_time: float or int
        """
        assert isinstance(press_time, float) or isinstance(
            press_time, int
        ), "press_time should be float or int"
        self._check_if_stopped()

        if self.is_on():
            logging.warning(
                "Relay is already on when pressing once! Will turn relay off "
                f"in {press_time} seconds."
            )

        self.on()
        await asyncio.sleep(press_time)
        self.off()

    def is_on(self):
        """Checks if the relay is turned on

        :return: True if the relay is turned on
        :rtype: bool
        """
        self._check_if_stopped()

        return self._pi.read(self._pin) == self._on_level

    def is_off(self):
        """Checks if the relay is turned off

        :return: True if the relay is turned off
        :rtype: bool
        """
        self._check_if_stopped()

        return not self.is_on()

    def on_level_is_low(self):
        """Checks if the relay is on when the GPIO state is LOW

        :return: True if the relay is on when the GPIO state is LOW
        :rtype: bool
        """
        self._check_if_stopped()

        return self._on_level_low

    def _check_if_stopped(self):
        if self._stopped:
            raise RuntimeError("Relay already stopped")

    def stop(self):
        """Sets the pin to input state and stops pigpio daemon connection"""
        self._check_if_stopped()

        self._pi.set_pull_up_down(self._pin, pigpio.PUD_OFF)
        self._pi.set_mode(self._pin, pigpio.INPUT)
        self._pi.stop()
        self._stopped = True


if __name__ == "__main__":

    async def main():
        relay = Relay(26)
        print(f"Relay on level is low: {relay.on_level_is_low()}")
        print(f"Relay is initially on: {relay.is_on()}")
        await asyncio.sleep(0.5)

        print("Turning the relay on")
        relay.on()
        await asyncio.sleep(1)
        print("Turning the relay off")
        relay.off()
        await asyncio.sleep(2)

        print("Pressing the relay once for 1 second")
        await relay.press_once(1)
        await asyncio.sleep(2)
        print("Toggle relay state")
        relay.toggle()
        print(f"Relay is now on: {relay.is_on()}")
        await asyncio.sleep(1)
        print("Toggle relay state again")
        relay.toggle()
        print(f"Relay is now off: {relay.is_off()}")

        relay.stop()

    asyncio.run(main())
