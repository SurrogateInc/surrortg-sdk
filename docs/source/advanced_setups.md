# Advanced game setups

This page describes some advanced configurations which can be used for creating
more advanced and complex games.

## Running controller and streamer on different machines

Sometimes it can be useful to run controller (python SDK) and streamer on
different machines. For instance in some cases you might want to setup streaming
from a PC while controlling some hardware through Raspberry Pi's GPIO. This is
supported, although it has a drawback of slightly increased latency due to
controls being routed through a server instead of using a peer-to-peer connection.

The controller and streamer installation works exactly same as when running them
on the same machine. Each machine needs it's own config file, but these can be
identical except the device_id field needs to be different.

To pair a controller and a streamer from different machines into a single playable
robot which one player controls, you need to set the controller and streamer
ids accordingly in the admin panel. These are found in the `Game Engine` section
of the settings page. By default each robot assumes controller and
streamer ids are the same.

Same streamer can be used with multiple controllers, e.g. if you have a single
camera aimed at the game arena but multiple robots which are controller by
different players.

## Logical units

The controller SDK can run in a logical mode. This means that no players will
ever connect to the logical unit, but game state events are received normally.

The logical unit can be used for building game logic or other auxiliary
services like OBS scene switcher. As example, the game logic could be an arena
which changes somehow based on the game state. To give some examples, a gate could
open and close based on whether the game is running or not, or some LEDs could change
color based on the game state.

To run controller in logical mode, add `robot_type=RobotType.LOGICAL` to the
[Game class run() method](modules/surrortg.html#module-surrortg.game.Game.run).
If you are running multiple logical controllers on the same device, you can
pass `device_id=<some id>`. This way you don't need to duplicate the entire
config file to change the device id. Otherwise the controller can be installed,
used and developed in the same way as any other controller.

An example of logical controller can be found in `surrortg/utils/obs_scene_switcher.py`
in the bottom of the file under the `if __name__ == "__main__":` section.
There a simple OBS scene switcher is built using a logical controller.
