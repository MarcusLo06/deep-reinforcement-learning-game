"""
Standard Gymnasium Environment wrapper for the Deep RL Action Arena.
Adheres strictly to Gymnasium API standards (reset, step, observation/action spaces).
Features 21-dimensional signed observation vector and potential-based guidance rewards.
"""

import math
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from .arena_game import ArenaGame
from . import config


class ArenaGymEnv(gym.Env):
    """
    Custom Gymnasium Environment for the continuous sci-fi action arena.
    Supports dual action representations (Control Style 1 vs Control Style 2).
    """

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": config.FPS}

    def __init__(self, control_style=1, render_mode=None, max_steps=config.MAX_EPISODE_STEPS):
        super().__init__()
        self.control_style = control_style
        self.render_mode = render_mode
        self.max_steps = max_steps
        self.current_step = 0
        self.prev_spawner_dist = 1.0

        self.game = ArenaGame(
            width=config.SCREEN_WIDTH,
            height=config.SCREEN_HEIGHT,
            control_style=self.control_style,
            render_mode=self.render_mode,
        )

        # Action Space
        if self.control_style == 1:
            # 5 discrete actions: 0:Noop, 1:Thrust, 2:RotLeft, 3:RotRight, 4:Shoot
            self.action_space = spaces.Discrete(5)
        elif self.control_style == 2:
            # 6 discrete actions: 0:Noop, 1:Up, 2:Down, 3:Left, 4:Right, 5:Shoot
            self.action_space = spaces.Discrete(6)
        else:
            raise ValueError(f"Invalid control style: {self.control_style}. Must be 1 or 2.")

        # Observation Space: 21-dimensional continuous feature vector
        # All numeric values normalized to [-1.0, 1.0] or [0.0, 1.0]
        # Includes signed angle differences (cos & sin) for disambiguated left/right turning
        self.observation_space = spaces.Box(
            low=np.array([
                0.0, 0.0, -1.0, -1.0, -1.0, -1.0,         # Player pos, vel, orientation cos/sin
                -1.0, -1.0, 0.0, -1.0, -1.0,              # Nearest enemy: dx, dy, dist, aim_cos, aim_sin
                -1.0, -1.0, 0.0, -1.0, -1.0,              # Nearest spawner: dx, dy, dist, aim_cos, aim_sin
                0.0, 0.0, 0.0, 0.0, 0.0                   # Health, phase, weapon cooldown, enemy/spawner ratios
            ], dtype=np.float32),
            high=np.array([
                1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                1.0, 1.0, 1.0, 1.0, 1.0,
                1.0, 1.0, 1.0, 1.0, 1.0,
                1.0, 1.0, 1.0, 1.0, 1.0
            ], dtype=np.float32),
            dtype=np.float32
        )

    def _get_nearest_spawner_dist_norm(self):
        ship = self.game.ship
        w, h = self.game.width, self.game.height
        play_h = h - config.HUD_HEIGHT
        diag = math.hypot(w, play_h)
        if len(self.game.spawners) > 0:
            nearest_s = min(self.game.spawners, key=lambda s: (s.pos - ship.pos).length_squared())
            return (nearest_s.pos - ship.pos).length() / diag
        return 1.0

    def _get_observation(self):
        ship = self.game.ship
        w, h = self.game.width, self.game.height
        play_h = h - config.HUD_HEIGHT
        diag = math.hypot(w, play_h)

        # 1. Player Features
        sx = np.clip(ship.pos.x / w, 0.0, 1.0)
        sy = np.clip((ship.pos.y - config.HUD_HEIGHT) / play_h, 0.0, 1.0)
        svx = np.clip(ship.vel.x / config.SHIP_MAX_SPEED, -1.0, 1.0)
        svy = np.clip(ship.vel.y / config.SHIP_MAX_SPEED, -1.0, 1.0)
        fwd = ship.heading_vector
        cos_ang = float(fwd.x)
        sin_ang = float(fwd.y)

        # 2. Nearest Enemy Features (Includes signed sin & cos for precise left/right turning)
        edx, edy, edist, e_align_cos, e_align_sin = 0.0, 0.0, 1.0, 0.0, 0.0
        if len(self.game.enemies) > 0:
            nearest_e = min(self.game.enemies, key=lambda e: (e.pos - ship.pos).length_squared())
            delta_e = nearest_e.pos - ship.pos
            d_len = delta_e.length()
            edx = float(delta_e.x / w)
            edy = float(delta_e.y / play_h)
            edist = float(min(1.0, d_len / diag))
            if d_len > 0.001:
                e_dir = delta_e / d_len
                e_align_cos = float(fwd.dot(e_dir))
                # 2D cross product: >0 means target is to the RIGHT, <0 means to the LEFT
                e_align_sin = float(fwd.x * e_dir.y - fwd.y * e_dir.x)

        # 3. Nearest Spawner Features (Includes signed sin & cos for directional navigation)
        sdx, sdy, sdist, s_align_cos, s_align_sin = 0.0, 0.0, 1.0, 0.0, 0.0
        if len(self.game.spawners) > 0:
            nearest_s = min(self.game.spawners, key=lambda s: (s.pos - ship.pos).length_squared())
            delta_s = nearest_s.pos - ship.pos
            s_len = delta_s.length()
            sdx = float(delta_s.x / w)
            sdy = float(delta_s.y / play_h)
            sdist = float(min(1.0, s_len / diag))
            if s_len > 0.001:
                s_dir = delta_s / s_len
                s_align_cos = float(fwd.dot(s_dir))
                # 2D cross product: >0 means target is to the RIGHT, <0 means to the LEFT
                s_align_sin = float(fwd.x * s_dir.y - fwd.y * s_dir.x)

        # 4. Status Features
        health_ratio = np.clip(ship.health / ship.max_health, 0.0, 1.0)
        phase_ratio = np.clip(self.game.phase / config.MAX_PHASE, 0.0, 1.0)
        weapon_ready = 1.0 if ship.shoot_cooldown <= 0 else np.clip(1.0 - (ship.shoot_cooldown / config.BULLET_COOLDOWN), 0.0, 1.0)
        enemy_ratio = np.clip(len(self.game.enemies) / 20.0, 0.0, 1.0)
        spawner_ratio = np.clip(len(self.game.spawners) / 8.0, 0.0, 1.0)

        obs = np.array([
            sx, sy, svx, svy, cos_ang, sin_ang,
            np.clip(edx, -1.0, 1.0), np.clip(edy, -1.0, 1.0), np.clip(edist, 0.0, 1.0),
            np.clip(e_align_cos, -1.0, 1.0), np.clip(e_align_sin, -1.0, 1.0),
            np.clip(sdx, -1.0, 1.0), np.clip(sdy, -1.0, 1.0), np.clip(sdist, 0.0, 1.0),
            np.clip(s_align_cos, -1.0, 1.0), np.clip(s_align_sin, -1.0, 1.0),
            health_ratio, phase_ratio, weapon_ready, enemy_ratio, spawner_ratio
        ], dtype=np.float32)

        return obs

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.game.reset(self.control_style)
        self.prev_spawner_dist = self._get_nearest_spawner_dist_norm()
        obs = self._get_observation()
        info = {
            "phase": self.game.phase,
            "score": self.game.score,
            "health": self.game.ship.health,
            "enemies_killed": self.game.enemies_killed,
            "spawners_destroyed": self.game.spawners_destroyed,
        }
        return obs, info

    def step(self, action):
        self.current_step += 1
        metrics = self.game.step(int(action))

        # 1. Base Step Cost
        reward = config.PENALTY_TIME_STEP

        # 2. Discrete Event Rewards (Destroying bases & enemies)
        if metrics["spawners_destroyed"] > 0:
            reward += metrics["spawners_destroyed"] * config.REWARD_KILL_SPAWNER

        if metrics["enemies_killed"] > 0:
            reward += metrics["enemies_killed"] * config.REWARD_KILL_ENEMY

        if metrics["phase_advanced"]:
            reward += config.REWARD_CLEAR_PHASE

        if metrics["bullet_hit"]:
            reward += config.REWARD_HIT_TARGET

        # 3. Target Navigation & Potential Guidance
        curr_spawner_dist = self._get_nearest_spawner_dist_norm()
        dist_delta = self.prev_spawner_dist - curr_spawner_dist
        if dist_delta > 0:
            # Reward making forward progress toward the nearest spawner
            reward += 1.8 * dist_delta
        self.prev_spawner_dist = curr_spawner_dist

        # 4. Aim Alignment & Firing Reward
        shoot_action = 4 if self.control_style == 1 else 5
        if int(action) == shoot_action:
            if metrics["bullet_fired"]:
                # Award aim alignment bonus ONLY when a bullet is physically fired
                if metrics["aim_alignment"] > 0.5:
                    reward += config.REWARD_AIM_ALIGNMENT * metrics["aim_alignment"]
                else:
                    reward -= 0.02  # Fired into empty space
            else:
                # Attempted to shoot while on cooldown
                reward -= 0.01

        # 5. Movement Incentive: Penalize standing completely stationary
        if self.game.ship.vel.length() < 20.0:
            reward -= 0.015

        # 6. Safety & Damage Penalties
        if metrics["wall_hit"]:
            reward += config.PENALTY_WALL_COLLISION

        if metrics["nearest_enemy_dist"] < 65.0:
            reward += config.PENALTY_HAZARD_PROXIMITY

        if metrics["damage_taken"] > 0:
            reward += (metrics["damage_taken"] / 15.0) * config.PENALTY_DAMAGE_TAKEN

        if metrics["player_died"]:
            reward += config.PENALTY_DEATH

        terminated = not self.game.ship.is_alive
        truncated = self.current_step >= self.max_steps

        obs = self._get_observation()
        info = {
            "phase": self.game.phase,
            "score": self.game.score,
            "health": self.game.ship.health,
            "enemies_killed": self.game.enemies_killed,
            "spawners_destroyed": self.game.spawners_destroyed,
            "shots_fired": self.game.shots_fired,
            "shots_hit": self.game.shots_hit,
        }

        if self.render_mode == "human":
            self.render()

        return obs, float(reward), bool(terminated), bool(truncated), info

    def render(self, flip=True):
        self.game.render(flip=flip)

    def close(self):
        self.game.screen = None
