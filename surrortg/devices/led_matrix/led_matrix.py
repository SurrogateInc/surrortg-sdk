import asyncio
import logging
import os
import time
from functools import partial
from math import sqrt

from PIL import Image
from rpi_ws281x import Color, PixelStrip

from surrortg.game_io import ConfigType

# LED strip configuration:
LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10 # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 10  # Set to 0 for darkest and 255 for brightest
LED_INVERT = (
    False  # True to invert the signal (when using NPN transistor level shift)
)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53

BEGIN_BLINKING_TIME_LEFT = 3
BLINK_INTERVAL = 0.3

GAME_AREA_SIZE_KEY = "Game area side length (number of squares)"
BLINK_TIME_KEY = "Time left to start blinking"
BLINK_INTERVAL_KEY = "Blinking interval (in seconds)"
CUSTOM_KEY = "custom"
BG_COLOR_R_KEY = "Background color red value"
BG_COLOR_G_KEY = "Background color blue value"
BG_COLOR_B_KEY = "Background color green value"
LED_BRIGHTNESS_KEY = "Led brightness"

BACKGROUND_RGB = (65, 10, 79)
BACKGROUND_COLOR = Color(*BACKGROUND_RGB)

SUPPORTED_IMG_TYPES = (".jpg", ".jpeg", ".png")


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
    :param size: number of squares per side. Only tested with default size: 4.
    :type size: int, optional
    :param led_count: total number of LEDs in the strip/matrix. Defaults to
        1024. Must match the size of the physical LED matrix.
    :type led_count: int, optional
    """

    def __init__(
        self,
        io=None,
        size=1,
        led_count=64,
        brightness=LED_BRIGHTNESS,
        enabled=True,
    ):
        self.io = io
        if self.io is not None:
            self.io.register_config(
                BLINK_TIME_KEY,
                ConfigType.INTEGER,
                3,
                False,
                minimum=1,
                maximum=10,
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

        self.brightness = brightness
        self.enabled = enabled
        self.led_count = led_count

        self.strip = PixelStrip(
            self.led_count,
            LED_PIN,
            LED_FREQ_HZ,
            LED_DMA,
            LED_INVERT,
            self.brightness,
            LED_CHANNEL,
        )
        self.bg_color = BACKGROUND_COLOR
        self.bg_rgb = BACKGROUND_RGB

        self.color_timer = None
        self.area_dim = size
        self.num_squares = self.area_dim ** 2
        self.pixel_map = self._generate_pixel_map(
            self.num_squares, self.led_count
        )
        self.blink_time = 3
        self.blink_interval = 0.3
        self.images = {}
        self.image_dim = int(sqrt(led_count))
        image_dir = "images/" + str(self.image_dim)
        self.image_dir = os.path.join(os.path.dirname(__file__), image_dir)
        self.images = self._generate_image_map()
        if self.enabled:
            self.begin()

    def begin(self):
        self.strip.begin()
        self.reset_leds()

    def _generate_image_map(self):
        img_map = {}
        for filename in os.listdir(self.image_dir):
            if self.is_supported_image(filename):
                full_path = self.image_dir + "/" + filename
                key = filename.split(".", 1)[0]
                img = self.read_image_file(full_path)
                logging.info(
                    f"adding img to dict: {filename}, key in map: {key},"
                    f" full path: {full_path}"
                )
                img_map[key] = img
        return img_map

    async def image_gallery(self, duration=5):
        """Show all images found in images dict in infinite loop"""
        if not self.enabled:
            logging.warning("led matrix disabled")
            return
        while True:
            for img in self.images:
                self.show_image(img)
                await asyncio.sleep(duration)

    def show_image(self, image_name, fill_bg=False):
        if not self.enabled:
            logging.warning("led matrix disabled, not showing image")
            return
        if image_name not in self.images:
            if os.path.isfile(image_name) and self.is_supported_image(
                image_name
            ):
                logging.info(f"adding image {image_name} to led matrix images")
                self.images[image_name] = self.read_image_file(image_name)
            else:
                logging.warning(
                    f"led matrix image {image_name} not found or not supported"
                )
                return
        logging.info(f"showing image {image_name}")
        self.draw_pixels(self.images[image_name], fill_bg)

    def is_supported_image(self, filename):
        return filename.endswith(SUPPORTED_IMG_TYPES)

    def enable(self):
        logging.info("enabling led matrix")
        was_enabled = self.enabled
        self.enabled = True
        if not was_enabled:
            self.begin()

    def disable(self):
        logging.info("disabling led matrix")
        if self.enabled:
            if self.color_timer is not None:
                self.color_timer.cancel()
            self.turn_off_leds()
        self.enabled = False

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
        :param begin_blinking: amount of time left when starting to blink,
            defaults to 3 seconds
        :type begin_blinking: number, optional
        :param blink_interval: frequency of blinking, defaults to 0.3 seconds
        :type blink_interval: number, optional
        :param bg_color: color the area will be set to at the end
        :type bg_color: Color(), optional
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
            began_blinking = time.time()
            while time.time() - began_blinking < self.begin_blinking:
                self.callback(color=Color(255, 0, 0))
                await asyncio.sleep(self.blink_interval)
                self.callback(color=self.bg_color)
                await asyncio.sleep(self.blink_interval)

    def solid_color(self, color, pixels):
        """Set all LEDs in the pixels-argument to the same color

        :param color: color which will be set for all given LEDs
        :type color: Color()
        :param pixels: pixel indices
        :type pixels: list of int
        """
        if not self.enabled:
            logging.warning("led matrix disabled")
            return
        for i in pixels:
            self.strip.setPixelColor(i, color)
        self.strip.show()

    def set_all_leds_to_color(self, color):
        if not self.enabled:
            logging.warning("led matrix disabled")
            return
        self.solid_color(color, [i for i in range(self.led_count)])

    def set_all_leds_to_rgb(self, rgb):
        if not self.enabled:
            logging.warning("led matrix disabled")
            return
        self.solid_color(Color(*rgb), [i for i in range(self.led_count)])

    def draw_pixels(self, pixels, fill_bg=False):
        """Set color for LEDs at indices given in the pixels-parameter

        :param pixels: pixel indices and their colors
        :type pixels: list of (int, (int, int, int)) tuples
        :param fill_bg: fill empty (all color values < 30) pixels with
            background color
        :type fill_bg: bool, optional
        """
        if not self.enabled:
            logging.warning("led matrix disabled")
            return
        if fill_bg:
            self.set_empty_pixels_to_bg(pixels, self.bg_rgb)
        for pixel in pixels:
            self.strip.setPixelColor(
                pixel[0], Color(pixel[1][0], pixel[1][1], pixel[1][2])
            )
        self.strip.show()

    async def test_pixels(self):
        for i in range(self.led_count):
            self.strip.setPixelColor(i, Color(255, 0, 0))
            self.strip.show()
            await asyncio.sleep(0.1)
            self.turn_off_leds()

    async def test_pixel_mapping(self):
        dim = int(sqrt(self.led_count))
        for y in range(dim):
            for x in range(dim):
                pixel = self.map_pixel_to_led_small_no_snake(x, y)
                logging.info(f"mapped coord {x, y} to pixel {pixel}")
                self.strip.setPixelColor(pixel, Color(255, 0, 0))
                self.strip.show()
                await asyncio.sleep(0.1)
                self.turn_off_leds()

    def map_pixel_to_led_idx(self, x, y):
        """Maps pixel coordinates to LED index on the LED strip

        :param x: x coordinate of the pixel
        :type x: Int
        :param y: x coordinate of the pixel
        :type y: Int

        :return: index of led
        :rtype: int
        """
        if self.led_count == 64:
            return self.map_pixel_to_led_small_no_snake(x, y)
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

    def map_pixel_to_led_small_no_snake(self, x, y):
        return x + 8 * (y % 8)

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

    def read_image_file(self, filename):
        pixels = []
        with Image.open(filename) as img:
            logging.info(f"reading img file into pixels: {filename}")
            img = img.convert("RGB")
            dim = int(sqrt(self.led_count))
            if img.size[0] > dim + 1 or img.size[1] > dim + 1:
                logging.info(
                    f"image {filename} doesn't fit into LED matrix."
                    f" Image size:{img.size[0]}, {img.size[1]}; matrix size:"
                    f" {dim}, {dim}. Resizing.."
                )
                img = img.resize((dim, dim), Image.NEAREST)
            pixels = img.load()
            width, height = img.size
            pixels = [
                (self.map_pixel_to_led_idx(x, y), pixels[x, y])
                for x in range(width)
                for y in range(height)
            ]
        return pixels

    def dampen_colors(self, rgb):
        new_rgb = list(rgb)
        highest_val = max(new_rgb)
        max_val = 80
        mult = 1
        if highest_val > max_val:
            mult = max_val / highest_val

        new_rgb[0] = int(new_rgb[0] * mult)
        new_rgb[1] = int(new_rgb[1] * mult)
        new_rgb[2] = int(new_rgb[2] * mult)

        return tuple(new_rgb)

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
        if not self.enabled:
            logging.warning("led matrix disabled")
            return
        """Calling this resets all LEDs to background color"""
        self.solid_color(
            self.bg_color,
            [i for i in range(self.led_count)],
        )

    def turn_off_leds(self):
        if not self.enabled:
            logging.warning("led matrix disabled")
            return
        """Calling this resets all LEDs to background color"""
        self.solid_color(
            Color(0, 0, 0),
            [i for i in range(self.led_count)],
        )

    async def countdown(self):
        if not self.enabled:
            logging.warning("led matrix disabled")
            return
        logging.info(f"on_countdown {self.led_count}")
        if not {"1", "2", "3"} <= self.images.keys():
            logging.error("images 1,2,3 not found, aborting countdown display")
            return
        await asyncio.sleep(3.85)
        logging.info("drawing 3")
        self.draw_pixels(self.images["3"])
        await asyncio.sleep(2.85)
        logging.info("drawing 2")
        self.turn_off_leds()
        self.draw_pixels(self.images["2"])
        await asyncio.sleep(2.85)
        self.turn_off_leds()
        logging.info("drawing 1")
        self.draw_pixels(self.images["1"])
        await asyncio.sleep(2.85)
        self.reset_leds()

    def end_game(self):
        if not self.enabled:
            logging.warning("led matrix disabled")
            return
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
        if self.io is None:
            return
        if not self.enabled:
            logging.warning("led matrix disabled")
            return
        self.configs = configs
        self.blink_time = self.configs[CUSTOM_KEY][BLINK_TIME_KEY]
        self.blink_interval = self.configs[CUSTOM_KEY][BLINK_INTERVAL_KEY]
        self.pixel_map = self._generate_pixel_map(
            self.num_squares, self.led_count
        )
        self.strip.setBrightness(self.configs[CUSTOM_KEY][LED_BRIGHTNESS_KEY])
        bg_red = self.configs[CUSTOM_KEY][BG_COLOR_R_KEY]
        bg_blue = self.configs[CUSTOM_KEY][BG_COLOR_G_KEY]
        bg_green = self.configs[CUSTOM_KEY][BG_COLOR_B_KEY]
        self.bg_rbg = (bg_red, bg_blue, bg_green)
        self.bg_color = Color(*self.bg_rbg)
        self.increase_contrast(self.images["1"], self.bg_rbg)
        self.increase_contrast(self.images["2"], self.bg_rbg)
        self.increase_contrast(self.images["3"], self.bg_rbg)
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

    def set_timed_area(self, idx=0, timeout=10):
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
        if not self.enabled:
            logging.warning("led matrix disabled")
            return
        if self.color_timer is not None:
            self.color_timer.cancel()
        self.color_timer = self.TimedColorChange(
            partial(self.solid_color, pixels=self.pixel_map[idx]),
            timeout,
            self.blink_time,
            self.blink_interval,
            self.bg_color,
        )

    def on_exit(self):
        """Call this before exiting program to turn off all LEDs"""
        if not self.enabled:
            logging.warning("led matrix disabled")
            return
        self.turn_off_leds()
        if self.color_timer is not None:
            self.color_timer.cancel()
