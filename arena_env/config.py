"""
Configuration parameters for Assignment 3 Part 2 Deep RL Pygame Arena.
Contains game physics, entity statistics, phase progression rules, and RL reward weights.
"""

# Arena & Display Settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
HUD_HEIGHT = 44                   # Height of top statistic bar; play area is y in [HUD_HEIGHT, SCREEN_HEIGHT]
FPS = 60
SIMULATION_DT = 1.0 / FPS
MAX_EPISODE_STEPS = 1500          # Max steps before episode truncation

# Colors (Sleek Dark Sci-Fi Palette)
COLOR_BG = (10, 14, 23)
COLOR_GRID = (20, 28, 44)
COLOR_BORDER = (40, 60, 90)
COLOR_SHIP = (0, 255, 204)        # Neon Cyan
COLOR_SHIP_THRUST = (255, 180, 50)
COLOR_BULLET = (255, 230, 80)     # Bright Yellow
COLOR_ENEMY = (255, 60, 90)       # Neon Crimson
COLOR_SPAWNER = (180, 70, 255)    # Neon Purple
COLOR_SPAWNER_CORE = (230, 160, 255)
COLOR_HEALTH_BG = (40, 40, 50)
COLOR_HEALTH_FILL = (0, 230, 120)
COLOR_HEALTH_DAMAGE = (255, 50, 50)
COLOR_TEXT = (220, 230, 245)
COLOR_HUD_BG = (15, 20, 32, 220)

# Ship Parameters
SHIP_RADIUS = 16.0
SHIP_MAX_SPEED = 280.0
SHIP_THRUST = 420.0
SHIP_ROT_SPEED = 240.0             # Degrees per second for Control Style 1
SHIP_LINEAR_DRAG = 0.96            # Drag multiplier per frame
SHIP_DIRECT_SPEED = 240.0          # Speed for Control Style 2 (Direct Movement)
SHIP_MAX_HEALTH = 100.0
SHIP_INVULN_TIME = 0.45            # Seconds of invulnerability after being hit

# Weapon Parameters
BULLET_SPEED = 520.0
BULLET_LIFETIME = 1.1              # Seconds
BULLET_COOLDOWN = 0.20             # Minimum seconds between shots
BULLET_DAMAGE = 25.0
BULLET_RADIUS = 4.0

# Enemy Parameters
ENEMY_RADIUS = 12.0
ENEMY_BASE_SPEED = 110.0
ENEMY_MAX_HEALTH = 25.0            # 1 shot kill with 25 damage bullet
ENEMY_DAMAGE = 15.0
ENEMY_ATTACK_COOLDOWN = 0.6        # Seconds between melee hits on player

# Spawner Parameters
SPAWNER_RADIUS = 22.0
SPAWNER_MAX_HEALTH = 100.0         # 4 shots to destroy
SPAWNER_BASE_INTERVAL = 3.5        # Seconds per spawn in Phase 1
SPAWNER_MIN_INTERVAL = 1.2         # Fastest spawn interval in late phases
MAX_ENEMIES_PER_SPAWNER = 4        # Cap per spawner to prevent overwhelming

# Phase System Settings
MAX_PHASE = 5
PHASE_CONFIGS = {
    1: {"spawners": 2, "spawn_interval": 3.8, "enemy_speed_mult": 1.0},
    2: {"spawners": 3, "spawn_interval": 3.2, "enemy_speed_mult": 1.08},
    3: {"spawners": 3, "spawn_interval": 2.6, "enemy_speed_mult": 1.15},
    4: {"spawners": 4, "spawn_interval": 2.2, "enemy_speed_mult": 1.22},
    5: {"spawners": 4, "spawn_interval": 1.8, "enemy_speed_mult": 1.30},
}

# Control Style Definitions
CONTROL_STYLE_1_ACTIONS = {
    0: "NOOP",
    1: "THRUST",
    2: "ROTATE_LEFT",
    3: "ROTATE_RIGHT",
    4: "SHOOT",
}

CONTROL_STYLE_2_ACTIONS = {
    0: "NOOP",
    1: "MOVE_UP",
    2: "MOVE_DOWN",
    3: "MOVE_LEFT",
    4: "MOVE_RIGHT",
    5: "SHOOT",
}

# Reward & Penalty Structure (Optimized for active intentional combat & kiting)
REWARD_KILL_ENEMY = 15.0
REWARD_KILL_SPAWNER = 65.0
REWARD_CLEAR_PHASE = 130.0
REWARD_HIT_TARGET = 4.0
PENALTY_DAMAGE_TAKEN = -8.0
PENALTY_DEATH = -100.0
PENALTY_TIME_STEP = -0.005         # Gentle nudge to discourage stalling
PENALTY_WALL_COLLISION = -0.15     # Discourage hugging/trapping against boundaries & HUD
REWARD_AIM_ALIGNMENT = 0.12        # Stronger reward for shooting when aimed at enemy/spawner
PENALTY_HAZARD_PROXIMITY = -0.04   # Penalty when enemy is dangerously close (< 60px)
