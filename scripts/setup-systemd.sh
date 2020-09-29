if [ ! -d "/usr/lib/systemd/system" ]; then
    sudo mkdir /usr/lib/systemd/system
fi
echo "copying controller-rpi.service to /usr/lib/systemd/system/controller.service"
sudo cp controller-rpi.service /usr/lib/systemd/system/controller.service
echo "restarting systemd daemon"
sudo systemctl daemon-reload
echo "restarting controller unit"
sudo systemctl restart controller
echo "controller unit status"
sudo systemctl status controller