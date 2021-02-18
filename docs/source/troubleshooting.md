# Troubleshooting

You should always read the logs of the streamer and controller modules to determine
what is the issue you are facing. You will need to use special tools to
[control them](#Restarting-controller-and-streamer) and [readout the logs](#Reading-the-logs).

The streamer and controller modules share the same configuration file when used
on the same device. Therefore, there are some settings and potential issues that
[they share](#Most-common-issues).

## Restarting controller and streamer

```
sudo systemctl <command> <srtg or controller or srtg-watcherstream>
```

- enable - enables systemd module to be ran always after boot
- disable - disabled systemd module to be ran after boot
- start - starts the systemd unit
- stop - stops the systemd unit
- restart - stops and starts the systemd unit
- status - shows the status of the systemd unit

## Reading the logs

to open the whole log file, starting from the beginning:

```
sudo journalctl -u <srtg or controller or srtg-watcherstream>
```

to open the log file and follow logs at real-time run

```
sudo journalctl -fu <srtg or controller or srtg-watcherstream>
```

you can also use grep to print out only the specific lines you are interested in

```
sudo journalctl -fu <srtg or controller or srtg-watcherstream> | grep "<string to find>"
```

## Most common issues

Most common issues are fairly simple and can usually be seen from the logs quickly.

- Wrong or missing token
- Controller/streamer not restarted after changes to the configuration file
- Mismatching controller/streamer IDs between admin settings and configuration file

## Streamer troubleshooting

Most common streamer issues are related to the camera and its configuration.

if you are using raspberry pi camera (flat CSI cable one),
**Make sure that you have enabled the camera interface from raspi-config** and
that your configuration file is using `rpi_csi` type in video sources.

Insufficient GPU memory can cause issues with the streamer. To increase GPU memory:

`sudo raspi-config` -> `advanced options` -> `memory split` -> 256 (or 512 if your
Pi has 1GB or more RAM available) or by editing `/boot/config.txt` -> `gpu_mem=256`.
Reboot the system after.

## Audio troubleshooting

See [the troubleshooting section on the audio page](streamer.html#troubleshooting).

## Controller troubleshooting

If you are running your controller code as both systemd unit and sometimes directly,
it means you will have 2 instances running at the same time. This will cause an
error of duplicate controller IDs on the server. If you are doing development and
running the controller directly on your terminal, stop the controller systemd unit
while doing that `sudo systemctl stop controller`, and remember to start it after
you want to use it again.
