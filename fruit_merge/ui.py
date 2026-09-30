"""Sidebar dashboard, preview widgets, evolution chain reference, and game-over modals."""

import json
import os
import tkinter as tk
from typing import Callable, Optional
from fruit_merge.constants import (
    CARD_BG,
    CARD_BORDER,
    CARD_HOVER,
    FRUIT_TIERS,
    HIGH_SCORE_FILE,
    MAX_TIER,
    NEON_CYAN,
    NEON_GREEN,
    NEON_PINK,
    SIDEBAR_BG,
    TEXT_ACCENT,
    TEXT_MUTED,
    TEXT_PRIMARY,
)
from fruit_merge.i18n import get_fruit_name, t
from fruit_merge.sprites import SpriteManager


class SidebarPanel(tk.Frame):
    """Modern arcade sidebar displaying scores, next fruit preview, evolution guide, and controls."""

    def __init__(
        self,
        parent: tk.Widget,
        on_restart: Callable[[], None],
        on_toggle_pause: Callable[[], None],
        on_toggle_sound: Callable[[], None],
        on_open_settings: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, bg=SIDEBAR_BG, **kwargs)
        self.on_restart = on_restart
        self.on_toggle_pause = on_toggle_pause
        self.on_toggle_sound = on_toggle_sound
        self.on_open_settings = on_open_settings
        self.sm = SpriteManager.get_instance()

        self.score_var = tk.StringVar(value="0")
        self.high_score_var = tk.StringVar(value=str(self.load_high_score()))
        self.sound_btn_text = tk.StringVar(value=t("btn_sound_on"))
        self.pause_btn_text = tk.StringVar(value=t("btn_pause_sidebar"))
        self._bump_job: Optional[str] = None
        self._is_sound_enabled = True
        self._is_paused = False
        self._current_next_tier = 1

        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)

        # 1. Header / Title Banner (Cozy Magic Cafe Aesthetic)
        title_frame = tk.Frame(self, bg=SIDEBAR_BG, pady=12)
        title_frame.pack(fill=tk.X, padx=14)

        self.lbl_title = tk.Label(
            title_frame,
            text=t("cafe_title"),
            font=("Segoe UI", 15, "bold"),
            fg="#F59E0B",
            bg=SIDEBAR_BG,
        )
        self.lbl_title.pack()
        self.lbl_subtitle = tk.Label(
            title_frame,
            text=t("cafe_subtitle"),
            font=("Segoe UI", 9, "bold"),
            fg="#B8A28E",
            bg=SIDEBAR_BG,
        )
        self.lbl_subtitle.pack(pady=(2, 0))

        # 2. Score Cards (Current & High Score on carved mahogany plaque)
        score_card = tk.Frame(
            self,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
            padx=14,
            pady=10,
        )
        score_card.pack(fill=tk.X, padx=14, pady=6)
        score_card.columnconfigure(0, weight=1)
        score_card.columnconfigure(1, weight=1)

        # Current Score
        self.lbl_score_header = tk.Label(score_card, text=t("score_label"), font=("Segoe UI", 8, "bold"), fg="#B8A28E", bg=CARD_BG)
        self.lbl_score_header.grid(row=0, column=0, sticky="w")
        self.lbl_score = tk.Label(
            score_card, textvariable=self.score_var, font=("Segoe UI", 16, "bold"), fg="#FFFBEB", bg=CARD_BG
        )
        self.lbl_score.grid(row=1, column=0, sticky="w")

        # Best Score
        self.lbl_best_header = tk.Label(score_card, text=t("best_harvest_label"), font=("Segoe UI", 8, "bold"), fg="#F59E0B", bg=CARD_BG)
        self.lbl_best_header.grid(row=0, column=1, sticky="e")
        self.lbl_high_score = tk.Label(
            score_card, textvariable=self.high_score_var, font=("Segoe UI", 16, "bold"), fg="#F59E0B", bg=CARD_BG
        )
        self.lbl_high_score.grid(row=1, column=1, sticky="e")

        # 3. Next Fruit Preview Card
        next_card = tk.Frame(
            self,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
            padx=12,
            pady=8,
        )
        next_card.pack(fill=tk.X, padx=14, pady=6)

        self.lbl_next_header = tk.Label(next_card, text=t("next_harvest_label"), font=("Segoe UI", 8, "bold"), fg="#B8A28E", bg=CARD_BG)
        self.lbl_next_header.pack(anchor="w")

        self.preview_canvas = tk.Canvas(
            next_card, width=180, height=84, bg="#18120C", highlightthickness=1, highlightbackground=CARD_BORDER
        )
        self.preview_canvas.pack(pady=4)

        self.next_name_lbl = tk.Label(
            next_card, text=get_fruit_name(1), font=("Segoe UI", 10, "bold"), fg="#FFFBEB", bg=CARD_BG
        )
        self.next_name_lbl.pack()

        # 4. Evolution Chain Reference Guide
        evo_card = tk.Frame(
            self,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
            padx=10,
            pady=8,
        )
        evo_card.pack(fill=tk.X, padx=14, pady=6)

        self.lbl_evo_header = tk.Label(evo_card, text=t("evolution_recipe_label"), font=("Segoe UI", 8, "bold"), fg="#B8A28E", bg=CARD_BG)
        self.lbl_evo_header.pack(anchor="w", pady=(0, 4))

        self.evo_canvas = tk.Canvas(evo_card, width=220, height=54, bg="#18120C", highlightthickness=1, highlightbackground=CARD_BORDER)
        self.evo_canvas.pack()
        self._draw_evolution_chain()

        # 5. Controls & Action Buttons (Styled like warm wooden cafe plaques)
        ctrl_card = tk.Frame(
            self,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        ctrl_card.pack(fill=tk.X, padx=14, pady=8)

        btn_style = {
            "font": ("Segoe UI", 9, "bold"),
            "bd": 0,
            "cursor": "hand2",
            "pady": 5,
            "relief": tk.FLAT,
        }

        # Restart Button (Warm rich amber/terracotta wood plaque)
        self.btn_restart = tk.Button(
            ctrl_card,
            text=t("btn_restart_sidebar"),
            bg="#B45309",
            fg="#FFFBEB",
            activebackground="#D97706",
            activeforeground="#FFFFFF",
            command=self.on_restart,
            **btn_style,
        )
        self.btn_restart.pack(fill=tk.X, pady=2)
        self._attach_hover_effect(self.btn_restart, "#B45309", "#D97706")

        # Pause Button (Artisan espresso wood plaque)
        self.btn_pause = tk.Button(
            ctrl_card,
            textvariable=self.pause_btn_text,
            bg="#38271B",
            fg="#FFFBEB",
            activebackground="#4D3626",
            activeforeground="#FFFFFF",
            command=self.on_toggle_pause,
            **btn_style,
        )
        self.btn_pause.pack(fill=tk.X, pady=2)
        self._attach_hover_effect(self.btn_pause, "#38271B", "#4D3626")

        # Sound Button (Warm bronze/walnut plaque)
        self.btn_sound = tk.Button(
            ctrl_card,
            textvariable=self.sound_btn_text,
            bg="#2A1D14",
            fg="#FFFBEB",
            activebackground="#3D2C1F",
            activeforeground="#FFFFFF",
            command=self.on_toggle_sound,
            **btn_style,
        )
        self.btn_sound.pack(fill=tk.X, pady=2)
        self._attach_hover_effect(self.btn_sound, "#2A1D14", "#3D2C1F")

        # Settings Button (Deep walnut/gold trim plaque)
        if self.on_open_settings:
            self.btn_settings = tk.Button(
                ctrl_card,
                text=t("btn_settings_sidebar"),
                bg="#231710",
                fg="#FFFBEB",
                activebackground="#3A271C",
                activeforeground="#FFFFFF",
                command=self.on_open_settings,
                **btn_style,
            )
            self.btn_settings.pack(fill=tk.X, pady=2)
            self._attach_hover_effect(self.btn_settings, "#231710", "#3A271C")

        # Keybindings tips
        help_text = f"{t('controls_title')}:\n{t('ctrl_aim')}\n{t('ctrl_drop')}\n{t('ctrl_shortcuts')}"
        self.lbl_help = tk.Label(
            self,
            text=help_text,
            font=("Segoe UI", 8),
            fg="#B8A28E",
            bg=SIDEBAR_BG,
            justify=tk.LEFT,
        )
        self.lbl_help.pack(padx=14, pady=(6, 0), anchor="w")

    def _attach_hover_effect(self, btn: tk.Button, normal_bg: str, hover_bg: str) -> None:
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.config(bg=normal_bg))

    def _draw_evolution_chain(self) -> None:
        """Draws small realistic fruit icons connected with arrows showing evolution tier order."""
        self.evo_canvas.delete("all")
        y_top = 16
        y_bot = 40

        x_start = 14
        step = 34
        # Row 1: Tiers 1-6
        for t in range(1, 7):
            cx = x_start + (t - 1) * step
            d = 18 + int((t - 1) * 2.2)
            photo = self.sm.get_fruit_sprite(t, d, 0.0)
            if photo:
                self.evo_canvas.create_image(cx, y_top, image=photo)
            else:
                cfg = FRUIT_TIERS[t]
                cr = d / 2.0
                self.evo_canvas.create_oval(
                    cx - cr, y_top - cr, cx + cr, y_top + cr,
                    fill=cfg.color, outline=cfg.dark_color, width=1
                )
            if t < 6:
                self.evo_canvas.create_text(cx + step / 2, y_top, text="›", fill="#D97706", font=("Segoe UI", 9, "bold"))

        # Row 2: Tiers 7-11
        for t in range(7, MAX_TIER + 1):
            idx = t - 7
            cx = x_start + idx * step
            d = 20 + int(idx * 2.5)
            photo = self.sm.get_fruit_sprite(t, d, 0.0)
            if photo:
                self.evo_canvas.create_image(cx, y_bot, image=photo)
            else:
                cfg = FRUIT_TIERS[t]
                cr = d / 2.0
                self.evo_canvas.create_oval(
                    cx - cr, y_bot - cr, cx + cr, y_bot + cr,
                    fill=cfg.color, outline=cfg.dark_color, width=1
                )
            if t < MAX_TIER:
                self.evo_canvas.create_text(cx + step / 2, y_bot, text="›", fill="#D97706", font=("Segoe UI", 9, "bold"))

    def update_next_preview(self, tier: int) -> None:
        """Renders the upcoming realistic fruit inside the preview card with a glowing backdrop aura."""
        self._current_next_tier = tier
        self.preview_canvas.delete("all")
        cfg = FRUIT_TIERS[tier]
        fruit_name = get_fruit_name(tier)
        tier_str = t("go_tier_fmt", name=fruit_name, tier=tier)
        self.next_name_lbl.config(text=tier_str)

        cx = 90
        cy = 42
        r = min(28.0, cfg.radius * 0.75)

        # Soft background glowing lantern aura
        self.preview_canvas.create_oval(
            cx - r * 1.35, cy - r * 1.35, cx + r * 1.35, cy + r * 1.35,
            fill="#3D2817", outline="", tags="preview_glow"
        )

        diameter = min(60, int(cfg.radius * 1.6))
        photo = self.sm.get_fruit_sprite(tier, diameter, 0.0)
        if photo:
            self.preview_canvas.create_image(cx, cy, image=photo, tags="preview_fruit")
        else:
            self.preview_canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=cfg.color, outline=cfg.dark_color, width=1.8
            )

    def bump_score(self, score: int) -> None:
        """Plays a pop-scale bump animation on the score readout."""
        self.score_var.set(str(score))
        if self._bump_job:
            try:
                self.after_cancel(self._bump_job)
            except Exception:
                pass
            self._bump_job = None
        try:
            self.lbl_score.config(fg="#F59E0B", font=("Segoe UI", 18, "bold"))
            def _restore():
                self._bump_job = None
                try:
                    if self.winfo_exists() and self.lbl_score.winfo_exists():
                        self.lbl_score.config(fg="#FFFBEB", font=("Segoe UI", 16, "bold"))
                except Exception:
                    pass
            self._bump_job = self.after(160, _restore)
        except Exception:
            pass

    def set_score(self, score: int) -> None:
        self.score_var.set(str(score))

    def set_high_score(self, high_score: int) -> None:
        self.high_score_var.set(str(high_score))

    def set_sound_state(self, enabled: bool) -> None:
        self._is_sound_enabled = enabled
        self.sound_btn_text.set(t("btn_sound_on") if enabled else t("btn_sound_off"))

    def set_paused_state(self, is_paused: bool) -> None:
        self._is_paused = is_paused
        self.pause_btn_text.set(t("btn_resume_sidebar") if is_paused else t("btn_pause_sidebar"))

    def refresh_language(self) -> None:
        """Dynamically re-applies localized text to all sidebar labels and controls."""
        try:
            self.lbl_title.config(text=t("cafe_title"))
            self.lbl_subtitle.config(text=t("cafe_subtitle"))
            self.lbl_score_header.config(text=t("score_label"))
            self.lbl_best_header.config(text=t("best_harvest_label"))
            self.lbl_next_header.config(text=t("next_harvest_label"))
            self.lbl_evo_header.config(text=t("evolution_recipe_label"))
            self.btn_restart.config(text=t("btn_restart_sidebar"))
            if hasattr(self, "btn_settings"):
                self.btn_settings.config(text=t("btn_settings_sidebar"))
            help_text = f"{t('controls_title')}:\n{t('ctrl_aim')}\n{t('ctrl_drop')}\n{t('ctrl_shortcuts')}"
            self.lbl_help.config(text=help_text)
            self.set_sound_state(self._is_sound_enabled)
            self.set_paused_state(self._is_paused)
            self.update_next_preview(self._current_next_tier)
        except Exception:
            pass

    @staticmethod
    def load_high_score() -> int:
        if os.path.exists(HIGH_SCORE_FILE):
            try:
                with open(HIGH_SCORE_FILE, "r") as f:
                    return json.load(f).get("high_score", 0)
            except Exception:
                return 0
        return 0

    @staticmethod
    def save_high_score(high_score: int) -> None:
        try:
            with open(HIGH_SCORE_FILE, "w") as f:
                json.dump({"high_score": high_score}, f)
        except Exception:
            pass

    def destroy(self) -> None:
        if self._bump_job:
            try:
                self.after_cancel(self._bump_job)
            except Exception:
                pass
            self._bump_job = None
        super().destroy()
