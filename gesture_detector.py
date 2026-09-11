"""
gesture_detector.py — Geometric rule-based hand gesture recognition engine.
Implements:
1. Level 1: Double-Hand Velocity Slap (OPEN -> APPROACH -> CONTACT -> COOLDOWN state machine)
2. Level 2: Spider-Man Web Shooter (🤘 middle/ring folded, index/pinky/thumb extended)
3. Level 3: Dual Finger Guns (👈 👉 index extended, thumb raised, other fingers folded)
"""

import math
import time
import numpy as np
import config
from hand_tracker import (
    WRIST, THUMB_CMC, THUMB_MCP, THUMB_IP, THUMB_TIP,
    INDEX_MCP, INDEX_PIP, INDEX_DIP, INDEX_TIP,
    MIDDLE_MCP, MIDDLE_PIP, MIDDLE_DIP, MIDDLE_TIP,
    RING_MCP, RING_PIP, RING_DIP, RING_TIP,
    PINKY_MCP, PINKY_PIP, PINKY_DIP, PINKY_TIP
)

# ==============================================================================
# GEOMETRIC UTILITIES
# ==============================================================================

def distance_2d(p1, p2):
    """Euclidean distance between two 2D points."""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def distance_3d(p1, p2):
    """Euclidean distance between two 3D points."""
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)

def is_finger_extended(hand, tip_idx, pip_idx, mcp_idx=WRIST, extension_ratio=1.12):
    """
    Returns True if fingertip is significantly farther from wrist than PIP joint.
    Works reliably across different hand scales and camera distances.
    """
    wrist = hand.landmarks_norm[WRIST]
    tip = hand.landmarks_norm[tip_idx]
    pip = hand.landmarks_norm[pip_idx]

    dist_tip_wrist = distance_2d(tip[:2], wrist[:2])
    dist_pip_wrist = distance_2d(pip[:2], wrist[:2])

    return dist_tip_wrist > (dist_pip_wrist * extension_ratio)

def is_finger_folded(hand, tip_idx, pip_idx, mcp_idx=WRIST, fold_ratio=1.05):
    """
    Returns True if fingertip is curled inward towards wrist/palm relative to PIP.
    """
    wrist = hand.landmarks_norm[WRIST]
    tip = hand.landmarks_norm[tip_idx]
    pip = hand.landmarks_norm[pip_idx]

    dist_tip_wrist = distance_2d(tip[:2], wrist[:2])
    dist_pip_wrist = distance_2d(pip[:2], wrist[:2])

    return dist_tip_wrist < (dist_pip_wrist * fold_ratio)

def is_thumb_extended(hand):
    """Checks if thumb is extended away from index base."""
    thumb_tip = hand.landmarks_norm[THUMB_TIP]
    index_mcp = hand.landmarks_norm[INDEX_MCP]
    wrist = hand.landmarks_norm[WRIST]
    dist_thumb_index = distance_2d(thumb_tip[:2], index_mcp[:2])
    dist_wrist_index = distance_2d(wrist[:2], index_mcp[:2])
    return dist_thumb_index > (dist_wrist_index * 0.70)

# ==============================================================================
# LEVEL 1: DOUBLE-HAND SLAP DETECTOR (OPTIMIZED)
# ==============================================================================

class SlapDetector:
    """
    Optimized double-hand slap detector:
    - Adaptive to hand scale (works close or far from webcam)
    - Instant-clap trigger (no frame-lag or dropped fast claps)
    - Occlusion-aware: recognizes when clapping hands temporarily merge in MediaPipe
    - Guarantees hands must separate before re-triggering
    """
    STATE_OPEN = "OPEN"
    STATE_APPROACH = "APPROACH"
    STATE_COOLDOWN = "COOLDOWN"

    def __init__(self):
        self.state = self.STATE_OPEN
        self.last_time = time.time()
        self.approach_start_time = 0.0
        self.cooldown_until = 0.0
        self.last_velocity = 0.0
        self.last_known_midpoint = None
        # History format: [(timestamp, distance, midpoint_screen)]
        self.history = []

    def update(self, hands):
        """
        Updates slap state given current frame's detected hands.
        Returns: (slap_event_fired, slap_screen_pos, confidence_score)
        """
        now = time.time()
        dt = max(now - self.last_time, 0.001)
        self.last_time = now

        # Prune history older than 0.35s
        self.history = [entry for entry in self.history if now - entry[0] <= 0.35]

        # ----------------------------------------------------------------------
        # CASE A: Two hands detected
        # ----------------------------------------------------------------------
        if len(hands) >= 2:
            hand_a, hand_b = hands[0], hands[1]
            dist_norm = distance_2d(hand_a.palm_center_norm, hand_b.palm_center_norm)
            mid_screen = (hand_a.palm_center_screen + hand_b.palm_center_screen) / 2.0
            self.last_known_midpoint = mid_screen

            # Hand scale estimation (wrist to index MCP)
            scale_a = distance_2d(hand_a.wrist_norm, hand_a.landmarks_norm[INDEX_MCP][:2])
            scale_b = distance_2d(hand_b.wrist_norm, hand_b.landmarks_norm[INDEX_MCP][:2])
            avg_scale = max((scale_a + scale_b) / 2.0, 0.06)

            # Adaptive contact threshold based on hand scale
            contact_thresh = max(config.SLAP_CONTACT_DISTANCE, avg_scale * 1.35)
            start_thresh = max(config.SLAP_START_DISTANCE, avg_scale * 2.2)

            self.history.append((now, dist_norm, mid_screen))

            # Compute approach velocity over recent frames
            velocity = 0.0
            if len(self.history) >= 2:
                dt_hist = self.history[-1][0] - self.history[0][0]
                if dt_hist > 0.01:
                    velocity = (self.history[-1][1] - self.history[0][1]) / dt_hist
            self.last_velocity = velocity

            max_recent_dist = max(entry[1] for entry in self.history)

            # 1. Check Cooldown
            if now < self.cooldown_until:
                if dist_norm > start_thresh * 0.85:
                    self.state = self.STATE_OPEN
                return False, None, 0.0

            # 2. Check for approach motion
            if dist_norm < start_thresh and velocity < -config.SLAP_SPEED_THRESHOLD * 0.6:
                if self.state == self.STATE_OPEN:
                    self.state = self.STATE_APPROACH
                    self.approach_start_time = now

            # 3. CONTACT DETECTION (High-Responsiveness)
            # Fires if:
            # - Current distance is within contact threshold
            # AND (we were approaching, OR velocity is negative, OR hands came together from further away)
            is_contact = dist_norm <= contact_thresh
            is_fast_close = (velocity < -config.SLAP_SPEED_THRESHOLD * 0.5) or (max_recent_dist - dist_norm > 0.07)

            if is_contact and (self.state == self.STATE_APPROACH or is_fast_close):
                slap_pos = mid_screen.copy()
                speed_score = min(abs(velocity) / max(config.SLAP_SPEED_THRESHOLD, 0.01), 1.0)
                confidence = float(np.clip(0.75 + 0.20 * speed_score, 0.7, 0.99))

                self.state = self.STATE_COOLDOWN
                self.cooldown_until = now + config.SLAP_COOLDOWN
                self.history.clear()
                return True, slap_pos, confidence

            # Reset approach state if timed out
            if self.state == self.STATE_APPROACH and (now - self.approach_start_time > config.SLAP_TIMEOUT):
                self.state = self.STATE_OPEN

            return False, None, 0.0

        # ----------------------------------------------------------------------
        # CASE B: One or zero hands (MediaPipe occlusion during physical clap)
        # ----------------------------------------------------------------------
        else:
            if now < self.cooldown_until:
                return False, None, 0.0

            # If we had 2 hands approaching very fast in the last 120ms and suddenly dropped to 1 hand,
            # this is a physical hand-on-hand slap occlusion!
            if len(self.history) >= 2 and self.last_known_midpoint is not None:
                recent_entries = [e for e in self.history if now - e[0] <= 0.14]
                if len(recent_entries) >= 2:
                    min_recent_dist = min(e[1] for e in recent_entries)
                    if min_recent_dist < config.SLAP_CONTACT_DISTANCE * 1.5 and self.last_velocity < -config.SLAP_SPEED_THRESHOLD * 0.7:
                        slap_pos = self.last_known_midpoint.copy()
                        if len(hands) == 1:
                            # Refine with current single palm if nearby
                            single_palm = hands[0].palm_center_screen
                            if distance_2d(single_palm, slap_pos) < 180:
                                slap_pos = (slap_pos + single_palm) / 2.0

                        self.state = self.STATE_COOLDOWN
                        self.cooldown_until = now + config.SLAP_COOLDOWN
                        self.history.clear()
                        return True, slap_pos, 0.88

            # Clear approach state if hands completely missing
            self.state = self.STATE_OPEN
            return False, None, 0.0

# ==============================================================================
# LEVEL 2: SPIDER-MAN WEB SHOOT DETECTOR (🤘)
# ==============================================================================

class SpiderWebDetector:
    """
    Detects Spider-Man web shooter pose:
    - Middle & ring fingers folded into palm
    - Index & pinky fingers extended outwards
    - Thumb extended/abducted
    Works on either hand.
    """
    def __init__(self):
        self.last_shot_time = 0.0
        self.last_hand_used = None

    def check_hand_pose(self, hand):
        """Returns (is_web_pose, confidence_score)"""
        # Extended fingers: Index, Pinky, Thumb
        index_ext = is_finger_extended(hand, INDEX_TIP, INDEX_PIP)
        pinky_ext = is_finger_extended(hand, PINKY_TIP, PINKY_PIP)
        thumb_ext = is_thumb_extended(hand)

        # Folded fingers: Middle, Ring
        middle_folded = is_finger_folded(hand, MIDDLE_TIP, MIDDLE_PIP)
        ring_folded = is_finger_folded(hand, RING_TIP, RING_PIP)

        score = 0.0
        if index_ext: score += 0.25
        if pinky_ext: score += 0.25
        if middle_folded: score += 0.25
        if ring_folded: score += 0.25
        if thumb_ext: score += 0.15
        score = min(score, 1.0)

        is_match = (index_ext and pinky_ext and middle_folded and ring_folded)
        return is_match, score

    def update(self, hands):
        """
        Evaluates hands for web shooting pose.
        Returns: (web_event_fired, origin_screen, direction_vector, confidence)
        """
        now = time.time()
        if now - self.last_shot_time < config.WEB_COOLDOWN:
            return False, None, None, 0.0

        best_score = 0.0
        chosen_hand = None

        for hand in hands:
            is_match, score = self.check_hand_pose(hand)
            if score > best_score:
                best_score = score
            if is_match:
                chosen_hand = hand
                break

        if chosen_hand is not None:
            # Compute shooting direction: vector from wrist to index tip (or midpoint of index and pinky)
            wrist_sc = chosen_hand.wrist
            index_sc = chosen_hand.index_tip
            pinky_sc = chosen_hand.pinky_tip
            target_sc = (index_sc + pinky_sc) / 2.0

            dx = target_sc[0] - wrist_sc[0]
            dy = target_sc[1] - wrist_sc[1]
            length = math.hypot(dx, dy)
            if length > 1e-5:
                direction = np.array([dx / length, dy / length], dtype=np.float32)
            else:
                direction = np.array([0.0, -1.0], dtype=np.float32)

            origin = chosen_hand.palm_center_screen.copy()
            self.last_shot_time = now
            self.last_hand_used = chosen_hand.label
            return True, origin, direction, float(best_score)

        return False, None, None, float(best_score)

# ==============================================================================
# LEVEL 3: DUAL FINGER GUN DETECTOR (👈 👉)
# ==============================================================================

class FingerGunDetector:
    """
    Detects tactical finger gun pose and thumb-click trigger:
    - Index finger extended forward (aiming ray)
    - Middle, ring, and pinky folded into palm
    - Thumb acts as hammer/trigger:
      - Cocked UP: gun is armed and aiming
      - Clicked DOWN: triggers laser discharge immediately!
    - Works with either single hand or dual-wielding hands.
    """
    def __init__(self):
        self.last_fire_time = 0.0
        self.locked_target_id = None
        self.last_update_time = time.time()
        # Track thumb cocked status: {hand_label: bool}
        self.thumb_cocked = {}

    def check_gun_pose(self, hand):
        """
        Checks if a hand is in finger-gun pose (index extended, others folded).
        Returns: (is_gun_aiming, is_thumb_up, confidence_score)
        """
        index_ext = is_finger_extended(hand, INDEX_TIP, INDEX_PIP)
        middle_fold = is_finger_folded(hand, MIDDLE_TIP, MIDDLE_PIP)
        ring_fold = is_finger_folded(hand, RING_TIP, RING_PIP)
        pinky_fold = is_finger_folded(hand, PINKY_TIP, PINKY_PIP)

        # Scale based on wrist to index MCP distance
        scale = max(distance_2d(hand.wrist_norm, hand.landmarks_norm[INDEX_MCP][:2]), 0.05)
        dist_thumb_mcp = distance_2d(hand.thumb_tip_norm, hand.landmarks_norm[INDEX_MCP][:2])
        dist_thumb_pip = distance_2d(hand.thumb_tip_norm, hand.landmarks_norm[INDEX_PIP][:2])

        thumb_ratio_mcp = dist_thumb_mcp / scale
        thumb_ratio_pip = dist_thumb_pip / scale

        # Thumb is cocked UP if extended away from index knuckle/PIP
        is_thumb_up = (thumb_ratio_mcp > 0.60 and thumb_ratio_pip > 0.50)
        # Thumb is clicked DOWN if pulled close to index knuckle/PIP
        is_thumb_down = (thumb_ratio_mcp < 0.52 or thumb_ratio_pip < 0.44)

        score = 0.0
        if index_ext: score += 0.35
        if middle_fold: score += 0.25
        if ring_fold: score += 0.20
        if pinky_fold: score += 0.20

        # Gun pose requires index extended and middle/ring folded
        is_gun = index_ext and middle_fold and ring_fold
        return is_gun, is_thumb_up, is_thumb_down, score

    def update(self, hands, mosquitoes):
        """
        Evaluates finger guns and detects thumb click trigger on either hand.
        Returns:
            fire_event (bool),
            left_origin (np.ndarray),
            right_origin (np.ndarray),
            target_pos (np.ndarray),
            is_locked (bool),
            lock_progress (float),
            confidence (float)
        """
        now = time.time()
        self.last_update_time = now

        if len(hands) == 0:
            self.thumb_cocked.clear()
            self.locked_target_id = None
            return False, None, None, None, False, 0.0, 0.0

        gun_hands = []
        clicked_hand = None
        scores = []

        for i, hand in enumerate(hands):
            hand_id = getattr(hand, "label", f"hand_{i}")
            is_gun, is_thumb_up, is_thumb_down, score = self.check_gun_pose(hand)
            scores.append(score)

            if is_gun:
                gun_hands.append(hand)
                # Was this hand previously cocked?
                was_cocked = self.thumb_cocked.get(hand_id, True)

                # Detect transition from UP (cocked) -> DOWN (clicked)
                if was_cocked and is_thumb_down:
                    self.thumb_cocked[hand_id] = False
                    if clicked_hand is None:
                        clicked_hand = hand
                elif is_thumb_up:
                    self.thumb_cocked[hand_id] = True
            else:
                self.thumb_cocked[hand_id] = True

        avg_conf = float(np.mean(scores)) if scores else 0.0

        if not gun_hands:
            self.locked_target_id = None
            return False, None, None, None, False, 0.0, avg_conf

        # Determine beam origins
        if len(gun_hands) >= 2:
            origin_l = gun_hands[0].index_tip.copy()
            origin_r = gun_hands[1].index_tip.copy()
            aim_hands = gun_hands[:2]
        else:
            origin_l = gun_hands[0].index_tip.copy()
            origin_r = gun_hands[0].index_tip.copy()
            aim_hands = [gun_hands[0]]

        # Calculate aiming rays for active gun hands
        aim_vectors = []
        for h in aim_hands:
            # Ray from index MCP to index tip gives accurate pointing direction
            ray = h.index_tip - h.landmarks_screen[INDEX_MCP]
            norm = np.linalg.norm(ray)
            if norm > 1e-5:
                aim_vectors.append((h.index_tip, ray / norm))
            else:
                # Fallback to wrist-to-tip
                ray_w = h.index_tip - h.wrist
                norm_w = np.linalg.norm(ray_w)
                aim_vectors.append((h.index_tip, (ray_w / norm_w) if norm_w > 1e-5 else np.array([0.0, -1.0])))

        # Find best candidate mosquito aligned with any gun's aiming cone
        best_candidate = None
        best_angle_score = 99999.0
        min_cos = math.cos(math.radians(config.FINGER_GUN_CONE_ANGLE))

        for m in mosquitoes:
            if not m.is_alive:
                continue
            m_pos = np.array([m.x, m.y], dtype=np.float32)

            for tip, direction in aim_vectors:
                to_m = m_pos - tip
                dist = np.linalg.norm(to_m)
                if dist < 1e-5:
                    continue
                to_m_norm = to_m / dist
                cos_sim = np.dot(direction, to_m_norm)

                if cos_sim > min_cos:
                    # Score based on angular alignment and proximity
                    angle_err = 1.0 - cos_sim
                    if angle_err < best_angle_score:
                        best_angle_score = angle_err
                        best_candidate = m

        if best_candidate is not None:
            target_pos = np.array([best_candidate.x, best_candidate.y], dtype=np.float32)
            self.locked_target_id = best_candidate.id
            is_locked = True
            lock_prog = 1.0
        else:
            self.locked_target_id = None
            is_locked = False
            lock_prog = 0.0
            # Project aim ray into distance for default visual targeting
            primary_tip, primary_dir = aim_vectors[0]
            target_pos = primary_tip + primary_dir * 500.0
            target_pos[0] = np.clip(target_pos[0], 40, config.SCREEN_WIDTH - 40)
            target_pos[1] = np.clip(target_pos[1], 40, config.SCREEN_HEIGHT - 40)

        # Trigger laser when either thumb clicks!
        fire_event = False
        if clicked_hand is not None:
            if now - self.last_fire_time >= config.FINGER_GUN_COOLDOWN:
                fire_event = True
                self.last_fire_time = now

        return fire_event, origin_l, origin_r, target_pos, is_locked, lock_prog, avg_conf

# ==============================================================================
# LEVEL COMPLETE: BOTH FISTS DETECTOR (✊✊)
# ==============================================================================

class BothFistsDetector:
    """
    Detects both hands simultaneously forming a tight fist (all fingers curled
    inward to form a ball). Requires the pose to be held for HOLD_DURATION
    seconds before firing, preventing accidental triggers from mid-gesture
    transitions. Resets automatically when either hand opens.
    """
    HOLD_DURATION = 0.6  # seconds both fists must be held before triggering

    def __init__(self):
        self.hold_start_time = None
        self.progress = 0.0  # 0.0 → 1.0 fill progress

    def _is_fist(self, hand):
        """
        Returns True when all four fingers AND thumb are fully curled into a fist.
        Uses a slightly tighter fold_ratio than the standard helper so that
        half-closed hands don't accidentally trigger.
        """
        index_folded  = is_finger_folded(hand, INDEX_TIP,  INDEX_PIP,  fold_ratio=0.96)
        middle_folded = is_finger_folded(hand, MIDDLE_TIP, MIDDLE_PIP, fold_ratio=0.96)
        ring_folded   = is_finger_folded(hand, RING_TIP,   RING_PIP,   fold_ratio=0.96)
        pinky_folded  = is_finger_folded(hand, PINKY_TIP,  PINKY_PIP,  fold_ratio=0.96)
        thumb_folded  = not is_thumb_extended(hand)
        return index_folded and middle_folded and ring_folded and pinky_folded and thumb_folded

    def update(self, hands):
        """
        Call once per frame with the current hand list.
        Returns: (fired: bool, progress: float 0.0–1.0)
          - fired=True when both fists have been held for HOLD_DURATION.
          - progress reflects how far through the hold the player is (for UI bar).
        """
        now = time.time()

        both_fists = (
            len(hands) >= 2
            and self._is_fist(hands[0])
            and self._is_fist(hands[1])
        )

        if both_fists:
            if self.hold_start_time is None:
                self.hold_start_time = now
            elapsed = now - self.hold_start_time
            self.progress = min(elapsed / self.HOLD_DURATION, 1.0)
            if elapsed >= self.HOLD_DURATION:
                # Reset for next use
                self.hold_start_time = None
                self.progress = 0.0
                return True, 1.0
            return False, self.progress
        else:
            # Either hand opened — reset
            self.hold_start_time = None
            self.progress = 0.0
            return False, 0.0

    def reset(self):
        """Clears hold state (call when leaving the LEVEL_COMPLETE screen)."""
        self.hold_start_time = None
        self.progress = 0.0
