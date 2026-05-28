# Releases

This project uses GitHub releases to mark firmware states that matter for the
physical ESP32-S3 webcam board.

## v0.1 - Currently Flashed Board Image

- Release tag: `v0.1`
- GitHub release: https://github.com/JacobFV/esp32-usb-webcam/releases/tag/v0.1
- Firmware commit: `54e61aa01dbaf6be2d96e71c09f14ed6deaeff5d`
- Equivalent firmware-input commits: `54e61aa` through `da6cf4b`
- Live board identity: `303a:8000 Espressif ESP UVC Device`
- Live descriptor: UVC-only, two USB Video interfaces, no CDC ACM serial
- Advertised first mode: `1280x720 @ 15fps`
- Verified host capture: `/dev/video0` reads `640x480` frames through V4L2

The commits between `54e61aa` and `da6cf4b` changed documentation only, so the
firmware image currently on the board corresponds to the initial UVC firmware.

## v0.2 - Latest Recovery-Capable Firmware

- Release tag: `v0.2`
- GitHub release: https://github.com/JacobFV/esp32-usb-webcam/releases/tag/v0.2
- Firmware commit: `3915250688fd6398863fa6b4145b02824b0fefe6`
- Status: builds successfully but has not been flashed to the currently
  connected board
- USB behavior: composite UVC + CDC ACM
- Recovery path: send `bootloader` or `reboot-bootloader` to the CDC serial
  port, or open the port at 1200 baud and close it, to request ESP32-S3 ROM
  download mode

This version keeps the webcam as a standard UVC device while adding a serial
recovery/control interface to avoid future UVC-only lockouts.
