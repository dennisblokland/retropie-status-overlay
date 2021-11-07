from RPi import GPIO
class RotaryEncoder(object):
    """ A class to decode mechanical rotary encoder pulses.
        Ported to RPi.GPIO from the pigpio sample here:
        http://abyz.co.uk/rpi/pigpio/examples.html
    """
    def __init__(self, gpioA, gpioB, callback=None, gpioButton=None, buttonCallback=None):
        """ Instantiate the class. Takes three arguments: the two pin numbers to
            which the rotary encoder is connected, plus a callback to run when the
            switch is turned.
            The callback receives one argument: a `delta` that will be either 1 or -1.
            One of them means that the dial is being turned to the right; the other
            means that the dial is being turned to the left. I'll be damned if I know
            yet which one is which.
        """

        self._gpio_a = gpioA
        self._gpio_b = gpioB
        self._lev_a = 0
        self._lev_b = 0
        self._callback = callback
        self._last_gpio = None

        self._gpio_button = gpioButton
        self._button_callback = buttonCallback

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._gpio_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self._gpio_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.add_event_detect(self._gpio_a, GPIO.BOTH, self._gpio_input_rotation_callback)
        GPIO.add_event_detect(self._gpio_b, GPIO.BOTH, self._gpio_input_rotation_callback)

        if self._gpio_button:
            GPIO.setup(self._gpio_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self._gpio_button, GPIO.FALLING,
                                  self._gpio_input_button_callback, bouncetime=500)

    def __del__(self):
        GPIO.remove_event_detect(self._gpio_a)
        GPIO.remove_event_detect(self._gpio_b)
        if self._gpio_button:
            GPIO.remove_event_detect(self._gpio_button)
        GPIO.cleanup()

    def _gpio_input_button_callback(self, channel):
        self._button_callback(GPIO.input(channel))

    def _gpio_input_rotation_callback(self, channel):
        level = GPIO.input(channel)
        if channel == self._gpio_a:
            self._lev_a = level
        else:
            self._lev_b = level

        # Debounce
        if channel == self._last_gpio:
            return

        # When both inputs are at 1, we'll fire a callback. If A was the most
        # recent pin set high, it'll be forward, and if B was the most recent pin
        # set high, it'll be reverse.
        self._last_gpio = channel
        if channel == self._gpio_a and level == 1:
            if self._lev_b == 1:
                self._callback(1)
        elif channel == self._gpio_b and level == 1:
            if self._lev_a == 1:
                self._callback(-1)