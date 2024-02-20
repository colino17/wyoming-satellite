# Tutorial with 16-LED Neopixel Ring

Create a voice satellite using a [Raspberry Pi Zero 3B+](https://www.raspberrypi.com/products/raspberry-pi-3-model-b-plus/) and a [16-LED Neopixel Ring](https://www.adafruit.com/product/1463).

This tutorial should work for almost any Raspberry Pi and USB microphone. Audio enhancements and local wake word detection may require a 64-bit operating system.

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
  python3
  python3-pip
  git \
  pigpio \
  python-pigpio \
  python3-pigpio \
  python3-venv
  libopenblas-dev
sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
sudo python3 -m pip install --force-reinstall adafruit-blinka
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
  -r requirements_neopixel.txt
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
    --mic-command 'arecord -D plughw:CARD=CMTECK,DEV=0 -q -r 16000 -c 1 -f S16_LE -t raw' \
    --snd-command 'aplay -D plughw:CARD=UACDemoV10,DEV=0 -q -r 22050 -c 1 -f S16_LE -t raw' \
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
