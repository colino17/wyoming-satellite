# Tutorial with 16-LED Neopixel Ring

Create a voice satellite using a [Raspberry Pi Zero 3B+](https://www.raspberrypi.com/products/raspberry-pi-3-model-b-plus/) and a [16-LED Neopixel Ring](https://www.adafruit.com/product/1463).

Note that this tutorial uses a USB microphone and speaker and uses Pulseaudio rather than ALSA for the sound inputs/outputs, however it will also work with the appropriate ALSA substitutions. See the other tutorials for more standard ALSA setups.

## Install Raspberry Pi OS

Follow instructions to [install Raspberry Pi OS](https://www.raspberrypi.com/software/). Under "Choose OS", pick "Raspberry Pi OS (other)" and "Raspberry Pi OS (Legacy, **64-bit**) Lite".

When asked if you'd like to apply customization settings, choose "Edit Settings" and:

* Set a username/password
* Configure the wireless LAN
* Under the Services tab, enable SSH and use password authentication

Once flashed, you can insert your Micro SD card into the Pi and boot into Raspberry Pi OS.

## Install System Dependencies

Install system dependencies:

```sh
sudo apt-get update
sudo apt-get install --no-install-recommends  \
  pulseaudio \
  pulseaudio-utils \
  python3 \
  python3-pip \
  git \
  pigpio \
  python-pigpio \
  python3-pigpio \
  python3-venv \
  libopenblas-dev
sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
sudo python3 -m pip install --force-reinstall adafruit-blinka
```

## Configure Audio

Disable Pulseaudio service:

```sh
sudo systemctl --global disable pulseaudio.service pulseaudio.socket

```

Disable autospawn:

```sh
sudo nano /etc/pulse/client.conf
...
; autospawn = no
```

Edit Pulseaudio service:

```sh
sudo systemctl edit --force --full pulseaudio.service
```

```text
[Unit]
Description=PulseAudio system server

[Service]
Type=notify
ExecStart=pulseaudio --daemonize=no --system --realtime --log-target=journal

[Install]
WantedBy=multi-user.target
```

Enable Pulseaudio service and add user to group:

```sh
systemctl --system enable pulseaudio.service
systemctl --system start pulseaudio.service
sudo usermod -a -G pulse-access yourusername
```

Enable the appropriate output sink using the sink number and active port:

```sh
pactl list sinks
pactl set-sink-port 2 "analog-output"
paplay /usr/share/sounds/alsa/Front_Center.wav
pactl -- set-sink-volume 2 80%
```

Modify the Pulseaudio settings to add ducking at the bottom:

```sh
sudo nano /etc/pulse/system.pa
...
load-module module-role-ducking trigger_roles=announce,phone,notification,event ducking_roles=any_role volume=33%
```


## Configure Using Raspi-Config

Enable SPI in Raspi-Config under Interface Options:

```sh
sudo raspi-config
```

## Install Wyoming Satellite

Clone the repository:

```sh
git clone https://github.com/rhasspy/wyoming-satellite.git
```

Install the program:

```sh
cd wyoming-satellite/
python3 -m venv .venv
.venv/bin/pip3 install --upgrade pip
.venv/bin/pip3 install --upgrade wheel setuptools
.venv/bin/pip3 install \
  -f 'https://synesthesiam.github.io/prebuilt-apps/' \
  -r requirements.txt \
  -r requirements_audio_enhancement.txt \
  -r requirements_vad.txt
.venv/bin/pip3 install rpi_ws281x adafruit-circuitpython-neopixel
.venv/bin/pip3 install --force-reinstall adafruit-blinka
```

Test if installation was successful:

```sh
script/run --help
```

## Create Wyoming-Satellite Service

Create the service:

``` sh
sudo systemctl edit --force --full wyoming-satellite.service
```

Using the following template with the appropriate changes to user, execstart, name, [mic and sound devices](https://github.com/rhasspy/wyoming-satellite/blob/master/docs/tutorial_2mic.md#determine-audio-devices), wav file paths, and working directory:

```text
[Unit]
Description=Wyoming Satellite Service
Wants=network-online.target
After=network-online.target
Requires=wyoming-event.service

[Service]
Type=simple
User=username
Environment=XDG_RUNTIME_DIR=/run/user/1000
ExecStart=/home/pi/wyoming-satellite/script/run \
    --name 'Satellite Name' \
    --uri 'tcp://0.0.0.0:10700' \
    --mic-command 'parecord --property=media.role=phone --rate=16000 --channels=1 --format=s16le --raw --latency-msec 10' \
    --snd-command 'paplay --property=media.role=announce --rate=44100 --channels=1 --format=s16le --raw --latency-msec 10' \
    --snd-command-rate 44100 \
    --awake-wav /home/pi/wyoming-satellite/sounds/awake.wav \
    --done-wav /home/pi/wyoming-satellite/sounds/done.wav \
    --mic-noise-suppression 2 \
    --mic-auto-gain 5 \
    --vad \
    --event-uri 'tcp://127.0.0.1:10500'
WorkingDirectory=/home/pi/wyoming-satellite
Restart=always
RestartSec=1

[Install]
WantedBy=default.target
```

## Create Wyoming-Event Service

Create the service:

``` sh
sudo systemctl edit --force --full wyoming-event.service
```

Using the following template with the appropriate changes to execstart and working directory (note that I haven't found a workaround for the neopixel library requiring root access for the lights to work properly):

```text
[Unit]
Description=Wyoming Event Service

[Service]
Type=simple
User=root
ExecStart=/home/colin/wyoming-satellite/script/run_neopixelring16 \
    --uri 'tcp://127.0.0.1:10500'
WorkingDirectory=/home/colin/wyoming-satellite
Restart=always
RestartSec=1

[Install]
WantedBy=default.target
```

## Start and Enable Services

Start Services:

``` sh
sudo systemctl enable --now wyoming-event.service
sudo systemctl enable --now wyoming-satellite.service
```

Start Services:
``` sh
sudo systemctl start wyoming-event.service
sudo systemctl start wyoming-satellite.service
```

If any changes are needed to any services they can be done with the following commands:

```sh
sudo systemctl edit --force --full wyoming-event.service
sudo systemctl daemon-reload
sudo systemctl restart wyoming-event.service
```

Monitor logs with the following commands:

``` sh
journalctl -u wyoming-satellite.service -f
journalctl -u wyoming-event.service -f
```
