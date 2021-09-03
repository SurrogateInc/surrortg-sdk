import asyncio
import logging
import os
import time

import adafruit_ssd1306
from PIL import Image, ImageChops, ImageDraw, ImageFont

ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")
FONT_PATH = os.path.join(ASSETS_PATH, "FreeMono.ttf")
LOGO_PATH = os.path.join(ASSETS_PATH, "surrogatetv_logo.png")
LOADING_GIF_PATH = os.path.join(ASSETS_PATH, "loading_balls_2.gif")


class Oled:
    """Class for controlling I2C OLED screen with SSD1306 chip

    :param i2c: I2C connection
    :type i2c: For example busio.I2C or board.i2c
    :param addr: I2C address, defaults to 0x3C
    :type addr: hexadecimal, optional
    :param max_update_interval: Update interval of the screen, defaults to 0.5
    :type max_update_interval: float, optional
    :param width: OLED screen width, defaults to 128
    :type width: int, optional
    :param height: OLED screen height, defaults to 64
    :type height: int, optional
    """

    def __init__(
        self, i2c, addr=0x3C, max_update_interval=0.5, width=128, height=64
    ):
        self._working = False
        self._i2c = i2c
        self._addr = addr
        self._max_update_interval = max_update_interval
        self._width = width
        self._height = height
        self._last_update_ts = time.time()
        self._last_text_written = ""
        self._render_task = None

        # Prevent RuntimeError from asyncio by ignoring max_update_interval
        # if no asyncio loop is running
        if not asyncio.get_event_loop().is_running():
            logging.error(
                "Not running with asyncio! max_update_interval ignored"
            )
            self._max_update_interval = 0

        # Try to init oled display using Adafruit library
        self._safe_init()

        # Show empty display if working
        self.clear()

    def show_text(
        self,
        text,
        x=0,
        y=0,
        invert_colors=False,
        font_size=36,
        fit_to_screen=True,
    ):
        """Show text on the OLED screen

        :param text: Text to show on the screen
        :type text: str
        :param x: x-position of the text on the screen, defaults to 0
        :type x: int, optional
        :param y: y-position of the text on the screen, defaults to 0
        :type y: int, optional
        :param invert_colors: If True, screen colors are inverted,
            defaults to False
        :type invert_colors: bool, optional
        :param font_size: Font size of the text, defaults to 36
        :type font_size: int, optional
        :param fit_to_screen: If True, the text is fitted on the screen,
            defaults to True
        :type fit_to_screen: bool, optional
        """
        assert isinstance(text, str), "text must be a string"
        assert isinstance(x, int) and x in range(
            self._width
        ), "x must be positive and smaller than screen width"
        assert isinstance(y, int) and y in range(
            self._height
        ), "y must be positive and smaller than screen height"
        assert (
            isinstance(font_size, int) and font_size > 0
        ), "font_size must be a positive integer"

        if text is self._last_text_written:
            logging.info(
                f"'{text}' already written to OLED, not writing again"
            )
        else:
            # Try to re-init if broken
            if not self._working:
                self._safe_init()

            # Try showing only if in a working state
            if self._working:
                wait_time = self._wait_time_before_render()
                # Try showing now only if enough time has passed
                if wait_time < 0:
                    self._render_text(
                        text, x, y, invert_colors, font_size, fit_to_screen
                    )
                # If not, create a task to write later
                else:
                    self._cancel_ongoing_render_tasks()
                    self._render_task = asyncio.create_task(
                        self._render_text_after_wait(
                            text,
                            x,
                            y,
                            invert_colors,
                            font_size,
                            fit_to_screen,
                            wait_time,
                        )
                    )

    def show_image(self, image, invert_colors=False):
        """Show image or animation on the OLED screen

        The image is resized to the size of the screen and images with
        different aspect ratio than the screen will be stretched to fill
        the entire screen.

        :param image: Image object or a file path of an image or animation
        :type image: Image or str
        :param invert_colors: If True, image colors are inverted,
            defaults to False
        :type invert_colors: bool, optional
        """
        assert isinstance(
            image, (str, Image)
        ), "image must be a string or an Image"

        # Try to re-init if broken
        if not self._working:
            self._safe_init()

        # Try showing only if in a working state
        if self._working:
            wait_time = self._wait_time_before_render()
            # Try showing now only if enough time has passed
            if wait_time < 0:
                self._render_image(image, invert_colors)
            # If not, create a task to write later
            else:
                self._cancel_ongoing_render_tasks()
                self._render_task = asyncio.create_task(
                    self._render_image_after_wait(
                        image, invert_colors, wait_time
                    )
                )

    def clear(self, invert_colors=False):
        """Clears the OLED screen

        :param invert_colors: If True, screen colors are inverted,
            defaults to False
        :type invert_colors: bool, optional
        """
        if self._working:
            fill = 255 if invert_colors else 0
            self._oled.fill(fill)
            self._safe_show()
            self._last_text_written = ""

    def _cancel_ongoing_render_tasks(self):
        if self._render_task is not None and not self._render_task.done():
            self._render_task.cancel()

    def _wait_time_before_render(self):
        return self._max_update_interval - (time.time() - self._last_update_ts)

    def _render_text(
        self, text, x, y, invert_colors, font_size, fit_to_screen
    ):
        if fit_to_screen:
            text_processed, actual_font_size = self._fit_text(
                text, x, y, font_size
            )
        else:
            text_processed = text
            actual_font_size = font_size

        # External font is used so that font size can be changed
        font = ImageFont.truetype(FONT_PATH, actual_font_size)
        image = Image.new("1", (self._width, self._height))
        draw = ImageDraw.Draw(image)
        draw.text((x, y), text_processed, font=font, fill=255)

        if invert_colors:
            image = ImageChops.invert(image)

        self._oled.image(image)
        self._safe_show()
        self._last_text_written = text
        self._last_update_ts = time.time()

    async def _render_text_after_wait(
        self, text, x, y, invert_colors, font_size, fit_to_screen, wait_time
    ):
        await asyncio.sleep(wait_time)
        self._render_text(text, x, y, invert_colors, font_size, fit_to_screen)

    def _render_image(self, image, invert_colors):
        assert isinstance(
            image, (str, Image)
        ), "image must be a string or an Image"

        if isinstance(image, str):
            try:
                image_in = Image.open(image)
            except FileNotFoundError:
                logging.error(f"File '{image}' not found!")
                return
        elif isinstance(image, Image):
            image_in = image

        # Show image frame by frame
        # All Image objects have at least a single frame
        for i in range(image_in.n_frames):
            image_in.seek(i)

            # Resize and convert image to 1-bit
            im = image_in.resize(
                (self._width, self._height), Image.BICUBIC
            ).convert("1")

            if invert_colors:
                im = ImageChops.invert(im)

            # Display the image
            self._oled.image(im)
            self._safe_show()

    async def _render_image_after_wait(self, image, invert_colors, wait_time):
        await asyncio.sleep(wait_time)
        self._render_image(image, invert_colors)

    def _fit_text(self, text, x, y, font_size):
        font = ImageFont.truetype(FONT_PATH, font_size)
        image = Image.new("1", (self._width, self._height))
        draw = ImageDraw.Draw(image)
        min_font_size = 20
        too_small_font_size = font_size <= min_font_size

        input_rows = text.split("\n")
        output_rows = []
        temp_words = []

        for row in input_rows:
            words = row.split()

            while len(words) > 0:
                temp_words += [words[0]]
                temp_row = " ".join(temp_words)
                _, _, width, _ = draw.textbbox((x, y), temp_row, font=font)
                if width < self._width:
                    del words[0]
                    continue

                if len(temp_words) < 2:
                    if too_small_font_size:
                        logging.warning(
                            f"Could not fit word '{temp_words[0]}' to OLED "
                            f"on row {len(output_rows) + 1}"
                        )
                        del words[0]
                        output_rows += [temp_row]
                        temp_words = []
                    else:
                        return self._fit_text(text, x, y, font_size - 4)
                else:
                    output_rows += [" ".join(temp_words[:-1])]
                    temp_words = []

        if len(temp_words) > 0:
            output_rows += [" ".join(temp_words)]

        output = "\n".join(output_rows)
        _, _, width, height = draw.textbbox((x, y), output, font=font)

        # Try again with smaller font size if text does not fit
        if height > self._height:
            if too_small_font_size:
                logging.warning("Could not fit text to screen")
                return (output, font_size)
            return self._fit_text(text, x, y, font_size - 4)

        return (output, font_size)

    def _safe_init(self):
        try:
            self._oled = adafruit_ssd1306.SSD1306_I2C(
                self._width, self._height, self._i2c, addr=self._addr
            )
            self._working = True
        except (OSError, ValueError):
            logging.error(f"Oled init failed at address {hex(self._addr)}")
            self._working = False

    def _safe_show(self):
        try:
            self._oled.show()
            self._working = True
        except OSError:
            logging.error(f"Oled show() failed at address {hex(self._addr)}")
            self._working = False


if __name__ == "__main__":
    import board

    logging.basicConfig(level=logging.INFO)
    i2c = board.I2C()
    oled = Oled(i2c)

    oled.show_text("ERROR")
    time.sleep(2)
    oled.show_text("a nice text", x=40, y=10)
    time.sleep(2)
    oled.show_text("VERYLONGWORD THAT MIGHT NOT FIT")
    time.sleep(2)
    oled.show_text(
        "NO WRAP HERE", invert_colors=True, font_size=18, fit_to_screen=False
    )
    time.sleep(2)
    oled.show_image(LOGO_PATH)
    time.sleep(2)
    oled.show_image(LOADING_GIF_PATH, invert_colors=True)
    oled.clear()
    time.sleep(0.5)
    oled.clear(invert_colors=True)
    time.sleep(1)
    oled.show_text("exiting", y=15)
    time.sleep(1)
    oled.clear()
