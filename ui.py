"""
ui.py — Polished Pygame graphical interface engine.
Includes:
- Title Menu with interactive glassmorphism buttons
- Sensor Calibration Screen with live hand telemetry
- How To Play screen with live landmark preview
- Tactical Military Mosquito Threat Radar (with sweeping beam and blips)
- Camera PIP HUD with AI telemetry status
- Dynamic combo and miss commentary banners
- Dramatic level transition banners
- Humorous Mosquito Combat Report dossier (Kerala Survival Rating badge)
- Local Leaderboard screen
"""

import math
import time
# pyrefly: ignore [missing-import]
import pygame
import config

# Color Palette
COLOR_BG_DARK = (15, 18, 24)
COLOR_PANEL_BG = (24, 30, 42, 220)
COLOR_PANEL_BORDER = (45, 60, 85)
COLOR_CYAN = (0, 220, 255)
COLOR_NEON_GREEN = (50, 255, 130)
COLOR_YELLOW = (255, 215, 0)
COLOR_RED = (255, 60, 70)
COLOR_WHITE = (245, 248, 255)
COLOR_GRAY = (140, 155, 175)
COLOR_DARK_GRAY = (40, 48, 60)
COLOR_DARK_GREEN = (170, 255, 0)

class Button:
    """Glassmorphism UI button with hover animations."""
    def __init__(self, rect, text, font, base_color=(30, 40, 58), hover_color=(45, 68, 100), text_color=COLOR_WHITE):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, mouse_down):
        return self.is_hovered and mouse_down

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.base_color
        border_color = COLOR_CYAN if self.is_hovered else COLOR_PANEL_BORDER

        # Draw rounded button body
        btn_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(btn_surf, (*color[:3], 230), (0, 0, self.rect.width, self.rect.height), border_radius=8)
        pygame.draw.rect(btn_surf, border_color, (0, 0, self.rect.width, self.rect.height), width=2, border_radius=8)
        surface.blit(btn_surf, self.rect.topleft)

        # Text label
        txt = self.font.render(self.text, True, COLOR_CYAN if self.is_hovered else self.text_color)
        t_rect = txt.get_rect(center=self.rect.center)
        surface.blit(txt, t_rect)

class UIEngine:
    """Central UI drawing system for menus, radar, HUD, and reports."""
    def __init__(self, screen):
        self.screen = screen
        self.width = config.SCREEN_WIDTH
        self.height = config.SCREEN_HEIGHT
        self.radar_angle = 0.0

        self._init_fonts()
        self._init_background()

    def _init_fonts(self):
        # Scale fonts if DEMO_MODE is active
        scale = 1.3 if config.DEMO_MODE else 1.0

        self.font_title = pygame.font.SysFont("impact", int(54 * scale))
        self.font_h1 = pygame.font.SysFont("arial", int(32 * scale), bold=True)
        self.font_h2 = pygame.font.SysFont("arial", int(24 * scale), bold=True)
        self.font_body = pygame.font.SysFont("arial", int(18 * scale))
        self.font_small = pygame.font.SysFont("arial", int(14 * scale))
        self.font_mono = pygame.font.SysFont("consolas", int(16 * scale), bold=True)

    def _init_background(self):
        """Creates a stylized dark indoor living room / patio background."""
        self.bg_surface = pygame.Surface((self.width, self.height))
        # Gradient background
        for y in range(self.height):
            ratio = y / self.height
            r = int(14 * (1.0 - ratio) + 22 * ratio)
            g = int(18 * (1.0 - ratio) + 26 * ratio)
            b = int(26 * (1.0 - ratio) + 38 * ratio)
            pygame.draw.line(self.bg_surface, (r, g, b), (0, y), (self.width, y))

        # Soft wall moulding / floor lines
        floor_y = self.height - 120
        pygame.draw.line(self.bg_surface, (35, 45, 65), (0, floor_y), (self.width, floor_y), 3)

        # Subtle vertical wall slats
        for x in range(0, self.width, 90):
            pygame.draw.line(self.bg_surface, (20, 26, 38), (x, 0), (x, floor_y), 1)

        # Floor perspective lines
        for x in range(-200, self.width + 200, 140):
            pygame.draw.line(self.bg_surface, (28, 36, 52), (x, floor_y), (x + 100, self.height), 2)

    def draw_background(self):
        self.screen.blit(self.bg_surface, (0, 0))

    def draw_camera_background(self, cam_surface, dim_alpha=0):
        """Draws the live webcam feed as the game background with optional darkening tint."""
        if cam_surface is not None:
            # Scale to fullscreen if needed
            if cam_surface.get_size() != (self.width, self.height):
                cam_surface = pygame.transform.scale(cam_surface, (self.width, self.height))
            self.screen.blit(cam_surface, (0, 0))

            # Apply dim overlay if specified (for menus/transitions)
            if dim_alpha > 0:
                dim_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                dim_surf.fill((10, 14, 22, dim_alpha))
                self.screen.blit(dim_surf, (0, 0))
        else:
            self.draw_background()

    # ==========================================================================
    # TITLE MENU
    # ==========================================================================
    def draw_menu(self, buttons, mouse_pos, cam_surface=None):
        self.draw_camera_background(cam_surface, dim_alpha=140)

        # Title card banner
        cx = self.width // 2
        title_txt = self.font_title.render("KOTHU BAT", True, COLOR_CYAN)
        t_rect = title_txt.get_rect(center=(cx, 160))

        # Glow shadow
        glow_txt = self.font_title.render("KOTHU BAT", True, (0, 100, 140))
        self.screen.blit(glow_txt, (t_rect.x + 3, t_rect.y + 3))
        self.screen.blit(title_txt, t_rect)

        # Subtitle
        sub_text = "by BAMBOO BOIS"
        sub_txt = self.font_h2.render(sub_text, True, COLOR_DARK_GREEN)
        self.screen.blit(sub_txt, sub_txt.get_rect(center=(cx, 220)))

        # Badges
        badge_text = ""
        b_surf = self.font_small.render(badge_text, True, COLOR_GRAY)
        self.screen.blit(b_surf, b_surf.get_rect(center=(cx, 260)))

        # Draw menu buttons
        for btn in buttons:
            btn.update(mouse_pos)
            btn.draw(self.screen)

    # ==========================================================================
    # HOW TO PLAY SCREEN
    # ==========================================================================
    def draw_how_to_play(self, back_button, mouse_pos, cam_surface=None):
        self.draw_camera_background(cam_surface, dim_alpha=160)

        cx = self.width // 2
        title = self.font_h1.render("HOW TO PLAY — 3 TACTICAL GESTURES", True, COLOR_CYAN)
        self.screen.blit(title, title.get_rect(center=(cx, 70)))

        # 3 Gesture Cards
        card_w, card_h = 340, 380
        cards_x = [120, 480, 840]
        y = 130

        gestures = [
            ("LEVEL 1: HANDS ON",
             "[ DOUBLE-HAND SLAP ]",
             "Bring BOTH hands together rapidly.",
             "Simulates a real mosquito slap.",
             "Midpoint velocity crushes all mosquitoes inside the slap radius.",
             COLOR_NEON_GREEN),
            ("LEVEL 2: SPIDER MODE",
             "[ SPIDER WEB SHOOTER ]",
             "Fold middle & ring fingers inward.",
             "Extend thumb, index & pinky",
             "Shoots high-velocity virtual silk web. Hits trigger 'THWIP!'.",
             COLOR_YELLOW),
            ("LEVEL 3: NO MERCY",
             "[ DUAL FINGER GUNS ]",
             "Extend both index fingers forward.",
             "Thumbs RAISED = armed. Click EITHER thumb DOWN = fire!",
             "Instantly fires dual orbital execution lasers at the locked target!",
             COLOR_RED)
        ]

        for i, (lvl, name, line1, line2, line3, accent) in enumerate(gestures):
            bx = cards_x[i]
            panel = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            pygame.draw.rect(panel, COLOR_PANEL_BG, (0, 0, card_w, card_h), border_radius=12)
            pygame.draw.rect(panel, accent, (0, 0, card_w, card_h), width=2, border_radius=12)
            self.screen.blit(panel, (bx, y))

            # Header
            t1 = self.font_h2.render(lvl, True, accent)
            self.screen.blit(t1, (bx + 20, y + 20))
            t2 = self.font_body.render(name, True, COLOR_WHITE)
            self.screen.blit(t2, (bx + 20, y + 55))

            # Body bullet points
            lines = [line1, line2, line3]
            curr_y = y + 110
            for l in lines:
                txt = self.font_body.render(f"- {l}", True, COLOR_GRAY)
                self.screen.blit(txt, (bx + 20, curr_y))
                curr_y += 36

        back_button.update(mouse_pos)
        back_button.draw(self.screen)

    # ==========================================================================
    # CALIBRATION SCREEN
    # ==========================================================================
    def draw_calibration(self, cam_surface, hands, start_button, skip_button, mouse_pos):
        self.draw_camera_background(cam_surface, dim_alpha=40)

        cx = self.width // 2
        title = self.font_h1.render("Searching for hands...", True, COLOR_DARK_GRAY)
        self.screen.blit(title, title.get_rect(center=(cx, 50)))

        sub = self.font_body.render("Make both fists to continue", True, COLOR_WHITE)
        self.screen.blit(sub, sub.get_rect(center=(cx, 90)))

        # Telemetry panel on bottom
        num_hands = len(hands)
        status_color = COLOR_NEON_GREEN if num_hands >= 2 else (COLOR_YELLOW if num_hands == 1 else COLOR_RED)
        status_str = f"OPTICAL TRACKING: {num_hands} / 2 HANDS DETECTED"
        status_txt = self.font_h1.render(status_str, True, status_color)
        self.screen.blit(status_txt, status_txt.get_rect(center=(cx, self.height - 130)))

        start_button.update(mouse_pos)
        start_button.draw(self.screen)
        skip_button.update(mouse_pos)
        skip_button.draw(self.screen)

    # ==========================================================================
    # IN-GAME HUD & MILITARY MOSQUITO THREAT RADAR
    # ==========================================================================
    def draw_hud(self, score, combo, killed, accuracy, time_left, level, level_cfg,
                 mosquitoes, cam_surface, hands, gesture_status, gesture_confidence, dt):
        # 1. Top Status Banner
        hud_bar = pygame.Surface((self.width, 70), pygame.SRCALPHA)
        pygame.draw.rect(hud_bar, (10, 14, 22, 210), (0, 0, self.width, 70))
        pygame.draw.line(hud_bar, COLOR_PANEL_BORDER, (0, 69), (self.width, 69), 2)
        self.screen.blit(hud_bar, (0, 0))

        # Level name
        lvl_title = self.font_h2.render(level_cfg["name"], True, COLOR_CYAN)
        self.screen.blit(lvl_title, (24, 12))
        lvl_sub = self.font_small.render(level_cfg["gesture_name"] + " | " + level_cfg["gesture_desc"], True, COLOR_GRAY)
        self.screen.blit(lvl_sub, (24, 42))

        # Score & Combo
        score_txt = self.font_h1.render(f"SCORE: {score:,}", True, COLOR_WHITE)
        self.screen.blit(score_txt, (520, 18))

        if combo > 1:
            combo_color = COLOR_NEON_GREEN if combo < 5 else (COLOR_YELLOW if combo < 10 else COLOR_RED)
            combo_txt = self.font_h2.render(f"COMBO x{combo}!", True, combo_color)
            self.screen.blit(combo_txt, (720, 22))

        # Kills & Accuracy
        kills_txt = self.font_body.render(f"KILLS: {killed}", True, COLOR_WHITE)
        self.screen.blit(kills_txt, (880, 16))
        acc_txt = self.font_small.render(f"ACCURACY: {accuracy}%", True, COLOR_GRAY)
        self.screen.blit(acc_txt, (880, 42))

        # Timer countdown bar
        time_sec = max(0, int(time_left))
        timer_str = f"{time_sec:02d}s"
        t_color = COLOR_WHITE if time_sec > 10 else COLOR_RED
        t_surf = self.font_h1.render(timer_str, True, t_color)
        self.screen.blit(t_surf, (1040, 18))

        # 2. Tactical Military Mosquito Threat Radar (Top Right)
        self._draw_threat_radar(mosquitoes, dt)

        # 3. AI Tracking Telemetry HUD (Bottom Left)
        self._draw_ai_telemetry_hud(hands, gesture_status, gesture_confidence)

    def _draw_threat_radar(self, mosquitoes, dt):
        """Draws dynamic military mosquito threat radar with sweeping beam and blips."""
        radar_size = 110
        rx = self.width - radar_size - 18
        ry = 80
        cx = rx + radar_size // 2
        cy = ry + radar_size // 2
        radius = radar_size // 2 - 4

        # Radar panel background
        radar_surf = pygame.Surface((radar_size, radar_size), pygame.SRCALPHA)
        pygame.draw.circle(radar_surf, (10, 25, 20, 220), (radar_size // 2, radar_size // 2), radius)
        # Green radar rings
        for r in [radius // 3, (radius * 2) // 3, radius]:
            pygame.draw.circle(radar_surf, (0, 180, 90, 120), (radar_size // 2, radar_size // 2), r, 1)
        # Crosshairs
        c = radar_size // 2
        pygame.draw.line(radar_surf, (0, 180, 90, 80), (c, 4), (c, radar_size - 4), 1)
        pygame.draw.line(radar_surf, (0, 180, 90, 80), (4, c), (radar_size - 4, c), 1)

        # Rotating radar sweep beam
        self.radar_angle = (self.radar_angle + 2.8 * dt) % (2 * math.pi)
        sweep_x = c + int(radius * math.cos(self.radar_angle))
        sweep_y = c + int(radius * math.sin(self.radar_angle))
        pygame.draw.line(radar_surf, (80, 255, 140, 220), (c, c), (sweep_x, sweep_y), 2)

        # Mosquito blips mapped to radar circular coordinates
        alive_count = 0
        for m in mosquitoes:
            if m.is_alive:
                alive_count += 1
                # Normalize mosquito position to radar disk
                norm_x = (m.x / self.width) * 2.0 - 1.0
                norm_y = (m.y / self.height) * 2.0 - 1.0
                bx = c + int(norm_x * (radius * 0.8))
                by = c + int(norm_y * (radius * 0.8))
                pygame.draw.circle(radar_surf, (255, 60, 60), (bx, by), 3)

        self.screen.blit(radar_surf, (rx, ry))
        pygame.draw.circle(self.screen, (0, 220, 120), (cx, cy), radius, 2)

        # Threat Level Badge
        if alive_count <= 4:
            t_color = COLOR_NEON_GREEN
            t_label = "THREAT: LOW"
        elif alive_count <= 9:
            t_color = COLOR_YELLOW
            t_label = "THREAT: MODERATE"
        else:
            t_color = COLOR_RED
            t_label = "THREAT: EXTREME"

        threat_surf = self.font_mono.render(t_label, True, t_color)
        t_rect = threat_surf.get_rect(center=(cx, ry + radar_size + 14))
        self.screen.blit(threat_surf, t_rect)

    def _draw_ai_telemetry_hud(self, hands, gesture_status, gesture_confidence):
        """Draws compact, high-tech AI tracking telemetry HUD in bottom-left corner."""
        w, h = 260, 68
        px = 24
        py = self.height - h - 20

        # High-tech glass panel
        telemetry_bar = pygame.Surface((w, h), pygame.SRCALPHA)
        telemetry_bar.fill((10, 16, 26, 200))
        num_hands = len(hands)
        border_color = COLOR_CYAN if num_hands > 0 else COLOR_RED
        pygame.draw.rect(telemetry_bar, border_color, (0, 0, w, h), width=2, border_radius=6)
        self.screen.blit(telemetry_bar, (px, py))

        # Title & Status text
        tag = self.font_small.render("AI OPTICAL SENSORS: ACTIVE", True, COLOR_CYAN)
        self.screen.blit(tag, (px + 12, py + 8))

        hand_status = f"HANDS: {num_hands}/2"
        h_color = COLOR_NEON_GREEN if num_hands == 2 else (COLOR_YELLOW if num_hands == 1 else COLOR_RED)
        t1 = self.font_mono.render(hand_status, True, h_color)
        self.screen.blit(t1, (px + 12, py + 26))

        conf_pct = int(gesture_confidence * 100)
        gest_text = f"{gesture_status} [{conf_pct}%]"
        t2 = self.font_mono.render(gest_text, True, COLOR_WHITE)
        self.screen.blit(t2, (px + 12, py + 46))

        # If zero hands detected: warning banner
        if num_hands == 0:
            warn_surf = pygame.Surface((440, 42), pygame.SRCALPHA)
            warn_surf.fill((180, 20, 20, 220))
            pygame.draw.rect(warn_surf, COLOR_RED, (0, 0, 440, 42), width=2, border_radius=6)
            warn_txt = self.font_h2.render("WHERE ARE YOUR HANDS? (SHOW HANDS)", True, COLOR_WHITE)
            warn_surf.blit(warn_txt, warn_txt.get_rect(center=(220, 21)))
            self.screen.blit(warn_surf, (self.width // 2 - 220, 85))

    def draw_hand_reticles(self, hands, current_level, slap_state="OPEN", last_velocity=0.0):
        """
        Draws subtle augmented-reality reticles directly over the player's hands on the camera feed.
        """
        for hand in hands:
            px, py = int(hand.palm_center_screen[0]), int(hand.palm_center_screen[1])

            # Subtle glowing circular reticle around palm center
            color = COLOR_CYAN if hand.label == "Left" else COLOR_NEON_GREEN
            pygame.draw.circle(self.screen, color, (px, py), 18, 2)
            pygame.draw.circle(self.screen, COLOR_WHITE, (px, py), 4)

            # High-tech corner tick marks around palm
            r = 24
            for angle_deg in [45, 135, 225, 315]:
                rad = math.radians(angle_deg)
                x1 = px + int(r * math.cos(rad))
                y1 = py + int(r * math.sin(rad))
                x2 = px + int((r + 6) * math.cos(rad))
                y2 = py + int((r + 6) * math.sin(rad))
                pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), 2)

        # LEVEL 1: Double-Hand Slap Proximity Meter
        if current_level == 1 and len(hands) >= 2:
            p1 = (int(hands[0].palm_center_screen[0]), int(hands[0].palm_center_screen[1]))
            p2 = (int(hands[1].palm_center_screen[0]), int(hands[1].palm_center_screen[1]))
            dist = math.hypot(p1[0] - p2[0], p1[1] - p2[1])

            # Proximity color transitions from Cyan -> Yellow -> Neon Green -> Orange
            if dist < 180:
                line_color = COLOR_RED if slap_state == "COOLDOWN" else COLOR_NEON_GREEN
                line_w = 4
            elif dist < 320:
                line_color = COLOR_YELLOW
                line_w = 3
            else:
                line_color = (0, 180, 220, 140)
                line_w = 2

            pygame.draw.line(self.screen, line_color, p1, p2, line_w)

            # Midpoint target circle (where the slap will land)
            mid = ((p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2)
            if slap_state == "APPROACH" or dist < 220:
                pygame.draw.circle(self.screen, (255, 255, 255), mid, int(config.SLAP_RADIUS), 1)
                pygame.draw.circle(self.screen, COLOR_YELLOW, mid, 8)

        # LEVEL 2: Spider Web Aiming Crosshair
        elif current_level == 2:
            for hand in hands:
                idx_tip = (int(hand.index_tip[0]), int(hand.index_tip[1]))
                wrist = (int(hand.wrist[0]), int(hand.wrist[1]))
                dx, dy = idx_tip[0] - wrist[0], idx_tip[1] - wrist[1]
                length = max(math.hypot(dx, dy), 1e-5)
                # Aiming guide line
                aim_end = (idx_tip[0] + int(dx / length * 90), idx_tip[1] + int(dy / length * 90))
                pygame.draw.line(self.screen, (0, 220, 255, 180), idx_tip, aim_end, 2)
                pygame.draw.circle(self.screen, (0, 220, 255), aim_end, 6, 2)

        # LEVEL 3: Tactical Finger Gun Crosshairs
        elif current_level == 3 and len(hands) >= 2:
            for hand in hands:
                tip = (int(hand.index_tip[0]), int(hand.index_tip[1]))
                pygame.draw.circle(self.screen, COLOR_RED, tip, 8, 2)
                pygame.draw.line(self.screen, COLOR_RED, (tip[0] - 12, tip[1]), (tip[0] + 12, tip[1]), 2)
                pygame.draw.line(self.screen, COLOR_RED, (tip[0], tip[1] - 12), (tip[0], tip[1] + 12), 2)

    # ==========================================================================
    # LEVEL COMPLETE & TRANSITION SCREEN
    # ==========================================================================
    def draw_level_complete(self, finished_level, quote, next_button, mouse_pos, cam_surface=None, fist_progress=0.0):
        self.draw_camera_background(cam_surface, dim_alpha=150)

        cx = self.width // 2
        cy = self.height // 2

        # Glow panel
        panel_w, panel_h = 760, 400
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, COLOR_PANEL_BG, (0, 0, panel_w, panel_h), border_radius=16)
        pygame.draw.rect(panel, COLOR_CYAN, (0, 0, panel_w, panel_h), width=3, border_radius=16)
        self.screen.blit(panel, (cx - panel_w // 2, cy - panel_h // 2))

        # Big Title
        t1 = self.font_title.render(f"LEVEL {finished_level} COMPLETE!", True, COLOR_NEON_GREEN)
        self.screen.blit(t1, t1.get_rect(center=(cx, cy - 130)))

        # Humorous quote
        q_surf = self.font_h2.render(f'"{quote}"', True, COLOR_YELLOW)
        self.screen.blit(q_surf, q_surf.get_rect(center=(cx, cy - 65)))

        if finished_level < 3:
            next_name = config.LEVELS[finished_level + 1]["name"]
            n_surf = self.font_body.render("", True, COLOR_WHITE)
            self.screen.blit(n_surf, n_surf.get_rect(center=(cx, cy - 15)))

        # ── Both-Fists Gesture Hint ──────────────────────────────────────────
        bar_w, bar_h = 360, 22
        bar_x = cx - bar_w // 2
        bar_y = cy + 30

        if fist_progress > 0.0:
            # Active: glowing progress bar
            hint_surf = self.font_h2.render("", True, COLOR_CYAN)
            self.screen.blit(hint_surf, hint_surf.get_rect(center=(cx, bar_y - 28)))

            # Background track
            pygame.draw.rect(self.screen, (30, 45, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
            # Filled portion
            fill_w = int(bar_w * fist_progress)
            if fill_w > 0:
                pygame.draw.rect(self.screen, COLOR_CYAN, (bar_x, bar_y, fill_w, bar_h), border_radius=6)
            # Border
            pygame.draw.rect(self.screen, COLOR_CYAN, (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=6)
            # Percentage label
            pct_txt = self.font_small.render(f"{int(fist_progress * 100)}%", True, COLOR_WHITE)
            self.screen.blit(pct_txt, pct_txt.get_rect(center=(cx, bar_y + bar_h // 2)))
        else:
            # Idle: static prompt so the player knows the gesture exists
            hint_surf = self.font_body.render("HOLD FISTS TO CONTINUE!", True, COLOR_CYAN)
            self.screen.blit(hint_surf, hint_surf.get_rect(center=(cx, bar_y)))
        # ─────────────────────────────────────────────────────────────────────

        next_button.update(mouse_pos)
        next_button.draw(self.screen)


    # ==========================================================================
    # COMBAT REPORT / GAME OVER SCREEN
    # ==========================================================================
    def draw_combat_report(self, report, buttons, mouse_pos, cam_surface=None):
        self.draw_camera_background(cam_surface, dim_alpha=150)

        cx = self.width // 2
        top_y = 40

        title = self.font_title.render("MOSQUITO COMBAT REPORT", True, COLOR_CYAN)
        self.screen.blit(title, title.get_rect(center=(cx, top_y + 25)))

        subtitle = self.font_body.render("TACTICAL AI PESTILENCE NEUTRALIZATION ASSESSMENT", True, COLOR_GRAY)
        self.screen.blit(subtitle, subtitle.get_rect(center=(cx, top_y + 65)))

        # Big dossier box
        box_w, box_h = 860, 420
        box_x = (self.width - box_w) // 2
        box_y = top_y + 95

        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(box, COLOR_PANEL_BG, (0, 0, box_w, box_h), border_radius=12)
        pygame.draw.rect(box, COLOR_PANEL_BORDER, (0, 0, box_w, box_h), width=2, border_radius=12)
        self.screen.blit(box, (box_x, box_y))

        # Left Column: Raw Metrics
        col1_x = box_x + 40
        y = box_y + 35
        metrics_left = [
            ("TOTAL SCORE", f"{report['score']:,}", COLOR_WHITE),
            ("MOSQUITOES ENCOUNTERED", f"{report['encountered']}", COLOR_WHITE),
            ("MOSQUITOES KILLED", f"{report['killed']}", COLOR_NEON_GREEN),
            ("MOSQUITOES ESCAPED", f"{report['escaped']}", COLOR_RED),
            ("BEST COMBO STREAK", f"x{report['best_combo']}", COLOR_YELLOW),
            ("MISSED SLAPS", f"{report['missed_slaps']}", COLOR_GRAY),
            ("WEBS / BULLETS FIRED", f"{report['webs_fired']} / {report['finger_bullets']}", COLOR_GRAY)
        ]

        for label, val, color in metrics_left:
            l_txt = self.font_body.render(label, True, COLOR_GRAY)
            v_txt = self.font_h2.render(val, True, color)
            self.screen.blit(l_txt, (col1_x, y))
            self.screen.blit(v_txt, (col1_x + 300, y - 4))
            y += 45

        # Right Column: Big Kerala Survival Rating & AI Analysis
        col2_x = box_x + 500
        y2 = box_y + 30

        k_title = self.font_h2.render("CONGRATULATIONS!", True, COLOR_YELLOW)
        self.screen.blit(k_title, (col2_x, y2))

        # Big glowing percentage badge
        badge_val = report["kerala_survival"]
        badge_txt = self.font_title.render(badge_val, True, COLOR_NEON_GREEN)
        self.screen.blit(badge_txt, (col2_x + 20, y2 + 35))

        # Additional tactical rates
        y3 = y2 + 120
        rates = [
            ("KILL RATE", f"{report['kill_rate']}%"),
            ("ACCURACY", f"{report['accuracy']}%"),
            ("REACTION TIME", f"{report['reaction_time']}s")
        ]
        for rl, rv in rates:
            rt_txt = self.font_body.render(f"{rl}: {rv}", True, COLOR_WHITE)
            self.screen.blit(rt_txt, (col2_x, y3))
            y3 += 28

        # Threat Assessment
        th_txt = self.font_small.render("THREAT LEVEL: " + report["threat_level"], True, COLOR_CYAN)
        self.screen.blit(th_txt, (col2_x, y3 + 10))

        # Assigned Rank Title Banner across bottom of box
        rank_banner_y = box_y + box_h - 60
        r_txt = self.font_h2.render("RANK: " + report["title"], True, COLOR_YELLOW)
        self.screen.blit(r_txt, r_txt.get_rect(center=(cx, rank_banner_y)))

        # Draw action buttons
        for btn in buttons:
            btn.update(mouse_pos)
            btn.draw(self.screen)

    # ==========================================================================
    # LEADERBOARD SCREEN
    # ==========================================================================
    def draw_leaderboard(self, scores, back_button, mouse_pos, cam_surface=None):
        self.draw_camera_background(cam_surface, dim_alpha=160)

        cx = self.width // 2
        title = self.font_title.render("LOCAL HALL OF MOSQUITO SLAPPERS", True, COLOR_CYAN)
        self.screen.blit(title, title.get_rect(center=(cx, 75)))

        box_w, box_h = 760, 420
        box_x = (self.width - box_w) // 2
        box_y = 130

        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(box, COLOR_PANEL_BG, (0, 0, box_w, box_h), border_radius=12)
        pygame.draw.rect(box, COLOR_PANEL_BORDER, (0, 0, box_w, box_h), width=2, border_radius=12)
        self.screen.blit(box, (box_x, box_y))

        # Table headers
        hx = box_x + 40
        hy = box_y + 25
        headers = [("RANK", 0), ("AGENT NAME", 100), ("SCORE", 300), ("KILLS", 440), ("KERALA RATING", 560)]
        for h_text, x_off in headers:
            h_surf = self.font_body.render(h_text, True, COLOR_GRAY)
            self.screen.blit(h_surf, (hx + x_off, hy))

        pygame.draw.line(self.screen, COLOR_PANEL_BORDER, (box_x + 20, hy + 30), (box_x + box_w - 20, hy + 30), 2)

        # Rows
        row_y = hy + 45
        for i, s in enumerate(scores):
            r_color = COLOR_YELLOW if i == 0 else (COLOR_CYAN if i == 1 else COLOR_WHITE)
            rank_str = f"#{i+1}"
            self.screen.blit(self.font_h2.render(rank_str, True, r_color), (hx, row_y))
            self.screen.blit(self.font_body.render(s.get("name", "UNKNOWN"), True, COLOR_WHITE), (hx + 100, row_y + 4))
            self.screen.blit(self.font_body.render(f"{s.get('score', 0):,}", True, COLOR_NEON_GREEN), (hx + 300, row_y + 4))
            self.screen.blit(self.font_body.render(str(s.get("kills", 0)), True, COLOR_WHITE), (hx + 440, row_y + 4))
            self.screen.blit(self.font_body.render(str(s.get("rating", "N/A")), True, COLOR_YELLOW), (hx + 560, row_y + 4))
            row_y += 46

        back_button.update(mouse_pos)
        back_button.draw(self.screen)

    # ==========================================================================
    # COUNTDOWN SCREEN (auto-start when 2 hands detected)
    # ==========================================================================
    def draw_countdown(self, cam_surface, seconds_left, hands):
        """Draws a 3-second countdown overlay before auto-starting the game."""
        self.draw_camera_background(cam_surface, dim_alpha=90)

        cx = self.width // 2
        cy = self.height // 2

        num_hands = len(hands)
        # Hand status bar at bottom
        status_color = COLOR_NEON_GREEN if num_hands >= 2 else COLOR_YELLOW
        status_str = f"OPTICAL TRACKING: {num_hands} / 2 HANDS DETECTED"
        status_txt = self.font_h1.render(status_str, True, status_color)
        self.screen.blit(status_txt, status_txt.get_rect(center=(cx, self.height - 80)))

        # GET READY label
        ready_txt = self.font_h1.render("GET READY!", True, COLOR_YELLOW)
        self.screen.blit(ready_txt, ready_txt.get_rect(center=(cx, cy - 120)))

        # Giant pulsing countdown number
        disp_num = str(max(1, math.ceil(seconds_left)))
        pulse = 1.0 + 0.12 * math.sin(time.time() * 8.0)
        base_size = int(180 * pulse)
        count_font = pygame.font.SysFont("impact", base_size)
        # Glow shadow
        glow = count_font.render(disp_num, True, (0, 100, 180))
        self.screen.blit(glow, glow.get_rect(center=(cx + 5, cy + 10)))
        count_surf = count_font.render(disp_num, True, COLOR_CYAN)
        self.screen.blit(count_surf, count_surf.get_rect(center=(cx, cy)))

        # Subtitle
        sub = self.font_body.render("Both hands detected — game auto-starts!", True, COLOR_GRAY)
        self.screen.blit(sub, sub.get_rect(center=(cx, cy + 130)))

    # ==========================================================================
    # PAUSE MENU
    # ==========================================================================
    def draw_pause_menu(self, buttons, mouse_pos, sound_on, cam_surface=None):
        """Draws the pause overlay with Resume, Quit to Menu, and Sound toggle."""
        self.draw_camera_background(cam_surface, dim_alpha=160)

        cx = self.width // 2
        cy = self.height // 2

        # Glass panel
        panel_w, panel_h = 420, 320
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel, COLOR_PANEL_BG, (0, 0, panel_w, panel_h), border_radius=16)
        pygame.draw.rect(panel, COLOR_CYAN, (0, 0, panel_w, panel_h), width=3, border_radius=16)
        self.screen.blit(panel, (cx - panel_w // 2, cy - panel_h // 2))

        # Title
        title = self.font_title.render("PAUSED", True, COLOR_CYAN)
        glow = self.font_title.render("PAUSED", True, (0, 80, 120))
        self.screen.blit(glow, glow.get_rect(center=(cx + 3, cy - 118)))
        self.screen.blit(title, title.get_rect(center=(cx, cy - 120)))

        # Draw buttons
        btn_resume, btn_menu, btn_sound = buttons
        # Dynamically update sound button label
        btn_sound.text = f"SOUND: {'ON  ●' if sound_on else 'OFF ○'}"
        for btn in buttons:
            btn.update(mouse_pos)
            btn.draw(self.screen)
