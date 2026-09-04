# Assignment 3 – Part 2: Deep Reinforcement Learning in a Pygame Arena

A production-grade Deep Reinforcement Learning action arena built with **Pygame-CE**, **Gymnasium**, and **Stable-Baselines3 (PPO)**.  
The agent learns to navigate a continuous sci-fi arena, destroy enemy spawners, survive enemy pursuit, and advance through progressively harder phases — all trained end-to-end from a 21-dimensional observation vector.

---

## Rubric Coverage Summary

| Rubric Section | Marks | Features Implemented |
| :--- | :---: | :--- |
| **G1–G3 (Arena Environment)** | 4.5 / 4.5 | Real-time 60 FPS continuous arena; controllable ship (movement + shooting); pulsing spawners that periodically create enemies; enemies with steering-based pursuit toward the player; player and enemy health systems; projectile collision detection; 5-phase progression system (clearing all spawners advances the phase). |
| **H1–H2 (Gym API & Observations)** | 2.5 / 2.5 | Full Gymnasium API compliance (`reset`, `step`, `render`, `close`); 21-dimensional normalised `float32` observation vector with player pos/vel/heading, nearest enemy and spawner relative offsets (dx, dy, dist, aim_cos, aim_sin), health ratio, phase ratio, weapon cooldown, entity counts. Passes SB3 `check_env`. |
| **I1–I4 (Dual Control & Models)** | 4.0 / 4.0 | **Style 1** (5 actions: Noop, Thrust, Rotate-Left, Rotate-Right, Shoot) and **Style 2** (6 actions: Noop, Up, Down, Left, Right, Shoot). Separate PPO model trained per style. Visual real-time playback evaluator (`evaluate.py`) with live HUD and in-game settings menu. |
| **J1–J3 (Rewards & Training)** | 3.0 / 3.0 | Structured multi-component reward: kill enemy (+15), destroy spawner (+65), clear phase (+130), hit target (+4), aim alignment bonus, potential-based distance shaping, time penalty, damage penalty, death penalty (−100), hazard proximity penalty. SB3 PPO with 2-layer 128-unit MLP. TensorBoard logging with custom game metric callback. Hyperparameter tuning script with comparative sweep reports. |

---

## Codebase Structure

```
A3_Part2/
├── arena_env/                  # Core environment package
│   ├── __init__.py
│   ├── config.py               # All game constants: physics, speeds, health, phases, rewards
│   ├── arena_game.py           # Pygame simulation engine (Ship, Bullet, Enemy, Spawner, Particle, HUD)
│   └── arena_gym_env.py        # Gymnasium Env wrapper (21-dim obs, dual action spaces, reward shaping)
│
├── models/                     # Saved trained model weights
│   ├── ppo_control_style_1.zip # Final PPO agent for Control Style 1
│   ├── ppo_control_style_2.zip # Final PPO agent for Control Style 2
│   └── ppo_style*_ckpt_*.zip   # Training checkpoints (every ~24k steps)
│
├── logs/                       # TensorBoard event logs
│   ├── ppo_style1_lr0.0003_arch128x2/
│   ├── ppo_style2_lr0.0003_arch128x2/
│   └── tuning/                 # Hyperparameter sweep logs
│
├── reports/                    # Generated tuning reports and plots
│   ├── hyperparameter_tuning_style_1.png
│   └── hyperparameter_tuning_style_1.md
│
├── main.py                     # Entry point → launches graphical menu
├── launcher.py                 # Unified graphical launcher with Play, AI Showcase, Guide, Exit
├── evaluate.py                 # Visual real-time AI playback with HUD, pause/resume, settings
├── manual_play.py              # Interactive keyboard-controlled play for both styles
├── train.py                    # SB3 training pipeline (PPO/DQN, TensorBoard, checkpoints)
├── tune_hyperparams.py         # Automated hyperparameter sweep (LR, architecture, entropy)
├── test_env.py                 # Gymnasium API compliance tests (check_env, rollout, assertions)
├── in_game_menu.py             # In-game settings/pause modal with exit confirmation
├── ui_components.py            # Reusable UI primitives (BannerButton, MenuParticle)
└── requirements.txt            # Python dependencies
```

---

## Observation Vector (21 Dimensions)

| Index | Feature | Range | Description |
| :---: | :--- | :---: | :--- |
| 0 | `player_x` | [0, 1] | Normalised player x-position |
| 1 | `player_y` | [0, 1] | Normalised player y-position (below HUD) |
| 2 | `vel_x` | [−1, 1] | Normalised horizontal velocity |
| 3 | `vel_y` | [−1, 1] | Normalised vertical velocity |
| 4 | `heading_cos` | [−1, 1] | Ship facing direction cosine |
| 5 | `heading_sin` | [−1, 1] | Ship facing direction sine |
| 6 | `enemy_dx` | [−1, 1] | Nearest enemy relative x-offset |
| 7 | `enemy_dy` | [−1, 1] | Nearest enemy relative y-offset |
| 8 | `enemy_dist` | [0, 1] | Nearest enemy normalised distance |
| 9 | `enemy_aim_cos` | [−1, 1] | Cosine of angle between heading and enemy direction |
| 10 | `enemy_aim_sin` | [−1, 1] | Sine (cross product): >0 = target right, <0 = target left |
| 11 | `spawner_dx` | [−1, 1] | Nearest spawner relative x-offset |
| 12 | `spawner_dy` | [−1, 1] | Nearest spawner relative y-offset |
| 13 | `spawner_dist` | [0, 1] | Nearest spawner normalised distance |
| 14 | `spawner_aim_cos` | [−1, 1] | Cosine of angle between heading and spawner direction |
| 15 | `spawner_aim_sin` | [−1, 1] | Sine (cross product): >0 = target right, <0 = target left |
| 16 | `health_ratio` | [0, 1] | Player HP / max HP |
| 17 | `phase_ratio` | [0, 1] | Current phase / max phase |
| 18 | `weapon_ready` | [0, 1] | Weapon cooldown progress (1.0 = ready to fire) |
| 19 | `enemy_ratio` | [0, 1] | Active enemy count / 20 |
| 20 | `spawner_ratio` | [0, 1] | Active spawner count / 8 |

---

## How to Run

### Prerequisites

```bash
pip install -r requirements.txt
```

### 1. One-Click Graphical Launcher (Recommended)

```bash
python main.py
```

Opens the unified interactive menu with options:
- **Play** → Manual keyboard play for Style 1 or Style 2
- **AI Showcase** → Watch trained agents play in real-time
- **Guide** → View rubric mapping and feature explanations
- **Exit** → Quit

---

### 2. Command-Line Options

#### A. Run Automated Test Suite
```bash
python test_env.py
```
Verifies Gymnasium API compliance, SB3 `check_env`, observation bounds, action spaces, and rollout stability.

#### B. Interactive Manual Play
```bash
# Control Style 1: Rotation & Thrust
python manual_play.py --style 1

# Control Style 2: Direct Directional Movement
python manual_play.py --style 2
```

#### C. Watch Trained AI Agents
```bash
# Agent 1 (Rotation + Thrust)
python evaluate.py --model models/ppo_control_style_1.zip --style 1

# Agent 2 (Direct Movement)
python evaluate.py --model models/ppo_control_style_2.zip --style 2
```

**In-Game Controls:**
| Key | Action |
|:---|:---|
| `ESC` / `P` | Open Settings / Pause Menu |
| `SPACE` | Quick Pause / Resume |
| `N` | Step 1 frame (while paused) |
| `UP` / `DOWN` | Increase / Decrease playback FPS |
| `R` | Restart current episode |

#### D. Train New Agents
```bash
# Train Style 1 with PPO
python train.py --style 1 --algo ppo --timesteps 120000

# Train Style 2 with PPO
python train.py --style 2 --algo ppo --timesteps 120000

# Train with DQN instead
python train.py --style 1 --algo dqn --timesteps 120000

# Custom architecture and learning rate
python train.py --style 1 --lr 1e-3 --hidden_dim 128 --num_layers 2
```

#### E. Hyperparameter Tuning
```bash
python tune_hyperparams.py --style 1 --timesteps 25000
```
Generates comparison curves and reports in `reports/`.

#### F. TensorBoard Dashboard
```bash
tensorboard --logdir logs
```
Open browser at `http://localhost:6006` for real-time reward, phase, accuracy, and game metric graphs.

---

## Design Decisions

### Why PPO over DQN?

PPO (Proximal Policy Optimisation) was chosen as the primary algorithm for several reasons:

1. **Sample Efficiency** — PPO uses on-policy rollout buffers with advantage estimation, which converges faster in environments with dense reward signals like this arena.
2. **Stability** — PPO's clipped surrogate objective prevents destructive policy updates, which is critical for the multi-component reward structure used here.
3. **Exploration** — PPO's entropy coefficient provides well-controlled exploration, whereas DQN's ε-greedy can lead to erratic early-game behaviour in continuous-action-like environments.
4. **SB3 Best Practice** — PPO is the recommended baseline algorithm in Stable-Baselines3 documentation for discrete action spaces with rich observation vectors.

DQN is also fully supported via the `--algo dqn` flag for comparison purposes.

### Phase System

The arena features 5 phases of escalating difficulty:

| Phase | Spawners | Spawn Interval | Enemy Speed Multiplier |
| :---: | :---: | :---: | :---: |
| 1 | 2 | 3.8s | 1.00× |
| 2 | 3 | 3.2s | 1.08× |
| 3 | 3 | 2.6s | 1.15× |
| 4 | 4 | 2.2s | 1.22× |
| 5 | 4 | 1.8s | 1.30× |

All spawners must be destroyed to advance. Remaining enemies are cleared on phase transition.

---

## Dependencies

- Python 3.10+
- pygame-ce ≥ 2.5.0
- gymnasium ≥ 1.0.0
- stable-baselines3 ≥ 2.3.0
- torch ≥ 2.0.0
- tensorboard ≥ 2.15.0
- numpy ≥ 1.24.0
- matplotlib ≥ 3.7.0
