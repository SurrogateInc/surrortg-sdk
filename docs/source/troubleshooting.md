# Troubleshooting

You should always read the logs of the streamer and controller modules to determine what is the issue you are facing. You can refer to [info-page](systemctl_and_journalctl) to see how to access the logs using journalctl tool.

## General troubleshootin

The streamer and controller modules share the same configuration file when used on the same device. Therefore, there are some settings and potential issues that they share

## Streamer troubleshooting

Most common streamer issues are related to the camera and its configuration.

if you are using raspberry pi camera (flat CSI cable one), <strong>Make sure that you have enabled the camera interface from raspi-config</strong>

## Controller trouble shooting
