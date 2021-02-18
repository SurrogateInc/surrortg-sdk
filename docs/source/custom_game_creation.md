# Custom game creation (IN DEVELOPMENT)

After you have finished the [installation](getting_started), you are ready
to start experimenting with your own [custom game](#custom-game-based-on-templates)
based on the templates.

## Custom game based on templates

This chapter teaches you how to create a custom game from scracth
or how to integrate existing Python game to the platform.

### SimpleGame template

The `game_templates` directory contains multiple templates, one of
which is `simple_game.py`:

```python
from surrortg import Game  # First we need import the Game
from surrortg.inputs import Switch  # and our preferred input(s)
from surrortg.inputs import Joystick
import logging
import asyncio
import time


# Create a custom switch, it really can do what ever you want.
class MySwitch(Switch):
    async def on(self, seat=0):
        # FIRE!!! or jump or drive or whatever you want
        logging.info(f"on for seat {seat}")

    async def off(self, seat=0):
        # stop the thing you were doing
        logging.info(f"off for seat {seat}")


# Create a joystick, it can control anything with 4 or 8 directions
class MyJoystick(Joystick):
    async def handle_coordinates(self, x, y, seat=0):
        logging.info(f"\tx:{x}, y:{y}")
        logging.info(f"{self.get_direction_8(x,y)}")
        # handle player input here

    async def reset(self, seat=0):
        logging.info(f"reset")


class SimpleGame(Game):
    async def on_init(self):
        # During the Game initialization callback register your switch so the
        # Game Engine knows where to send the user input during the games.
        # Make sure that the name matches with the admin panel one.
        self.io.register_inputs({"switch": MySwitch()})
        self.io.register_inputs({"joystick_main": MyJoystick()})

    async def on_start(self):
        """
        Simple game simulates a 3 player game where timestamp scores
        are sent for each seat and the game is ended with the final score
        parameter in the third send score method.
        """
        start_time = time.time()
        await asyncio.sleep(5)
        score_temp = self.convert_to_ms(time.time() - start_time)
        self.io.send_score(score=score_temp, seat=0)
        await asyncio.sleep(5)
        score_temp = self.convert_to_ms(time.time() - start_time)
        self.io.send_score(score=score_temp, seat=1)
        await asyncio.sleep(5)
        score_temp = self.convert_to_ms(time.time() - start_time)
        self.io.send_score(score=score_temp, seat=2, final_score=True)

    def convert_to_ms(self, time):
        """
        When a game is using timestamp scores, the controller must provide the
        scores as milliseconds. This is a simple conversion function that
        converts seconds to milliseconds.

        :param time: Time in seconds
        :returns: Time in milliseconds
        """
        text = f"{time:.2}"
        converted = float(text)
        scaled = converted * 1000
        return scaled


# And now you are ready to play!
if __name__ == "__main__":
    SimpleGame().run()
```

The SimpleGame template does not do much by itself other than it provides
a convenient basis for basically any simple game for the platform.

So at the top of the file, we import generic
[Game](modules/surrortg.html#module-surrortg.game) class and
[Switch](modules/surrortg.inputs.html#module-surrortg.inputs.switch)
class from the [inputs](modules/surrortg.inputs.html#surrortg-inputs)
subpackage:

```python
from surrortg import Game  # First we need import the Game
from surrortg.inputs import Switch  # and our preferred input(s)
```

Then we implement
[Switch](modules/surrortg.inputs.html#module-surrortg.inputs.switch)
class's [on](modules/surrortg.inputs.html#surrortg.inputs.switch.Switch.on)
and [off](modules/surrortg.inputs.html#surrortg.inputs.switch.Switch.off)
methods. Currently it only has `logging` as a place holder for the actual implementation.

Then the template goes into overriding
[Game](modules/surrortg.html#module-surrortg.game)'s
[on_init](modules/surrortg.html#surrortg.game.Game.on_init)
method, which is used to initialize classes and registering inputs.

Then [GameIO](modules/surrortg.html#module-surrortg.game_io)
class instance accessed thourgh `self.io` is used to
[register](modules/surrortg.html#surrortg.game_io.GameIO.register_inputs)
the MySwitch input defined above.

```python
class SimpleGame(Game):
    async def on_init(self):
        # During the Game initialization callback register your switch so the
        # Game Engine knows where to send the user input during the games.
        # Make sure that the name matches with the admin panel one.
        self.io.register_inputs({"switch": MySwitch()})
        self.io.register_inputs({"joystick_main": MyJoystick()})
```

Then the custom Game can be started by calling
[run()](modules/surrortg.html#surrortg.game.Game.run).

```python
# And now you are ready to play!
SimpleGame().run()
```

Now when you execute the game with

```
cd ~/surrortg-sdk/
sudo python3 -m game_templates.simple_game
```

and gueue to the game.

You should be able to see printing:

```
on
off
on
off
...
```

when you press the key down and up you have bound to a name `switch` from the
Admin panel.

The game will stop after 15 seconds, after the controller sends final scores from
the on_start method.

### Custom game example: LEDTestGame

Now we are ready to look into previous chapter's
[LEDTestGame](getting_started.html#running-the-ledtestgame) in more
detail, and how would you create that by yourself.

LEDTestGame uses pigpio, which is a library for controlling GPIO pins in Raspberry
Pi. It allows GPIO pins to be controlled multiple ways, one of them being through
Python. The main part of pigpio is its daemon, which is a Linux service. It must
be running in order for the pigpio to work. And assuming that either the pre made
SDK image was used, or that all steps were followed in manual SDK installation,
pigpio should be already installed to your Raspberry Pi and its daemon service
enabled such that it starts automatically even after reboot.

The following code shows minimum steps to use pigpio to blink LED with fixed interval.
It is commented heavily and attempts to explain all steps clearly.

```python
from time import sleep
import pigpio

# BCM pin number for LED pin
LED_PIN = 17

# Connect to pigpio daemon. It is possible that connecting to daemon fails and
# in such case it is necessary to handle that for example by raising exception.
pi = pigpio.pi()
if not pi.connected:
    raise RuntimeError("Could not connect to pigpio daemon.")

# Set LED pin to output mode. It is not strictly necessary to do this as pigpio
# will set the pin to output mode when it is being driven to HIGH or LOW, but
# this can clarify what pin is intended to be use for, especially in more
# complex code.
pi.set_mode(LED_PIN, pigpio.OUTPUT)

# Start toggling LED on and off
while True:
    pi.write(LED_PIN, pigpio.HIGH)
    sleep(1)
    pi.write(LED_PIN, pigpio.LOW)
    sleep(1)
```

Now that we have some kind of understanding how pigpio can be used to control GPIO
pin to blink an LED, we can move forward to turn this a bit closer to LEDTestGame.

```python
import logging

import pigpio

from surrortg import Game
from surrortg.inputs import Switch


LED_PIN = 17


# This class mainly implements functionality that happens when the LED input
# is pressed or released during game. It inherents from Switch parent class,
# which provides basic functionality for switch type input. In this case most
# important functionality provided by Switch class are on() and off() methods,
# which are called when the LED input is pressed or released. We can override
# these methods to add custom code that is executed on such events.
class LEDSwitch(Switch):
    def __init__(self):
        # Connect to pigpio daemon
        self._pi = pigpio.pi()
        if not self._pi.connected:
            raise RuntimeError("Could not connect to pigpio daemon.")

        # Initialize LED pin
        self._pi.set_mode(LED_PIN, pigpio.OUTPUT)

    # Override on() method to implement custom functionality when the LED input
    # is pressed; Turn on the LED and log the event.
    async def on(self, seat=0):
        self._pi.write(LED_PIN, pigpio.HIGH)
        logging.info("LED on")

    # Override off() method to implement custom functionality when the LED input
    # is released; Turn off the LED and log the event.
    async def off(self, seat=0):
        self._pi.write(LED_PIN, pigpio.LOW)
        logging.info("LED off")

    # Override shutdown method to implement custom functionality when
    # controller code stops running.
    async def shutdown(self, seat):
        # Set LED pin into safe state by setting it to input mode
        self._pi.set_mode(LED_PIN, pigpio.INPUT)
        # Close pigpio daemon connection
        self._pi.close()


# This class implements all functionality related to the game itself. It
# must inherent from Game parent class because it will provide lot of features
# that are happening behind the scenes and are mandatory for the game to work.
class LedTestGame(Game):
    # Override on_init() method. This method is called once when the controller
    # software starts to run and can be used to initialize various things.
    async def on_init(self):
        # Register the LED input. This will inform Surrogate platform from all
        # inputs that the controller supports and add those to the game.
        self.io.register_inputs({"switch": LEDSwitch()})


if __name__ == "__main__":
    # Start running the game.
    LedTestGame().run()
```

This game will control the LED when corresponding input is pressed, but it will
do so until Game Engine tells it to stop (300 seconds by default). It is useful
to have such a timeout to prevent the game from running forever, but usually the
game should also be stopped if specific condition occurs. In the following code
we will add score feature, which will increment score every time the LED input
is pressed, and stops the game when score reaches 10. With these changes this code
should be now equivalent to the LEDTestGame.

```python
import logging

import pigpio

from surrortg import Game
from surrortg.inputs import Switch


LED_PIN = 17


class LEDSwitch(Switch):
    # LEDSwitch takes now additional parameter which is callback function
    # to handle score updates.
    def __init__(self, score_cb):
        # Connect to pigpio daemon
        self._pi = pigpio.pi()
        if not self._pi.connected:
            raise RuntimeError("Could not connect to pigpio daemon.")

        # Initialize LED pin
        self._pi.set_mode(LED_PIN, pigpio.OUTPUT)
        # Store reference to score callback function
        self.score_cb = score_cb

    async def on(self, seat=0):
        self._pi.write(LED_PIN, pigpio.HIGH)
        # Call score callback every time LED input is pressed
        self.score_cb()
        logging.info("LED on")

    async def off(self, seat=0):
        self._pi.write(LED_PIN, pigpio.LOW)
        logging.info("LED off")

    async def shutdown(self, seat):
        # Set LED pin into safe state by setting it to input mode
        self._pi.set_mode(LED_PIN, pigpio.INPUT)
        # Close pigpio daemon connection
        self._pi.close()


class LedTestGame(Game):
    # This function will be used to increment score and send updated score to
    # Game Engine. It will also send final score when score reaches 10, which
    # causes Game Engine to end the game.
    def update_score(self):
        self.score += 1
        logging.info(f"score: {self.score}")
        if self.score >= 10:
            # End game by sending final score to Game Engine.
            self.io.send_score(score=self.score, final_score=True)
            # Disable all registered inputs.
            self.io.disable_inputs()
        else:
            # Send updated scores to Game Engine.
            self.io.send_score(score=self.score)

    async def on_init(self):
        # Register LED input with update score callback function
        self.io.register_inputs({"switch": LEDSwitch(self.update_score)})

    async def on_prepare(self):
        # Set score to 0 before game starts
        self.score = 0


if __name__ == "__main__":
    # Start running the game
    LedTestGame().run()
```

This process can be extended to basically any Python program:
find an appropriate template from game_templates, and extend/modify
it into your use case.

## Further reading

You can find other templates in the `game_templates` and `game` directories.
You should also take a look at [game_development](game_development) and [ready examples](ready_games).

The [inputs](modules/surrortg.inputs.html#surrortg-inputs) subpackage contains also
many other types of inputs, such as
[Joystick](modules/surrortg.inputs.html#module-surrortg.inputs.joystick),
which works well when more complex user input is required.

The [GameIO](modules/surrortg.html#module-surrortg.game_io)
class also contains much more methods for communication with the Game Engine,
such as sending
[progresses](modules/surrortg.html#surrortg.game_io.GameIO.send_progress),
[laps](modules/surrortg.html#surrortg.game_io.GameIO.send_lap),
[scores](modules/surrortg.html#surrortg.game_io.GameIO.send_score),
[enabling](modules/surrortg.html#surrortg.game_io.GameIO.enable_inputs) and
[disabling](modules/surrortg.html#surrortg.game_io.GameIO.disable_inputs) inputs
or [resetting all registered inputs](modules/surrortg.html#surrortg.game_io.GameIO.reset_inputs).

[on_init](modules/surrortg.html#surrortg.game.Game.on_init) is just one of
the many methods, that can be used to control the [Game](modules/surrortg.html#module-surrortg.game).
Other major ones include
[on_prepare](modules/surrortg.html#surrortg.game.Game.on_prepare),
[on_pre_game](modules/surrortg.html#surrortg.game.Game.on_pre_game),
[on_start](modules/surrortg.html#surrortg.game.Game.on_start),
[on_finish](modules/surrortg.html#surrortg.game.Game.on_finish) and
[on_exit](modules/surrortg.html#surrortg.game.Game.on_exit).
More explanations can be found from the [Game loop](game_loop) page.
