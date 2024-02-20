####################
## IMPORT MODULES ##
####################
import argparse # ALLOWS THE USE OF COMMAND LINE ARGUMENTS
import asyncio # ALLOWS WRITING OF CONCURRENT CODE USING THE ASYNC/AWAIT SYNTAX
import logging # ALLOWS LOGGING
import time # PROVIDES TIME RELATED FUNCTIONS

import board # ALLOWS INTERACTION WOTH RPI GPIO PINS
import neopixel # PROVIDES NEOPIXEL LED FUNCTIONS

from functools import partial
from math import ceil
from typing import Tuple

from wyoming.asr import Transcript
from wyoming.event import Event
from wyoming.satellite import (
    SatelliteConnected,
    SatelliteDisconnected,
)
from wyoming.tts import Synthesize
from wyoming.snd import Played
from wyoming.server import AsyncEventHandler, AsyncServer
from wyoming.wake import Detection

###############
## VARIABLES ##
###############
# This section defines the GPIO pin (GPIO 21) that the Neopixel Ring is attached to. It also defines the number of LEDs in the ring (16).
pixels = neopixel.NeoPixel(board.D21, 16)
# These are the various colors (RGB) that can be used throughout. Max brightness white would be "255, 255, 255", however this seems exceedingly bright and also seems to get quite hot if set for more than a few seconds.
red = 50, 0, 0
blue = 0, 20, 50
green = 10, 50, 0
white = 50, 50, 50
purple = 40, 0, 50
yellow = 50, 20, 0
orange = 50, 10, 0
black = 0, 0, 0
# Variable used for logging purposes.
_LOGGER = logging.getLogger()

###################
## MAIN FUNCTION ##
###################
async def main() -> None:
# This handles the command line arguments that the program can use. In this case there are two possible arguments, "--uri" which is required and determines the server IP and port, and "--debug" which is an optional flag to increase the logging level.
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", required=True, help="unix:// or tcp://")
    parser.add_argument("--debug", action="store_true", help="Log DEBUG messages")
    args = parser.parse_args()
# This handles the logging level. By default basic logging is used, whereas adding the "--debug" argument invokes more verbose logs.
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    _LOGGER.debug(args)
    _LOGGER.info("Ready")
# This starts the Server with the URI defined in the systemd service (ex: "tcp://127.0.0.1:10500").
    server = AsyncServer.from_uri(args.uri)
    try:
        await server.run(partial(LEDsEventHandler, args))
    except KeyboardInterrupt:
        pass
    finally:
        pixels.fill((black))

###############################
## EVENT HANDLER FOR CLIENTS ##
###############################
class LEDsEventHandler(AsyncEventHandler):
    def __init__(
        self,
        cli_args: argparse.Namespace,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)

        self.cli_args = cli_args
        self.client_id = str(time.monotonic_ns())

        _LOGGER.debug("Client connected: %s", self.client_id)

# This function is used to add a 0.2 second delay.
    def sleepLED(self):
        time.sleep(0.25)
# This function can be called to turn off the LEDs.
    def clearLED(self):
        pixels.fill((black))
# This function will flash the LEDs twice using whatever color is set as "fc".
    def flashLED(self, fc):
        for i in range(2):
            pixels.fill((fc))
            self.sleepLED()
            self.clearLED()
            self.sleepLED()
# This function sets the LEDs to whatever solid color is set as "sc".
    def solidLED(self, sc):
        pixels.fill((sc))

    async def handle_event(self, event: Event) -> bool:
        _LOGGER.debug(event)
# This event is triggered when the wake word is detected.
        if Detection.is_type(event.type):
            self.flashLED(white)
# This event is triggered when the server has successfully transcribed the speech to text request.
        elif Transcript.is_type(event.type):
            self.flashLED(green)
# This event is triggered when the TTS service is responding.
        elif Synthesize.is_type(event.type):
            self.solidLED(blue)
# This event is triggered when the TTS response playback has ended.
        elif Played.is_type(event.type):
            self.clearLED()
# This event is triggered when the satellite connects to the main server.
        elif SatelliteConnected.is_type(event.type):
            self.flashLED(green)
            self.sleepLED()
            self.flashLED(green)
# This event is triggered when the satellite is unable to connect to the main server.
        elif SatelliteDisconnected.is_type(event.type):
            self.flashLED(orange)
            self.sleepLED()
            self.flashLED(orange)
            self.sleepLED()
            self.solidLED(red)
        return True

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
