import time
from enum import Enum, auto
from threading import RLock

import pigpio

from games.arcade_pinball.config import (
    MAX_BLINKING_INTERVAL,
    REQUIRED_BLINKING_TIME,
    REQUIRED_TIME_TO_REGISTER_STATE,
)


class StartLEDStates(Enum):
    ON = auto()
    OFF = auto()
    BLINKING = auto()


class StartLED:
    def __init__(self, io, pi, pin):
        self.io = io
        self.pi = pi
        self.pi.set_mode(pin, pigpio.INPUT)
        self.pi.set_pull_up_down(pin, pigpio.PUD_UP)
        self.pi.set_glitch_filter(pin, 2000)

        self.rlock = RLock()

        # setup pigpio callback for start button led sensor
        self.led_cb = self.pi.callback(
            pin,
            pigpio.EITHER_EDGE,
            self.led_cb_fn,
        )
        now_ts = time.time()
        self.falling_edge_ts = now_ts
        self.rising_edge_ts = now_ts
        self.blinking_start = now_ts
        self.prev_logged_led_status = None

    def led_cb_fn(self, pin, edge, tick):
        with self.rlock:
            now_ts = time.time()

            # reset blinking start if required
            if (
                now_ts - max(self.falling_edge_ts, self.rising_edge_ts)
                > MAX_BLINKING_INTERVAL
            ):
                self.blinking_start = now_ts

            # update the correct timestamp
            if edge == pigpio.FALLING_EDGE:
                self.falling_edge_ts = now_ts
            else:  # edge == pigpio.RISING_EDGE
                self.rising_edge_ts = now_ts

    def get_state(self):
        with self.rlock:
            now_ts = time.time()
            latest_ts = max(self.falling_edge_ts, self.rising_edge_ts)
            oldest_ts = min(self.falling_edge_ts, self.rising_edge_ts)

            # return BLINKING if:
            # 1. has been blinking long enough
            # 2. now_ts would not reset blinking timer
            if (
                now_ts - self.blinking_start > REQUIRED_BLINKING_TIME
                and now_ts - latest_ts <= MAX_BLINKING_INTERVAL
            ):
                if self.prev_logged_led_status != StartLEDStates.BLINKING:
                    self.io.log_admin("Start LED: BLINKING")
                    self.prev_logged_led_status = StartLEDStates.BLINKING
                return StartLEDStates.BLINKING

            # Otherwise return ON/OFF.
            # to filter out random single blinks:
            # do not trust the latest timestamp if has just changed
            # except if was the old one for only a while
            if (
                now_ts - latest_ts < REQUIRED_TIME_TO_REGISTER_STATE
                and latest_ts - oldest_ts > REQUIRED_TIME_TO_REGISTER_STATE
            ):
                trust_latest = False
            else:
                trust_latest = True

            # return ON or OFF based on the correct timestamp
            if (trust_latest and latest_ts == self.falling_edge_ts) or (
                not trust_latest and oldest_ts == self.falling_edge_ts
            ):
                if self.prev_logged_led_status != StartLEDStates.OFF:
                    self.io.log_admin("Start LED: OFF")
                    self.prev_logged_led_status = StartLEDStates.OFF
                return StartLEDStates.OFF
            else:
                if self.prev_logged_led_status != StartLEDStates.ON:
                    self.io.log_admin("Start LED: ON")
                    self.prev_logged_led_status = StartLEDStates.ON
                return StartLEDStates.ON

    async def shutdown(self):
        if self.pi.connected:
            self.led_cb.cancel()
