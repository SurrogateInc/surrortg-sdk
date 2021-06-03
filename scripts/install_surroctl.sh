#!/bin/bash
python3 -m pip install click toml
sudo python3 -m pip install click toml
sudo ln -sf /home/pi/surrortg-sdk/scripts/surroctl.py /usr/local/bin/surroctl
printf "\n\n"
surroctl --help
printf "\nsurroctl installed\n"