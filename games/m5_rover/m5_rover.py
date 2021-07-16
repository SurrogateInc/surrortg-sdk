from surrortg.devices.tcp import TcpActuator, TcpCar, TcpCommandId


class M5Rover(TcpCar):
    """Class for TCP-controlled M5 Rover

    :param game_io: The game's GameIO object
    :type game_io: GameIO
    :param throttle_mult: multiplier for throttle value, defaults to 1.0
    :type throttle_mult: float, optional
    :param steering_mult: multiplier for steering value, defaults to 1.0
    :type steering_mult: float, optional
    :param sideways_mult: multiplier for sideways throttle value,
        defaults to 1.0
    :type sideways_mult: float, optional
    """

    def __init__(
        self,
        game_io,
        throttle_mult=1.0,
        steering_mult=1.0,
        sideways_mult=1.0,
    ):
        super().__init__(game_io, throttle_mult, steering_mult)
        self.add_inputs(
            {"sideways": TcpActuator(TcpCommandId.CUSTOM_1, sideways_mult)}
        )
