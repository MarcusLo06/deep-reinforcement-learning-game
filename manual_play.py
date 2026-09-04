"""
Interactive manual play script for Assignment 3 Part 2.
Allows testing both Control Style 1 and Control Style 2 with keyboard controls in real time.
Features in-game Pause / Settings modal, restart, controls guide, and exit confirmation warning dialog.
"""

import os
import sys
import argparse
import pygame

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from arena_env.arena_gym_env import ArenaGymEnv
from arena_env import config
from in_game_menu import InGameMenu


def run_manual_play(style=1, return_to_menu=False):
    print("==================================================")
    print("        ARENA MANUAL PLAY CONTROLS               ")
    print("==================================================")
    print("General Controls:")
    print("  ESC / P   : Pause / Open Settings Menu")
    print("  R         : Restart / Reset Episode")
    print("  1 / 2     : Switch to Control Style 1 or 2")
    print("\nControl Style 1 (Rotation & Thrust):")
    print("  W / UP    : Thrust Forward")
    print("  A / LEFT  : Rotate Left")
    print("  D / RIGHT : Rotate Right")
    print("  SPACE     : Shoot Laser")
    print("\nControl Style 2 (Direct Movement):")
    print("  W / UP    : Move Up")
    print("  S / DOWN  : Move Down")
    print("  A / LEFT  : Move Left")
    print("  D / RIGHT : Move Right")
    print("  SPACE     : Shoot Laser")
    print("==================================================")

    current_style = style
    env = ArenaGymEnv(control_style=current_style, render_mode="human")
    obs, info = env.reset()

    in_game_menu = InGameMenu(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
    is_paused = False

    running = True
    clock = pygame.time.Clock()
    total_reward = 0.0

    while running:
        dt = clock.tick(config.FPS) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        # Check window and menu events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if is_paused:
                action = in_game_menu.handle_event(event, mouse_pos)
                if action == "RESUME":
                    is_paused = False
                elif action == "RESTART":
                    obs, info = env.reset()
                    total_reward = 0.0
                    is_paused = False
                    print("Game restarted from Settings Menu!")
                elif action == "EXIT_CONFIRMED":
                    running = False
                    break
            else:
                # Click gear icon or press ESC/P to pause
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if in_game_menu.gear_rect.collidepoint(mouse_pos):
                        is_paused = True
                        in_game_menu.reset_state()

                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_p):
                        is_paused = True
                        in_game_menu.reset_state()
                    elif event.key == pygame.K_r:
                        obs, info = env.reset()
                        total_reward = 0.0
                        print("Game reset!")
                    elif event.key == pygame.K_1:
                        current_style = 1
                        env.close()
                        env = ArenaGymEnv(control_style=1, render_mode="human")
                        obs, info = env.reset()
                        total_reward = 0.0
                        print("Switched to Control Style 1 (Rotation + Thrust)")
                    elif event.key == pygame.K_2:
                        current_style = 2
                        env.close()
                        env = ArenaGymEnv(control_style=2, render_mode="human")
                        obs, info = env.reset()
                        total_reward = 0.0
                        print("Switched to Control Style 2 (Direct Movement)")

        if not running:
            break

        if is_paused:
            # Render game scene in background and draw modal overlay on top
            env.render(flip=False)
            in_game_menu.update(mouse_pos, dt)
            in_game_menu.draw_modal(env.game.screen, mouse_pos)
            pygame.display.flip()
            continue

        # Normal Gameplay: determine action from currently held keys
        keys = pygame.key.get_pressed()
        action = 0  # Default NOOP

        if current_style == 1:
            # Actions: 0: Noop, 1: Thrust, 2: Rotate Left, 3: Rotate Right, 4: Shoot
            if keys[pygame.K_SPACE]:
                action = 4
            elif keys[pygame.K_w] or keys[pygame.K_UP]:
                action = 1
            elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
                action = 2
            elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                action = 3

        elif current_style == 2:
            # Actions: 0: Noop, 1: Up, 2: Down, 3: Left, 4: Right, 5: Shoot
            if keys[pygame.K_SPACE]:
                action = 5
            elif keys[pygame.K_w] or keys[pygame.K_UP]:
                action = 1
            elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
                action = 2
            elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
                action = 3
            elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                action = 4

        # Step environment
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward

        if terminated or truncated:
            reason = "PLAYER DESTROYED" if terminated else "TIME LIMIT REACHED"
            print(f"[{reason}] Final Score: {info['score']} | Phase Reached: {info['phase']} | Total Reward: {total_reward:.2f}")
            obs, info = env.reset()
            total_reward = 0.0

    env.close()
    if not return_to_menu:
        pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manual interactive play for Pygame Arena.")
    parser.add_argument("--style", type=int, default=1, choices=[1, 2], help="Control Style (1: Rotation+Thrust, 2: Direct Movement)")
    args = parser.parse_args()
    run_manual_play(args.style)
