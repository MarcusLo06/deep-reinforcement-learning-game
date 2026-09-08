"""
Audio Manager for Assignment 3 Part 2.
Handles sound effects (SFX) and background music (BGM) playback,
dynamic volume scaling (Master, Music, SFX), and persistent settings.
"""

import os
import json
import pygame

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "audio_settings.json")


class AudioManager:
    """
    Central audio controller managing BGM streams and SFX sound pools.
    Safely handles environments without sound hardware or missing files.
    """

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.mixer_initialized = False
        self.sounds = {}
        self.music_loaded = False
        self.is_music_playing = False

        # Volume levels (0.0 to 1.0)
        self.master_volume = 0.8
        self.music_volume = 0.6
        self.sfx_volume = 0.8

        self._load_settings()
        self._init_mixer()
        self._load_audio_files()

    def _init_mixer(self):
        """Safely initializes pygame mixer."""
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.pre_init(44100, -16, 2, 512)
                pygame.mixer.init()
                self.mixer_initialized = True
            except Exception as e:
                print(f"[AudioManager] Warning: Mixer initialization failed ({e}). Audio disabled.")
                self.mixer_initialized = False
        else:
            self.mixer_initialized = True

    def _load_settings(self):
        """Loads volume preferences from audio_settings.json."""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.master_volume = max(0.0, min(1.0, float(data.get("master_volume", 0.8))))
                    self.music_volume = max(0.0, min(1.0, float(data.get("music_volume", 0.6))))
                    self.sfx_volume = max(0.0, min(1.0, float(data.get("sfx_volume", 0.8))))
            except Exception as e:
                print(f"[AudioManager] Could not load audio settings: {e}")

    def save_settings(self):
        """Saves current volume preferences to audio_settings.json."""
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "master_volume": round(self.master_volume, 2),
                    "music_volume": round(self.music_volume, 2),
                    "sfx_volume": round(self.sfx_volume, 2)
                }, f, indent=2)
        except Exception as e:
            print(f"[AudioManager] Could not save audio settings: {e}")

    def _load_audio_files(self):
        """Loads BGM and SFX files if mixer is active."""
        if not self.mixer_initialized:
            return

        # 1. Background Music
        bgm_path = os.path.join(BASE_DIR, "music", "background_music.mp3")
        if os.path.exists(bgm_path):
            try:
                pygame.mixer.music.load(bgm_path)
                self.music_loaded = True
                self._apply_music_volume()
            except Exception as e:
                print(f"[AudioManager] Failed loading BGM: {e}")
                self.music_loaded = False
        else:
            print(f"[AudioManager] Music file not found at {bgm_path}")

        # 2. Sound Effects
        sfx_map = {
            "shoot": "shoot.mp3",
            "enemy_explosion": "enemy_explosion.mp3",
            "spawner_destroy": "spawner_destroy.mp3",
            "player_hurt": "player_hurt.mp3",
            "phase_complete": "phase_complete.mp3",
        }

        for name, filename in sfx_map.items():
            sfx_path = os.path.join(BASE_DIR, "sfx", filename)
            if os.path.exists(sfx_path):
                try:
                    snd = pygame.mixer.Sound(sfx_path)
                    eff_vol = self.master_volume * self.sfx_volume
                    snd.set_volume(eff_vol)
                    self.sounds[name] = snd
                except Exception as e:
                    print(f"[AudioManager] Failed loading SFX '{name}': {e}")
            else:
                print(f"[AudioManager] SFX file not found: {sfx_path}")

    def _apply_music_volume(self):
        if self.mixer_initialized and self.music_loaded:
            eff_vol = self.master_volume * self.music_volume
            try:
                pygame.mixer.music.set_volume(eff_vol)
            except Exception:
                pass

    def _apply_sfx_volumes(self):
        if self.mixer_initialized:
            eff_vol = self.master_volume * self.sfx_volume
            for snd in self.sounds.values():
                try:
                    snd.set_volume(eff_vol)
                except Exception:
                    pass

    # ---------------- Music Controls ----------------
    def play_music(self, loop=-1):
        """Starts background music loop if not already playing."""
        if not self.mixer_initialized or not self.music_loaded:
            return
        try:
            if not pygame.mixer.music.get_busy():
                self._apply_music_volume()
                pygame.mixer.music.play(loops=loop)
                self.is_music_playing = True
        except Exception as e:
            print(f"[AudioManager] play_music error: {e}")

    def stop_music(self):
        """Stops background music."""
        if self.mixer_initialized:
            try:
                pygame.mixer.music.stop()
                self.is_music_playing = False
            except Exception:
                pass

    def pause_music(self):
        """Pauses background music."""
        if self.mixer_initialized and self.is_music_playing:
            try:
                pygame.mixer.music.pause()
            except Exception:
                pass

    def unpause_music(self):
        """Resumes background music."""
        if self.mixer_initialized and self.is_music_playing:
            try:
                pygame.mixer.music.unpause()
            except Exception:
                pass

    # ---------------- SFX Controls ----------------
    def play_sfx(self, name):
        """Plays a sound effect by name."""
        if not self.mixer_initialized:
            return
        snd = self.sounds.get(name)
        if snd is not None and self.master_volume > 0 and self.sfx_volume > 0:
            try:
                snd.play()
            except Exception:
                pass

    def test_sfx(self):
        """Plays a sample sound to test volume settings."""
        self.play_sfx("shoot")

    # ---------------- Volume Sliders ----------------
    def set_master_volume(self, val):
        self.master_volume = max(0.0, min(1.0, float(val)))
        self._apply_music_volume()
        self._apply_sfx_volumes()
        self.save_settings()

    def set_music_volume(self, val):
        self.music_volume = max(0.0, min(1.0, float(val)))
        self._apply_music_volume()
        self.save_settings()

    def set_sfx_volume(self, val):
        self.sfx_volume = max(0.0, min(1.0, float(val)))
        self._apply_sfx_volumes()
        self.save_settings()


def get_audio_manager():
    """Convenience helper to retrieve the AudioManager singleton."""
    return AudioManager.get_instance()
