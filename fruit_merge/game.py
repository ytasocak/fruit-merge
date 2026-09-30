"""Main Fruit Merge game loop, canvas rendering, input handling, and state machine."""

import math
import random
import time
import tkinter as tk
from typing import Callable, Dict, List, Optional, Tuple
from PIL import ImageTk

from fruit_merge.audio import AudioManager
from fruit_merge.constants import (
    BG_COLOR,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    COMBO_TIMEOUT_SECONDS,
    CONTAINER_BG,
    CONTAINER_BOTTOM,
    CONTAINER_LEFT,
    CONTAINER_RIGHT,
    CONTAINER_TOP,
    CONTAINER_WALL_CORE,
    CONTAINER_WALL_GLOW,
    CONTAINER_WALL_SHINE,
    DANGER_LINE_COLOR,
    DANGER_TRIGGER_SECONDS,
    DANGER_Y,
    DROP_COOLDOWN_MS,
    DROP_TIERS,
    DROP_WEIGHTS,
    DROP_Y,
    FRUIT_TIERS,
    GUIDE_LINE_COLOR,
    NEON_CYAN,
    NEON_PINK,
    TEXT_ACCENT,
    TEXT_MUTED,
    TIER_BODY_SCALE,
    WALL_THICKNESS,
    FruitConfig,
)
from fruit_merge.fruit import FruitVisual
from fruit_merge.i18n import I18n, get_fruit_name, t
from fruit_merge.particles import ParticleManager
from fruit_merge.physics import MergeEvent, PhysicsManager
from fruit_merge.sprites import SpriteManager
from fruit_merge.ui import SidebarPanel


class GameState:
    START = "start"
    AIMING = "aiming"
    COOLDOWN = "cooldown"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    SETTINGS = "settings"


class FruitMergeGame(tk.Frame):
    """Core game canvas, physics coordinator, and input handler with rich arcade animations."""

    def __init__(self, master: tk.Tk, start_in_menu: bool = True, **kwargs):
        super().__init__(master, bg=BG_COLOR, **kwargs)
        self.master = master
        self.sm = SpriteManager.get_instance()
        self.current_bg_photo = None

        # Dynamic viewport scaling & centering
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.render_offset_x = 0.0
        self.render_offset_y = 0.0

        # Screen shake / impact juice
        self.shake_trauma = 0.0

        # Combo streak system
        self.combo_count = 0
        self.last_merge_time = 0.0

        # Game state variables
        self.state = GameState.START if start_in_menu else GameState.AIMING
        self.score = 0
        self.high_score = SidebarPanel.load_high_score()
        self.is_new_high_score = False

        # Session tracking statistics
        self.highest_tier_reached = 1
        self.total_merges = 0
        self.max_combo = 0

        # Settings state
        self._settings_return_state: str = GameState.START

        # Physics & audio managers
        self.physics = PhysicsManager()
        self.audio = AudioManager(enabled=True)
        self.particles = ParticleManager()

        # Active visual representations mapped by fruit_id
        self.visuals: Dict[int, FruitVisual] = {}

        # Dropper state
        self.current_tier = self._pick_drop_fruit()
        self.next_tier = self._pick_drop_fruit()
        self.aim_x = (CONTAINER_LEFT + CONTAINER_RIGHT) / 2.0
        self.last_drop_time = 0.0

        # Danger line & countdown state
        self.danger_timer = 0.0
        self.pulse_phase = 0.0

        # Overlay graphics & image reference holders
        self.overlay_items: list[int] = []
        self._overlay_photos: list[ImageTk.PhotoImage] = []
        self._button_clicked_this_event: bool = False

        # Build UI layout & canvas
        self._build_layout()
        self._bind_inputs()

        # Show initial start screen if in menu
        if self.state == GameState.START:
            self._show_start_overlay()

        # Start game loop
        self._last_frame_time = time.perf_counter()
        self._loop_job: Optional[str] = None
        self._cooldown_job: Optional[str] = None
        self._running = True
        self._game_loop()

    def _build_layout(self) -> None:
        self.pack(fill=tk.BOTH, expand=True)

        # Left / Center: Resizable Game Canvas
        self.canvas = tk.Canvas(
            self,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg=BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 5), pady=10)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Right: Sidebar panel (stays docked right, fill Y)
        self.sidebar = SidebarPanel(
            self,
            on_restart=self.restart,
            on_toggle_pause=self.toggle_pause,
            on_toggle_sound=self.toggle_sound,
            on_open_settings=self.open_settings,
        )
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 10), pady=10)
        self.sidebar.update_next_preview(self.next_tier)
        self.sidebar.set_high_score(self.high_score)

        # Draw ambient background particles
        self.particles.init_ambient(
            self.canvas,
            (CONTAINER_LEFT, CONTAINER_TOP, CONTAINER_RIGHT, CONTAINER_BOTTOM),
            count=18,
        )

        # Draw static container walls and danger line
        self._draw_static_elements()

        # Dropper aim elements (guide line and preview fruit)
        self.aim_photo: Optional[tk.PhotoImage] = None
        self._init_dropper_graphics()

    def _on_canvas_configure(self, event: tk.Event) -> None:
        """Dynamically adjusts viewport scale and centering when the canvas is resized."""
        if event.width <= 20 or event.height <= 20:
            return

        scale_x = event.width / CANVAS_WIDTH
        scale_y = event.height / CANVAS_HEIGHT
        self.scale = min(scale_x, scale_y)
        self.offset_x = (event.width - CANVAS_WIDTH * self.scale) / 2.0
        self.offset_y = (event.height - CANVAS_HEIGHT * self.scale) / 2.0
        self.render_offset_x = self.offset_x
        self.render_offset_y = self.offset_y

        # Render composite atmospheric background with glass container
        bg_photo = self.sm.get_background_composite(
            event.width, event.height, self.scale, self.offset_x, self.offset_y
        )
        if bg_photo:
            self.current_bg_photo = bg_photo
            self.canvas.itemconfig(self.bg_image_id, image=bg_photo)
            self.canvas.coords(self.bg_image_id, 0, 0)
            self.canvas.tag_lower(self.bg_image_id)

        self._update_static_elements()
        self._update_dropper_graphics()

        if self.state == GameState.START:
            self._show_start_overlay()
        elif self.state == GameState.GAME_OVER:
            self._show_game_over_overlay()
        elif self.state == GameState.PAUSED:
            self._show_pause_overlay()
        elif self.state == GameState.SETTINGS:
            self._show_settings_overlay()

    def _draw_static_elements(self) -> None:
        # Background wallpaper image
        self.bg_image_id = self.canvas.create_image(0, 0, anchor="nw", tags="background_image")

        # Fallback glass playfield container background
        self.bg_box_id = self.canvas.create_rectangle(
            CONTAINER_LEFT, CONTAINER_TOP, CONTAINER_RIGHT, CONTAINER_BOTTOM,
            fill="", outline="", tags="background"
        )

        # Container walls: layered with outer neon glow and core
        self.wall_glow_left = self.canvas.create_line(0, 0, 0, 0, fill=CONTAINER_WALL_GLOW, tags="wall")
        self.wall_glow_right = self.canvas.create_line(0, 0, 0, 0, fill=CONTAINER_WALL_GLOW, tags="wall")
        self.wall_glow_bot = self.canvas.create_line(0, 0, 0, 0, fill=CONTAINER_WALL_GLOW, tags="wall")

        self.left_wall_id = self.canvas.create_line(0, 0, 0, 0, fill=CONTAINER_WALL_CORE, capstyle=tk.ROUND, tags="wall")
        self.right_wall_id = self.canvas.create_line(0, 0, 0, 0, fill=CONTAINER_WALL_CORE, capstyle=tk.ROUND, tags="wall")
        self.bottom_wall_id = self.canvas.create_line(0, 0, 0, 0, fill=CONTAINER_WALL_CORE, capstyle=tk.ROUND, tags="wall")

        # Top shine trim
        self.wall_shine_bot = self.canvas.create_line(0, 0, 0, 0, fill=CONTAINER_WALL_SHINE, tags="wall")

        # Danger line (dashed line near top)
        self.danger_line_id = self.canvas.create_line(
            CONTAINER_LEFT + 5, DANGER_Y, CONTAINER_RIGHT - 5, DANGER_Y,
            fill="#F43F5E", width=2, dash=(6, 4), tags="danger_line"
        )
        self.danger_text_id = self.canvas.create_text(
            (CONTAINER_LEFT + CONTAINER_RIGHT) / 2.0, DANGER_Y - 14,
            text="", fill="#F43F5E", font=("Segoe UI", 9, "bold"), tags="danger_text"
        )

        self._update_static_elements()

    def _update_static_elements(self) -> None:
        """Repositions and scales container boundaries to match current viewport and camera shake."""
        s = self.scale
        ox = self.render_offset_x
        oy = self.render_offset_y
        w_thick = max(4.0, WALL_THICKNESS * s)
        glow_thick = w_thick + 6.0 * s

        # When photorealistic background with glass vitrine is active, hide flat wall bars
        wall_state = "hidden" if self.current_bg_photo else "normal"

        # Outer glow lines
        self.canvas.coords(self.wall_glow_left, ox + CONTAINER_LEFT * s, oy + CONTAINER_TOP * s, ox + CONTAINER_LEFT * s, oy + CONTAINER_BOTTOM * s)
        self.canvas.itemconfig(self.wall_glow_left, width=glow_thick, state=wall_state)

        self.canvas.coords(self.wall_glow_right, ox + CONTAINER_RIGHT * s, oy + CONTAINER_TOP * s, ox + CONTAINER_RIGHT * s, oy + CONTAINER_BOTTOM * s)
        self.canvas.itemconfig(self.wall_glow_right, width=glow_thick, state=wall_state)

        self.canvas.coords(self.wall_glow_bot, ox + CONTAINER_LEFT * s, oy + CONTAINER_BOTTOM * s, ox + CONTAINER_RIGHT * s, oy + CONTAINER_BOTTOM * s)
        self.canvas.itemconfig(self.wall_glow_bot, width=glow_thick, state=wall_state)

        # Core walls
        self.canvas.coords(self.left_wall_id, ox + CONTAINER_LEFT * s, oy + CONTAINER_TOP * s, ox + CONTAINER_LEFT * s, oy + CONTAINER_BOTTOM * s)
        self.canvas.itemconfig(self.left_wall_id, width=w_thick, state=wall_state)

        self.canvas.coords(self.right_wall_id, ox + CONTAINER_RIGHT * s, oy + CONTAINER_TOP * s, ox + CONTAINER_RIGHT * s, oy + CONTAINER_BOTTOM * s)
        self.canvas.itemconfig(self.right_wall_id, width=w_thick, state=wall_state)

        self.canvas.coords(self.bottom_wall_id, ox + CONTAINER_LEFT * s, oy + CONTAINER_BOTTOM * s, ox + CONTAINER_RIGHT * s, oy + CONTAINER_BOTTOM * s)
        self.canvas.itemconfig(self.bottom_wall_id, width=w_thick, state=wall_state)

        # Shine line
        self.canvas.coords(self.wall_shine_bot, ox + (CONTAINER_LEFT + 8) * s, oy + (CONTAINER_BOTTOM - 2) * s, ox + (CONTAINER_RIGHT - 8) * s, oy + (CONTAINER_BOTTOM - 2) * s)
        self.canvas.itemconfig(self.wall_shine_bot, width=max(1.0, 1.5 * s), state=wall_state)

        # Danger line (warm styled warning line)
        self.canvas.coords(
            self.danger_line_id,
            ox + (CONTAINER_LEFT + 5) * s, oy + DANGER_Y * s,
            ox + (CONTAINER_RIGHT - 5) * s, oy + DANGER_Y * s,
        )
        self.canvas.itemconfig(self.danger_line_id, fill=DANGER_LINE_COLOR, width=max(1.5, 2.0 * s), dash=(8, 5))

        # Danger text
        self.canvas.coords(
            self.danger_text_id,
            ox + ((CONTAINER_LEFT + CONTAINER_RIGHT) / 2.0) * s,
            oy + (DANGER_Y - 14) * s,
        )
        font_size = max(8, int(9 * s))
        self.canvas.itemconfig(self.danger_text_id, font=("Segoe UI", font_size, "bold"))

    def _init_dropper_graphics(self) -> None:
        """Visual items for the fruit waiting to be dropped and its aim line."""
        self.guide_line_id = self.canvas.create_line(
            self.aim_x, DROP_Y, self.aim_x, CONTAINER_BOTTOM - 10,
            fill=GUIDE_LINE_COLOR, width=1.5, dash=(4, 4), tags="guide"
        )

        # Realistic fruit sprite item
        self.aim_sprite_id = self.canvas.create_image(
            self.aim_x, DROP_Y, tags="aim_fruit"
        )

        # Fallback procedural circle
        cfg = FRUIT_TIERS[self.current_tier]
        r = cfg.radius
        self.aim_body_id = self.canvas.create_oval(
            self.aim_x - r, DROP_Y - r, self.aim_x + r, DROP_Y + r,
            fill=cfg.color, outline=cfg.dark_color, width=2, tags="aim_fruit"
        )
        self.aim_highlight_id = self.canvas.create_oval(
            self.aim_x - r * 0.45, DROP_Y - r * 0.55,
            self.aim_x - r * 0.1, DROP_Y - r * 0.2,
            fill=cfg.highlight_color, outline="", tags="aim_fruit"
        )

        ed = r * 0.28
        er = max(2.0, r * 0.09)
        ey = DROP_Y - r * 0.02
        self.aim_eye_l = self.canvas.create_oval(
            self.aim_x - ed - er, ey - er, self.aim_x - ed + er, ey + er,
            fill="#1E1E2E", outline="", tags="aim_fruit"
        )
        self.aim_eye_r = self.canvas.create_oval(
            self.aim_x + ed - er, ey - er, self.aim_x + ed + er, ey + er,
            fill="#1E1E2E", outline="", tags="aim_fruit"
        )
        self.aim_mouth = self.canvas.create_arc(
            self.aim_x - r * 0.18, DROP_Y + r * 0.1,
            self.aim_x + r * 0.18, DROP_Y + r * 0.26,
            start=200, extent=140, style=tk.ARC,
            outline="#1E1E2E", width=1.2, tags="aim_fruit"
        )

        self._update_dropper_graphics()

    def _update_dropper_graphics(self) -> None:
        """Refreshes color, position, and animated bob of aiming fruit."""
        if self.state in (GameState.START, GameState.GAME_OVER, GameState.PAUSED, GameState.SETTINGS):
            try:
                self.canvas.itemconfigure("aim_fruit", state="hidden")
                self.canvas.itemconfigure(self.guide_line_id, state="hidden")
            except Exception:
                pass
            return

        cfg = FRUIT_TIERS[self.current_tier]
        r = cfg.radius

        # Clamp aim_x within container walls with safe wall margin
        min_x = CONTAINER_LEFT + r + 14
        max_x = CONTAINER_RIGHT - r - 14
        self.aim_x = max(min_x, min(max_x, self.aim_x))

        s = self.scale
        ox = self.render_offset_x
        oy = self.render_offset_y

        # Gentle floating hover bob animation
        aim_bob = math.sin(time.perf_counter() * 5.0) * 3.5

        sx = ox + self.aim_x * s
        sy = oy + (DROP_Y + aim_bob) * s
        sr = r * s

        # Update guide line
        try:
            self.canvas.itemconfigure(self.guide_line_id, state="normal")
            self.canvas.coords(
                self.guide_line_id,
                sx, sy + sr,
                sx, oy + (CONTAINER_BOTTOM - 10) * s,
            )
            self.canvas.itemconfig(self.guide_line_id, width=max(1.0, 1.5 * s))
        except Exception:
            pass

        # Update realistic fruit sprite with quantized size and reference retention
        scale_factor = TIER_BODY_SCALE.get(self.current_tier, 1.12)
        diameter = max(10, int(round(sr * 2.0 * scale_factor / 2.0)) * 2)
        photo = self.sm.get_fruit_sprite(self.current_tier, diameter, 0.0)
        if photo:
            self.aim_photo = photo
            try:
                self.canvas.coords(self.aim_sprite_id, sx, sy)
                self.canvas.itemconfig(self.aim_sprite_id, image=photo)
                self.canvas.itemconfigure(self.aim_sprite_id, state="normal")
                self.canvas.itemconfigure(self.aim_body_id, state="hidden")
                self.canvas.itemconfigure(self.aim_highlight_id, state="hidden")
            except Exception:
                pass
        else:
            try:
                self.canvas.itemconfigure(self.aim_sprite_id, state="hidden")
                self.canvas.coords(self.aim_body_id, sx - sr, sy - sr, sx + sr, sy + sr)
                self.canvas.itemconfig(self.aim_body_id, fill=cfg.color, outline=cfg.dark_color, width=max(1.5, sr * 0.05))
                self.canvas.itemconfigure(self.aim_body_id, state="normal")
                self.canvas.coords(
                    self.aim_highlight_id,
                    sx - sr * 0.45, sy - sr * 0.55,
                    sx - sr * 0.1, sy - sr * 0.2,
                )
                self.canvas.itemconfig(self.aim_highlight_id, fill=cfg.highlight_color)
                self.canvas.itemconfigure(self.aim_highlight_id, state="normal")
            except Exception:
                pass

        # Face (centered precisely on cherry and all fruits)
        ed = sr * 0.28
        er = max(2.2, sr * 0.09)
        ey = sy + sr * (0.04 if self.current_tier == 1 else -0.02)
        self.canvas.coords(self.aim_eye_l, sx - ed - er, ey - er, sx - ed + er, ey + er)
        self.canvas.coords(self.aim_eye_r, sx + ed - er, ey - er, sx + ed + er, ey + er)
        self.canvas.coords(
            self.aim_mouth,
            sx - sr * 0.18, ey + sr * 0.12,
            sx + sr * 0.18, ey + sr * 0.28,
        )
        self.canvas.itemconfig(self.aim_mouth, width=max(1.2, sr * 0.04))

    def _bind_inputs(self) -> None:
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Button-1>", self._on_mouse_click)

        self.master.bind("<Left>", lambda e: self._nudge_aim(-20))
        self.master.bind("<a>", lambda e: self._nudge_aim(-20))
        self.master.bind("<A>", lambda e: self._nudge_aim(-20))

        self.master.bind("<Right>", lambda e: self._nudge_aim(20))
        self.master.bind("<d>", lambda e: self._nudge_aim(20))
        self.master.bind("<D>", lambda e: self._nudge_aim(20))

        self.master.bind("<space>", lambda e: self._on_space_pressed())
        self.master.bind("<Return>", lambda e: self._on_return_pressed())
        self.master.bind("<Down>", lambda e: self._trigger_drop() if self.state == GameState.AIMING else None)
        self.master.bind("<s>", lambda e: self._trigger_drop() if self.state == GameState.AIMING else None)
        self.master.bind("<S>", lambda e: self._trigger_drop() if self.state == GameState.AIMING else None)

        self.master.bind("<p>", lambda e: self.toggle_pause())
        self.master.bind("<P>", lambda e: self.toggle_pause())
        self.master.bind("<r>", lambda e: self._on_r_pressed())
        self.master.bind("<R>", lambda e: self._on_r_pressed())
        self.master.bind("<m>", lambda e: self._on_m_pressed())
        self.master.bind("<M>", lambda e: self._on_m_pressed())
        self.master.bind("<o>", lambda e: self.open_settings())
        self.master.bind("<O>", lambda e: self.open_settings())
        self.master.bind("<Escape>", lambda e: self._on_esc_pressed())

    def _on_space_pressed(self) -> None:
        # Spacebar ONLY drops fruit during active gameplay!
        # It never accidentally dismisses the Start screen or Game Over screen.
        if self.state == GameState.AIMING:
            self._trigger_drop()

    def _on_return_pressed(self) -> None:
        # Prevent Return from inadvertently starting or resetting without button interaction
        pass

    def _on_r_pressed(self) -> None:
        if self.state in (GameState.AIMING, GameState.COOLDOWN, GameState.PAUSED, GameState.GAME_OVER):
            self.restart()

    def _on_m_pressed(self) -> None:
        if self.state in (GameState.GAME_OVER, GameState.PAUSED):
            self.return_to_start()
        else:
            self.toggle_sound()

    def _on_esc_pressed(self) -> None:
        if self.state == GameState.SETTINGS:
            self.close_settings()
        elif self.state == GameState.PAUSED:
            self.toggle_pause()
        elif self.state == GameState.GAME_OVER:
            self.return_to_start()
        elif self.state in (GameState.AIMING, GameState.COOLDOWN):
            self.toggle_pause()

    def _on_mouse_move(self, event: tk.Event) -> None:
        if self.state in (GameState.AIMING, GameState.COOLDOWN):
            if self.scale > 0:
                self.aim_x = (event.x - self.offset_x) / self.scale
            else:
                self.aim_x = float(event.x)
            try:
                self._update_dropper_graphics()
            except Exception:
                pass

    def _on_mouse_click(self, event: tk.Event) -> None:
        # If an interactive button was pressed during this click, consume the event cleanly
        if self._button_clicked_this_event:
            self._button_clicked_this_event = False
            return

        # Crucial: mouse clicks outside buttons NEVER dismiss Start, Game Over, or Pause overlays!
        # The game strictly waits for the user to click the interactive buttons.
        if self.state != GameState.AIMING:
            return

        # Check if an interactive canvas button with its own handler was clicked
        clicked = self.canvas.find_withtag("current")
        if clicked:
            tags = self.canvas.gettags(clicked[0])
            if "interactive_btn" in tags:
                return

        if self.scale > 0:
            self.aim_x = (event.x - self.offset_x) / self.scale
        else:
            self.aim_x = float(event.x)
        self._trigger_drop()

    def _nudge_aim(self, delta_x: float) -> None:
        if self.state in (GameState.AIMING, GameState.COOLDOWN):
            self.aim_x += delta_x
            self._update_dropper_graphics()

    def _trigger_drop(self) -> None:
        now = time.perf_counter() * 1000.0
        if self.state != GameState.AIMING:
            return
        if now - self.last_drop_time < DROP_COOLDOWN_MS:
            return

        cfg = FRUIT_TIERS[self.current_tier]
        r = cfg.radius
        clamped_x = max(CONTAINER_LEFT + r + 14, min(CONTAINER_RIGHT - r - 14, self.aim_x))
        self.highest_tier_reached = max(self.highest_tier_reached, self.current_tier)

        # Spawn fruit in physics space
        fid = self.physics.spawn_fruit(self.current_tier, clamped_x, DROP_Y, vx=0.0, vy=50.0)
        visual = FruitVisual(
            self.canvas, fid, self.current_tier, clamped_x, DROP_Y,
            scale=self.scale, offset_x=self.render_offset_x, offset_y=self.render_offset_y
        )
        visual.trigger_wobble()
        self.visuals[fid] = visual

        # Audio feedback
        self.audio.play_drop()

        # Update drop states
        self.last_drop_time = now
        self.state = GameState.COOLDOWN

        # Hide aim preview during brief cooldown
        self.canvas.itemconfigure("aim_fruit", state="hidden")
        self.canvas.itemconfigure(self.guide_line_id, state="hidden")

        # Cycle next fruit
        self.current_tier = self.next_tier
        self.next_tier = self._pick_drop_fruit()
        self.sidebar.update_next_preview(self.next_tier)

        if self._cooldown_job:
            try:
                self.master.after_cancel(self._cooldown_job)
            except Exception:
                pass
        self._cooldown_job = self.master.after(DROP_COOLDOWN_MS, self._finish_cooldown)

    def _finish_cooldown(self) -> None:
        self._cooldown_job = None
        if not self._running:
            return
        if self.state == GameState.COOLDOWN:
            self.state = GameState.AIMING
            self._update_dropper_graphics()

    def _pick_drop_fruit(self) -> int:
        return random.choices(DROP_TIERS, weights=DROP_WEIGHTS, k=1)[0]

    def _game_loop(self) -> None:
        """Main fixed-rate update loop (~60 FPS)."""
        if not self._running:
            return

        try:
            now = time.perf_counter()
            dt = min(0.04, now - self._last_frame_time)
            self._last_frame_time = now

            # Update screen shake trauma
            if self.shake_trauma > 0.0:
                self.shake_trauma = max(0.0, self.shake_trauma - dt * 2.2)
                shake_sq = self.shake_trauma * self.shake_trauma
                sx = (random.random() * 2.0 - 1.0) * 8.0 * shake_sq * self.scale
                sy = (random.random() * 2.0 - 1.0) * 8.0 * shake_sq * self.scale
                self.render_offset_x = self.offset_x + sx
                self.render_offset_y = self.offset_y + sy
                self._update_static_elements()
            else:
                if self.render_offset_x != self.offset_x or self.render_offset_y != self.offset_y:
                    self.render_offset_x = self.offset_x
                    self.render_offset_y = self.offset_y
                    self._update_static_elements()

            if self.state in (GameState.AIMING, GameState.COOLDOWN):
                # 1. Physics Step & Collision Merge handling
                merge_events = self.physics.step(dt)
                if merge_events:
                    self._handle_merges(merge_events)

                # 2. Update Visual Fruit Coordinates & Animations
                active_fruits = self.physics.get_all_fruits_state()
                active_ids = set()
                for fid, x, y, angle, tier in active_fruits:
                    active_ids.add(fid)
                    near_danger = (y - FRUIT_TIERS[tier].radius < DANGER_Y + 45)
                    if fid in self.visuals:
                        self.visuals[fid].update(
                            x, y, angle, self.scale, self.render_offset_x, self.render_offset_y,
                            dt=dt, near_danger=near_danger
                        )
                    else:
                        visual = FruitVisual(
                            self.canvas, fid, tier, x, y,
                            scale=self.scale, offset_x=self.render_offset_x, offset_y=self.render_offset_y
                        )
                        visual.trigger_wobble()
                        visual.update(
                            x, y, angle, self.scale, self.render_offset_x, self.render_offset_y,
                            dt=dt, near_danger=near_danger
                        )
                        self.visuals[fid] = visual

                # Clean up visuals of removed fruits
                for dead_id in list(self.visuals.keys()):
                    if dead_id not in active_ids:
                        self.visuals[dead_id].destroy()
                        del self.visuals[dead_id]

                # 4. Check Danger Line Overflow
                self._check_danger_line(dt)

                # 5. Update dropper hover animation
                if self.state == GameState.AIMING:
                    self._update_dropper_graphics()

            # 3. Update Particle Effects & Ambient motes (runs in all states)
            self.particles.update(dt, self.scale, self.render_offset_x, self.render_offset_y)
        except Exception as e:
            print(f"Game loop exception handled: {e}")
        finally:
            if self._running:
                self._loop_job = self.master.after(16, self._game_loop)

    def _handle_merges(self, merges: list[MergeEvent]) -> None:
        now = time.perf_counter()
        if now - self.last_merge_time < COMBO_TIMEOUT_SECONDS:
            self.combo_count += 1
        else:
            self.combo_count = 1
        self.last_merge_time = now

        for ev in merges:
            cfg = FRUIT_TIERS[ev.tier]
            is_max = ev.new_tier is None

            # Track session achievements
            self.total_merges += 1
            if ev.new_tier:
                self.highest_tier_reached = max(self.highest_tier_reached, ev.new_tier)
            elif is_max:
                self.highest_tier_reached = 11
            self.max_combo = max(self.max_combo, self.combo_count)

            # Calculate score with combo multiplier
            mult = self.combo_count
            points = ev.score * mult
            self.score += points
            self.sidebar.bump_score(self.score)

            # High score update
            if self.score > self.high_score:
                self.high_score = self.score
                self.sidebar.set_high_score(self.high_score)
                SidebarPanel.save_high_score(self.high_score)
                self.is_new_high_score = True

            # Audio chime
            self.audio.play_merge(ev.new_tier if ev.new_tier else 11)

            # Screen shake juice
            shake_amt = 0.38 if is_max or ev.tier >= 8 else (0.24 if ev.tier >= 4 else 0.15)
            self.shake_trauma = min(1.0, self.shake_trauma + shake_amt)

            # Pop combo banner if combo streak active
            if mult >= 2:
                self.particles.spawn_combo(
                    self.canvas, ev.x, ev.y, mult,
                    scale=self.scale, offset_x=self.render_offset_x, offset_y=self.render_offset_y
                )

            # Visual juice bursts & expanding shockwaves
            burst_count = 32 if is_max else 18
            radius = cfg.radius * 1.3
            self.particles.spawn_merge_burst(
                self.canvas, ev.x, ev.y, cfg.color, cfg.highlight_color,
                radius=radius, count=burst_count,
                scale=self.scale, offset_x=self.render_offset_x, offset_y=self.render_offset_y
            )
            self.particles.spawn_floating_score(
                self.canvas, ev.x, ev.y, points, is_bonus=(is_max or mult >= 3),
                scale=self.scale, offset_x=self.render_offset_x, offset_y=self.render_offset_y
            )

    def _check_danger_line(self, dt: float) -> None:
        overflowing, highest_y = self.physics.check_overflow(DANGER_Y)

        if overflowing:
            self.danger_timer += dt
            self.pulse_phase += dt * 8.0
            # Red pulse visual
            pulse_brightness = int(140 + 115 * math.sin(self.pulse_phase))
            hex_color = f"#{pulse_brightness:02x}2040"
            self.canvas.itemconfig(self.danger_line_id, fill=hex_color, width=max(2.0, 3.0 * self.scale))

            remaining = max(0.0, DANGER_TRIGGER_SECONDS - self.danger_timer)
            self.canvas.itemconfig(
                self.danger_text_id,
                text=t("danger_warning", remaining=remaining),
                fill="#F59E0B",
            )

            # Audio warning ping every ~0.8s
            if int((self.danger_timer - dt) * 1.5) < int(self.danger_timer * 1.5):
                self.audio.play_danger()

            # Trigger Game Over
            if self.danger_timer >= DANGER_TRIGGER_SECONDS:
                self._trigger_game_over()
        else:
            self.danger_timer = max(0.0, self.danger_timer - dt * 2.0)
            self.canvas.itemconfig(self.danger_line_id, fill=DANGER_LINE_COLOR, width=max(1.5, 2.0 * self.scale))
            self.canvas.itemconfig(self.danger_text_id, text="")

    def _trigger_game_over(self) -> None:
        self.state = GameState.GAME_OVER
        self.audio.play_game_over()
        self._update_dropper_graphics()
        self._show_game_over_overlay()

    def _create_canvas_button(
        self,
        cx: float,
        cy: float,
        width: float,
        height: float,
        text: str,
        command: Callable[[], None],
        tag: str,
        bg_color: str = "#059669",
        hover_color: str = "#10B981",
        border_color: str = "#F59E0B",
        text_color: str = "#FFFBEB",
        font_size: int = 13,
        radius: float = 12.0,
    ) -> list[int]:
        """Creates an interactive, anti-aliased rounded button on the canvas with hover and click states."""
        s = self.scale
        hw = width / 2.0
        hh = height / 2.0
        x1 = cx - hw
        y1 = cy - hh
        x2 = cx + hw
        y2 = cy + hh
        r = min(radius * s, hh * 0.85)

        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]
        btn_body = self.canvas.create_polygon(
            points, smooth=True, fill=bg_color, outline=border_color,
            width=max(1.5, 2.0 * s), tags=(tag, "overlay", "interactive_btn")
        )
        btn_text = self.canvas.create_text(
            cx, cy, text=text, fill=text_color,
            font=("Segoe UI", max(9, int(font_size * s)), "bold"),
            tags=(tag, "overlay", "interactive_btn")
        )

        def on_enter(e):
            self.canvas.itemconfig(btn_body, fill=hover_color)
            self.canvas.config(cursor="hand2")

        def on_leave(e):
            self.canvas.itemconfig(btn_body, fill=bg_color)
            self.canvas.config(cursor="")

        def on_click(e):
            self._button_clicked_this_event = True
            self.canvas.config(cursor="")
            if hasattr(self, "audio"):
                self.audio.play_click()
            self.master.after_idle(command)

        self.canvas.tag_bind(tag, "<Enter>", on_enter)
        self.canvas.tag_bind(tag, "<Leave>", on_leave)
        self.canvas.tag_bind(tag, "<Button-1>", on_click)

        return [btn_body, btn_text]

    def _show_start_overlay(self) -> None:
        """Renders the opening Cafe & Kitchen Welcome screen matching the artisan cafe atmosphere."""
        self._clear_overlay()
        s = self.scale
        ox = self.render_offset_x
        oy = self.render_offset_y

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw <= 1 or ch <= 1:
            cw = CANVAS_WIDTH
            ch = CANVAS_HEIGHT

        cx = ox + (CANVAS_WIDTH / 2.0) * s
        cy = oy + (CANVAS_HEIGHT / 2.0) * s

        # Dark warm cafe atmosphere vignette
        bg_id = self.canvas.create_rectangle(
            0, 0, cw, ch,
            fill="#120D0A", stipple="gray75", tags="overlay"
        )
        self.overlay_items.append(bg_id)

        # Artisan carved wood plaque card with drop shadow and brass rivets
        pw = int(390 * s)
        ph = int(520 * s)
        plaque_photo = self.sm.get_plaque_card(
            pw, ph,
            border_color=(217, 119, 6),
            fill_color=(38, 25, 16),
            master=self.master,
        )
        if plaque_photo:
            self._overlay_photos.append(plaque_photo)
            plaque_id = self.canvas.create_image(cx, cy, image=plaque_photo, tags="overlay")
            self.overlay_items.append(plaque_id)
        else:
            box_id = self.canvas.create_rectangle(
                cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2,
                fill="#261910", outline="#D97706", width=max(2.0, 2.5 * s), tags="overlay"
            )
            self.overlay_items.append(box_id)

        top_y = cy - ph / 2.0

        # Header: Cafe title & subtitle
        t_sub1 = self.canvas.create_text(
            cx, top_y + 35 * s,
            text=t("start_cafe_header"), fill="#F59E0B",
            font=("Segoe UI", max(8, int(11 * s)), "bold"), tags="overlay"
        )
        t_title = self.canvas.create_text(
            cx, top_y + 64 * s,
            text=t("start_game_title"), fill="#FFFBEB",
            font=("Segoe UI", max(16, int(24 * s)), "bold"), tags="overlay"
        )
        t_sub2 = self.canvas.create_text(
            cx, top_y + 88 * s,
            text="Artisan Kitchen & Watermelon Quest", fill="#D4B996",
            font=("Segoe UI", max(8, int(11 * s))), tags="overlay"
        )
        # Golden divider
        div1 = self.canvas.create_line(
            cx - 120 * s, top_y + 104 * s, cx + 120 * s, top_y + 104 * s,
            fill="#B45309", width=max(1.0, 1.5 * s), tags="overlay"
        )
        div_star = self.canvas.create_text(
            cx, top_y + 104 * s, text="◆", fill="#F59E0B",
            font=("Segoe UI", max(8, int(10 * s)), "bold"), tags="overlay"
        )
        self.overlay_items.extend([t_sub1, t_title, t_sub2, div1, div_star])

        # Mascot fruit showcase (Strawberry, Melon, Orange)
        straw_photo = self.sm.get_fruit_sprite(2, int(48 * s), angle_rad=0.18, master=self.master)
        melon_photo = self.sm.get_fruit_sprite(10, int(72 * s), master=self.master)
        orange_photo = self.sm.get_fruit_sprite(5, int(54 * s), angle_rad=-0.18, master=self.master)

        if melon_photo:
            self._overlay_photos.append(melon_photo)
            m_id = self.canvas.create_image(cx, top_y + 148 * s, image=melon_photo, tags="overlay")
            self.overlay_items.append(m_id)
        if straw_photo:
            self._overlay_photos.append(straw_photo)
            s_id = self.canvas.create_image(cx - 75 * s, top_y + 155 * s, image=straw_photo, tags="overlay")
            self.overlay_items.append(s_id)
        if orange_photo:
            self._overlay_photos.append(orange_photo)
            o_id = self.canvas.create_image(cx + 75 * s, top_y + 152 * s, image=orange_photo, tags="overlay")
            self.overlay_items.append(o_id)

        # High score badge pill
        badge_y = top_y + 208 * s
        badge_text = t("high_score_pill", score=f"{self.high_score:,}")
        badge_half_w = max(100 * s, (len(badge_text) * 4.4 + 18) * s / 2.0)
        badge_points = [
            cx - badge_half_w, badge_y - 13 * s,
            cx + badge_half_w, badge_y - 13 * s,
            cx + badge_half_w, badge_y + 13 * s,
            cx - badge_half_w, badge_y + 13 * s,
        ]
        b_box = self.canvas.create_polygon(
            badge_points, smooth=True, fill="#322216", outline="#D97706",
            width=max(1.0, 1.5 * s), tags="overlay"
        )
        b_txt = self.canvas.create_text(
            cx, badge_y,
            text=badge_text, fill="#FDE68A",
            font=("Segoe UI", max(8, int(11 * s)), "bold"), tags="overlay"
        )
        self.overlay_items.extend([b_box, b_txt])

        # How to play card box
        rules_y = top_y + 233 * s
        rules_w = 340 * s
        rules_h = 118 * s
        r_box = self.canvas.create_rectangle(
            cx - rules_w / 2, rules_y, cx + rules_w / 2, rules_y + rules_h,
            fill="#1C120C", outline="#483626", width=max(1.0, 1.5 * s), tags="overlay"
        )
        self.overlay_items.append(r_box)

        rx = cx - rules_w / 2 + 16 * s
        r1 = self.canvas.create_text(
            rx, rules_y + 17 * s,
            text=t("rule_1"), fill="#FFFBEB",
            font=("Segoe UI", max(8, int(10 * s)), "bold"), anchor="w", tags="overlay"
        )
        r2 = self.canvas.create_text(
            rx, rules_y + 42 * s,
            text=t("rule_2"), fill="#FFFBEB",
            font=("Segoe UI", max(8, int(10 * s)), "bold"), anchor="w", tags="overlay"
        )
        r3 = self.canvas.create_text(
            rx, rules_y + 68 * s,
            text=t("rule_3"), fill="#F43F5E",
            font=("Segoe UI", max(8, int(10 * s)), "bold"), anchor="w", tags="overlay"
        )
        r4 = self.canvas.create_text(
            rx, rules_y + 94 * s,
            text=t("rule_4"), fill="#B8A28E",
            font=("Segoe UI", max(7, int(9 * s))), anchor="w", tags="overlay"
        )
        self.overlay_items.extend([r1, r2, r3, r4])

        # Primary Start Button
        btn_start = self._create_canvas_button(
            cx=cx,
            cy=top_y + 384 * s,
            width=230 * s,
            height=42 * s,
            text=t("btn_start_game"),
            command=self.start_game,
            tag="start_btn",
            bg_color="#059669",
            hover_color="#10B981",
            border_color="#F59E0B",
            text_color="#FFFBEB",
            font_size=13,
        )
        self.overlay_items.extend(btn_start)

        # Settings Button
        btn_settings = self._create_canvas_button(
            cx=cx,
            cy=top_y + 434 * s,
            width=230 * s,
            height=36 * s,
            text=t("btn_start_settings"),
            command=self.open_settings,
            tag="start_settings_btn",
            bg_color="#2E1C12",
            hover_color="#452A1C",
            border_color="#B45309",
            text_color="#FFFBEB",
            font_size=11,
        )
        self.overlay_items.extend(btn_settings)

        # Hint text (constrained width, zero overflow)
        t_hint = self.canvas.create_text(
            cx, top_y + 478 * s,
            text=t("start_hint"), fill="#B8A28E",
            width=int(330 * s), justify=tk.CENTER,
            font=("Segoe UI", max(8, int(10 * s))), tags="overlay"
        )
        self.overlay_items.append(t_hint)

    def start_game(self) -> None:
        """Transitions from the start screen into active gameplay."""
        if hasattr(self, "audio"):
            self.audio.play_start()
        self._clear_overlay()
        self.state = GameState.AIMING
        self._update_dropper_graphics()

    def return_to_start(self) -> None:
        """Returns to the opening cafe start screen from Game Over or Pause."""
        self.restart(start_in_menu=True)

    def open_settings(self) -> None:
        """Opens the Settings modal from any current screen (Start, Pause, or Playing)."""
        if self.state == GameState.SETTINGS:
            return
        self._settings_return_state = self.state
        self.state = GameState.SETTINGS
        self._update_dropper_graphics()
        self._show_settings_overlay()

    def close_settings(self) -> None:
        """Saves settings and returns to the previous state."""
        self._clear_overlay()
        if self._settings_return_state == GameState.START:
            self.state = GameState.START
            self._update_dropper_graphics()
            self._show_start_overlay()
        elif self._settings_return_state == GameState.PAUSED:
            self.state = GameState.PAUSED
            self._update_dropper_graphics()
            self._show_pause_overlay()
        elif self._settings_return_state == GameState.GAME_OVER:
            self.state = GameState.GAME_OVER
            self._update_dropper_graphics()
            self._show_game_over_overlay()
        else:
            self.state = GameState.AIMING
            self._update_dropper_graphics()

    def _select_language(self, lang: str) -> None:
        """Switches active language, updates sidebar, and re-renders settings overlay."""
        I18n.get_instance().set_language(lang)
        self.sidebar.refresh_language()
        self._show_settings_overlay()

    def _toggle_settings_sound(self) -> None:
        """Toggles sound and re-renders settings overlay."""
        self.toggle_sound()
        self._show_settings_overlay()

    def _show_settings_overlay(self) -> None:
        """Renders the settings modal overlay with language selection and sound controls."""
        self._clear_overlay()
        s = self.scale
        ox = self.render_offset_x
        oy = self.render_offset_y

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw <= 1 or ch <= 1:
            cw = CANVAS_WIDTH
            ch = CANVAS_HEIGHT

        cx = ox + (CANVAS_WIDTH / 2.0) * s
        cy = oy + (CANVAS_HEIGHT / 2.0) * s

        # Dark vignette background
        bg_id = self.canvas.create_rectangle(
            0, 0, cw, ch,
            fill="#120D0A", stipple="gray75", tags="overlay"
        )
        self.overlay_items.append(bg_id)

        # Plaque
        pw = int(380 * s)
        ph = int(450 * s)
        plaque_photo = self.sm.get_plaque_card(
            pw, ph,
            border_color=(217, 119, 6),
            fill_color=(38, 25, 16),
            master=self.master,
        )
        if plaque_photo:
            self._overlay_photos.append(plaque_photo)
            plaque_id = self.canvas.create_image(cx, cy, image=plaque_photo, tags="overlay")
            self.overlay_items.append(plaque_id)
        else:
            box_id = self.canvas.create_rectangle(
                cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2,
                fill="#261910", outline="#D97706", width=max(2.0, 2.5 * s), tags="overlay"
            )
            self.overlay_items.append(box_id)

        top_y = cy - ph / 2.0

        # Header Title
        t_title = self.canvas.create_text(
            cx, top_y + 36 * s,
            text=t("settings_title"), fill="#F59E0B",
            font=("Segoe UI", max(13, int(18 * s)), "bold"), tags="overlay"
        )
        div = self.canvas.create_line(
            cx - 110 * s, top_y + 56 * s, cx + 110 * s, top_y + 56 * s,
            fill="#B45309", width=max(1.0, 1.5 * s), tags="overlay"
        )
        self.overlay_items.extend([t_title, div])

        # Section 1: Language
        t_lang_lbl = self.canvas.create_text(
            cx, top_y + 82 * s,
            text=t("settings_lang_label"), fill="#FFFBEB",
            font=("Segoe UI", max(9, int(11 * s)), "bold"), tags="overlay"
        )
        self.overlay_items.append(t_lang_lbl)

        cur_lang = I18n.get_instance().language

        # English button
        is_en = (cur_lang == "en")
        en_bg = "#059669" if is_en else "#261910"
        en_hover = "#10B981" if is_en else "#3E281B"
        en_border = "#F59E0B" if is_en else "#5C3E28"
        en_text = "🇬🇧 English" + ("  ✓" if is_en else "")
        btn_en = self._create_canvas_button(
            cx=cx - 72 * s,
            cy=top_y + 122 * s,
            width=130 * s,
            height=38 * s,
            text=en_text,
            command=lambda: self._select_language("en"),
            tag="settings_lang_en",
            bg_color=en_bg,
            hover_color=en_hover,
            border_color=en_border,
            text_color="#FFFBEB",
            font_size=11,
        )
        self.overlay_items.extend(btn_en)

        # Turkish button
        is_tr = (cur_lang == "tr")
        tr_bg = "#059669" if is_tr else "#261910"
        tr_hover = "#10B981" if is_tr else "#3E281B"
        tr_border = "#F59E0B" if is_tr else "#5C3E28"
        tr_text = "🇹🇷 Türkçe" + ("  ✓" if is_tr else "")
        btn_tr = self._create_canvas_button(
            cx=cx + 72 * s,
            cy=top_y + 122 * s,
            width=130 * s,
            height=38 * s,
            text=tr_text,
            command=lambda: self._select_language("tr"),
            tag="settings_lang_tr",
            bg_color=tr_bg,
            hover_color=tr_hover,
            border_color=tr_border,
            text_color="#FFFBEB",
            font_size=11,
        )
        self.overlay_items.extend(btn_tr)

        div_mid = self.canvas.create_line(
            cx - 120 * s, top_y + 162 * s, cx + 120 * s, top_y + 162 * s,
            fill="#483626", width=1, tags="overlay"
        )
        self.overlay_items.append(div_mid)

        # Section 2: Audio
        t_sound_lbl = self.canvas.create_text(
            cx, top_y + 188 * s,
            text=t("settings_sound_label"), fill="#FFFBEB",
            font=("Segoe UI", max(9, int(11 * s)), "bold"), tags="overlay"
        )
        self.overlay_items.append(t_sound_lbl)

        sound_enabled = self.audio.enabled
        sound_text = t("settings_sound_toggle_on") if sound_enabled else t("settings_sound_toggle_off")
        sound_bg = "#38271B" if sound_enabled else "#221610"
        sound_hover = "#4D3626" if sound_enabled else "#332219"
        btn_sound = self._create_canvas_button(
            cx=cx,
            cy=top_y + 226 * s,
            width=240 * s,
            height=40 * s,
            text=sound_text,
            command=self._toggle_settings_sound,
            tag="settings_sound_toggle",
            bg_color=sound_bg,
            hover_color=sound_hover,
            border_color="#B45309",
            text_color="#FFFBEB",
            font_size=11,
        )
        self.overlay_items.extend(btn_sound)

        div_bot = self.canvas.create_line(
            cx - 120 * s, top_y + 270 * s, cx + 120 * s, top_y + 270 * s,
            fill="#483626", width=1, tags="overlay"
        )
        self.overlay_items.append(div_bot)

        # Fruit preview showcase in settings (Kiraz & Portakal)
        cherry_photo = self.sm.get_fruit_sprite(1, int(36 * s), master=self.master)
        orange_photo = self.sm.get_fruit_sprite(5, int(42 * s), master=self.master)
        if cherry_photo:
            self._overlay_photos.append(cherry_photo)
            c_id = self.canvas.create_image(cx - 95 * s, top_y + 315 * s, image=cherry_photo, tags="overlay")
            self.overlay_items.append(c_id)
        if orange_photo:
            self._overlay_photos.append(orange_photo)
            o_id = self.canvas.create_image(cx + 95 * s, top_y + 315 * s, image=orange_photo, tags="overlay")
            self.overlay_items.append(o_id)

        # Close / Save Button
        btn_save = self._create_canvas_button(
            cx=cx,
            cy=top_y + 365 * s,
            width=220 * s,
            height=44 * s,
            text=t("btn_save_close"),
            command=self.close_settings,
            tag="settings_close_btn",
            bg_color="#059669",
            hover_color="#10B981",
            border_color="#F59E0B",
            text_color="#FFFBEB",
            font_size=12,
        )
        self.overlay_items.extend(btn_save)

        # Hint text
        t_hint = self.canvas.create_text(
            cx, top_y + 415 * s,
            text=t("settings_hint"), fill="#B8A28E",
            width=int(320 * s), justify=tk.CENTER,
            font=("Segoe UI", max(8, int(10 * s))), tags="overlay"
        )
        self.overlay_items.append(t_hint)

    def _show_game_over_overlay(self) -> None:
        """Renders the Game Over / Harvest Summary screen matching the cafe theme."""
        self._clear_overlay()
        s = self.scale
        ox = self.render_offset_x
        oy = self.render_offset_y

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw <= 1 or ch <= 1:
            cw = CANVAS_WIDTH
            ch = CANVAS_HEIGHT

        cx = ox + (CANVAS_WIDTH / 2.0) * s
        cy = oy + (CANVAS_HEIGHT / 2.0) * s

        # Crimson-tinted dark cafe vignette
        bg_id = self.canvas.create_rectangle(
            0, 0, cw, ch,
            fill="#18080A", stipple="gray75", tags="overlay"
        )
        self.overlay_items.append(bg_id)

        # Plaque with warm rose-crimson border
        pw = int(390 * s)
        ph = int(520 * s)
        plaque_photo = self.sm.get_plaque_card(
            pw, ph,
            border_color=(225, 29, 72),
            fill_color=(36, 18, 16),
            master=self.master,
        )
        if plaque_photo:
            self._overlay_photos.append(plaque_photo)
            plaque_id = self.canvas.create_image(cx, cy, image=plaque_photo, tags="overlay")
            self.overlay_items.append(plaque_id)
        else:
            box_id = self.canvas.create_rectangle(
                cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2,
                fill="#241210", outline="#E11D48", width=max(2.0, 2.5 * s), tags="overlay"
            )
            self.overlay_items.append(box_id)

        top_y = cy - ph / 2.0

        # Header
        t_sub1 = self.canvas.create_text(
            cx, top_y + 32 * s,
            text=t("go_subtitle"), fill="#F43F5E",
            font=("Segoe UI", max(8, int(11 * s)), "bold"), tags="overlay"
        )
        t_title = self.canvas.create_text(
            cx, top_y + 60 * s,
            text=t("go_title"), fill="#EF4444",
            font=("Segoe UI", max(15, int(23 * s)), "bold"), tags="overlay"
        )
        div1 = self.canvas.create_line(
            cx - 120 * s, top_y + 80 * s, cx + 120 * s, top_y + 80 * s,
            fill="#991B1B", width=max(1.0, 1.5 * s), tags="overlay"
        )
        div_star = self.canvas.create_text(
            cx, top_y + 80 * s, text="◆", fill="#F59E0B",
            font=("Segoe UI", max(8, int(10 * s)), "bold"), tags="overlay"
        )
        self.overlay_items.extend([t_sub1, t_title, div1, div_star])

        # Score Box
        sc_w = 340 * s
        sc_h = 80 * s
        sc_y = top_y + 98 * s
        sc_box = self.canvas.create_rectangle(
            cx - sc_w / 2, sc_y, cx + sc_w / 2, sc_y + sc_h,
            fill="#1C0E0E", outline="#782424", width=max(1.0, 1.5 * s), tags="overlay"
        )
        sc_lbl = self.canvas.create_text(
            cx, sc_y + 20 * s,
            text=t("go_score_label"), fill="#B8A28E",
            font=("Segoe UI", max(8, int(10 * s)), "bold"), tags="overlay"
        )
        sc_val = self.canvas.create_text(
            cx, sc_y + 50 * s,
            text=f"{self.score:,}", fill="#FFFBEB",
            font=("Segoe UI", max(18, int(26 * s)), "bold"), tags="overlay"
        )
        self.overlay_items.extend([sc_box, sc_lbl, sc_val])

        # High score banner
        hsb_y = top_y + 198 * s
        if self.is_new_high_score:
            h_text = t("go_new_record")
            h_color = "#F59E0B"
            h_bg = "#45220E"
            h_border = "#F59E0B"
        else:
            h_text = t("go_best_score", score=f"{self.high_score:,}")
            h_color = "#FDE68A"
            h_bg = "#301A14"
            h_border = "#B45309"

        h_half_w = max(110 * s, (len(h_text) * 4.4 + 18) * s / 2.0)
        h_points = [
            cx - h_half_w, hsb_y - 13 * s,
            cx + h_half_w, hsb_y - 13 * s,
            cx + h_half_w, hsb_y + 13 * s,
            cx - h_half_w, hsb_y + 13 * s,
        ]
        h_box = self.canvas.create_polygon(
            h_points, smooth=True, fill=h_bg, outline=h_border,
            width=max(1.0, 1.5 * s), tags="overlay"
        )
        h_lbl = self.canvas.create_text(
            cx, hsb_y,
            text=h_text, fill=h_color,
            font=("Segoe UI", max(8, int(11 * s)), "bold"), tags="overlay"
        )
        self.overlay_items.extend([h_box, h_lbl])

        # Run highlights panel (Highest fruit reached & combos)
        hl_y = top_y + 225 * s
        hl_w = 340 * s
        hl_h = 100 * s
        hl_box = self.canvas.create_rectangle(
            cx - hl_w / 2, hl_y, cx + hl_w / 2, hl_y + hl_h,
            fill="#180D0D", outline="#4A2222", width=max(1.0, 1.5 * s), tags="overlay"
        )
        self.overlay_items.append(hl_box)

        # Fruit sprite
        highest_fruit_photo = self.sm.get_fruit_sprite(
            self.highest_tier_reached, int(54 * s), master=self.master
        )
        if highest_fruit_photo:
            self._overlay_photos.append(highest_fruit_photo)
            hf_id = self.canvas.create_image(
                cx - 100 * s, hl_y + 36 * s, image=highest_fruit_photo, tags="overlay"
            )
            self.overlay_items.append(hf_id)

        f_name = get_fruit_name(self.highest_tier_reached)

        t_hf_lbl = self.canvas.create_text(
            cx - 55 * s, hl_y + 25 * s,
            text=t("go_biggest_fruit_label"), fill="#B8A28E",
            font=("Segoe UI", max(8, int(10 * s))), anchor="w", tags="overlay"
        )
        t_hf_val = self.canvas.create_text(
            cx - 55 * s, hl_y + 46 * s,
            text=t("go_tier_fmt", name=f_name, tier=self.highest_tier_reached), fill="#FFFBEB",
            font=("Segoe UI", max(9, int(12 * s)), "bold"), anchor="w", tags="overlay"
        )
        div_sub = self.canvas.create_line(
            cx - hl_w / 2 + 15 * s, hl_y + 68 * s, cx + hl_w / 2 - 15 * s, hl_y + 68 * s,
            fill="#381B1B", width=1, tags="overlay"
        )
        t_sub_stats = self.canvas.create_text(
            cx, hl_y + 84 * s,
            text=t("go_stats_fmt", merges=self.total_merges, combo=self.max_combo), fill="#F59E0B",
            font=("Segoe UI", max(8, int(10 * s)), "bold"), tags="overlay"
        )
        self.overlay_items.extend([t_hf_lbl, t_hf_val, div_sub, t_sub_stats])

        # Action Buttons
        btn_again = self._create_canvas_button(
            cx=cx,
            cy=top_y + 365 * s,
            width=240 * s,
            height=44 * s,
            text=t("btn_play_again"),
            command=self.restart,
            tag="gameover_restart_btn",
            bg_color="#059669",
            hover_color="#10B981",
            border_color="#F59E0B",
            text_color="#FFFBEB",
            font_size=13,
        )
        self.overlay_items.extend(btn_again)

        btn_menu = self._create_canvas_button(
            cx=cx,
            cy=top_y + 418 * s,
            width=240 * s,
            height=38 * s,
            text=t("btn_main_menu"),
            command=self.return_to_start,
            tag="gameover_menu_btn",
            bg_color="#3A2518",
            hover_color="#523522",
            border_color="#B45309",
            text_color="#FFFBEB",
            font_size=12,
        )
        self.overlay_items.extend(btn_menu)

        t_hint = self.canvas.create_text(
            cx, top_y + 465 * s,
            text=t("go_hint"), fill="#B8A28E",
            width=int(320 * s), justify=tk.CENTER,
            font=("Segoe UI", max(8, int(10 * s))), tags="overlay"
        )
        self.overlay_items.append(t_hint)

    def _show_pause_overlay(self) -> None:
        """Renders the Pause overlay matching the artisan wooden cafe aesthetic."""
        self._clear_overlay()
        s = self.scale
        ox = self.render_offset_x
        oy = self.render_offset_y

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw <= 1 or ch <= 1:
            cw = CANVAS_WIDTH
            ch = CANVAS_HEIGHT

        cx = ox + (CANVAS_WIDTH / 2.0) * s
        cy = oy + (CANVAS_HEIGHT / 2.0) * s

        bg_id = self.canvas.create_rectangle(
            0, 0, cw, ch,
            fill="#120D0A", stipple="gray75", tags="overlay"
        )
        self.overlay_items.append(bg_id)

        pw = int(350 * s)
        ph = int(410 * s)
        plaque_photo = self.sm.get_plaque_card(
            pw, ph,
            border_color=(217, 119, 6),
            fill_color=(38, 25, 16),
            master=self.master,
        )
        if plaque_photo:
            self._overlay_photos.append(plaque_photo)
            plaque_id = self.canvas.create_image(cx, cy, image=plaque_photo, tags="overlay")
            self.overlay_items.append(plaque_id)
        else:
            box_id = self.canvas.create_rectangle(
                cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2,
                fill="#261910", outline="#D97706", width=max(2.0, 2.5 * s), tags="overlay"
            )
            self.overlay_items.append(box_id)

        top_y = cy - ph / 2.0

        t1 = self.canvas.create_text(
            cx, top_y + 36 * s,
            text=t("pause_title"), fill="#FDE68A",
            font=("Segoe UI", max(13, int(19 * s)), "bold"), tags="overlay"
        )
        t2 = self.canvas.create_text(
            cx, top_y + 64 * s,
            text=t("pause_current_score", score=f"{self.score:,}"), fill="#FFFBEB",
            font=("Segoe UI", max(10, int(14 * s)), "bold"), tags="overlay"
        )
        div = self.canvas.create_line(
            cx - 100 * s, top_y + 84 * s, cx + 100 * s, top_y + 84 * s,
            fill="#B45309", width=1, tags="overlay"
        )
        self.overlay_items.extend([t1, t2, div])

        btn_resume = self._create_canvas_button(
            cx=cx,
            cy=top_y + 126 * s,
            width=220 * s,
            height=42 * s,
            text=t("btn_resume"),
            command=self.toggle_pause,
            tag="pause_resume_btn",
            bg_color="#059669",
            hover_color="#10B981",
            border_color="#F59E0B",
            text_color="#FFFBEB",
            font_size=13,
        )
        self.overlay_items.extend(btn_resume)

        btn_restart = self._create_canvas_button(
            cx=cx,
            cy=top_y + 178 * s,
            width=220 * s,
            height=38 * s,
            text=t("btn_restart"),
            command=self.restart,
            tag="pause_restart_btn",
            bg_color="#3A2518",
            hover_color="#523522",
            border_color="#B45309",
            text_color="#FFFBEB",
            font_size=12,
        )
        self.overlay_items.extend(btn_restart)

        btn_settings = self._create_canvas_button(
            cx=cx,
            cy=top_y + 226 * s,
            width=220 * s,
            height=38 * s,
            text=t("btn_settings"),
            command=self.open_settings,
            tag="pause_settings_btn",
            bg_color="#2E1C12",
            hover_color="#452A1C",
            border_color="#B45309",
            text_color="#FFFBEB",
            font_size=12,
        )
        self.overlay_items.extend(btn_settings)

        btn_menu = self._create_canvas_button(
            cx=cx,
            cy=top_y + 274 * s,
            width=220 * s,
            height=38 * s,
            text=t("btn_main_menu"),
            command=self.return_to_start,
            tag="pause_menu_btn",
            bg_color="#261910",
            hover_color="#3E281B",
            border_color="#78350F",
            text_color="#FFFBEB",
            font_size=12,
        )
        self.overlay_items.extend(btn_menu)

        t_hint = self.canvas.create_text(
            cx, top_y + 330 * s,
            text=t("pause_hint"), fill="#B8A28E",
            width=int(320 * s), justify=tk.CENTER,
            font=("Segoe UI", max(8, int(10 * s))), tags="overlay"
        )
        self.overlay_items.append(t_hint)

    def _clear_overlay(self) -> None:
        try:
            self.canvas.config(cursor="")
        except Exception:
            pass
        for item in self.overlay_items:
            try:
                self.canvas.delete(item)
            except Exception:
                pass
        self.overlay_items.clear()
        self._overlay_photos.clear()

    def toggle_pause(self) -> None:
        if self.state in (GameState.START, GameState.GAME_OVER, GameState.SETTINGS):
            return
        if self.state == GameState.PAUSED:
            self.state = GameState.AIMING
            self.sidebar.set_paused_state(False)
            self._clear_overlay()
            self._update_dropper_graphics()
        else:
            self.state = GameState.PAUSED
            self.sidebar.set_paused_state(True)
            self._update_dropper_graphics()
            self._show_pause_overlay()

    def toggle_sound(self) -> None:
        enabled = self.audio.toggle_sound()
        self.sidebar.set_sound_state(enabled)

    def restart(self, start_in_menu: bool = False) -> None:
        """Resets the game state, physics, and canvas for a fresh playthrough or return to menu."""
        if self._cooldown_job:
            try:
                self.master.after_cancel(self._cooldown_job)
            except Exception:
                pass
            self._cooldown_job = None

        self._clear_overlay()
        self.physics.reset()
        self.particles.clear()

        # Re-initialize ambient background particles
        self.particles.init_ambient(
            self.canvas,
            (CONTAINER_LEFT, CONTAINER_TOP, CONTAINER_RIGHT, CONTAINER_BOTTOM),
            count=18,
        )

        for visual in self.visuals.values():
            visual.destroy()
        self.visuals.clear()

        self.score = 0
        self.combo_count = 0
        self.last_merge_time = 0.0
        self.shake_trauma = 0.0
        self.is_new_high_score = False
        self.highest_tier_reached = 1
        self.total_merges = 0
        self.max_combo = 0
        self.danger_timer = 0.0

        self.sidebar.set_score(0)
        self.sidebar.set_paused_state(False)

        self.current_tier = self._pick_drop_fruit()
        self.next_tier = self._pick_drop_fruit()
        self.sidebar.update_next_preview(self.next_tier)

        self.canvas.itemconfig(self.danger_line_id, fill="#F43F5E")
        self.canvas.itemconfig(self.danger_text_id, text="")

        if start_in_menu:
            self.state = GameState.START
            self._update_dropper_graphics()
            self._show_start_overlay()
        else:
            self.state = GameState.AIMING
            self._update_dropper_graphics()

    def destroy(self) -> None:
        self._running = False
        if self._loop_job:
            try:
                self.master.after_cancel(self._loop_job)
            except Exception:
                pass
            self._loop_job = None
        if self._cooldown_job:
            try:
                self.master.after_cancel(self._cooldown_job)
            except Exception:
                pass
            self._cooldown_job = None
        self.audio.stop()
        super().destroy()
