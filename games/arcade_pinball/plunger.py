import asyncio
import logging
import time

import pigpio

from games.arcade_pinball.arcade_button import ArcadeButton
from games.arcade_pinball.config import (
    AUTO_PLUNGE_TIME,
    BALL_SAVE_PLUNGE_TIME,
    PLUNGER_MIN_FREQ,
    PLUNGER_PRESS_TIME,
    WAIT_FOR_BALL_SAVE,
)
from surrortg.inputs import Switch


class Plunger(Switch):
    def __init__(
        self,
        io,
        pi,
        plunger_pin,
        ball_sensor_pin,
        plunger_press_time=PLUNGER_PRESS_TIME,
    ):
        assert (
            plunger_press_time < PLUNGER_MIN_FREQ
        ), "Simultanious plunger presses possible"
        assert (
            AUTO_PLUNGE_TIME >= BALL_SAVE_PLUNGE_TIME
        ), "Auto plunge can happen before ball save plunge"
        self.io = io
        self.pi = pi

        # setup ball sensor
        self.ball_sensor_pin = ball_sensor_pin
        self.pi.set_mode(self.ball_sensor_pin, pigpio.INPUT)
        self.pi.set_pull_up_down(self.ball_sensor_pin, pigpio.PUD_UP)
        self.pi.set_glitch_filter(self.ball_sensor_pin, 20000)
        self.ball_counter = 0

        # setup plunger
        self.plunger_button = ArcadeButton(
            self.pi,
            plunger_pin,
            "plunger_button",
            button_press_time=plunger_press_time,
        )

        # setup pigpio callback for ball sensor
        self.ball_sensor_cb = self.pi.callback(
            self.ball_sensor_pin,
            pigpio.EITHER_EDGE,
            self.ball_in_lane_callback,
        )

        # setup state
        self.last_plunge_time = time.time() - PLUNGER_MIN_FREQ
        self.plunge_allowed = self.ball_detected()
        self.falling_edge_ts = time.time()

        # get asyncio loop for pigpio callback
        self._loop = asyncio.get_running_loop()
        self._auto_plunge_task = None

        # Shoot the current ball if there is already one.
        # This should start the callback loop which makes sure all of the
        # balls get shot at some point, so the game does not get stuck
        if self.plunge_allowed:
            asyncio.run_coroutine_threadsafe(self.on(), self._loop)

    async def on(self, seat=0):
        # this makes sure, that _plunge() won't get cancelled which could
        # potentially lead into some safety hazards
        if self.pi.connected:
            await asyncio.shield(self._plunge())

    async def _plunge_after(self, delay):
        await asyncio.sleep(delay)
        await self.on()

    async def create_and_exec_auto_plunge_task(self):
        # cancel previous auto plunge task if exists
        self._cancel_auto_plunge_task()
        # create a new auto plunge task
        self._auto_plunge_task = asyncio.create_task(
            self._plunge_after(AUTO_PLUNGE_TIME)
        )
        await self._auto_plunge_task

    # TODO all this logic is somewhat unnecessary if we have
    # a plunging button in the machine. However, it will still work
    # and count balls correctly for us
    async def _plunge(self):
        # make sure that is allowed to plunge timewise
        if time.time() < self.last_plunge_time + PLUNGER_MIN_FREQ:
            self.io.log_admin(
                "Plunger not activated: not enough time has passed",
                also_log=True,
            )
            return

        # make sure that a ball is detected
        if not self.plunge_allowed:
            # Check for a bug if ball sensor edges are configured wrong
            if self.ball_detected():
                self.io.log_admin(
                    "BUG: Ball seems to be in lane, but plunging not allowed",
                    also_log=True,
                )
            else:
                self.io.log_admin(
                    "Plunger not activated: plunging not allowed"
                    ", no ball detected",
                    also_log=True,
                )
            return

        # make sure machine has had time to auto plunge itself
        if time.time() < self.falling_edge_ts + BALL_SAVE_PLUNGE_TIME:
            if WAIT_FOR_BALL_SAVE:
                self.io.log_admin(
                    "Plunger not activated: waiting for ball save plunge",
                    also_log=True,
                )
                return
            else:
                self.io.log_admin(
                    "Potential automatic ball save ignored, plunging",
                    also_log=True,
                )

        # update last_plunge_time and start plunging
        self.last_plunge_time = time.time()
        self.io.log_admin("Plunger activated", also_log=True)
        # Our code plunged the ball -> it is counted ball
        self._cancel_auto_plunge_task()  # cancel if existing auto plunge task
        await self.plunger_button.single_press()
        self.increase_ball_counter()

    def increase_ball_counter(self):
        self.ball_counter += 1
        if WAIT_FOR_BALL_SAVE:
            logging.info(f"Currently on ball {self.ball_counter}")
        else:
            logging.info(
                f"Currently maybe on ball {self.ball_counter} "
                "(WAIT_FOR_BALL_SAVE == False)"
            )

    def reset_ball_counter(self):
        self.ball_counter = 0

    async def off(self, seat=0):
        await self.plunger_button.off()

    def ball_detected(self):
        return self.pi.read(self.ball_sensor_pin) == 0

    async def set_plunge_allowed(self, value):
        self.plunge_allowed = value

    def ball_in_lane_callback(self, pin, edge, tick):
        # Ball entered: call to auto plunge after AUTO_PLUNGE_TIME
        # TODO this is a hardware issue we are having, the
        # edge should be FALLING when ball enters, but for
        # some reason new PCB gives opposite edge, even
        # the sensor reading is correct (low when ball is in)
        if edge == pigpio.RISING_EDGE:
            self.falling_edge_ts = time.time()
            logging.debug("Falling edge, plunging allowed")
            asyncio.run_coroutine_threadsafe(
                self.set_plunge_allowed(True), self._loop
            )
            asyncio.run_coroutine_threadsafe(
                self.create_and_exec_auto_plunge_task(), self._loop
            )
        # Ball exited:
        else:
            logging.debug("Rising edge, plunging not allowed")
            asyncio.run_coroutine_threadsafe(
                self.set_plunge_allowed(False), self._loop
            )

    def _cancel_auto_plunge_task(self):
        if (
            self._auto_plunge_task is not None
            and not self._auto_plunge_task.done()
        ):
            self._auto_plunge_task.cancel()

    async def shutdown(self, seat=0):
        self._cancel_auto_plunge_task()
        if self.pi.connected:
            self.ball_sensor_cb.cancel()
            self.pi.set_pull_up_down(self.ball_sensor_pin, pigpio.PUD_OFF)
            await self.off()


if __name__ == "__main__":
    from games.arcade_pinball.config import BALL_SENSOR_PIN, PLUNGER_PIN

    pi = pigpio.pi()
    if not pi.connected:
        raise RuntimeError("Could not connect to pigpio")

    class IODummy:
        def log_admin(self, message, log_admin=False):
            print(message)

    async def plunge_once():
        print("Plunging once")
        plunger = Plunger(
            IODummy(),
            pi,
            PLUNGER_PIN,
            BALL_SENSOR_PIN,
            plunger_press_time=PLUNGER_PRESS_TIME,
        )
        await plunger.on()
        await plunger.shutdown()

    asyncio.run(plunge_once())
