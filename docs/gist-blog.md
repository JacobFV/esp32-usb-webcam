# Making An ESP32-S3 Show Up As A Real USB Webcam

I wanted an ESP32 camera board to act like an ordinary webcam. Not a Wi-Fi
stream, not an access point, not a little HTTP camera server: a real USB Video
Class device that Linux would expose as `/dev/video0`.

The working hardware was a Seeed XIAO ESP32S3 Sense. That matters because the
board has native USB, PSRAM, and a camera module. A generic ESP32-CAM module
without native USB cannot become a normal USB webcam just by changing Python or
host-side code.

The firmware that worked is an ESP-IDF project built with PlatformIO. It uses
Espressif's camera driver to capture MJPEG frames and Espressif's
`usb_device_uvc` component to expose those frames over USB UVC.

The most important correction was backing out of the Wi-Fi-camera failure mode.
An AP plus HTTP stream can be useful, but it is not a USB webcam. The final
firmware contains no Wi-Fi setup, no AP mode, no password, and no stream URL.

The build had a few sharp edges:

- PlatformIO needed `[platformio] src_dir = main`.
- ESP-IDF 6 broke the camera dependency on an old LEDC include, so the project
  pins `espressif32@6.9.0`.
- The managed `usb_device_uvc` component duplicated `usb_descriptors.c.o` under
  PlatformIO, so the UVC component is vendored with a small CMake adjustment.
- The XIAO camera pinout needs Kconfig ranges that allow GPIO numbers up to 48.

The final proof was simple: after flashing, Linux reported an `Espressif ESP UVC
Device`, created `/dev/video0`, and OpenCV captured a real `640x480` frame from
it.

Project repo: https://github.com/JacobFV/esp32-usb-webcam
