#!/usr/bin/env python3

import argparse
import socket
import struct
from datetime import datetime


CAN_FRAME = struct.Struct("=IB3x8s")
CAN_EFF_FLAG = 0x80000000
CAN_SFF_MASK = 0x000007FF
CAN_EFF_MASK = 0x1FFFFFFF
PSA_SPEED_RPM_CAN_ID = 0x0B6


def decode_0b6(data):
    rpm = (data[0] << 5) | (data[1] >> 3)
    speed_kmh = ((data[2] << 8) | data[3]) / 100
    trip_cm = (data[4] << 8) | data[5]
    fuel_counter = data[6]
    return rpm, speed_kmh, trip_cm, fuel_counter


def dashboard_values(rpm, speed_kmh):
    return {
        "RPM": "%d revolutions_per_minute" % rpm,
        "SPEED": "%.2f kilometer_per_hour" % speed_kmh,
    }


def open_can_socket(interface):
    can_socket = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
    can_socket.bind((interface,))
    return can_socket


def read_can_frame(can_socket):
    frame = can_socket.recv(CAN_FRAME.size)
    can_id, can_dlc, data = CAN_FRAME.unpack(frame)
    if can_id & CAN_EFF_FLAG:
        frame_id = can_id & CAN_EFF_MASK
    else:
        frame_id = can_id & CAN_SFF_MASK
    return frame_id, data[:can_dlc]


def format_frame_data(data):
    return " ".join("%02X" % byte for byte in data)


def print_decoded_frame(frame_id, data):
    rpm, speed_kmh, trip_cm, fuel_counter = decode_0b6(data)
    values = dashboard_values(rpm, speed_kmh)
    print(
        "%s id=%03X data=%s rpm=%d speed=%.2fkm/h trip_cm=%d fuel_counter=%d values=%s"
        % (
            datetime.now().isoformat(timespec="milliseconds"),
            frame_id,
            format_frame_data(data),
            rpm,
            speed_kmh,
            trip_cm,
            fuel_counter,
            values,
        )
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interface", default="can0")
    parser.add_argument("--once", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    can_socket = open_can_socket(args.interface)

    while True:
        frame_id, data = read_can_frame(can_socket)
        if frame_id != PSA_SPEED_RPM_CAN_ID or len(data) < 8:
            continue

        print_decoded_frame(frame_id, data)
        if args.once:
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
