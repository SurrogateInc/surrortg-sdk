# Easy games to hook up

## Sphero rover exploration game

Before starting the tutorial, make sure that you have all of the required hardware
and the your Raspberry Pi has [SurroRTG SDK installed](getting_started).

**The Required hardware**

- [Sphero RVR](https://sphero.com/products/rvr)
- [Raspberry Pi 3b+ or 4](https://www.raspberrypi.org/products/)
- Jumper cables
- [a supported camera](camera_support)
- Optionally: a mount for the camera

### Hook everything up

First secure the Raspberry Pi inside the RVR. Then use three jumper cables to connect:

Raspberry Pi's GND to RVR's GND
Raspberry Pi's TX to RVR's RX
Raspberry Pi's RX to RVR's TX

Mount and connect the camera to Raspberry Pi. Then connect the USB cable from the
RVR to power up Raspberry Pi, press the button on the RVR's side to turn it on.

### Create the game on Surrogate.tv

Go to [surrogate.tv/admin](https://surrogate.tv/admin) and click `Create a new game`.

Then choose your custom title, description, and short ID, and then choose type
of the game to be `RVR`. This will create a Admin panel with the correct settings
for you. Optionally you can customize the looks by changing the default image assets.

### SurroRTG SDK's setup page

**Not supported yet. Use the [manual-setup-guide](#manual-setup-of-the-code)**

Connect to the hotspot created by the Raspberry Pi, and you'll get to the
Setup Page. From the setup page copy and paste the `Robot token` from the
Admin Panel, and choose the Gametype `RVR`.

Then give your wifi password to the robot to connect to surrogate.tv, and
click next.

### Manual setup of the code

You will need to enable serial communication on your raspberry pi by `sudo raspi-config`
to enable serial communication or just add line `enable_uart=1` to the end of
`/boot/config.txt` and reboot the raspberry pi.

Then you will need run the setup script to install the sphero-sdk and dependencies.
Run the following commands in the **games/rvr/ directory**.

```
sudo pip3 install -r requirements.txt

./SETUP.sh
```

You can test the game by running in your project root directory:

```
sudo python3 -m games.rvr.game
```

or by modifying the systemd file controller-rpi.service by changing the game module
path in the line starting with `Environment=GAME_MODULE=` to use games.rvr.game
and running at your project root directory:

```
./scripts/setup-systemd.sh
```

Now you should be able to got to [surrogate.tv/game/YOUR_SHORT_ID](https://surrogate.tv/game/YOUR_SHORT_ID),
and play the game!

## Running the LEDTestGame

Get the LED, wires and the 330 ohm resistor and connect them similarly to the
image below. Make sure that the LED's short leg is on the same side as the
GND. Optionally, some jumper cables and a breadboard can be used for easier construction.

![Led wiring](_static/images/led.png)

(Image from a beginner friendly
[Lighting an LED tutorial](https://projects.raspberrypi.org/en/projects/physical-computing/2))

From the terminal, you can now start the LEDTestGame by running
the following command in your SurroRTG SDK’s repository root:

```
sudo python3 -m games.led_test_game.game
```

This should now allow you to queue to the game at `www.surrogate.tv/game/<SHORT_ID_YOU_CHOSE>`,
and while on the game you can blink the lights with the space bar. After 10 blinks,
the game should end with a score of 10.

## Rc-Car Game

One of the easiest things to physically hook up to a raspberry pi is a RC-car.
This guide shows to hook up and control RC-car that has a separate servo and electrical
speed controller (ESC).

Required connections

1. Raspberry pi GND, servo GND and ESC GND together
2. Servo signal and ESC signal cables to Raspberry pi GPIOs
3. ESC power (+5V) to Servo power in

You will most likely also want to protect your RPI GPIOs by adding resistors.

The example code can be found in `game_templates/car_game.py`. The example code
explanation can be found [here](modules/game_templates.html#car-game)
