#!/bin/bash
sudo apt-get update && sudo apt-get upgrade
sudo systemctl disable hciuart
sudo apt-get install -y\
    libjpeg-dev libtiff5-dev libjasper-dev libpng-dev libavcodec-dev libavformat-dev \
    libswscale-dev libv4l-dev libxvidcore-dev libx264-dev libatlas-base-dev gfortran \
    python3-dev libilmbase-dev libopenexr-dev libgstreamer1.0-dev libhdf5-dev \
    libhdf5-serial-dev libqtgui4 libqt4-test