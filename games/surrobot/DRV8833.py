import logging

import pigpio


class DRV8833:
    def __init__(self, *, ain1, ain2, bin1, bin2, sleep=None, pwm_freq=40000):
        # Connect to pigpio daemon
        self._pi = pigpio.pi()
        if not self._pi.connected:
            raise RuntimeError("Could not connect to pigpio daemon.")

        # Store motor speeds
        self._motor_1_speed = 0
        self._motor_2_speed = 0

        # Store motor driver control pins
        self._ain1 = ain1
        self._ain2 = ain2
        self._bin1 = bin1
        self._bin2 = bin2
        self._sleep = sleep

        # Set motor driver control pins to output mode
        self._pi.set_mode(self._ain1, pigpio.OUTPUT)
        self._pi.set_mode(self._ain2, pigpio.OUTPUT)
        self._pi.set_mode(self._bin1, pigpio.OUTPUT)
        self._pi.set_mode(self._bin2, pigpio.OUTPUT)
        if self._sleep is not None:
            self._pi.set_mode(self._sleep, pigpio.OUTPUT)

        # Set motor driver speed control PWM frequency
        self._pi.set_PWM_frequency(self._ain1, pwm_freq)
        self._pi.set_PWM_frequency(self._ain2, pwm_freq)
        self._pi.set_PWM_frequency(self._bin1, pwm_freq)
        self._pi.set_PWM_frequency(self._bin2, pwm_freq)

        # Stop motors and enable motor driver
        self._pi.set_PWM_dutycycle(self._ain1, 0)
        self._pi.set_PWM_dutycycle(self._ain2, 0)
        self._pi.set_PWM_dutycycle(self._bin1, 0)
        self._pi.set_PWM_dutycycle(self._bin2, 0)
        if self._sleep is not None:
            self._pi.write(self._sleep, pigpio.HIGH)

    def set_motor_speed(self, *, motor_number, speed):
        assert 1 <= motor_number <= 2, f"Invalid motor number: {motor_number}."
        assert -1 <= speed <= 1, f"Motor speed out of range: {speed}."
        logging.debug(f"Motor {motor_number} speed: {speed}.")

        if motor_number == 1:
            self._motor_1_speed = speed
        else:
            self._motor_2_speed = speed

        # Convert the speed to range of 0 - 255
        speed = round(speed * 255)

        # Convert speed to PWM duty cycle
        # Duty cycle must be positive and inverted for slow decay mode
        duty_cycle = 255 - abs(speed)

        if motor_number == 1:
            if speed > 0:
                # Forward in slow decay mode
                self._pi.set_PWM_dutycycle(self._ain1, 255)
                self._pi.set_PWM_dutycycle(self._ain2, duty_cycle)
            else:
                # Reverse or braking in slow decay mode
                self._pi.set_PWM_dutycycle(self._ain1, duty_cycle)
                self._pi.set_PWM_dutycycle(self._ain2, 255)
        else:
            if speed > 0:
                # Forward in slow decay mode
                self._pi.set_PWM_dutycycle(self._bin1, 255)
                self._pi.set_PWM_dutycycle(self._bin2, duty_cycle)
            else:
                # Reverse or braking in slow decay mode
                self._pi.set_PWM_dutycycle(self._bin1, duty_cycle)
                self._pi.set_PWM_dutycycle(self._bin2, 255)

    def get_motor_speed(self, *, motor_number):
        assert 1 <= motor_number <= 2, f"Invalid motor number: {motor_number}."

        if motor_number == 1:
            return self._motor_1_speed
        else:
            return self._motor_2_speed


class DRV8833Motor:
    def __init__(self, *, drv8833, motor_number, direction="+"):
        assert 1 <= motor_number <= 2, f"Invalid motor number: {motor_number}."
        assert (
            direction == "+" or direction == "-"
        ), "Incorrect direction, must be either '+' or '-'."

        self._drv8833 = drv8833
        self._motor_number = motor_number
        self._direction = 1 if direction == "+" else -1

    @property
    def speed(self):
        return self._drv8833.get_motor_speed(motor_number=self._motor_number)

    @speed.setter
    def speed(self, speed):
        assert -1 <= speed <= 1, f"Motor speed out of range: {speed}."

        # Correct the direction
        speed *= self._direction

        self._drv8833.set_motor_speed(
            motor_number=self._motor_number, speed=speed
        )


class MotorController:
    def __init__(self, motor_fl, motor_fr, motor_rr, motor_rl):
        # Store all motors
        self._motor_fl = motor_fl
        self._motor_fr = motor_fr
        self._motor_rr = motor_rr
        self._motor_rl = motor_rl

        # Longitudinal = speed along forward-backward axis
        # Rotational = rotational speed around the center of the wheels
        self._longitudinal_speed = 0
        self._rotational_speed = 0

    @property
    def longitudinal_speed(self):
        return self._longitudinal_speed

    @longitudinal_speed.setter
    def longitudinal_speed(self, speed):
        if speed > 1:
            speed = 1
        if speed < -1:
            speed = -1
        self._longitudinal_speed = speed
        self._update_speed()

    @property
    def rotational_speed(self):
        return self._rotational_speed

    @rotational_speed.setter
    def rotational_speed(self, speed):
        if speed > 1:
            speed = 1
        if speed < -1:
            speed = -1
        self._rotational_speed = speed
        self._update_speed()

    def _update_speed(self):
        # Set forward/backward speed
        speed_fl = self._longitudinal_speed
        speed_fr = self._longitudinal_speed
        speed_rr = self._longitudinal_speed
        speed_rl = self._longitudinal_speed

        # Add rotational speed
        speed_fl += self._rotational_speed
        speed_fr -= self._rotational_speed
        speed_rr -= self._rotational_speed
        speed_rl += self._rotational_speed

        # Limit one wheel speed between -1 to 1
        if speed_fl > 1:
            speed_fl = 1
        if speed_fr > 1:
            speed_fr = 1
        if speed_rr > 1:
            speed_rr = 1
        if speed_rl > 1:
            speed_rl = 1
        if speed_fl < -1:
            speed_fl = -1
        if speed_fr < -1:
            speed_fr = -1
        if speed_rr < -1:
            speed_rr = -1
        if speed_rl < -1:
            speed_rl = -1

        self._motor_fl.speed = speed_fl
        self._motor_fr.speed = speed_fr
        self._motor_rr.speed = speed_rr
        self._motor_rl.speed = speed_rl
