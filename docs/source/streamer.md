# Streamer

The srtg-streamer has various different configuration options and there are
multiple advanced setups one can build. This section explains some of the more
complex configurations. Installation and basic usage is covered in
[Getting Started](getting_started.html#installing-surrogate-streamer).

## Audio

On this page you will find information on how audio works in the
surrogate streamer, how to enable and configure audio, as well as some
troubleshooting tips.

If a feature is missing, you can always let us know. However, as the audio
configuration relies heavily on ALSA, you can also try to implement your
own asound.conf configuration.
For more details, check out [Custom audio configuration (advanced).](#custom-audio-configuration)

This page is a work in progress, and any feedback is greatly appreciated!
Ping Henri(dev) in Discord for feedback and questions.

- [Enabling audio](#enabling-audio)
- [Choosing audio capture device](#choosing-audio-capture-device)
- [Disabling asound.conf generation](#disabling-asound-conf-generation)
- [Audio processing](#audio-processing)
- [Example audio config](#example-audio-config)
- [Troubleshooting](#troubleshooting)
- [Custom audio configuration (advanced)](#custom-audio-configuration)

### Enabling audio

To enable audio, you must add the following to the /etc/srtg/srtg.toml
configuration file:

```
[[sources]]
kind = "audio"
label = "main"
```

The default audio capture device chosen by ALSA is used, unless a device is
specified in the srtg.toml file. To choose a specific audio capture device,
see [choosing audio capture device](#choosing-audio-capture-device).
If you are having issues see [Troubleshooting](#troubleshooting).
For optional audio processing parameters, see [Audio processing](#audio-processing).

### Choosing audio capture device

<strong>WARNING:</strong> this will overwrite your /etc/asound.conf file.
A backup will be saved, however.

If you have multiple audio capture devices (aka "cards" in alsa parlance)
and wish to specify which one is used, you can find a list of available
devices with the following command:

```
sudo arecord --list-devices
```

The output will look something like this:

```
**** List of CAPTURE Hardware Devices ****
card 1: webcam [Full HD webcam], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
card 2: C925e [Logitech Webcam C925e], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
```

To choose the second device on the list, you would add the string after
"card 2:" to the config file:

```
[sources.audio_params]
audio_capture_dev_name = "C925e"
```

Only one audio capture device can be specified at a time.

<strong>Beta feature:</strong> If you have an audio capture card with multiple
devices, you can specify which device to use by also adding the subdevice
number to the config file:

```
[sources.audio_params]
audio_capture_dev_name = "C925e"
audio_capture_dev_idx = 0
```

### Disabling asound conf generation

Add the following on its own line to /etc/asound.conf to disable automatic
generation of the asound.conf file.

```
# Surrogate ignore
```

This can cause issues with audio unless you make sure the asound.conf stays
correct for your system configuration.

### Audio processing

There are optional audio parameters which can be used to enable additional audio
processing in WebRTC. To enable one of the parameters, add the following under
[sources.audio_params] in the srtg.toml configuration file.

```
parameter_name_here = true
```

All the parameters are options exposed by WebRTC. Unfortunately we can't provide
more detailed documentation on the options at this time.

Here is the complete list of the parameters:

- echo_cancellation
- auto_gain_control
- highpass_filter
- noise_suppression
- typing_detection
- experimental_agc
- experimental_ns
- residual_echo_detector
- tx_agc_limiter

Note that most of these are presumably meant to improve the audio quality of
a microphone, and will likely only decrease audio quality when used with line
input. You are free to experiment with them, however.

### Example audio config

This is an example of what the audio part of an srtg.toml file may
look like.

```
# Audio, optional. This will enable audio if you have an audio capture device
# connected.
# The default alsa device will be used, unless a specific device is chosen with
# the additional audio parameters below.
[[sources]]
kind = "audio"
label = "main"

# Optional parameter to set the default audio capture device. NOTE: only one
# audio capture device can be specified at a time. The [[sources]] audio
# parameter must also be set.
[sources.audio_params]
audio_capture_dev_name = "C925e"
# Optional - default value is 0
audio_capture_dev_idx = 0
```

### Troubleshooting

<strong>Restarting everything is always a good thing to try.</strong>

Having issues with audio? <strong>If you are not getting audio at all</strong>,
please check the following:

- The audio source is properly connected

- The audio source is actually generating sound

- The audio source is not muted (plugging in a 3.5 mm connector can mute other
  outputs on some devices)

- You have enabled audio in srtg.toml

    - If multiple audio capture devices are connected, make sure you have
      specified the device to use in srtg.toml

- The audio capture device shows up in arecord. See
  [below](#available-audio-capture-devices)

- The audio capture device is getting audio. See
  [how to record an audio sample](#record-an-audio-sample)

- The /etc/asound.conf file is getting generated correctly. See
  [example asound conf file](#example-asound-conf-file)

- Make sure automatic generation of asound.conf is not disabled. See
  [disabling asound.conf generation](#disabling-asound-conf-generation)

<strong> If you are getting audio, but the quality is bad</strong>, try the
following:

- Make sure everything is connected properly
- If possible, play around with the volume levels of the source device and
    the audio capture card. [How to change capture volume.](#changing-volume)
- Try a different USB slot
- Try disconnecting other USB devices
- Try a different capture device

Unfortunately, getting decent quality audio with a raspberry pi can be a bit hit
and miss.

<strong> Known issues:</strong>

- The quality of the audio coming through the streamer is not as good as the
  source audio -- this is due to the processing and encoding WebRTC does on the
  audio, as well as the bitrate of the audio. Improving the audio quality is
  still a work in progress.
- Delay in the watcher stream audio is also a known issue.

Next we introduce a collection of commands you can use to get information about
the audio capture devices you have connected to your device, and to troubleshoot
audio issues.

#### Available audio capture devices

To see what audio capture devices are available, run:

```
sudo arecord --list-devices
```

The output will look something like this:

```
**** List of CAPTURE Hardware Devices ****
card 1: webcam [Full HD webcam], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
card 2: C925e [Logitech Webcam C925e], device 0: USB Audio [USB Audio]
  Subdevices: 1/1
  Subdevice #0: subdevice #0
```

The name after the card number, for example 'webcam' and 'C925e' in the output
above, is the device name used in the srtg.toml configuration file to set the
audio capture device.

#### Audio capture device parameters

Use this command to list the hardware parameters of an audio capture device.
The parameters include sampling rate, format, and channel count, among others.

Note that you must change DEVICE_NAME to the name or index of the device you
wish to investigate. The name and index can be found with
[arecord --list-devices](#available-audio-capture-devices).

```
sudo arecord -D hw:DEVICE_NAME,0 --dump-hw-params
```

#### Record an audio sample

Arecord can be used to record an audio sample from an audio capture device.
If you are having trouble with audio, you can use this command to test whether
the audio capture device is receiving audio at all.

The -V flag enables a VU meter, which should show the volume level in the
terminal, telling you whether the device is receiving audio or not.

Note that you must first get the device hardware parameters with
[arecord --dump-hw-params](#audio-capture-device-parameters).

```
sudo arecord -V stereo -D hw:DEVICE_NAME,0 -r RATE -f FORMAT -c CHANNELS audio_record.wav
```

To listen to the sample, you may either play it through the raspberry pi 3.5 mm
jack using aplay, or copy it to another computer (using scp, for example)
and play it from there.

#### Changing volume

To change the capture volume of an audio capture device, you can use alsamixer.

Run:

```
sudo alsamixer
```

Then do the following:

1. press F6 to choose the correct audio capture device
2. press F4 to choose capture
3. you can now change the volume

This way you can try to find the best audio quality by varying the switch audio
output volume and the alsamixer volume.

Capture volume control may not be available by default for digital inputs.
If you run into this issue, please let us know! You can also create your custom
asound.conf to hopefully enable volume control for any device by replacing your
/etc/asound.conf with the one below (NOTE: You must change the device name and
rate to correct values for your audio capture device):

<details>
  <summary><strong><strong>Beta feature:
  </strong> Asound.conf with volume control</strong></summary>

```
# This file was generated by Surrogate Streamer.
# If you wish to disable the file generation,
# add the following on its own line (without the quotes):"# Surrogate ignore"
# Surrogate ignore
pcm.device{
        rate 48000
        type hw
        card MS2109
        device 0
}

pcm.softvol {
    type softvol
    slave {
        pcm "dsnooper"
    }
    control {
        name "MS2109"
        card MS2109
    }
    min_dB -5.0
    max_dB 20.0
    resolution 6
}

pcm.dsnooper{
    type dsnoop
    ipc_key 2048
    ipc_perm 0666
    slave.pcm "device"
}
pcm.!default{
    type plug
    slave.pcm "softvol"
}
```

</details>
<br/>

#### Example asound conf file

An example of what /etc/asound.conf generated by the surrogate streamer should
look like. The rate and card should match the audio capture device you wish to
use.

```
# This file was generated by Surrogate Streamer.
# If you wish to disable the file generation,
# add the following on its own line (without the quotes):"# Surrogate ignore"
pcm.device{
        rate 44100
        type hw
        card Headset
        device 0
}

pcm.dsnooper{
    type dsnoop
    ipc_key 2048

    ipc_perm 0666
    slave.pcm "device"
}
pcm.!default{
    type plug
    slave.pcm "dsnooper"

```

### Custom audio configuration

Warning: this requires tinkering with the asound.conf configuration file, which
can be tricky. You will have to do the required research yourself.

The audio source of the streamer and the watcher stream is the default audio
device of ALSA. All the audio device configuration is eventually done through
the automatically generated /etc/asound.conf file. Thus, if you want to have a
more complex audio system and are prepared to do the work, you are free to
create your own asound.conf file. To disable the automatic generation of the
asound.conf file, see
[Disabling asound.conf generation.](#disabling-asound-conf-generation)
