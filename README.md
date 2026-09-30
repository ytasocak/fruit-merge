# 🍉 Fruit Merge

A fast, responsive, and beautifully crafted 2D physics puzzle game, built in **Python** using **Tkinter** and **Pymunk 2D Physics**.

Set inside a cozy artisan fruit cafe with carved mahogany plaques, realistic fruit sprites, juicy screen effects, and a complete multi-language localization system.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Physics](https://img.shields.io/badge/Physics-Pymunk_7.3-339933)](https://www.pymunk.org/)
[![GUI](https://img.shields.io/badge/GUI-Tkinter-FF6B6B)](https://docs.python.org/3/library/tkinter.html)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Languages](https://img.shields.io/badge/Languages-English%20%7C%20Türkçe-F59E0B)](fruit_merge/i18n.py)

---

## 🎮 Gameplay & Rules

1. **Aim & Drop**: Move the dropper horizontally above the glass container using the mouse or keyboard (`A` / `D` or arrow keys). Click or press `Space` to release the fruit into the vitrine.
2. **Merge Mechanics**: When two identical fruits touch, they collide, burst, and merge into the next higher tier fruit at their contact midpoint, awarding harvest points.
3. **Danger Deadline**: Watch the top red deadline! If fruits stack above the dashed warning line for more than **3 continuous seconds**, the kitchen overflows and the harvest session concludes with the **Game Over** summary screen.
4. **Watermelon Quest**: Progress through 11 evolutionary tiers to unlock the ultimate **Watermelon**. Merging two giant Watermelons grants a massive **5,000 point celebration bonus**!

---

## 🍒 Fruit Evolution Recipe (11 Tiers)

| Tier | Fruit | Emoji | Merge Score |
| :---: | :--- | :---: | :---: |
| **1** | Cherry / Kiraz | 🍒 | +2 |
| **2** | Strawberry / Çilek | 🍓 | +4 |
| **3** | Grape / Üzüm | 🍇 | +8 |
| **4** | Dekopon / Dekopon | 🍊 | +16 |
| **5** | Orange / Portakal | 🍊 | +32 |
| **6** | Apple / Elma | 🍎 | +64 |
| **7** | Pear / Armut | 🍐 | +128 |
| **8** | Peach / Şeftali | 🍑 | +256 |
| **9** | Pineapple / Ananas | 🍍 | +512 |
| **10** | Melon / Kavun | 🍈 | +1024 |
| **11** | Watermelon / Karpuz | 🍉 | +2048 *(Two Watermelons = +5000 Bonus!)* |

---

## ✨ Key Features

- **Cozy Artisan Cafe Theme**: Deep warm atmospheric vitrine background (`assets/background.jpg`), carved mahogany wooden plaques with brass rivets, and photorealistic fruit sprite renders.
- **Pymunk 2D Rigid-Body Physics**: Smooth continuous collision detection, natural rolling, friction, mass-proportional inertia, and zero tunneling or stacking jitter.
- **Juicy Feedback & Game Feel**:
  - Expanding radial shockwaves and colorful particle bursts upon merging.
  - Tier-calibrated camera screen shake trauma on impactful drops and high-tier merges.
  - Floating score indicators with celebratory multipliers (`COMBO x2!`, `SUPER x3!`, `FEVER x4!`).
  - Spring-damper jelly wobble physics upon landing and merging.
- **Animated Emotional Fruits**: Fruits feature facial animations including periodic natural blinking and frightened, trembling expressions when approaching the danger line.
- **Multi-Language (i18n) Support**:
  - Starts in **English** by default.
  - Fully localized in **Turkish (Türkçe)** and **English**.
  - Interactive **Settings Modal** accessible from Start, Pause, Sidebar, or `[O]` key.
  - Dynamic on-the-fly UI switching with zero restart required.
  - Persistent preferences stored in `settings.json`.
- **Zero-Dependency Procedural Audio**: Generates and plays audio chimes, merge sounds, drop thuds, and alert warnings in a non-blocking background worker thread using native Windows PCM audio.
- **Responsive Layout**: Game canvas dynamically scales, maintaining clean pixel sharpness and proportions across any window dimensions.

---

## 🕹️ Controls & Shortcuts

| Action | Mouse | Keyboard |
| :--- | :--- | :--- |
| **Aim Dropper** | Move Mouse Horizontally | `Left` / `Right` or `A` / `D` |
| **Drop Fruit** | Left Click | `Space` or `Down` or `S` |
| **Pause / Resume** | Click Pause Button | `P` |
| **Restart Game** | Click Restart Button | `R` |
| **Settings (Language & Audio)** | Click Settings Button | `O` |
| **Return to Menu** | Click Main Menu Button | `M` (when paused/game over) |
| **Mute / Unmute Audio** | Click Sound Button | `M` (during active play) |
| **Cancel / Close Modal** | — | `Escape` |
| **Fullscreen** | Window Maximize | `F11` |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** (tested on Python 3.10, 3.11, 3.12, 3.13)
- Windows (native audio support via `winsound`)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ytasocak/fruit-merge.git
   cd fruit-merge
   ```

2. **Create and activate a virtual environment** *(recommended)*:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # Windows CMD:
   .venv\Scripts\activate.bat
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   # For development and testing tools:
   pip install -r requirements-dev.txt
   ```

### Launch the Game

Run via direct script:
```bash
python main.py
```
Or execute as a Python module:
```bash
python -m fruit_merge
```

---

## 🧪 Running Automated Tests

The repository includes a comprehensive test suite covering physics simulation, collision merges, tier progressions, high score persistence, headless UI states, i18n localization, and module entry points.

Run all tests via `unittest`:
```bash
python -m unittest discover -s tests -v
```

Expected output:
```text
test_aim_nudge_and_clamping (test_game_integration.TestGameIntegration) ... ok
test_buttons_strictly_required_for_state_transitions (test_game_integration.TestGameIntegration) ... ok
test_combo_streak_and_screen_shake (test_game_integration.TestGameIntegration) ... ok
test_drop_and_cooldown (test_game_integration.TestGameIntegration) ... ok
test_game_over_and_menu_navigation (test_game_integration.TestGameIntegration) ... ok
test_i18n_default_and_language_toggle (test_game_integration.TestGameIntegration) ... ok
test_package_main_module (test_game_integration.TestGameIntegration) ... ok
test_project_paths_exist (test_game_integration.TestGameIntegration) ... ok
...
Ran 26 tests in ~3.7s
OK (26/26 passed)
```

---

## 📁 Project Architecture

```
fruit-merge/
├── assets/
│   ├── background.jpg          # Photorealistic cafe interior wallpaper
│   └── fruits/                 # Transparent PNG sprites for Tiers 1-11
│       ├── tier_1_cherry.png
│       ├── tier_2_strawberry.png
│       └── ...
├── fruit_merge/
│   ├── __init__.py             # Module initialization & version info
│   ├── __main__.py             # Package execution entry point (`python -m fruit_merge`)
│   ├── audio.py                # Multi-threaded procedural audio synthesizer & worker
│   ├── constants.py            # Physics parameters, fruit tiers, colors, geometry
│   ├── fruit.py                # Visual fruit wrapper, wobble animations, blinking faces
│   ├── game.py                 # Core game canvas, state machine, overlay renderer
│   ├── i18n.py                 # Localization singleton, translations dictionary (EN/TR)
│   ├── particles.py            # Shockwaves, juice bursts, floating text, star particles
│   ├── physics.py              # Pymunk rigid body physics, contact listeners, merges
│   ├── sprites.py              # SpriteManager caching, plaque card generators
│   └── ui.py                   # Sidebar panel, evolution guide, score & preview cards
├── tests/
│   ├── test_game_integration.py# End-to-end headless Tkinter GUI & state tests
│   ├── test_physics.py         # Pymunk collision & merge verification tests
│   └── test_progression.py     # Fruit tier radii, drop weights, high score tests
├── .gitattributes              # Line ending normalization & binary handling
├── .gitignore                  # Standard Python, IDE, OS, and local runtime ignore
├── LICENSE                     # MIT Open Source License
├── main.py                     # Desktop launcher entry point with custom app icon
├── pyproject.toml              # Modern PEP 518/621 packaging & metadata configuration
├── README.md                   # Project documentation
├── requirements.txt            # Core runtime dependencies (Pymunk, Pillow)
└── requirements-dev.txt        # Optional developer/testing dependencies
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

