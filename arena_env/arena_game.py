"""
Core Pygame Action Arena simulation engine for Assignment 3 Part 2.
Implements continuous physics, entity management, collision detection,
particle visual effects, health systems, and phase progression.
"""

import math
import random
import pygame
from pygame.math import Vector2
from . import config


class Particle:
    """Visual particle for explosions, hits, and thruster exhaust."""

    def __init__(self, x, y, vx, vy, color, radius, lifetime):
        self.pos = Vector2(x, y)
        self.vel = Vector2(vx, vy)
        self.color = color
        self.radius = radius
        self.max_lifetime = lifetime
        self.lifetime = lifetime

    def update(self, dt):
        self.pos += self.vel * dt
        self.vel *= 0.95  # friction
        self.lifetime -= dt

    @property
    def is_alive(self):
        return self.lifetime > 0

    def draw(self, surface):
        if self.lifetime <= 0:
            return
        alpha = max(0, min(255, int(255 * (self.lifetime / self.max_lifetime))))
        r = max(1, int(self.radius * (self.lifetime / self.max_lifetime)))
        p_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        c = (self.color[0], self.color[1], self.color[2], alpha)
        pygame.draw.circle(p_surf, c, (r + 1, r + 1), r)
        surface.blit(p_surf, (self.pos.x - r - 1, self.pos.y - r - 1))


class Bullet:
    """Projectile fired by player ship."""

    def __init__(self, x, y, direction_vector, speed=config.BULLET_SPEED):
        self.pos = Vector2(x, y)
        self.vel = direction_vector.normalize() * speed if direction_vector.length() > 0 else Vector2(1, 0) * speed
        self.radius = config.BULLET_RADIUS
        self.lifetime = config.BULLET_LIFETIME
        self.damage = config.BULLET_DAMAGE
        self.is_alive = True

    def update(self, dt, width, height):
        self.pos += self.vel * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.is_alive = False
        # Arena boundary check (including top HUD bar boundary)
        if self.pos.x < 0 or self.pos.x > width or self.pos.y < config.HUD_HEIGHT or self.pos.y > height:
            self.is_alive = False

    def draw(self, surface):
        center = (int(self.pos.x), int(self.pos.y))
        pygame.draw.circle(surface, (255, 255, 200), center, int(self.radius))
        pygame.draw.circle(surface, config.COLOR_BULLET, center, int(self.radius + 2), 1)


class Enemy:
    """Chaser enemy spawned by spawners that navigates toward the player."""

    def __init__(self, x, y, speed=config.ENEMY_BASE_SPEED):
        self.pos = Vector2(x, y)
        self.vel = Vector2(0, 0)
        self.speed = speed
        self.radius = config.ENEMY_RADIUS
        self.max_health = config.ENEMY_MAX_HEALTH
        self.health = self.max_health
        self.is_alive = True
        self.damage = config.ENEMY_DAMAGE
        self.attack_cooldown = 0.0
        self.angle = 0.0

    def update(self, dt, target_pos, width, height):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        # Steering towards player
        to_target = target_pos - self.pos
        dist = to_target.length()
        if dist > 0.001:
            desired_vel = (to_target / dist) * self.speed
            self.vel += (desired_vel - self.vel) * min(1.0, 10.0 * dt)
            self.angle = math.degrees(math.atan2(self.vel.y, self.vel.x))

        self.pos += self.vel * dt

        # Clamp within arena (strictly below HUD)
        min_y = config.HUD_HEIGHT + self.radius + 2
        self.pos.x = max(self.radius, min(width - self.radius, self.pos.x))
        self.pos.y = max(min_y, min(height - self.radius, self.pos.y))

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
            return True
        return False

    def draw(self, surface):
        center = (int(self.pos.x), int(self.pos.y))
        rad = math.radians(self.angle)
        fwd = Vector2(math.cos(rad), math.sin(rad))
        right = Vector2(-fwd.y, fwd.x)

        p1 = self.pos + fwd * self.radius
        p2 = self.pos - fwd * (self.radius * 0.7) + right * (self.radius * 0.7)
        p3 = self.pos - fwd * (self.radius * 0.3)
        p4 = self.pos - fwd * (self.radius * 0.7) - right * (self.radius * 0.7)

        pts = [(int(p.x), int(p.y)) for p in [p1, p2, p3, p4]]
        pygame.draw.polygon(surface, config.COLOR_ENEMY, pts)
        pygame.draw.polygon(surface, (255, 180, 200), pts, 1)

        if self.health < self.max_health:
            bar_w = 20
            bar_h = 3
            bx = self.pos.x - bar_w / 2
            by = self.pos.y - self.radius - 6
            pct = max(0.0, self.health / self.max_health)
            pygame.draw.rect(surface, config.COLOR_HEALTH_BG, (bx, by, bar_w, bar_h))
            pygame.draw.rect(surface, config.COLOR_HEALTH_DAMAGE, (bx, by, int(bar_w * pct), bar_h))


class Spawner:
    """Pulsing base structure that periodically creates enemies."""

    def __init__(self, x, y, spawn_interval=config.SPAWNER_BASE_INTERVAL, enemy_speed=config.ENEMY_BASE_SPEED):
        self.pos = Vector2(x, y)
        self.radius = config.SPAWNER_RADIUS
        self.max_health = config.SPAWNER_MAX_HEALTH
        self.health = self.max_health
        self.spawn_interval = spawn_interval
        self.enemy_speed = enemy_speed
        self.spawn_timer = random.uniform(0.5, spawn_interval)
        self.is_alive = True
        self.pulse_phase = random.uniform(0, math.pi * 2)

    def update(self, dt, current_enemy_count):
        self.pulse_phase += dt * 3.0
        self.spawn_timer -= dt
        spawned_enemy = None
        if self.spawn_timer <= 0:
            self.spawn_timer = self.spawn_interval
            spawn_angle = random.uniform(0, math.pi * 2)
            spawn_dist = self.radius + config.ENEMY_RADIUS + 4.0
            sx = self.pos.x + math.cos(spawn_angle) * spawn_dist
            sy = self.pos.y + math.sin(spawn_angle) * spawn_dist
            # Keep spawned enemy strictly below HUD
            sy = max(config.HUD_HEIGHT + config.ENEMY_RADIUS + 4, sy)
            spawned_enemy = Enemy(sx, sy, speed=self.enemy_speed)
        return spawned_enemy

    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
            return True
        return False

    def draw(self, surface):
        center = (int(self.pos.x), int(self.pos.y))
        pulse_r = self.radius + math.sin(self.pulse_phase) * 3.0

        pygame.draw.circle(surface, config.COLOR_SPAWNER, center, int(pulse_r), 2)
        pts = []
        for i in range(8):
            ang = self.pulse_phase * 0.5 + i * (math.pi / 4)
            px = self.pos.x + math.cos(ang) * (self.radius * 0.7)
            py = self.pos.y + math.sin(ang) * (self.radius * 0.7)
            pts.append((int(px), int(py)))
        pygame.draw.polygon(surface, config.COLOR_SPAWNER_CORE, pts)
        pygame.draw.circle(surface, (255, 255, 255), center, 4)

        bar_w = 36
        bar_h = 5
        bx = self.pos.x - bar_w / 2
        by = self.pos.y - self.radius - 10
        pct = max(0.0, self.health / self.max_health)
        pygame.draw.rect(surface, config.COLOR_HEALTH_BG, (bx, by, bar_w, bar_h))
        pygame.draw.rect(surface, config.COLOR_SPAWNER, (bx, by, int(bar_w * pct), bar_h))
        pygame.draw.rect(surface, (255, 255, 255), (bx, by, bar_w, bar_h), 1)


class PlayerShip:
    """Controllable player ship supporting both Control Style 1 and Control Style 2."""

    def __init__(self, x, y, control_style=1):
        self.pos = Vector2(x, y)
        self.vel = Vector2(0, 0)
        self.angle = -90.0
        self.control_style = control_style
        self.radius = config.SHIP_RADIUS
        self.max_health = config.SHIP_MAX_HEALTH
        self.health = self.max_health
        self.shoot_cooldown = 0.0
        self.invuln_timer = 0.0
        self.is_thrusting = False
        self.is_alive = True

    @property
    def heading_vector(self):
        rad = math.radians(self.angle)
        return Vector2(math.cos(rad), math.sin(rad))

    def reset(self, x, y, control_style=None):
        self.pos = Vector2(x, y)
        self.vel = Vector2(0, 0)
        self.angle = -90.0
        if control_style is not None:
            self.control_style = control_style
        self.health = self.max_health
        self.shoot_cooldown = 0.0
        self.invuln_timer = 0.0
        self.is_thrusting = False
        self.is_alive = True

    def apply_action(self, action_idx, dt):
        fired_bullet = False
        self.is_thrusting = False

        if self.control_style == 1:
            # Control Style 1: 0:Noop, 1:Thrust, 2:RotLeft, 3:RotRight, 4:Shoot
            if action_idx == 1:
                self.is_thrusting = True
                fwd = self.heading_vector
                self.vel += fwd * (config.SHIP_THRUST * dt)
            elif action_idx == 2:
                self.angle -= config.SHIP_ROT_SPEED * dt
            elif action_idx == 3:
                self.angle += config.SHIP_ROT_SPEED * dt
            elif action_idx == 4:
                if self.shoot_cooldown <= 0:
                    fired_bullet = True
                    self.shoot_cooldown = config.BULLET_COOLDOWN

        elif self.control_style == 2:
            # Control Style 2: 0:Noop, 1:Up, 2:Down, 3:Left, 4:Right, 5:Shoot
            direct_dir = Vector2(0, 0)
            if action_idx == 1:
                direct_dir.y = -1
            elif action_idx == 2:
                direct_dir.y = 1
            elif action_idx == 3:
                direct_dir.x = -1
            elif action_idx == 4:
                direct_dir.x = 1
            elif action_idx == 5:
                if self.shoot_cooldown <= 0:
                    fired_bullet = True
                    self.shoot_cooldown = config.BULLET_COOLDOWN

            if direct_dir.length() > 0:
                self.is_thrusting = True
                target_vel = direct_dir.normalize() * config.SHIP_DIRECT_SPEED
                blend = min(1.0, 16.0 * dt)
                self.vel += (target_vel - self.vel) * blend
                self.angle = math.degrees(math.atan2(direct_dir.y, direct_dir.x))
            else:
                self.vel *= 0.88

        return fired_bullet

    def update(self, dt, width, height):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
        if self.invuln_timer > 0:
            self.invuln_timer -= dt

        if self.control_style == 1:
            self.vel *= config.SHIP_LINEAR_DRAG
            if self.vel.length() > config.SHIP_MAX_SPEED:
                self.vel = self.vel.normalize() * config.SHIP_MAX_SPEED

        self.pos += self.vel * dt

        # Wall bounds collision (Strictly below HUD height)
        hit_wall = False
        min_y = config.HUD_HEIGHT + self.radius + 2

        if self.pos.x < self.radius:
            self.pos.x = self.radius
            self.vel.x = -self.vel.x * 0.5
            hit_wall = True
        elif self.pos.x > width - self.radius:
            self.pos.x = width - self.radius
            self.vel.x = -self.vel.x * 0.5
            hit_wall = True

        if self.pos.y < min_y:
            self.pos.y = min_y
            self.vel.y = -self.vel.y * 0.5
            hit_wall = True
        elif self.pos.y > height - self.radius:
            self.pos.y = height - self.radius
            self.vel.y = -self.vel.y * 0.5
            hit_wall = True

        return hit_wall

    def take_damage(self, amount):
        if self.invuln_timer > 0:
            return False
        self.health -= amount
        self.invuln_timer = config.SHIP_INVULN_TIME
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
        return True

    def draw(self, surface):
        if not self.is_alive:
            return

        rad = math.radians(self.angle)
        fwd = Vector2(math.cos(rad), math.sin(rad))
        right = Vector2(-fwd.y, fwd.x)

        if self.is_thrusting:
            t_len = random.uniform(8, 16)
            t_back = self.pos - fwd * (self.radius + t_len)
            t1 = self.pos - fwd * (self.radius * 0.7) + right * (self.radius * 0.35)
            t2 = self.pos - fwd * (self.radius * 0.7) - right * (self.radius * 0.35)
            pygame.draw.polygon(surface, config.COLOR_SHIP_THRUST, [
                (int(t1.x), int(t1.y)), (int(t_back.x), int(t_back.y)), (int(t2.x), int(t2.y))
            ])

        p_nose = self.pos + fwd * self.radius
        p_left = self.pos - fwd * (self.radius * 0.7) - right * (self.radius * 0.7)
        p_center = self.pos - fwd * (self.radius * 0.3)
        p_right = self.pos - fwd * (self.radius * 0.7) + right * (self.radius * 0.7)

        pts = [(int(p.x), int(p.y)) for p in [p_nose, p_right, p_center, p_left]]

        if self.invuln_timer > 0 and int(self.invuln_timer * 20) % 2 == 0:
            pygame.draw.circle(surface, (100, 200, 255), (int(self.pos.x), int(self.pos.y)), int(self.radius + 6), 2)
            pygame.draw.polygon(surface, (255, 255, 255), pts)
        else:
            pygame.draw.polygon(surface, config.COLOR_SHIP, pts)
            pygame.draw.polygon(surface, (255, 255, 255), pts, 2)
            cockpit = self.pos + fwd * (self.radius * 0.2)
            pygame.draw.circle(surface, (255, 255, 255), (int(cockpit.x), int(cockpit.y)), 3)


class ArenaGame:
    """Full Game Simulation Environment managing state, entities, and rendering."""

    def __init__(self, width=config.SCREEN_WIDTH, height=config.SCREEN_HEIGHT, control_style=1, render_mode=None):
        self.width = width
        self.height = height
        self.control_style = control_style
        self.render_mode = render_mode

        self.screen = None
        self.clock = None
        self.font = None
        self.hud_font = None

        center_y = config.HUD_HEIGHT + (self.height - config.HUD_HEIGHT) / 2
        self.ship = PlayerShip(self.width / 2, center_y, self.control_style)
        self.bullets = []
        self.enemies = []
        self.spawners = []
        self.particles = []

        self.phase = 1
        self.step_count = 0
        self.score = 0
        self.enemies_killed = 0
        self.spawners_destroyed = 0
        self.shots_fired = 0
        self.shots_hit = 0

        self.reset()

    def reset(self, control_style=None):
        if control_style is not None:
            self.control_style = control_style

        center_y = config.HUD_HEIGHT + (self.height - config.HUD_HEIGHT) / 2
        self.ship.reset(self.width / 2, center_y, self.control_style)
        self.bullets.clear()
        self.enemies.clear()
        self.spawners.clear()
        self.particles.clear()

        self.phase = 1
        self.step_count = 0
        self.score = 0
        self.enemies_killed = 0
        self.spawners_destroyed = 0
        self.shots_fired = 0
        self.shots_hit = 0

        self._spawn_phase_spawners(self.phase)

    def _spawn_phase_spawners(self, phase_num):
        self.spawners.clear()
        p_cfg = config.PHASE_CONFIGS.get(phase_num, config.PHASE_CONFIGS[config.MAX_PHASE])
        num_spawners = p_cfg["spawners"]
        interval = p_cfg["spawn_interval"]
        speed = config.ENEMY_BASE_SPEED * p_cfg["enemy_speed_mult"]

        cx = self.width / 2
        cy = config.HUD_HEIGHT + (self.height - config.HUD_HEIGHT) / 2
        radius = min(self.width, self.height - config.HUD_HEIGHT) * 0.36

        for i in range(num_spawners):
            angle = (i * (2 * math.pi / num_spawners)) + (math.pi / 4)
            sx = cx + math.cos(angle) * radius
            sy = cy + math.sin(angle) * radius
            # Ensure strictly within playable bounds below HUD
            sx = max(60, min(self.width - 60, sx))
            sy = max(config.HUD_HEIGHT + 45, min(self.height - 60, sy))
            self.spawners.append(Spawner(sx, sy, spawn_interval=interval, enemy_speed=speed))

    def _create_explosion(self, x, y, color, count=16, speed=160.0):
        for _ in range(count):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(40.0, speed)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd
            rad = random.uniform(2.0, 5.0)
            life = random.uniform(0.3, 0.6)
            self.particles.append(Particle(x, y, vx, vy, color, rad, life))

    def step(self, action_idx, dt=config.SIMULATION_DT):
        self.step_count += 1
        metrics = {
            "enemies_killed": 0,
            "spawners_destroyed": 0,
            "phase_advanced": False,
            "damage_taken": 0.0,
            "player_died": False,
            "bullet_hit": False,
            "bullet_fired": False,
            "wall_hit": False,
            "aim_alignment": 0.0,
            "nearest_enemy_dist": float("inf"),
            "nearest_spawner_dist": float("inf"),
        }

        # 1. Apply Player Action
        fired = self.ship.apply_action(action_idx, dt)
        if fired:
            self.shots_fired += 1
            metrics["bullet_fired"] = True
            nose = self.ship.pos + self.ship.heading_vector * (self.ship.radius + 2)
            self.bullets.append(Bullet(nose.x, nose.y, self.ship.heading_vector))
            self._create_explosion(nose.x, nose.y, config.COLOR_BULLET, count=4, speed=60.0)

        # 2. Update Ship Physics
        wall_hit = self.ship.update(dt, self.width, self.height)
        metrics["wall_hit"] = wall_hit

        # 3. Update Bullets
        for b in self.bullets:
            b.update(dt, self.width, self.height)
        self.bullets = [b for b in self.bullets if b.is_alive]

        # 4. Update Spawners & Periodic Spawning
        for s in self.spawners:
            spawned = s.update(dt, len(self.enemies))
            if spawned:
                self.enemies.append(spawned)
                self._create_explosion(spawned.pos.x, spawned.pos.y, config.COLOR_SPAWNER, count=6, speed=50.0)

        # 5. Update Enemies
        for e in self.enemies:
            e.update(dt, self.ship.pos, self.width, self.height)

        # 6. Projectile Collisions (Bullets -> Enemies & Spawners)
        for b in self.bullets:
            if not b.is_alive:
                continue

            for e in self.enemies:
                if not e.is_alive:
                    continue
                if (b.pos - e.pos).length_squared() < (b.radius + e.radius) ** 2:
                    b.is_alive = False
                    metrics["bullet_hit"] = True
                    self.shots_hit += 1
                    killed = e.take_damage(b.damage)
                    self._create_explosion(e.pos.x, e.pos.y, config.COLOR_ENEMY, count=8, speed=100.0)
                    if killed:
                        metrics["enemies_killed"] += 1
                        self.enemies_killed += 1
                        self.score += 100
                        self._create_explosion(e.pos.x, e.pos.y, (255, 200, 50), count=20, speed=200.0)
                    break

            if not b.is_alive:
                continue

            for s in self.spawners:
                if not s.is_alive:
                    continue
                if (b.pos - s.pos).length_squared() < (b.radius + s.radius) ** 2:
                    b.is_alive = False
                    metrics["bullet_hit"] = True
                    self.shots_hit += 1
                    destroyed = s.take_damage(b.damage)
                    self._create_explosion(s.pos.x, s.pos.y, config.COLOR_SPAWNER, count=10, speed=120.0)
                    if destroyed:
                        metrics["spawners_destroyed"] += 1
                        self.spawners_destroyed += 1
                        self.score += 500
                        self._create_explosion(s.pos.x, s.pos.y, (220, 100, 255), count=35, speed=250.0)
                    break

        self.enemies = [e for e in self.enemies if e.is_alive]
        self.spawners = [s for s in self.spawners if s.is_alive]

        # 7. Enemy -> Player Collisions: Enemy explodes & disappears upon hitting player
        for e in self.enemies:
            if not e.is_alive:
                continue
            delta = e.pos - self.ship.pos
            dist = delta.length()
            min_dist = e.radius + self.ship.radius
            if dist < min_dist:
                # Deal damage to player
                damaged = self.ship.take_damage(e.damage)
                if damaged:
                    metrics["damage_taken"] += e.damage
                    self._create_explosion(self.ship.pos.x, self.ship.pos.y, config.COLOR_HEALTH_DAMAGE, count=14, speed=160.0)
                    if not self.ship.is_alive:
                        metrics["player_died"] = True
                        self._create_explosion(self.ship.pos.x, self.ship.pos.y, (255, 50, 50), count=40, speed=280.0)

                # Enemy is destroyed on impact and triggers explosion
                e.is_alive = False
                self._create_explosion(e.pos.x, e.pos.y, config.COLOR_ENEMY, count=16, speed=150.0)

        # Remove destroyed enemies
        self.enemies = [e for e in self.enemies if e.is_alive]

        # 8. Phase Progression System
        if len(self.spawners) == 0:
            metrics["phase_advanced"] = True
            self.phase += 1
            self.score += 1000
            for e in self.enemies:
                self._create_explosion(e.pos.x, e.pos.y, config.COLOR_ENEMY, count=10, speed=120.0)
            self.enemies.clear()
            self._spawn_phase_spawners(self.phase)

        # 9. Update Visual Particles
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.is_alive]

        # 10. Compute Nearest Distances and Aim Alignment
        ship_fwd = self.ship.heading_vector

        # Nearest Enemy
        if len(self.enemies) > 0:
            nearest_enemy = min(self.enemies, key=lambda e: (e.pos - self.ship.pos).length_squared())
            metrics["nearest_enemy_dist"] = (nearest_enemy.pos - self.ship.pos).length()
            to_e = (nearest_enemy.pos - self.ship.pos).normalize()
            metrics["aim_alignment"] = max(metrics["aim_alignment"], ship_fwd.dot(to_e))

        # Nearest Spawner
        if len(self.spawners) > 0:
            nearest_spawner = min(self.spawners, key=lambda s: (s.pos - self.ship.pos).length_squared())
            metrics["nearest_spawner_dist"] = (nearest_spawner.pos - self.ship.pos).length()
            to_s = (nearest_spawner.pos - self.ship.pos).normalize()
            metrics["aim_alignment"] = max(metrics["aim_alignment"], ship_fwd.dot(to_s))

        return metrics

    def render(self, flip=True):
        """Visually renders the animated game scene to the Pygame screen."""
        if self.screen is None:
            if not pygame.get_init():
                pygame.init()
            if not pygame.display.get_init():
                pygame.display.init()
            if not pygame.font.get_init():
                pygame.font.init()
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption(f"Pygame Action Arena - Control Style {self.control_style}")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont("Consolas", 14, bold=True)
            self.hud_font = pygame.font.SysFont("Consolas", 18, bold=True)

        # 1. Background Grid & Sci-Fi Glow (Strictly below HUD)
        self.screen.fill(config.COLOR_BG)
        grid_size = 40
        for x in range(0, self.width, grid_size):
            pygame.draw.line(self.screen, config.COLOR_GRID, (x, config.HUD_HEIGHT), (x, self.height), 1)
        for y in range(config.HUD_HEIGHT, self.height, grid_size):
            pygame.draw.line(self.screen, config.COLOR_GRID, (0, y), (self.width, y), 1)

        # Arena Outer Border (Around playable area)
        pygame.draw.rect(self.screen, config.COLOR_BORDER, (0, config.HUD_HEIGHT, self.width, self.height - config.HUD_HEIGHT), 2)

        # 2. Draw Entities
        for s in self.spawners:
            s.draw(self.screen)

        for e in self.enemies:
            e.draw(self.screen)

        for b in self.bullets:
            b.draw(self.screen)

        for p in self.particles:
            p.draw(self.screen)

        self.ship.draw(self.screen)

        # 3. Rich HUD Display (Rendered firmly on top)
        self._render_hud()

        if flip:
            pygame.display.flip()
            if self.clock:
                self.clock.tick(config.FPS)

    def _render_hud(self):
        """Draws health bar, phase badges, score, settings button and simulation statistics."""
        hud_h = config.HUD_HEIGHT
        hud_surf = pygame.Surface((self.width, hud_h), pygame.SRCALPHA)
        hud_surf.fill(config.COLOR_HUD_BG)
        self.screen.blit(hud_surf, (0, 0))
        pygame.draw.line(self.screen, config.COLOR_BORDER, (0, hud_h), (self.width, hud_h), 2)

        # Player Health Bar (Enlarged & High-Visibility: 180x24)
        bx, by = 14, 10
        bw, bh = 180, 24
        hp_pct = max(0.0, min(1.0, self.ship.health / self.ship.max_health))

        # Metallic track background
        pygame.draw.rect(self.screen, (22, 28, 42), (bx, by, bw, bh), border_radius=6)

        # Dynamic health fill
        fill_w = int(bw * hp_pct)
        if fill_w > 0:
            if hp_pct > 0.50:
                fill_color = (0, 230, 130)       # Vibrant Emerald Green
            elif hp_pct > 0.25:
                fill_color = (255, 195, 45)      # Warning Amber
            else:
                fill_color = (255, 50, 75)       # Critical Neon Crimson

            if fill_w >= bw - 3:
                pygame.draw.rect(self.screen, fill_color, (bx, by, fill_w, bh), border_radius=6)
            else:
                pygame.draw.rect(self.screen, fill_color, (bx, by, fill_w, bh), border_top_left_radius=6, border_bottom_left_radius=6)

            # Glass highlight sheen on upper half
            sheen = pygame.Surface((fill_w, bh // 2), pygame.SRCALPHA)
            sheen.fill((255, 255, 255, 45))
            self.screen.blit(sheen, (bx, by))

        # Outer border
        bdr_color = (0, 230, 180) if self.ship.invuln_timer > 0 else (70, 110, 160)
        pygame.draw.rect(self.screen, bdr_color, (bx, by, bw, bh), width=2, border_radius=6)

        # Centered bold health text with shadow for high contrast readability
        hp_str = f"HP  {int(self.ship.health)} / {int(self.ship.max_health)}"
        shadow_txt = self.font.render(hp_str, True, (10, 15, 25))
        hp_txt = self.font.render(hp_str, True, (255, 255, 255))
        tx = bx + (bw - hp_txt.get_width()) // 2
        ty = by + (bh - hp_txt.get_height()) // 2
        self.screen.blit(shadow_txt, (tx + 1, ty + 1))
        self.screen.blit(hp_txt, (tx, ty))

        # Phase Badge
        phase_txt = self.hud_font.render(f"PHASE {self.phase}", True, (255, 215, 0))
        self.screen.blit(phase_txt, (210, 11))

        # Spawners & Enemies Counters
        spawners_txt = self.font.render(f"Spawners: {len(self.spawners)}", True, config.COLOR_SPAWNER_CORE)
        enemies_txt = self.font.render(f"Enemies: {len(self.enemies)}", True, config.COLOR_ENEMY)
        self.screen.blit(spawners_txt, (312, 13))
        self.screen.blit(enemies_txt, (422, 13))

        # Score & Style Info
        score_txt = self.font.render(f"Score: {self.score}", True, config.COLOR_TEXT)
        style_txt = self.font.render(f"Style: {self.control_style}", True, (150, 200, 255))
        self.screen.blit(score_txt, (524, 13))
        self.screen.blit(style_txt, (636, 13))

        # Settings Gear Icon Button (Top Right: 46x30)
        gear_rect = pygame.Rect(self.width - 56, 7, 46, 30)
        mouse_pos = pygame.mouse.get_pos()
        is_hover = gear_rect.collidepoint(mouse_pos)

        bg_col = (38, 64, 105) if is_hover else (24, 36, 56)
        bdr_col = (0, 255, 204) if is_hover else (0, 190, 160)
        pygame.draw.rect(self.screen, bg_col, gear_rect, border_radius=6)
        pygame.draw.rect(self.screen, bdr_col, gear_rect, width=2, border_radius=6)

        # High-visibility vector cogwheel/gear icon
        cx = gear_rect.centerx
        cy = gear_rect.centery
        radius = 8
        gear_col = (255, 255, 255) if is_hover else (0, 255, 204)
        for i in range(8):
            ang = i * (math.pi / 4.0)
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            x1 = cx + cos_a * (radius - 2)
            y1 = cy + sin_a * (radius - 2)
            x2 = cx + cos_a * (radius + 4)
            y2 = cy + sin_a * (radius + 4)
            pygame.draw.line(self.screen, gear_col, (int(x1), int(y1)), (int(x2), int(y2)), 3)
        pygame.draw.circle(self.screen, gear_col, (int(cx), int(cy)), int(radius), 2)
        pygame.draw.circle(self.screen, (15, 20, 32), (int(cx), int(cy)), 3, 0)
        pygame.draw.circle(self.screen, gear_col, (int(cx), int(cy)), 3, 1)
