"""High-performance sprite management, rotation caching, and glass container compositing."""

import math
import os
from collections import OrderedDict
from typing import Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFilter, ImageTk

from fruit_merge.constants import (
    CONTAINER_BOTTOM,
    CONTAINER_LEFT,
    CONTAINER_RIGHT,
    CONTAINER_TOP,
    FRUIT_TIERS,
)

import tkinter as tk

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
FRUITS_DIR = os.path.join(ASSETS_DIR, "fruits")
BG_PATH = os.path.join(ASSETS_DIR, "background.jpg")

FRUIT_FILENAMES = {
    1: "tier_1_cherry.png",
    2: "tier_2_strawberry.png",
    3: "tier_3_grape.png",
    4: "tier_4_dekopon.png",
    5: "tier_5_orange.png",
    6: "tier_6_apple.png",
    7: "tier_7_pear.png",
    8: "tier_8_peach.png",
    9: "tier_9_pineapple.png",
    10: "tier_10_melon.png",
    11: "tier_11_watermelon.png",
}


class SpriteManager:
    """Loads, scales, rotates, and caches realistic fruit sprites and composite backgrounds."""

    _instance: Optional["SpriteManager"] = None

    @classmethod
    def get_instance(cls) -> "SpriteManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.raw_fruits: Dict[int, Image.Image] = {}
        self.raw_bg: Optional[Image.Image] = None
        self._sprite_cache: OrderedDict[Tuple[int, int, int], ImageTk.PhotoImage] = OrderedDict()
        self._bg_cache: Dict[Tuple[int, int, int, int, int], ImageTk.PhotoImage] = {}
        self._plaque_cache: Dict[Tuple[int, int, Tuple[int, int, int], Tuple[int, int, int]], ImageTk.PhotoImage] = {}
        self._cached_master: Optional[tk.Misc] = None

        self.load_assets()

    def _get_active_master(self, master: Optional[tk.Misc] = None) -> Optional[tk.Misc]:
        """Resolves the currently active Tk master window, validating its existence."""
        candidate = master or getattr(tk, "_default_root", None)
        if candidate is not None:
            try:
                if candidate.winfo_exists():
                    return candidate
            except Exception:
                pass
        return None

    def _validate_master_cache(self, master: Optional[tk.Misc] = None) -> Optional[tk.Misc]:
        """Invalidates PhotoImage caches if the Tk master/interpreter has changed or been destroyed."""
        active = self._get_active_master(master)
        if active != self._cached_master:
            self.clear_cache()
            self._cached_master = active
        return active

    def load_assets(self) -> None:
        """Loads fruit textures and wallpaper background."""
        for tier, filename in FRUIT_FILENAMES.items():
            path = os.path.join(FRUITS_DIR, filename)
            if os.path.exists(path):
                try:
                    img = Image.open(path).convert("RGBA")
                    self.raw_fruits[tier] = img
                except Exception as e:
                    print(f"Error loading {path}: {e}")

        if os.path.exists(BG_PATH):
            try:
                self.raw_bg = Image.open(BG_PATH).convert("RGBA")
            except Exception as e:
                print(f"Error loading background {BG_PATH}: {e}")

    def clear_cache(self) -> None:
        self._sprite_cache.clear()
        self._bg_cache.clear()
        self._plaque_cache.clear()

    def get_plaque_card(
        self,
        width: int,
        height: int,
        border_color: Tuple[int, int, int] = (217, 119, 6),
        fill_color: Tuple[int, int, int] = (42, 28, 18),
        master: Optional[tk.Misc] = None,
    ) -> Optional[ImageTk.PhotoImage]:
        """Generates a high-quality artisan wooden plaque card with drop shadow and brass rivets."""
        active_master = self._validate_master_cache(master)

        w = max(50, int(width))
        h = max(50, int(height))
        cache_key = (w, h, border_color, fill_color)
        if cache_key in self._plaque_cache:
            return self._plaque_cache[cache_key]

        pad = 16
        img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))

        # Soft blurred drop shadow
        shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow)
        sdraw.rounded_rectangle([0, 0, w - 1, h - 1], radius=18, fill=(0, 0, 0, 160))
        shadow_blur = shadow.filter(ImageFilter.GaussianBlur(8))
        img.paste(shadow_blur, (pad, pad + 6), shadow_blur)

        # Plaque body with rich wood border
        pdraw = ImageDraw.Draw(img)
        x1, y1, x2, y2 = pad, pad, pad + w - 1, pad + h - 1
        pdraw.rounded_rectangle([x1, y1, x2, y2], radius=18, fill=(*fill_color, 252), outline=(28, 18, 10, 255), width=3)
        pdraw.rounded_rectangle([x1 + 3, y1 + 3, x2 - 3, y2 - 3], radius=15, outline=(*border_color, 240), width=2)
        pdraw.rounded_rectangle([x1 + 6, y1 + 6, x2 - 6, y2 - 6], radius=12, outline=(253, 230, 138, 90), width=1)

        # 4 golden brass rivets in corners
        rivet_dist = 14
        rivet_r = 3
        for rx, ry in [
            (x1 + rivet_dist, y1 + rivet_dist),
            (x2 - rivet_dist, y1 + rivet_dist),
            (x1 + rivet_dist, y2 - rivet_dist),
            (x2 - rivet_dist, y2 - rivet_dist),
        ]:
            pdraw.ellipse([rx - rivet_r, ry - rivet_r, rx + rivet_r, ry + rivet_r], fill=(217, 119, 6, 255), outline=(253, 230, 138, 255), width=1)

        try:
            photo = ImageTk.PhotoImage(img, master=active_master)
            self._plaque_cache[cache_key] = photo
            return photo
        except Exception:
            return None

    def get_fruit_sprite(
        self, tier: int, diameter: int, angle_rad: float = 0.0, master: Optional[tk.Misc] = None
    ) -> Optional[ImageTk.PhotoImage]:
        """Returns a cached, rotated, and scaled PhotoImage for the specified fruit tier."""
        if tier not in self.raw_fruits:
            return None

        active_master = self._validate_master_cache(master)

        diameter = max(10, int(diameter))
        # Quantize angle to 6-degree increments (60 angles max per size) for high cache hit rate
        angle_deg = int(round(math.degrees(angle_rad) % 360 / 6)) * 6

        cache_key = (tier, diameter, angle_deg)
        if cache_key in self._sprite_cache:
            self._sprite_cache.move_to_end(cache_key)
            return self._sprite_cache[cache_key]

        # Prevent unbounded cache growth using LRU eviction without destroying active sprites
        while len(self._sprite_cache) > 2000:
            self._sprite_cache.popitem(last=False)

        base = self.raw_fruits[tier]
        scaled = base.resize((diameter, diameter), Image.Resampling.BILINEAR)
        if angle_deg != 0:
            rotated = scaled.rotate(-angle_deg, resample=Image.Resampling.BILINEAR)
        else:
            rotated = scaled

        try:
            photo = ImageTk.PhotoImage(rotated, master=active_master)
            self._sprite_cache[cache_key] = photo
            return photo
        except Exception:
            return None

    def get_background_composite(
        self, width: int, height: int, scale: float, offset_x: float, offset_y: float, master: Optional[tk.Misc] = None
    ) -> Optional[ImageTk.PhotoImage]:
        """Composites the atmospheric background with the crystal glass container overlay."""
        if not self.raw_bg:
            return None

        active_master = self._validate_master_cache(master)

        width = max(100, int(width))
        height = max(100, int(height))
        s_int = int(scale * 100)
        ox_int = int(offset_x)
        oy_int = int(offset_y)

        cache_key = (width, height, s_int, ox_int, oy_int)
        if cache_key in self._bg_cache:
            return self._bg_cache[cache_key]

        # Clear stale background renders
        self._bg_cache.clear()

        # 1. Aspect Fill: dynamic center crop focused on the cafe counter & sign,
        # completely cutting out the cluttered left shelf with conflicting jars/colors
        bg_w, bg_h = self.raw_bg.size
        target_aspect = width / height
        bg_aspect = bg_w / bg_h

        if target_aspect < bg_aspect:
            # Viewport is narrower/taller than background image (portrait)
            crop_w = int(bg_h * target_aspect)
            # Center on cafe counter & sign (cx ≈ 0.62 * bg_w), avoiding the left shelf
            cx = int(bg_w * 0.62)
            left = max(0, min(bg_w - crop_w, cx - crop_w // 2))
            crop_rect = (left, 0, left + crop_w, bg_h)
            cropped_bg = self.raw_bg.crop(crop_rect)
        else:
            # Viewport is wider than background image
            crop_h = int(bg_w / target_aspect)
            cy = bg_h // 2
            top = max(0, min(bg_h - crop_h, cy - crop_h // 2))
            crop_rect = (0, top, bg_w, top + crop_h)
            cropped_bg = self.raw_bg.crop(crop_rect)

        bg_scaled = cropped_bg.resize((width, height), Image.Resampling.BILINEAR)

        # 2. Render artisan crystal glass container overlay
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        cx1 = int(offset_x + CONTAINER_LEFT * scale)
        cy1 = int(offset_y + CONTAINER_TOP * scale)
        cx2 = int(offset_x + CONTAINER_RIGHT * scale)
        cy2 = int(offset_y + CONTAINER_BOTTOM * scale)
        corner_r = int(20 * scale)

        # 2a. Heavy antique mahogany & brass pedestal stand at base
        pedestal_h = int(12 * scale)
        draw.rounded_rectangle(
            [cx1 - int(6 * scale), cy2 - int(2 * scale), cx2 + int(6 * scale), cy2 + pedestal_h],
            radius=int(6 * scale),
            fill=(45, 30, 20, 235),
            outline=(180, 130, 45, 230),
            width=max(1, int(2 * scale)),
        )
        # Golden brass base trim highlight
        draw.line(
            [(cx1 - int(3 * scale), cy2), (cx2 + int(3 * scale), cy2)],
            fill=(245, 205, 120, 200),
            width=max(1, int(2 * scale)),
        )

        # 2b. Dark smoky espresso glass interior: deeply darkened for high contrast fruit pop
        # Uniformly dark with zero light streaks or discoloration on the left side
        draw.rounded_rectangle([cx1, cy1, cx2, cy2], radius=corner_r, fill=(10, 7, 5, 210))

        # 2d. Polished antique brass / amber glowing glass border
        glow_w = max(2, int(3.5 * scale))
        draw.rounded_rectangle(
            [cx1, cy1, cx2, cy2],
            radius=corner_r,
            outline=(205, 150, 50, 220),
            width=glow_w,
        )

        # 2e. Inner candlelight specular reflection on glass rim
        draw.rounded_rectangle(
            [cx1 + 2, cy1 + 2, cx2 - 2, cy2 - 2],
            radius=max(1, corner_r - 2),
            outline=(255, 245, 215, 75),
            width=1,
        )

        # 2f. Top dispenser brass collar rim
        collar_h = int(6 * scale)
        draw.rounded_rectangle(
            [cx1 - int(4 * scale), cy1 - collar_h, cx2 + int(4 * scale), cy1 + int(2 * scale)],
            radius=int(4 * scale),
            fill=(60, 42, 28, 225),
            outline=(225, 175, 65, 240),
            width=max(1, int(2 * scale)),
        )

        # Composite together
        composite = Image.alpha_composite(bg_scaled, overlay)
        try:
            photo = ImageTk.PhotoImage(composite, master=active_master)
            self._bg_cache[cache_key] = photo
            return photo
        except Exception:
            self.clear_cache()
            try:
                photo = ImageTk.PhotoImage(composite, master=active_master)
                self._bg_cache[cache_key] = photo
                return photo
            except Exception:
                return None
