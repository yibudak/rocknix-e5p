# E5P LEDs: ES control — WORKING (2026-06-11)

## Hardware

4 plain GPIO LEDs (on/off only, no PWM — brightness impossible):

| LED | Role |
|---|---|
| yglled / ygrled | joystick ring LEDs (GPIO4_C4/C5) |
| workled, led3 | status LEDs |
| `mmc0::` | eMMC activity trigger (auto-blinks on I/O — this was the "flicker" seen during display work, plus reboot churn + 3.3V rail dips from panel init; all benign) |

## ES integration (ROCKNIX quirks system)

- `/usr/bin/ledcontrol` = dispatcher → `/usr/lib/autostart/quirks/devices/${QUIRK_DEVICE}/bin/ledcontrol`
  (QUIRK_DEVICE = DT model string "GameMT E5 Plus"), else platform RK3566 fallback.
- ES shows the LED COLOR menu when `DEVICE_LED_CONTROL=true` in
  `/storage/.config/profile.d/010-led_control` (platform quirk writes it on
  every RK3566 at each boot). Menu options come from `ledcontrol list`;
  selection applies ON SETTINGS-SCREEN EXIT (save-on-close), persists as
  `led.color` in system.cfg.
- E5P script options: `default` (all on) / `off` / `ring` (ring only) /
  `status` (status only). `restore` case re-applies at boot;
  `poweroff/charging/discharging` hooks handled.

## Files

- `quirks/GameMT E5 Plus/bin/ledcontrol` — the E5P LED script; the
  `/usr/bin/ledcontrol` dispatcher picks it up automatically once it is
  installed under `quirks/devices/GameMT E5 Plus/bin/` in the image.
- `quirks/GameMT E5 Plus/010-led_control` — sets `DEVICE_LED_CONTROL=true`
  and `DEVICE_LED_BRIGHTNESS=false` (hides the brightness menu, which this
  hardware can't honor). Runs after the platform quirk, so it wins.

## Verified

LED COLOR menu works end-to-end on hardware (off → LEDs out). BRIGHTNESS
menu intentionally hidden on this hardware.
