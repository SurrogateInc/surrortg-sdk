## Open questions

### 1. Do we have different game modes as different game.py implementations?

### Different game.py implementations:

Good

+ Uses the current abstraction for different game types
+ Clear separation between game-templates and needed configs

Bad

- Have to implement logic to change current game.py from FE?
- How to make sure all robots in same game type?
- How does robot configs react when there is robot with new settings?
  - Does it still show old ones?

### Same game.py implementation, selection for game type is just robot config:

Good

+ Configs always same (user conditional part on the JSON schema form)
+ No need to create new logic for change game.py from FE
+ All robots listen to same "game-template" shared config

Bad

- Need to extend the JSON schema robot config implementation
- Needs new abstraction of "games inside game" very similar to what the game templates
  already do

### 2. How to handle the different extensions, driving modes and inputs?

My idea:

- Divide the robot to "areas" based on function + extension layout
- "Movement" - Both sides (4x motors, 4x), 4 wheel driving, 2 wheel driving etc
- "Top servos" - (3x servos), camera movement, robot arm, etc
- "Top servos 2" - (3x servos), robot arm, etc
- "Bottom servo" - (1x servo), front claw, button presser
- "Top Led" - (1x led matrix), something else in future?
- "Bottom Sensor" - (1x i2c), color, etc

For ex: Thru configs user can set the "movement" to "4 wheel drive".
This will automatically create "joytick" input for movement with "WASD"
This way we can make sure config is easy for the user and we can have easy
instruction on what device to add where + there is no way to "overlap"

Different game modes can also limit the options based on the need for that game mode.
Implementation wise these areas are the same for all game modes.

### 3. How to change default key binds "on the fly" for different game modes?

For ex: Someone selects "Movement" option "4 Motors", we offer Joystick "WASD", but
if we also have option "1 Motor" we could just offer actuator with "WS".

Other option is always offer "Movement" "WASD" and just use the WS if its single motor mode,
but this might be more limiting in other cases (like 3x servos on top where it can be robot arm
or totally different 3x servo device that might want totally different type inputs)


## TODO:

### Phase 1 (Before 3d case)

- Python architecture for game templates, hw and slots
- Basic bot (yellow bot, no 3d printed box)
    - Python architecture (game-templates, extension slots)
    - Slot options
        - movement:
            - 4 wheel drive (d)
            - 2 wheel drive
        - top-slot-1: 2 servo camera gimbal (d)
        - bottom-slot: Claw (d)
        - sensor-slot: light sensor (d)
    - Prototype game-templates
        - "Racing game" (d)
- QR reader WiFi setup
    - WiFi/Robot-Token with reading QR code with camera (RasPi Image)
    - Generate QR code in admin panel (FE)
    - Shortened Robot-Token (FE, BE)?
- Multiple I2C devices testing
    - Currently I have connected 2 Oled screens, servo board and I2C light sensor to bot.
      There is issues if for ex. moving servo + change Oled image at same time (writing)
      the image takes time.
    - Logic to only change Oled screen image max every 0.5 sec?
    - Clock hz?
    - Reserve some GPIO pins directly from Raspi to be used with servos?
    - Use separate I2C for servo board?
- How to check if specific I2C device exists without crashing the app?
- Test Leevis 2 power solutions (separate motor/servo power vs same motor/servo power)
- Conditional configs
- Change inputs after 'on_config'
- Investigate mic options
- Investigate speaker options

- Website redesign
    - What is needed and what not?
- One working game-template?

### Phase 2 (after 3d printed box)

- Leevis board ("hat" to connect components easily)
- Actual 3d printed prototype case
- Test heat issues
- Effect of magnets?
- Game types, extensions, etc ...


## Old notes
- LCD panel eyes
    - Use also when not connected to GE (indicate status)
- Light sensor
- Game template python design architecture
- Design different pre-configured "input/function groups" (4 wheel drive vs 4 individual motors)
    - Driving mode (side 4x motors, 4x servos)
        - 4 wheel drive
        - 2 wheel drive
        - 2 wheel back drive - front servo steer
        - Custom
        - Disable
    - Front bottom servo
        - Claw
        - Custom
        - Disable
    - Front top 3x servos
        - 2 pivot camera
        - Custom
        - Disable
    - Front top 4x servos?
        - Robot arm
        - Custom
        - Disable
    - Back top 1x led
        - Led
        - Disable
    - Bottom I2C sensor
        - Light sensor
        - Disabled
- How to check that I2C device is there?
- QR reader setup to Robot
- QR generator web
- Setup flow
- Better PCA9685 code
- Enum support to robot configs
- Conditional setup for robot config?
- Mobile actuator
- 2 wheel drive
- 4 wheel drive

