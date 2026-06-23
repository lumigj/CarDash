# PSA CAN speed/RPM sample

This folder is for reading PSA CAN data directly, separate from the existing
OBD-II polling path in `scripts/obd_interface.py`.

The first target frame is CAN ID `0x0B6` on PSA `CAN-INFO`. AutoWP documents
this frame as coming from the BSI and carrying tachometer plus actual vehicle
speed.

## First physical connection to try

Start at the car's OBD-II port with a SocketCAN-compatible CAN adapter.

```text
CAN adapter CAN_H -> OBD-II pin 6
CAN adapter CAN_L -> OBD-II pin 14
CAN adapter GND   -> OBD-II pin 5
```

Do not connect the LCD ribbon cable. The PSA LCD ribbon is I2C for display
segments, not CAN.

If the CAN adapter is USB powered, do not connect OBD-II pin 16. If the adapter
has a 120 ohm termination jumper, leave it disabled when connected to the car.

## Bring up SocketCAN

Use listen-only mode while sniffing.

```bash
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 500000 listen-only on
sudo ip link set can0 up
```

If `0x0B6` does not appear, try `250000` and `125000` as the bitrate. Some PSA
signals may be on an internal CAN-INFO bus rather than exposed on the OBD-II
connector.

Optional raw check:

```bash
candump -tz can0,0B6:7FF
```

## Run the sample reader

```bash
python can/read_psa_0b6.py --interface can0
```

Print one decoded frame and exit:

```bash
python can/read_psa_0b6.py --interface can0 --once
```

## Decode map

AutoWP shows `0x0B6` as this 8-byte payload:

```text
MMMMMMMM MMMMM000 SSSSSSSS SSSSSSSS TTTTTTTT TTTTTTTT FFFFFFFF 11010000
```

That means:

```text
bytes 0..1: RPM, 13 bits, top-aligned with 3 padding bits
bytes 2..3: actual speed * 100 in km/h
bytes 4..5: odometer from start, cm
byte 6:     fuel consumption counter
byte 7:     usually 0xD0
```

The sample converts decoded values to the same string shape that
`obd_interface.py` already understands:

```python
{
    "RPM": "793 revolutions_per_minute",
    "SPEED": "25.00 kilometer_per_hour",
}
```

