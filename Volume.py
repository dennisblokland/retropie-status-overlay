import subprocess
import sys
import threading
import signal
import logging
import queue

VOLUME_MIXER_CONTROL_ID = "Digital"
VOLUME_MIN = 10
VOLUME_MAX = 96
VOLUME_INCREMENT = 5

class Volume(object):
    """ A wrapper API for interacting with the volume settings on the RPi. """

    def __init__(self):
        self._min = VOLUME_MIN
        self._max = VOLUME_MAX
        self._increment = VOLUME_INCREMENT
        self._last_volume = VOLUME_MIN
        self._volume = VOLUME_MIN
        self._is_muted = False
        self._sync()

    def up(self):
        """ Increases the volume by one increment. """
        return self._set_volume(self._volume + self._increment)

    def down(self):
        """ Decreases the volume by one increment. """
        return self._set_volume(self._volume - self._increment)

    def toggle(self):
        """ Toggles muting between on and off. """
        if self._is_muted:
            cmd = "set '{}' unmute".format(VOLUME_MIXER_CONTROL_ID)
        else:
            # We're about to mute ourselves, so we should remember the last volume
            # value we had because we'll want to restore it later.
            self._last_volume = self._volume
            cmd = "set '{}' mute".format(VOLUME_MIXER_CONTROL_ID)
        self._sync(self._amixer(cmd))
        if not self._is_muted:
            # If we just unmuted ourselves, we should restore whatever volume we
            # had previously.
            self._set_volume(self._last_volume)
        return self._is_muted

    def get_volume(self):
        """ Volume accessor """
        return self._volume

    def _set_volume(self, val):
        """ Sets volume to a specific value. """
        self._volume = self._constrain(val)
        self._sync(self._amixer("set '{}' unmute {}%".format(VOLUME_MIXER_CONTROL_ID, self._volume)))
        return self._volume

    # Ensures the volume value is between our minimum and maximum.
    def _constrain(self, val):
        if val < self._min:
            return self._min
        if val > self._max:
            return self._max
        return val

    def _amixer(self, cmd):
        """ Execute bash command to set up sound level on linux environement.
            Return output of command
        """
        process = subprocess.Popen("amixer {}".format(cmd), shell=True, stdout=subprocess.PIPE)
        code = process.wait()
        if code != 0:
            #Error : unable to setup volume level / mute - unmute
            sys.exit(0)
        return process.stdout

    def _sync(self, output=None):
        """ Read the output of `amixer` to get the system volume and mute state.
            This is designed not to do much work because it'll get called with every
            click of the knob in either direction, which is why we're doing simple
            string scanning and not regular expressions.
        """
        if output is None:
            output = self._amixer("get '{}'".format(VOLUME_MIXER_CONTROL_ID))
        lines = output.readlines()
        #if STACK_TRACE:
            #strings = [line.decode('utf8') for line in lines]
            #print "OUTPUT:"
            #print "".join(strings)
        last = lines[-1].decode('utf-8')

        # The last line of output will have two values in square brackets. The
        # first will be the volume (e.g., "[95%]") and the second will be the
        # mute state ("[off]" or "[on]").
        index_1 = last.rindex('[') + 1
        index_2 = last.rindex(']')

        self.is_muted = last[index_1:index_2] == 'off'

        index_1 = last.index('[') + 1
        index_2 = last.index('%')
        # In between these two will be the percentage value.
        pct = last[index_1:index_2]

        self._volume = int(pct)
        logging.debug("Volume is now at %s", self._volume)
