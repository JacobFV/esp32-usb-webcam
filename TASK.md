# ESP32 USB Webcam Task Log

This file is the handoff log for future agents working in this repo. The next
goal is to turn the existing proof-of-concept firmware into a fully functional,
normal-feeling USB webcam.

Public repo:
- https://github.com/JacobFV/esp32-usb-webcam

Public build note / gist:
- https://gist.github.com/JacobFV/f36f57def2b0b1446036fef3fa4c1016

Portfolio entry:
- Repo: `/home/brandonin-2/Code/jvboid.dev`
- Project page source: `content/projects/esp32-usb-webcam.mdx`
- Representative asset: `public/assets/img/projects/esp32-usb-webcam-frame.jpg`

Verified hardware state:
- Board: ESP32-S3, MAC `24:58:7c:e2:a0:f0`
- USB device after successful flash: `303a:8000 Espressif ESP UVC Device`
- Linux devices: `/dev/video0` and `/dev/video1`
- OpenCV verified frame capture from index `0`: `640x480`, saved to `/tmp/esp32-uvc-video0.jpg`
- The image was visually checked and shows a real camera frame.
- Standalone repo build was later verified with `pio run` from `/home/brandonin-2/Code/esp32-usb-webcam`.
- A later host-side USB reset attempt de-enumerated the UVC function on this machine. The firmware was already proven, but another live capture may require physically replugging/resetting the board into the UVC app or bootloader state.

Current local hardware state as of 2026-05-26:
- `pio run` succeeds in this standalone repo.
- The temporary `1a86:55d3 QinHeng Electronics USB Single Serial` /
  `/dev/ttyACM0` device was a servo driver board, not the ESP32-S3 webcam.
- After the servo board was unplugged, the ESP32-S3 webcam reappeared as
  `303a:8000 Espressif ESP UVC Device` with `/dev/video0` and `/dev/video1`.
- The currently flashed ESP32-S3 app is UVC-only. It exposes no
  `/dev/ttyACM*`/serial-JTAG endpoint, so there is no software flash path from
  the current app state.

Update from 2026-05-26:
- The advertised default mode was changed from HD to VGA so normal camera apps
  do not select a mode that exceeds the ESP32-S3 full-speed USB/JPEG buffer.
- Advertised MJPEG modes are now `640x480@15`, `480x320@30`, `320x240@30`,
  and `160x120@30`.
- The UVC transfer buffer was raised to 128 KiB and runtime support for
  `160x120` was added.
- `pio run` succeeds after deleting the ignored generated
  `sdkconfig.seeed_xiao_esp32s3` and regenerating it from `sdkconfig.defaults`.
- Upload to `/dev/ttyACM0` still failed with `No serial data received`.
  DTR/RTS and 1200-baud reset attempts did not change the device out of
  `1a86:55d3`. A physical BOOT/RESET or replug is likely required before the
  next flash attempt.
- After the user unplugged a servo driver board, `/dev/ttyACM0` and
  `1a86:55d3` disappeared. Treat that failed upload target as likely not the
  ESP32-S3 webcam. No flashing occurred because esptool never connected.
- Added `tools/verify_uvc.py --loops 10` for repeated Linux V4L2
  open/read/release verification.
- The ESP32 later appeared as `303a:8000 Espressif ESP UVC Device` with
  `/dev/video0` and `/dev/video1`. `/dev/video0` and the by-id `video-index0`
  path passed 10 repeated `640x480` OpenCV open/read/release cycles.
- Descriptor inspection showed the live board was still running the older image:
  frame index 1 remained `1280x720`, so the VGA-default firmware commit had not
  been flashed yet.
- `/dev/video1` timed out when used as a capture source; use
  `video-index0`/`/dev/video0` for verification.
- Starting multiple capture clients concurrently reproduced the old reliability
  problem: later single-client reads timed out even though UVC enumeration
  remained present. A host `usbreset 303a:8000` then hung in the kernel. A
  physical unplug/replug is required before more live testing.
- After physical replug, the board re-enumerated as UVC and again passed 10
  repeated `640x480` reads from the `video-index0` by-id path. A sequential
  FFmpeg `640x480` MJPEG read also succeeded. FFmpeg default-open selected
  `640x480`, and 10 repeated FFmpeg open/read/close cycles succeeded.
- Added a firmware-side stream recovery patch: failed
  `tud_video_n_frame_xfer()` starts are now dropped instead of treated as
  in-flight transfers forever, stale transfers time out and reset the streaming
  endpoint, and stream-stop transitions flush endpoint/task state.
- The patched firmware builds, but it is not flashed yet. The connected board
  exposes UVC only and no `/dev/ttyACM*`/serial-JTAG endpoint, so there is no
  safe software flashing path from the current app state. Flashing still
  requires getting the ESP32-S3 into ROM serial/JTAG bootloader mode or adding a
  firmware reboot-to-bootloader path in a future image.
- Added a future firmware recovery path: the UVC firmware now builds as a
  composite UVC + CDC ACM device. After that image is flashed, the host should
  see both video nodes and a serial node. Sending `bootloader` or
  `reboot-bootloader` to the serial node, or opening it at 1200 baud and
  closing it, requests ESP32-S3 ROM download mode for the next flash. This is
  built and documented, but it is not yet flashed onto the board.

Update from 2026-05-27:
- Re-tested the plugged board. It still enumerates as `303a:8000 Espressif ESP
  UVC Device` with `/dev/video0` and `/dev/video1`, and no `/dev/ttyACM*`.
- Descriptor inspection still shows the UVC-only image with two Video
  interfaces and first advertised frame `1280x720 @ 15fps`.
- `tools/verify_uvc.py --loops 3 --device
  /dev/v4l/by-id/usb-Espressif_ESP_UVC_Device_12345678-video-index0` passed
  with three `640x480` frame reads.
- The currently flashed firmware corresponds to `54e61aa`. Commits through
  `da6cf4b` are firmware-input equivalent because they changed docs only.
- Added `docs/releases.md` and README release mapping. GitHub releases should
  mark `v0.1` as the currently flashed UVC-only image and `v0.2` as the latest
  recovery-capable firmware.

Important: do not reintroduce Wi-Fi/AP camera firmware.
- Earlier HTTP/AP firmware was flashed and then rejected.
- It was erased with `esptool.py erase_flash`.
- Forced Wi-Fi rescan no longer showed `coffee-station-cam`.
- The working implementation is USB Video Class (UVC) only.
- Do not add SSIDs, passwords, AP mode, HTTP streaming, mDNS discovery, or any network-camera fallback.

Standalone repo:
- `/home/brandonin-2/Code/esp32-usb-webcam`

Build command that worked:
```bash
pio run
```

Flash command that worked:
```bash
pio run -t upload --upload-port /dev/ttyACM1
```

Verification command that worked:
```bash
python - <<'PY'
import cv2, os, time
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
time.sleep(1)
ok, frame = cap.read()
print(ok, None if frame is None else frame.shape)
if ok:
    cv2.imwrite('/tmp/esp32-uvc-video0.jpg', frame)
    print(os.path.getsize('/tmp/esp32-uvc-video0.jpg'))
cap.release()
PY
```

Key build issues already solved:
- PlatformIO ESP-IDF mode requires `[platformio] src_dir = main`.
- ESP-IDF 6 / `platform = espressif32@7.0.1` failed with `esp32-camera` including old `driver/ledc.h`; use `platform = espressif32@6.9.0` / ESP-IDF 5.3.1.
- The managed `usb_device_uvc` component triggered a duplicate `usb_descriptors.c.o` action in PlatformIO.
- Fix: vendor `usb_device_uvc` under `components/usb_device_uvc`, compile `tusb/usb_descriptors.c` as part of that component, and remove the `target_sources(${tusb_lib} ...)` package-manager path.
- Removing `cu_pkg_define_version(...)` required adding explicit version compile definitions:
  `USB_DEVICE_UVC_VER_MAJOR=1`, `USB_DEVICE_UVC_VER_MINOR=3`, `USB_DEVICE_UVC_VER_PATCH=0`.
- XIAO ESP32S3 Sense camera pins require Kconfig ranges up to GPIO 48.

Published repo contents:
- `platformio.ini`
- `CMakeLists.txt`
- `partitions.csv`
- `sdkconfig.defaults`
- `main/`
- `components/usb_device_uvc/`
- `README.md`
- `docs/build-notes.md`
- `docs/gist-blog.md`
- `docs/next-agent-handoff.md`
- `assets/esp32-uvc-frame.jpg`

Generated files intentionally excluded:
- `.pio/`
- `managed_components/`
- `sdkconfig.*` except `sdkconfig.defaults`

Recommended next work:
1. Put the ESP32-S3 into ROM download bootloader mode. If no BOOT button is
   accessible, hold GPIO0 low while resetting EN/RST.
2. Flash from this standalone repo.
3. Confirm it re-enumerates as `303a:8000 Espressif ESP UVC Device` plus a CDC
   ACM serial node.
4. Confirm `/dev/video0` capture works reliably after repeated open/close cycles.
5. Confirm the CDC recovery path can reboot the board into ROM download mode.
6. Improve the firmware until it behaves like a normal webcam in common apps:
   stable enumeration, predictable video node, usable default resolution, no capture hangs, reasonable frame rate, and graceful recovery after app close.
