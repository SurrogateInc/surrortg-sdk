# Relay game

Relay game is an example of how Raspberry Pi and our SDK can be used to control
relays. Relays are just electrically controlled switches, which makes them easy
to understand and use. The main idea behind a relay is that it can control relatively
high voltage and current with a small control signal.

There are three typical use cases where one might need a relay with Raspberry Pi.
First one is when the controlled load (High power LED, motor, heating element etc.)
requires higher current than Raspberry Pi's GPIO pins can supply (more than ~16
mA). Second case is when controlled load requires different voltage than Raspberry
Pi's GPIO pins supplies (smaller or higher than 3,3 V). And the last case is if
the controlled load requires AC current, because Raspberry Pi's GPIO pins can only
supply DC current.

This documentation will show step by step how to use SainSmart 4-channel 5 V relay
module, but software can be configured easily to support as many relays as Raspberry
Pi has GPIO pins (this will be covered at the end of the documentation). There
are also lots of similar/duplicate relay modules out there, so those can be used
also if availability is a problem.

> **WARNING:** Do not attempt to connect plain relay directly to Raspberry Pi's
GPIO pins if you are not familiar with inductive kickback and don't know how to
protect GPIO pins from it. Relay has a coil in the secondary side which can generate
voltage spike when control signal is disconnected. This voltage spike can damage
sensitive electronics very easily and result into a broken Raspberry Pi. Relay
modules have drive circuit which takes care of the voltage spikes and protects
the device which is controlling the relays.

## Hardware setup

**Required hardware**

- Raspberry Pi
- Raspberry Pi power supply
- SainSmart 4-channel 5 V relay module
- 6 pcs female to female jumper wires

**Setup**

1. Wiring between Raspberry Pi and relay module:
    - **Ground** to **GND**
    - **5V Power** to **VCC**
    - **GPIO 26** to **IN1**
    - **GPIO 19** to **IN2**
    - **GPIO 13** to **IN3**
    - **GPIO 6** to **IN4**
2. Relay module should have jumper connector between JD-VCC and VCC by default,
   and that should be left connected.

![Relay module wiring](_static/images/relay_module_wiring.jpg)

## Software setup

> **NOTE:** All of our games requires the installation of the [SurroRTG SDK](getting_started.html#sdk-installation).

1. [Create new game to our platform](getting_started.html#create-a-game-instance-on-surrogate-tv)
2. [Edit the streamer configuration file](getting_started.html#configuration-file)
   according to the current game setup. This means mainly the device id, game token
   and camera settings.
3. Start the controller software
    - If controller software is run manually from the terminal, following command
      can be run at the SDK root to start the software.
      `sudo python3 -m games.relay_game.game`
    - [If controller software is run as a service](getting_started.html#running-the-surrortg-python-sdk-controller-automatically-on-boot),
      edit the service configuration file to start correct python module.
4. Go to the game dashboard and verify that streamer and controller are connected
   to the game engine. Both should have green checkmark to indicate connection.
5. Make correct key bindings for the relays from the game dashboard.

And now the relay game should be set up correctly and relays can be controlled
either by starting to play the game or open admin preview from the game dashboard.

## Game configuration

Some of the games has `config.py` file, which defines various constants. These
are used to make the software more flexible and that way software can adapt for
example to different hardware configurations. If you want to modify the values
of these constants, that should be done by creating a `config_local.py` file and
defining the constants there with the same name and new value.

`GPIO_SWITCHES` is a dictionary where each item corresponds to GPIO pin which controls
one relay. It is used to define how many relays are used, what are the names for
the player inputs and what Raspberry Pi GPIO pin is used to control that relay.

`ON_LEVEL` defines the logic level for the GPIO pins when those are in active state.
Some relay modules activates the relay when the inputs are LOW and others when
the inputs are HIGH. This constant can be used to adapt to that variation and activate
relays only when the inputs are active.
