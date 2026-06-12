# E5P Vibration: NO MOTOR POPULATED (2026-06-11)

Stock DT has a gpio-leds entry "motor" = **GPIO3_C4** (gpio3-20 / global 116,
active high) — reference-design leftover. Verified end to end:

- ROCKNIX: pin driven as plain GPIO (devmem, mux func0) AND as pwm14_m0
  (alt-func 1) through the rocknix-singleadc-joypad FF_RUMBLE path
  ("rumble setup success", effect upload + play OK) → no vibration.
- Stock Android (ground truth): `echo 255 > /sys/class/leds/motor/brightness`
  → debugfs shows gpio-116 "out hi" → no vibration. Android has NO vibrator
  HAL (vendor vintf manifest lacks it), no timed_output, and the stock joypad
  node has no pwms property — the led path is the only motor path stock ever
  had, and it does nothing.

Conclusion: motor not mounted on this unit. Reddit claims of E5P rumble are
wrong or a different revision.

Kept in dts anyway (harmless, ready if a motored revision shows up):
`&pwm14` (pwm14m0_pins on GPIO3_C4) + joypad `pwms = <&pwm14 0 25000 0>`,
`pwm-names = "enable"`. The joypad advertises FF_RUMBLE that physically does
nothing; disable via sysfs `rumble_enable` if it ever bothers an emulator.
