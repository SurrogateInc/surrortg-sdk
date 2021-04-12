import asyncio
import copy
import logging
import time

import pigpio


class Servo:
    def __init__(
        self,
        pin,
        initial_value=None,
        min_pulse_width=500,
        max_pulse_width=2500,
        move_min_full_sweep_time=0.5,
        move_update_freq=20,
    ):
        assert (
            500 <= min_pulse_width <= 2500
        ), "min_pulse_width should be between 500 and 2500"
        assert (
            500 <= max_pulse_width <= 2500
        ), "max_pulse_width should be between 500 and 2500"
        assert (
            min_pulse_width < max_pulse_width
        ), "min_pulse_width should be less than max_pulse_width"
        assert (
            move_min_full_sweep_time > 0
        ), "move_min_full_sweep_time should be positive"
        assert move_update_freq > 0, "move_update_freq should be positive"

        self._pin = pin
        self._min_pulse_width = min_pulse_width
        self._max_pulse_width = max_pulse_width
        self._max_move_amount = 1 / (
            move_update_freq * move_min_full_sweep_time
        )
        self._move_update_freq = move_update_freq
        self._latest_move_start_time = None

        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Could not connect to pigpio daemon")
        self.pi.set_mode(self._pin, pigpio.OUTPUT)

        if initial_value is not None:
            self.value = initial_value

    @property
    def value(self):
        pulse_width = self.pi.get_servo_pulsewidth(self._pin)
        if pulse_width == 0:  # Is detached
            return None
        return (pulse_width - self._min_pulse_width) / (
            self._max_pulse_width - self._min_pulse_width
        )

    @value.setter
    def value(self, value):
        assert 0 <= value <= 1, f"Value {value} not inside 0 to 1 or None"
        scaled_val = (
            value * (self._max_pulse_width - self._min_pulse_width)
            + self._min_pulse_width
        )  # Scale 0-1 between min and max pulse width
        self.pi.set_servo_pulsewidth(self._pin, scaled_val)

    def detach(self):
        self.pi.set_servo_pulsewidth(self._pin, 0)

    def min(self):
        self.value = 0

    def mid(self):
        self.value = 0.5

    def max(self):
        self.value = 1.0

    def start_moving(self, speed):
        asyncio.create_task(self.move_until_end(speed))

    async def move_until_end(self, speed):
        assert -1 <= speed <= 1, f"Speed {speed} outside -1 to 1"
        assert speed != 0, "Speed cannot be 0"

        if self.value is None:
            logging.warning("Servo start value not known, guessing middle 0.5")
            self.value = 0.5

        self._latest_move_start_time = time.time()
        move_start_time_copy = copy.copy(self._latest_move_start_time)
        await self._move_until_end(speed, move_start_time_copy)

    def _move_values(self, speed, move_start_time):
        while True:
            if (
                self._latest_move_start_time != move_start_time  # New move
                or self.value is None  # Is detached
                or (speed < 0 and self.value == 0)  # At min end
                or (speed > 0 and self.value == 1)  # At max end
            ):
                return

            yield max(0, min(1, self.value + self._max_move_amount * speed))

    async def _move_until_end(self, speed, move_start_time):
        for value in self._move_values(speed, move_start_time):
            self.value = value
            await asyncio.sleep(1 / self._move_update_freq)

    def stop_moving(self):
        self._latest_move_start_time = None

    def stop(self):
        self.stop_moving()
        self.detach()
        self.pi.stop()


if __name__ == "__main__":

    async def main():
        servo = Servo(17)

        servo.value = 0
        time.sleep(1)
        print(f"Servo value: {servo.value}")

        servo.detach()
        time.sleep(1)
        print(f"Servo value: {servo.value}")

        servo.value = 0.5
        time.sleep(1)
        print(f"Servo value: {servo.value}")

        servo.value = 1
        time.sleep(1)
        print(f"Servo value: {servo.value}")

        print("Moving left max speed in background")
        servo.start_moving(-1)
        await asyncio.sleep(1)

        print("Moving right 1/5th speed until at the end")
        await servo.move_until_end(0.2)

        servo.stop()

    asyncio.run(main())
