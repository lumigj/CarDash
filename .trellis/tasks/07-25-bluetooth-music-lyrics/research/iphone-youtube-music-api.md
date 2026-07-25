# iPhone and YouTube Music Public API Research

## Conclusion

There is no supported public API that lets a separate iPhone application or Raspberry Pi observe the live title, playback position, and lyrics of the YouTube Music iPhone application while audio continues through an unrelated car audio connection.

This is a combination of two boundaries:

1. YouTube's public APIs do not expose the current playback session of the YouTube Music mobile application.
2. iOS does not give one application general access to another application's now-playing state.

## YouTube APIs

The YouTube Data API exposes catalog resources such as videos, playlists, channels, searches, and caption tracks. It does not expose a user's current YouTube Music playback session, live playback position, or YouTube Music lyrics.

The YouTube IFrame Player API exposes player state and current time only for an embedded player created and controlled by the integrating application. It cannot inspect the separate YouTube Music iPhone application.

Caption tracks are not equivalent to YouTube Music's synchronized lyrics and do not solve live track detection.

Sources:

* https://developers.google.com/youtube/v3/docs
* https://developers.google.com/youtube/iframe_api_reference

## iOS media APIs

`MPNowPlayingInfoCenter` is used by a media application to publish its own now-playing information to the system. It is not an API for reading the private now-playing information of another application.

`MPMusicPlayerController` is designed around the device music library and Apple Music playback. It does not expose the playback session of YouTube Music.

Consequently, a custom CarDash companion application cannot continuously read YouTube Music's title, duration, position, pause, seek, or track-change state from the iPhone.

Sources:

* https://developer.apple.com/documentation/mediaplayer/mpnowplayinginfocenter/default%28%29
* https://developer.apple.com/documentation/mediaplayer/mpmusicplayercontroller

## Google Cast

The Google Cast sender SDK exposes the media session controlled by that sender application. A separate companion application cannot attach to the YouTube Music application's private Cast session and use it as a general now-playing feed.

Source:

* https://developers.google.com/cast/docs/ios_sender/integrate

## Remaining options

### Manual share or Shortcut

The user can explicitly share a track URL or invoke a Shortcut that posts available data to CarDash. CarDash can then look up lyrics independently and start an approximate local timer.

Limitations:

* It is not automatic when the next track starts.
* Pause, seek, and playback speed changes are not observable.
* Data available to a Share Sheet action depends on what YouTube Music shares.

### Controlled playback

If playback happens in a player controlled by CarDash, such as an embedded YouTube player, the integration can observe player state and current time. This changes the product from a passive display for the iPhone app into the playback controller.

### Unsupported extraction

Private endpoints, UI scraping, traffic interception, jailbreaking, or screen recognition may expose some state, but they are brittle, maintenance-heavy, and unsuitable for the intended MVP.

## Lyrics after track identification

Once title, artist, and duration are known, an independent provider such as LRCLIB can return plain or synchronized lyrics. The lyrics lookup itself is feasible; reliably identifying and tracking the current song under the required iPhone audio architecture is the blocked part.

