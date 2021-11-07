import Volume
import RotaryEncoder
import logging
import queue
import subprocess
import sys
import threading
import signal


PM_GPIO_A = 23
PM_GPIO_B = 24
PM_GPIO_BUTTON = 12

class EventWrapper(object):
    """ This class encapsulate event, fire by knob action, and put volume delta into FIFO queue.
        This is necessary to ensure than every action is treat in order by main thread
    """
    def __init__(self):
        self._volume = Volume()
        self._queue = queue.Queue()
        self._event = threading.Event()
        self._encoder = RotaryEncoder(PM_GPIO_A, PM_GPIO_B, callback=self._on_turn,
                                      gpioButton=PM_GPIO_BUTTON,
                                      buttonCallback=self._on_press_toggle)
        logging.debug("Volume knob using pins %s (A) and %s (B)", PM_GPIO_A, PM_GPIO_B)
        if PM_GPIO_BUTTON != None:
            logging.debug("Volume mute button using pin %s", PM_GPIO_BUTTON)
        logging.debug("Initial volume: %s", self._volume.get_volume())

    def __del__(self):
        self._encoder.__del__()

    def _on_press_toggle(self):
        self._volume.toggle()
        logging.debug("Toggled mute to: %s", self._volume.is_muted)
        self._event.set()

    def _on_turn(self, delta):
        self._queue.put(delta)
        self._event.set()

    def wait_event(self):
        """ This method stop main thread until event fires """
        self._event.wait()

    def consume_queue(self):
        """ This method loop on queue and increase or decrease volume according to delta value """
        while not self._queue.empty():
            if self._queue.get() == 1:
                self._volume.up()
                logging.debug("Increase volume")
            else:
                logging.debug("Decrease volume")
                self._volume.down()

    def clear_event(self):
        """ Flush Events once queue is empty """
        self._event.clear()