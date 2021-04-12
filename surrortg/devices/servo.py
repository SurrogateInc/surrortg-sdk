import pigpio


class Servo:
    def __init__(
        self,
        pin,
        initial_value=None,
        min_pulse_width=500,
        max_pulse_width=2500,
        move_min_sweep_time=1,
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

        self.pin = pin
        self.min_pulse_width = min_pulse_width
        self.max_pulse_width = max_pulse_width
        self.move_min_sweep_time = move_min_sweep_time
        self.move_update_freq = move_update_freq

        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Could not connect to pigpio daemon")
        self.pi.set_mode(self.pin, pigpio.OUTPUT)

        if initial_value is not None:
            self.value = initial_value

    def detach(self):
        self.pi.set_servo_pulsewidth(self.pin, 0)

    @property
    def value(self):
        pulse_width = self.pi.get_servo_pulsewidth(self.pin)
        if pulse_width == 0:  # Is detached
            return None
        return (pulse_width - self.min_pulse_width) / (
            self.max_pulse_width - self.min_pulse_width
        )

    @value.setter
    def value(self, value):
        assert 0 <= value <= 1, f"Value {value} not inside 0 to 1 or None"
        scaled_val = (
            value * (self.max_pulse_width - self.min_pulse_width)
            + self.min_pulse_width
        )  # Scale 0-1 between min and max pulse width
        self.pi.set_servo_pulsewidth(self.pin, scaled_val)

    def min(self):
        self.value = 0

    def mid(self):
        self.value = 0.5

    def max(self):
        self.value = 1.0

    async def start_moving(self, speed):
        assert -1 <= speed <= 1, f"Speed {speed} outside -1 to 1"
        # TODO move until stopped
        # - move_min_sweep_time tells the min time to move from min to max,
        #   which corresponds to speed of 1
        # - move_update_freq tells how many times updated per second

    def stop_moving(self):
        # TODO stop moving
        pass

    def stop(self):
        self.stop_moving()
        self.detach()
        self.pi.stop()


if __name__ == "__main__":
    import time

    servo = Servo(17)
    servo.value = 0
    print(f"Servo value: {servo.value}")
    time.sleep(1)
    servo.value = 0.5
    print(f"Servo value: {servo.value}")
    time.sleep(1)
    servo.value = 1
    print(f"Servo value: {servo.value}")
    time.sleep(1)
    servo.detach()
    print(f"Servo value: {servo.value}")
    time.sleep(1)
    servo.stop()
    print("Stopped")
