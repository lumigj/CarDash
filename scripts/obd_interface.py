#!/usr/bin/env python3

import argparse
from pathlib import Path
import signal
import sys
import threading
import time

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import obd
from PyQt5.QtCore import Qt, QRectF, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from dashboard.camera_view import CameraView
from obd_logger import connect, get_commands, simple_value
from scripts.reverse_gpio import ReverseGearMonitor


is_mock = False
BACKGROUND_COLOR = "#030712"
BASE_WINDOW_WIDTH = 1280
BASE_WINDOW_HEIGHT = 720
DEFAULT_PORTS = [
    "/dev/ttyUSB0",
    "/dev/ttyUSB1",
]

UI_REFRESH_MS = 100
RETRY_INTERVAL_S = 5.0
ALL_COMMANDS = {
    # Value is the minimum seconds between polls. 0.0 means poll every loop.
    # Comment out a command here to stop polling it and hide its right-side widget.
    "TIMING_ADVANCE": 0.0,
    "THROTTLE_POS": 0.0,
    "ENGINE_LOAD": 0.0,
    "INTAKE_PRESSURE": 0.3,
    "INTAKE_TEMP": 15.0,
    "COOLANT_TEMP": 15.0,
    "STATUS": 20.0,
    "SHORT_FUEL_TRIM_1": 0.3,
    "LONG_FUEL_TRIM_1": 36.0,
}
GAUGE_RANGES = {
    "TIMING_ADVANCE": (-20, 40),
    "THROTTLE_POS": (0, 100),
    "ENGINE_LOAD": (0, 100),
    "COOLANT_TEMP": (40, 120),
}

MOCK_VALUES = {
    "RPM": "6024 revolutions_per_minute",
    "SPEED": "196 kilometer_per_hour",
    "TIMING_ADVANCE": "2.0 degree",
    "COOLANT_TEMP": "89 degree_Celsius",
    "THROTTLE_POS": "55 percent",
    "ENGINE_LOAD": "38 percent",
    "INTAKE_TEMP": "70 degree_Celsius",
    "INTAKE_PRESSURE": "48 kilopascal",
    "STATUS": "MIL=False DTC=0 ignition=spark",
    "SHORT_FUEL_TRIM_1": "5.46875 percent",
    "LONG_FUEL_TRIM_1": "9.375 percent",
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock dashboard and camera.",
    )
    parser.add_argument("--port", help="ELM327 port, for example /dev/ttyUSB0")
    parser.add_argument("--mockfull", action="store_true")
    args = parser.parse_args()
    if args.mock and args.mockfull:
        parser.error("--mock and --mockfull cannot be used together")
    if args.mock and args.port:
        parser.error("--mock cannot be used with --port")
    if args.mockfull and args.port:
        parser.error("--mockfull cannot be used with --port")
    return args


def compact_value(name, value):
    text = str(value)
    if name == "STATUS" and text != "-":
        return text.replace("MIL=False", "MIL OFF").replace("MIL=True", "MIL ON").replace(" ignition=", " ")

    return (
        text.replace(" revolutions_per_minute", " rpm")
        .replace(" kilometer_per_hour", " km/h")
        .replace(" degree_Celsius", " C")
        .replace(" kilopascal", " kPa")
        .replace(" percent", "%")
        .replace(" degree", " deg")
    )


def display_name(name):
    names = {
        "TIMING_ADVANCE": "TIMING",
        "THROTTLE_POS": "THROTTLE",
        "ENGINE_LOAD": "LOAD",
        "INTAKE_PRESSURE": "INTAKE kPa",
        "INTAKE_TEMP": "INTAKE C",
        "COOLANT_TEMP": "COOLANT",
        "SHORT_FUEL_TRIM_1": "ST FUEL",
        "LONG_FUEL_TRIM_1": "LT FUEL",
    }
    return names.get(name, name.replace("_", " "))


def numeric_value(value):
    text = str(value)
    if text == "-":
        return 0
    return round(float(text.split(" ", 1)[0]))


def gauge_value(name, value):
    if str(value) == "-":
        return 0

    minimum, maximum = GAUGE_RANGES[name]
    number = numeric_value(value)
    return max(minimum, min(maximum, number))


def fit_16_9_size(width, height):
    fitted_height = round(width * 9 / 16)
    if fitted_height <= height:
        return width, fitted_height
    return round(height * 16 / 9), height


def scaled(value, scale):
    return max(1, round(value * scale))


class QueryThread(QThread):
    values_changed = pyqtSignal(dict)
    status_changed = pyqtSignal(str)

    def __init__(self, port):
        super().__init__()
        self.setObjectName("query thread")
        self.port = port
        self.connection = None
        self.commands = {}
        self.next_polls = {
            name: 0.0
            for name in ALL_COMMANDS
        }
        self.running = True

    def run(self):
        threading.current_thread().name = "query thread"

        if is_mock:
            self.status_changed.emit("MOCK DATA")
            self.poll_loop()
            return

        retry_at = 0
        while self.running:
            now = time.monotonic()
            if now >= retry_at:
                if self.connect_live():
                    self.poll_loop()
                retry_at = time.monotonic() + RETRY_INTERVAL_S
            else:
                remaining = int(retry_at - now) + 1
                self.status_changed.emit("CANNOT CONNECT OBD - RETRY IN %dS" % remaining)
            self.msleep(100)

    def poll_loop(self):
        while self.running:
            names = self.due_commands(time.monotonic())
            if names and not self.poll(names):
                return

            self.msleep(1)

    def due_commands(self, now):
        names = []
        for name, interval in ALL_COMMANDS.items():
            if now >= self.next_polls[name]:
                names.append(name)
                self.next_polls[name] = now + interval
        return names

    def stop(self):
        self.running = False
        self.close_connection()

    def connect_live(self):
        ports = [self.port] if self.port else DEFAULT_PORTS
        errors = []

        self.status_changed.emit("CONNECTING OBD")
        for port in ports:
            if not self.running:
                return False
            try:
                self.connect_port(port)
                self.status_changed.emit("LIVE %s" % port)
                return True
            except Exception as error:
                errors.append(str(error))

        self.close_connection()
        self.values_changed.emit({name: "-" for name in ALL_COMMANDS})
        self.status_changed.emit(
            "CANNOT CONNECT OBD - RETRY IN %dS" % int(RETRY_INTERVAL_S)
        )
        print("\n".join(errors))
        return False

    def connect_port(self, port):
        self.close_connection()
        self.connection = connect(port)
        if self.connection.status() == obd.OBDStatus.NOT_CONNECTED:
            raise RuntimeError("%s: could not connect to ELM327" % port)

        self.commands = {
            cmd.name: cmd
            for cmd in get_commands(self.connection, list(ALL_COMMANDS))
        }
        if not self.commands:
            raise RuntimeError("%s: no dashboard OBD commands supported" % port)

        for name in ALL_COMMANDS:
            cmd = self.commands.get(name)
            if cmd:
                response = self.connection.query(cmd)
                if not response.is_null():
                    return

        raise RuntimeError("%s: connected but no dashboard values returned" % port)

    def close_connection(self):
        if self.connection:
            self.connection.close()
        self.connection = None
        self.commands = {}
        self.next_polls = {
            name: 0.0
            for name in ALL_COMMANDS
        }

    def poll(self, names):
        if is_mock:
            values = {name: MOCK_VALUES.get(name, "-") for name in names}
        else:
            values = {}
            try:
                for name in names:
                    cmd = self.commands.get(name)
                    if cmd:
                        values[name] = simple_value(self.connection.query(cmd))
            except Exception as error:
                self.close_connection()
                self.values_changed.emit({name: "-" for name in ALL_COMMANDS})
                self.status_changed.emit("OBD LOST - RETRY IN 10S")
                print(error)
                return False

        if values:
            self.values_changed.emit(values)
        return True


class GaugeBar(QWidget):
    def __init__(self, name, scale):
        super().__init__()
        self.name = name
        self.scale = scale
        self.value = 0
        self.setFixedHeight(scaled(24, scale))

    def set_value(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(self.rect()).adjusted(0, 0, -1, -1)
        radius = scaled(4, self.scale)
        painter.setPen(QColor("#334155"))
        painter.setBrush(QColor("#111827"))
        painter.drawRoundedRect(rect, radius, radius)

        value = self.value
        minimum, maximum = GAUGE_RANGES[self.name]

        if self.name == "TIMING_ADVANCE":
            center = rect.left() + rect.width() / 2
            half_width = rect.width() / 2
            if value < 0:
                width = abs(value) / abs(minimum) * half_width
                fill = QRectF(center - width, rect.top(), width, rect.height())
                color = QColor("#ef4444")
            else:
                width = value / maximum * half_width
                fill = QRectF(center, rect.top(), width, rect.height())
                color = QColor("#22c55e")

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(fill, radius, radius)
            painter.setPen(QColor("#64748b"))
            painter.drawLine(round(center), round(rect.top()), round(center), round(rect.bottom()))
        else:
            width = (value - minimum) / (maximum - minimum) * rect.width()
            fill = QRectF(rect.left(), rect.top(), width, rect.height())
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.fill_color(value))
            painter.drawRoundedRect(fill, radius, radius)

    def fill_color(self, value):
        if self.name != "COOLANT_TEMP":
            return QColor("#22c55e")
        if value >= 105:
            return QColor("#ef4444")
        if value >= 95:
            return QColor("#eab308")
        return QColor("#22c55e")


class GaugeMetric(QFrame):
    def __init__(self, name, scale):
        super().__init__()
        self.name = name
        self.setMinimumSize(scaled(240, scale), scaled(150, scale))
        self.setStyleSheet(
            "QFrame { background-color: #0b111b; border: 1px solid #243041; "
            "border-radius: %dpx; }"
            "QLabel { background: transparent; border: 0; }" % scaled(12, scale)
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(
            scaled(18, scale),
            scaled(15, scale),
            scaled(18, scale),
            scaled(16, scale),
        )
        layout.setSpacing(scaled(12, scale))

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(scaled(8, scale))

        title = QLabel(display_name(name))
        title.setStyleSheet(
            "font-size: %dpx; color: #94a3b8; font-weight: 600;" % scaled(18, scale)
        )
        header.addWidget(title)

        self.value_label = QLabel("-")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.value_label.setStyleSheet(
            "font-size: %dpx; color: #f8fafc; font-weight: bold;" % scaled(30, scale)
        )
        header.addWidget(self.value_label, 1)
        layout.addLayout(header)

        layout.addStretch(1)
        self.bar = GaugeBar(name, scale)
        layout.addWidget(self.bar)
        self.setLayout(layout)

    def set_value(self, value):
        value = gauge_value(self.name, value)
        self.value_label.setText(self.display_text(value))
        self.bar.set_value(value)

    def display_text(self, value):
        if self.name == "TIMING_ADVANCE":
            return "%.1f deg" % value
        if self.name == "COOLANT_TEMP":
            return "%d C" % round(value)
        return "%d%%" % round(value)


class InfoMetric(QFrame):
    def __init__(self, name, scale):
        super().__init__()
        self.name = name
        self.setMinimumSize(scaled(240, scale), scaled(150, scale))
        self.setStyleSheet(
            "QFrame { background-color: #0b111b; border: 1px solid #243041; "
            "border-radius: %dpx; }"
            "QLabel { background: transparent; border: 0; }" % scaled(12, scale)
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(
            scaled(18, scale),
            scaled(15, scale),
            scaled(18, scale),
            scaled(16, scale),
        )
        layout.setSpacing(scaled(8, scale))

        title = QLabel(display_name(name))
        title.setStyleSheet(
            "font-size: %dpx; color: #94a3b8; font-weight: 600;" % scaled(18, scale)
        )
        layout.addWidget(title)

        layout.addStretch(1)
        self.value_label = QLabel("-")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.value_label.setWordWrap(True)
        value_size = 24 if name == "STATUS" else 32
        self.value_label.setStyleSheet(
            "font-size: %dpx; color: #f8fafc; font-weight: bold;" % scaled(value_size, scale)
        )
        layout.addWidget(self.value_label)

        self.setLayout(layout)

    def set_value(self, value):
        self.value_label.setText(compact_value(self.name, value))


class ObdWindow(QWidget):
    def __init__(self, query_thread, window_size):
        super().__init__()
        self.query_thread = query_thread
        self.latest_values = {name: "-" for name in ALL_COMMANDS}
        self.obd_status = "STARTING"
        self.is_reverse = False
        self.window_width, self.window_height = window_size
        self.scale = min(
            self.window_width / BASE_WINDOW_WIDTH,
            self.window_height / BASE_WINDOW_HEIGHT,
        )

        self.setWindowTitle("OBD Dashboard")
        self.resize(self.window_width, self.window_height)
        self.setStyleSheet("background-color: %s; color: white;" % BACKGROUND_COLOR)

        layout = QVBoxLayout()
        layout.setContentsMargins(
            scaled(12, self.scale),
            scaled(6, self.scale),
            scaled(12, self.scale),
            scaled(12, self.scale),
        )
        layout.setSpacing(scaled(8, self.scale))

        self.status_label = QLabel(self.status_text())
        self.status_label.setStyleSheet(
            "font-size: %dpx; color: #fb7185; font-weight: 600;" % scaled(15, self.scale)
        )
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.gauge_metrics = {}
        self.info_metrics = {}
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: %s; border: 0;" % BACKGROUND_COLOR)

        self.dashboard_page = QWidget()
        self.dashboard_page.setStyleSheet("background-color: %s; border: 0;" % BACKGROUND_COLOR)
        dashboard_grid = QGridLayout()
        dashboard_grid.setContentsMargins(
            scaled(8, self.scale),
            0,
            scaled(8, self.scale),
            scaled(4, self.scale),
        )
        dashboard_grid.setHorizontalSpacing(scaled(14, self.scale))
        dashboard_grid.setVerticalSpacing(scaled(14, self.scale))

        metric_grid = (
            ("TIMING_ADVANCE", "THROTTLE_POS", "ENGINE_LOAD"),
            ("COOLANT_TEMP", "INTAKE_PRESSURE", "INTAKE_TEMP"),
            ("SHORT_FUEL_TRIM_1", "LONG_FUEL_TRIM_1", "STATUS"),
        )
        for row, names in enumerate(metric_grid):
            for column, name in enumerate(names):
                if name not in ALL_COMMANDS:
                    continue
                if name in GAUGE_RANGES:
                    metric = GaugeMetric(name, self.scale)
                    self.gauge_metrics[name] = metric
                else:
                    metric = InfoMetric(name, self.scale)
                    self.info_metrics[name] = metric
                dashboard_grid.addWidget(metric, row, column)

        for index in range(3):
            dashboard_grid.setColumnStretch(index, 1)
            dashboard_grid.setRowStretch(index, 1)
        self.dashboard_page.setLayout(dashboard_grid)

        self.camera_page = CameraView(self.scale, mock=is_mock)
        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.camera_page)
        layout.addWidget(self.stack, 1)

        self.setLayout(layout)

        self.query_thread.values_changed.connect(self.save_latest_values)
        self.query_thread.status_changed.connect(self.save_status)
        self.query_thread.start()

        self.reverse_monitor = ReverseGearMonitor(mock=is_mock)
        self.reverse_monitor.reverse_changed.connect(self.set_reverse_mode)
        self.reverse_monitor.start()

        self.ui_timer = QTimer(self)
        self.ui_timer.setObjectName("ui thread refresh timer")
        self.ui_timer.timeout.connect(self.update_values)
        self.ui_timer.start(UI_REFRESH_MS)
        self.update_values()

    def status_text(self):
        if self.is_reverse:
            return "REVERSE CAMERA | %s" % self.obd_status
        return self.obd_status

    def save_latest_values(self, values):
        self.latest_values.update(values)

    def save_status(self, status):
        self.obd_status = status

    def set_reverse_mode(self, is_reverse):
        self.is_reverse = is_reverse
        self.camera_page.set_reverse_state(is_reverse)
        if is_reverse:
            self.stack.setCurrentWidget(self.camera_page)
        else:
            self.stack.setCurrentWidget(self.dashboard_page)
        self.status_label.setText(self.status_text())

    def update_values(self):
        self.status_label.setText(self.status_text())
        for name in self.gauge_metrics:
            self.gauge_metrics[name].set_value(self.latest_values[name])
        for name in self.info_metrics:
            self.info_metrics[name].set_value(self.latest_values[name])

    def closeEvent(self, event):
        self.reverse_monitor.stop()
        self.camera_page.stop()
        self.query_thread.stop()
        self.query_thread.wait()
        event.accept()


def main():
    global is_mock

    args = parse_args()
    is_mf = args.mockfull
    is_mock = args.mock or is_mf

    app = QApplication(sys.argv)
    threading.current_thread().name = "ui thread"
    QThread.currentThread().setObjectName("ui thread")
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    app.signal_timer = QTimer()
    app.signal_timer.timeout.connect(lambda: None)
    app.signal_timer.start(200)

    screen = app.primaryScreen().geometry()
    window_size = fit_16_9_size(screen.width(), screen.height())

    query_thread = QueryThread(args.port)
    window = ObdWindow(query_thread, window_size)

    if is_mock and not is_mf:
        window.show()
    else:
        window.showFullScreen()

    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
