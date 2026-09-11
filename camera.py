"""
camera.py — Threaded, fault-tolerant webcam capture manager.
Ensures zero main-thread blocking, handles horizontal mirroring,
and provides seamless synthetic fallback if no webcam is connected.
"""

import cv2
import numpy as np
import threading
import time
import pygame
import config

class CameraManager:
    def __init__(self, camera_index=config.CAMERA_INDEX, width=config.CAMERA_WIDTH, height=config.CAMERA_HEIGHT):
        self.camera_index = camera_index
        self.target_width = width
        self.target_height = height
        self.mirror = config.MIRROR_CAMERA

        self.cap = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

        self.latest_frame = None
        self.latest_timestamp = 0.0
        self.is_connected = False
        self.error_message = ""

        # Synthetic animation state for fallback
        self._synth_tick = 0

        self._start_capture()

    def _start_capture(self):
        """Attempts to open the webcam and start background capture thread."""
        try:
            # On Windows, cv2.CAP_DSHOW can provide faster init, fallback to default
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_index)

            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
                self.cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
                self.is_connected = True
            else:
                self.is_connected = False
                self.error_message = "Webcam could not be opened (Index %d)" % self.camera_index
        except Exception as e:
            self.is_connected = False
            self.error_message = str(e)

        self.running = True
        self.thread = threading.Thread(target=self._capture_worker, daemon=True)
        self.thread.start()

    def _capture_worker(self):
        """Worker loop running in background thread."""
        while self.running:
            if self.is_connected and self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    if self.mirror:
                        frame = cv2.flip(frame, 1)

                    with self.lock:
                        self.latest_frame = frame
                        self.latest_timestamp = time.time()
                else:
                    # Temporary read failure
                    time.sleep(0.01)
            else:
                # Generate synthetic test frame if no camera
                self._synth_tick += 1
                frame = self._generate_synthetic_frame()
                with self.lock:
                    self.latest_frame = frame
                    self.latest_timestamp = time.time()
                time.sleep(1.0 / config.CAMERA_FPS)

    def _generate_synthetic_frame(self):
        """Creates a high-tech synthetic grid frame when no physical camera is available."""
        h, w = self.target_height, self.target_width
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:, :] = (20, 24, 30)

        # Draw tech grid lines
        grid_size = 40
        for x in range(0, w, grid_size):
            cv2.line(frame, (x, 0), (x, h), (35, 45, 55), 1)
        for y in range(0, h, grid_size):
            cv2.line(frame, (0, y), (w, y), (35, 45, 55), 1)

        # Draw radar pulse circle
        center = (w // 2, h // 2)
        radius = int((self._synth_tick * 4) % (min(w, h) // 2))
        cv2.circle(frame, center, radius, (0, 180, 255), 1)

        # Overlay notification text
        cv2.putText(frame, "SIMULATED SENSOR FEED (NO WEBCAM)", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2)
        cv2.putText(frame, "STATUS: AI AWAITING HAND SENSORS", (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

        return frame

    def get_frame(self):
        """
        Returns (has_frame, frame_bgr).
        Thread-safe copy of the latest captured frame.
        """
        with self.lock:
            if self.latest_frame is None:
                return False, None
            return True, self.latest_frame.copy()

    def get_pygame_surface(self, target_width=None, target_height=None):
        """
        Converts the latest frame into a Pygame Surface for UI rendering.
        """
        with self.lock:
            if self.latest_frame is None:
                return None
            frame = self.latest_frame.copy()

        if target_width and target_height:
            frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_LINEAR)

        # Convert OpenCV BGR to Pygame RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
        return surface

    def stop(self):
        """Stops capture and releases camera resource."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None
        self.is_connected = False
