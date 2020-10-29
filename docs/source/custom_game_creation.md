# Custom game creation

After you have finished the [installation](getting_started), you are ready
to start experimenting with your own [custom game](#custom-game-based-on-templates)
based on the templates.

## Custom game based on templates

This chapter teaches you how to create a custom game from scracth
or how to integrate existing Python game to the platform.

### SimpleGame template

The `game_templates` directory contains multiple templates, one of
which is [simple_game](simple_game):

```python
from surrortg import Game  # First we need import the Game
from surrortg.inputs import Switch  # and our preferred input(s)


# Create a custom switch, it really can do what ever you want.
class MySwitch(Switch):
    async def on(self, seat=0):
        # FIRE!!! or jump or drive or whatever you want
        print("on")

    async def off(self, seat=0):
        # stop the thing you were doing
        print("off")


class SimpleGame(Game):
    async def on_init(self):
        # During the Game initialization callback register your switch so the
        # Game Engine knows where to send the user input during the games.
        # Make sure that the name matches with the admin panel one.
        self.io.register_inputs({"switch": MySwitch()})


# And now you are ready to play!
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
methods.

(Currently it only has `print` as a place holder for the actual implementation)

```python
# Create a custom switch, it really can do what ever you want.
class MySwitch(Switch):
    async def on(self, seat=0):
        # FIRE!!! or jump or drive or whatever you want
        print("on")

    async def off(self, seat=0):
        # stop the thing you were doing
        print("off")
```

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
```

Then the custom Game can be started by calling
[run()](modules/surrortg.html#surrortg.game.Game.run).

```python
# And now you are ready to play!
SimpleGame().run()
```

Now when you execute the game with

```
cd ~/surrortg-sdk/getting_started
python simple_game.py
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

The `game_templates` directory contains also more complicated templates
such as [AdvancedGame](advanced_game) and [CarGame](car_game).

The [inputs](modules/surrortg.inputs.html#surrortg-inputs) subpackage contains also
many other types of inputs, such as
[Joystick](modules/surrortg.inputs.html#module-surrortg.inputs.joystick),
which works well when more complex user input is required. An example usage
can be seen for example in the [AdvancedGame](advanced_game) template.

The [GameIO](modules/surrortg.html#module-surrortg.game_io)
class also contains much more methods for communication with the Game Engine,
such as sending
[progresses](modules/surrortg.html#surrortg.game_io.GameIO.send_progress),
[laps](modules/surrortg.html#surrortg.game_io.GameIO.send_lap),
[scores](modules/surrortg.html#surrortg.game_io.GameIO.send_score),
[enabling](modules/surrortg.html#surrortg.game_io.GameIO.enable_inputs) and
[disabling](modules/surrortg.html#surrortg.game_io.GameIO.disable_inputs) inputs or
[resetting all registered inputs](modules/surrortg.html#surrortg.game_io.GameIO.reset_inputs).

[on_init](modules/surrortg.html#surrortg.game.Game.on_init) is just one of
the many methods, that can be used to control the [Game](modules/surrortg.html#module-surrortg.game).
Other major ones include
[on_prepare](modules/surrortg.html#surrortg.game.Game.on_prepare),
[on_pre_game](modules/surrortg.html#surrortg.game.Game.on_pre_game),
[on_start](modules/surrortg.html#surrortg.game.Game.on_start),
[on_finish](modules/surrortg.html#surrortg.game.Game.on_finish) and
[on_exit](modules/surrortg.html#surrortg.game.Game.on_exit).
More explanations can be found from the [Game loop](game_loop) page.

Especially for the more advanced games, you might need to also know more
[advanced Admin panel configuration](advanced_admin_panel).
