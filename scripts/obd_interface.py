#!/usr/bin/env python3

import argparse
import sys

import obd
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

from obd_logger import DASHBOARD_COMMANDS, connect, get_commands, read_values


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", help="ELM327 port, for example /dev/ttyUSB0")
    parser.add_argument("--interval", type=float, default=0.5)
    return parser.parse_args()


class ObdWindow(QWidget):
    def __init__(self, connection, commands, interval):
        super().__init__()
        self.connection = connection
        self.commands = commands

        self.setWindowTitle("OBD Dashboard")

        layout = QVBoxLayout()
        self.labels = {}
        for name in DASHBOARD_COMMANDS:
            label = QLabel("%s: -" % name)
            label.setStyleSheet("font-size: 32px;")
            layout.addWidget(label)
            self.labels[name] = label
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_values)
        self.timer.start(int(interval * 1000))
        self.update_values()

    def update_values(self):
        values = read_values(self.connection, self.commands)
        for name, value in values.items():
            self.labels[name].setText("%s: %s" % (name, value))

    def closeEvent(self, event):
        self.connection.close()
        event.accept()


def main():
    args = parse_args()
    connection = connect(args.port)

    if connection.status() == obd.OBDStatus.NOT_CONNECTED:
        print("Could not connect to ELM327")
        return 1

    app = QApplication(sys.argv)
    window = ObdWindow(
        connection,
        get_commands(connection, DASHBOARD_COMMANDS),
        args.interval,
    )
    window.resize(480, 360)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
