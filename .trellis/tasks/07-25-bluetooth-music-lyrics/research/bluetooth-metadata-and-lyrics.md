# Bluetooth Metadata and Lyrics Research

## Findings

### Raspberry Pi Bluetooth capability

The repository documents a 64-bit Raspberry Pi OS installation but does not identify the board model. Raspberry Pi 3, 4, and 5 boards include Bluetooth, as do wireless Zero variants. Older boards and non-wireless Compute Modules may require a USB Bluetooth adapter.

Verify the actual board and controller on the Raspberry Pi:

```bash
tr -d '\0' </proc/device-tree/model
echo
bluetoothctl list
bluetoothctl show
```

If `bluetoothctl list` shows a controller, the hardware and BlueZ controller are available.

Source: https://www.raspberrypi.com/documentation/computers/raspberry-pi.html

### What Bluetooth can provide

The practical phone-to-Pi path is:

```text
Phone YouTube Music
  -> Bluetooth A2DP audio
  -> Raspberry Pi PipeWire/WirePlumber

Phone AVRCP metadata
  -> BlueZ org.bluez.MediaPlayer1
  -> title, artist, album, duration, playback status, position
```

WirePlumber supports the `a2dp_sink` role, which makes the Raspberry Pi a Bluetooth audio receiver.

BlueZ exposes the remote player over D-Bus. Its `Track` dictionary contains title, artist, album, genre, track counts, track number, and duration. It also exposes playback status and position.

Neither the Bluetooth AVRCP media attributes nor BlueZ `MediaPlayer1.Track` includes a lyrics field. Bluetooth can identify the track and provide approximate playback position, but it cannot deliver YouTube Music's lyric text.

Sources:

* https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/bluetooth.html
* https://bluez.readthedocs.io/en/latest/media-api/
* https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Assigned_Numbers/out/en/index-en.html

### Lyrics source

The official YouTube Data API documents video metadata, captions, playlists, and related resources, but it is not a phone now-playing/YouTube Music lyrics API. It does not provide the required Bluetooth playback-to-lyrics bridge.

LRCLIB is a feasible independent lyrics source:

* Public API with no API key.
* Returns plain lyrics and synchronized LRC lyrics.
* Exact lookup accepts track title, artist, album, and duration, matching the fields available from AVRCP/BlueZ.
* Requires a responsible identifying client header and rate-limit handling.
* Coverage and matching are not guaranteed, so the UI needs a no-lyrics fallback and local caching.

Sources:

* https://developers.google.com/youtube/v3/docs/videos
* https://www.lrclib.net/docs

## Feasible approaches

### A. Raspberry Pi as Bluetooth audio receiver (recommended for MVP)

1. Pair the phone to the Raspberry Pi.
2. Enable/use PipeWire's A2DP sink role.
3. Subscribe to `org.bluez.MediaPlayer1` D-Bus property changes.
4. On a track change, query and cache LRCLIB lyrics using title, artist, album, and duration.
5. Use BlueZ playback position to highlight synchronized lyric lines.
6. Route received audio from the Pi to HDMI, USB audio, or an AUX output.

Advantages:

* No custom phone application.
* Works with YouTube Music and other phone players that publish AVRCP metadata.
* Track duration and position allow synchronized lyrics.

Trade-offs:

* The phone sends media audio to the Pi; it generally cannot keep sending the same audio directly to a separate car Bluetooth receiver.
* Audio output from the Pi to the vehicle must be solved.
* Metadata quality varies by phone/player.

### B. Phone companion bridge

Use a small Android companion application to read MediaSession/notification metadata and send title, artist, duration, and position to the Pi over Wi-Fi or BLE. The Pi or phone then queries LRCLIB.

Advantages:

* Phone audio can continue going directly to the car stereo.
* More control over reconnect and metadata behavior.

Trade-offs:

* Requires a separate Android application and notification/media-session permission.
* The standard Android media metadata fields still do not contain lyrics.
* This approach is not available for the target iPhone: public iOS APIs do not let a companion read YouTube Music's live playback session.

### C. Run YouTube Music on the Raspberry Pi

Open YouTube Music in a browser on the Pi and display its lyrics UI or integrate around browser state.

Advantages:

* Avoids Bluetooth metadata synchronization.

Trade-offs:

* Heavier, less reliable at boot, and difficult to integrate cleanly with the PyQt dashboard and backup camera.
* Authentication, browser focus, and UI changes make it brittle.

This is not recommended for the CarDash MVP.

## CarDash integration notes

Recommended software components:

```text
BlueZ D-Bus watcher
  -> now-playing state
  -> lyrics lookup/cache worker
  -> parsed timed lyric lines
  -> PyQt signal
  -> LyricsView
```

The existing backup-camera page must retain priority. The lyrics view should live on the normal dashboard page or as another stacked page that is immediately overridden when reverse is active.

MVP fallback states:

* Bluetooth disconnected.
* Connected but no media player metadata.
* Track found but lyrics unavailable.
* Lyrics request offline or rate-limited.
* Unsynchronized lyrics only.
