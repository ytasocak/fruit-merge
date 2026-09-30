"""Internationalization (i18n) and localization system for Fruit Merge.

Supports English (default) and Turkish, with persistent settings and dynamic UI updates.
"""

import json
import os
from typing import Dict, Any, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(PROJECT_ROOT, "settings.json")
DEFAULT_LANGUAGE = "en"

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # App & Window
        "window_title": "Fruit Merge",

        # Sidebar Dashboard
        "cafe_title": "☕ MAGIC FRUIT CAFE 🍎",
        "cafe_subtitle": "✦ Artisan Kitchen & Harvest ✦",
        "score_label": "📋 SCORE",
        "best_harvest_label": "🏆 BEST HARVEST",
        "next_harvest_label": "NEXT HARVEST",
        "evolution_recipe_label": "EVOLUTION RECIPE",
        "controls_title": "KITCHEN CONTROLS",
        "ctrl_aim": "• Mouse or A / D to aim",
        "ctrl_drop": "• Click or Space to drop",
        "ctrl_shortcuts": "• P: Pause • R: Restart • F11: Fullscreen",
        "btn_restart_sidebar": "🔄 New Game (R)",
        "btn_pause_sidebar": "⏸ Pause (P)",
        "btn_resume_sidebar": "▶ Resume (P)",
        "btn_sound_on": "🔊 Sound: ON",
        "btn_sound_off": "🔇 Sound: OFF",
        "btn_settings_sidebar": "⚙ Settings (O)",

        # Start Screen
        "start_cafe_header": "☕ THE MAGIC FRUIT CAFE & KITCHEN",
        "start_game_title": "FRUIT MERGE",
        "badge_tasty": "DELICIOUS",
        "badge_harvest": "HARVEST",
        "high_score_pill": "🏆 HIGH SCORE: {score}",
        "rule_1": "🎯 Aim with mouse: Click to drop fruit",
        "rule_2": "✨ Merge matching fruits to reach Watermelon!",
        "rule_3": "⚠️ Don't overflow! 3s above red line ends game",
        "rule_4": "⌨️ [A/D] Aim  [Space] Drop  [P] Pause  [R] Restart",
        "btn_start_game": "▶ START GAME",
        "btn_start_settings": "⚙ SETTINGS",
        "start_hint": "Click 'START GAME' button above to begin",

        # Game Over Screen
        "go_subtitle": "☕ CAFE OVERFLOW • KITCHEN CLOSED",
        "go_title": "HARVEST COMPLETE",
        "go_score_label": "TOTAL HARVEST SCORE",
        "go_new_record": "🏆 NEW RECORD! CONGRATULATIONS!",
        "go_best_score": "🏆 Best Harvest: {score}",
        "go_biggest_fruit_label": "Biggest Fruit Unlocked:",
        "go_tier_fmt": "{name} (Tier {tier})",
        "go_stats_fmt": "Total Merges: {merges}  •  Max Combo: x{combo} 🔥",
        "btn_play_again": "🔄 PLAY AGAIN",
        "btn_main_menu": "🏠 MAIN MENU",
        "go_hint": "[R] Play Again   •   [M] Main Menu",

        # Pause Screen
        "pause_title": "☕ CAFE ON BREAK",
        "pause_current_score": "Current Score: {score}",
        "btn_resume": "▶ RESUME",
        "btn_restart": "🔄 RESTART",
        "btn_settings": "⚙ SETTINGS",
        "pause_hint": "[P] Resume   •   [R] Restart   •   [M] Menu",

        # Settings Screen / Modal
        "settings_title": "⚙ GAME SETTINGS",
        "settings_lang_label": "LANGUAGE / DİL",
        "settings_sound_label": "AUDIO & SOUND EFFECTS",
        "settings_sound_toggle_on": "🔊 Sound Effects: ON",
        "settings_sound_toggle_off": "🔇 Sound Effects: OFF",
        "btn_save_close": "✓ SAVE & CLOSE",
        "settings_hint": "Select language and audio preferences",

        # In-Game Warnings & Overflows
        "danger_warning": "⚠️ CAFE OVERFLOW WARNING: {remaining:.1f}s",

        # Fruit Names
        "fruit_1": "Cherry",
        "fruit_2": "Strawberry",
        "fruit_3": "Grape",
        "fruit_4": "Dekopon",
        "fruit_5": "Orange",
        "fruit_6": "Apple",
        "fruit_7": "Pear",
        "fruit_8": "Peach",
        "fruit_9": "Pineapple",
        "fruit_10": "Melon",
        "fruit_11": "Watermelon",
    },
    "tr": {
        # App & Window
        "window_title": "Fruit Merge",

        # Sidebar Dashboard
        "cafe_title": "☕ MAGIC FRUIT CAFE 🍎",
        "cafe_subtitle": "✦ Usta Kafe & Hasat ✦",
        "score_label": "📋 SKOR",
        "best_harvest_label": "🏆 EN İYİ SKOR",
        "next_harvest_label": "SIRADAKİ MEYVE",
        "evolution_recipe_label": "EVRİM SIRASI",
        "controls_title": "KAFE KONTROLLERİ",
        "ctrl_aim": "• Fare veya A / D: Nişan al",
        "ctrl_drop": "• Tıkla veya Boşluk: Meyveyi bırak",
        "ctrl_shortcuts": "• P: Mola • R: Yeniden • F11: Tam Ekran",
        "btn_restart_sidebar": "🔄 Yeni Oyun (R)",
        "btn_pause_sidebar": "⏸ Mola (P)",
        "btn_resume_sidebar": "▶ Devam Et (P)",
        "btn_sound_on": "🔊 Ses: AÇIK",
        "btn_sound_off": "🔇 Ses: KAPALI",
        "btn_settings_sidebar": "⚙ Ayarlar (O)",

        # Start Screen
        "start_cafe_header": "☕ THE MAGIC FRUIT CAFE & KITCHEN",
        "start_game_title": "MEYVE BİRLEŞTİRME",
        "badge_tasty": "LEZZETLİ",
        "badge_harvest": "HASAT",
        "high_score_pill": "🏆 EN YÜKSEK SKOR: {score}",
        "rule_1": "🎯 Fareyle nişan al: Tıkla ve meyveyi bırak",
        "rule_2": "✨ Aynı meyveleri birleştir, dev Karpuz'a ulaş!",
        "rule_3": "⚠️ Taşırma! Kırmızı çizgide 3 sn kalırsa biter",
        "rule_4": "⌨️ [A/D] Nişan  [Boşluk] At  [P] Mola  [R] Yeniden",
        "btn_start_game": "▶ OYUNA BAŞLA",
        "btn_start_settings": "⚙ AYARLAR",
        "start_hint": "Başlamak için 'OYUNA BAŞLA' butonuna tıkla",

        # Game Over Screen
        "go_subtitle": "☕ KAFE KAPANDI • KITCHEN OVERFLOW",
        "go_title": "HASAT TAMAMLANDI",
        "go_score_label": "TOPLANAN HASAT SKORU",
        "go_new_record": "🏆 YENİ REKOR! TEBRİKLER!",
        "go_best_score": "🏆 En Yüksek Skor: {score}",
        "go_biggest_fruit_label": "Ulaşılan En Büyük Meyve:",
        "go_tier_fmt": "{name} (Seviye {tier})",
        "go_stats_fmt": "Toplam Birleşme: {merges}  •  Maks Kombo: x{combo} 🔥",
        "btn_play_again": "🔄 YENİDEN OYNA",
        "btn_main_menu": "🏠 ANA MENÜ",
        "go_hint": "[R] Yeniden Oyna   •   [M] Ana Menü",

        # Pause Screen
        "pause_title": "☕ KAFE MOLA VERDİ",
        "pause_current_score": "Şu Anki Skor: {score}",
        "btn_resume": "▶ DEVAM ET",
        "btn_restart": "🔄 YENİDEN BAŞLA",
        "btn_settings": "⚙ AYARLAR",
        "pause_hint": "[P] Devam   •   [R] Yeniden   •   [M] Menü",

        # Settings Screen / Modal
        "settings_title": "⚙ OYUN AYARLARI",
        "settings_lang_label": "DİL / LANGUAGE",
        "settings_sound_label": "SES & EFEKTLER",
        "settings_sound_toggle_on": "🔊 Ses Efektleri: AÇIK",
        "settings_sound_toggle_off": "🔇 Ses Efektleri: KAPALI",
        "btn_save_close": "✓ KAYDET & KAPAT",
        "settings_hint": "Tercih ettiğiniz dili ve ses ayarlarını seçin",

        # In-Game Warnings & Overflows
        "danger_warning": "⚠️ TAŞMA UYARISI: {remaining:.1f}s",

        # Fruit Names
        "fruit_1": "Kiraz",
        "fruit_2": "Çilek",
        "fruit_3": "Üzüm",
        "fruit_4": "Dekopon",
        "fruit_5": "Portakal",
        "fruit_6": "Elma",
        "fruit_7": "Armut",
        "fruit_8": "Şeftali",
        "fruit_9": "Ananas",
        "fruit_10": "Kavun",
        "fruit_11": "Karpuz",
    },
}


class I18n:
    """Manages language state and translation lookups."""

    _instance: Optional["I18n"] = None

    def __init__(self):
        self.language: str = DEFAULT_LANGUAGE
        self.load_settings()

    @classmethod
    def get_instance(cls) -> "I18n":
        if cls._instance is None:
            cls._instance = I18n()
        return cls._instance

    def load_settings(self) -> None:
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    lang = data.get("language", DEFAULT_LANGUAGE)
                    if lang in TRANSLATIONS:
                        self.language = lang
                    else:
                        self.language = DEFAULT_LANGUAGE
            except Exception:
                self.language = DEFAULT_LANGUAGE
        else:
            self.language = DEFAULT_LANGUAGE

    def save_settings(self) -> None:
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({"language": self.language}, f, indent=2)
        except Exception:
            pass

    def set_language(self, lang: str) -> None:
        if lang in TRANSLATIONS:
            self.language = lang
            self.save_settings()

    def t(self, key: str, **kwargs) -> str:
        lang_dict = TRANSLATIONS.get(self.language, TRANSLATIONS[DEFAULT_LANGUAGE])
        text = lang_dict.get(key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key))
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    def get_fruit_name(self, tier: int) -> str:
        return self.t(f"fruit_{tier}")


def t(key: str, **kwargs) -> str:
    """Shortcut function to fetch translation for current language."""
    return I18n.get_instance().t(key, **kwargs)


def get_fruit_name(tier: int) -> str:
    """Shortcut function to fetch translated fruit name."""
    return I18n.get_instance().get_fruit_name(tier)
