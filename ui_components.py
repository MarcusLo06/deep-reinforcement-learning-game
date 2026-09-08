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


class VolumeSlider:
    """
    Volume Slider with draggable thumb
    """

    def __init__(self, center_x, center_y, width, height, label, initial_val=0.8, on_change=None):
        self.cx = center_x
        self.cy = center_y
        self.w = width
        self.h = height
        self.label = label
        self.value = max(0.0, min(1.0, float(initial_val)))
        self.on_change = on_change

        self.is_dragging = False
        self.is_hovered = False

        btn_size = 24
        pad = 8
        self.track_w = width - (btn_size * 2 + pad * 2)
        self.track_h = 10

        # Position elements relative to (center_x, center_y)
        total_w = width
        start_x = center_x - total_w // 2

        self.btn_minus = pygame.Rect(start_x, center_y + 4, btn_size, btn_size)
        self.track_rect = pygame.Rect(start_x + btn_size + pad, center_y + 4 + (btn_size - self.track_h) // 2, self.track_w, self.track_h)
        self.btn_plus = pygame.Rect(self.track_rect.right + pad, center_y + 4, btn_size, btn_size)

        self.thumb_radius = 8

    def set_value(self, new_val):
        new_val = max(0.0, min(1.0, float(new_val)))
        if abs(new_val - self.value) > 0.001:
            self.value = new_val
            if self.on_change:
                self.on_change(self.value)

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_minus.collidepoint(mouse_pos):
                self.set_value(round(self.value - 0.05, 2))
                return True
            elif self.btn_plus.collidepoint(mouse_pos):
                self.set_value(round(self.value + 0.05, 2))
                return True
            elif self.track_rect.inflate(10, 16).collidepoint(mouse_pos):
                self.is_dragging = True
                val = (mouse_pos[0] - self.track_rect.x) / self.track_rect.width
                self.set_value(val)
                return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging:
                self.is_dragging = False
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                val = (mouse_pos[0] - self.track_rect.x) / self.track_rect.width
                self.set_value(val)
                return True

        return False

    def update(self, mouse_pos, dt=0.016):
        self.is_hovered = self.track_rect.inflate(16, 20).collidepoint(mouse_pos)

    def draw(self, surface, label_font, val_font):
        # 1. Label and Percentage text
        lbl_surf = label_font.render(self.label, True, (0, 255, 204))
        surface.blit(lbl_surf, (self.btn_minus.x, self.cy - 20))

        pct_str = f"{int(round(self.value * 100))}%"
        val_surf = val_font.render(pct_str, True, (255, 215, 0))
        surface.blit(val_surf, (self.btn_plus.right - val_surf.get_width(), self.cy - 20))

        # 2. Minus [-] Button
        mouse_pos = pygame.mouse.get_pos()
        m_hov = self.btn_minus.collidepoint(mouse_pos)
        pygame.draw.rect(surface, (35, 50, 75) if m_hov else (20, 28, 42), self.btn_minus, border_radius=4)
        pygame.draw.rect(surface, (0, 255, 204) if m_hov else (60, 90, 130), self.btn_minus, width=1, border_radius=4)
        m_txt = val_font.render("-", True, (255, 255, 255) if m_hov else (180, 205, 230))
        surface.blit(m_txt, (self.btn_minus.centerx - m_txt.get_width() // 2, self.btn_minus.centery - m_txt.get_height() // 2))

        # 3. Plus [+] Button
        p_hov = self.btn_plus.collidepoint(mouse_pos)
        pygame.draw.rect(surface, (35, 50, 75) if p_hov else (20, 28, 42), self.btn_plus, border_radius=4)
        pygame.draw.rect(surface, (0, 255, 204) if p_hov else (60, 90, 130), self.btn_plus, width=1, border_radius=4)
        p_txt = val_font.render("+", True, (255, 255, 255) if p_hov else (180, 205, 230))
        surface.blit(p_txt, (self.btn_plus.centerx - p_txt.get_width() // 2, self.btn_plus.centery - p_txt.get_height() // 2))

        # 4. Slider Track (Background)
        pygame.draw.rect(surface, (15, 20, 32), self.track_rect, border_radius=5)
        pygame.draw.rect(surface, (50, 75, 110), self.track_rect, width=1, border_radius=5)

        # 5. Filled Level Bar (Neon Cyan)
        fill_w = int(self.track_rect.width * self.value)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.track_rect.x, self.track_rect.y, fill_w, self.track_rect.height)
            pygame.draw.rect(surface, (0, 230, 180), fill_rect, border_radius=5)
            # Glass shine
            shine_rect = pygame.Rect(self.track_rect.x, self.track_rect.y, fill_w, max(1, self.track_rect.height // 2))
            shine_surf = pygame.Surface((fill_w, max(1, self.track_rect.height // 2)), pygame.SRCALPHA)
            shine_surf.fill((255, 255, 255, 60))
            surface.blit(shine_surf, shine_rect.topleft)

        # 6. Thumb Knob (Gold diamond / glowing circle)
        thumb_x = self.track_rect.x + fill_w
        thumb_y = self.track_rect.centery
        thumb_col = (255, 235, 120) if (self.is_dragging or self.is_hovered) else (220, 195, 80)
        pygame.draw.circle(surface, thumb_col, (thumb_x, thumb_y), self.thumb_radius)
        pygame.draw.circle(surface, (20, 30, 45), (thumb_x, thumb_y), self.thumb_radius, width=2)
        pygame.draw.circle(surface, (255, 255, 255), (thumb_x, thumb_y), 3)

