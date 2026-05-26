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
- `lsusb` currently shows the plugged board as `1a86:55d3 QinHeng Electronics USB Single Serial`.
- `/dev/ttyACM0` exists.
- No `/dev/v4l/by-id/usb-Espressif_ESP_UVC_Device_12345678-video-index0` symlink is currently present.
- This means the next session should start by getting the board back into a clean flash/app state, then re-verifying UVC enumeration and frame capture.

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
1. Replug/reset the board so `/dev/ttyACM0` is usable for flashing.
2. Flash from this standalone repo.
3. Confirm it re-enumerates as `303a:8000 Espressif ESP UVC Device`.
4. Confirm `/dev/video0` capture works reliably after repeated open/close cycles.
5. Improve the firmware until it behaves like a normal webcam in common apps:
   stable enumeration, predictable video node, usable default resolution, no capture hangs, reasonable frame rate, and graceful recovery after app close.
