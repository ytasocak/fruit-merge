"""Particle effects, shockwave rings, floating combos, and ambient sparkles for juicy game animations."""

import math
import random
import tkinter as tk
from typing import List, Optional


class JuiceParticle:
    """A single juice droplet emitted during a fruit merge."""

    def __init__(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        color: str,
        radius: float = 4.0,
        scale: float = 1.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.radius = radius
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(80.0, 340.0)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(40.0, 140.0)
        self.gravity = 680.0
        self.max_life = random.randint(18, 32)
        self.life = self.max_life
        self.color = color

        sx = offset_x + x * scale
        sy = offset_y + y * scale
        sr = max(1.0, self.radius * scale)
        self.item_id = canvas.create_oval(
            sx - sr, sy - sr, sx + sr, sy + sr,
            fill=color,
            outline="",
            tags="particle",
        )

    def update(self, dt: float, scale: float = 1.0, offset_x: float = 0.0, offset_y: float = 0.0) -> bool:
        self.life -= 1
        if self.life <= 0:
            self.canvas.delete(self.item_id)
            return False

        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        current_r = max(1.0, self.radius * (self.life / self.max_life))
        sx = offset_x + self.x * scale
        sy = offset_y + self.y * scale
        sr = max(1.0, current_r * scale)
        self.canvas.coords(
            self.item_id,
            sx - sr, sy - sr, sx + sr, sy + sr,
        )
        return True

    def destroy(self) -> None:
        self.canvas.delete(self.item_id)


class ShockwaveRing:
    """An expanding circular neon shockwave ring that pops outward on impact."""

    def __init__(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        initial_radius: float,
        color: str,
        scale: float = 1.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.base_radius = initial_radius
        self.max_life = 16
        self.life = self.max_life
        self.color = color

        sx = offset_x + x * scale
        sy = offset_y + y * scale
        sr = self.base_radius * scale
        self.item_id = canvas.create_oval(
            sx - sr, sy - sr, sx + sr, sy + sr,
            outline=color,
            width=3,
            tags="particle",
        )

    def update(self, dt: float, scale: float = 1.0, offset_x: float = 0.0, offset_y: float = 0.0) -> bool:
        self.life -= 1
        if self.life <= 0:
            self.canvas.delete(self.item_id)
            return False

        progress = 1.0 - (self.life / self.max_life)
        r = self.base_radius * (1.0 + progress * 1.8)
        sx = offset_x + self.x * scale
        sy = offset_y + self.y * scale
        sr = max(1.0, r * scale)
        stroke_w = max(1.0, (1.0 - progress) * 3.5 * scale)

        self.canvas.coords(self.item_id, sx - sr, sy - sr, sx + sr, sy + sr)
        self.canvas.itemconfig(self.item_id, width=stroke_w)
        return True

    def destroy(self) -> None:
        self.canvas.delete(self.item_id)


class FloatingScore:
    """Animated floating score text that drifts upward and fades away."""

    def __init__(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        score: int,
        is_bonus: bool = False,
        scale: float = 1.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.vy = -80.0
        self.max_life = 36
        self.life = self.max_life
        self.is_bonus = is_bonus

        text = f"+{score}" if not is_bonus else f"★ +{score} ★"
        color = "#F59E0B" if is_bonus or score >= 500 else "#F8FAFC"
        self.base_font_size = 17 if is_bonus else (14 if score >= 100 else 12)

        sx = offset_x + x * scale
        sy = offset_y + y * scale
        scaled_size = max(8, int(self.base_font_size * scale))

        self.item_id = canvas.create_text(
            sx, sy,
            text=text,
            fill=color,
            font=("Segoe UI", scaled_size, "bold"),
            tags="particle",
        )

    def update(self, dt: float, scale: float = 1.0, offset_x: float = 0.0, offset_y: float = 0.0) -> bool:
        self.life -= 1
        if self.life <= 0:
            self.canvas.delete(self.item_id)
            return False

        self.vy *= 0.94
        self.y += self.vy * dt
        sx = offset_x + self.x * scale
        sy = offset_y + self.y * scale
        self.canvas.coords(self.item_id, sx, sy)
        return True

    def destroy(self) -> None:
        self.canvas.delete(self.item_id)


class FloatingComboBanner:
    """Juicy pop banner for combo streaks (COMBO x2, SUPER x3, FEVER x4)."""

    def __init__(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        combo: int,
        scale: float = 1.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ):
        self.canvas = canvas
        self.x = x
        self.y = y - 20
        self.vy = -45.0
        self.max_life = 40
        self.life = self.max_life

        if combo >= 4:
            text = f"🔥 FEVER x{combo}! 🔥"
            color = "#F43F5E"
            size = 17
        elif combo == 3:
            text = f"⚡ SUPER x{combo}! ⚡"
            color = "#EC4899"
            size = 15
        else:
            text = f"✨ COMBO x{combo}! ✨"
            color = "#F59E0B"
            size = 14

        self.base_font_size = size
        sx = offset_x + self.x * scale
        sy = offset_y + self.y * scale
        scaled_size = max(9, int(size * scale))

        self.item_id = canvas.create_text(
            sx, sy,
            text=text,
            fill=color,
            font=("Segoe UI", scaled_size, "bold"),
            tags="particle",
        )

    def update(self, dt: float, scale: float = 1.0, offset_x: float = 0.0, offset_y: float = 0.0) -> bool:
        self.life -= 1
        if self.life <= 0:
            self.canvas.delete(self.item_id)
            return False

        self.vy *= 0.95
        self.y += self.vy * dt
        sx = offset_x + self.x * scale
        sy = offset_y + self.y * scale
        self.canvas.coords(self.item_id, sx, sy)
        return True

    def destroy(self) -> None:
        self.canvas.delete(self.item_id)


class AmbientSparkle:
    """Subtle glowing star particles floating in the game container background."""

    def __init__(self, canvas: tk.Canvas, bounds: tuple[float, float, float, float]):
        self.canvas = canvas
        left, top, right, bottom = bounds
        self.bounds = bounds
        self.x = random.uniform(left + 20, right - 20)
        self.y = random.uniform(top + 20, bottom - 20)
        self.vy = -random.uniform(12.0, 30.0)
        self.vx = random.uniform(-6.0, 6.0)
        self.max_radius = random.uniform(1.2, 2.4)
        self.phase = random.uniform(0, math.pi * 2)

        colors = ["#7C3AED", "#A78BFA", "#EC4899", "#F59E0B", "#38BDF8"]
        self.color = random.choice(colors)

        self.item_id = canvas.create_oval(
            self.x, self.y, self.x + 1, self.y + 1,
            fill=self.color,
            outline="",
            tags="ambient_sparkle",
        )

    def update(self, dt: float, scale: float = 1.0, offset_x: float = 0.0, offset_y: float = 0.0) -> bool:
        self.phase += dt * 3.0
        self.y += self.vy * dt
        self.x += self.vx * dt

        left, top, right, bottom = self.bounds
        if self.y < top + 10:
            self.y = bottom - 15
            self.x = random.uniform(left + 20, right - 20)

        r = self.max_radius * (0.6 + 0.4 * math.sin(self.phase))
        sx = offset_x + self.x * scale
        sy = offset_y + self.y * scale
        sr = max(0.8, r * scale)

        self.canvas.coords(self.item_id, sx - sr, sy - sr, sx + sr, sy + sr)
        return True

    def destroy(self) -> None:
        self.canvas.delete(self.item_id)


class ParticleManager:
    """Manages all active particles, shockwaves, combo banners, and ambient sparkles."""

    def __init__(self):
        self.particles: List[JuiceParticle] = []
        self.shockwaves: List[ShockwaveRing] = []
        self.scores: List[FloatingScore] = []
        self.combos: List[FloatingComboBanner] = []
        self.ambient: List[AmbientSparkle] = []

    def init_ambient(self, canvas: tk.Canvas, bounds: tuple[float, float, float, float], count: int = 15) -> None:
        """Initializes soft ambient background motes."""
        self.clear_ambient()
        for _ in range(count):
            self.ambient.append(AmbientSparkle(canvas, bounds))

    def clear_ambient(self) -> None:
        for a in self.ambient:
            a.destroy()
        self.ambient.clear()

    def spawn_merge_burst(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        color: str,
        highlight_color: str,
        radius: float = 24.0,
        count: int = 12,
        scale: float = 1.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ) -> None:
        """Spawns an explosive burst of juice droplets and expanding shockwave ring at (x, y)."""
        # Shockwave ring (capped at 4)
        while len(self.shockwaves) >= 4:
            old = self.shockwaves.pop(0)
            old.destroy()
        self.shockwaves.append(
            ShockwaveRing(canvas, x, y, radius, highlight_color, scale=scale, offset_x=offset_x, offset_y=offset_y)
        )
        # Droplets (capped at 40 active droplets for peak performance)
        actual_count = min(count, max(0, 40 - len(self.particles)))
        for _ in range(actual_count):
            c = color if random.random() > 0.3 else highlight_color
            r = random.uniform(2.5, 5.0)
            self.particles.append(
                JuiceParticle(canvas, x, y, c, r, scale=scale, offset_x=offset_x, offset_y=offset_y)
            )

    def spawn_floating_score(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        score: int,
        is_bonus: bool = False,
        scale: float = 1.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ) -> None:
        # Capped at 5 active floating scores
        while len(self.scores) >= 5:
            old = self.scores.pop(0)
            old.destroy()
        self.scores.append(
            FloatingScore(canvas, x, y, score, is_bonus, scale=scale, offset_x=offset_x, offset_y=offset_y)
        )

    def spawn_combo(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        combo: int,
        scale: float = 1.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
    ) -> None:
        # Replace previous combo banner with the newest, highest multiplier to avoid text stacking
        for c in self.combos:
            c.destroy()
        self.combos.clear()
        self.combos.append(
            FloatingComboBanner(canvas, x, y, combo, scale=scale, offset_x=offset_x, offset_y=offset_y)
        )

    def update(self, dt: float, scale: float = 1.0, offset_x: float = 0.0, offset_y: float = 0.0) -> None:
        self.particles = [p for p in self.particles if p.update(dt, scale, offset_x, offset_y)]
        self.shockwaves = [w for w in self.shockwaves if w.update(dt, scale, offset_x, offset_y)]
        self.scores = [s for s in self.scores if s.update(dt, scale, offset_x, offset_y)]
        self.combos = [c for c in self.combos if c.update(dt, scale, offset_x, offset_y)]
        for a in self.ambient:
            a.update(dt, scale, offset_x, offset_y)

    def clear(self) -> None:
        for p in self.particles:
            p.destroy()
        self.particles.clear()
        for w in self.shockwaves:
            w.destroy()
        self.shockwaves.clear()
        for s in self.scores:
            s.destroy()
        self.scores.clear()
        for c in self.combos:
            c.destroy()
        self.combos.clear()
