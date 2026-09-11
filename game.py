"""
game.py — Central state machine and game orchestration engine.
Coordinates camera feed, MediaPipe hand tracking, gesture detectors,
mosquito spawning/physics, scoring, visual effects, and sound playback.
"""

import math
import random
import time
import cv2
import pygame
import numpy as np

import config
from camera import CameraManager
from hand_tracker import HandTracker
from gesture_detector import SlapDetector, SpiderWebDetector, FingerGunDetector, BothFistsDetector
from mosquito import Mosquito
from sound import SoundManager
from effects import EffectsManager
from statistics import CombatStats, LeaderboardManager
from ui import UIEngine, Button

class GameState:
    MENU = "MENU"
    CALIBRATION = "CALIBRATION"
    COUNTDOWN = "COUNTDOWN"
    HOW_TO_PLAY = "HOW_TO_PLAY"
    LEVEL_INTRO = "LEVEL_INTRO"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    LEVEL_COMPLETE = "LEVEL_COMPLETE"
    GAME_OVER = "GAME_OVER"
    LEADERBOARD = "LEADERBOARD"

class MosquitoSlapperGame:
    def __init__(self, screen):
        self.screen = screen
        self.state = GameState.MENU
        self.current_level = 1
        self.level_time_left = 35.0

        # Subsystems
        self.camera = CameraManager()
        self.tracker = HandTracker()
        self.sound = SoundManager()
        self.effects = EffectsManager()
        self.stats = CombatStats()
        self.leaderboard = LeaderboardManager()
        self.ui = UIEngine(screen)

        # Gesture Detectors
        self.slap_detector = SlapDetector()
        self.web_detector = SpiderWebDetector()
        self.gun_detector = FingerGunDetector()
        self.both_fists_detector = BothFistsDetector()  # Level complete gesture
        self.fist_hold_progress = 0.0  # Passed to UI progress bar

        # Entity lists
        self.mosquitoes = []
        self.spawn_timer = 0.0

        # UI & Feedback
        self.last_miss_message_time = 0.0
        self.intro_timer = 0.0
        self.gesture_status = "SCANNING"
        self.gesture_confidence = 0.0

        # Countdown auto-start state
        self.countdown_timer = 0.0
        self.countdown_active = False

        # Input state
        self.hands = []
        self.latest_frame = None
        self.cam_surface_fullscreen = None

        # Level transition quote cache
        self.transition_quote = ""

        self._init_buttons()

    def _init_buttons(self):
        cx = config.SCREEN_WIDTH // 2
        f_h2 = self.ui.font_h2

        # Menu Buttons
        btn_w, btn_h = 280, 52
        start_y = 310
        gap = 64
        self.btn_start = Button((cx - btn_w // 2, start_y, btn_w, btn_h), "START GAME", f_h2)
        self.btn_how_to = Button((cx - btn_w // 2, start_y + gap, btn_w, btn_h), "HOW TO PLAY", f_h2)
        self.btn_stats = Button((cx - btn_w // 2, start_y + gap * 2, btn_w, btn_h), "LEADERBOARD", f_h2)
        self.btn_exit = Button((cx - btn_w // 2, start_y + gap * 3, btn_w, btn_h), "EXIT", f_h2)

        # Calibration Buttons
        self.btn_calib_proceed = Button((cx - 150, 610, 300, 50), "PROCEED TO GAME", f_h2)
        self.btn_calib_skip = Button((config.SCREEN_WIDTH - 160, 30, 130, 42), "SKIP >", self.ui.font_body)

        # How To Play Button
        self.btn_how_to_back = Button((cx - 140, 590, 280, 50), "BACK TO MENU", f_h2)

        # Level Complete Button
        self.btn_next_level = Button((cx - 140, 440, 280, 52), "CONTINUE >", f_h2)

        # Game Over Buttons
        gov_w, gov_h = 240, 50
        self.btn_play_again = Button((cx - 380, 590, gov_w, gov_h), "PLAY AGAIN", f_h2)
        self.btn_gov_leaderboard = Button((cx - 120, 590, gov_w, gov_h), "LEADERBOARD", f_h2)
        self.btn_gov_menu = Button((cx + 140, 590, gov_w, gov_h), "MAIN MENU", f_h2)

        # Leaderboard back button
        self.btn_lead_back = Button((cx - 140, 590, 280, 50), "BACK TO MENU", f_h2)

        # Pause Menu Buttons
        p_btn_w, p_btn_h = 300, 52
        p_start_y = config.SCREEN_HEIGHT // 2 - 30
        p_gap = 64
        self.btn_pause_resume = Button((cx - p_btn_w // 2, p_start_y, p_btn_w, p_btn_h), "RESUME", f_h2)
        self.btn_pause_menu = Button((cx - p_btn_w // 2, p_start_y + p_gap, p_btn_w, p_btn_h), "QUIT TO MENU", f_h2)
        self.btn_pause_sound = Button((cx - p_btn_w // 2, p_start_y + p_gap * 2, p_btn_w, p_btn_h), "SOUND: ON  ●", f_h2)

    def start_game(self):
        """Resets combat stats and starts calibration."""
        self.stats.reset()
        self.current_level = 1
        self.countdown_timer = 0.0
        self.countdown_active = False
        self.state = GameState.CALIBRATION

    def start_level(self, level_num):
        """Initializes entities and timer for given level."""
        self.current_level = level_num
        lvl_cfg = config.LEVELS[level_num]
        self.level_time_left = lvl_cfg["duration"]
        self.mosquitoes.clear()
        self.spawn_timer = 0.0
        self.both_fists_detector.reset()
        self.fist_hold_progress = 0.0

        # Pre-spawn initial batch
        initial_count = lvl_cfg["min_mosquitoes"]
        for _ in range(initial_count):
            self._spawn_mosquito()

        self.state = GameState.PLAYING
        self.sound.play_fanfare()

    def _spawn_mosquito(self):
        """Spawns a mosquito safely away from player's hands."""
        margin = 80
        # Try finding a spawn point away from tracked hands
        for _ in range(5):
            x = random.randint(margin, config.SCREEN_WIDTH - margin)
            y = random.randint(margin + 60, config.SCREEN_HEIGHT - margin)

            # Avoid spawning right under palm centers
            too_close = False
            for hand in self.hands:
                if math.hypot(x - hand.palm_center_screen[0], y - hand.palm_center_screen[1]) < 140:
                    too_close = True
                    break
            if not too_close:
                break

        m = Mosquito(x, y, self.current_level)
        self.mosquitoes.append(m)
        self.stats.record_encounter()

    def handle_event(self, event):
        """Handles mouse clicks, key bindings, and debug toggles."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                config.DEBUG_MODE = not config.DEBUG_MODE
                print("[Game] DEBUG_MODE:", config.DEBUG_MODE)
            elif event.key == pygame.K_m:
                config.DEMO_MODE = not config.DEMO_MODE
                self.ui._init_fonts()
                print("[Game] DEMO_MODE:", config.DEMO_MODE)
            elif event.key == pygame.K_ESCAPE:
                if self.state == GameState.PLAYING:
                    # ESC during gameplay opens pause menu
                    self.state = GameState.PAUSED
                elif self.state == GameState.PAUSED:
                    # ESC from pause resumes the game
                    self.state = GameState.PLAYING
                elif self.state in (GameState.HOW_TO_PLAY, GameState.LEADERBOARD,
                                    GameState.CALIBRATION, GameState.COUNTDOWN):
                    self.state = GameState.MENU

        # Mouse / Space fallback trigger during gameplay (accessibility & testing)
        if self.state == GameState.PLAYING:
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                mouse_x, mouse_y = pygame.mouse.get_pos()
                self._execute_manual_fallback_action(mouse_x, mouse_y)

    def _execute_manual_fallback_action(self, mx, my):
        """Allows testing gesture actions using mouse/space if webcam is unavailable."""
        if self.current_level == 1:
            # Simulate double-hand slap at mouse location
            self._process_slap_collision(np.array([mx, my], dtype=np.float32), 0.95)
        elif self.current_level == 2:
            # Simulate Spider-Man web projectile towards mouse
            cx, cy = config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT - 60
            dx, dy = mx - cx, my - cy
            dist = max(math.hypot(dx, dy), 1e-5)
            self._fire_web(cx, cy, dx / dist, dy / dist, 0.95)
        elif self.current_level == 3:
            # Simulate tactical double laser gun at mouse location
            self._execute_tactical_laser(
                np.array([mx - 150, config.SCREEN_HEIGHT - 80]),
                np.array([mx + 150, config.SCREEN_HEIGHT - 80]),
                np.array([mx, my], dtype=np.float32)
            )

    def update(self, dt):
        """Main game frame update."""
        # 1. Update Camera & Hand Tracker
        ret, frame_bgr = self.camera.get_frame()
        if ret and frame_bgr is not None:
            self.latest_frame = frame_bgr
            self.hands = self.tracker.process_frame(frame_bgr)
            # Create fullscreen camera surface for augmented reality gameplay
            # In calibration or debug mode, draw skeleton bones on the frame
            if self.state == GameState.CALIBRATION or config.DEBUG_MODE:
                draw_frame = self.tracker.draw_landmarks_on_image(frame_bgr.copy(), self.hands)
                frame_rgb = cv2.cvtColor(draw_frame, cv2.COLOR_BGR2RGB)
            else:
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

            # Fast surface creation matching screen dimensions
            self.cam_surface_fullscreen = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))

        # 2. Update based on current state
        if self.state == GameState.PLAYING:
            self._update_playing(dt)

        elif self.state == GameState.COUNTDOWN:
            self._update_countdown(dt)

        elif self.state == GameState.CALIBRATION:
            # When both hands are detected, kick off the countdown
            if len(self.hands) >= 2 and not self.countdown_active:
                self.countdown_active = True
                self.countdown_timer = 3.0
                self.state = GameState.COUNTDOWN

        elif self.state == GameState.LEVEL_INTRO:
            self.intro_timer -= dt
            if self.intro_timer <= 0:
                self.start_level(self.current_level)

        # 3. Update Visual Effects & Audio
        self.effects.update(dt)
        alive_mosquitoes = sum(1 for m in self.mosquitoes if m.is_alive)
        # Suppress buzz while paused or not playing
        self.sound.update_buzz(alive_mosquitoes if self.state == GameState.PLAYING else 0)

    def _update_countdown(self, dt):
        """Ticks the 3-second auto-start countdown; transitions to Level 1 on completion."""
        # If hands drop below 2 during countdown, cancel back to calibration
        if len(self.hands) < 2:
            self.countdown_active = False
            self.countdown_timer = 0.0
            self.state = GameState.CALIBRATION
            return
        self.countdown_timer -= dt
        if self.countdown_timer <= 0:
            self.countdown_active = False
            self.start_level(1)

    def _update_playing(self, dt):
        lvl_cfg = config.LEVELS[self.current_level]
        self.level_time_left -= dt

        # Spawn mosquitoes gradually
        self.spawn_timer += dt
        alive_count = sum(1 for m in self.mosquitoes if m.is_alive)
        if self.spawn_timer >= lvl_cfg["spawn_interval"] and alive_count < lvl_cfg["max_mosquitoes"]:
            self.spawn_timer = 0.0
            self._spawn_mosquito()

        # Update mosquitoes
        for m in self.mosquitoes:
            m.update(dt)
        self.mosquitoes = [m for m in self.mosquitoes if not m.is_finished()]

        # Update Projectiles collision
        self._update_projectiles_collision()

        # Execute gesture detection according to current level
        if self.current_level == 1:
            self._update_level1_slap()
        elif self.current_level == 2:
            self._update_level2_web()
        elif self.current_level == 3:
            self._update_level3_gun(dt)

        # Check level completion
        if self.level_time_left <= 0:
            self._on_level_complete()

    def _update_level1_slap(self):
        """Level 1: Double-hand slap detection."""
        slap_event, slap_pos, conf = self.slap_detector.update(self.hands)
        self.gesture_confidence = conf

        if self.slap_detector.state == SlapDetector.STATE_APPROACH:
            self.gesture_status = "SLAP PRIMED"
        elif self.slap_detector.state == SlapDetector.STATE_COOLDOWN:
            self.gesture_status = "SLAP COOLDOWN"
        else:
            self.gesture_status = "SLAP READY" if len(self.hands) >= 2 else "AWAITING HANDS"

        if slap_event and slap_pos is not None:
            self._process_slap_collision(slap_pos, conf)

    def _process_slap_collision(self, slap_pos, confidence):
        """Checks mosquitoes within slap radius of palm midpoint."""
        self.stats.record_action("SLAP")
        slap_x, slap_y = slap_pos[0], slap_pos[1]
        slap_radius = config.SLAP_RADIUS * config.LEVELS[self.current_level]["slap_radius_multiplier"]

        # Trigger visual cartoon shockwave ring at slap point
        self.effects.add_shockwave(slap_x, slap_y, max_radius=slap_radius * 1.15)

        killed_any = False
        for m in self.mosquitoes:
            if not m.is_alive:
                continue
            dist = math.hypot(m.x - slap_x, m.y - slap_y)
            if dist <= (slap_radius + m.radius):
                # MOSQUITO KILLED!
                m.kill("SLAP")
                killed_any = True
                self.stats.record_kill("SLAP", m.time_alive)
                self.effects.add_splat(m.x, m.y)
                self.effects.add_floating_text(f"+{config.SCORE_PER_KILL * min(self.stats.current_combo, config.MAX_COMBO_MULTIPLIER)}", m.x, m.y, (50, 255, 130))

        if killed_any:
            self.sound.play_slap()
            self.sound.play_splat()
            self.sound.play_combo(self.stats.current_combo)
            self.effects.add_floating_text("WHAM!", slap_x, slap_y - 30, (255, 235, 40), font_size=32)
            self.effects.trigger_shake(intensity=12, duration=0.22)
            self._trigger_combo_commentary(slap_x, slap_y)
        else:
            # Missed slap!
            self.stats.record_miss("SLAP")
            self.sound.play_miss()
            self.effects.trigger_shake(intensity=5, duration=0.12)
            self._trigger_miss_commentary(slap_x, slap_y)

    def _update_level2_web(self):
        """Level 2: Spider-Man web shooter detection."""
        web_event, origin, direction, conf = self.web_detector.update(self.hands)
        self.gesture_confidence = conf
        self.gesture_status = "WEB READY" if conf >= 0.75 else "WEB CHARGING"

        if web_event and origin is not None and direction is not None:
            self._fire_web(origin[0], origin[1], direction[0], direction[1], conf)

    def _fire_web(self, ox, oy, dx, dy, conf):
        """Creates an animated web projectile."""
        self.stats.record_action("WEB")
        self.effects.add_web(ox, oy, dx, dy)
        self.sound.play_web()
        self.effects.add_floating_text("THWIP!", ox, oy - 20, (0, 220, 255), font_size=24)

    def _update_projectiles_collision(self):
        """Checks collisions between active web projectiles and mosquitoes."""
        for proj in self.effects.projectiles:
            if proj.is_exploding or proj.is_dead():
                continue
            for m in self.mosquitoes:
                if not m.is_alive:
                    continue
                dist = math.hypot(m.x - proj.pos[0], m.y - proj.pos[1])
                if dist <= (proj.radius + m.radius):
                    # Web hit!
                    proj.explode()
                    m.kill("WEB")
                    self.stats.record_kill("WEB", m.time_alive)
                    self.effects.add_splat(m.x, m.y)
                    self.sound.play_splat()
                    self.sound.play_combo(self.stats.current_combo)
                    self.effects.add_floating_text("SPLAT!", m.x, m.y, (0, 255, 200))
                    self._trigger_combo_commentary(m.x, m.y)
                    break

    def _update_level3_gun(self, dt):
        """Level 3: Dual tactical finger gun execution detection."""
        fire_event, orig_l, orig_r, target_pos, is_locked, lock_prog, conf = (
            self.gun_detector.update(self.hands, self.mosquitoes)
        )
        self.gesture_confidence = conf

        if is_locked:
            self.gesture_status = "TARGET LOCKED!"
        elif lock_prog > 0.1:
            self.gesture_status = f"LOCKING ON [{int(lock_prog*100)}%]"
        else:
            self.gesture_status = "AIMING CONE ACTIVE" if len(self.hands) >= 2 else "AWAITING 2 HANDS"

        if fire_event and orig_l is not None and orig_r is not None and target_pos is not None:
            self._execute_tactical_laser(orig_l, orig_r, target_pos)

    def _execute_tactical_laser(self, orig_l, orig_r, target_pos):
        """Executes orbital twin laser execution volley."""
        self.stats.record_action("GUN")
        self.effects.add_laser(orig_l, orig_r, target_pos)
        self.sound.play_laser()

        tx, ty = target_pos[0], target_pos[1]
        self.effects.add_floating_text("PEW PEW!", tx, ty - 30, (255, 60, 80), font_size=32)

        # Destroy mosquitoes near laser target
        hit_any = False
        for m in self.mosquitoes:
            if not m.is_alive:
                continue
            dist = math.hypot(m.x - tx, m.y - ty)
            if dist <= (65 + m.radius):
                m.kill("GUN")
                hit_any = True
                self.stats.record_kill("GUN", m.time_alive)
                self.effects.add_splat(m.x, m.y, count=30)
                self.effects.add_floating_text("OBLITERATED!", m.x, m.y, (255, 230, 0))

        if hit_any:
            self.sound.play_splat()
            self.sound.play_combo(self.stats.current_combo)
            self._trigger_combo_commentary(tx, ty)
        else:
            self.stats.record_miss("GUN")
            self._trigger_miss_commentary(tx, ty)

    def _trigger_combo_commentary(self, x, y):
        """Displays humorous escalating combo messages."""
        streak = self.stats.current_combo
        if streak in config.COMBO_MESSAGES:
            msg = config.COMBO_MESSAGES[streak]
            color = (50, 255, 130) if streak < 5 else ((255, 215, 0) if streak < 10 else (255, 60, 80))
            self.effects.add_floating_text(msg, x, y - 50, color, font_size=28, vy=-60)

    def _trigger_miss_commentary(self, x, y):
        """Displays humorous roast on missed slaps with cooldown."""
        now = time.time()
        if now - self.last_miss_message_time > config.MISS_MESSAGE_COOLDOWN:
            self.last_miss_message_time = now
            msg = random.choice(config.MISS_MESSAGES)
            self.effects.add_floating_text(msg, x, y - 40, (220, 160, 160), font_size=22, vy=-50)

    def _on_level_complete(self):
        """Transitions between levels or concludes with Game Over."""
        self.sound.play_fanfare()
        self.transition_quote = config.LEVEL_TRANSITION_QUOTES.get(self.current_level, "LEVEL FINISHED.")

        if self.current_level < 3:
            self.state = GameState.LEVEL_COMPLETE
        else:
            # Final game completion
            report = self.stats.compute_report()
            self.leaderboard.add_score("PLAYER", report["score"], report["killed"], report["kerala_survival"])
            self.state = GameState.GAME_OVER

    def render(self):
        """Main rendering pass applying screen shake and UI drawing."""
        # Screen shake offset
        ox, oy = self.effects.shake_offset
        mouse_pos = pygame.mouse.get_pos()
        mouse_down = pygame.mouse.get_pressed()[0]

        if self.state == GameState.MENU:
            buttons = [self.btn_start, self.btn_how_to, self.btn_stats, self.btn_exit]
            self.ui.draw_menu(buttons, mouse_pos, cam_surface=self.cam_surface_fullscreen)

            if self.btn_start.is_clicked(mouse_pos, mouse_down):
                self.start_game()
            elif self.btn_how_to.is_clicked(mouse_pos, mouse_down):
                self.state = GameState.HOW_TO_PLAY
            elif self.btn_stats.is_clicked(mouse_pos, mouse_down):
                self.state = GameState.LEADERBOARD
            elif self.btn_exit.is_clicked(mouse_pos, mouse_down):
                pygame.event.post(pygame.event.Event(pygame.QUIT))

        elif self.state == GameState.CALIBRATION:
            self.ui.draw_calibration(self.cam_surface_fullscreen, self.hands, self.btn_calib_proceed, self.btn_calib_skip, mouse_pos)
            if self.btn_calib_proceed.is_clicked(mouse_pos, mouse_down) or self.btn_calib_skip.is_clicked(mouse_pos, mouse_down):
                # Manual skip/proceed resets countdown and jumps straight in
                self.countdown_active = False
                self.start_level(1)

        elif self.state == GameState.COUNTDOWN:
            self.ui.draw_countdown(self.cam_surface_fullscreen, self.countdown_timer, self.hands)

        elif self.state == GameState.HOW_TO_PLAY:
            self.ui.draw_how_to_play(self.btn_how_to_back, mouse_pos, cam_surface=self.cam_surface_fullscreen)
            if self.btn_how_to_back.is_clicked(mouse_pos, mouse_down):
                self.state = GameState.MENU

        elif self.state == GameState.PLAYING:
            # 1. Background: Live Mirrored Webcam Video!
            self.ui.draw_camera_background(self.cam_surface_fullscreen, dim_alpha=0)

            # 2. Hand AR Reticles & Proximity slap guides directly on camera feed
            self.ui.draw_hand_reticles(self.hands, self.current_level, self.slap_detector.state, self.slap_detector.last_velocity)

            # 3. Render Mosquitoes directly inside the camera feed!
            for m in self.mosquitoes:
                m.draw(self.screen)

            # 4. Render Visual Effects (Shockwaves, Splatters, Webs, Lasers, Floating text)
            self.effects.draw(self.screen, self.ui.font_h2)

            # 5. In-Game HUD (Radar, Score, Timer, AI Telemetry)
            report = self.stats.compute_report()
            lvl_cfg = config.LEVELS[self.current_level]
            self.ui.draw_hud(
                score=self.stats.score,
                combo=self.stats.current_combo,
                killed=self.stats.killed,
                accuracy=report["accuracy"],
                time_left=self.level_time_left,
                level=self.current_level,
                level_cfg=lvl_cfg,
                mosquitoes=self.mosquitoes,
                cam_surface=self.cam_surface_fullscreen,
                hands=self.hands,
                gesture_status=self.gesture_status,
                gesture_confidence=self.gesture_confidence,
                dt=1.0 / config.TARGET_FPS
            )

            # 6. Debug Overlay (if DEBUG_MODE active)
            if config.DEBUG_MODE:
                self._draw_debug_overlay()

        elif self.state == GameState.PAUSED:
            pause_buttons = [self.btn_pause_resume, self.btn_pause_menu, self.btn_pause_sound]
            self.ui.draw_pause_menu(pause_buttons, mouse_pos, self.sound.is_sound_on(), cam_surface=self.cam_surface_fullscreen)

            if self.btn_pause_resume.is_clicked(mouse_pos, mouse_down):
                self.state = GameState.PLAYING
            elif self.btn_pause_menu.is_clicked(mouse_pos, mouse_down):
                self.state = GameState.MENU
            elif self.btn_pause_sound.is_clicked(mouse_pos, mouse_down):
                self.sound.toggle_sound()

        elif self.state == GameState.LEVEL_COMPLETE:
            # Both-fists gesture to continue (✊✊ hold for 0.6 s)
            fist_fired, fist_progress = self.both_fists_detector.update(self.hands)
            self.fist_hold_progress = fist_progress

            self.ui.draw_level_complete(
                self.current_level, self.transition_quote,
                self.btn_next_level, mouse_pos,
                cam_surface=self.cam_surface_fullscreen,
                fist_progress=fist_progress
            )

            # Advance level via gesture OR button click
            advance = fist_fired or self.btn_next_level.is_clicked(mouse_pos, mouse_down)
            if advance:
                self.start_level(self.current_level + 1)

        elif self.state == GameState.GAME_OVER:
            report = self.stats.compute_report()
            buttons = [self.btn_play_again, self.btn_gov_leaderboard, self.btn_gov_menu]
            self.ui.draw_combat_report(report, buttons, mouse_pos, cam_surface=self.cam_surface_fullscreen)

            if self.btn_play_again.is_clicked(mouse_pos, mouse_down):
                self.start_game()
            elif self.btn_gov_leaderboard.is_clicked(mouse_pos, mouse_down):
                self.state = GameState.LEADERBOARD
            elif self.btn_gov_menu.is_clicked(mouse_pos, mouse_down):
                self.state = GameState.MENU

        elif self.state == GameState.LEADERBOARD:
            scores = self.leaderboard.get_top_scores()
            self.ui.draw_leaderboard(scores, self.btn_lead_back, mouse_pos, cam_surface=self.cam_surface_fullscreen)
            if self.btn_lead_back.is_clicked(mouse_pos, mouse_down):
                self.state = GameState.MENU

    def _draw_debug_overlay(self):
        """Draws developer debug indicators, palm coordinates, hitboxes, and velocities."""
        debug_surf = pygame.Surface((320, 180), pygame.SRCALPHA)
        debug_surf.fill((10, 10, 15, 200))
        self.screen.blit(debug_surf, (20, 80))

        lines = [
            f"FPS: {int(pygame.time.Clock().get_fps())}",
            f"Hands Tracked: {len(self.hands)}",
            f"Current Level: {self.current_level}",
            f"Active Mosquitoes: {len(self.mosquitoes)}",
            f"Slap Velocity: {self.slap_detector.last_velocity:.2f}",
            f"Slap State: {self.slap_detector.state}",
            f"Gesture Status: {self.gesture_status}",
            f"Gesture Match: {int(self.gesture_confidence*100)}%"
        ]
        y = 86
        for line in lines:
            t = self.ui.font_mono.render(line, True, (0, 255, 255))
            self.screen.blit(t, (28, y))
            y += 20

        # Draw palm positions & collision circles on main canvas
        for hand in self.hands:
            px, py = int(hand.palm_center_screen[0]), int(hand.palm_center_screen[1])
            pygame.draw.circle(self.screen, (255, 0, 0), (px, py), 8)
            pygame.draw.circle(self.screen, (0, 255, 0), (px, py), config.SLAP_RADIUS, 1)

    def cleanup(self):
        """Releases camera and audio resources."""
        self.camera.stop()
        self.sound.stop_all()
