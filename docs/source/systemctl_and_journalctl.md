# Linux tools help

As our streamer and controller are ran as systemd modules. You will need to use special tools to control them and readout the logs.

## systemctl - systemd control

```
sudo systemctl <command> srtg/controller
```

-   enable - enables systemd module to be ran always after boot
-   start - starts the systemd unit
-   stop - stops the systemd unit
-   restart - stops and starts the systemd unit
-   status - shows the status of the systemd unit

## journalctl - logs

to open the whole log file, starting from the beginning:

```
sudo journalctl -u srtg/controller
```

to open the log file and follow logs at real-time run

```
sudo journalctl -fu srtg/controller
```

you can also use grep to print out only the specific lines you are interested in

```
sudo journalctl -fu srtg/controller | grep "<string to find>"
```
