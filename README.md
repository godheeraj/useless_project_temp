# 🦟 Kothu Bat — Over-Engineered Pest Control

> *"An unnecessarily advanced computer-vision solution to a problem that does not exist."*

Built for the **College Make-a-Thon**, **Mosquito Slapping AI** is an absurd, hilarious, and playable desktop vision game using **Python, OpenCV, MediaPipe Hands, and Pygame**.

The application uses your **webcam as the primary controller**. By tracking up to 21 3D hand landmarks in real-time, the custom geometric AI state machine recognizes three distinct gestures across three progressively chaotic levels to neutralize virtual mosquito swarms.

---

## 🌟 Key Features

1. **Augmented Reality (AR) Camera Feed Gameplay**:
   - **Mosquitoes in your Room**: Instead of a separate synthetic screen, **the live mirrored webcam feed is the entire game background**.
   - Mosquitoes fly and buzz directly around your physical head, body, and surroundings.
   - Cartoon blood splatters, shockwave rings, web nets, and lasers appear directly overlaid onto your live camera video.
2. **Three Tactical Gesture Levels**:
   - **Level 1 — HANDS ON**: The **Optimized Double-Hand Slap**. Features adaptive hand-scale thresholds, instant-clap triggers, MediaPipe hand-occlusion recovery, and real-time AR proximity guide lines with expanding shockwaves.
   - **Level 2 — SPIDER MODE**: The **Spider-Man Web Shooter (🤘)**. Fold middle and ring fingers, extend thumb, index, and pinky to fire animated virtual silk projectiles with iconic *"THWIP!"* feedback.
   - **Level 3 — NO MERCY**: **Dual Tactical Finger Guns (👈 👉)**. Aim both index fingers at mosquitoes to lock onto targets, then **click either thumb DOWN** to instantly trigger the dual orbital laser strike (*"PEW PEW!"*) with screen shake and explosive splats.
3. **Auto-Start Countdown**:
   - The calibration screen detects when **both hands are visible** to the camera and automatically begins a **3-second animated countdown** before launching Level 1 — no button press required.
   - If either hand leaves the frame during the countdown, it cancels gracefully back to the calibration screen.
   - The *"PROCEED TO GAME"* and *"SKIP >"* buttons remain available as an instant fallback.
4. **Pause Menu**:
   - Press **ESC** at any time during gameplay to open the **Pause Menu** overlay.
   - Options: **Resume** (continue playing), **Quit to Menu** (return to main menu), **Sound On/Off** (toggle all audio).
   - ESC again or clicking *Resume* returns seamlessly to the game where it left off.
3. **Procedural Audio & Cartoon Visuals**:
   - Built-in procedural sound engine synthesizing physical slap thuds, web chirps, sci-fi laser zaps, dynamic proximity buzzing, and victory fanfares.
   - Animated mosquito sprites with 30 Hz flapping wings, directional tilt, and comical "X" eyes on death.
   - 6 flight behaviors: Random wander, sinusoidal wave, sudden direction darts, acceleration sprints, hovering, and zig-zags.
4. **Tactical Military HUD**:
   - Real-time **Military Mosquito Threat Radar** in the top-right corner with sweeping beam and live mosquito blips (🟢 LOW, 🟡 MODERATE, 🔴 EXTREME).
   - Compact **AI Telemetry HUD** in the bottom-left corner displaying real-time hand counts, tracking status, and gesture match percentages.
5. **Hilarious Combat Dossier**:
   - Evaluates your performance with absurd metrics: Mosquito Kill Rate, Slap Efficiency, Average Reaction Time, and the proprietary **Kerala Survival Rating (%)**.
   - Assigns dynamic rank titles (e.g., *"YOU ARE THE MOSQUITO'S SIDEKICK"*, *"PROFESSIONAL MOSQUITO HATER"*, *"THE MOSQUITO POPULATION HAS REQUESTED ASYLUM"*).
   - Each kill is worth **10 points**, with combo multipliers up to **10×** for consecutive kills.
6. **Presentation & Debug Modes**:
   - `DEBUG_MODE` (`D` key): Displays FPS, hand counts, palm coordinates, slap velocity, hitboxes, and gesture match percentages.
   - `DEMO_MODE` (`M` key): Make-a-Thon presentation mode with oversized typography and high-contrast popups legible to judges from 5+ meters away.
7. **Graceful Fallbacks**:
   - If no webcam is available or tracking is temporarily interrupted, the game displays high-tech alerts and allows mouse clicks / spacebar to simulate gestures for testing and accessibility.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10 to 3.13+**
- A standard USB or built-in webcam
- Windows, macOS, or Linux

### 2. Installation

Clone or open the project folder, then install the dependencies:

```bash
pip install -r requirements.txt
```

*(Dependencies: `pygame>=2.6.0`, `opencv-python>=4.10.0`, `mediapipe>=0.10.0`, `numpy>=1.26.0`)*

### 3. Launch the Game

Run the main application:

```bash
python main.py
```

---

## 🎮 Gameplay & Controls

| Input / Gesture | Action | Level / Screen |
| :--- | :--- | :--- |
| **Double-Hand Slap** 🤲 | Bring both palms together rapidly | **Level 1** |
| **Spider Web Gesture** 🤘 | Fold middle & ring fingers, extend thumb, index, pinky | **Level 2** |
| **Dual Finger Guns** 👈 👉 | Extend both index fingers — click either thumb DOWN to fire | **Level 3** |
| **Mouse Click / Spacebar** | Manual action fallback (simulate slap/web/laser) | Any Level |
| **Key `D`** | Toggle Developer Debug Mode | Anytime |
| **Key `M`** | Toggle Stage Demo Presentation Mode | Anytime |
| **Key `ESC`** | Open Pause Menu (during gameplay) / Back to Menu | In-Game |

---

## 🧠 How the Gesture Recognition Works

Rather than relying on brittle raw pixel coordinates or heavy external deep learning models, the system leverages **MediaPipe Hands** landmark geometry combined with temporal smoothing:

### 1. Exponential Moving Average Smoothing
Camera sensor noise and high-frequency hand tremors are filtered using:
$$\hat{P}_t = \alpha P_t + (1 - \alpha)\hat{P}_{t-1}$$
where $\alpha = 0.55$. This guarantees smooth tracking without introducing perceptible input lag.

### 2. Level 1: Slap State Machine
To differentiate a genuine slap from simply resting hands together, the engine uses a 4-stage state machine:
$$\text{OPEN} \xrightarrow{\Delta d / \Delta t < -v_{\text{threshold}}} \text{APPROACH} \xrightarrow{d < d_{\text{contact}}} \text{CONTACT} \xrightarrow{} \text{COOLDOWN} \xrightarrow{d > d_{\text{start}}} \text{OPEN}$$
The midpoint between palms:
$$P_{\text{slap}} = \frac{P_{\text{left\_palm}} + P_{\text{right\_palm}}}{2}$$
destroys all mosquitoes within `SLAP_RADIUS` (configurable in `config.py`).

### 3. Level 2: Spider-Man Web Geometry (🤘)
Evaluates joint relative distances to the wrist:
- **Extended Fingers (Index, Pinky)**: $\text{dist}(\text{Tip}, \text{Wrist}) > 1.12 \times \text{dist}(\text{PIP}, \text{Wrist})$
- **Folded Fingers (Middle, Ring)**: $\text{dist}(\text{Tip}, \text{Wrist}) < 1.05 \times \text{dist}(\text{PIP}, \text{Wrist})$
- Vector heading: $\vec{v} = \frac{P_{\text{index\_tip}} - P_{\text{wrist}}}{\|P_{\text{index\_tip}} - P_{\text{wrist}}\|}$ launches the web projectile along the player's aim.

### 4. Level 3: Dual Finger Guns (👈 👉)
Requires both hands to independently satisfy the finger-gun pose (Index extended, Thumb raised, others folded). Aiming rays projected from both index fingertips calculate intersection angles with mosquitoes. A lock-on target is identified, and the laser fires **instantly when either hand's thumb clicks DOWN** (UP→DOWN thumb transition), triggering the dual laser volley.

### 5. Auto-Start Countdown
When the calibration screen detects `len(hands) >= 2`, a 3-second countdown begins automatically. The countdown decrements each frame and calls `start_level(1)` upon reaching zero. If the hand count drops below 2 mid-countdown, it cancels cleanly back to calibration.

### 6. Pause Menu
`ESC` during `GameState.PLAYING` transitions to `GameState.PAUSED`. The pause overlay renders on top of a dimmed camera feed and presents three options: **Resume** (returns to `PLAYING`), **Quit to Menu** (returns to `MENU`), and **Sound On/Off** (calls `SoundManager.toggle_sound()`). Game updates and buzzing are fully suspended during the paused state.

---

## 📂 Project Architecture

```
useless_project/
├── main.py                 # Application entry point & 60 FPS master game loop
├── config.py               # Configurable thresholds, speeds, and humorous text
├── camera.py               # Threaded OpenCV capture with horizontal mirroring & fallbacks
├── hand_tracker.py         # MediaPipe HandLandmarker wrapper & landmark smoothing
├── gesture_detector.py     # Rule-based geometric detectors (Slap, Web, Finger Guns)
├── mosquito.py             # Mosquito agents with 6 flight patterns & procedural sprites
├── game.py                 # Central state machine (Menu, Calibration, Play, GameOver)
├── ui.py                   # UI engine: menus, radar HUD, camera PIP, combat report
├── effects.py              # Visual particle engine: cartoon splats, web trails, lasers
├── sound.py                # Procedural audio synthesizer (slap, buzz, web, laser, fanfare)
├── statistics.py           # Combat statistics tracker & local high scores JSON
├── assets/
│   ├── models/hand_landmarker.task # MediaPipe Hand Landmarker model
│   ├── sprites/            # Procedurally generated mosquito sprites
│   └── sounds/             # Synthesized sound effects
├── data/
│   └── scores.json         # Local high scores & leaderboard history
├── requirements.txt        # Python dependency manifest
└── README.md               # Complete project manual & presentation guide
```

---

## 🛠️ Tuning & Configuration (`config.py`)

All gameplay mechanics and computer-vision parameters can be adjusted in `config.py`:

```python
# Slap Sensitivity
SLAP_START_DISTANCE = 0.32        # Normalized distance to prime slap
SLAP_CONTACT_DISTANCE = 0.11      # Normalized distance for slap contact
SLAP_SPEED_THRESHOLD = 0.55       # Normalized distance delta/sec for slap velocity
SLAP_RADIUS = 95                  # Collision radius in pixels

# Web Shooter
WEB_SPEED = 1300                  # Projectile velocity in px/sec
WEB_COOLDOWN = 0.32               # Debounce interval between shots

# Presentation Modes
DEBUG_MODE = False                # Toggle with 'D' key
DEMO_MODE = False                 # Toggle with 'M' key
```

---

## 🔧 Troubleshooting

### 1. Webcam is not detected
- Check that another application (Zoom, Teams, Discord, or browser) is not currently holding an exclusive lock on the camera.
- If you have multiple cameras, change `CAMERA_INDEX = 0` to `CAMERA_INDEX = 1` in `config.py`.
- If no webcam is available, the game will automatically switch to **Simulated Sensor Mode** and enable mouse clicks / spacebar for gesture simulation.

### 2. Hand tracking feels jittery
- Ensure adequate lighting on your hands. Dark rooms or strong backlighting reduce computer vision confidence.
- Adjust `TRACKING_SMOOTHING_ALPHA` in `config.py` (e.g. set to `0.40` for heavier smoothing).

### 3. Audio is silent
- Pygame sound uses procedural synthesis via NumPy. Ensure your system volume is turned on and speakers/headphones are selected as the default audio device.
