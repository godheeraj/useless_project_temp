"""
config.py — Configuration and tuning parameters for Mosquito Slapping AI.
Easily adjust gameplay balance, computer vision thresholds, and presentation modes.
"""

import os

# ==============================================================================
# DISPLAY & ENGINE SETTINGS
# ==============================================================================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TARGET_FPS = 60
WINDOW_TITLE = "KOTHU BAT AI"

# Debug & Presentation Modes
DEBUG_MODE = False       # Displays landmark coordinates, angles, hitboxes, and velocities
DEMO_MODE = False        # Make-a-thon mode: Extra large fonts, oversized popups for stage viewing

# Asset & Data Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MODELS_DIR = os.path.join(ASSETS_DIR, "models")
SPRITES_DIR = os.path.join(ASSETS_DIR, "sprites")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
DATA_DIR = os.path.join(BASE_DIR, "data")
SCORES_FILE = os.path.join(DATA_DIR, "scores.json")
MODEL_PATH = os.path.join(MODELS_DIR, "hand_landmarker.task")

# ==============================================================================
# CAMERA & COMPUTER VISION SETTINGS
# ==============================================================================
CAMERA_INDEX = 0
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_FPS = 30
MIRROR_CAMERA = True     # Invert camera horizontally for intuitive mirror-like feedback

# Hand Tracking & Landmark Smoothing
MAX_HANDS = 2
TRACKING_SMOOTHING_ALPHA = 0.50   # Exponential smoothing factor (0.0 to 1.0)
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# ==============================================================================
# GESTURE RECOGNITION THRESHOLDS
# ==============================================================================

# Level 1: Double-Hand Slap (Optimized for natural clap speed and hand occlusion)
SLAP_START_DISTANCE = 0.28        # Normalized distance required to prime the slap
SLAP_CONTACT_DISTANCE = 0.16      # Normalized distance considered contact (generous for palm cups)
SLAP_SPEED_THRESHOLD = 0.35       # Rate of approach required to distinguish slap from resting hands
SLAP_RADIUS = 135                 # Pixel collision radius around slap midpoint
SLAP_COOLDOWN = 0.28              # Seconds before another slap can be detected
SLAP_TIMEOUT = 0.50               # Max seconds from approach to contact

# Level 2: Spider-Man Web Shoot
WEB_SPEED = 1300                  # Pixels per second
WEB_LIFETIME = 0.85               # Projectile lifespan in seconds
WEB_RADIUS = 35                   # Collision radius around web head
WEB_COOLDOWN = 0.32               # Seconds between web shots
WEB_EXPAND_MAX_RADIUS = 60        # Exploding web radius on hit

# Level 3: Double Finger Gun
FINGER_GUN_COOLDOWN = 0.25        # Seconds between laser shots
FINGER_GUN_CONE_ANGLE = 45.0      # Degrees tolerance for pointing toward a mosquito
TARGET_LOCK_TIME = 0.0            # Instant thumb click trigger (replaces timer lock-on)
LASER_BEAM_DURATION = 0.28        # Duration laser beam remains on screen

# ==============================================================================
# LEVEL DEFINITIONS & DIFFICULTY
# ==============================================================================
LEVELS = {
    1: {
        "name": "LEVEL 1: HANDS ON",
        "subtitle": "",
        "gesture_name": "Double-Hand Slap",
        "gesture_desc": "Bring both hands together rapidly to crush the pests!",
        "min_mosquitoes": 3,
        "max_mosquitoes": 5,
        "mosquito_speed_min": 110,
        "mosquito_speed_max": 180,
        "mosquito_scale": 1.25,
        "spawn_interval": 2.2,
        "duration": 30,           # Seconds
        "target_kills": 15,
        "slap_radius_multiplier": 1.0
    },
    2: {
        "name": "LEVEL 2: SPIDER MODE",
        "subtitle": "Spider-Man Web Blast Protocol",
        "gesture_name": "Spider Web Shooter",
        "gesture_desc": "Fold middle & ring fingers, extend thumb, index & pinky!",
        "min_mosquitoes": 7,
        "max_mosquitoes": 10,
        "mosquito_speed_min": 190,
        "mosquito_speed_max": 280,
        "mosquito_scale": 1.0,
        "spawn_interval": 1.4,
        "duration": 30,           # Seconds
        "target_kills": 25,
        "slap_radius_multiplier": 0.8
    },
    3: {
        "name": "LEVEL 3: NO MERCY",
        "subtitle": "Dual-Wield Tactical Finger Gun Execution",
        "gesture_name": "Double Finger Gun",
        "gesture_desc": "Aim index fingers at targets — click either thumb DOWN to fire lasers!",
        "min_mosquitoes": 12,
        "max_mosquitoes": 18,
        "mosquito_speed_min": 280,
        "mosquito_speed_max": 420,
        "mosquito_scale": 0.85,
        "spawn_interval": 0.8,
        "duration": 45,           # Seconds
        "target_kills": 40,
        "slap_radius_multiplier": 0.6
    }
}

# ==============================================================================
# SCORING & MULTIPLIERS
# ==============================================================================
SCORE_PER_KILL = 10
MAX_COMBO_MULTIPLIER = 10

# Dynamic Combo Commentary
COMBO_MESSAGES = {
    1: "Nice.",
    2: "Not bad.",
    3: "Okay, you have experience.",
    4: "WHO HURT YOU?",
    5: "THE MOSQUITOES ARE AFRAID.",
    7: "CALL THE MOSQUITO CONTROL BOARD.",
    10: "KERALA IS SAFE AGAIN.",
    15: "ABSOLUTE PESTILENCE PURGER.",
    20: "YOU ARE THE MOSQUITO."
}

# Dynamic Miss Commentary (Triggered on empty slaps/shots)
MISS_MESSAGES = [
    "Bro slapped air.",
    "Excellent furniture attack.",
    "That mosquito is laughing at you.",
    "0 mosquitoes harmed.",
    "Try hitting the mosquito, not your dignity.",
    "Wind resistance +100.",
    "The wall didn't deserve that."
]
MISS_MESSAGE_COOLDOWN = 1.8      # Seconds between miss message popups

# Level Complete Quotes
LEVEL_TRANSITION_QUOTES = {
    1: "UP NEXT : LEVEL 2 - SPIDER MODE.",
    2: "UP NEXT : LEVEL 3 - NO MERCY.",
    3: "THE MOSQUITO APOCALYPSE HAS CONCLUDED."
}

# Combat Report Rating Titles (Based on total kills)
RANKING_TITLES = [
    (0, 15, "YOU ARE THE MOSQUITO'S SIDEKICK [DEFENSELESS]"),
    (16, 35, "DECENT MOSQUITO MANAGEMENT [APPRENTICE]"),
    (36, 55, "PROFESSIONAL MOSQUITO HATER [VETERAN]"),
    (56, 80, "CERTIFIED BIOLOGICAL HAZARD [ELITE]"),
    (81, 9999, "THE MOSQUITO POPULATION HAS REQUESTED ASYLUM [LEGEND]")
]

# ==============================================================================
# AUDIO & SOUND SETTINGS
# ==============================================================================
AUDIO_SAMPLE_RATE = 44100
AUDIO_CHANNELS = 2
MASTER_VOLUME = 0.85
BUZZ_MAX_VOLUME = 0.4
SFX_VOLUME = 0.9
