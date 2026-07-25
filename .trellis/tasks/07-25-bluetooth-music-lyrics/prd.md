# Bluetooth Music Lyrics Display

## Goal

Display the current song title, playback progress, and lyrics on the Raspberry Pi CarDash screen. CarDash controls playback, mixes all of its audio locally, and sends one A2DP media stream to the vehicle.

## What I already know

* CarDash is a Raspberry Pi PyQt application designed for a 1280x720 in-car screen.
* The existing app already uses a stacked page layout for the dashboard and backup camera.
* The iPhone will act as a controller rather than the vehicle's media-audio source.
* The phone is an iPhone.
* Bluetooth AVRCP can provide track metadata and playback position, but not lyric text.
* LRCLIB can resolve plain or synchronized lyrics from title, artist, album, and duration.
* The target hardware is a Raspberry Pi 5 Model B Rev 1.1.
* BlueZ detects controller `2C:CF:67:F4:93:B8`; it is powered, pairable, and advertises Audio Sink, Audio Source, and AVRCP controller/target profiles.
* The Raspberry Pi must not become the phone's Bluetooth audio receiver.
* The vehicle's Bluetooth audio system must remain the final audio output.
* The vehicle distinguishes media audio from navigation guidance, and that distinction must be understood before changing the active Bluetooth source.
* The user accepts sending all CarDash audio through one A2DP media stream; a separate vehicle navigation channel is not required.
* The repository currently has no HTTP server dependency; `requirements-rpi.txt` only lists the OBD package.
* The user selected the iPhone Personal Hotspot plus Safari remote approach.

## Assumptions (temporary)

* The desired MVP is a readable now-playing/lyrics page, not a full YouTube Music client running on the Raspberry Pi.
* Internet access may be available through the phone hotspot or another network.

## Open Questions

* Is synchronized line-by-line lyric timing required for the MVP?
* Is the 1280x720 CarDash screen touch-enabled?

## Requirements (evolving)

* CarDash controls the playing track and therefore owns the now-playing state.
* Display song title, artist, playback state, and lyrics on the CarDash screen.
* Pair the Raspberry Pi to the vehicle as the A2DP media source.
* Mix all CarDash audio locally and send it as one A2DP stream.
* Have the Raspberry Pi automatically join the iPhone Personal Hotspot.
* Serve a lightweight local control page that the iPhone opens in Safari.
* Preserve the existing backup-camera page priority.
* Keep the UI readable and minimally distracting in a vehicle.

## Acceptance Criteria (evolving)

* [x] Raspberry Pi Bluetooth availability can be verified with documented commands.
* [ ] Changing tracks through the selected CarDash control surface updates the displayed title and artist.
* [ ] Lyrics are resolved for the current track and shown on the screen.
* [ ] Raspberry Pi audio plays through the vehicle's Bluetooth media input.
* [ ] All CarDash audio uses A2DP; no HFP navigation-channel emulation is used.
* [ ] Entering reverse still switches immediately to the backup-camera page.
* [ ] Missing lyrics or network failure does not stop the dashboard.

## Definition of Done

* Tests added or updated where practical.
* Static checks pass.
* Raspberry Pi setup and pairing steps are documented.
* Lyrics provider limitations and fallback behavior are documented.
* Rollback leaves the existing dashboard and backup-camera behavior intact.

## Out of Scope

* Extracting or scraping lyrics directly from the YouTube Music application UI.
* Replacing YouTube Music with a custom music streaming client.
* Receiving or playing phone audio on the Raspberry Pi.
* Implementing the feature before the playback and lyrics data paths are selected.

## Research References

* [`research/bluetooth-metadata-and-lyrics.md`](research/bluetooth-metadata-and-lyrics.md) - Bluetooth metadata limits, lyrics providers, and feasible architectures.
* [`research/iphone-youtube-music-api.md`](research/iphone-youtube-music-api.md) - Public API limits for observing YouTube Music playback on an iPhone.
* [`research/vehicle-bluetooth-audio-channels.md`](research/vehicle-bluetooth-audio-channels.md) - Why Bluetooth Classic cannot label independent media and navigation streams.
* [`research/iphone-cardash-remote.md`](research/iphone-cardash-remote.md) - Simple control paths without making the Raspberry Pi a hotspot.

## Feasible Approaches

### Approach A: Manual iPhone share/shortcut trigger

Keep the current audio path. The user explicitly shares the current track or runs a Shortcut that sends available track data to CarDash. CarDash resolves lyrics independently. This cannot reliably observe seeks, pauses, or automatic track changes.

### Approach B: CarDash-controlled player

Play through a web/player surface controlled by CarDash so that title and playback time are directly observable. The Raspberry Pi pairs to the vehicle as an A2DP audio source and sends the resulting audio over the vehicle's Bluetooth connection. This enables reliable synchronization but replaces the iPhone as the vehicle's media-audio source. Standard A2DP presents one media stream, so any CarDash music/navigation mixing and ducking happens on the Pi; the vehicle does not receive a separate navigation-channel label.

### Approach C: Unofficial extraction

Use private APIs, UI scraping, traffic interception, or a modified device. This is brittle and is not recommended.

## Remote Control Approaches

### Approach 1: CarDash touch UI plus vehicle AVRCP controls (recommended if the screen is touch-enabled)

Select music on the CarDash screen. Use the vehicle's existing play/pause/next/previous controls over AVRCP after the Raspberry Pi becomes the A2DP source. This requires no iPhone-to-Pi control connection.

### Approach 2: Raspberry Pi joins the iPhone Personal Hotspot

The Raspberry Pi automatically joins the iPhone's hotspot for internet access and hosts a small local control page. Safari opens the Raspberry Pi address; the iPhone does not join a Raspberry Pi hotspot. Initial local reachability and reconnect behavior must be tested on the actual iPhone.

### Approach 3: BLE native iPhone remote

Build and maintain a native iOS application that sends BLE commands to a GATT service on the Raspberry Pi. This avoids Wi-Fi but adds application signing, installation, and a second codebase, so it is not recommended for the MVP.

## Decision (ADR-lite)

**Context**: The phone already has a separate audio path and the Raspberry Pi is only needed as a display.

**Decision**: CarDash will control playback. The Raspberry Pi will connect to the vehicle as its A2DP media source, mix all CarDash audio locally, and send one media stream. Do not use HFP to simulate a navigation channel.

**Consequences**: CarDash can know the exact playback position without reading another iPhone application's state. The vehicle will not expose separate media/navigation volume handling for CarDash audio. The iPhone can remain a controller, but it is no longer the source of the vehicle's media stream.

## Technical Notes

* Likely integration point: `scripts/obd_interface.py` stacked page layout.
* Existing priority page: `dashboard/camera_view.py`.
* Raspberry Pi 5 Bluetooth hardware and the required BlueZ media profiles are available.
* The iPhone may send AVRCP metadata to its active car Bluetooth audio endpoint, but the data-only Raspberry Pi connection is not that endpoint.
* The Raspberry Pi advertises the Audio Source role required to send its own playback audio to a vehicle Bluetooth receiver.
* Bluetooth Classic A2DP/HFP does not define a general navigation-audio context. A vehicle's separate navigation volume/channel is likely implemented by CarPlay, Android Auto, a proprietary protocol, HFP behavior, or the vehicle's internal navigation system.
* Apple Personal Hotspot can share cellular internet over Wi-Fi, Bluetooth, or USB. It may disconnect inactive clients to save battery.
