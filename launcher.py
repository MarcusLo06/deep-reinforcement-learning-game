"""
Unified Graphical Launcher & Assessment Suite with Premium Game Menu Aesthetic.
Features ornamental diamond-wing banner buttons, hierarchical submenus (Play, AI Showcase, Guide, Exit),
and full keyboard/mouse navigation matching the visual reference.
"""

import os
import sys
import math
import random
import pygame

# Ensure local imports resolve
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from arena_env import config
from manual_play import run_manual_play
from evaluate import evaluate
from ui_components import BannerButton, MenuParticle


class UnifiedLauncher:
    """Interactive Graphical Menu Application."""

    def __init__(self, width=800, height=600):
        pygame.init()
        pygame.display.init()
        pygame.font.init()

        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Assignment 3 Part 2 - Deep RL Arena Launcher")
        self.clock = pygame.time.Clock()

        # Fonts
        self.title_font = pygame.font.SysFont("Trebuchet MS", 34, bold=True)
        self.subtitle_font = pygame.font.SysFont("Consolas", 13, bold=True)
        self.btn_font = pygame.font.SysFont("Trebuchet MS", 20, bold=True)
        self.btn_sub_font = pygame.font.SysFont("Trebuchet MS", 16, bold=True)
        self.tag_font = pygame.font.SysFont("Consolas", 12, bold=True)
        self.guide_font = pygame.font.SysFont("Consolas", 13, bold=True)
        self.guide_header_font = pygame.font.SysFont("Trebuchet MS", 20, bold=True)

        # Ambient particles
        self.particles = [MenuParticle(self.width, self.height) for _ in range(40)]
        self.time_elapsed = 0.0

        # Menus State: 'MAIN', 'PLAY_SELECT', 'AI_SELECT', 'GUIDE'
        self.state = "MAIN"

        # Model Paths Check
        self.model_1_path = os.path.join(current_dir, "models", "ppo_control_style_1.zip")
        self.model_2_path = os.path.join(current_dir, "models", "ppo_control_style_2.zip")

        self._build_menus()

    def _build_menus(self):
        cx = self.width // 2
        btn_w = 260
        btn_h = 48
        gap = 64
        start_y = 230

        # MAIN MENU BUTTONS
        self.main_buttons = [
            BannerButton(cx, start_y + 0 * gap, btn_w, btn_h, "PLAY"),
            BannerButton(cx, start_y + 1 * gap, btn_w, btn_h, "AI SHOWCASE"),
            BannerButton(cx, start_y + 2 * gap, btn_w, btn_h, "GUIDE"),
            BannerButton(cx, start_y + 3 * gap, btn_w, btn_h, "EXIT"),
        ]

        # PLAY SUBMENU (Style 1 vs Style 2)
        sub_w = 340
        self.play_buttons = [
            BannerButton(cx, start_y + 0 * gap, sub_w, btn_h, "STYLE 1: ROTATION & THRUST"),
            BannerButton(cx, start_y + 1 * gap, sub_w, btn_h, "STYLE 2: DIRECT MOVEMENT"),
            BannerButton(cx, start_y + 2.5 * gap, 200, 42, "BACK"),
        ]

        # AI SHOWCASE SUBMENU (Agent 1 vs Agent 2)
        self.ai_buttons = [
            BannerButton(cx, start_y + 0 * gap, sub_w, btn_h, "AGENT 1 (STYLE 1 POLICY)"),
            BannerButton(cx, start_y + 1 * gap, sub_w, btn_h, "AGENT 2 (STYLE 2 POLICY)"),
            BannerButton(cx, start_y + 2.5 * gap, 200, 42, "BACK"),
        ]

        # GUIDE SCREEN BACK BUTTON (Placed reliably at center bottom)
        self.guide_back_btn = BannerButton(cx, 545, 190, 40, "◄ BACK")

    def _check_models(self):
        return os.path.exists(self.model_1_path), os.path.exists(self.model_2_path)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            self.time_elapsed += dt
            mouse_pos = pygame.mouse.get_pos()

            # 1. Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if self.state == "MAIN":
                        if event.key in (pygame.K_1, pygame.K_p):
                            self.state = "PLAY_SELECT"
                        elif event.key in (pygame.K_2, pygame.K_a):
                            self.state = "AI_SELECT"
                        elif event.key in (pygame.K_3, pygame.K_g):
                            self.state = "GUIDE"
                        elif event.key in (pygame.K_4, pygame.K_ESCAPE, pygame.K_q):
                            running = False
                    elif self.state == "PLAY_SELECT":
                        if event.key == pygame.K_1:
                            self._launch_manual(1)
                        elif event.key == pygame.K_2:
                            self._launch_manual(2)
                        elif event.key in (pygame.K_ESCAPE, pygame.K_b, pygame.K_BACKSPACE):
                            self.state = "MAIN"
                    elif self.state == "AI_SELECT":
                        if event.key == pygame.K_1:
                            self._launch_eval(1)
                        elif event.key == pygame.K_2:
                            self._launch_eval(2)
                        elif event.key in (pygame.K_ESCAPE, pygame.K_b, pygame.K_BACKSPACE):
                            self.state = "MAIN"
                    elif self.state == "GUIDE":
                        if event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN, pygame.K_b, pygame.K_BACKSPACE):
                            self.state = "MAIN"

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "MAIN":
                        for i, btn in enumerate(self.main_buttons):
                            if btn.is_hovered:
                                if i == 0:
                                    self.state = "PLAY_SELECT"
                                elif i == 1:
                                    self.state = "AI_SELECT"
                                elif i == 2:
                                    self.state = "GUIDE"
                                elif i == 3:
                                    running = False
                    elif self.state == "PLAY_SELECT":
                        if self.play_buttons[0].is_hovered:
                            self._launch_manual(1)
                        elif self.play_buttons[1].is_hovered:
                            self._launch_manual(2)
                        elif self.play_buttons[2].is_hovered:
                            self.state = "MAIN"
                    elif self.state == "AI_SELECT":
                        if self.ai_buttons[0].is_hovered:
                            self._launch_eval(1)
                        elif self.ai_buttons[1].is_hovered:
                            self._launch_eval(2)
                        elif self.ai_buttons[2].is_hovered:
                            self.state = "MAIN"
                    elif self.state == "GUIDE":
                        if self.guide_back_btn.is_hovered:
                            self.state = "MAIN"

            # 2. Update Animations
            for p in self.particles:
                p.update(dt)

            if self.state == "MAIN":
                for btn in self.main_buttons:
                    btn.update(mouse_pos, dt)
            elif self.state == "PLAY_SELECT":
                for btn in self.play_buttons:
                    btn.update(mouse_pos, dt)
            elif self.state == "AI_SELECT":
                for btn in self.ai_buttons:
                    btn.update(mouse_pos, dt)
            elif self.state == "GUIDE":
                self.guide_back_btn.update(mouse_pos, dt)

            # 3. Render Background
            self.screen.fill(config.COLOR_BG)

            # Cyber grid lines
            for x in range(0, self.width, 40):
                pygame.draw.line(self.screen, (16, 22, 34), (x, 0), (x, self.height), 1)
            for y in range(0, self.height, 40):
                pygame.draw.line(self.screen, (16, 22, 34), (0, y), (self.width, y), 1)

            # Ambient particles
            for p in self.particles:
                p.draw(self.screen)

            # 4. Render Active View
            if self.state in ("MAIN", "PLAY_SELECT", "AI_SELECT"):
                self._draw_header()
                current_buttons = (
                    self.main_buttons if self.state == "MAIN"
                    else self.play_buttons if self.state == "PLAY_SELECT"
                    else self.ai_buttons
                )
                for btn in current_buttons:
                    font_to_use = self.btn_font if len(btn.text) <= 15 else self.btn_sub_font
                    btn.draw(self.screen, font_to_use, self.tag_font)
                self._draw_footer()
            elif self.state == "GUIDE":
                self._draw_guide_screen()

            # Outer frame border
            pygame.draw.rect(self.screen, config.COLOR_BORDER, (0, 0, self.width, self.height), 3)

            pygame.display.flip()

        pygame.quit()
        sys.exit(0)

    def _draw_header(self):
        header_h = 135
        header_surf = pygame.Surface((self.width, header_h), pygame.SRCALPHA)
        header_surf.fill((12, 16, 26, 230))
        self.screen.blit(header_surf, (0, 0))
        pygame.draw.line(self.screen, config.COLOR_BORDER, (0, header_h), (self.width, header_h), 2)

        # Pulsing Game Title
        glow_val = int(210 + 45 * math.sin(self.time_elapsed * 2.8))
        title_col = (0, glow_val, int(glow_val * 0.85))
        t_surf = self.title_font.render("DEEP RL ACTION ARENA", True, title_col)
        self.screen.blit(t_surf, ((self.width - t_surf.get_width()) // 2, 20))

        sub_surf = self.subtitle_font.render(
            "Assignment 3 • Part 2: Gymnasium & Stable-Baselines3", True, (180, 205, 235)
        )
        self.screen.blit(sub_surf, ((self.width - sub_surf.get_width()) // 2, 64))

        # Model Status Badges
        m1_ok, m2_ok = self._check_models()
        s1_col = (0, 230, 120) if m1_ok else (255, 90, 90)
        s2_col = (0, 230, 120) if m2_ok else (255, 90, 90)
        st1_txt = self.tag_font.render(f"● Agent 1: {'Ready' if m1_ok else 'Missing'}", True, s1_col)
        st2_txt = self.tag_font.render(f"● Agent 2: {'Ready' if m2_ok else 'Missing'}", True, s2_col)
        self.screen.blit(st1_txt, (self.width // 2 - 170, 96))
        self.screen.blit(st2_txt, (self.width // 2 + 50, 96))

        if self.state == "PLAY_SELECT":
            lbl = self.btn_font.render("— SELECT CONTROL STYLE —", True, (255, 215, 0))
            self.screen.blit(lbl, ((self.width - lbl.get_width()) // 2, 168))
        elif self.state == "AI_SELECT":
            lbl = self.btn_font.render("— SELECT TRAINED AGENT —", True, (255, 215, 0))
            self.screen.blit(lbl, ((self.width - lbl.get_width()) // 2, 168))

    def _draw_footer(self):
        f_txt = self.tag_font.render("Click with Mouse or Press [1-4] • ESC to go Back / Exit", True, (110, 135, 165))
        self.screen.blit(f_txt, ((self.width - f_txt.get_width()) // 2, self.height - 24))

    def _draw_guide_screen(self):
        modal_w = 720
        modal_h = 560
        mx = (self.width - modal_w) // 2
        my = 18

        modal_surf = pygame.Surface((modal_w, modal_h), pygame.SRCALPHA)
        modal_surf.fill((14, 18, 30, 245))
        self.screen.blit(modal_surf, (mx, my))
        pygame.draw.rect(self.screen, (0, 255, 204), (mx, my, modal_w, modal_h), 2, border_radius=8)

        t_surf = self.guide_header_font.render("CONTROLS & INSTRUCTIONS", True, (0, 255, 204))
        self.screen.blit(t_surf, (mx + 24, my + 14))
        pygame.draw.line(self.screen, (40, 60, 90), (mx + 20, my + 42), (mx + modal_w - 20, my + 42), 1)

        # Clear, formatted instruction lines
        lines = [
            ("1. Style 1 (Rotation & Thrust):", (255, 215, 0)),
            ("  • W / UP    = THRUST FORWARD", (220, 230, 245)),
            ("  • A / LEFT  = ROTATE LEFT", (220, 230, 245)),
            ("  • D / RIGHT = ROTATE RIGHT", (220, 230, 245)),
            ("  • SPACE     = SHOOT LASER", (220, 230, 245)),
            ("", (0, 0, 0)),
            ("2. Style 2 (Direct Movement):", (255, 215, 0)),
            ("  • W / UP    = MOVE UP", (220, 230, 245)),
            ("  • S / DOWN  = MOVE DOWN", (220, 230, 245)),
            ("  • A / LEFT  = MOVE LEFT", (220, 230, 245)),
            ("  • D / RIGHT = MOVE RIGHT", (220, 230, 245)),
            ("  • SPACE     = SHOOT LASER", (220, 230, 245)),
            ("  • 1 / 2     = SWITCH STYLE IN REAL TIME", (180, 210, 240)),
            ("  • R         = RESET EPISODE", (180, 210, 240)),
            ("  • ESC       = BACK TO GAME MENU", (180, 210, 240)),
            ("", (0, 0, 0)),
            ("3. AI Evaluation Controls:", (255, 215, 0)),
            ("  • SPACE     = PAUSE / RESUME SIMULATION", (220, 230, 245)),
            ("  • N         = STEP 1 SINGLE FRAME (WHEN PAUSED)", (220, 230, 245)),
            ("  • UP / DOWN = INCREASE / DECREASE SIMULATION SPEED", (220, 230, 245)),
            ("  • R         = RESET EPISODE", (180, 210, 240)),
            ("  • ESC       = BACK TO GAME MENU", (180, 210, 240)),
        ]

        cy = my + 52
        for text, col in lines:
            if text:
                s = self.guide_font.render(text, True, col)
                self.screen.blit(s, (mx + 28, cy))
            cy += 19

        # Draw Back Button (Matches Diamond Wing Banner Style)
        self.guide_back_btn.draw(self.screen, self.btn_sub_font, self.tag_font)

    def _launch_manual(self, style):
        print(f"\n>>> Launching Manual Play (Control Style {style})...")
        run_manual_play(style=style, return_to_menu=True)
        self._reinit_screen()

    def _launch_eval(self, style):
        model_path = self.model_1_path if style == 1 else self.model_2_path
        print(f"\n>>> Launching AI Evaluation (Agent {style} - Style {style})...")
        evaluate(model_path=model_path, style=style, algo="ppo", episodes=10, deterministic=False, return_to_menu=True)
        self._reinit_screen()

    def _reinit_screen(self):
        if not pygame.get_init():
            pygame.init()
        if not pygame.display.get_init():
            pygame.display.init()
        if not pygame.font.get_init():
            pygame.font.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Assignment 3 Part 2 - Deep RL Arena Launcher")
        self.clock = pygame.time.Clock()


def main():
    launcher = UnifiedLauncher()
    launcher.run()


if __name__ == "__main__":
    main()
