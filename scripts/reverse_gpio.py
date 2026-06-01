import sys
import threading
import time

from PyQt5.QtCore import QObject, QTimer, pyqtSignal


REVERSE_PIN = 17
REVERSE_POLL_MS = 100
REVERSE_DEBOUNCE_S = 0.15


class ReverseGearMonitor(QObject):
    reverse_changed = pyqtSignal(bool)

    def __init__(
        self,
        mock=False,
        initial_reverse=False,
        reverse_pin=REVERSE_PIN,
        poll_ms=REVERSE_POLL_MS,
        debounce_s=REVERSE_DEBOUNCE_S,
    ):
        super().__init__()
        self.mock = mock
        self.reverse_pin = reverse_pin
        self.poll_ms = poll_ms
        self.debounce_s = debounce_s
        self.GPIO = None
        self.is_reverse = initial_reverse
        self.pending_reverse = None
        self.pending_since = 0.0
        self.stdin_thread = None

        self.timer = QTimer(self)
        self.timer.setObjectName("reverse gear poll timer")
        self.timer.timeout.connect(self.poll)

    def start(self):
        self.reverse_changed.emit(self.is_reverse)

        if self.mock:
            self.start_mock_stdin()
            return

        import RPi.GPIO as GPIO

        self.GPIO = GPIO
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setup(self.reverse_pin, self.GPIO.IN, pull_up_down=self.GPIO.PUD_UP)
        self.is_reverse = self.read_reverse()
        self.reverse_changed.emit(self.is_reverse)
        self.timer.start(self.poll_ms)

    def stop(self):
        self.timer.stop()
        if self.GPIO:
            self.GPIO.cleanup(self.reverse_pin)
            self.GPIO = None

    def poll(self):
        sampled_reverse = self.read_reverse()
        if sampled_reverse == self.is_reverse:
            self.pending_reverse = None
            return

        now = time.monotonic()
        if sampled_reverse != self.pending_reverse:
            self.pending_reverse = sampled_reverse
            self.pending_since = now
            return

        if now - self.pending_since < self.debounce_s:
            return

        self.pending_reverse = None
        self.is_reverse = sampled_reverse
        self.reverse_changed.emit(self.is_reverse)

    def read_reverse(self):
        if self.mock:
            return self.is_reverse
        return self.GPIO.input(self.reverse_pin) == self.GPIO.LOW

    def start_mock_stdin(self):
        self.stdin_thread = threading.Thread(
            target=self.stdin_loop,
            name="mock reverse stdin",
            daemon=True,
        )
        self.stdin_thread.start()
        print("Mock reverse input: type R then Enter for reverse, N then Enter for normal.")

    def stdin_loop(self):
        while True:
            line = sys.stdin.readline()
            if line == "":
                return
            self.handle_mock_command(line)

    def handle_mock_command(self, line):
        command = line.strip().upper()
        if command == "R":
            self.set_mock_reverse(True)
        elif command in ("N", "D", "0"):
            self.set_mock_reverse(False)

    def set_mock_reverse(self, is_reverse):
        if not self.mock or is_reverse == self.is_reverse:
            return
        self.is_reverse = is_reverse
        if self.is_reverse:
            print("Mock reverse: ACTIVE")
        else:
            print("Mock reverse: INACTIVE")
        self.reverse_changed.emit(self.is_reverse)
