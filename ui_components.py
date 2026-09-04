"""
Shared UI Components for Assignment 3 Part 2.
Contains ornamental diamond-wing BannerButton and ambient particle system.
"""

import math
import random
import pygame


class MenuParticle:
    """Drifting ambient dust particle for rich background atmosphere."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.reset()

    def reset(self):
        self.x = random.uniform(0, self.width)
        self.y = random.uniform(0, self.height)
        self.vx = random.uniform(-10.0, 10.0)
        self.vy = random.uniform(15.0, 45.0)
        self.radius = random.uniform(1.0, 2.5)
        self.alpha = random.uniform(60, 180)
        self.pulse = random.uniform(0, math.pi * 2)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.pulse += dt * 2.0
        if self.y > self.height or self.x < 0 or self.x > self.width:
            self.reset()
            self.y = 0

    def draw(self, surface):
        a = max(20, min(255, int(self.alpha + math.sin(self.pulse) * 40)))
        surf = pygame.Surface((int(self.radius * 2 + 2), int(self.radius * 2 + 2)), pygame.SRCALPHA)
        pygame.draw.circle(surf, (220, 230, 255, a), (int(self.radius + 1), int(self.radius + 1)), int(self.radius))
        surface.blit(surf, (self.x - self.radius - 1, self.y - self.radius - 1))


class BannerButton:
    """
    Ornamental Game Button styled after classic RPG / Action game plaques:
    Rectangular central banner with sharp diamond / arrow endcap wings.
    """

    def __init__(self, center_x, center_y, width, height, text, tag=""):
        self.cx = center_x
        self.cy = center_y
        self.w = width
        self.h = height
        self.text = text
        self.tag = tag

        self.rect = pygame.Rect(center_x - width // 2, center_y - height // 2, width, height)
        self.is_hovered = False
        self.hover_anim = 0.0

    def update(self, mouse_pos, dt=0.016):
        wing_w = self.h * 0.45
        hit_box = pygame.Rect(self.rect.x - wing_w, self.rect.y, self.w + wing_w * 2, self.h)
        self.is_hovered = hit_box.collidepoint(mouse_pos)

        target = 1.0 if self.is_hovered else 0.0
        self.hover_anim += (target - self.hover_anim) * min(1.0, 15.0 * dt)

    def draw(self, surface, font, tag_font=None):
        expand = self.hover_anim * 6.0
        bw = self.w + expand * 2
        bh = self.h + expand * 0.8
        bx = self.cx - bw / 2
        by = self.cy - bh / 2

        wing_len = bh * 0.42 + expand * 0.3

        # Palette: Parchment / Gold Ribbon Style (Matching Reference Image)
        r_base = int(228 + 27 * self.hover_anim)
        g_base = int(214 + 28 * self.hover_anim)
        b_base = int(162 + 22 * self.hover_anim)
        banner_col = (r_base, g_base, b_base)

        border_col = (45, 52, 60) if not self.is_hovered else (20, 30, 45)
        text_col = (20, 38, 48) if not self.is_hovered else (5, 20, 32)
        inner_trim_col = (185, 168, 115) if not self.is_hovered else (240, 200, 80)

        # 1. Outer Shadow / Glow
        if self.hover_anim > 0.05:
            glow_surf = pygame.Surface((int(bw + wing_len * 2 + 20), int(bh + 20)), pygame.SRCALPHA)
            g_alpha = int(90 * self.hover_anim)
            pygame.draw.rect(
                glow_surf,
                (0, 255, 204, g_alpha),
                (10, 10, int(bw + wing_len * 2), int(bh)),
                border_radius=4,
            )
            surface.blit(glow_surf, (bx - wing_len - 10, by - 10))

        # 2. Main Central Banner
        banner_rect = pygame.Rect(int(bx), int(by), int(bw), int(bh))
        pygame.draw.rect(surface, banner_col, banner_rect)
        pygame.draw.rect(surface, border_col, banner_rect, width=3)

        # 3. Left Wing (Diamond / Arrow Plaque Endcap)
        left_tip = (bx - wing_len, self.cy)
        left_top_notch = (bx, by)
        left_bot_notch = (bx, by + bh)

        left_pts = [left_top_notch, left_tip, left_bot_notch]
        pygame.draw.polygon(surface, banner_col, left_pts)
        pygame.draw.polygon(surface, border_col, left_pts, width=3)

        # Left inner diamond ornament
        l_inner_tip = (bx - wing_len * 0.82, self.cy)
        l_inner_top = (bx - wing_len * 0.28, by + bh * 0.25)
        l_inner_bot = (bx - wing_len * 0.28, by + bh * 0.75)
        l_inner_right = (bx - wing_len * 0.05, self.cy)
        pygame.draw.polygon(surface, inner_trim_col, [l_inner_top, l_inner_tip, l_inner_bot, l_inner_right])
        pygame.draw.polygon(surface, border_col, [l_inner_top, l_inner_tip, l_inner_bot, l_inner_right], width=2)

        # 4. Right Wing (Diamond / Arrow Plaque Endcap)
        rx = bx + bw
        right_tip = (rx + wing_len, self.cy)
        right_top_notch = (rx, by)
        right_bot_notch = (rx, by + bh)

        right_pts = [right_top_notch, right_tip, right_bot_notch]
        pygame.draw.polygon(surface, banner_col, right_pts)
        pygame.draw.polygon(surface, border_col, right_pts, width=3)

        # Right inner diamond ornament
        r_inner_tip = (rx + wing_len * 0.82, self.cy)
        r_inner_top = (rx + wing_len * 0.28, by + bh * 0.25)
        r_inner_bot = (rx + wing_len * 0.28, by + bh * 0.75)
        r_inner_left = (rx + wing_len * 0.05, self.cy)
        pygame.draw.polygon(surface, inner_trim_col, [r_inner_top, r_inner_tip, r_inner_bot, r_inner_left])
        pygame.draw.polygon(surface, border_col, [r_inner_top, r_inner_tip, r_inner_bot, r_inner_left], width=2)

        # 5. Top & Bottom Inner Border Trim Lines
        trim_inset = 4
        pygame.draw.line(
            surface,
            inner_trim_col,
            (bx + trim_inset, by + trim_inset),
            (rx - trim_inset, by + trim_inset),
            2,
        )
        pygame.draw.line(
            surface,
            inner_trim_col,
            (bx + trim_inset, by + bh - trim_inset),
            (rx - trim_inset, by + bh - trim_inset),
            2,
        )

        # 6. Button Text (Bold, Sharp, Centered)
        t_surf = font.render(self.text, True, text_col)
        surface.blit(t_surf, (self.cx - t_surf.get_width() // 2, self.cy - t_surf.get_height() // 2 - 1))

        # 7. Badge / Rubric Tag
        if self.tag and tag_font:
            tag_surf = tag_font.render(self.tag, True, (0, 255, 204) if self.is_hovered else (255, 215, 0))
            surface.blit(tag_surf, (rx + wing_len + 14, self.cy - tag_surf.get_height() // 2))
