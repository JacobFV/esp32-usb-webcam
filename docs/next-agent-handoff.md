# Next Agent Handoff

The next agent should assume this repo is the source of truth for the ESP32-S3
USB webcam firmware.

## User Intent

Make the board behave like a fully functional, normal-seeming USB webcam.

That means:

- It enumerates as a standard USB Video Class device.
- Linux creates `/dev/video*`.
- Apps can open it through V4L2 without custom host software.
- It does not use Wi-Fi, AP mode, HTTP streaming, credentials, or network
  discovery.
- It survives normal webcam usage: repeated opens, closes, app switches, and
  reconnects.

## Hardware

Verified target board:

- Seeed XIAO ESP32S3 Sense
- OV2640 camera module
- Native USB
- PSRAM

Earlier successful board identity:

- ESP32-S3 MAC: `24:58:7c:e2:a0:f0`
- Successful UVC USB ID: `303a:8000 Espressif ESP UVC Device`

Current host state recorded on 2026-05-26:

- `pio run` succeeds.
- The plugged board currently appears as `1a86:55d3 QinHeng Electronics USB Single Serial`.
- `/dev/ttyACM0` exists.
- The previous `/dev/video0` UVC node is not currently present.
- Upload to `/dev/ttyACM0` failed with `No serial data received` after the
  reliable-mode firmware change.
- DTR/RTS toggles and a 1200-baud touch did not move the device out of
  `1a86:55d3`.
- The user then unplugged a servo driver board and `/dev/ttyACM0` /
  `1a86:55d3` disappeared, so that serial device was likely not the ESP32-S3
  webcam. Esptool never connected and did not flash it.
- The ESP32 later appeared as `303a:8000 Espressif ESP UVC Device` with
  `/dev/video0` and `/dev/video1`. The `video-index0` path passed 10 repeated
  OpenCV open/read/release cycles at `640x480`; `video-index1` timed out as a
  capture source.
- Descriptor inspection showed that live board was still running the older
  image with frame index 1 as `1280x720`, not the committed VGA-default image.
- Starting multiple capture clients concurrently reproduced the old reliability
  issue: subsequent single-client reads timed out while UVC enumeration remained
  present. A host `usbreset 303a:8000` then hung in the kernel.
- After physical unplug/replug, the board re-enumerated as UVC and again passed
  10 repeated `640x480` OpenCV reads from `video-index0`. A sequential FFmpeg
  `640x480` MJPEG capture also succeeded. FFmpeg default-open selected
  `640x480`, and 10 repeated FFmpeg open/read/close cycles succeeded.
- A firmware-side recovery patch has been committed but not flashed. It drops
  refused frame transfers instead of waiting forever, times out stale in-flight
  transfers, resets the streaming endpoint on stream stop, and builds cleanly.
- The connected board currently exposes UVC only and no
  `/dev/ttyACM*`/serial-JTAG endpoint. There is no safe software flashing path
  from this app state; flashing still requires ROM bootloader mode or a future
  firmware reboot-to-bootloader path.

## Known Good Proof

The firmware was successfully flashed before this handoff. After that flash,
Linux saw:

```text
303a:8000 Espressif ESP UVC Device
/dev/video0
/dev/video1
/dev/v4l/by-id/usb-Espressif_ESP_UVC_Device_12345678-video-index0 -> ../../video0
```

OpenCV then captured a real frame:

```text
shape: (480, 640, 3)
saved: /tmp/esp32-uvc-video0.jpg
```

That captured frame is committed as:

```text
assets/esp32-uvc-frame.jpg
```

## Build

Use PlatformIO:

```bash
pio run
```

This has been verified in the standalone repo.

Do not upgrade `platform = espressif32@6.9.0` casually. PlatformIO
`espressif32@7.0.1` pulled ESP-IDF 6 and broke the camera dependency on an old
`driver/ledc.h` include.

## Flash

Typical command:

```bash
pio run -t upload --upload-port /dev/ttyACM0
```

Earlier successful command used `/dev/ttyACM1`:

```bash
pio run -t upload --upload-port /dev/ttyACM1
```

If permission fails, check whether the user is in `dialout` or whether udev has
applied an ACL. Do not assume the port number is stable.

## Verify

After flashing and reset:

```bash
lsusb | rg '303a:8000|UVC|Espressif'
ls -l /dev/v4l/by-id/
```

Then test frame capture:

```bash
tools/verify_uvc.py --loops 10
```

Or manually:

```bash
python - <<'PY'
import cv2, os, time

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
time.sleep(1)

ok, frame = cap.read()
print("opened:", cap.isOpened())
print("read:", ok, None if frame is None else frame.shape)
if ok:
    out = "/tmp/esp32-uvc-video0.jpg"
    cv2.imwrite(out, frame)
    print("saved:", out, os.path.getsize(out))
cap.release()
PY
```

For a "normal webcam" pass, repeat open/read/release in a loop and test at least
one GUI camera app or browser-based camera picker.

## Architecture Notes

The application is in:

```text
main/usb_webcam_main.c
```

The board pin mapping is in:

```text
main/camera_pin.h
```

The project vendors Espressif's UVC component at:

```text
components/usb_device_uvc/
```

That vendoring is intentional. The managed component caused a duplicate
`usb_descriptors.c.o` action in PlatformIO. The local component builds
`tusb/usb_descriptors.c` directly and uses explicit version macros.

The current firmware advertises conservative MJPEG modes for normal webcam
apps:

- `640x480 @ 15fps`
- `480x320 @ 30fps`
- `320x240 @ 30fps`
- `160x120 @ 30fps`

The default is VGA. This avoids the earlier HD default, which could make
ordinary host apps choose a mode larger than the ESP32-S3 full-speed USB path
could reliably deliver.

The current component code also checks the return value from
`tud_video_n_frame_xfer()`. If the USB stack refuses a transfer, the firmware
drops that frame and resets the stream endpoint instead of marking the transfer
busy forever. This is intended to make repeated app opens, closes, and app
switches recover like a normal webcam.

## Failure Modes Already Seen

- Wi-Fi/AP camera firmware was the wrong interface. Do not restore it.
- ESP-IDF 6 / PlatformIO `espressif32@7.0.1` broke the camera dependency.
- The managed `usb_device_uvc` CMake path duplicated USB descriptor objects.
- A host-side USB reset attempt de-enumerated the UVC function and left only the
  serial interface visible. Prefer physical replug/reset before diagnosing
  firmware from that state.
- OpenCV capture can hang if the USB/video state is half-reset. Use bounded
  commands like `timeout 12 ...` while iterating.

## Definition Of Done For The Next Iteration

- Fresh flash from this repo succeeds.
- `lsusb` shows `303a:8000 Espressif ESP UVC Device`.
- `/dev/v4l/by-id/usb-Espressif_ESP_UVC_Device_12345678-video-index0` exists.
- A bounded OpenCV capture succeeds at `640x480`.
- Repeated capture open/close succeeds at least 10 times.
- A normal webcam consumer can see and open the camera.
- Documentation is updated with any new exact command or issue encountered.
