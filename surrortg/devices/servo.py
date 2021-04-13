import asyncio
import copy
import logging
import time

import pigpio


class Servo:
    def __init__(
        self,
        pin,
        min_pulse_width=500,
        max_pulse_width=2500,
        move_min_full_sweep_time=0.5,
        move_update_freq=25,
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
        self._rotation_speed = 0

        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Could not connect to pigpio daemon")
        self.pi.set_mode(self._pin, pigpio.OUTPUT)

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

    @property
    def rotation_speed(self):
        return self._rotation_speed

    @rotation_speed.setter
    def rotation_speed(self, rotation_speed):
        self._rotation_speed = rotation_speed
        if rotation_speed == 0:
            self._latest_move_start_time = None
        else:
            value = 0 if rotation_speed < 0 else 1
            asyncio.create_task(self.rotate_to(value, rotation_speed))

    async def rotate_to(self, value, rotation_speed=None):
        if self.value is None:
            logging.warning("Servo start value not known, guessing middle 0.5")
            self.value = 0.5

        if rotation_speed is None:
            rotation_speed = -1 if value < self.value else 1

        assert (
            -1 <= rotation_speed <= 1
        ), f"Rotation speed {rotation_speed} outside -1 to 1"
        assert rotation_speed != 0, "Rotation speed cannot be 0"

        if rotation_speed < 0 and value <= self.value:
            min_value = value
            max_value = 1
        elif rotation_speed > 0 and value >= self.value:
            min_value = 0
            max_value = value
        else:
            logging.warning(
                f"Rotation speed {rotation_speed} goes away from value "
                f"{value}, as the current value is {self.value}. "
                "Not rotating."
            )
            return

        self._latest_move_start_time = time.time()
        move_start_time_copy = copy.copy(self._latest_move_start_time)

        for value in self._rotation_values(
            rotation_speed, move_start_time_copy, min_value, max_value
        ):
            self.value = value
            await asyncio.sleep(1 / self._move_update_freq)
        self._rotation_speed = 0

    def _rotation_values(self, speed, move_start_time, min_value, max_value):
        while (
            self._latest_move_start_time
            == move_start_time  # No new moves, stopped or detached
            and not (speed < 0 and self.value == min_value)  # Not at min end
            and not (speed > 0 and self.value == max_value)  # Not at max end
        ):
            yield max(
                min_value,
                min(max_value, self.value + self._max_move_amount * speed),
            )

    def detach(self):
        self.rotation_speed = 0
        self.pi.set_servo_pulsewidth(self._pin, 0)

    def stop(self):
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
        servo.rotation_speed = -1
        await asyncio.sleep(1)

        print("Moving right half speed in background")
        servo.rotation_speed = 0.5
        await asyncio.sleep(1)

        print("Moving left 1/10th speed until at the middle")
        await servo.rotate_to(0.5, rotation_speed=-0.1)
        await servo.rotate_to(1)
        await servo.rotate_to(0)

        servo.stop()

    asyncio.run(main())
