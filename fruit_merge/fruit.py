"""Visual representation of realistic 3D fruit sprites with animations on Tkinter Canvas."""

import math
import random
import tkinter as tk
from typing import List, Optional
from fruit_merge.constants import FRUIT_TIERS, FruitConfig, TIER_BODY_SCALE
from fruit_merge.sprites import SpriteManager


def rotate_point(cx: float, cy: float, px: float, py: float, angle: float) -> tuple[float, float]:
    """Rotates point (px, py) around center (cx, cy) by angle in radians."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    dx = px - cx
    dy = py - cy
    rx = cx + dx * cos_a - dy * sin_a
    ry = cy + dx * sin_a + dy * cos_a
    return rx, ry


class FruitVisual:
    """Manages the realistic sprite rendering and expressive animations of a fruit."""

    def __init__(
        self,
        canvas: tk.Canvas,
        fruit_id: int,
        tier: int,
        x: float,
        y: float,
        scale: float = 1.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ):
        self.canvas = canvas
        self.fruit_id = fruit_id
        self.tier = tier
        self.cfg: FruitConfig = FRUIT_TIERS[tier]
        self.r = self.cfg.radius
        self.items: List[int] = []
        self.sm = SpriteManager.get_instance()

        # Animation states: jelly wobble & natural blinking
        self.wobble_elapsed = 0.0
        self.wobble_duration = 0.42
        self.blink_timer = random.uniform(1.8, 5.0)
        self.is_blinking = False
        self.blink_duration = 0.12
        self.blink_elapsed = 0.0
        self.current_photo: Optional[ImageTk.PhotoImage] = None

        self._create_graphics(x, y, scale, offset_x, offset_y)

    def trigger_wobble(self) -> None:
        """Triggers a juicy elastic wobble oscillation."""
        self.wobble_elapsed = 0.0

    def _create_graphics(
        self, x: float, y: float, scale: float = 1.0, offset_x: float = 0.0, offset_y: float = 0.0
    ) -> None:
        sx = offset_x + x * scale
        sy = offset_y + y * scale
        sr = self.r * scale
        cfg = self.cfg
        tag = f"fruit_{self.fruit_id}"

        # Scale diameter cleanly to match physical collision circle with zero air gap
        scale_factor = TIER_BODY_SCALE.get(self.tier, 1.12)
        diameter = max(10, int(round(sr * 2.0 * scale_factor / 2.0)) * 2)
        photo = self.sm.get_fruit_sprite(self.tier, diameter, 0.0)
        self.current_photo = photo

        # 1. Realistic Sprite Image
        if photo:
            self.image_id: Optional[int] = self.canvas.create_image(
                sx, sy, image=photo, tags=("fruit", tag)
            )
            self.items.append(self.image_id)
            self.body_id: Optional[int] = None
        else:
            self.image_id = None
            # Fallback procedural circle
            self.body_id = self.canvas.create_oval(
                sx - sr, sy - sr, sx + sr, sy + sr,
                fill=cfg.color, outline=cfg.dark_color, width=max(1.5, sr * 0.05),
                tags=("fruit", tag),
            )
            self.items.append(self.body_id)

        # 2. Cute Kawaii Facial Expression overlay (blinking eyes & sweet smile)
        eye_dist = sr * 0.28
        eye_r = max(2.2, sr * 0.09)
        eye_y_offset = sr * (0.04 if self.tier == 1 else -0.02)

        # Left eye
        self.eye_l_id = self.canvas.create_oval(
            sx - eye_dist - eye_r, sy + eye_y_offset - eye_r,
            sx - eye_dist + eye_r, sy + eye_y_offset + eye_r,
            fill="#1E1E2E", outline="", tags=("fruit", tag),
        )
        # Right eye
        self.eye_r_id = self.canvas.create_oval(
            sx + eye_dist - eye_r, sy + eye_y_offset - eye_r,
            sx + eye_dist + eye_r, sy + eye_y_offset + eye_r,
            fill="#1E1E2E", outline="", tags=("fruit", tag),
        )

        # White eye glints
        glint_r = max(1.0, eye_r * 0.45)
        self.glint_l_id = self.canvas.create_oval(
            sx - eye_dist, sy + eye_y_offset - glint_r,
            sx - eye_dist + glint_r * 1.5, sy + eye_y_offset + glint_r * 0.5,
            fill="#FFFFFF", outline="", tags=("fruit", tag),
        )
        self.glint_r_id = self.canvas.create_oval(
            sx + eye_dist, sy + eye_y_offset - glint_r,
            sx + eye_dist + glint_r * 1.5, sy + eye_y_offset + glint_r * 0.5,
            fill="#FFFFFF", outline="", tags=("fruit", tag),
        )

        # Rosy blush cheeks (for tier >= 2)
        self.cheek_l_id: Optional[int] = None
        self.cheek_r_id: Optional[int] = None
        if self.tier >= 2:
            cheek_dist = sr * 0.44
            cheek_y = sy + sr * 0.12
            cr = max(2.5, sr * 0.12)
            self.cheek_l_id = self.canvas.create_oval(
                sx - cheek_dist - cr, cheek_y - cr * 0.5,
                sx - cheek_dist + cr, cheek_y + cr * 0.5,
                fill="#FF80AB", outline="", tags=("fruit", tag),
            )
            self.cheek_r_id = self.canvas.create_oval(
                sx + cheek_dist - cr, cheek_y - cr * 0.5,
                sx + cheek_dist + cr, cheek_y + cr * 0.5,
                fill="#FF80AB", outline="", tags=("fruit", tag),
            )
            self.items.extend([self.cheek_l_id, self.cheek_r_id])

        # Smile mouth
        mouth_w = max(2.5, sr * 0.18)
        mouth_y = sy + sr * 0.16
        self.mouth_id = self.canvas.create_arc(
            sx - mouth_w, mouth_y - mouth_w * 0.6,
            sx + mouth_w, mouth_y + mouth_w * 0.6,
            start=200, extent=140, style=tk.ARC,
            outline="#1E1E2E", width=max(1.5, sr * 0.04),
            tags=("fruit", tag),
        )

        self.items.extend([self.eye_l_id, self.eye_r_id, self.glint_l_id, self.glint_r_id, self.mouth_id])

    def update(
        self,
        x: float,
        y: float,
        angle: float,
        scale: float = 1.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        dt: float = 0.016,
        near_danger: bool = False,
    ) -> None:
        """Updates sprite image rotation, position, wobble factor, and facial reactions."""
        # 1. Update wobble factor
        if self.wobble_elapsed < self.wobble_duration:
            self.wobble_elapsed += dt
            t = self.wobble_elapsed
            decay = math.exp(-t * 9.0)
            wobble_factor = 1.0 + 0.30 * decay * math.sin(t * 26.0)
        else:
            wobble_factor = 1.0

        # 2. Update blinking
        self.blink_timer -= dt
        if self.blink_timer <= 0:
            self.is_blinking = True
            self.blink_elapsed += dt
            if self.blink_elapsed >= self.blink_duration:
                self.is_blinking = False
                self.blink_elapsed = 0.0
                self.blink_timer = random.uniform(2.5, 6.0)

        sx = offset_x + x * scale
        sy = offset_y + y * scale
        sr = self.r * scale * wobble_factor

        # 3. Update Realistic Fruit Sprite (quantized diameter avoids generating dozens of wobble sizes)
        scale_factor = TIER_BODY_SCALE.get(self.tier, 1.12)
        diameter = max(10, int(round(sr * 2.0 * scale_factor / 2.0)) * 2)
        photo = self.sm.get_fruit_sprite(self.tier, diameter, angle)

        if self.image_id and photo:
            self.current_photo = photo
            try:
                self.canvas.coords(self.image_id, sx, sy)
                self.canvas.itemconfig(self.image_id, image=photo)
            except Exception:
                pass
        elif self.body_id:
            try:
                self.canvas.coords(self.body_id, sx - sr, sy - sr, sx + sr, sy + sr)
            except Exception:
                pass

        # 4. Rotate and update cute facial expression
        eye_dist = sr * 0.28
        eye_r = max(2.2, sr * (0.14 if near_danger else 0.09))
        eye_y_offset = sr * (0.04 if self.tier == 1 else -0.02)

        el_x, el_y = rotate_point(sx, sy, sx - eye_dist, sy + eye_y_offset, angle)
        er_x, er_y = rotate_point(sx, sy, sx + eye_dist, sy + eye_y_offset, angle)

        if self.is_blinking and not near_danger:
            slit_h = max(1.0, eye_r * 0.25)
            self.canvas.coords(self.eye_l_id, el_x - eye_r, el_y - slit_h, el_x + eye_r, el_y + slit_h)
            self.canvas.coords(self.eye_r_id, er_x - eye_r, er_y - slit_h, er_x + eye_r, er_y + slit_h)
            self.canvas.itemconfigure(self.glint_l_id, state="hidden")
            self.canvas.itemconfigure(self.glint_r_id, state="hidden")
        else:
            self.canvas.itemconfigure(self.glint_l_id, state="normal")
            self.canvas.itemconfigure(self.glint_r_id, state="normal")
            self.canvas.coords(self.eye_l_id, el_x - eye_r, el_y - eye_r, el_x + eye_r, el_y + eye_r)
            self.canvas.coords(self.eye_r_id, er_x - eye_r, er_y - eye_r, er_x + eye_r, er_y + eye_r)

            glint_r = max(1.0, eye_r * 0.45)
            gl_x, gl_y = rotate_point(sx, sy, sx - eye_dist + glint_r * 0.5, sy + eye_y_offset - glint_r * 0.5, angle)
            gr_x, gr_y = rotate_point(sx, sy, sx + eye_dist + glint_r * 0.5, sy + eye_y_offset - glint_r * 0.5, angle)
            self.canvas.coords(self.glint_l_id, gl_x - glint_r, gl_y - glint_r, gl_x + glint_r, gl_y + glint_r)
            self.canvas.coords(self.glint_r_id, gr_x - glint_r, gr_y - glint_r, gr_x + glint_r, gr_y + glint_r)

        # Cheeks
        if self.cheek_l_id and self.cheek_r_id:
            cheek_dist = sr * 0.44
            cheek_y = sy + sr * 0.12
            cr = max(2.5, sr * 0.12)
            cl_x, cl_y = rotate_point(sx, sy, sx - cheek_dist, cheek_y, angle)
            cr_x, cr_y = rotate_point(sx, sy, sx + cheek_dist, cheek_y, angle)
            self.canvas.coords(self.cheek_l_id, cl_x - cr, cl_y - cr * 0.5, cl_x + cr, cl_y + cr * 0.5)
            self.canvas.coords(self.cheek_r_id, cr_x - cr, cr_y - cr * 0.5, cr_x + cr, cr_y + cr * 0.5)

        # Mouth
        if near_danger:
            m_r = max(2.0, sr * 0.08)
            m_x, m_y = rotate_point(sx, sy, sx, sy + sr * 0.16, angle)
            self.canvas.coords(self.mouth_id, m_x - m_r, m_y - m_r, m_x + m_r, m_y + m_r)
            self.canvas.itemconfig(self.mouth_id, start=0, extent=359, style=tk.ARC, width=max(1.5, sr * 0.04))
        else:
            mouth_w = max(2.5, sr * 0.18)
            mouth_y = sy + sr * 0.16
            m_x, m_y = rotate_point(sx, sy, sx, mouth_y, angle)
            start_deg = (200 - math.degrees(angle)) % 360
            self.canvas.coords(self.mouth_id, m_x - mouth_w, m_y - mouth_w * 0.6, m_x + mouth_w, m_y + mouth_w * 0.6)
            self.canvas.itemconfig(self.mouth_id, start=start_deg, extent=140, style=tk.ARC, width=max(1.5, sr * 0.04))

    def destroy(self) -> None:
        """Removes all canvas items associated with this fruit."""
        for item_id in self.items:
            self.canvas.delete(item_id)
        self.items.clear()
