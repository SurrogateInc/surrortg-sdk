import asyncio
import logging
from functools import partial
from math import sqrt

from PIL import Image
from rpi_ws281x import Color, PixelStrip

from surrortg.game_io import ConfigType

# LED strip configuration:
LED_COUNT = 1024  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10 # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 10  # Set to 0 for darkest and 255 for brightest
LED_INVERT = (
    False  # True to invert the signal (when using NPN transistor level shift)
)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

OUT_OF_TIME_BLINK_SECONDS = 3
OUT_OF_TIME_BLINK_INTERVAL = 0.2

GAME_AREA_SIZE_KEY = "Game area side length (number of squares)"
BLINK_TIME_KEY = "Time left to start blinking"
BLINK_INTERVAL_KEY = "Blinking interval (in seconds)"
CUSTOM_KEY = "custom"
BG_COLOR_R_KEY = "Background color red value"
BG_COLOR_G_KEY = "Background color blue value"
BG_COLOR_B_KEY = "Background color green value"
LED_BRIGHTNESS_KEY = "Led brightness"

BACKGROUND_COLOR = Color(135, 21, 158)

# TODO: use relative path
IMAGE_DIR_PATH = "/home/pi/surrortg-sdk/surrortg/devices/led_matrix/images/"


class LedMatrix:
    """Class for controlling an LED strip that forms a matrix.

    So far only tested with a 32x32, 1024 LED strip/matrix. Should work for
    other sizes as well with some customization.

    Provides methods for setting pixel color, as well as a method for

    Provides configuration parameters to the web interface.

    Short example of how to integrate the class into game logic:

    .. code-block:: python

        from surrortg.image_recognition.aruco import ArucoFinder

        YourGame(Game):
        async def on_init(self):
            self.led_matrix = LedMatrix(self.io, DEF_GAME_AREA_SIZE)

        async def on_config(self):
            self.led_matrix.handle_config(self.configs)

        async def on_countdown(self):
            await self.led_matrix.countdown()

        async def on_start(self):
            self.finder.on_start()

        async def end_game(self):
            self.led_matrix.end_game()

        async def on_exit(self, reason, exception):
            self.led_matrix.on_exit()

        def _set_new_area(self):
            self.cur_area_idx = self._next_area_idx()
            self.led_matrix.set_timed_area(self.cur_area_idx, self.time)


    :param io: GameIO instance, used to register configs
    :type io: GameIO
    :param size: number of squares per side. Only tested with size=4
    :type size: int, optional
    """

    def __init__(self, io, size=4, led_count=LED_COUNT):
        self.io = io
        self.io.register_config(
            BLINK_TIME_KEY, ConfigType.INTEGER, 3, False, minimum=1, maximum=10
        )
        self.io.register_config(
            BLINK_INTERVAL_KEY,
            ConfigType.NUMBER,
            0.3,
            False,
            minimum=0.05,
            maximum=3,
        )
        self.io.register_config(
            BG_COLOR_R_KEY,
            ConfigType.INTEGER,
            0,
            False,
            minimum=0,
            maximum=255,
        )
        self.io.register_config(
            BG_COLOR_G_KEY,
            ConfigType.INTEGER,
            0,
            False,
            minimum=0,
            maximum=255,
        )
        self.io.register_config(
            BG_COLOR_B_KEY,
            ConfigType.INTEGER,
            0,
            False,
            minimum=0,
            maximum=255,
        )
        self.io.register_config(
            LED_BRIGHTNESS_KEY,
            ConfigType.INTEGER,
            20,
            False,
            minimum=0,
            maximum=255,
        )

        self.strip = PixelStrip(
            led_count,
            LED_PIN,
            LED_FREQ_HZ,
            LED_DMA,
            LED_INVERT,
            LED_BRIGHTNESS,
            LED_CHANNEL,
        )
        self.bg_color = BACKGROUND_COLOR

        self.strip.begin()

        self.color_timer = None
        self.area_dim = size
        if self.strip.numPixels() == 1024:
            self.img_one = self.read_image_file(IMAGE_DIR_PATH + "32/1.jpg")
            self.img_two = self.read_image_file(IMAGE_DIR_PATH + "32/2.jpg")
            self.img_three = self.read_image_file(IMAGE_DIR_PATH + "32/3.jpg")

    class TimedColorChange:
        """Calls color changes at regular intervals for given duration.
        Color sequence is green, yellow, red. The area will start blinking
        when time left equals begin_blinking. The color of the area is set
        to background color at the end of the sequence or when cancelled.

        :param callback: callback which will set the color of the square
        :type callback: function that takes color=Color() as its only
            parameter
        :param timeout: duration of the complete color sequence
        :type timeout: number
        :param begin_blinking: amount of time left when starting to blink
        :type begin_blinking: number
        :param blink_interval: frequency of blinking
        :type blink_interval: number
        :param bg_color: color the area will be set to at the end
        :type bg_color: Color()
        """

        def __init__(
            self,
            callback,
            timeout,
            begin_blinking=3,
            blink_interval=0.3,
            bg_color=BACKGROUND_COLOR,
        ):
            self.callback = callback
            self.begin_blinking = begin_blinking
            self.blink_interval = blink_interval
            self.time_interval = (timeout - self.begin_blinking) / 3
            self.callback(color=Color(0, 255, 0))
            self.task = asyncio.create_task(self._job())
            self.bg_color = bg_color

        def cancel(self):
            """Cancel the timer, setting the area to bg_color"""
            if self.task is not None:
                self.task.cancel()
                self.callback(color=self.bg_color)
                self.task = None

        async def _job(self):
            await asyncio.sleep(self.time_interval)
            self.callback(color=Color(255, 255, 0))
            await asyncio.sleep(self.time_interval)
            self.callback(color=Color(255, 0, 0))
            await asyncio.sleep(self.time_interval)
            while True:
                self.callback(color=self.bg_color)
                await asyncio.sleep(self.blink_interval)
                self.callback(color=Color(255, 0, 0))
                await asyncio.sleep(self.blink_interval)

    def solid_color(self, strip, color, pixels):
        """Set all LEDs in the pixels-argument to the same color

        :param strip: LED strip object
        :type strip: PixelStrip
        :param color: color which will be set for all given LEDs
        :type color: Color()
        :param pixels: pixel indices and their colors
        :type pixels: list of int
        """
        for i in pixels:
            strip.setPixelColor(i, color)
        strip.show()

    def draw_pixels(self, strip, pixels):
        """Set color for LEDs at indices given in the pixels-parameter

        :param strip: LED strip object
        :type strip: PixelStrip
        :param pixels: pixel indices and their colors
        :type pixels: list of (int, (int, int, int)) tuples
        """
        for pixel in pixels:
            strip.setPixelColor(
                pixel[0], Color(pixel[1][0], pixel[1][1], pixel[1][2])
            )
        strip.show()

    def map_pixel_to_led_idx(self, x, y):
        """Maps pixel coordinates to LED index on the LED strip

        :param x: x coordinate of the pixel
        :type x: Int
        :param y: x coordinate of the pixel
        :type y: Int

        :return: index of led
        :rtype: int
        """
        sq_row = y // 8
        sq_col = x // 8
        sq_idx = sq_row * 4 + sq_col
        row = y % 8
        col = x % 8
        led_idx = 0
        if sq_row % 2 != 0:
            if col % 2 != 0:
                row = 7 - row
            led_idx = ((sq_row * 4 + 3 - sq_col) * 64) + (7 - col) * 8 + row
        else:
            if col % 2 != 0:
                row = 7 - row
            led_idx = sq_idx * 64 + col * 8 + row
        return led_idx

    def read_rgb_file(self, filename):
        lines = []
        pixels = []
        with open(filename, "r") as file:
            lines = file.readlines()
        for line in lines:
            y = int(line.split(",")[0])
            x = int(line.split(",")[1])
            r = int(line.split(",")[2].split("   ")[0].split("[")[1])
            g = int(line.split(",")[2].split("   ")[1])
            b = int(line.split(",")[2].split("   ")[2].split("]")[0])
            pixel = self.map_pixel_to_led_idx(x, y)
            pixels.append((pixel, (r, g, b)))
        return pixels

    # TODO: use opencv for reading images
    def read_image_file(self, filename):
        pixels = []
        with Image.open(filename) as img:
            img = img.convert("RGB")
            pixels = img.load()
            width, height = img.size
            pixels = [
                (self.map_pixel_to_led_idx(x, y), pixels[x, y])
                for x in range(width)
                for y in range(height)
            ]
        return pixels

    def set_empty_pixels_to_bg(self, pixels, bg_color):
        for i, pixel in enumerate(pixels):
            if pixel[1][0] < 30 and pixel[1][1] < 30 and pixel[1][2] < 30:
                pixels[i] = (pixel[0], bg_color)

    def increase_image_saturation(self, pixels):
        for i, pixel in enumerate(pixels):
            new_color = list(pixel[1])
            for c in range(3):
                if new_color[c] > 180:
                    new_color[c] = 255
            pixels[i] = (pixel[0], tuple(new_color))

    def increase_contrast(self, pixels, bg_color):
        self.set_empty_pixels_to_bg(pixels, bg_color)
        self.increase_image_saturation(pixels)

    def set_size(self, size):
        self.area_dim = size
        self.num_squares = self.area_dim ** 2

    def reset_leds(self):
        """Calling this resets all LEDs to background color"""
        self.solid_color(
            self.strip,
            self.bg_color,
            [i for i in range(self.strip.numPixels())],
        )

    async def countdown(self):
        logging.info(f"on_countdown {self.strip.numPixels()}")
        if self.strip.numPixels() != 1024:
            return
        await asyncio.sleep(3.85)
        logging.info("drawing 3")
        self.draw_pixels(self.strip, self.img_three)
        await asyncio.sleep(0.85)
        logging.info("drawing 2")
        self.reset_leds()
        self.draw_pixels(self.strip, self.img_two)
        await asyncio.sleep(0.85)
        self.reset_leds()
        logging.info("drawing 1")
        self.draw_pixels(self.strip, self.img_one)
        await asyncio.sleep(0.85)
        self.reset_leds()

    def end_game(self):
        """Resets all LEDs to background color and stops color timer"""
        self.color_timer.cancel()
        self.reset_leds()

    def handle_config(self, configs):
        """Method for handling configs from the web config interface.

        The LEDs get reset to the background color during this method call.

        :param configs: self.configs from the Game object which owns this
            instance
        :type configs: dict
        """
        self.configs = configs
        self.blink_time = self.configs[CUSTOM_KEY][BLINK_TIME_KEY]
        self.blink_interval = self.configs[CUSTOM_KEY][BLINK_INTERVAL_KEY]
        self.pixel_map = self._generate_pixel_map(
            self.num_squares, self.strip.numPixels()
        )
        self.strip.setBrightness(self.configs[CUSTOM_KEY][LED_BRIGHTNESS_KEY])
        bg_red = self.configs[CUSTOM_KEY][BG_COLOR_R_KEY]
        bg_blue = self.configs[CUSTOM_KEY][BG_COLOR_G_KEY]
        bg_green = self.configs[CUSTOM_KEY][BG_COLOR_B_KEY]
        self.bg_color = Color(bg_red, bg_green, bg_blue)
        if self.strip.numPixels() == 1024:
            self.increase_contrast(self.img_one, (bg_red, bg_green, bg_blue))
            self.increase_contrast(self.img_two, (bg_red, bg_green, bg_blue))
            self.increase_contrast(self.img_three, (bg_red, bg_green, bg_blue))
        self.reset_leds()

    def _generate_pixel_map(self, num_squares, pixel_count):
        pixel_map = []
        pixels_per_square = pixel_count / num_squares
        matrix_dim = sqrt(num_squares)
        if matrix_dim % 1 != 0:
            raise ValueError(
                "Number of squares for LED matrix must match an even-sided"
                "rectangle (i.e. 16->4x4"
            )
        if pixels_per_square % 1 != 0:
            logging.warning(
                "LED count and number of LED squares do not match evenly! "
                "Some LEDs may not light up."
            )
            pixels_per_square = pixel_count // num_squares
        for square in range(num_squares):
            pixels = []
            row_idx = square // matrix_dim
            # Invert odd rows because the LED matrices are connected in a
            # "snake" pattern instead of just rows
            if row_idx % 2 != 0:
                square = (
                    (row_idx + 1) * matrix_dim
                    - 1
                    - (square - row_idx * matrix_dim)
                )
            pixels = [
                p
                for p in range(
                    int(square * pixels_per_square),
                    int((square + 1) * pixels_per_square),
                )
            ]
            pixel_map.append(pixels)
        return pixel_map

    def set_timed_area(self, idx, timeout):
        """Make a square at given index change colors and finally blink

        The square will go from green, to yellow, to red, and finally blink
        for blink_time (set in web interface) before resetting to background
        color.

        :param idx: index of the square
        :type idx: int
        :param timeout: total duration of the timer. Time will be evenly
            divided between green, yellow, and red colors.
        :type timeout: number
        """
        if self.color_timer is not None:
            self.color_timer.cancel()
        self.color_timer = self.TimedColorChange(
            partial(
                self.solid_color, strip=self.strip, pixels=self.pixel_map[idx]
            ),
            timeout,
            self.blink_time,
            self.blink_interval,
            self.bg_color,
        )

    def on_exit(self):
        """Call this before exiting program to turn off all LEDs"""
        self.solid_color(self.strip, Color(0, 0, 0), self.strip.numPixels())
        if self.color_timer is not None:
            self.color_timer.cancel()
