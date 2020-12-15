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
a convinient basis for basically any simple game for the platform.

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

From the official Raspberry Pi
[Lighting an LED tutorial](https://projects.raspberrypi.org/en/projects/physical-computing/2)
, you will learn that to be able to blink a LED indefinately you can use
the following
[code](https://projects.raspberrypi.org/en/projects/physical-computing/4):

```python
from gpiozero import LED
from time import sleep

led = LED(17)

while True:
    led.on()
    sleep(1)
    led.off()
    sleep(1)
```

Here we can see that for blinking LEDs there are three steps:

1. import LED from gpiozero with `from gpiozero import LED`
2. initilize LED to the GPIO pin 17 with `led = LED(17)`
3. Turn the LED on and off by calling `led.on()` and `led.off()`

Let's now use this knowledge to modify the SimpleGame into the LEDTestGame:

```python
from gpiozero import LED  # step 1.
from surrortg import Game
from surrortg.inputs import Switch


class LEDSwitch(Switch):
    def __init__(self):
        self.led = LED(17)  # step 2.

    async def on(self, seat=0):
        print("LED on")
        self.led.on()  # step 3.

    async def off(self, seat=0):
        print("LED off")
        self.led.off()  # step 3.


class LedTestGame(Game):
    async def on_init(self):
        self.io.register_inputs({"switch": LEDSwitch()})

LedTestGame().run()
```

This process can be extended to basically any Python program:
find an appropriate template from game_templates, and extend/modify
it into your use case.

## Further reading

You can find other templates in the `game_templates` and `game` folders. You should
also take a look at [game_development](game_development) and [ready examples](ready_games).

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
