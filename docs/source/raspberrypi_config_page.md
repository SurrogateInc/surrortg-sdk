# Raspberrypi configuration tool

For your easier setup, our premade image hosts a configuration tool in form
of a website.

After booting the raspberrypi with our image installed it will provide a hotspot
where you will need to connect to setup the raspberrypi.

1. Connect to the hotspot raspberrypi is offering. This should be "raspberrypi"
    by default. **password is: passphrase**

2. After you are connected to the hotspot, open website [here](raspberrypi.local:3000)
    or by typing `hostname.local:3000`. (in this case `raspberrypi.local:3000`)

3. Now you should see the configration website

## Using the configuration tool

The tool allows you to do the following things

1. configure and connect to a wifi

2. set robotId which also changes the raspberrypi's hostname

3. set token for your controller and streamer

4. reconnect (restart) controller and streamer modules
