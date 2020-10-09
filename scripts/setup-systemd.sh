if [ ! -d "/usr/lib/systemd/system" ]; then
    sudo mkdir /usr/lib/systemd/system
fi
SCRIPT_PATH=$(dirname `which $0`)
echo "copying controller-rpi.service to /usr/lib/systemd/system/controller.service"
sudo cp $SCRIPT_PATH/controller-rpi.service /usr/lib/systemd/system/controller.service
echo "restarting systemd daemon"
sudo systemctl daemon-reload
echo "enabling controller unit to start after reboot"
sudo systemctl enable controller
echo "restarting controller unit"
sudo systemctl restart controller
echo "controller unit status"
sudo systemctl status controller