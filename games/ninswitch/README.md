# Ninswitch games

Ninswitch directory contains three games:

- **game_simple.py** which contains code only for the Switch controls
- **game_imagerec.py** which is the same as game_simple.py, but it also has an image
    recognition sample code
- **game_irlkart.py** which contains the full code for the irlkart game

The games are made possible by [gdsports](https://github.com/gdsports)'s [NSGadget_Pi](https://github.com/gdsports/NSGadget_Pi)
library, which forwards the controls from Rapberry Pi to Switch.

## Hardware setup

Hardware requirements:

- Switch console
- Adafruit Trinket M0
- HDMI capture device
- HDMI cable
- Micro USB cable
- Jumper cables

Following [NSGadget_Pi](https://github.com/gdsports/NSGadget_Pi)'s setup:

1. Setup Trinket M0:
    - Download the [firmware](https://github.com/gdsports/NSGadget_Pi/blob/master/firmware/NSGadget.ino.f9e9ee2.trinket_m0.bin.uf2)
    - Plug in the Trinket M0 to the computer with the micro USB cable
    - Double tap the Trinket M0 reset button
    - When the TRINKETBOOT USB drive appears, drop the UF2 file on to the drive
    - Wait a few seconds until the Trinket M0 reboots
2. Do the wiring between Trinket M0 and Raspberry Pi:  
   **Bat** to **5V0**  
   **Gnd** to **Gnd**  
   **Rst** to **GPIO 23**  
   **RX (3)** to **GPIO 14 (TXD)**  
   **TX (4)** to **GPIO 15 (RXD)**
3. Connect Trinket M0 to Switch dock with the micro USB cable
4. Connect Raspberry Pi to Switch dock through HDMI Capture device and HDMI cable

## Software setup

Software requirements:

- Surrortg installed
- Knowledge on how to run different games inside `/games` directory
- Audio setup done

The image recognition needs a loopback device set up to `/dev/video21`:

1. First install srtg-watcherstream with `sudo apt install srtg-watcherstream`
2. Use `sudo nano /etc/modprobe.d/v4l2loopback.conf` to add another loopback device:
    - Replace `video_nr=20` with `video_nr=20,21`
    - Save and exit
3. Run `sudo rmmod v4l2loopback && sudo modprobe v4l2loopback` to update configurations

To install everything correctly on Raspberry Pi:

1. First change to the ninswitch directory with `cd games/ninswitch`
2. Install the Python requirements by running `sudo pip3 install -r requirements.txt`
3. Run the setup script with `sudo ./setup.sh`
4. Use `sudo nano /boot/config.txt` to add `dtoverlay=disable-bt` as the last line
    of config.txt. Then save and exit.
5. Change the raspi config with `sudo raspi-config`:
    - Select `Interfacing Options`
    - Select `P6 Serial`
    - Disable the login shell
    - Enable the serial interface
    - Exit raspi-config
6. Reboot with `sudo reboot`

## Image recognition

**game_imagerec.py** has a sample code how to detect a flag from the loopback
device stream.

This is possible through `surrortg/image_recognition`'s AsyncVideoCapture,
which reads individual frames from the loopback device stream in a separate
`image_rec_main`-task:

```python
from surrortg.image_recognition import AsyncVideoCapture, get_pixel_detector

...

    async def image_rec_main(self):
        # create capture
        self.cap = await AsyncVideoCapture.create("/dev/video21")

        ...

        # loop through frames
        i = 0
        async for frame in self.cap.frames():
            ...
```

The flag is detected with the help of `get_pixel_detector`-function.

It receives a list of spesific pixels from the flag, as pixel coordinates and colors,
and outputs a function that returns `True/False` based on whether the input frame
has similar pixels.

The color match sensitivity can be modified with `close=` -parameter, which defaults
to 25, smaller value requires closer match for each pixel to return `True`.

```python
# sample detectable
# ((x, y), (r, g, b))
FLAG_PIXELS = [
    ((206, 654), (14, 14, 12)),
    ((215, 655), (254, 254, 254)),
    ((223, 654), (11, 11, 11)),
    ((222, 663), (252, 252, 252)),
    ((214, 662), (0, 0, 0)),
    ((206, 661), (253, 251, 252)),
    ((205, 670), (20, 18, 19)),
    ((213, 670), (252, 252, 252)),
    ((222, 669), (0, 0, 0)),
    ((201, 650), (2, 2, 4)),
]

...

        # get detector
        has_flag = get_pixel_detector(FLAG_PIXELS)

        # loop through frames
        i = 0
        async for frame in self.cap.frames():
            # detect
            if has_flag(frame):
                logging.info("Has flag!")

```

### Creating custom image recognition

#### Save frame

First, you need to have a sample frame from the loopback device.

This can be done by changing `SAVE_FRAMES`variable from `False` to `True` from `game_imagerec.py`.
Then run the game until the point your detectable object is seen and stop the game.

You should then revert `SAVE_FRAMES` back to `False` to increase the frame processing
rate and prevent filling up the SD-card.

Alternatively, you can use the input `capture_frame` while running the game
through the site (needs to be bound in dashboard). to capture individual
frames as opposed to persistently capturing frames.

Assuming you have a working ssh connection, these images can be copied from the
raspi to current directory on your PC with scp:  
`scp -r <USER>@<RASPI_ADDRESS>:/opt/srtg-python/imgs/ .`

#### Generate pixel values

On your PC Python, install OpenCV by running `pip install opencv-contrib-python`

Then, you are able to create custom image recognition code by running pixel_detect
-program:  
`python surrortg/image_recognition/pixel_detect.py <PATH_TO_FRAME> <DETECTABLE_NAME>`

You can now click the interesting pixels that are included inside the detectable.
Press `Q` to exit.

This process should print a sample code to the terminal, an example output:

```
$ python surrortg/image_recognition/pixel_detect.py 103.jpg coin

Click the pixels to detect, example script is printed during the usage
press Q to exit

Printed values can be used together with 'get_pixel_detector'-function
For example:


import asyncio
from surrortg.image_recognition import AsyncVideoCapture, get_pixel_detector

# ((x, y), (r, g, b))
COIN_PIXELS = [
    ((70, 656), (209, 171, 0)),
    ((73, 665), (255, 231, 16)),
    ((80, 665), (247, 205, 5)),
    ((67, 668), (240, 206, 13)),
    ((60, 656), (200, 197, 58)),
]


SOURCE = "/dev/video21"

async def main():
    # create coin detector
    has_coin = get_pixel_detector(COIN_PIXELS)

    # create capture device
    async with await AsyncVideoCapture.create(SOURCE) as frames:
        async for frame in frames:
            # print if coin is detected
            if has_coin(frame):
                print("has coin")
            else:
                print("doesn't have coin")

asyncio.run(main())
```

## Trinket reset feature

Trinket M0's have been found to be quite temperamental with some controls. For this
reason one of the Raspberry Pi's GPIO pin is wired to Trinket's reset pin to be
able to reset the Trinket with the Raspberry Pi. This reset feature is available
in all ninswitch games and can be used two different ways, either through the admin
preview or as a part of the game loop.

If reset feature is used through admin preview, it means that reset control needs
to be mapped to some key through the dashboard. After that Trinket can be reset
by using the preview feature accessible only by the admins.

Another way to use reset feature is to configure it to reset Trinket each game
loop. This can be beneficial for games which are not always hosted and are intended
to run long periods of time on their own. This is disabled by default, but can
be enabled through the config.

Trinket reset feature has two configuration options. `TRINKET_RESET_PIN` is used
to define which Raspberry Pi GPIO pin is used to reset Trinket. It defaults to
23, but can be set to any free GPIO pin if needed. This requires to change the
reset pin wiring on the Raspberry Pi side according to the new pin. `RESET_TRINKET_EACH_LOOP`
is used to define if Trinket reset is performed each game loop and is disabled
by default. These constants can be overridden by defining them in the `config_local.py`
file.
