"""Game constants, fruit tier specifications, colors, and layout settings."""

import os
from dataclasses import dataclass
from typing import Tuple, List, Dict


@dataclass(frozen=True)
class FruitConfig:
    tier: int
    name: str
    radius: float
    mass: float
    score: int
    color: str
    highlight_color: str
    dark_color: str
    feature_color: str  # For stem, seeds, or stripes


# Window & Layout dimensions
WINDOW_TITLE = "Fruit Merge"
CANVAS_WIDTH = 460
CANVAS_HEIGHT = 650
SIDEBAR_WIDTH = 260
WINDOW_WIDTH = CANVAS_WIDTH + SIDEBAR_WIDTH + 30
WINDOW_HEIGHT = 680

# Playfield coordinates (Container inside Canvas)
CONTAINER_LEFT = 35
CONTAINER_RIGHT = CANVAS_WIDTH - 35  # 425 -> 390px inner width
CONTAINER_BOTTOM = CANVAS_HEIGHT - 35
CONTAINER_TOP = 130             # Glass jar top mouth rim (sits below hanging cafe sign)
WALL_THICKNESS = 16
CORNER_RADIUS = 20

# Drop & Danger settings
DROP_Y = 65
DANGER_Y = 145                 # Danger overflow line inside container
DANGER_TRIGGER_SECONDS = 3.0
DROP_COOLDOWN_MS = 550

# Physics constants
PHYSICS_FPS = 60
PHYSICS_SUBSTEPS = 2
GRAVITY = 1400.0
DEFAULT_ELASTICITY = 0.22
DEFAULT_FRICTION = 0.55
WALL_SIDE_ELASTICITY = 0.0      # Zero rebound on container side walls prevents ricocheting across the jar
WALL_FLOOR_ELASTICITY = 0.08    # Soft landing on the floor
WALL_FRICTION = 0.85            # High wall friction prevents erratic sliding and absorbs drop kinetic energy
COLLISION_TYPE_FRUIT = 1
COLLISION_TYPE_WALL = 2

# Visual Theme Colors (Warm Magic Fruit Cafe & Kitchen Palette)
BG_COLOR = "#120D0A"           # Deep warm roasted coffee
SIDEBAR_BG = "#1A130E"         # Deep dark mahogany wood sidebar
CARD_BG = "#261C14"            # Warm artisan wood plaque card
CARD_BORDER = "#483626"        # Polished walnut frame border
CARD_HOVER = "#34261C"         # Warm ambient highlight
CONTAINER_BG = "#160F0A"       # Warm-tinted crystal glass interior
CONTAINER_WALL_GLOW = "#78350F"# Warm amber wood glow
CONTAINER_WALL_CORE = "#B45309"# Polished brass / golden bronze trim
CONTAINER_WALL_SHINE = "#FDE68A"# Warm specular candlelight reflection
TEXT_PRIMARY = "#FFFBEB"       # Warm cream ivory
TEXT_MUTED = "#B8A28E"         # Warm soft sepia
TEXT_ACCENT = "#F59E0B"        # Radiant amber gold
CAFE_GOLD = "#D97706"          # Golden honey
DANGER_LINE_COLOR = "#E11D48"  # Warm crimson-rose warning line (harmonized with cafe palette)
DANGER_BG_COLOR = "#2A0E12"    # Deep dark warm hazard tint
GUIDE_LINE_COLOR = "#F59E0B"   # Radiant amber gold dashed aim guide
NEON_PINK = "#F43F5E"          # Accent rose
NEON_CYAN = "#06B6D4"          # Accent cyan
NEON_GREEN = "#10B981"         # Mint emerald

COMBO_TIMEOUT_SECONDS = 2.4    # Max seconds between merges to maintain combo streak

# Fruit Evolution Tiers (1 to 11)
FRUIT_TIERS: Dict[int, FruitConfig] = {
    1: FruitConfig(
        tier=1,
        name="Cherry",
        radius=16.0,
        mass=1.0,
        score=2,
        color="#E53935",
        highlight_color="#FF8A80",
        dark_color="#B71C1C",
        feature_color="#33691E",  # green stem
    ),
    2: FruitConfig(
        tier=2,
        name="Strawberry",
        radius=22.0,
        mass=1.8,
        score=4,
        color="#FF2A6D",
        highlight_color="#FFA0B8",
        dark_color="#C2185B",
        feature_color="#4CAF50",  # leaf cap
    ),
    3: FruitConfig(
        tier=3,
        name="Grape",
        radius=29.0,
        mass=3.0,
        score=8,
        color="#8E24AA",
        highlight_color="#CE93D8",
        dark_color="#4A148C",
        feature_color="#6A1B9A",
    ),
    4: FruitConfig(
        tier=4,
        name="Dekopon",
        radius=37.0,
        mass=4.8,
        score=16,
        color="#FB8C00",
        highlight_color="#FFE082",
        dark_color="#E65100",
        feature_color="#2E7D32",  # top knot
    ),
    5: FruitConfig(
        tier=5,
        name="Orange",
        radius=46.0,
        mass=7.0,
        score=32,
        color="#FF5722",
        highlight_color="#FFAB91",
        dark_color="#BF360C",
        feature_color="#388E3C",
    ),
    6: FruitConfig(
        tier=6,
        name="Apple",
        radius=56.0,
        mass=10.0,
        score=64,
        color="#D32F2F",
        highlight_color="#EF9A9A",
        dark_color="#8B0000",
        feature_color="#4E342E",  # brown stem
    ),
    7: FruitConfig(
        tier=7,
        name="Pear",
        radius=67.0,
        mass=14.0,
        score=128,
        color="#AFB42B",
        highlight_color="#E6EE9C",
        dark_color="#827717",
        feature_color="#5D4037",
    ),
    8: FruitConfig(
        tier=8,
        name="Peach",
        radius=78.0,
        mass=19.0,
        score=256,
        color="#FF7043",
        highlight_color="#FFCCBC",
        dark_color="#D84315",
        feature_color="#2E7D32",
    ),
    9: FruitConfig(
        tier=9,
        name="Pineapple",
        radius=90.0,
        mass=25.0,
        score=512,
        color="#FBC02D",
        highlight_color="#FFF59D",
        dark_color="#F57F17",
        feature_color="#2E7D32",  # green crown
    ),
    10: FruitConfig(
        tier=10,
        name="Melon",
        radius=103.0,
        mass=32.0,
        score=1024,
        color="#7CB342",
        highlight_color="#C5E1A5",
        dark_color="#33691E",
        feature_color="#558B2F",
    ),
    11: FruitConfig(
        tier=11,
        name="Watermelon",
        radius=118.0,
        mass=42.0,
        score=2048,
        color="#2E7D32",
        highlight_color="#81C784",
        dark_color="#1B5E20",
        feature_color="#1B5E20",  # dark green stripes
    ),
}

MAX_TIER = 11

# Multipliers to scale sprite rendering so the visible fruit body diameter exactly matches the physics circle (2 * r)
# Guarantees zero visible gap when two fruits rest or collide against each other!
TIER_BODY_SCALE: Dict[int, float] = {
    1: 1.22,   # Cherry
    2: 1.12,   # Strawberry
    3: 1.17,   # Grape
    4: 1.10,   # Dekopon
    5: 1.14,   # Orange
    6: 1.18,   # Apple
    7: 1.13,   # Pear
    8: 1.10,   # Peach
    9: 1.20,   # Pineapple
    10: 1.08,  # Melon
    11: 1.14,  # Watermelon
}

# Drop pool tiers & weighted probabilities
DROP_TIERS: List[int] = [1, 2, 3, 4, 5]
DROP_WEIGHTS: List[float] = [0.38, 0.28, 0.18, 0.11, 0.05]

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIGH_SCORE_FILE = os.path.join(PROJECT_ROOT, "highscore.json")
