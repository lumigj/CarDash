#!/usr/bin/env python3

import argparse
import time
from datetime import datetime, timezone

import obd


DASHBOARD_COMMANDS = [
    "RPM",
    "SPEED",
    "COOLANT_TEMP",
    "THROTTLE_POS",
    "ENGINE_LOAD",
    "INTAKE_TEMP",
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", help="ELM327 port, for example /dev/ttyUSB0")
    parser.add_argument("--interval", type=float, default=1.0)
    return parser.parse_args()


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def simple_value(response):
    if response.is_null():
        return "-"

    value = response.value
    if all(hasattr(value, attr) for attr in ["MIL", "DTC_count", "ignition_type"]):
        return "MIL=%s DTC=%s ignition=%s" % (
            value.MIL,
            value.DTC_count,
            value.ignition_type,
        )

    return str(value)


def connect(port):
    return obd.OBD(port)


def get_commands(connection, names=None):
    if names is None:
        return sorted(
            [
                cmd
                for cmd in connection.supported_commands
                if cmd.mode == 1 and not cmd.name.startswith("PIDS_")
            ],
            key=lambda cmd: (cmd.mode, cmd.pid, cmd.name),
        )

    commands = []
    for name in names:
        cmd = getattr(obd.commands, name)
        if connection.supports(cmd):
            commands.append(cmd)
    return commands


def read_values(connection, commands):
    return {cmd.name: simple_value(connection.query(cmd)) for cmd in commands}


def main():
    args = parse_args()

    connection = connect(args.port)
    if connection.status() == obd.OBDStatus.NOT_CONNECTED:
        print("Could not connect to ELM327")
        return 1

    commands = get_commands(connection)

    print("Connected")
    print("Reading %d commands every %.1f seconds" % (len(commands), args.interval))

    try:
        while True:
            print("\n%s" % utc_now())
            for name, value in read_values(connection, commands).items():
                print("%s: %s" % (name, value))
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        connection.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
