# ESP32 USB Webcam Task Log

Current goal: make a standalone public repo for the working ESP32-S3 USB webcam firmware, publish it to GitHub, write a public gist/blog-style build note, and add a project entry with representative asset to `~/Code/jvboid.dev`.

Verified hardware state:
- Board: ESP32-S3, MAC `24:58:7c:e2:a0:f0`
- USB device after successful flash: `303a:8000 Espressif ESP UVC Device`
- Linux devices: `/dev/video0` and `/dev/video1`
- OpenCV verified frame capture from index `0`: `640x480`, saved to `/tmp/esp32-uvc-video0.jpg`
- The image was visually checked and shows a real camera frame.
- Standalone repo build was later verified with `pio run` from `/home/brandonin-2/Code/esp32-usb-webcam`.
- A later host-side USB reset attempt de-enumerated the UVC function on this machine. The firmware was already proven, but another live capture may require physically replugging/resetting the board into the UVC app or bootloader state.

Important: do not reintroduce Wi-Fi/AP camera firmware.
- Earlier HTTP/AP firmware was flashed and then rejected.
- It was erased with `esptool.py erase_flash`.
- Forced Wi-Fi rescan no longer showed `coffee-station-cam`.
- The working implementation is USB Video Class (UVC) only.

Working source currently lives in:
- `/home/brandonin-2/Code/coffee-station/firmware/esp32-usb-webcam`

The standalone repo should be:
- `/home/brandonin-2/Code/esp32-usb-webcam`

Build command that worked:
```bash
pio run -d firmware/esp32-usb-webcam
```

Flash command that worked:
```bash
pio run -d firmware/esp32-usb-webcam -t upload --upload-port /dev/ttyACM1
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

Standalone repo files to include:
- `platformio.ini`
- `CMakeLists.txt`
- `partitions.csv`
- `sdkconfig.defaults`
- `main/`
- `components/usb_device_uvc/`
- `README.md`
- `.gitignore`
- representative asset copied from `/tmp/esp32-uvc-video0.jpg`, likely `assets/esp32-uvc-frame.jpg`

Generated files to exclude:
- `.pio/`
- `managed_components/`
- `dependencies.lock` can be committed only if you want reproducible component resolution; because `usb_device_uvc` is vendored and other dependencies are normal components, prefer committing it if present and stable, but do not commit `.pio`.
- `sdkconfig.seeed_xiao_esp32s3` is generated; prefer not to commit unless needed.

Publishing steps still needed:
1. Copy cleaned firmware into `/home/brandonin-2/Code/esp32-usb-webcam`.
2. Initialize git, commit.
3. Create GitHub repo and push.
4. Create public gist/blog with build notes and issues.
5. Add project entry to `/home/brandonin-2/Code/jvboid.dev` with representative asset.
6. Run whatever validation the site repo uses.
