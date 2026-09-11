"""
effects.py — Visual effects engine: particle systems, web projectiles,
tactical laser beams, floating score text popups, and screen shake.
"""

import math
import random
import pygame
import numpy as np
import config

class Particle:
    """Individual cartoon splat/spark particle."""
    def __init__(self, x, y, color, vx=None, vy=None, radius=None, lifespan=0.45):
        self.x = float(x)
        self.y = float(y)
        self.color = color

        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(60, 320)
        self.vx = vx if vx is not None else math.cos(angle) * speed
        self.vy = vy if vy is not None else math.sin(angle) * speed

        self.radius = radius if radius is not None else random.uniform(3, 8)
        self.lifespan = lifespan
        self.age = 0.0

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        # Air drag and gravity
        self.vx *= (1.0 - 1.8 * dt)
        self.vy += 220 * dt

    def is_dead(self):
        return self.age >= self.lifespan

    def draw(self, surface):
        progress = self.age / self.lifespan
        alpha = max(0, int(255 * (1.0 - progress)))
        r = max(1, int(self.radius * (1.0 - 0.3 * progress)))

        # Create small temporary alpha surface for smooth fading
        p_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        color_with_alpha = (*self.color[:3], alpha)
        pygame.draw.circle(p_surf, color_with_alpha, (r, r), r)
        surface.blit(p_surf, (int(self.x - r), int(self.y - r)))

class FloatingText:
    """Animated floating text popup (+100, THWIP!, Combo, Miss roast)."""
    def __init__(self, text, x, y, color=(255, 255, 255), font_size=28, lifespan=0.9, vy=-90):
        self.text = text
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.font_size = font_size
        self.lifespan = lifespan
        self.age = 0.0
        self.vy = vy

    def update(self, dt):
        self.age += dt
        self.y += self.vy * dt

    def is_dead(self):
        return self.age >= self.lifespan

    def draw(self, surface, font):
        progress = self.age / self.lifespan
        alpha = max(0, int(255 * (1.0 - progress)))

        # Render text with black shadow/outline
        text_surf = font.render(self.text, True, self.color)
        shadow_surf = font.render(self.text, True, (0, 0, 0))

        # Scale slightly on pop
        scale = 1.0 + 0.3 * math.sin(progress * math.pi)
        if scale != 1.0:
            w = int(text_surf.get_width() * scale)
            h = int(text_surf.get_height() * scale)
            text_surf = pygame.transform.scale(text_surf, (w, h))
            shadow_surf = pygame.transform.scale(shadow_surf, (w, h))

        text_surf.set_alpha(alpha)
        shadow_surf.set_alpha(alpha)

        rect = text_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(shadow_surf, (rect.x + 2, rect.y + 2))
        surface.blit(text_surf, rect)

class WebProjectile:
    """Animated Spider-Man web projectile with trailing silk line."""
    def __init__(self, origin_x, origin_y, dir_x, dir_y):
        self.origin = np.array([origin_x, origin_y], dtype=np.float32)
        self.pos = np.array([origin_x, origin_y], dtype=np.float32)
        self.dir = np.array([dir_x, dir_y], dtype=np.float32)
        self.speed = config.WEB_SPEED
        self.lifetime = config.WEB_LIFETIME
        self.age = 0.0
        self.radius = config.WEB_RADIUS
        self.is_exploding = False
        self.explode_age = 0.0
        self.explode_duration = 0.22

    def update(self, dt):
        if self.is_exploding:
            self.explode_age += dt
            return

        self.age += dt
        self.pos += self.dir * self.speed * dt

    def is_dead(self):
        if self.is_exploding:
            return self.explode_age >= self.explode_duration
        return self.age >= self.lifetime

    def explode(self):
        self.is_exploding = True

    def draw(self, surface):
        if self.is_exploding:
            # Draw expanding spider web net
            progress = self.explode_age / self.explode_duration
            cur_r = int(config.WEB_EXPAND_MAX_RADIUS * math.sqrt(progress))
            alpha = max(0, int(255 * (1.0 - progress)))

            web_surf = pygame.Surface((cur_r * 2 + 4, cur_r * 2 + 4), pygame.SRCALPHA)
            wc = (240, 248, 255, alpha)
            c = cur_r + 2
            # Concentric web rings
            for ring_r in [cur_r // 3, (cur_r * 2) // 3, cur_r]:
                if ring_r > 2:
                    pygame.draw.circle(web_surf, wc, (c, c), ring_r, 2)
            # Radial web spokes
            for i in range(8):
                rad = i * (math.pi / 4)
                ex = c + int(cur_r * math.cos(rad))
                ey = c + int(cur_r * math.sin(rad))
                pygame.draw.line(web_surf, wc, (c, c), (ex, ey), 2)

            surface.blit(web_surf, (int(self.pos[0] - c), int(self.pos[1] - c)))
        else:
            # Trailing silk filament
            line_color = (230, 245, 255, 180)
            pygame.draw.line(surface, line_color,
                             (int(self.origin[0]), int(self.origin[1])),
                             (int(self.pos[0]), int(self.pos[1])), 3)

            # Web projectile head
            head_x, head_y = int(self.pos[0]), int(self.pos[1])
            pygame.draw.circle(surface, (255, 255, 255), (head_x, head_y), 10)
            pygame.draw.circle(surface, (0, 220, 255), (head_x, head_y), 14, 2)

            # Mini web spokes around head
            for i in range(6):
                rad = self.age * 12 + i * (math.pi / 3)
                sx = head_x + int(16 * math.cos(rad))
                sy = head_y + int(16 * math.sin(rad))
                pygame.draw.line(surface, (200, 235, 255), (head_x, head_y), (sx, sy), 2)

class LaserBeam:
    """Tactical dual laser execution beam with pulsating neon aura."""
    def __init__(self, origin_l, origin_r, target_pos):
        self.origin_l = origin_l
        self.origin_r = origin_r
        self.target = target_pos
        self.duration = config.LASER_BEAM_DURATION
        self.age = 0.0

    def update(self, dt):
        self.age += dt

    def is_dead(self):
        return self.age >= self.duration

    def draw(self, surface):
        progress = self.age / self.duration
        alpha = max(0, int(255 * (1.0 - progress)))

        # Electric neon colors: Core white, Aura cyan/magenta
        for orig in (self.origin_l, self.origin_r):
            # Outer aura
            p1 = (int(orig[0]), int(orig[1]))
            p2 = (int(self.target[0]), int(self.target[1]))

            # Draw thick aura
            pygame.draw.line(surface, (0, 180, 255, alpha), p1, p2, 12)
            pygame.draw.line(surface, (0, 255, 230, alpha), p1, p2, 6)
            # White hot laser core
            pygame.draw.line(surface, (255, 255, 255, alpha), p1, p2, 3)

        # Huge impact flash at target
        tx, ty = int(self.target[0]), int(self.target[1])
        r = int(35 * (1.0 - progress * 0.5))
        pygame.draw.circle(surface, (255, 255, 255), (tx, ty), r)
        pygame.draw.circle(surface, (0, 230, 255), (tx, ty), r + 8, 3)

class Shockwave:
    """Expanding cartoon slap shockwave ring."""
    def __init__(self, x, y, max_radius=140, duration=0.25, color=(255, 255, 255)):
        self.x = float(x)
        self.y = float(y)
        self.max_radius = float(max_radius)
        self.duration = duration
        self.color = color
        self.age = 0.0

    def update(self, dt):
        self.age += dt

    def is_dead(self):
        return self.age >= self.duration

    def draw(self, surface):
        progress = self.age / self.duration
        alpha = max(0, int(255 * (1.0 - progress)))
        cur_r = max(4, int(self.max_radius * math.sqrt(progress)))
        ring_surf = pygame.Surface((cur_r * 2 + 8, cur_r * 2 + 8), pygame.SRCALPHA)
        c = cur_r + 4
        # Draw double shockwave rings
        pygame.draw.circle(ring_surf, (*self.color[:3], alpha), (c, c), cur_r, 4)
        if cur_r > 16:
            pygame.draw.circle(ring_surf, (0, 220, 255, alpha // 2), (c, c), cur_r - 10, 2)
        surface.blit(ring_surf, (int(self.x - c), int(self.y - c)))

class EffectsManager:
    """Coordinates all visual effects, screen shake, and floating text."""
    def __init__(self):
        self.particles = []
        self.floating_texts = []
        self.projectiles = []
        self.lasers = []
        self.shockwaves = []

        self.shake_duration = 0.0
        self.shake_intensity = 0.0
        self.shake_offset = [0, 0]

    def trigger_shake(self, intensity=10, duration=0.25):
        self.shake_intensity = max(self.shake_intensity, intensity)
        self.shake_duration = max(self.shake_duration, duration)

    def add_shockwave(self, x, y, max_radius=140):
        self.shockwaves.append(Shockwave(x, y, max_radius))

    def add_splat(self, x, y, count=22):
        """Creates cartoon blood/goo particles and yellow impact sparks."""
        # Red blood drops
        for _ in range(count):
            color = random.choice([
                (210, 20, 20), (180, 15, 15), (240, 40, 40), (140, 10, 10)
            ])
            self.particles.append(Particle(x, y, color, lifespan=random.uniform(0.35, 0.65)))

        # Golden impact stars
        for _ in range(count // 2):
            color = random.choice([(255, 240, 80), (255, 255, 200)])
            self.particles.append(Particle(x, y, color, radius=random.uniform(2, 4), lifespan=0.25))

    def add_floating_text(self, text, x, y, color=(255, 255, 255), font_size=28, vy=-90):
        self.floating_texts.append(FloatingText(text, x, y, color, font_size, vy=vy))

    def add_web(self, origin_x, origin_y, dir_x, dir_y):
        self.projectiles.append(WebProjectile(origin_x, origin_y, dir_x, dir_y))

    def add_laser(self, origin_l, origin_r, target_pos):
        self.lasers.append(LaserBeam(origin_l, origin_r, target_pos))
        self.trigger_shake(intensity=14, duration=0.28)

    def update(self, dt):
        # Update shockwaves
        for sw in self.shockwaves:
            sw.update(dt)
        self.shockwaves = [sw for sw in self.shockwaves if not sw.is_dead()]

        # Update particles
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if not p.is_dead()]

        # Update floating texts
        for ft in self.floating_texts:
            ft.update(dt)
        self.floating_texts = [ft for ft in self.floating_texts if not ft.is_dead()]

        # Update projectiles
        for pr in self.projectiles:
            pr.update(dt)
        self.projectiles = [pr for pr in self.projectiles if not pr.is_dead()]

        # Update lasers
        for l in self.lasers:
            l.update(dt)
        self.lasers = [l for l in self.lasers if not l.is_dead()]

        # Update screen shake
        if self.shake_duration > 0:
            self.shake_duration -= dt
            self.shake_offset = [
                random.randint(-int(self.shake_intensity), int(self.shake_intensity)),
                random.randint(-int(self.shake_intensity), int(self.shake_intensity))
            ]
            self.shake_intensity = max(0.0, self.shake_intensity - (40 * dt))
        else:
            self.shake_offset = [0, 0]

    def draw(self, surface, font):
        # Draw shockwaves
        for sw in self.shockwaves:
            sw.draw(surface)

        # Draw web projectiles
        for pr in self.projectiles:
            pr.draw(surface)

        # Draw laser beams
        for l in self.lasers:
            l.draw(surface)

        # Draw particles
        for p in self.particles:
            p.draw(surface)

        # Draw floating texts
        for ft in self.floating_texts:
            ft.draw(surface, font)
