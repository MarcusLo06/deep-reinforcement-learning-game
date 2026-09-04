"""
Stable-Baselines3 Deep RL Training Pipeline for Assignment 3 Part 2.
Supports PPO and DQN, custom multi-layer architectures, TensorBoard logging,
and custom game metrics tracking (enemies killed, spawners destroyed, phase reached).
"""

import os
import argparse
import numpy as np
import gymnasium as gym
from stable_baselines3 import PPO, DQN
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.monitor import Monitor

from arena_env.arena_gym_env import ArenaGymEnv
from arena_env import config


class ArenaMetricsCallback(BaseCallback):
    """
    Custom Stable-Baselines3 callback that records rich game statistics
    to TensorBoard upon each episode completion.
    """

    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_scores = []
        self.episode_phases = []
        self.episode_enemies = []
        self.episode_spawners = []
        self.episode_accuracies = []

    def _on_step(self) -> bool:
        # Check infos for done signals
        for info in self.locals.get("infos", []):
            if "episode" in info:  # Monitor wrapper adds 'episode' dict
                pass
            if "score" in info and self.locals.get("dones", [False])[0]:
                score = info.get("score", 0)
                phase = info.get("phase", 1)
                enemies = info.get("enemies_killed", 0)
                spawners = info.get("spawners_destroyed", 0)
                shots_fired = info.get("shots_fired", 0)
                shots_hit = info.get("shots_hit", 0)
                acc = (shots_hit / max(1, shots_fired)) * 100.0

                self.episode_scores.append(score)
                self.episode_phases.append(phase)
                self.episode_enemies.append(enemies)
                self.episode_spawners.append(spawners)
                self.episode_accuracies.append(acc)

                # Log scalar to TensorBoard
                self.logger.record("game/episode_score", score)
                self.logger.record("game/phase_reached", phase)
                self.logger.record("game/enemies_killed", enemies)
                self.logger.record("game/spawners_destroyed", spawners)
                self.logger.record("game/accuracy_percent", acc)

        return True


def make_env(control_style=1, seed=0):
    def _init():
        env = ArenaGymEnv(control_style=control_style, render_mode=None)
        env = Monitor(env)
        return env
    return _init


def train(args):
    os.makedirs(args.models_dir, exist_ok=True)
    os.makedirs(args.log_dir, exist_ok=True)

    print("==================================================")
    print(f"       STARTING TRAINING: STYLE {args.style} ({args.algo.upper()})")
    print("==================================================")
    print(f"  Control Style    : {args.style} ({'Rotation+Thrust' if args.style == 1 else 'Direct Movement'})")
    print(f"  Algorithm        : {args.algo.upper()}")
    print(f"  Total Timesteps  : {args.timesteps:,}")
    print(f"  Learning Rate    : {args.lr}")
    print(f"  Network Arch     : {[args.hidden_dim] * args.num_layers}")
    print(f"  TensorBoard Log  : {args.log_dir}")
    print(f"  Models Directory : {args.models_dir}")
    print("==================================================")

    # Create vectorized environment
    env = DummyVecEnv([make_env(control_style=args.style, seed=args.seed)])

    # Setup Network Architecture (MLP with at least one hidden layer, satisfying Rubric J2)
    net_arch = [args.hidden_dim] * args.num_layers
    policy_kwargs = dict(net_arch=net_arch)

    run_name = f"{args.algo}_style{args.style}_lr{args.lr}_arch{args.hidden_dim}x{args.num_layers}"
    tb_log_path = os.path.join(args.log_dir, run_name)

    # Initialize RL Algorithm
    if args.algo.lower() == "ppo":
        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=args.lr,
            n_steps=args.n_steps,
            batch_size=args.batch_size,
            gamma=args.gamma,
            ent_coef=args.ent_coef,
            policy_kwargs=policy_kwargs,
            verbose=1,
            tensorboard_log=tb_log_path,
            seed=args.seed,
        )
    elif args.algo.lower() == "dqn":
        model = DQN(
            "MlpPolicy",
            env,
            learning_rate=args.lr,
            buffer_size=50000,
            learning_starts=2000,
            batch_size=args.batch_size,
            gamma=args.gamma,
            exploration_fraction=0.25,
            exploration_initial_eps=1.0,
            exploration_final_eps=0.05,
            policy_kwargs=policy_kwargs,
            verbose=1,
            tensorboard_log=tb_log_path,
            seed=args.seed,
        )
    else:
        raise ValueError(f"Unsupported algorithm: {args.algo}. Choose 'ppo' or 'dqn'.")

    # Callbacks
    metrics_cb = ArenaMetricsCallback()
    checkpoint_cb = CheckpointCallback(
        save_freq=max(10000, args.timesteps // 5),
        save_path=args.models_dir,
        name_prefix=f"{args.algo}_style{args.style}_ckpt",
    )

    # Begin Training
    model.learn(
        total_timesteps=args.timesteps,
        callback=[metrics_cb, checkpoint_cb],
        progress_bar=True,
    )

    # Save Final Model
    final_model_name = f"{args.algo}_control_style_{args.style}"
    final_save_path = os.path.join(args.models_dir, final_model_name)
    model.save(final_save_path)
    print(f"\n[SUCCESS] Final model saved to: {final_save_path}.zip")

    env.close()
    return final_save_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Deep RL Agent on Pygame Arena.")
    parser.add_argument("--style", type=int, default=1, choices=[1, 2], help="Control Style (1: Rotation+Thrust, 2: Direct)")
    parser.add_argument("--algo", type=str, default="ppo", choices=["ppo", "dqn"], help="RL Algorithm (ppo or dqn)")
    parser.add_argument("--timesteps", type=int, default=120000, help="Total training timesteps")
    parser.add_argument("--lr", type=float, default=3e-4, help="Learning rate")
    parser.add_argument("--gamma", type=float, default=0.99, help="Discount factor")
    parser.add_argument("--n_steps", type=int, default=2048, help="Rollout buffer size for PPO")
    parser.add_argument("--batch_size", type=int, default=64, help="Minibatch size")
    parser.add_argument("--ent_coef", type=float, default=0.01, help="Entropy coefficient for exploration")
    parser.add_argument("--hidden_dim", type=int, default=128, help="Neurons per hidden layer")
    parser.add_argument("--num_layers", type=int, default=2, help="Number of hidden layers")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--models_dir", type=str, default="models", help="Directory to save models")
    parser.add_argument("--log_dir", type=str, default="logs", help="Directory for TensorBoard logs")

    args = parser.parse_args()
    train(args)
