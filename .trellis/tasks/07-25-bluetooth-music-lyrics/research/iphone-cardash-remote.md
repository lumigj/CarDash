# iPhone to CarDash Remote Control

## Goal

Control Raspberry Pi playback from an iPhone without requiring the Raspberry Pi to create a Wi-Fi hotspot.

## Repository constraints

The application is a Python/PyQt dashboard. `requirements-rpi.txt` currently contains only the OBD package and the project has no HTTP server, WebSocket, BLE GATT, or native iOS components.

## Options

### CarDash touch UI and vehicle AVRCP

If the dashboard display is touch-enabled, selection can happen locally. Once the Raspberry Pi is the vehicle's A2DP source, the vehicle's media keys can provide ordinary AVRCP play/pause/next/previous controls.

This is the smallest system because the iPhone does not need to control CarDash.

### Raspberry Pi joins the iPhone Personal Hotspot

The direction of the Wi-Fi connection can be reversed:

```text
iPhone Personal Hotspot
  ├─ cellular internet for Raspberry Pi
  └─ local network path for a Safari remote page

Raspberry Pi
  ├─ joins the saved hotspot automatically
  ├─ streams music and resolves lyrics
  └─ serves a small local control page
```

The remote can be a normal Safari page saved to the iPhone Home Screen. A minimal implementation can use HTTP/JSON polling rather than a WebSocket and avoid a native iOS application.

Apple documents that Personal Hotspot can share cellular internet over Wi-Fi, Bluetooth, or USB. Apple also notes that devices may disconnect when the hotspot is inactive to save battery. Apple does not document the Raspberry-Pi-specific host-to-client reachability behavior, so Safari access to the Pi must be validated on the actual phone before adopting this architecture.

Sources:

* https://support.apple.com/guide/iphone/share-your-internet-connection-iph45447ca6/ios
* https://support.apple.com/111785

### BLE native application

A native iOS application can be a BLE central and send commands to a Raspberry Pi GATT peripheral. This avoids Wi-Fi networking but requires a separate Swift application, signing and installation, and BLE reconnect/state handling.

It is not simpler than a local webpage and is not recommended for the MVP.

## Recommendation

1. If the CarDash screen is touch-enabled, use the local UI and vehicle AVRCP buttons; do not build an iPhone remote for the MVP.
2. Otherwise, have the Raspberry Pi join the iPhone Personal Hotspot and use a small Safari control page.
3. Do not build a native BLE app unless hotspot behavior proves unacceptable.

