"""
In-Game Settings & Pause Modal System for Assignment 3 Part 2.
Provides in-game pause menu with Resume, Restart, Controls Guide, and
Exit to Menu with an interactive warning confirmation dialog.
Styled with the same ornamental gold diamond-wing banners.
"""

import math
import pygame
from ui_components import BannerButton, VolumeSlider
from arena_env import config
from audio_manager import get_audio_manager


class InGameMenu:
    """
    Manages in-game pause overlay, audio settings, controls guide,
    and exit confirmation warning dialog.
    """

    def __init__(self, width=config.SCREEN_WIDTH, height=config.SCREEN_HEIGHT):
        if not pygame.get_init():
            pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

        self.width = width
        self.height = height
        self.state = "SETTINGS"  # 'SETTINGS', 'AUDIO', 'GUIDE', 'CONFIRM_EXIT'

        # Audio Manager
        self.audio = get_audio_manager()

        # Fonts
        self.title_font = pygame.font.SysFont("Trebuchet MS", 26, bold=True)
        self.btn_font = pygame.font.SysFont("Trebuchet MS", 18, bold=True)
        self.btn_sub_font = pygame.font.SysFont("Trebuchet MS", 15, bold=True)
        self.tag_font = pygame.font.SysFont("Consolas", 12, bold=True)
        self.body_font = pygame.font.SysFont("Consolas", 13, bold=True)
        self.warn_font = pygame.font.SysFont("Trebuchet MS", 16, bold=True)
        self.slider_font = pygame.font.SysFont("Consolas", 13, bold=True)

        cx = self.width // 2
        start_y = 180
        gap = 52
        btn_w = 260
        btn_h = 40

        # 1. Main Pause Menu Buttons
        self.settings_buttons = [
            BannerButton(cx, start_y + 0 * gap, btn_w, btn_h, "RESUME"),
            BannerButton(cx, start_y + 1 * gap, btn_w, btn_h, "AUDIO & VOLUME"),
            BannerButton(cx, start_y + 2 * gap, btn_w, btn_h, "RESTART"),
            BannerButton(cx, start_y + 3 * gap, btn_w, btn_h, "CONTROLS GUIDE"),
            BannerButton(cx, start_y + 4 * gap, btn_w, btn_h, "EXIT TO MENU"),
        ]

        # 2. Audio Settings Sliders & Back Button
        slider_w = 340
        sl_y = 185
        sl_gap = 62
        self.master_slider = VolumeSlider(
            cx, sl_y + 0 * sl_gap, slider_w, 24, "MASTER VOLUME",
            self.audio.master_volume, on_change=self.audio.set_master_volume
        )
        self.music_slider = VolumeSlider(
            cx, sl_y + 1 * sl_gap, slider_w, 24, "BGM MUSIC",
            self.audio.music_volume, on_change=self.audio.set_music_volume
        )
        self.sfx_slider = VolumeSlider(
            cx, sl_y + 2 * sl_gap, slider_w, 24, "SFX EFFECTS",
            self.audio.sfx_volume, on_change=self.audio.set_sfx_volume
        )
        self.audio_back_btn = BannerButton(cx, 375, 180, 38, "◄ BACK")

        # 3. Guide Back Button
        self.guide_back_btn = BannerButton(cx, 535, 180, 38, "◄ BACK")

        # 4. Exit Confirmation Buttons
        self.confirm_yes_btn = BannerButton(cx - 110, 365, 170, 42, "YES, EXIT")
        self.confirm_no_btn = BannerButton(cx + 110, 365, 170, 42, "NO, CANCEL")

        # 5. Top-Right Settings Icon Hitbox (46x30)
        self.gear_rect = pygame.Rect(self.width - 56, 7, 46, 30)

    def reset_state(self):
        self.state = "SETTINGS"
        self.master_slider.set_value(self.audio.master_volume)
        self.music_slider.set_value(self.audio.music_volume)
        self.sfx_slider.set_value(self.audio.sfx_volume)

    def handle_event(self, event, mouse_pos):
        """
        Processes events when menu is active or when gear button is clicked.
        Returns one of: 'TOGGLE_PAUSE', 'RESUME', 'RESTART', 'EXIT_CONFIRMED', None
        """
        # 1. Gear Icon Click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.gear_rect.collidepoint(mouse_pos):
                return "TOGGLE_PAUSE"

        # 2. Audio Sliders Interaction
        if self.state == "AUDIO":
            if self.master_slider.handle_event(event, mouse_pos):
                return None
            if self.music_slider.handle_event(event, mouse_pos):
                return None
            if self.sfx_slider.handle_event(event, mouse_pos):
                return None

        # 3. Keydown Shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_p, pygame.K_PAUSE):
                return "TOGGLE_PAUSE"

            if self.state == "SETTINGS":
                if event.key in (pygame.K_ESCAPE, pygame.K_SPACE):
                    return "RESUME"
                elif event.key in (pygame.K_a, pygame.K_v):
                    self.state = "AUDIO"
                elif event.key == pygame.K_r:
                    return "RESTART"
                elif event.key == pygame.K_g:
                    self.state = "GUIDE"
                elif event.key == pygame.K_e:
                    self.state = "CONFIRM_EXIT"

            elif self.state == "AUDIO":
                if event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN, pygame.K_b, pygame.K_BACKSPACE):
                    self.state = "SETTINGS"

            elif self.state == "GUIDE":
                if event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN, pygame.K_b, pygame.K_BACKSPACE):
                    self.state = "SETTINGS"

            elif self.state == "CONFIRM_EXIT":
                if event.key in (pygame.K_y, pygame.K_RETURN):
                    return "EXIT_CONFIRMED"
                elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                    self.state = "SETTINGS"

        # 4. Mouse Clicks inside Active Menu
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == "SETTINGS":
                if self.settings_buttons[0].is_hovered:
                    return "RESUME"
                elif self.settings_buttons[1].is_hovered:
                    self.state = "AUDIO"
                elif self.settings_buttons[2].is_hovered:
                    return "RESTART"
                elif self.settings_buttons[3].is_hovered:
                    self.state = "GUIDE"
                elif self.settings_buttons[4].is_hovered:
                    self.state = "CONFIRM_EXIT"

            elif self.state == "AUDIO":
                if self.audio_back_btn.is_hovered:
                    self.state = "SETTINGS"

            elif self.state == "GUIDE":
                if self.guide_back_btn.is_hovered:
                    self.state = "SETTINGS"

            elif self.state == "CONFIRM_EXIT":
                if self.confirm_yes_btn.is_hovered:
                    return "EXIT_CONFIRMED"
                elif self.confirm_no_btn.is_hovered:
                    self.state = "SETTINGS"

        return None

    def update(self, mouse_pos, dt=0.016):
        if self.state == "SETTINGS":
            for btn in self.settings_buttons:
                btn.update(mouse_pos, dt)
        elif self.state == "AUDIO":
            self.master_slider.update(mouse_pos, dt)
            self.music_slider.update(mouse_pos, dt)
            self.sfx_slider.update(mouse_pos, dt)
            self.audio_back_btn.update(mouse_pos, dt)
        elif self.state == "GUIDE":
            self.guide_back_btn.update(mouse_pos, dt)
        elif self.state == "CONFIRM_EXIT":
            self.confirm_yes_btn.update(mouse_pos, dt)
            self.confirm_no_btn.update(mouse_pos, dt)

    def draw_gear_icon(self, surface, mouse_pos):
        """Draws the top-right settings/gear button in the HUD with crisp vector graphics."""
        is_hover = self.gear_rect.collidepoint(mouse_pos)
        bg_col = (38, 64, 105) if is_hover else (24, 36, 56)
        bdr_col = (0, 255, 204) if is_hover else (0, 190, 160)

        pygame.draw.rect(surface, bg_col, self.gear_rect, border_radius=6)
        pygame.draw.rect(surface, bdr_col, self.gear_rect, width=2, border_radius=6)

        # High-visibility vector cogwheel/gear icon
        cx = self.gear_rect.centerx
        cy = self.gear_rect.centery
        radius = 8
        gear_col = (255, 255, 255) if is_hover else (0, 255, 204)
        num_teeth = 8
        for i in range(num_teeth):
            ang = i * (math.pi / 4.0)
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            x1 = cx + cos_a * (radius - 2)
            y1 = cy + sin_a * (radius - 2)
            x2 = cx + cos_a * (radius + 4)
            y2 = cy + sin_a * (radius + 4)
            pygame.draw.line(surface, gear_col, (int(x1), int(y1)), (int(x2), int(y2)), 3)
        pygame.draw.circle(surface, gear_col, (int(cx), int(cy)), int(radius), 2)
        pygame.draw.circle(surface, (15, 20, 32), (int(cx), int(cy)), 3, 0)
        pygame.draw.circle(surface, gear_col, (int(cx), int(cy)), 3, 1)

        # Hover Tooltip
        if is_hover:
            tip_surf = self.tag_font.render("SETTINGS [ESC]", True, (0, 255, 204))
            tip_w = tip_surf.get_width() + 10
            tip_h = tip_surf.get_height() + 6
            tip_x = min(self.width - tip_w - 6, self.gear_rect.centerx - tip_w // 2)
            tip_y = self.gear_rect.bottom + 5
            tip_bg = pygame.Surface((tip_w, tip_h), pygame.SRCALPHA)
            tip_bg.fill((10, 16, 26, 230))
            surface.blit(tip_bg, (tip_x, tip_y))
            pygame.draw.rect(surface, (0, 255, 204), (tip_x, tip_y, tip_w, tip_h), width=1, border_radius=4)
            surface.blit(tip_surf, (tip_x + 5, tip_y + 3))

    def draw_modal(self, surface, mouse_pos):
        """Renders the dark blurred modal overlay and active sub-view."""
        dim_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim_surf.fill((8, 12, 20, 215))
        surface.blit(dim_surf, (0, 0))

        if self.state == "SETTINGS":
            self._draw_settings_view(surface)
        elif self.state == "AUDIO":
            self._draw_audio_view(surface)
        elif self.state == "GUIDE":
            self._draw_guide_view(surface)
        elif self.state == "CONFIRM_EXIT":
            self._draw_confirm_view(surface)

    def _draw_settings_view(self, surface):
        mw, mh = 440, 390
        mx = (self.width - mw) // 2
        my = 105

        # Modal Box
        m_surf = pygame.Surface((mw, mh), pygame.SRCALPHA)
        m_surf.fill((16, 22, 36, 245))
        surface.blit(m_surf, (mx, my))
        pygame.draw.rect(surface, (0, 255, 204), (mx, my, mw, mh), width=2, border_radius=8)

        # Title Plaque
        t_surf = self.title_font.render("GAME PAUSED", True, (0, 255, 204))
        surface.blit(t_surf, ((self.width - t_surf.get_width()) // 2, my + 16))
        pygame.draw.line(surface, (40, 60, 90), (mx + 20, my + 48), (mx + mw - 20, my + 48), 1)

        # Draw Buttons
        for btn in self.settings_buttons:
            btn.draw(surface, self.btn_font, self.tag_font)

        # Footer Hint
        hint_txt = self.tag_font.render("Click or press [SPACE] to Resume • [ESC] to return", True, (120, 150, 185))
        surface.blit(hint_txt, ((self.width - hint_txt.get_width()) // 2, my + mh - 22))

    def _draw_audio_view(self, surface):
        mw, mh = 460, 370
        mx = (self.width - mw) // 2
        my = 115

        m_surf = pygame.Surface((mw, mh), pygame.SRCALPHA)
        m_surf.fill((16, 22, 36, 250))
        surface.blit(m_surf, (mx, my))
        pygame.draw.rect(surface, (0, 255, 204), (mx, my, mw, mh), width=2, border_radius=8)

        # Title
        t_surf = self.title_font.render("AUDIO & VOLUME SETTINGS", True, (0, 255, 204))
        surface.blit(t_surf, ((self.width - t_surf.get_width()) // 2, my + 16))
        pygame.draw.line(surface, (40, 60, 90), (mx + 20, my + 48), (mx + mw - 20, my + 48), 1)

        # Sliders
        self.master_slider.draw(surface, self.slider_font, self.tag_font)
        self.music_slider.draw(surface, self.slider_font, self.tag_font)
        self.sfx_slider.draw(surface, self.slider_font, self.tag_font)

        # Back Button (Centered)
        self.audio_back_btn.draw(surface, self.btn_sub_font, self.tag_font)

        # Footer Hint
        hint_txt = self.tag_font.render("Drag slider or click [-]/[+] • [ESC] Back", True, (120, 150, 185))
        surface.blit(hint_txt, ((self.width - hint_txt.get_width()) // 2, my + mh - 22))


    def _draw_guide_view(self, surface):
        mw, mh = 700, 540
        mx = (self.width - mw) // 2
        my = 26

        m_surf = pygame.Surface((mw, mh), pygame.SRCALPHA)
        m_surf.fill((14, 18, 30, 250))
        surface.blit(m_surf, (mx, my))
        pygame.draw.rect(surface, (0, 255, 204), (mx, my, mw, mh), width=2, border_radius=8)

        t_surf = self.title_font.render("CONTROLS & INSTRUCTIONS", True, (0, 255, 204))
        surface.blit(t_surf, ((self.width - t_surf.get_width()) // 2, my + 14))
        pygame.draw.line(surface, (40, 60, 90), (mx + 20, my + 46), (mx + mw - 20, my + 46), 1)

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
            ("  • 1 / 2     = SWITCH STYLE IN REAL TIME", (220, 230, 245)),
            ("  • R         = RESET EPISODE", (220, 230, 245)),
            ("  • ESC       = PAUSE / SETTINGS MENU", (220, 230, 245)),
            ("", (0, 0, 0)),
            ("3. AI Evaluation Controls:", (255, 215, 0)),
            ("  • SPACE     = PAUSE / RESUME SIMULATION", (220, 230, 245)),
            ("  • N         = STEP 1 SINGLE FRAME (WHEN PAUSED)", (220, 230, 245)),
            ("  • UP / DOWN = INCREASE / DECREASE SIMULATION SPEED", (220, 230, 245)),
        ]

        cy = my + 56
        for text, col in lines:
            if text:
                s = self.body_font.render(text, True, col)
                surface.blit(s, (mx + 28, cy))
            cy += 19

        self.guide_back_btn.draw(surface, self.btn_sub_font, self.tag_font)

    def _draw_confirm_view(self, surface):
        mw, mh = 500, 240
        mx = (self.width - mw) // 2
        my = 180

        # Warning Box with glowing gold/crimson border
        m_surf = pygame.Surface((mw, mh), pygame.SRCALPHA)
        m_surf.fill((20, 24, 38, 252))
        surface.blit(m_surf, (mx, my))
        pygame.draw.rect(surface, (255, 180, 50), (mx, my, mw, mh), width=3, border_radius=8)

        # Warning Header
        t_surf = self.title_font.render("⚠️ EXIT TO MAIN MENU?", True, (255, 200, 60))
        surface.blit(t_surf, ((self.width - t_surf.get_width()) // 2, my + 20))
        pygame.draw.line(surface, (60, 70, 95), (mx + 20, my + 56), (mx + mw - 20, my + 56), 1)

        # Warning Description
        d1 = self.body_font.render("Are you sure you want to leave the current game?", True, (230, 240, 255))
        d2 = self.body_font.render("Current session score and phase progress will be lost.", True, (180, 200, 225))
        surface.blit(d1, ((self.width - d1.get_width()) // 2, my + 72))
        surface.blit(d2, ((self.width - d2.get_width()) // 2, my + 98))

        # Confirm Buttons (YES / NO)
        self.confirm_yes_btn.draw(surface, self.btn_sub_font, self.tag_font)
        self.confirm_no_btn.draw(surface, self.btn_sub_font, self.tag_font)
