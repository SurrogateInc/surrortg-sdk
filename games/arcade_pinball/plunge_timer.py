import time
from threading import RLock

import pigpio

from games.arcade_pinball.config import (
    BALL_SENSOR_PIN,
    PLUNGER_PIN,
    PLUNGER_PRESS_TIME,
)

MAX_ALLOWED_PLUNGE_TIME = 2 * PLUNGER_PRESS_TIME

if __name__ == "__main__":
    # setup initial end, define callback function
    end = None
    end_lock = RLock()  # should be redundant, but let's be sure about that

    def end_timer(*args):
        with end_lock:
            global end
            if end is None:  # update end only once
                end = time.time()
                pi.write(PLUNGER_PIN, 0)

    # connect pigpio
    pi = pigpio.pi()
    if not pi.connected:
        raise RuntimeError("Could not connect to pigpio")

    # setup ball sensor callback
    pi.set_mode(BALL_SENSOR_PIN, pigpio.INPUT)
    pi.set_pull_up_down(BALL_SENSOR_PIN, pigpio.PUD_UP)
    cb = pi.callback(BALL_SENSOR_PIN, pigpio.RISING_EDGE, end_timer)

    # plunge and start timer
    pi.set_mode(PLUNGER_PIN, pigpio.OUTPUT)
    pi.write(PLUNGER_PIN, 1)
    start = time.time()

    # wait for the callback to work
    time.sleep(MAX_ALLOWED_PLUNGE_TIME)

    # stop callback
    cb.cancel()
    pi.set_pull_up_down(BALL_SENSOR_PIN, pigpio.PUD_OFF)

    # stop the plunger if not already stopped
    pi.write(PLUNGER_PIN, 0)

    # release pigpio
    pi.stop()

    # print the result
    with end_lock:
        if end is not None:
            print(f"Plunge time: {end - start} seconds")
        else:
            print("Could not measure, maybe increase MAX_ALLOWED_PLUNGE_TIME")
