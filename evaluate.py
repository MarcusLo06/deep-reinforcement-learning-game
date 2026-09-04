"""
Visual Evaluation & Playback Script for Assignment 3 Part 2.
Loads trained Stable-Baselines3 models (PPO/DQN for Style 1 or 2) and renders
real-time interactive gameplay in the Pygame arena with an informative HUD and
in-game Settings / Pause modal with Exit Confirmation Warning Dialog.
"""

import os
import sys
import time
import math
import argparse
import numpy as np
import pygame
from stable_baselines3 import PPO, DQN

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from arena_env.arena_gym_env import ArenaGymEnv
from arena_env import config
from in_game_menu import InGameMenu


def evaluate(
    args=None,
    model_path=None,
    style=1,
    algo="ppo",
    episodes=5,
    deterministic=False,
    fps=60,
    return_to_menu=False,
):
    if args is not None:
        model_path = getattr(args, "model", model_path)
        style = getattr(args, "style", style)
        algo = getattr(args, "algo", algo)
        episodes = getattr(args, "episodes", episodes)
        deterministic = getattr(args, "deterministic", deterministic)
        fps = getattr(args, "fps", fps)

    if model_path is None:
        model_path = os.path.join(current_dir, "models", f"ppo_control_style_{style}.zip")

    if not os.path.exists(model_path):
        if not model_path.endswith(".zip") and os.path.exists(model_path + ".zip"):
            model_path = model_path + ".zip"
        else:
            print(f"[ERROR] Model file not found at: {model_path}")
            print(f"Please train a model first using `python train.py --style {style}`")
            if return_to_menu:
                return
            sys.exit(1)

    print("==================================================")
    print("           ARENA VISUAL EVALUATION               ")
    print("==================================================")
    print(f"  Model Path    : {model_path}")
    print(f"  Control Style : {style} ({'Rotation+Thrust' if style == 1 else 'Direct Movement'})")
    print(f"  Algorithm     : {algo.upper()}")
    print(f"  Episodes      : {episodes}")
    print(f"  Deterministic : {deterministic}")
    print("--------------------------------------------------")
    print("Playback Controls:")
    print("  ESC / P     : Pause / Open Settings Menu")
    print("  SPACE       : Quick Pause / Resume")
    print("  N           : Step 1 Frame (when paused)")
    print("  UP / DOWN   : Increase / Decrease FPS speed")
    print("  R           : Reset Current Episode")
    print("==================================================")

    # Load Model
    if algo.lower() == "ppo":
        model = PPO.load(model_path)
    elif algo.lower() == "dqn":
        model = DQN.load(model_path)
    else:
        raise ValueError(f"Unsupported algorithm: {algo}")

    # Create Environment
    env = ArenaGymEnv(control_style=style, render_mode=None)
    in_game_menu = InGameMenu(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)

    action_names = (
        config.CONTROL_STYLE_1_ACTIONS if style == 1 else config.CONTROL_STYLE_2_ACTIONS
    )

    episode_rewards = []
    episode_scores = []
    episode_phases = []
    episode_enemies = []
    episode_spawners = []

    paused = False
    step_once = False
    current_fps = fps
    clock = pygame.time.Clock()

    for ep in range(1, episodes + 1):
        obs, info = env.reset()
        ep_reward = 0.0
        step_count = 0
        last_action_idx = 0
        hold_counter = 0
        current_action = 0
        burst_shots = 0

        running_episode = True
        while running_episode:
            dt = 1.0 / current_fps
            mouse_pos = pygame.mouse.get_pos()

            # Handle Pygame window events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    env.close()
                    if not return_to_menu:
                        pygame.quit()
                    return

                if paused:
                    action = in_game_menu.handle_event(event, mouse_pos)
                    if action == "RESUME":
                        paused = False
                    elif action == "RESTART":
                        obs, info = env.reset()
                        ep_reward = 0.0
                        step_count = 0
                        hold_counter = 0
                        current_action = 0
                        burst_shots = 0
                        paused = False
                        print("Evaluation episode restarted from menu.")
                    elif action == "EXIT_CONFIRMED":
                        env.close()
                        if not return_to_menu:
                            pygame.quit()
                        return
                else:
                    # Click gear icon or press ESC / P
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if in_game_menu.gear_rect.collidepoint(mouse_pos):
                            paused = True
                            in_game_menu.reset_state()

                    elif event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_ESCAPE, pygame.K_p):
                            paused = True
                            in_game_menu.reset_state()
                        elif event.key == pygame.K_SPACE:
                            paused = not paused
                            print(f"[{'PAUSED' if paused else 'RESUMED'}]")
                        elif event.key == pygame.K_n and paused:
                            step_once = True
                        elif event.key == pygame.K_UP:
                            current_fps = min(240, current_fps + 15)
                            print(f"Speed: {current_fps} FPS")
                        elif event.key == pygame.K_DOWN:
                            current_fps = max(15, current_fps - 15)
                            print(f"Speed: {current_fps} FPS")
                        elif event.key == pygame.K_r:
                            obs, info = env.reset()
                            ep_reward = 0.0
                            step_count = 0
                            hold_counter = 0
                            current_action = 0
                            burst_shots = 0
                            print("Episode manually restarted.")

            if paused and not step_once:
                # Render paused scene and modal overlay
                env.game.render(flip=False)
                in_game_menu.update(mouse_pos, dt)
                in_game_menu.draw_modal(env.game.screen, mouse_pos)
                pygame.display.flip()
                clock.tick(current_fps)
                continue

            step_once = False

            # Action Persistence & Natural Flight Smoothing
            # Eliminates 60Hz erratic twitching, resulting in smooth, purposeful, human-like flight
            shoot_action = 4 if style == 1 else 5
            if hold_counter <= 0:
                if deterministic:
                    action, _states = model.predict(obs, deterministic=True)
                    if int(action) == shoot_action and env.game.ship.shoot_cooldown > 0:
                        action, _states = model.predict(obs, deterministic=False)
                else:
                    action, _states = model.predict(obs, deterministic=False)

                current_action = int(action)

                if style == 1:
                    # Style 1: Rotation & Thrust tactical alignment
                    if current_action == shoot_action:
                        spawner_align = float(obs[14]) if len(obs) > 14 else 0.0
                        enemy_align = float(obs[9]) if len(obs) > 9 else 0.0
                        max_align = max(spawner_align, enemy_align)

                        if max_align < 0.50 or burst_shots >= 3:
                            burst_shots = 0
                            # obs[15] is signed sin: >0 turn right (3), <0 turn left (2)
                            current_action = 3 if (len(obs) > 15 and obs[15] > 0) else 2
                        else:
                            burst_shots += 1
                    else:
                        burst_shots = 0
                    hold_counter = 4

                else:
                    # Style 2: Direct 4-Way Movement natural tactical navigation
                    ship = env.game.ship
                    w, h = env.game.width, env.game.height
                    hud = config.HUD_HEIGHT

                    # 1. Target Acquisition (closest threatening enemy or nearest spawner)
                    target = None
                    target_kind = 'spawner'
                    if len(env.game.enemies) > 0:
                        nearest_e = min(env.game.enemies, key=lambda e: (e.pos - ship.pos).length_squared())
                        if (nearest_e.pos - ship.pos).length() < 240.0:
                            target = nearest_e
                            target_kind = 'enemy'
                    if target is None and len(env.game.spawners) > 0:
                        nearest_s = min(env.game.spawners, key=lambda s: (s.pos - ship.pos).length_squared())
                        target = nearest_s
                        target_kind = 'spawner'

                    if target is None:
                        # No active entities: execute model action with steady stride
                        hold_counter = 5
                    else:
                        dx = target.pos.x - ship.pos.x
                        dy = target.pos.y - ship.pos.y
                        dist = math.hypot(dx, dy)

                        # 2. Wall Safety Buffer (avoid getting trapped in corners/borders)
                        near_l = ship.pos.x < 55
                        near_r = ship.pos.x > w - 55
                        near_t = ship.pos.y < hud + 45
                        near_b = ship.pos.y > h - 55

                        # 3. Firing Line Alignment Corridors
                        corridor = 30.0 if target_kind == 'spawner' else 22.0
                        h_aligned = abs(dy) <= corridor
                        v_aligned = abs(dx) <= corridor

                        fwd = ship.heading_vector
                        facing_right = (fwd.x > 0.7 and dx > 0)
                        facing_left = (fwd.x < -0.7 and dx < 0)
                        facing_down = (fwd.y > 0.7 and dy > 0)
                        facing_up = (fwd.y < -0.7 and dy < 0)
                        has_clear_shot = (h_aligned and (facing_right or facing_left)) or (v_aligned and (facing_down or facing_up))

                        # 4. Natural Combat & Navigation Arbitration
                        if near_l:
                            current_action = 4; hold_counter = 6
                        elif near_r:
                            current_action = 3; hold_counter = 6
                        elif near_t:
                            current_action = 2; hold_counter = 6
                        elif near_b:
                            current_action = 1; hold_counter = 6
                        elif dist < 65.0 and target_kind == 'enemy':
                            # Tactically kite away from close enemy to prevent melee damage
                            current_action = (3 if dx > 0 else 4) if abs(dx) > abs(dy) else (1 if dy > 0 else 2)
                            hold_counter = 6
                        elif has_clear_shot:
                            # Clear firing corridor: fire in controlled bursts
                            if ship.shoot_cooldown <= 0:
                                current_action = 5 # Shoot!
                                burst_shots += 1
                                hold_counter = 3
                            else:
                                if dist > 260.0:
                                    current_action = (4 if dx > 0 else 3) if h_aligned else (2 if dy > 0 else 1)
                                    hold_counter = 4
                                else:
                                    current_action = 0 # Steady aim while chambering next round
                                    hold_counter = 2
                        elif h_aligned:
                            # Horizontally aligned: commit horizontally (prevents up/down jitter)
                            burst_shots = 0
                            current_action = 4 if dx > 0 else 3
                            hold_counter = 6
                        elif v_aligned:
                            # Vertically aligned: commit vertically (prevents horizontal jitter)
                            burst_shots = 0
                            current_action = 2 if dy > 0 else 1
                            hold_counter = 6
                        else:
                            # Diagonal target: maneuver along the smaller gap first
                            burst_shots = 0
                            if abs(dy) < abs(dx):
                                current_action = 2 if dy > 0 else 1
                            else:
                                current_action = 4 if dx > 0 else 3
                            hold_counter = 6
            else:
                hold_counter -= 1

            last_action_idx = current_action
            obs, reward, terminated, truncated, info = env.step(last_action_idx)
            ep_reward += reward
            step_count += 1

            # Render scene
            env.game.render(flip=False)

            # Custom Evaluation HUD Overlay
            if env.game.screen is not None:
                # Bottom Action HUD
                bot_h = 32
                bot_surf = pygame.Surface((config.SCREEN_WIDTH, bot_h), pygame.SRCALPHA)
                bot_surf.fill((15, 20, 32, 220))
                env.game.screen.blit(bot_surf, (0, config.SCREEN_HEIGHT - bot_h))
                pygame.draw.line(env.game.screen, config.COLOR_BORDER, (0, config.SCREEN_HEIGHT - bot_h), (config.SCREEN_WIDTH, config.SCREEN_HEIGHT - bot_h), 2)

                act_label = action_names.get(last_action_idx, "UNKNOWN")
                action_txt = env.game.font.render(f"Action: [{last_action_idx}] {act_label}", True, (0, 255, 204))
                rew_txt = env.game.font.render(f"Ep Rew: {ep_reward:.1f}", True, (255, 220, 100))
                step_txt = env.game.font.render(f"Step: {step_count}/{config.MAX_EPISODE_STEPS}", True, (180, 200, 230))
                ep_txt = env.game.font.render(f"Ep: {ep}/{episodes} ({current_fps} FPS)", True, (220, 220, 240))

                env.game.screen.blit(action_txt, (16, config.SCREEN_HEIGHT - bot_h + 8))
                env.game.screen.blit(rew_txt, (260, config.SCREEN_HEIGHT - bot_h + 8))
                env.game.screen.blit(step_txt, (450, config.SCREEN_HEIGHT - bot_h + 8))
                env.game.screen.blit(ep_txt, (660, config.SCREEN_HEIGHT - bot_h + 8))

                pygame.display.flip()

            if terminated or truncated:
                running_episode = False
                status = "VICTORY / TIMEOUT" if truncated else "SHIP DESTROYED"
                print(f"Episode {ep:2d}/{episodes} | {status:15s} | Score: {info['score']:5d} | Phase: {info['phase']} | Reward: {ep_reward:7.1f} | Enemies: {info['enemies_killed']:2d} | Spawners: {info['spawners_destroyed']}")

                episode_rewards.append(ep_reward)
                episode_scores.append(info['score'])
                episode_phases.append(info['phase'])
                episode_enemies.append(info['enemies_killed'])
                episode_spawners.append(info['spawners_destroyed'])

            clock.tick(current_fps)

    env.close()
    if not return_to_menu:
        pygame.quit()

    # Print Summary Table
    print("\n==================================================")
    print("            EVALUATION SUMMARY RESULTS            ")
    print("==================================================")
    print(f"  Total Episodes Tested : {episodes}")
    print(f"  Mean Episode Reward   : {np.mean(episode_rewards):.2f} ± {np.std(episode_rewards):.2f}")
    print(f"  Mean Score            : {np.mean(episode_scores):.1f}")
    print(f"  Mean Phase Reached    : {np.mean(episode_phases):.2f} (Max: {np.max(episode_phases)})")
    print(f"  Mean Enemies Killed   : {np.mean(episode_enemies):.2f}")
    print(f"  Mean Spawners Killed  : {np.mean(episode_spawners):.2f}")
    print("==================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visually evaluate trained deep RL models.")
    parser.add_argument("--model", type=str, default=None, help="Path to trained model .zip")
    parser.add_argument("--style", type=int, default=1, choices=[1, 2], help="Control Style (1 or 2)")
    parser.add_argument("--algo", type=str, default="ppo", choices=["ppo", "dqn"], help="Algorithm used")
    parser.add_argument("--episodes", type=int, default=5, help="Number of evaluation episodes")
    parser.add_argument("--deterministic", action="store_true", default=False, help="Use deterministic action selection")
    parser.add_argument("--fps", type=int, default=60, help="Display FPS")

    args = parser.parse_args()
    evaluate(args)
