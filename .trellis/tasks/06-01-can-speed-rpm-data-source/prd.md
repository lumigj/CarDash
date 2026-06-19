# CAN Speed/RPM Data Source

## Goal

Replace or supplement OBD-derived dashboard speed/RPM with PSA raw CAN data, starting from AutoWP's `0x0B6` BSI speed/RPM frame. The goal is to read values from the vehicle network directly and feed the existing PyQt dashboard without rewriting the rendering layer.

## What I already know

* Current CarDash uses `scripts/obd_interface.py` to poll an ELM327 OBD adapter over USB.
* The dashboard rendering code only needs numeric speed and RPM via `DashBoard.set_values(...)`.
* The current app stores values as strings such as `"196 kilometer_per_hour"` and `"6024 revolutions_per_minute"`, then converts them with `numeric_value(...)`.
* `can/read_psa_0b6.py` already contains a standalone SocketCAN sample that decodes CAN ID `0x0B6`.
* `can/README.md` already documents the first wiring attempt and decode map.
* AutoWP documents PSA `0x0B6` as a BSI frame containing tachometer and actual speed.
* If the OBD-II socket is occupied by a CAN adapter, the existing ELM327 cannot also be plugged in directly unless a splitter or separate CAN tap is used.

## Assumptions

* The first safe physical access point should be the OBD-II connector, using CAN pins 6/14/5, because it is reversible and similar to the existing ELM327 workflow.
* The OBD-II connector may not expose the needed PSA `CAN-INFO` frame on this vehicle. If `0x0B6` is missing, a later hardware step must tap the internal CAN-INFO pair behind the display/radio/BSI.
* The initial implementation should be read-only/listen-only and must not transmit CAN frames.

## Requirements

* Document the physical CAN connection from Raspberry Pi to car, including a recommended shopping list.
* Document options for keeping original OBD metrics while also reading raw CAN.
* Add a CAN data source that can read SocketCAN frames from an interface such as `can0`.
* Decode PSA CAN ID `0x0B6` into RPM and speed.
* Feed decoded values into the current dashboard in the same shape used by OBD values.
* Keep the existing OBD path available until CAN has been validated on the real car.
* Support a hybrid MVP where CAN provides speed/RPM and OBD can continue to provide slower secondary metrics.
* Keep capture in listen-only mode for validation.

## Acceptance Criteria

* [ ] README/docs explain the physical wiring from Raspberry Pi to CAN adapter to OBD-II pins 6/14/5.
* [ ] README/docs list recommended hardware and alternatives.
* [ ] A standalone command can print decoded `0x0B6` speed/RPM from `can0`.
* [ ] The dashboard can be launched with CAN speed/RPM as the primary source.
* [ ] If CAN speed/RPM is unavailable, the UI keeps running and shows a clear status.
* [ ] Existing mock mode continues to work.
* [ ] Existing OBD mode continues to work.

## Definition of Done

* Lint / syntax checks pass.
* Manual command examples are documented.
* Real-car validation steps are documented.
* No CAN frame transmission is added for the MVP.
* Docs explain the fallback if `0x0B6` is not visible on the OBD-II connector.

## Technical Approach

Use Python with Linux SocketCAN. This matches the current Python/PyQt app and avoids adding a dependency for the first version.

Physical flow:

```text
Raspberry Pi USB
  -> USB-CAN adapter
  -> CAN_H / CAN_L / GND wires
  -> OBD-II breakout pins 6 / 14 / 5
  -> vehicle CAN bus
```

If OBD-II does not expose `0x0B6`, use the same USB-CAN adapter but move CAN_H/CAN_L/GND to the internal PSA `CAN-INFO` wiring after locating the correct connector pins from the vehicle wiring diagram.

Hybrid physical options:

```text
Option 1: OBD splitter
  OBD socket
    -> splitter branch A -> ELM327 -> Raspberry Pi USB
    -> splitter branch B -> USB-CAN adapter -> Raspberry Pi USB

Option 2: CAN tap elsewhere
  OBD socket -> ELM327 -> Raspberry Pi USB
  internal CAN-INFO pair -> USB-CAN adapter -> Raspberry Pi USB

Option 3: CAN-only MVP
  OBD socket -> USB-CAN adapter -> Raspberry Pi USB
  no ELM327 for the first phase
```

Option 1 is convenient for testing but both devices share the same physical OBD CAN pins. It should be used read-only for the CAN adapter and may be noisy or unreliable depending on the ELM327 behavior and vehicle gateway. Option 2 is cleaner for the final hybrid install if the internal CAN-INFO pair is accessible and identified safely.

Implementation flow:

```text
SocketCAN can0
  -> raw CAN frame reader
  -> filter CAN ID 0x0B6
  -> decode rpm and speed_kmh
  -> emit {"RPM": "...", "SPEED": "..."}
  -> existing ObdWindow.latest_values
  -> existing dashboard_widget.set_values(...)
```

Expected decode:

```python
rpm = (data[0] << 5) | (data[1] >> 3)
speed_kmh = ((data[2] << 8) | data[3]) / 100
```

Likely code changes:

* Add a reusable CAN decoder module under `can/` or `scripts/`.
* Add a `CanQueryThread` with the same `values_changed` and `status_changed` signals as `QueryThread`.
* Add CLI options such as `--data-source obd|can|hybrid|mock` and `--can-interface can0`.
* In hybrid mode, use CAN for `SPEED` and `RPM`, and OBD for secondary metrics.

## Feasible Approaches

### Approach A: USB-CAN via OBD-II first (recommended)

How it works: Buy a SocketCAN-compatible USB-CAN adapter and an OBD-II breakout. Wire CAN_H/CAN_L/GND to OBD-II pins 6/14/5. Run in listen-only mode and search for `0x0B6`.

Pros: Lowest-risk wiring, reversible, close to the current ELM327 physical workflow.

Cons: The desired PSA `CAN-INFO` frame may not be exposed at the OBD-II port.

### Approach B: Raspberry Pi CAN HAT via OBD-II

How it works: Install a PiCAN-style HAT on the Raspberry Pi and wire its CAN screw terminal to OBD-II pins 6/14/5.

Pros: Integrated into the Pi, robust once mounted.

Cons: More Pi-specific setup, SPI overlay configuration, less convenient to test on a laptop.

### Approach C: Internal CAN-INFO tap

How it works: Tap the CAN-INFO twisted pair behind the display/radio/BSI and connect the CAN adapter in parallel.

Pros: Most likely to see display/BSI-specific PSA messages if OBD-II does not expose them.

Cons: Requires exact vehicle wiring diagram and careful physical access; higher risk than OBD-II breakout.

## Open Questions

* Which MVP physical mode should be implemented first: OBD splitter hybrid, CAN tap plus OBD, or CAN-only validation?

## Out of Scope

* Sending CAN frames to the car.
* Replacing the PyQt dashboard rendering.
* Driving the original PSA LCD panel directly from this task.
* Decoding every PSA CAN message.
* Guessing internal display/BSI connector pins without the exact car wiring diagram.

## Research References

* [`research/can-hardware-and-socketcan.md`](research/can-hardware-and-socketcan.md) — Hardware, SocketCAN, OBD-II pinout, and recommended MVP path.

## Technical Notes

* `can/README.md` contains the current manual wiring and command notes.
* `can/read_psa_0b6.py` is the current standalone sample reader.
* `scripts/obd_interface.py` is the integration target for dashboard data-source selection.
* `dashboard/dashboard.py` should not need major changes because it already accepts numeric speed/RPM.
