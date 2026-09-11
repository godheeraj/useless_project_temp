"""
hand_tracker.py — MediaPipe Hands processor with exponential smoothing,
landmark geometry extraction, and hand telemetry.
"""

import os
import urllib.request
import time
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import config

# Hand landmark indices
WRIST = 0
THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP = 1, 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP = 5, 6, 7, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP = 9, 10, 11, 12
RING_MCP, RING_PIP, RING_DIP, RING_TIP = 13, 14, 15, 16
PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP = 17, 18, 19, 20

# Standard hand skeletal connections
HAND_CONNECTIONS = [
    (WRIST, THUMB_CMC), (THUMB_CMC, THUMB_MCP), (THUMB_MCP, THUMB_IP), (THUMB_IP, THUMB_TIP),
    (WRIST, INDEX_MCP), (INDEX_MCP, INDEX_PIP), (INDEX_PIP, INDEX_DIP), (INDEX_DIP, INDEX_TIP),
    (INDEX_MCP, MIDDLE_MCP), (MIDDLE_MCP, MIDDLE_PIP), (MIDDLE_PIP, MIDDLE_DIP), (MIDDLE_DIP, MIDDLE_TIP),
    (MIDDLE_MCP, RING_MCP), (RING_MCP, RING_PIP), (RING_PIP, RING_DIP), (RING_DIP, RING_TIP),
    (RING_MCP, PINKY_MCP), (PINKY_MCP, PINKY_PIP), (PINKY_PIP, PINKY_DIP), (PINKY_DIP, PINKY_TIP),
    (WRIST, PINKY_MCP)
]

class HandData:
    """Encapsulates processed landmarks, palm center, and state for one tracked hand."""
    def __init__(self, label, landmarks_norm, screen_w=config.SCREEN_WIDTH, screen_h=config.SCREEN_HEIGHT):
        self.label = label  # "Left" or "Right"
        # 21 points: (x, y, z) normalized
        self.landmarks_norm = landmarks_norm
        # 21 points: (px, py) in game screen coordinates
        self.landmarks_screen = np.array([
            (p[0] * screen_w, p[1] * screen_h) for p in landmarks_norm
        ], dtype=np.float32)

        # Stable Palm Center: centroid of wrist, index_mcp, middle_mcp, and pinky_mcp
        palm_pts_norm = [landmarks_norm[WRIST], landmarks_norm[INDEX_MCP],
                         landmarks_norm[MIDDLE_MCP], landmarks_norm[PINKY_MCP]]
        self.palm_center_norm = np.mean(palm_pts_norm, axis=0)[:2]
        self.palm_center_screen = np.array([
            self.palm_center_norm[0] * screen_w,
            self.palm_center_norm[1] * screen_h
        ], dtype=np.float32)

        # Quick access to key points (in screen pixels)
        self.wrist = self.landmarks_screen[WRIST]
        self.thumb_tip = self.landmarks_screen[THUMB_TIP]
        self.index_tip = self.landmarks_screen[INDEX_TIP]
        self.middle_tip = self.landmarks_screen[MIDDLE_TIP]
        self.ring_tip = self.landmarks_screen[RING_TIP]
        self.pinky_tip = self.landmarks_screen[PINKY_TIP]

        # Normalized coordinates for invariant geometric tests
        self.wrist_norm = landmarks_norm[WRIST][:2]
        self.thumb_tip_norm = landmarks_norm[THUMB_TIP][:2]
        self.index_tip_norm = landmarks_norm[INDEX_TIP][:2]
        self.middle_tip_norm = landmarks_norm[MIDDLE_TIP][:2]
        self.ring_tip_norm = landmarks_norm[RING_TIP][:2]
        self.pinky_tip_norm = landmarks_norm[PINKY_TIP][:2]

class HandTracker:
    def __init__(self, model_path=config.MODEL_PATH, max_hands=config.MAX_HANDS):
        self.model_path = model_path
        self.max_hands = max_hands
        self.smoothing_alpha = config.TRACKING_SMOOTHING_ALPHA

        # Tracked smoothed hands state: list of smoothed landmarks (21, 3) per slot
        self.smoothed_hands = {}
        self.detector = None
        self.start_time = time.time()
        self.last_timestamp_ms = 0

        self._ensure_model_file()
        self._init_landmarker()

    def _ensure_model_file(self):
        """Downloads the official Google MediaPipe task model if missing."""
        if not os.path.exists(self.model_path):
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            print("[HandTracker] Model file not found. Downloading MediaPipe Hand Landmarker model...")
            urllib.request.urlretrieve(url, self.model_path)
            print("[HandTracker] Model downloaded to:", self.model_path)

    def _init_landmarker(self):
        """Creates the HandLandmarker task instance."""
        try:
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=self.max_hands,
                min_hand_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
                min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
                running_mode=vision.RunningMode.VIDEO
            )
            self.detector = vision.HandLandmarker.create_from_options(options)
            print("[HandTracker] MediaPipe HandLandmarker successfully initialized.")
        except Exception as e:
            print("[HandTracker] Error initializing HandLandmarker:", e)
            self.detector = None

    def process_frame(self, frame_bgr):
        """
        Runs MediaPipe hand detection on a BGR camera frame.
        Returns: list of HandData instances (up to 2).
        """
        if self.detector is None or frame_bgr is None:
            return []

        # Convert to RGB MediaPipe Image
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        # Monotonic timestamp in ms
        timestamp_ms = int((time.time() - self.start_time) * 1000)
        if timestamp_ms <= self.last_timestamp_ms:
            timestamp_ms = self.last_timestamp_ms + 1
        self.last_timestamp_ms = timestamp_ms

        try:
            results = self.detector.detect_for_video(mp_image, timestamp_ms)
        except Exception as e:
            # Safe recovery from frame drop or timestamp edge case
            return []

        if not results or not results.hand_landmarks:
            # Clear or decay smoothing history if no hands visible
            self.smoothed_hands.clear()
            return []

        processed_hands = []

        for i, landmarks in enumerate(results.hand_landmarks):
            # Handedness label
            label = "Right" if i == 0 else "Left"
            if results.handedness and i < len(results.handedness):
                categories = results.handedness[i]
                if categories and len(categories) > 0:
                    label = categories[0].category_name

            # Extract raw (x, y, z)
            raw_coords = np.array([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float32)

            # Exponential Moving Average Smoothing
            slot_key = label
            if slot_key in self.smoothed_hands:
                smoothed = (self.smoothing_alpha * raw_coords +
                            (1.0 - self.smoothing_alpha) * self.smoothed_hands[slot_key])
            else:
                smoothed = raw_coords.copy()

            self.smoothed_hands[slot_key] = smoothed

            # Create HandData object
            hand = HandData(label, smoothed)
            processed_hands.append(hand)

        # Sort hands left to right by palm x coordinate for consistent dual-hand mechanics
        processed_hands.sort(key=lambda h: h.palm_center_screen[0])
        return processed_hands

    def draw_landmarks_on_image(self, frame_bgr, hands):
        """
        Draws glowing cyberpunk skeleton overlays on camera frame preview.
        """
        h, w, _ = frame_bgr.shape

        for hand in hands:
            pts = [(int(p[0] * w), int(p[1] * h)) for p in hand.landmarks_norm]

            # Draw bones / connections
            for p1_idx, p2_idx in HAND_CONNECTIONS:
                pt1 = pts[p1_idx]
                pt2 = pts[p2_idx]
                cv2.line(frame_bgr, pt1, pt2, (0, 255, 170), 2, cv2.LINE_AA)

            # Draw joints
            for idx, pt in enumerate(pts):
                if idx in (THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP):
                    # Fingertips highlighted
                    cv2.circle(frame_bgr, pt, 5, (0, 220, 255), -1, cv2.LINE_AA)
                    cv2.circle(frame_bgr, pt, 7, (255, 255, 255), 1, cv2.LINE_AA)
                else:
                    cv2.circle(frame_bgr, pt, 3, (255, 120, 0), -1, cv2.LINE_AA)

            # Draw palm center
            palm_px = (int(hand.palm_center_norm[0] * w), int(hand.palm_center_norm[1] * h))
            cv2.circle(frame_bgr, palm_px, 6, (0, 0, 255), -1, cv2.LINE_AA)
            cv2.circle(frame_bgr, palm_px, 10, (0, 165, 255), 2, cv2.LINE_AA)

            # Hand label tag
            label_text = f"{hand.label.upper()} HAND"
            cv2.putText(frame_bgr, label_text, (palm_px[0] - 30, palm_px[1] - 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)

        return frame_bgr
