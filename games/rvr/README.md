# First time setup

Use ansible as usual to get the rvr/ to the raspi

Then on raspi:
use `sudo raspi-config` to enable serial communication
or
just add line `enable_uart=1` to the end of `/boot/config.txt`

and then reboot

Then run `./SETUP.sh`

and then reboot again