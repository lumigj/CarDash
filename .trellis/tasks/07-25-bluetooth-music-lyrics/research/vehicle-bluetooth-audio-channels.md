# Vehicle Bluetooth Media and Navigation Audio Channels

## Conclusion

A Raspberry Pi connected to a typical vehicle over Bluetooth Classic A2DP cannot send two labeled streams called "media" and "navigation." A2DP transports media audio, while HFP transports telephony audio. Bluetooth Classic does not attach a general content-purpose context such as navigation guidance to an audio stream.

If CarDash produces both music and navigation prompts, PipeWire can mix or duck them on the Raspberry Pi, but the vehicle receives the result as one A2DP media stream. The vehicle's independent navigation volume or navigation UI will not be activated.

## Bluetooth Classic profiles

The Bluetooth SIG states that A2DP and HFP have no mechanism to explicitly associate an audio stream with its purpose. Implementations infer purpose from the profile: AVDTP/A2DP is treated as media, while HFP call state and eSCO indicate telephony.

HFP is specified for a mobile phone and a hands-free device, including voice connections and call control. It is not a standardized navigation-audio profile.

Sources:

* https://www.bluetooth.com/wp-content/uploads/2023/09/LowEnergyAudioContextTypesandAvailability_INFO_v1.pdf
* https://docs.bluetooth.com/download/hfp_v1-10_showing_changes_since_hfp_v1-9/
* https://www.bluetooth.com/Specifications/Profiles-Overview/

## Implications for CarDash

### Raspberry Pi sends only music

The Raspberry Pi can be an A2DP source and the vehicle can be the A2DP sink. The vehicle treats this connection as media audio.

If the iPhone remains connected separately for navigation, whether the vehicle can play iPhone guidance while Pi media is active is specific to the head unit. Many systems support a second phone for calls, but that does not imply simultaneous media/navigation audio from two Bluetooth sources.

### Raspberry Pi sends music and navigation

CarDash can mix the streams locally:

```text
music ──────────────┐
                    ├─ local mix/duck ─ A2DP ─ vehicle media input
navigation prompt ──┘
```

This can make guidance audible and lower music volume during prompts, but the vehicle sees one media stream and exposes only its media-volume handling.

### HFP workaround

A Raspberry Pi acting as an HFP Audio Gateway could attempt to send a prompt over an SCO voice path. This simulates telephony rather than navigation and may mute A2DP, show call UI, reduce audio quality, or fail with a particular head unit. It is not a suitable default architecture.

### Proprietary navigation channel

A vehicle may expose a separate navigation volume through CarPlay, Android Auto, its own navigation system, or a manufacturer-specific integration. That behavior is outside standard A2DP and cannot be assumed from the Raspberry Pi's Bluetooth UUID list. The exact head-unit model and connection method are required to determine whether it has an accessible protocol.

