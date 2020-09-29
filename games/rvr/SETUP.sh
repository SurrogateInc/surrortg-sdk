#!/bin/bash
# run this to setup the rvr for the first time

# BEFORE RUNNING
# use 'sudo raspi-config' to enable serial communication
# or
# just add line 'enable_uart=1' to the end of '/boot/config.txt'
#
# and then reboot

# then run this


set -e
# clone the sdk if not already cloned
SCRIPT_PATH=$(dirname `which $0`)
cd $SCRIPT_PATH
SDK_DIR=./sphero-sdk-raspberrypi-python
if [ ! -d "$SDK_DIR" ]; then
    echo "SDK does not exist, cloning..."
    sudo apt-get -y install git
    git clone https://github.com/sphero-inc/sphero-sdk-raspberrypi-python.git
    cd sphero-sdk-raspberrypi-python
    git checkout 33645927d5a19796eea495e85e3f692d55e14b34
    git apply ../sphero.patch
    cd ..
fi
# run the official first-time-setup.sh
./sphero-sdk-raspberrypi-python/first-time-setup.sh


# then reboot again
