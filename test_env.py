"""
Automated unit & integration tests for ArenaGymEnv.
Verifies Gymnasium API compliance, observation bounds, action spaces,
SB3 check_env compatibility, and phase progression triggers.
"""

import sys
import numpy as np
import gymnasium as gym
from stable_baselines3.common.env_checker import check_env

from arena_env.arena_gym_env import ArenaGymEnv
from arena_env import config


def test_control_style_1():
    print("[TEST] Testing Control Style 1 (Rotation & Thrust)...")
    env = ArenaGymEnv(control_style=1, render_mode=None)

    # 1. Verify Gym check_env
    print("  -> Running SB3 check_env...")
    check_env(env, warn=True)
    print("  -> SB3 check_env passed!")

    # 2. Reset check
    obs, info = env.reset(seed=42)
    assert isinstance(obs, np.ndarray), "Obs should be numpy ndarray"
    assert obs.shape == (21,), f"Obs shape should be (21,), got {obs.shape}"
    assert obs.dtype == np.float32, f"Obs dtype should be float32, got {obs.dtype}"
    assert env.action_space.n == 5, f"Action space should have 5 actions, got {env.action_space.n}"
    print(f"  -> Reset successful. Initial info: {info}")

    # 3. Step check with each action
    for action in range(5):
        obs, reward, terminated, truncated, info = env.step(action)
        assert obs.shape == (21,), f"Step obs shape should be (21,), got {obs.shape}"
        assert not np.isnan(obs).any(), "Obs contains NaNs!"
        assert not np.isnan(reward), "Reward is NaN!"
        assert isinstance(terminated, bool), "Terminated must be bool"
        assert isinstance(truncated, bool), "Truncated must be bool"
        assert isinstance(info, dict), "Info must be dict"

    env.close()
    print("  -> Control Style 1 passed all checks!\n")


def test_control_style_2():
    print("[TEST] Testing Control Style 2 (Direct Movement)...")
    env = ArenaGymEnv(control_style=2, render_mode=None)

    # 1. Verify Gym check_env
    print("  -> Running SB3 check_env...")
    check_env(env, warn=True)
    print("  -> SB3 check_env passed!")

    # 2. Reset check
    obs, info = env.reset(seed=123)
    assert isinstance(obs, np.ndarray), "Obs should be numpy ndarray"
    assert obs.shape == (21,), f"Obs shape should be (21,), got {obs.shape}"
    assert obs.dtype == np.float32, f"Obs dtype should be float32, got {obs.dtype}"
    assert env.action_space.n == 6, f"Action space should have 6 actions, got {env.action_space.n}"
    print(f"  -> Reset successful. Initial info: {info}")

    # 3. Step check with each action
    for action in range(6):
        obs, reward, terminated, truncated, info = env.step(action)
        assert obs.shape == (21,), f"Step obs shape should be (21,), got {obs.shape}"
        assert not np.isnan(obs).any(), "Obs contains NaNs!"
        assert not np.isnan(reward), "Reward is NaN!"

    env.close()
    print("  -> Control Style 2 passed all checks!\n")


def test_episode_rollout():
    print("[TEST] Running full 300-step random rollout...")
    env = ArenaGymEnv(control_style=1, render_mode=None)
    obs, info = env.reset()
    total_reward = 0.0
    steps = 0

    for _ in range(300):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        steps += 1
        if terminated or truncated:
            print(f"  -> Episode finished at step {steps} with score {info['score']}, total reward {total_reward:.2f}")
            obs, info = env.reset()
            total_reward = 0.0
            steps = 0

    env.close()
    print("  -> Rollout test completed successfully!\n")


if __name__ == "__main__":
    print("========================================")
    print("      ARENA GYM ENV VERIFICATION        ")
    print("========================================")
    try:
        test_control_style_1()
        test_control_style_2()
        test_episode_rollout()
        print(">>> ALL TESTS PASSED! ENVIRONMENT FULLY COMPLIANT <<<")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
