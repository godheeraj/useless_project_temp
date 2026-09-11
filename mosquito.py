"""
mosquito.py — Mosquito entity with 6 movement patterns, flapping wing animation,
boundary steering, and procedural cartoon sprite generation.
"""

import math
import random
import os
# pyrefly: ignore [missing-import]
import pygame
import config

# Global sprite cache
_SPRITE_CACHE = {}

def create_procedural_mosquito_sprites():
    """Generates procedural cartoon mosquito sprites (wings up, wings down, dead)."""
    base_size = 72

    # 1. Alive Frame 1 (Wings UP)
    surf_up = pygame.Surface((base_size, base_size), pygame.SRCALPHA)
    cx, cy = base_size // 2, base_size // 2

    # Abdomen (striped oval)
    pygame.draw.ellipse(surf_up, (45, 45, 45), (cx - 7, cy + 2, 14, 26))
    pygame.draw.ellipse(surf_up, (90, 80, 50), (cx - 6, cy + 7, 12, 4))
    pygame.draw.ellipse(surf_up, (90, 80, 50), (cx - 6, cy + 15, 12, 4))

    # Thorax
    pygame.draw.circle(surf_up, (60, 60, 60), (cx, cy - 4), 9)

    # Head & Big Cartoon Eyes
    pygame.draw.circle(surf_up, (40, 40, 40), (cx, cy - 16), 7)
    pygame.draw.circle(surf_up, (220, 30, 30), (cx - 4, cy - 18), 4)
    pygame.draw.circle(surf_up, (220, 30, 30), (cx + 4, cy - 18), 4)
    pygame.draw.circle(surf_up, (255, 255, 255), (cx - 3, cy - 19), 1)
    pygame.draw.circle(surf_up, (255, 255, 255), (cx + 5, cy - 19), 1)

    # Needle Proboscis
    pygame.draw.line(surf_up, (20, 20, 20), (cx, cy - 22), (cx, cy - 33), 2)

    # Six bent legs
    leg_color = (30, 30, 30)
    # Left legs
    pygame.draw.lines(surf_up, leg_color, False, [(cx - 6, cy - 6), (cx - 18, cy - 14), (cx - 24, cy - 6)], 2)
    pygame.draw.lines(surf_up, leg_color, False, [(cx - 7, cy - 2), (cx - 22, cy - 1), (cx - 28, cy + 12)], 2)
    pygame.draw.lines(surf_up, leg_color, False, [(cx - 6, cy + 4), (cx - 20, cy + 12), (cx - 24, cy + 26)], 2)
    # Right legs
    pygame.draw.lines(surf_up, leg_color, False, [(cx + 6, cy - 6), (cx + 18, cy - 14), (cx + 24, cy - 6)], 2)
    pygame.draw.lines(surf_up, leg_color, False, [(cx + 7, cy - 2), (cx + 22, cy - 1), (cx + 28, cy + 12)], 2)
    pygame.draw.lines(surf_up, leg_color, False, [(cx + 6, cy + 4), (cx + 20, cy + 12), (cx + 24, cy + 26)], 2)

    # Wings UP (angled upwards, translucent cyan/white)
    wing_surf = pygame.Surface((base_size, base_size), pygame.SRCALPHA)
    pygame.draw.ellipse(wing_surf, (220, 240, 255, 175), (cx - 22, cy - 24, 20, 36))
    pygame.draw.ellipse(wing_surf, (220, 240, 255, 175), (cx + 2, cy - 24, 20, 36))
    pygame.draw.ellipse(wing_surf, (255, 255, 255, 230), (cx - 20, cy - 22, 16, 30), 1)
    pygame.draw.ellipse(wing_surf, (255, 255, 255, 230), (cx + 4, cy - 22, 16, 30), 1)
    surf_up.blit(wing_surf, (0, 0))

    # 2. Alive Frame 2 (Wings SPREAD / DOWN)
    surf_down = pygame.Surface((base_size, base_size), pygame.SRCALPHA)
    # Copy body
    surf_down.blit(surf_up, (0, 0))
    # Cover old wings with new horizontal spread wings
    wing_surf2 = pygame.Surface((base_size, base_size), pygame.SRCALPHA)
    pygame.draw.ellipse(wing_surf2, (220, 240, 255, 180), (cx - 30, cy - 12, 28, 18))
    pygame.draw.ellipse(wing_surf2, (220, 240, 255, 180), (cx + 2, cy - 12, 28, 18))
    pygame.draw.ellipse(wing_surf2, (255, 255, 255, 230), (cx - 28, cy - 10, 24, 14), 1)
    pygame.draw.ellipse(wing_surf2, (255, 255, 255, 230), (cx + 4, cy - 10, 24, 14), 1)

    # 3. Dead / Splatted Sprite
    surf_dead = pygame.Surface((base_size, base_size), pygame.SRCALPHA)
    # Red cartoon splat in background
    pygame.draw.circle(surf_dead, (190, 20, 20, 180), (cx, cy), 22)
    for _ in range(6):
        ox = cx + random.randint(-18, 18)
        oy = cy + random.randint(-18, 18)
        r = random.randint(4, 9)
        pygame.draw.circle(surf_dead, (180, 15, 15, 200), (ox, oy), r)

    # Squished body
    pygame.draw.ellipse(surf_dead, (35, 35, 35), (cx - 16, cy - 10, 32, 20))
    # Comical 'X' eyes
    def draw_x(s, px, py, size=5):
        pygame.draw.line(s, (255, 255, 255), (px - size, py - size), (px + size, py + size), 2)
        pygame.draw.line(s, (255, 255, 255), (px - size, py + size), (px + size, py - size), 2)
    draw_x(surf_dead, cx - 8, cy - 4)
    draw_x(surf_dead, cx + 8, cy - 4)
    # Bent broken legs sticking out
    pygame.draw.line(surf_dead, (20, 20, 20), (cx - 14, cy), (cx - 28, cy - 12), 2)
    pygame.draw.line(surf_dead, (20, 20, 20), (cx + 14, cy), (cx + 28, cy + 12), 2)
    pygame.draw.line(surf_dead, (20, 20, 20), (cx - 10, cy + 8), (cx - 22, cy + 22), 2)

    # Save sprites to cache and disk
    os.makedirs(config.SPRITES_DIR, exist_ok=True)
    pygame.image.save(surf_up, os.path.join(config.SPRITES_DIR, "mosquito_up.png"))
    pygame.image.save(surf_down, os.path.join(config.SPRITES_DIR, "mosquito_down.png"))
    pygame.image.save(surf_dead, os.path.join(config.SPRITES_DIR, "mosquito_dead.png"))

    return {
        "up": surf_up,
        "down": surf_down,
        "dead": surf_dead
    }

def get_sprites():
    global _SPRITE_CACHE
    if not _SPRITE_CACHE:
        # Check if disk files exist, else create procedurally
        up_path = os.path.join(config.SPRITES_DIR, "mosquito_up.png")
        down_path = os.path.join(config.SPRITES_DIR, "mosquito_down.png")
        dead_path = os.path.join(config.SPRITES_DIR, "mosquito_dead.png")

        if os.path.exists(up_path) and os.path.exists(down_path) and os.path.exists(dead_path):
            try:
                _SPRITE_CACHE["up"] = pygame.image.load(up_path).convert_alpha()
                _SPRITE_CACHE["down"] = pygame.image.load(down_path).convert_alpha()
                _SPRITE_CACHE["dead"] = pygame.image.load(dead_path).convert_alpha()
            except Exception:
                _SPRITE_CACHE = create_procedural_mosquito_sprites()
        else:
            _SPRITE_CACHE = create_procedural_mosquito_sprites()

    return _SPRITE_CACHE

class Mosquito:
    """
    Simulates a live mosquito with dynamic behaviors:
    1. Random wander
    2. Sinusoidal flutter
    3. Sudden direction darting
    4. Accelerating burst
    5. Hover pause
    6. Zig-zag evasions
    """
    _id_counter = 0

    BEHAVIORS = ["wander", "sine", "dart", "sprint", "hover", "zigzag"]

    def __init__(self, x, y, level=1):
        Mosquito._id_counter += 1
        self.id = Mosquito._id_counter
        self.x = float(x)
        self.y = float(y)
        self.level = level

        # Level configuration
        lvl_cfg = config.LEVELS.get(level, config.LEVELS[1])
        base_speed = random.uniform(lvl_cfg["mosquito_speed_min"], lvl_cfg["mosquito_speed_max"])
        self.base_speed = base_speed
        self.speed = base_speed
        self.scale = lvl_cfg["mosquito_scale"] * random.uniform(0.92, 1.08)

        # Movement direction
        self.angle = random.uniform(0, 2 * math.pi)
        self.vx = math.cos(self.angle) * self.speed
        self.vy = math.sin(self.angle) * self.speed

        # Behavior assignment
        self.behavior = random.choice(self.BEHAVIORS)
        self.behavior_timer = random.uniform(1.5, 3.5)

        # Internal animation & flutter
        self.time_alive = random.uniform(0, 100)
        self.wing_state = 0
        self.wing_timer = 0.0
        self.radius = int(24 * self.scale)

        # Sine & ZigZag parameters
        self.sine_freq = random.uniform(6.0, 12.0)
        self.sine_amp = random.uniform(40.0, 90.0)
        self.zigzag_sign = 1

        # Life state
        self.is_alive = True
        self.death_timer = 0.0
        self.death_duration = 0.55
        self.killer_gesture = ""

    def update(self, dt):
        """Updates position, flight steering, and wing flapping animation."""
        if not self.is_alive:
            self.death_timer += dt
            # Fall downwards slowly with gravity on death
            self.y += 180 * dt
            return

        self.time_alive += dt
        self.behavior_timer -= dt

        # Switch behaviors periodically
        if self.behavior_timer <= 0:
            self.behavior = random.choice(self.BEHAVIORS)
            self.behavior_timer = random.uniform(1.2, 3.0)
            if self.behavior == "sprint":
                self.speed = self.base_speed * 1.8
            elif self.behavior == "hover":
                self.speed = self.base_speed * 0.15
            else:
                self.speed = self.base_speed

        # Execute current flight pattern
        if self.behavior == "wander":
            # Smooth steering wander
            self.angle += random.uniform(-2.5, 2.5) * dt
            self.vx = math.cos(self.angle) * self.speed
            self.vy = math.sin(self.angle) * self.speed

        elif self.behavior == "sine":
            # Sinusoidal flutter
            self.angle += random.uniform(-0.8, 0.8) * dt
            perp_angle = self.angle + math.pi / 2
            sine_offset = math.sin(self.time_alive * self.sine_freq) * self.sine_amp
            self.vx = math.cos(self.angle) * self.speed + math.cos(perp_angle) * sine_offset
            self.vy = math.sin(self.angle) * self.speed + math.sin(perp_angle) * sine_offset

        elif self.behavior == "dart":
            # Sudden abrupt direction snap
            if random.random() < (0.04 * (60 * dt)):
                self.angle += random.choice([-1.2, 1.2, 2.1, -2.1])
            self.vx = math.cos(self.angle) * self.speed
            self.vy = math.sin(self.angle) * self.speed

        elif self.behavior == "sprint":
            self.vx = math.cos(self.angle) * self.speed
            self.vy = math.sin(self.angle) * self.speed

        elif self.behavior == "hover":
            # Hover with micro jitter
            self.vx = math.cos(self.angle) * self.speed + random.uniform(-20, 20)
            self.vy = math.sin(self.angle) * self.speed + random.uniform(-20, 20)

        elif self.behavior == "zigzag":
            # High-frequency alternating zig-zag
            if random.random() < (0.08 * (60 * dt)):
                self.zigzag_sign *= -1
            zig_angle = self.angle + (self.zigzag_sign * 0.9)
            self.vx = math.cos(zig_angle) * self.speed
            self.vy = math.sin(zig_angle) * self.speed

        # Apply velocity
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Boundary steering & bounce
        margin = 40
        if self.x < margin:
            self.x = margin
            self.angle = math.pi - self.angle + random.uniform(-0.3, 0.3)
        elif self.x > config.SCREEN_WIDTH - margin:
            self.x = config.SCREEN_WIDTH - margin
            self.angle = math.pi - self.angle + random.uniform(-0.3, 0.3)

        if self.y < margin + 60:  # Top HUD margin
            self.y = margin + 60
            self.angle = -self.angle + random.uniform(-0.3, 0.3)
        elif self.y > config.SCREEN_HEIGHT - margin:
            self.y = config.SCREEN_HEIGHT - margin
            self.angle = -self.angle + random.uniform(-0.3, 0.3)

        # Wing animation (very fast flap ~30 Hz)
        self.wing_timer += dt
        if self.wing_timer > 0.033:
            self.wing_timer = 0.0
            self.wing_state = 1 - self.wing_state

    def kill(self, gesture="SLAP"):
        """Marks mosquito as dead and triggers death state."""
        if self.is_alive:
            self.is_alive = False
            self.killer_gesture = gesture
            self.death_timer = 0.0

    def is_finished(self):
        """Returns True when death animation is complete and mosquito can be removed."""
        return not self.is_alive and self.death_timer >= self.death_duration

    def draw(self, surface):
        """Renders mosquito sprite with body rotation and wing flap."""
        sprites = get_sprites()

        if self.is_alive:
            spr = sprites["up"] if self.wing_state == 0 else sprites["down"]
            # Rotate sprite towards flight angle (in degrees, Pygame rotates CCW)
            # Default sprite faces upwards (-90 deg in cartesian)
            rot_deg = -math.degrees(self.angle) - 90
            scaled_w = int(spr.get_width() * self.scale)
            scaled_h = int(spr.get_height() * self.scale)
            scaled_spr = pygame.transform.scale(spr, (scaled_w, scaled_h))
            rotated_spr = pygame.transform.rotate(scaled_spr, rot_deg)
            rect = rotated_spr.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(rotated_spr, rect)
        else:
            # Dead squashed sprite with fade out
            spr = sprites["dead"]
            alpha = max(0, int(255 * (1.0 - self.death_timer / self.death_duration)))
            scaled_w = int(spr.get_width() * self.scale)
            scaled_h = int(spr.get_height() * self.scale)
            scaled_spr = pygame.transform.scale(spr, (scaled_w, scaled_h))
            scaled_spr.set_alpha(alpha)
            rect = scaled_spr.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(scaled_spr, rect)
