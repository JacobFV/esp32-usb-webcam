#!/usr/bin/env python3
"""Verify that the ESP32-S3 UVC firmware behaves like a normal webcam."""

from __future__ import annotations

import argparse
import glob
import os
import signal
import sys
import time
from pathlib import Path


class TimeoutError(Exception):
    pass


def _timeout(_signum, _frame):
    raise TimeoutError("capture timed out")


def default_device() -> str:
    by_id = sorted(glob.glob("/dev/v4l/by-id/*ESP_UVC_Device*video-index0"))
    if by_id:
        return by_id[0]
    video_nodes = sorted(glob.glob("/dev/video[0-9]*"))
    if video_nodes:
        return video_nodes[0]
    return "/dev/video0"


def capture_once(cv2, device: str, width: int, height: int, timeout_s: int, out: Path | None) -> tuple[int, int, int]:
    signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(timeout_s)
    cap = None
    try:
        cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            ok, frame = cap.read()
            if ok and frame is not None:
                if out is not None:
                    cv2.imwrite(str(out), frame)
                return frame.shape
            time.sleep(0.05)
        raise TimeoutError("no frame before deadline")
    finally:
        signal.alarm(0)
        if cap is not None:
            cap.release()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default=default_device(), help="V4L2 device path")
    parser.add_argument("--loops", type=int, default=10, help="open/read/release cycles")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--timeout", type=int, default=12, help="seconds per capture")
    parser.add_argument("--save", default="/tmp/esp32-uvc-frame.jpg", help="path for the first captured frame")
    args = parser.parse_args()

    try:
        import cv2
    except ImportError:
        print("OpenCV is required: python -m pip install opencv-python", file=sys.stderr)
        return 2

    device = os.path.realpath(args.device)
    save_path = Path(args.save) if args.save else None
    print(f"device: {args.device} -> {device}", flush=True)
    try:
        for i in range(args.loops):
            out = save_path if i == 0 else None
            shape = capture_once(cv2, args.device, args.width, args.height, args.timeout, out)
            print(f"{i + 1}/{args.loops}: read frame shape={shape}", flush=True)
    except TimeoutError as err:
        print(f"capture failed: {err}", file=sys.stderr, flush=True)
        return 1
    if save_path:
        print(f"saved: {save_path} ({save_path.stat().st_size} bytes)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
