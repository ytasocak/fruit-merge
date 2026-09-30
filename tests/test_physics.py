"""Automated unit tests for Pymunk physics, collision detection, and merging."""

import unittest
from fruit_merge.constants import (
    CONTAINER_BOTTOM,
    CONTAINER_LEFT,
    CONTAINER_RIGHT,
    DANGER_Y,
    FRUIT_TIERS,
    MAX_TIER,
)
from fruit_merge.physics import MergeEvent, PhysicsManager


class TestPhysicsManager(unittest.TestCase):
    def setUp(self):
        self.pm = PhysicsManager()

    def test_spawn_and_state(self):
        fid = self.pm.spawn_fruit(1, 200, 300)
        self.assertIn(fid, self.pm.fruits)
        state = self.pm.get_fruit_state(fid)
        self.assertIsNotNone(state)
        x, y, angle, tier = state
        self.assertEqual(tier, 1)
        self.assertAlmostEqual(x, 200, delta=1.0)
        self.assertAlmostEqual(y, 300, delta=1.0)

    def test_merge_identical_tiers(self):
        # Spawn two tier-1 fruits overlapping/colliding
        id1 = self.pm.spawn_fruit(1, 200, 300)
        id2 = self.pm.spawn_fruit(1, 200, 315)

        merges = []
        for _ in range(60):
            events = self.pm.step(1.0 / 60.0)
            if events:
                merges.extend(events)

        self.assertEqual(len(merges), 1, "Exactly one merge event should occur")
        ev = merges[0]
        self.assertEqual(ev.tier, 1)
        self.assertEqual(ev.new_tier, 2)
        self.assertEqual(ev.score, FRUIT_TIERS[2].score)
        self.assertEqual(len(self.pm.fruits), 1, "Should leave exactly 1 merged fruit")

        # Verify the new fruit is tier 2
        remaining_id = list(self.pm.fruits.keys())[0]
        _, _, remaining_tier = self.pm.fruits[remaining_id]
        self.assertEqual(remaining_tier, 2)

    def test_different_tiers_do_not_merge(self):
        # Spawn tier 1 and tier 2 touching
        id1 = self.pm.spawn_fruit(1, 200, 300)
        id2 = self.pm.spawn_fruit(2, 200, 325)

        merges = []
        for _ in range(60):
            events = self.pm.step(1.0 / 60.0)
            if events:
                merges.extend(events)

        self.assertEqual(len(merges), 0, "Different tiers must not merge")
        self.assertEqual(len(self.pm.fruits), 2, "Both fruits must remain")

    def test_max_tier_merge(self):
        # Spawn two max tier watermelons touching
        id1 = self.pm.spawn_fruit(MAX_TIER, 200, 300)
        id2 = self.pm.spawn_fruit(MAX_TIER, 200, 350)

        merges = []
        for _ in range(60):
            events = self.pm.step(1.0 / 60.0)
            if events:
                merges.extend(events)

        self.assertEqual(len(merges), 1)
        ev = merges[0]
        self.assertEqual(ev.tier, MAX_TIER)
        self.assertIsNone(ev.new_tier)
        self.assertEqual(ev.score, 5000)
        self.assertEqual(len(self.pm.fruits), 0, "Both watermelons pop and clear")

    def test_overflow_check(self):
        # When fruit is below danger line, no overflow
        fid = self.pm.spawn_fruit(1, 200, DANGER_Y + 100)
        # Settle it
        for _ in range(30):
            self.pm.step(1.0 / 60.0)
        overflowing, _ = self.pm.check_overflow(DANGER_Y)
        self.assertFalse(overflowing)

        # When fruit rests above danger line with low velocity, overflow is detected
        self.pm.reset()
        fid_top = self.pm.spawn_fruit(5, 200, DANGER_Y - 20, vx=0, vy=0)
        # Fruit top is DANGER_Y - 20 - radius < DANGER_Y
        overflowing, highest_y = self.pm.check_overflow(DANGER_Y)
        self.assertTrue(overflowing)
        self.assertLess(highest_y, DANGER_Y)

    def test_reset(self):
        self.pm.spawn_fruit(1, 200, 300)
        self.pm.spawn_fruit(2, 250, 300)
        self.assertEqual(len(self.pm.fruits), 2)
        self.pm.reset()
        self.assertEqual(len(self.pm.fruits), 0)


if __name__ == "__main__":
    unittest.main()
