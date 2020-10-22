# Setup:

run
```
sudo systemctl disable hciuart
sudo apt-get update && sudo apt-get upgrade
sudo apt-get install libjpeg-dev libtiff5-dev libjasper-dev libpng-dev libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev libatlas-base-dev gfortran python3-dev libilmbase-dev libopenexr-dev libgstreamer1.0-dev libhdf5-dev libhdf5-serial-dev libqtgui4 libqt4-test -y
```
# Rest is probably not used
# Before usage: Prepare /dev/ttyAMA0

If the Pi has built-in Bluetooth (Pi 3, Pi 3+, Pi 4, Pi zero W) disable Bluetooth to free up the PL011 UART.

The following is from /boot/overlays/README.

```
Name:   disable-bt
Info:   Disable onboard Bluetooth on Pi 3B, 3B+, 3A+, 4B and Zero W, restoring
        UART0/ttyAMA0 over GPIOs 14 & 15.
        N.B. To disable the systemd service that initialises the modem so it
        doesn't use the UART, use 'sudo systemctl disable hciuart'.
Load:   dtoverlay=disable-bt
```

sudo systemctl disable hciuart
sudo nano /boot/config.txt

Add `dtoverlay=disable-bt` as the last line of config.txt. Save and exit.

Turn off the login shell on /dev/ttyAMA0. This is necessary even if the Pi does not have Bluetooth.

`sudo raspi-config`

    Select Interfacing Options.
    Select P6 Serial.
    Disable the login shell.
    Enable the serial interface.
    Interfacing > Enable the camera interface
    Exit raspi-config


`sudo reboot`


Maybe required also:
`sudo apt install jstest-gtk python3 python3-pip python3-serial python3-gpiozero python3-mido`

Fix opencv issues:
https://www.pyimagesearch.com/2019/09/16/install-opencv-4-on-raspberry-pi-4-and-raspbian-buster/  
https://github.com/EdjeElectronics/TensorFlow-Object-Detection-on-the-Raspberry-Pi/issues/18  
pip install opencv-contrib-python==4.1.0.25  
