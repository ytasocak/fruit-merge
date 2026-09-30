"""Automated integration tests for FruitMergeGame GUI, inputs, and state changes."""

import os
import time
import tkinter as tk
import unittest
from fruit_merge.constants import CONTAINER_LEFT, CONTAINER_RIGHT, DANGER_Y
from fruit_merge.game import FruitMergeGame, GameState
from fruit_merge.sprites import SpriteManager


class TestGameIntegration(unittest.TestCase):
    def setUp(self):
        SpriteManager.get_instance().clear_cache()
        self.root = tk.Tk()
        self.root.withdraw()  # Headless mode: hide window from display
        self.game = FruitMergeGame(self.root)

    def tearDown(self):
        try:
            self.game.destroy()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        SpriteManager.get_instance().clear_cache()

    def test_initial_state_and_start_flow(self):
        # Default initialization launches into the opening cafe screen
        self.assertEqual(self.game.state, GameState.START)
        self.assertEqual(self.game.score, 0)
        self.assertIn(self.game.current_tier, range(1, 6))
        self.assertIn(self.game.next_tier, range(1, 6))
        self.assertEqual(len(self.game.visuals), 0)
        self.assertGreater(len(self.game.overlay_items), 0)

        # Transitioning to game clears overlay and activates AIMING state
        self.game.start_game()
        self.assertEqual(self.game.state, GameState.AIMING)
        self.assertEqual(len(self.game.overlay_items), 0)

    def test_aim_nudge_and_clamping(self):
        self.game.start_game()
        # Move aim left beyond boundary
        self.game._nudge_aim(-1000)
        self.root.update()
        self.assertGreaterEqual(self.game.aim_x, CONTAINER_LEFT)

        # Move aim right beyond boundary
        self.game._nudge_aim(2000)
        self.root.update()
        self.assertLessEqual(self.game.aim_x, CONTAINER_RIGHT)

    def test_drop_and_cooldown(self):
        self.game.start_game()
        initial_next = self.game.next_tier
        self.game._trigger_drop()
        self.root.update()

        # Should be in cooldown
        self.assertEqual(self.game.state, GameState.COOLDOWN)
        # Should have spawned 1 fruit
        self.assertEqual(len(self.game.physics.fruits), 1)
        self.assertEqual(len(self.game.visuals), 1)

        # Previous next_tier should now be current_tier
        self.assertEqual(self.game.current_tier, initial_next)

    def test_pause_and_resume(self):
        self.game.start_game()
        self.game.toggle_pause()
        self.root.update()
        self.assertEqual(self.game.state, GameState.PAUSED)
        self.assertGreater(len(self.game.overlay_items), 0)

        self.game.toggle_pause()
        self.root.update()
        self.assertEqual(self.game.state, GameState.AIMING)
        self.assertEqual(len(self.game.overlay_items), 0)

    def test_restart_resets_simulation(self):
        self.game.start_game()
        # Spawn some fruits
        self.game._trigger_drop()
        self.root.update()
        self.assertGreater(len(self.game.visuals), 0)

        # Restart directly to gameplay
        self.game.restart(start_in_menu=False)
        self.root.update()
        self.assertEqual(self.game.state, GameState.AIMING)
        self.assertEqual(self.game.score, 0)
        self.assertEqual(len(self.game.physics.fruits), 0)
        self.assertEqual(len(self.game.visuals), 0)

    def test_multiple_frame_ticks(self):
        self.game.start_game()
        # Run 20 updates
        for _ in range(20):
            self.root.update_idletasks()
            self.root.update()
            time.sleep(0.01)
        self.assertTrue(self.game._running)

    def test_window_resize_and_scaling(self):
        self.game.start_game()
        # Simulate canvas resizing to a larger resolution (e.g. 920x1300)
        event = tk.Event()
        event.width = 920
        event.height = 1300
        self.game._on_canvas_configure(event)

        # Scale should be 2.0 (920/460 = 2.0, 1300/650 = 2.0)
        self.assertAlmostEqual(self.game.scale, 2.0, places=2)
        self.assertAlmostEqual(self.game.offset_x, 0.0, places=2)
        self.assertAlmostEqual(self.game.offset_y, 0.0, places=2)

        # Test mouse aim projection under 2x scale
        mock_mouse_event = tk.Event()
        mock_mouse_event.x = 400  # Screen X
        self.game._on_mouse_move(mock_mouse_event)
        # Virtual X should be 400 / 2.0 = 200
        self.assertAlmostEqual(self.game.aim_x, 200.0, places=1)

        # Spawn fruit and verify update works under 2x scale
        fid = self.game.physics.spawn_fruit(1, 200, 300)
        self.game.physics.step(1.0 / 60.0)
        self.root.update_idletasks()
        self.root.update()
        self.assertTrue(self.game._running)

    def test_combo_streak_and_screen_shake(self):
        from fruit_merge.physics import MergeEvent
        self.game.start_game()
        self.assertEqual(self.game.combo_count, 0)
        self.assertEqual(self.game.shake_trauma, 0.0)

        # Trigger first merge
        mock_ev = MergeEvent(tier=1, new_tier=2, x=200, y=300, score=4, new_fruit_id=99)
        self.game._handle_merges([mock_ev])
        self.assertEqual(self.game.combo_count, 1)
        self.assertEqual(self.game.score, 4)
        self.assertGreater(self.game.shake_trauma, 0.0)

        # Trigger rapid second merge within combo window
        mock_ev2 = MergeEvent(tier=2, new_tier=3, x=200, y=300, score=8, new_fruit_id=100)
        self.game._handle_merges([mock_ev2])
        self.assertEqual(self.game.combo_count, 2)
        # Score = 4 + (8 * 2) = 20
        self.assertEqual(self.game.score, 20)
        # Banner spawned in particles
        self.assertGreaterEqual(len(self.game.particles.combos), 1)
        self.assertGreaterEqual(len(self.game.particles.shockwaves), 2)

    def test_game_over_and_menu_navigation(self):
        self.game.start_game()
        self.assertEqual(self.game.state, GameState.AIMING)

        # Trigger game over
        self.game._trigger_game_over()
        self.root.update()
        self.assertEqual(self.game.state, GameState.GAME_OVER)
        self.assertGreater(len(self.game.overlay_items), 0)

        # Navigate back to start screen
        self.game.return_to_start()
        self.root.update()
        self.assertEqual(self.game.state, GameState.START)
        self.assertEqual(self.game.score, 0)
        self.assertGreater(len(self.game.overlay_items), 0)

    def test_session_achievement_tracking(self):
        from fruit_merge.physics import MergeEvent
        self.game.start_game()
        self.assertEqual(self.game.highest_tier_reached, 1)
        self.assertEqual(self.game.total_merges, 0)
        self.assertEqual(self.game.max_combo, 0)

        # Simulate tier 1 -> tier 2 merge
        ev1 = MergeEvent(tier=1, new_tier=2, x=200, y=300, score=4, new_fruit_id=1)
        self.game._handle_merges([ev1])
        self.assertEqual(self.game.highest_tier_reached, 2)
        self.assertEqual(self.game.total_merges, 1)
        self.assertEqual(self.game.max_combo, 1)

        # Simulate tier 2 -> tier 5 merge
        ev2 = MergeEvent(tier=4, new_tier=5, x=200, y=300, score=32, new_fruit_id=2)
        self.game._handle_merges([ev2])
        self.assertEqual(self.game.highest_tier_reached, 5)
        self.assertEqual(self.game.total_merges, 2)
        self.assertEqual(self.game.max_combo, 2)

    def test_buttons_strictly_required_for_state_transitions(self):
        # 1. In START state, background clicks and spacebar must NOT start the game
        self.assertEqual(self.game.state, GameState.START)
        dummy_event = tk.Event()
        dummy_event.x = 100
        dummy_event.y = 100
        self.game._on_mouse_click(dummy_event)
        self.root.update()
        self.assertEqual(self.game.state, GameState.START)

        self.game._on_space_pressed()
        self.root.update()
        self.assertEqual(self.game.state, GameState.START)

        # Transitioning via start_game starts gameplay without ghost-dropping a fruit
        self.game.start_game()
        self.root.update()
        self.assertEqual(self.game.state, GameState.AIMING)
        self.assertEqual(len(self.game.physics.fruits), 0)

        # 2. In PAUSED state, canvas clicks must NOT unpause
        self.game.toggle_pause()
        self.assertEqual(self.game.state, GameState.PAUSED)
        self.game._on_mouse_click(dummy_event)
        self.root.update()
        self.assertEqual(self.game.state, GameState.PAUSED)
        self.game.toggle_pause()
        self.assertEqual(self.game.state, GameState.AIMING)

        # 3. In GAME_OVER state, canvas clicks and spacebar must NOT restart
        self.game._trigger_game_over()
        self.assertEqual(self.game.state, GameState.GAME_OVER)
        self.game._on_mouse_click(dummy_event)
        self.root.update()
        self.assertEqual(self.game.state, GameState.GAME_OVER)
        self.game._on_space_pressed()
        self.root.update()
        self.assertEqual(self.game.state, GameState.GAME_OVER)

    def test_i18n_default_and_language_toggle(self):
        from fruit_merge.i18n import I18n, t, get_fruit_name
        # Ensure reset to en
        I18n.get_instance().set_language("en")
        self.assertEqual(I18n.get_instance().language, "en")
        self.assertEqual(t("score_label"), "📋 SCORE")
        self.assertEqual(get_fruit_name(1), "Cherry")

        # Switch to Turkish
        self.game._select_language("tr")
        self.root.update()
        self.assertEqual(I18n.get_instance().language, "tr")
        self.assertEqual(t("score_label"), "📋 SKOR")
        self.assertEqual(get_fruit_name(1), "Kiraz")
        self.assertIn("SKOR", self.game.sidebar.lbl_score_header.cget("text"))

        # Switch back to English
        self.game._select_language("en")
        self.root.update()
        self.assertEqual(I18n.get_instance().language, "en")
        self.assertEqual(t("score_label"), "📋 SCORE")
        self.assertEqual(get_fruit_name(1), "Cherry")
        self.assertIn("SCORE", self.game.sidebar.lbl_score_header.cget("text"))

    def test_settings_modal_flow(self):
        # Open settings from start screen
        self.assertEqual(self.game.state, GameState.START)
        self.game.open_settings()
        self.root.update()
        self.assertEqual(self.game.state, GameState.SETTINGS)
        self.assertGreater(len(self.game.overlay_items), 0)

        # Close settings returns to start
        self.game.close_settings()
        self.root.update()
        self.assertEqual(self.game.state, GameState.START)

        # Open settings during active play returns to play
        self.game.start_game()
        self.assertEqual(self.game.state, GameState.AIMING)
        self.game.open_settings()
        self.root.update()
        self.assertEqual(self.game.state, GameState.SETTINGS)

        self.game.close_settings()
        self.root.update()
        self.assertEqual(self.game.state, GameState.AIMING)

    def test_project_paths_exist(self):
        from fruit_merge.constants import PROJECT_ROOT, HIGH_SCORE_FILE
        from fruit_merge.i18n import SETTINGS_FILE
        from fruit_merge.sprites import ASSETS_DIR, FRUITS_DIR, BG_PATH

        self.assertTrue(os.path.isdir(PROJECT_ROOT))
        self.assertTrue(os.path.isdir(ASSETS_DIR))
        self.assertTrue(os.path.isdir(FRUITS_DIR))
        self.assertTrue(os.path.isfile(BG_PATH))
        self.assertTrue(HIGH_SCORE_FILE.startswith(PROJECT_ROOT))
        self.assertTrue(SETTINGS_FILE.startswith(PROJECT_ROOT))

    def test_package_main_module(self):
        import fruit_merge.__main__ as pkg_main
        self.assertTrue(hasattr(pkg_main, "main"))


if __name__ == "__main__":
    unittest.main()
