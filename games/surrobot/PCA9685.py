#!/usr/bin/python

import math
import time
from surrortg.devices import Servo
import smbus

# ============================================================================
# Raspi PCA9685 16-Channel PWM Servo Driver
# ============================================================================


class PCA9685:

    # Registers/etc.
    __SUBADR1 = 0x02
    __SUBADR2 = 0x03
    __SUBADR3 = 0x04
    __MODE1 = 0x00
    __PRESCALE = 0xFE
    __LED0_ON_L = 0x06
    __LED0_ON_H = 0x07
    __LED0_OFF_L = 0x08
    __LED0_OFF_H = 0x09
    __ALLLED_ON_L = 0xFA
    __ALLLED_ON_H = 0xFB
    __ALLLED_OFF_L = 0xFC
    __ALLLED_OFF_H = 0xFD

    def __init__(self, address=0x40, debug=False):
        self.bus = smbus.SMBus(1)
        self.address = address
        self.debug = debug
        if self.debug:
            print("Reseting PCA9685")
        self.write(self.__MODE1, 0x00)

    def write(self, reg, value):
        "Writes an 8-bit value to the specified register/address"
        self.bus.write_byte_data(self.address, reg, value)
        if self.debug:
            print("I2C: Write 0x%02X to register 0x%02X" % (value, reg))

    def read(self, reg):
        "Read an unsigned byte from the I2C device"
        result = self.bus.read_byte_data(self.address, reg)
        if self.debug:
            print(
                "I2C: Device 0x%02X returned 0x%02X from reg 0x%02X"
                % (self.address, result & 0xFF, reg)
            )
        return result

    def set_pwm_freq(self, freq):
        "Sets the PWM frequency"
        prescaleval = 25000000.0  # 25MHz
        prescaleval /= 4096.0  # 12-bit
        prescaleval /= float(freq)
        prescaleval -= 1.0
        if self.debug:
            print("Setting PWM frequency to %d Hz" % freq)
            print("Estimated pre-scale: %d" % prescaleval)
        prescale = math.floor(prescaleval + 0.5)
        if self.debug:
            print("Final pre-scale: %d" % prescale)

        oldmode = self.read(self.__MODE1)
        newmode = (oldmode & 0x7F) | 0x10  # sleep
        self.write(self.__MODE1, newmode)  # go to sleep
        self.write(self.__PRESCALE, int(math.floor(prescale)))
        self.write(self.__MODE1, oldmode)
        time.sleep(0.005)
        self.write(self.__MODE1, oldmode | 0x80)

    def set_pwm(self, channel, on, off):
        "Sets a single PWM channel"
        self.write(self.__LED0_ON_L + 4 * channel, on & 0xFF)
        self.write(self.__LED0_ON_H + 4 * channel, on >> 8)
        self.write(self.__LED0_OFF_L + 4 * channel, off & 0xFF)
        self.write(self.__LED0_OFF_H + 4 * channel, off >> 8)
        if self.debug:
            print("channel: %d  LED_ON: %d LED_OFF: %d" % (channel, on, off))

    def set_servo_pulse(self, channel, pulse):
        "Sets the Servo Pulse,The PWM frequency must be 50HZ"
        pulse = (
            pulse * 4096 / 20000
        )  # PWM frequency is 50HZ,the period is 20000us
        self.set_pwm(channel, 0, int(pulse))


class PCA9685Servo(Servo):
    def __init__(
        self,
        pwm,
        channel=0,
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

        self._min_pulse_width = min_pulse_width
        self._max_pulse_width = max_pulse_width
        self._mid_pulse_width = (max_pulse_width + min_pulse_width) / 2
        self._max_pos_change_per_update = 2 / (
            rotation_update_freq * min_full_sweep_time
        )
        self._rotation_update_freq = rotation_update_freq
        self._latest_rotation_start_time = None
        self._position = None
        self._rotation_speed = 0
        self._stopped = False

        self._channel = channel
        self._pwm = pwm

    def _set_position(self, position):
        scaled_pos = (
            -position * (self._mid_pulse_width - self._min_pulse_width)
            + self._mid_pulse_width
        )  # Scale -1 to 1 between min and max pulse width
        self._pwm.set_servo_pulse(self._channel, int(scaled_pos))
        self._position = position

if __name__ == "__main__":

    pwm = PCA9685(0x40, debug=False)
    pwm.set_pwm_freq(50)
    while True:
        # set_servo_pulse(2,2500)
        for i in range(500, 2500, 10):
            pwm.set_servo_pulse(0, i)
            time.sleep(0.02)

        for i in range(2500, 500, -10):
            pwm.set_servo_pulse(0, i)
            time.sleep(0.02)
