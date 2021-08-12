import logging

from adafruit_tcs34725 import TCS34725


class SafeTCS34725:
    """'Safe' wrapper class for adafruit_tcs34725.TCS34725

    Original docs, that applies to this wrapper also:
    https://github.com/adafruit/Adafruit_CircuitPython_TCS34725

    This class does not raise errors, if initializing or
    setting/getting attributes fails due to loss of power or loss of I2C
    connection to the sensor. Instead, all errors will be logged with
    logging.error.

    If the sensor is in a broken state, it attempts to fix itself and restore
    the latest settings every time some attribute has been requested.

    Getting attribute returns 'None' if an error was raised.

    Note: due to implementation details, if the same attribute has been set
    multiple times for the sensor, restoring might fail due to sensor firmware
    logic.

    Extra properties and methods:
    - 'working' will tell what was the sensor in working state the last time
    - 'fix()'  will attempt fixing the sensor if broken and returns the result

    :param i2c: I2C connection
    :type i2c: for example busio.I2C or board.i2c
    :param address: I2C address, defaults to 0x29
    :type address: hexadecimal, optional
    """

    def __init__(self, i2c, address=0x29):
        self._internal_attributes = {
            "_working",
            "_i2c",
            "_address",
            "_attributes_set_order",
            "_state",
            "_tcs34725",
        }
        self._working = False
        self._i2c = i2c
        self._address = address
        self._attributes_set_order = []
        self._state = dict()
        self._tcs34725 = None
        self._safe_init()

    @property
    def working(self):
        """Get the latest known state of the sensor

        Note: this does not attempt to fix the sensor if broken,
        check fix() for that

        :return: Whether the sensor worked last time or not
        :rtype: bool
        """
        return self._working

    def fix(self):
        """Attempt fixing the sensor if broken

        Return the current sensor working state

        :return: Whether the sensor is in working state or not
        :rtype: bool
        """
        if not self._working:
            self._safe_init()

        return self._working

    def _safe_init(self):
        try:
            # Init adafruit_tcs34725
            self._tcs34725 = TCS34725(self._i2c, self._address)
            # Restore old state
            for attr in self._attributes_set_order:
                logging.info(
                    f"restoring: TCS34725.{attr} = {self._state[attr]}"
                )
                setattr(self._tcs34725, attr, self._state[attr])
            self._working = True
        except (OSError, ValueError) as e:
            logging.error(f"TCS34725.__init__() failed: {e}")
            self._working = False

    def __getattr__(self, name):
        # Check if internal use case
        if name == "_internal_attributes" or name in self._internal_attributes:
            # Default behaviour
            return self.__getattribute__(name)

        # Try re-init if broken
        self.fix()

        # Try getting only if in a working state
        if self._working:
            try:
                return getattr(self._tcs34725, name)
            except OSError as e:
                logging.error(f"Getting TCS34725.{name} failed: {e}")
                self._working = False

    def __setattr__(self, name, value):
        # Check if internal use case
        if name == "_internal_attributes" or name in self._internal_attributes:
            # Default behaviour
            return super().__setattr__(name, value)

        # Save value into state
        # NOTE: we now assume the user sets the values only in a proper order,
        # and each attribute is in the order only once
        if name not in self._attributes_set_order:
            self._attributes_set_order.append(name)
        self._state[name] = value

        # Try re-init if broken
        self.fix()

        # Try setting only if in a working state
        if self._working:
            try:
                setattr(self._tcs34725, name, value)
            except OSError as e:
                logging.error(f"Setting TCS34725.{name} failed: {e}")
                self._working = False


if __name__ == "__main__":
    import time

    import busio
    from board import SCL, SDA

    logging.basicConfig(level=logging.INFO)
    i2c = busio.I2C(SCL, SDA)
    color_sensor = SafeTCS34725(i2c)
    color_sensor.integration_time = 24
    color_sensor.interrupt = False
    color_sensor.gain = 60
    while True:
        print(f"lux: {color_sensor.lux}\t\t(working: {color_sensor.working})")
        time.sleep(0.5)
