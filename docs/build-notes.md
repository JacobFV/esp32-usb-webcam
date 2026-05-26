# Building A Real USB Webcam On ESP32-S3

This project started with a tempting wrong answer: treat the ESP32-CAM as a
network camera. That path worked mechanically, but it was not the requested
device class. The requirement was a USB webcam: when plugged in, the host should
see a standard UVC camera and create `/dev/video*`.

## What Worked

The working target is a Seeed XIAO ESP32S3 Sense. It has native USB, PSRAM, and
an attached camera module, which makes it suitable for a USB Video Class device.

The successful firmware uses:

- PlatformIO with ESP-IDF
- `platform = espressif32@6.9.0`
- Espressif's `esp32-camera` component
- Espressif's `usb_device_uvc` component, vendored locally
- MJPEG frames from the camera passed through USB UVC

After flashing, Linux detected:

```text
303a:8000 Espressif ESP UVC Device
/dev/video0
/dev/video1
```

OpenCV successfully captured a `640x480` MJPEG frame from `/dev/video0`.

## The Main False Start

The first implementation made the board behave like a Wi-Fi camera with an AP
and HTTP stream. That is useful for some ESP32-CAM modules, but it is not a USB
webcam. The AP firmware was erased and the project now intentionally contains no
Wi-Fi credentials, no access point setup, no web server, and no stream URL.

## Build Issues Solved

PlatformIO's ESP-IDF mode expects the application source directory to be stated
explicitly:

```ini
[platformio]
src_dir = main
```

The newest PlatformIO Espressif platform line pulled in ESP-IDF 6, where the
camera component failed on an older LEDC include:

```text
driver/ledc.h
```

Pinning PlatformIO to `espressif32@6.9.0` kept the build on ESP-IDF 5.3.x and
matched the camera component.

The managed `usb_device_uvc` component also caused a duplicate
`usb_descriptors.c.o` action under PlatformIO. The fix was to vendor the
component under `components/usb_device_uvc`, compile `tusb/usb_descriptors.c` as
part of that component, and avoid the package-manager CMake path that appended
the same source to the TinyUSB target.

Vendoring also meant replacing generated package version definitions with
explicit compile definitions:

```text
USB_DEVICE_UVC_VER_MAJOR=1
USB_DEVICE_UVC_VER_MINOR=3
USB_DEVICE_UVC_VER_PATCH=0
```

The XIAO ESP32S3 Sense pinout uses high GPIO numbers, so the camera Kconfig
ranges had to allow pins up to GPIO 48.

## Verification

The final verification was deliberately host-side, because a USB webcam is only
done when the operating system can use it as a camera:

```bash
lsusb | rg '303a:8000|UVC|Espressif'
ls -l /dev/v4l/by-id/
```

Then a frame was captured through V4L2:

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

The verified output was a real `640x480` camera frame.
