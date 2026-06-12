# E5P Audio: rk817 speakers — WORKING (2026-06-11)

## Board wiring quirk (from stock DT)

Stock `rockchip,rk817-codec` node: `out-l2spk-r2hp` + `spk-ctl-gpios =
GPIO4_C2 active-high` + `hp-volume = spk-volume = 0x0a`. Meaning: the two
speakers are fed from the **HP output path through an external amplifier**
enabled by GPIO4_C2. RK817's own SPKOUT pin is wired to NOTHING.

Consequences on mainline (our dts uses mainline rk817 codec +
simple-audio-card "rk817_ext"):

- `Playback Mux` must stay **'HP'** — selecting 'SPK' routes to the
  unconnected SPKOUT = total silence.
- Amp enable handled by the `speaker-amp` node in our dts
  (`enable-gpios = <&gpio4 RK_PC2 GPIO_ACTIVE_HIGH>`) — shows as gpio4-18
  "enable out hi" in debugfs. Already worked.
- Headphone jack detect = gpio4-22, input, IRQ (works, event2 input dev).

## Levels

Boot default Master = 100% (0dB) → clips on these small speakers. Android
runs DAC at -3.75dB (stock `hp-volume 0x0a`, 0.375dB/step scale) →
**Master 96%** is the Android-equivalent and verified to sound good on
hardware.

Applied at boot by the device quirk `quirks/GameMT E5 Plus/050-audio_path`
(audio path env vars + mux HP, Internal Speakers on, Master 96%). It runs
after the RK3566 platform quirk, so the device values win.

## Playback notes

- ALSA hw is held by pipewire — `aplay -D plughw` fails "busy"; use
  `XDG_RUNTIME_DIR=/var/run/0-runtime-dir pw-play file.wav`.
- No alsa-restore/asound.state in this image; mixer resets at boot — hence
  the boot-time quirk.
- Per-app/UI volume = wireplumber sink volume (`wpctl set-volume
  @DEFAULT_AUDIO_SINK@ 0.6`); sink IDs shuffle between boots, use
  @DEFAULT_AUDIO_SINK@.

## Idle hiss / amp power gate (2026-06-11)

ES keeps an SDL audio stream open for its whole lifetime (AudioManager inits
SDL_mixer at construction; streams silence continuously — pw-top shows the
sink permanently "running"). DAPM therefore never powers down the path and
the external speaker amp stays enabled: audible idle hiss + wasted power.
No ES setting closes it (bgmusic off doesn't help).

A polling watchdog service was prototyped and rejected (userspace poll loops
don't belong in the image). The proper fix is planned as an EmulationStation
patch: AudioManager closes the SDL device when idle, like it already does
around game launch. TODO at full-build time.
