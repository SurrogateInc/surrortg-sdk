# ColorCatcher

Implementation of the [ColorCatcher](https://www.surrogate.tv/game/colorcatcher)
game on Surrogate.tv.

This game uses multiple new features supported by the Surrogate Python SDK:

* 1024 LED Matrix
* Aruco detection
    * Aruco markers are used to help generate a virtual grid on the game area
    * Aruco detection is also used to detect the location of the M5 bot
* M5 Bot with Mecanum wheels using the SurroRTG Arduino library

## Physical setup

### Hardware requirements to run this game without modifications

* M5 bot with Mecanum wheel base with Surrogate Arduino firmware installed.
  (See the [docs](https://docs.surrogate.tv/tcp_bot_games.html) for more info.)
* Two USB web cameras
    * The camera used for image recognition should be positioned straight above
      the game area for optimal performance
    * The camera seen by players can be positioned freely
* Four 32*8 LED matrix panels (WS2812B)
    * Connect the data input of one of the matrices to the raspi GPIO pin 18
    * Connect the same matrix to the +5V and GND pins of the power supply
    * Daisy chain the matrix to the other LED matrices
* 5v power supply for the LED matrices
* Piece of transparent plastic placed on top of the LED matrices
* Four aruco markers placed at the corners of the game area with the following
  IDs: 46, 47, 48, 49
* One aruco marker on top of the M5 bot (with ID 0)
* Optional:
    * Walls for the game area. Can be made from wood, solid foam, etc.
    * USB charger for the M5 bot
    * Lighting for the game area

## How to use aruco markers

* Search the internet for a website to generate aruco markers
* Generate the markers using the "5x5, 50" dictionary and print them on paper
* Position four aruco markers at the corners of the physical game area

```
    ------------------------------------
    |      |                   |       |
    |  46  |                   |  47   | <-- aruco marker
    |------|    GAME           |-------|
           |    AREA           |
    |------|                   |-------|
    |  49  |                   |  48   |
    |      |                   |       |
    ------------------------------------
```

## Configuring the game

### Make sure the following python modules are installed

* rpi_ws281x
* Pillow
* opencv-contrib-python

### The following must be set for the game to work

* The IP address of the M5 bot must be set in the Game Engine settings on the
  dashboard settings page. See the [docs](https://docs.surrogate.tv/tcp_bot_games.html#check-the-ip-address-of-the-microcontroller)
  on how to check the IP address.
* The aruco detection camera must be set in the ARUCO_CAMERA_PATH variable in
  surrortg-sdk/games/color_catcher.py.
* The main gameplay camera must be set in /etc/srtg/srtg.toml:

```
[sources.video_params]
type = "v4l2"
width = 1280
height = 720
framerate = 30
v4l2_dev = "/dev/v4l/by-id/YOUR_CAMERA_HERE"
```