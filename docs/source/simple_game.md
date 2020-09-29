# SimpleGame

```python
from surrortg import Game  # First we need import the Game
from surrortg.inputs import Switch  # and our preferred input(s)
from surrortg.inputs import Joystick
import logging

# Create a custom switch, it really can do what ever you want.
class MySwitch(Switch):
    async def on(self, seat=0):
        # FIRE!!! or jump or drive or whatever you want
        print("on")

    async def off(self, seat=0):
        # stop the thing you were doing
        print("off")

# Create a joystick, it can control anything with 4 or 8 directions
class MyJoystick(Joystick):
    async def handle_coordinates(self,x,y,seat=0):
        logging.info(f"\tx:{x}, y:{y}")
        logging.info(f"{self.get_direction_8(x,y)}")
        # handle player input here

    async def reset(self):
        logging.info(f"reset")

class SimpleGame(Game):
    async def on_init(self):
        # During the Game initialization callback register your switch so the
        # Game Engine knows where to send the user input during the games.
        # Make sure that the name matches with the admin panel one.
        self.io.register_inputs({"switch": MySwitch()})
        self.io.register_inputs({"joystick_main": MyJoystick()})

# And now you are ready to play!
SimpleGame().run()
```
