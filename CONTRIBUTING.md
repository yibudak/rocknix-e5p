# Contributing

Thanks for helping make ROCKNIX on the GameMT E5 Plus better! Any kind of
contribution is welcome - you don't need to be a kernel developer.

## Ways to help

- **Test on your device.** The most valuable contribution. Flash an image,
  play games, and report what works and what doesn't.
- **Report bugs.** Open an issue with: what you did, what you expected,
  what happened, and logs if you can get them
  (`journalctl -b` and `dmesg` over SSH).
- **Improve documentation.** Typos, unclear steps, missing details - PRs to
  `docs/` are always appreciated.
- **Code.** Kernel patches, device-tree fixes, quirk scripts.

## Pull requests

- Keep PRs focused: one fix or feature per PR.
- Kernel C code follows the
  [Linux kernel coding style](https://www.kernel.org/doc/html/latest/process/coding-style.html).
- Shell scripts are POSIX `sh` (they run under BusyBox on the device) and
  must pass ShellCheck - CI runs it automatically.
- If you change hardware-facing behavior (DTS, panel driver, quirks), say in
  the PR description whether you tested on real hardware.

## Getting answers

Not sure where something lives? The `docs/` directory covers every subsystem
(display, WiFi, Bluetooth, audio, battery, LEDs) including the debugging
history of how each one was brought up. Start there, then open an issue.

## Safety rule

All development happens from **SD card**. Never write to the internal eMMC -
it holds the stock Android install that makes the device recoverable.
