# Game Dashboard

The dashboard is the go-to place when running and hosting the games online.
It gives the game creator a visualization of what is happening with the game and
offers tools to intervene in case something goes wrong. It's not necessary to read
through every detail this whole document, but this is where you can find all the
information about the admin pages. However, it's good to familiarize yourself with
the general functionality of the admin pages.

Here’s the full list of the dashboard functionality:

## Status section

The status section allows monitoring the game and to intervene in case of a malfunction.
Here are all the functions:

- `Turn-ON/OFF game engine` allows to turn off and restart the game engine. This
    is useful sometimes when encountering issues after making changes to the game,
    especially when using new features.  

- `Enable the Watcher Stream` allows creating a watcher stream for the game. Allowing
    people in the queue to see the game of the current player. Note: the watcher
    stream has to be installed on one of the robots with the streamer (see:
    [installing watcher stream](getting_started.html#installing-surrogate-watcher-stream)).

- `Set the game visibility to other people` allows hiding the game from the public
    (won’t be shown on the front page and category pages), meaning that the game
    can only be accessed via the game link.

## Game Loop

The game loop section visualizes the state of the Game Engine and allows you to
intervene in case of malfunction. Here are the explanations of the game loop states:

- **Start** - the game engine has started a new game.

- **Pause** the game loop, pausing the game engine, but still allowing
    the players to queue up (see Game Settings -> Game Engine for more information).
    The pause will only take place after the current game loop has finished (END
    has been reached, or RESTART button is pressed).

- **Controllers** - Checks if all of the enabled robot controllers
    and streamers have the correct configuration (on_config methods have completed).

- **Players** - Shows how many players are in-game. The game will
    await if the minimum player amount requirement is not met.

- **Game** - the actual game is taking place. To reach this state,
    the robot controllers need to approve game start or `Allow Game to Start?`
    has to be pressed by the game host.

- **End** - the game has captured an end game event, for example,
    the maximum time of the game has been reached, or all players have finished
    the game (all seats have sent their final scores).

- Additionally, the game host can press the `RESTART` button to force restart
    the game loop. This is useful when a game has entered an unexpected state
    and needs to be reset.

## Players

The player’s section visualizes the queue status of the game.

- **Current** - shows the usernames of the players that are currently
    in the game.

- **Queue** - shows the players that are next in line to play
    the game.

## Sets

Here you can see the full list of sets and robots of a certain subset connected
to the game engine. For a more detailed explanation of the robots, sets, and seats
see [the Game Settings - Robot Configuration page](admin_settings.html#robot-configuration).

Each robot has its own status indicators:

- **Controller** - indicates the unique ID of the controller for a
    certain robot, as well as an icon which indicates if it’s operational or not.

- **Streamer** - indicates the ID of the streamer for a certain robot,
    as well as an icon which indicates if it’s operational or not.

- **OptionId** - indicates the name of the robot visible to the player,
    in case the player is able to choose a robot they want to control

- `Enabled toggle` - allows to enable or disable a certain robot,
    in case of an issue.

- `Preview button` - allows the game host to connect to a certain robot and to
    see the video stream as well as to take over the control of the robot.
    Only works if there is no player currently controlling the robot.

What do different status colors mean?

- Red - no connection.

- Yellow - the connection is established but there has been no configuration confirmation
    from a controller or a streamer.

- Green - all is working correctly.

At the bottom left of the game dashboard page, you will see the settings button,
which opens [the game settings and configurations page](admin_settings).
