import logging
from collections import deque
from time import time


class SpamFilter:
    """Class for adding a spam filter for any input

    Only allows a certain number of inputs commands to pass through,
    during the specified rolling time window.
    :param max_inputs: maximum number of inputs allowed
    :type max_inputs: int
    :param per_seconds: time window length
    :type per_seconds: float
    """

    def __init__(self, max_inputs, per_seconds):
        self.max_inputs = max_inputs
        self.per_seconds = per_seconds
        self.input_timestamps = deque()

    def too_much_spam(self):
        """Check if input has received too many commands

        :return: 'True' if input has received too many commands
        :rtype: bool
        """
        # append the current timestamp
        self.input_timestamps.append(time())
        # check has there been enough inputs
        if len(self.input_timestamps) >= self.max_inputs:
            oldest = self.input_timestamps.popleft()
            # check if inputs have happened too fast
            seconds = time() - oldest
            if seconds < self.per_seconds:
                logging.debug(
                    f"{self.max_inputs} in {round(seconds, 2)} "
                    "seconds\t\tTOO MUCH"
                )
                return True
            else:
                logging.debug(
                    f"{self.max_inputs} in {round(seconds, 2)} seconds"
                )
        else:
            logging.debug(f"Not enough inputs: {len(self.input_timestamps)}")
        return False


if __name__ == "__main__":
    import sys

    from pynput import keyboard

    if len(sys.argv) != 3:
        print("Usage: spam_filter.py <max_inputs> <per_seconds>")
        print("\nUse both CTRL keys, exit with Esc")
        sys.exit(0)

    logging.getLogger().setLevel(logging.DEBUG)

    # track right and left ctrl keys
    keys = [keyboard.Key.ctrl, keyboard.Key.ctrl_r]
    spam_filter = SpamFilter(int(sys.argv[1]), float(sys.argv[2]))

    def on_press(key):
        if key == keyboard.Key.esc:
            return False
        if key in keys:
            spam_filter.too_much_spam()

    try:
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
    except KeyboardInterrupt:
        pass
    print("\n")
