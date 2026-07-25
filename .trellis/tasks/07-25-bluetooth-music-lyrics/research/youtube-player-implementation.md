# YouTube Player Implementation for CarDash

## Recommended architecture

```text
iPhone Safari
  -> HTTP/JSON over iPhone Personal Hotspot
  -> Raspberry Pi control server
  -> Qt music controller
  -> visible YouTube IFrame player on CarDash
  -> PipeWire/WirePlumber
  -> Bluetooth A2DP
  -> vehicle

YouTube player state
  -> title, duration, current time, playback state
  -> LRCLIB lookup/cache
  -> synchronized lyrics view
```

Safari is a remote only. The YouTube player and all audio run on the Raspberry Pi.

## Local network and remote page

The Raspberry Pi saves the iPhone Personal Hotspot as a NetworkManager Wi-Fi connection and reconnects to it at boot. The hotspot provides both internet access and the local path from Safari to the Pi.

The Pi serves a small mobile page at:

```text
http://lumisrpi.local:8765
```

The page should show the current track, progress, play/pause, previous/next, seek, and search. The Pi's current hotspot IP is displayed as a fallback if mDNS does not resolve.

To keep the MVP small, use HTTP/JSON and poll state twice per second instead of adding WebSockets or a native iOS application.

Suggested endpoints:

```text
GET  /api/state
GET  /api/search?q=<query>
POST /api/play        {"video_id": "..."}
POST /api/pause
POST /api/resume
POST /api/seek        {"seconds": 123}
POST /api/next
POST /api/previous
```

The server must send commands into the Qt event loop through signals. HTTP request threads must not mutate Qt widgets directly.

## YouTube playback

The supported integration path is the YouTube IFrame Player API. It provides:

* `loadVideoById`, play, pause, stop, and seek.
* Player state-change events.
* `getCurrentTime`, `getDuration`, and current video URL.
* Playlist navigation.

A Qt WebEngine page can host the player and use `runJavaScript()` to call the JavaScript player API and read state.

Important policy constraint: the embedded player cannot be hidden or used as an audio-only/background player. YouTube requires at least a 200x200 viewport, recommends 480x270 for 16:9, and requires an automatically playing player to be visible. YouTube policy also forbids separating the audio component.

Therefore the supported CarDash music page must visibly contain the YouTube player, with lyrics beside or below it. A hidden `QWebEnginePage` that continues music behind the OBD dashboard is not an acceptable official implementation.

Sources:

* https://developers.google.com/youtube/iframe_api_reference
* https://developers.google.com/youtube/terms/required-minimum-functionality
* https://developers.google.com/youtube/terms/developer-policies-guide
* https://doc.qt.io/qt-6/qwebenginepage.html

## Search

The remote search box can call `search.list` from the YouTube Data API and return video results. This requires a Google Cloud project and API key. Search calls have their own quota limit, so the server should debounce input, submit only explicit searches, and cache recent queries.

This searches YouTube videos; it does not reproduce a user's complete YouTube Music library, recommendations, or premium application experience.

Source:

* https://developers.google.com/youtube/v3/docs/search/list

## Lyrics

After playback starts, use the selected result title plus player duration to query LRCLIB. Cache the result by video ID and use the player's current time to select the active LRC line.

Fallback order:

1. Synchronized lyrics.
2. Plain lyrics.
3. Track title and progress with a "lyrics unavailable" message.

## A2DP output

PipeWire/WirePlumber exposes the vehicle Bluetooth connection as an audio output and supports the `a2dp_source` role. The player emits ordinary system audio; routing to the vehicle belongs to the operating-system setup rather than the PyQt request path.

Source:

* https://pipewire.pages.freedesktop.org/wireplumber/daemon/configuration/bluetooth.html

## Implementation phases

### Phase 1: Connectivity spike

* Pi auto-joins the iPhone hotspot.
* Safari reaches a mock remote page.
* Safari controls a local test audio file on the Pi.
* Pi sends that audio to the vehicle over A2DP.

This validates the network, control plane, and Bluetooth route without involving YouTube.

### Phase 2: Visible YouTube player

* Add Qt WebEngine.
* Display a compliant visible player on a new CarDash music page.
* Control one hard-coded embeddable video from Safari.
* Confirm remote-started unmuted playback works on the Raspberry Pi.
* Confirm player state and current time reach Python.

### Phase 3: Search and queue

* Add YouTube Data API search.
* Add a small queue and next/previous behavior.
* Cache searches to protect quota.

### Phase 4: Lyrics

* Add LRCLIB lookup and local cache.
* Render synchronized lyrics from the player time.
* Keep the backup camera as the highest-priority page.

## Rejected shortcuts

* `yt-dlp` plus an audio player: extracts/separates YouTube audio and depends on unofficial behavior.
* Hidden YouTube embed: violates the visible-player/background-play requirements.
* Automating `music.youtube.com`: brittle DOM/private behavior and not a stable public integration contract.
* Native iOS BLE app: more code and installation overhead than the hotspot web remote.

