# TCP-bot games

This section guides you through the process of running games where
smaller microcontroller-based robots are controlled with TCP commands.

To run these kinds of games, you will need at least one microcontroller with WiFi
connectivity in addition to the device running the Python code (such as a Raspberry
Pi). Some good options for microcontrollers are ESP32 and ESP8266 based development
boards, such as the [Wemos D1 mini](https://www.wemos.cc/en/latest/d1/d1_mini.html),
[ESP32-DevKitC](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/hw-reference/esp32/get-started-devkitc.html),
or the [M5StickC](https://m5stack-store.myshopify.com/collections/m5-hat/products/stick-c).

The games use our SurroRTG Arduino library that can be found in our
[Arduino Library GitHub repository](https://github.com/SurrogateInc/surrortg-firmware).
See the installation instructions below.

If you don't have the Python controller and game page setup yet, please follow
the instructions in our [Getting started section](getting_started.html#getting-started)
first.

## Using the SurroRTG Arduino library

### Installing Arduino IDE

To install Arduino IDE, download the installer and follow the instructions on the
[Arduino website](https://www.arduino.cc/en/software).

### Importing additional boards to Arduino IDE

The SurroRTG Arduino library supports ESP32 and ESP8266 based microcontrollers.
To be able to use the library and compile and upload code to your microcontrollers,
you need to import the board specifications to Arduino IDE.

For ESP32 microcontrollers, follow the instructions [here](https://randomnerdtutorials.com/installing-the-esp32-board-in-arduino-ide-windows-instructions/)

For ESP8266 microcontrollers, follow the instructions [here](https://randomnerdtutorials.com/how-to-install-esp8266-board-arduino-ide/)

### Installing SurroRTG Arduino library

The SurroRTG Arduino library can be found on our [Github repository](https://github.com/SurrogateInc/surrortg-firmware).
It is not included in the Arduino Library Index, so it must be installed manually.
To do so, download the [library](https://github.com/SurrogateInc/surrortg-firmware)
to your computer **as a zip-file**, and follow the instructions on
[Arduino website](https://www.arduino.cc/en/guide/libraries#toc4)
to import the library to Arduino IDE.

### Adding WiFi and OTA credentials for examples

**Note** All the examples need their own `wifi_secrets.h` file, so you
will need to repeat the process below for all the examples that you want
to use.

To connect to your wireless network, the examples need `wifi_secrets.h` files
that include your wireless network name and password. The files also contain
a password for Over-The-Air (OTA) updates, so that you can update the code
on your microcontroller wirelessly without plugging it to your computer
with a USB cable. You do need to perform the first code upload to a fresh
microcontroller using a USB cable, but after that you can choose between
uploading using OTA or a USB cable.

To configure your credentials, first open Arduino IDE and select the right
microcontroller board from the menus: `Tools -> Board ->` as shown in the
image below (Arduino MKR1000 is used as an example here, make sure to choose
the board that you are using). Make sure you have
[imported the additional boards](#importing-additional-boards-to-arduino-ide)
to your Arduino IDE if you don't see the correct board. If a compatible
microcontroller board is not selected, the examples of SurroRTG Arduino
library will show up as incompatible in the Arduino IDE.

```{image} _static/images/arduino-board-select.png
:alt: Arduino board selection
:width: 100%
:align: center
```

After selecting the right board, select one of the examples from the menus:
`File -> Examples -> SurroRTG`. Then go to `File -> Save As` to save the example
code to a new location. You can choose the file location yourself. After saving,
press the small arrow in the top right corner of the Arduino IDE window, in the
tab bar, to open a drop-down menu and select `New Tab` as seen in the picture
below. Arduino IDE then asks for a name for the new file. Type `wifi_secrets.h`
to the name field and press enter.

```{image} _static/images/arduino-new-tab.png
:alt: Arduino new tab creation
:width: 100%
:align: center
```

Copy the code below into the new file. Change the `ssid` to your wifi name
and `password` to your wifi password. Set the `ota_password` to a password
you would like to use to secure your OTA uploads to the microcontroller.
You can choose this password yourself, but you have to remember it if you
want to later upload code wirelessly to the microcontroller.

```c
#ifndef _SURRORTG_WIFI_SECRETS_H
#define _SURRORTG_WIFI_SECRETS_H

constexpr const char* ssid = "";            // Network name here
constexpr const char* password = "";        // Network password here
constexpr const char* ota_password = "";    // OTA-update password here

#endif  // _SURRORTG_WIFI_SECRETS_H
```

Now save the file. Change back to the example code by selecting the tab
from Arduino IDE's tab bar. Press the tick sign at the top left of Arduino
IDE to compile (Verify) the code as seen below. If the console header at the
bottom of the windows says "Done compiling", you have successfully setup your
credentials.

```{image} _static/images/arduino-compile.png
:alt: Arduino compile button
:width: 100%
:align: center
```

## TCP-bot dummy game

This is a simple game for testing the Python and microcontroller codes together.
We recommend starting with this example to see that everything works as expected.
The instructions guide you to setup one microcontroller first, but you can add
more microcontrollers to the game later following the instructions in the
[advanced features](#advanced-features) section.

### Upload firmware to a microcontroller

First, open the `TcpBotDummyGame` example code in Arduino IDE by selecting
from the menus: `File -> Examples -> SurroRTG -> TcpBotDummyGame`.
Then follow the instruction described in [Adding WiFi and OTA credential for examples](#adding-wifi-and-ota-credentials-for-examples)
to setup the credentials.

After you have configured the credentials, make sure you have the `TcpBotDummyGame`
file open, and you have selected the right port for the microcontroller, as seen
in the picture below. Press the Upload button on the top left of your Arduino
IDE. The console header at the bottom of your Arduino IDE should first say
"Uploading..." and then "Done uploading".

```{image} _static/images/arduino-port-select.png
:alt: Arduino port select
:width: 100%
:align: center
```

Once you have successfully uploaded the code to the microcontroller for the first
time, you can update the microcontroller's code using
[OTA-updates](#ota-updates).

If you face issues while uploading the code, and the console on the bottom of your
Arduino IDE does not say "wifi_secrets.h: No such file or directory",
check [Arduino Troubleshooting](https://www.arduino.cc/en/Main/Troubleshooting)
for help.

#### Check the IP address of the microcontroller

You now need to find out the IP address of the microcontroller, so that the
Python controller can be configured to send messages to the right IP address.

After the code has uploaded, open the Serial Monitor by pressing the button on
the top right of your Arduino IDE window. Set the baudrate from the drop-down
menu to 115200 as shown in the image below.

```{image} _static/images/arduino-baudrate.png
:alt: Arduino serial baudrate
:width: 100%
:align: center
```

The microcontroller code writes its IP address to the Serial
Monitor every 10 seconds if it is connected to the WiFi. If you can not see
the IP address in the Serial Monitor, check that you have entered the correct
WiFi credentials to the `wifi_secrets.h` file. While having the Serial Monitor
open, you can also try to upload the code again to see boot logs from the
microcontroller. If you do not see anything, double check the baudrate.
If that does not work, please check [Arduino Troubleshooting](https://www.arduino.cc/en/Main/Troubleshooting).

Here’s an example from Arduino IDE Serial Monitor tool:

```{image} _static/images/arduino-ip.png
:alt: Microcontroller IP address
:width: 100%
:align: center
```

This IP address needs to be
[configured on your game's settings](#configure-the-bot-in-the-game-settings).

### Configure the bot in the Game Settings

Let's assume your controller SDK and streamer run on a Raspberry Pi that is in
the same network with the microcontroller, and uses `tcp-bot` as the value of
`device_id` in its `srtg.toml` configuration file.

Open the Robot Configuration on the Admin panel by going to your game's
Game Settings, selecting the Game Engine section and scrolling to the bottom
of the page.

Your Admin panel configuration needs to have one seat configured per
microcontroller. The values of `seat` and `set` should both be 0 for this first
microcontroller. This should happen automatically once you start the Python
controller code in the Raspberry Pi for the first time. You can choose the
value for `Queue Option Id` yourself.

The IP address of the microcontroller also needs to be configured to the
Robot Configuration. Change the placeholder text of the
`Microcontroller_ip_addr` field to the IP of your microcontroller that
you discovered in the previous step.

Here's an example of the "Robot Configuration" with all of the necessary
fields filled.

```{image} _static/images/arduino-robot-config-1.png
:alt: Robot configuration for one microcontroller
:width: 100%
:align: center
```

### Testing the game

Now that you have configured one microcontroller to work with the Raspberry Pi,
you can test the game. Make sure the Python controller code is running. You should
see new lines appear in the controller logs as you press the arrow keys and spacebar.
Pressing the spacebar should also light up the built-in LED if your microcontroller
board has one.
If you are [running the controller as a systemd service](getting_started.html#running-the-surrortg-python-sdk-controller-automatically-on-boot),
you can see the logs with the command `sudo journalctl -fu controller`.

## Advanced features

### OTA-updates

Once you have uploaded the example code once to the microcontroller, and have
correctly configured WiFi and OTA-credentials, you can upload new versions of
the code via WiFi using Over-The-Air updates. This is a very useful feature if
your microcontroller is located somewhere where it is hard to access the USB
port of the device. Note that the microcontroller has to be in the same WiFi
network with the computer that you use to upload the code with.

To use OTA-updates, select the correct IP address under "Network ports" from the
Port selection menu as shown in the picture below. Then upload the code by using
the Upload button on the Arduino IDE.

```{image} _static/images/arduino-ota-port.png
:alt: Arduino OTA port select
:width: 100%
:align: center
```

### Configure multiple bots to a game

#### Admin panel setup for multiple bots

Let's assume your controller SDK and streamer run on a Raspberry Pi that is in
the same network with the microcontrollers, and uses `tcp-bot` as the value
of `device_id` in its `srtg.toml` configuration file.

The Robot Configuration in your game's Game settings needs to have 2 seats
configured in the same controller. This can be achieved by the following configuration.

| Id      | Streamer | Seat | Set |
| :-----: | :------: | :--: | :-: |
| tcp-bot | tcp-bot  | 0    | 0   |
| tcp-bot | tcp-bot  | 1    | 0   |

Add a new item to the Robot Configuration by pressing the "Add New" button under
the existing robot. Set the `Id` and `Streamer` fields to the `device_id` of
the Python controller as is set for the first robot in the configuration, in
this example `tcp-bot`. You can choose the `Queue Option Id` value yourself,
but it is probably best to set the values so that you can recognize the
microcontrollers easily. You can ignore the `Local Config Url` field.
Set the `Microcontroller_ip_addr` to match the new microcontroller's IP
address, which you can find out
[the same way as with the first microcontroller](#check-the-ip-address-of-the-microcontroller).
Remember to also enable the new microcontroller by turning on the `Enabled`
toggle button.

Here’s how the robot configuration would look like on the settings page:

```{image} _static/images/arduino-robot-config-2.png
:alt: Robot configuration for two microcontrollers
:width: 100%
:align: center
```

You can configure as many bots as you want by appending more robots to the
Robot Configuration on your game's Game Settings.
