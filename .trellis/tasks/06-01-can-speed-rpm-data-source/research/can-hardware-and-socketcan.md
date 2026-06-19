# CAN hardware and SocketCAN research

## Sources

* AutoWP PSA CAN bus notes: https://autowp.github.io/
* OBD-II connector pinout: https://obdtester.com/obd2_connector
* CANable overview: https://canable.io/index.html
* Linux SocketCAN kernel docs: https://docs.kernel.org/networking/can.html
* can-utils repository: https://github.com/linux-can/can-utils
* PiCAN2 overview: https://www.copperhilltech.shop/blog/pican2-can-bus-board-for-raspberry-pi-functionality-test/

## Findings

AutoWP documents PSA CAN ID `0x0B6` as a BSI frame on `CAN-INFO` carrying tachometer and actual speed. The speed field is documented as actual speed multiplied by 100 in km/h. The tachometer field is a 13-bit RPM value packed across the first two payload bytes.

The OBD-II connector is still useful as a physical access point. Standard J1962 pinout lists pin 6 as CAN High, pin 14 as CAN Low, pin 5 as signal ground, and pin 16 as battery positive. For passive sniffing with a USB-powered CAN adapter, use pins 6, 14, and 5 only.

The ELM327 adapter is not the right hardware for this task. It is an OBD diagnostic adapter that abstracts traffic behind ELM AT commands. For raw PSA frame sniffing and integration with Linux, use a SocketCAN-compatible CAN adapter.

Recommended first hardware path:

* CANable 2.0 or compatible candleLight/gs_usb USB-CAN adapter.
* OBD-II male breakout cable or OBD-II male to screw-terminal adapter.
* Short twisted pair from CAN_H/CAN_L to the breakout, plus ground.

Alternative hardware path:

* PiCAN2/PiCAN3-style Raspberry Pi CAN HAT.
* OBD breakout or a vehicle-side CAN-INFO tap.

Use listen-only mode for initial capture. Disable any adapter-side 120 ohm termination while attached to the car, because the vehicle CAN bus should already be terminated.

## Recommended MVP

1. Use USB-CAN over SocketCAN as the first integration target.
2. Try OBD-II pins 6/14/5 first because it is reversible and does not require cutting/tapping dashboard wiring.
3. If `0x0B6` is absent at the OBD-II port, move the same CAN adapter to the internal `CAN-INFO` pair behind the display/radio/BSI after identifying connector pins from the exact vehicle wiring diagram.
4. Implement a CAN data source that emits the same value shape as the current OBD path:

```python
{
    "RPM": "793 revolutions_per_minute",
    "SPEED": "25.00 kilometer_per_hour",
}
```

That keeps the existing dashboard rendering path mostly unchanged.

