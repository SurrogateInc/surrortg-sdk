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
        min_full_sweep_time=0.5,
        rotation_update_freq=25,
    ):
        """Simple to use servo class implemented with pigpio

        position property handles immediate position changes.
        rotation_speed property handles rotation with a spesific speed
        in the background.
        Also has rotate_to, detach and stop methods.

        :param pin: GPIO pin number
        :type pin: int
        :param min_pulse_width: between 500 and 2500, defaults to 500
        :type min_pulse_width: int, optional
        :param max_pulse_width: between 500 and 2500, defaults to 2500
        :type max_pulse_width: int, optional
        :param min_full_sweep_time: full sweep time in seconds,
            defaults to 0.5
        :type min_full_sweep_time: float, optional
        :param rotation_update_freq: rotation position update frequenzy,
            defaults to 25
        :type rotation_update_freq: int, optional
        :raises RuntimeError: If cannot connect to pigpio daemon
        """
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
            min_full_sweep_time > 0
        ), "min_full_sweep_time should be positive"
        assert (
            rotation_update_freq > 0
        ), "rotation_update_freq should be positive"

        self._pin = pin
        self._min_pulse_width = min_pulse_width
        self._max_pulse_width = max_pulse_width
        self._mid_pulse_width = (max_pulse_width + min_pulse_width) / 2
        self._max_pos_change_per_update = 2 / (
            rotation_update_freq * min_full_sweep_time
        )
        self._rotation_update_freq = rotation_update_freq
        self._latest_rotation_start_time = None
        self._rotation_speed = 0
        self._stopped = False

        self._pi = pigpio.pi()
        if not self._pi.connected:
            raise RuntimeError("Could not connect to pigpio daemon")
        self._pi.set_mode(self._pin, pigpio.OUTPUT)
        self._pi.set_servo_pulsewidth(self._pin, 0)

    @property
    def position(self):
        """:param position: Servo position between -1 and 1

        :return: 0 is in the middle, negative positions are on the left and
            positive are on the right
        :rtype: int
        """

        self._check_if_stopped()

        pulse_width = self._pi.get_servo_pulsewidth(self._pin)
        if pulse_width == 0:  # Is detached
            return None
        return (
            -(pulse_width - self._min_pulse_width)
            / (self._max_pulse_width - self._min_pulse_width)
            * 2
            + 1
        )

    @position.setter
    def position(self, position):
        assert -1 <= position <= 1, f"Position {position} not inside -1 to 1"
        self._check_if_stopped()

        scaled_pos = (
            -position * (self._mid_pulse_width - self._min_pulse_width)
            + self._mid_pulse_width
        )  # Scale -1 to 1 between min and max pulse width
        self._pi.set_servo_pulsewidth(self._pin, scaled_pos)

    @property
    def rotation_speed(self):
        """:param rotation_speed: Servo rotation speed between -1 and 1

        0 stops the servo, positive value rotates clockwise and negative
        counterclockwise. When end position is reached, servo stops and
        the rotation_speed updates to 0.

        :return: rotation speed value between -1 and 1
        :rtype: int
        """
        self._check_if_stopped()

        return self._rotation_speed

    @rotation_speed.setter
    def rotation_speed(self, rotation_speed):
        assert (
            -1 <= rotation_speed <= 1
        ), f"Rotation speed {rotation_speed} outside -1 to 1"
        self._check_if_stopped()

        # Set rotation speed
        self._rotation_speed = rotation_speed

        # Stop or start rotation depending on the value
        if rotation_speed == 0:
            self._latest_rotation_start_time = None
        else:
            position = -1 if rotation_speed < 0 else 1
            asyncio.create_task(self.rotate_to(position, rotation_speed))

    async def rotate_to(self, position, rotation_speed=None):
        """Rotate to some position, optionally with a spesific speed

        :param position: position between -1 and 1, see position property
        :type position: int
        :param rotation_speed: rotation speed between -1 and 1,
            see rotation_speed property. Defaults to None,
            which is changed to the max speed in the correct direction.
        :type rotation_speed: int, optional
        """
        self._check_if_stopped()

        if self.position is None:
            logging.warning("Servo position not known, guessing middle 0")
            self.position = 0

        if rotation_speed is None:
            rotation_speed = -1 if position < self.position else 1

        assert (
            -1 <= rotation_speed <= 1
        ), f"Rotation speed {rotation_speed} outside -1 to 1"
        assert rotation_speed != 0, "Rotation speed cannot be 0"

        # This stops all ongoing rotations
        self._latest_rotation_start_time = time.time()
        rotation_start_time_copy = copy.copy(self._latest_rotation_start_time)

        if rotation_speed < 0 and position <= self.position:
            min_position = position
            max_position = 1
        elif rotation_speed > 0 and position >= self.position:
            min_position = -1
            max_position = position
        else:
            logging.warning(
                f"Rotation speed {rotation_speed} goes away from position "
                f"{position}, as the current position is {self.position}. "
                "Not rotating."
            )
            return

        for position in self._rotation_positions(
            rotation_speed,
            rotation_start_time_copy,
            min_position,
            max_position,
        ):
            self.position = position
            await asyncio.sleep(1 / self._rotation_update_freq)

        # Set the rotation speed to 0
        # unless a new rotation was started or detached
        if self._latest_rotation_start_time == rotation_start_time_copy:
            self.rotation_speed = 0

    def _rotation_positions(
        self, speed, rotation_start_time, min_position, max_position
    ):
        while (
            self._latest_rotation_start_time
            == rotation_start_time  # No new rotations, stopped or detached
            and not (
                speed < 0 and self.position == min_position
            )  # Not at min end
            and not (
                speed > 0 and self.position == max_position
            )  # Not at max end
        ):
            yield max(
                min_position,
                min(
                    max_position,
                    self.position + self._max_pos_change_per_update * speed,
                ),
            )

    def _check_if_stopped(self):
        if self._stopped:
            raise RuntimeError("Servo already stopped")

    def detach(self):
        """Stops servo rotation and releases active servo control"""

        self._check_if_stopped()

        self.rotation_speed = 0
        self._pi.set_servo_pulsewidth(self._pin, 0)

    def stop(self):
        """Detaches servo and stops pigpio daemon connection"""

        self.detach()
        self._pi.stop()
        self._stopped = True


if __name__ == "__main__":

    async def main():
        servo = Servo(17)

        servo.position = -1
        print(f"Servo position: {servo.position}")
        time.sleep(1)

        servo.detach()
        print(f"Servo position: {servo.position}")
        time.sleep(1)

        servo.position = 0
        print(f"Servo position: {servo.position}")
        time.sleep(1)

        servo.position = 1
        print(f"Servo position: {servo.position}")
        time.sleep(1)

        print("Moving left max speed in background")
        servo.rotation_speed = -1
        await asyncio.sleep(1)

        print("Moving right half speed in background")
        servo.rotation_speed = 0.5
        await asyncio.sleep(1)

        print("Moving left 1/10th speed until at the middle")
        await servo.rotate_to(0, rotation_speed=-0.1)

        servo.stop()

    asyncio.run(main())
