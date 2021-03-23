import logging

import pigpio

from surrortg import Game  # First we need import the Game
from surrortg.inputs import LinearActuator  # and our preferred input(s)

MOTOR_PIN = 16
SERVO_PIN = 12


class PwmActuator(LinearActuator):
    """PwmActuator acts as controller for ESC and
    steering servo that take standard pwm servo input

    It receives values -1 ... 1 and maps that to matching
    pwm pulsewidth value where 0 input maps to 1500 pulsewidth.
    This correlates to middle position on servos, and 0 on a
    ESC.

    :param pi: instance of pigpio gpio control class
    :param pin: GPIO pin number to output the pwm signal
    :type pin: int
    :param: delta_max: Maximum value of pulsewidth dirrence
        from the middle (1500) position. Default value of 300
        translates to range of 1200 ... 1800. Be careful with this
        value as overturning servo might cause physical damage to
        the servo or the device it is attached to.
    :type delta_max: int
    :param calibration: Pulsewidth value that modifies the
        middle position used for operating. Default value 0 does
        not alter the 1500 middle position. This value can be used
        to fine tune the steering servo so that the wheels of the car
        are straight with the middle value.

    :var middle: Middle position used for 0 input mapping.
        Defaults to 1500 and adds the calibration value to itself.
    :var current_delta: Active value that is used to control
        the actuator. Defaults to half of delta_max, and can be
        modified with increase_delta and reduce_delta methods.
    """

    def __init__(self, pi, pin, delta_max=300, calibration=0):
        self.middle = 1500 + calibration
        self.delta_max = delta_max
        self.current_delta = delta_max / 2
        # Store and initialize pigpio for the control pin
        self.pi = pi
        self.pin = pin
        self.pi.set_mode(self.pin, pigpio.OUTPUT)
        self.pi.set_servo_pulsewidth(self.pin, self.middle)
        """  You can also change the pwm frequency
            if your use case requires it. More at:
            http://abyz.me.uk/rpi/pigpio/python.html#set_PWM_frequency """
        # self.pi.set_PWM_frequency(self.pin, <value>)

    async def drive_actuator(self, val, seat=0):
        """This function is called when input is received.
        It maps -1 ... 1 value to corresponding pulsewidth
        value. For example value -1 translates to 1500 (middle)
        minus current_delta which would be 1350 with default values.

        :param val: float value from ranging -1 to 1. If keyboard
            input is used it will be -1, 0 or 1.
        """
        new_val = self.middle + (val * self.current_delta)
        self.pi.set_servo_pulsewidth(self.pin, new_val)

    async def increase_delta(self, inc):
        """Method that is called from ShiftGear class to
        increase throttle or steering value. Changing the
        value will take effect only, after the input is
        cycled off-on once (release and press key).

        :param inc: Amount to increase the current_delta value
        :type: inc: int"""
        if (self.current_delta + inc) <= self.delta_max:
            self.current_delta += inc
            logging.info(
                f"current gear ratio {self.current_delta/self.delta_max}"
            )

    async def reduce_delta(self, inc):
        """Method that is called from ShiftGear class to
        decrease throttle or steering value. Changing the
        value will take effect only, after the input is
        cycled off-on once (release and press key).

        :param: inc: Amount to decrease the current_delta value
        :type: inc: int"""
        if (self.current_delta - inc) > 0:
            self.current_delta -= inc
            logging.info(
                f"current gear ratio {self.current_delta/self.delta_max}"
            )


class ShiftGear(LinearActuator):
    """Virtual actuator class that implements shifting gears or
    adjusting the amount of steering.

    :param: actuator: Instance of PwmActuator to be modified
    :param: inc: Amount of pulsewidth to modify with each shifting.
        Defaults to 10.
    :type: inc: Int
    """

    def __init__(self, actuator, inc=10):
        self.actuator = actuator
        self.increment = inc

    async def drive_actuator(self, val, seat=0):
        """Driving this virtual actuator increases the value
        of the connected actuator if the input is positive value,
        and decreases the value if it is negative. Off position
        (0) does nothing."""
        if val < 0:
            await self.actuator.reduce_delta(self.increment)
        elif val > 0:
            await self.actuator.increase_delta(self.increment)


class CarGame(Game):
    async def on_init(self):

        """First initialize the pigpio class. For this you have to have
        pigpio installed on your system and the pigpiod daemon running!"""
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Could not connect to pigpio")

        """Here we initialize our actuators with correct gpio pins
        and values.
        motor controls 1 ESC with 1 pwm signal
        steering controls 1 servo with 1 pwm signal
        throttle_shifting modifies the used speed (pwm signal) of the motor
        steering_shifting modifies the used turning angle (pwm signal) of the
        servo
        """
        self.motor = PwmActuator(self.pi, MOTOR_PIN, 250)
        self.steering = PwmActuator(self.pi, SERVO_PIN, 400)
        self.throttle_shifting = ShiftGear(self.motor)
        self.steering_shifting = ShiftGear(self.steering)
        """ During the Game initialization callback register your motor
        and steering so the Game Engine knows where to send the user input
        during the games. As we want to use also the shifting functionality
        in the game we must register those inputs to be used from the game
        as well. """
        self.io.register_inputs(
            {
                "motor": self.motor,
                "steering": self.steering,
                "throttle_shifting": self.throttle_shifting,
                "steering_shifting": self.steering_shifting,
            }
        )

    async def on_exit(self, reason, exception):
        await self.io.shutdown_inputs()
        self.pi.stop()


# And now you are ready to play!
if __name__ == "__main__":
    CarGame().run()

# More info about:
# Game: https://docs.surrogate.tv/modules/surrortg.html#module-surrortg.game # noqa: E501
# LinearActuator: https://docs.surrogate.tv/modules/surrortg.inputs.html#surrortg.inputs.linear_actuator.LinearActuator # noqa: E501
# Inputs: https://docs.surrogate.tv/modules/surrortg.inputs.html
# More examples and the full documentation: https://docs.surrogate.tv/game_development.html # noqa: E501
