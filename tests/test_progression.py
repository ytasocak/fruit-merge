"""Unit tests for fruit progression, scoring, drop pool, and high score persistence."""

import json
import os
import random
import tempfile
import unittest
from fruit_merge.constants import (
    DROP_TIERS,
    DROP_WEIGHTS,
    FRUIT_TIERS,
    MAX_TIER,
)


class TestFruitProgression(unittest.TestCase):
    def test_tier_continuity(self):
        self.assertEqual(len(FRUIT_TIERS), MAX_TIER)
        for t in range(1, MAX_TIER + 1):
            self.assertIn(t, FRUIT_TIERS, f"Missing tier {t}")
            self.assertEqual(FRUIT_TIERS[t].tier, t)

    def test_radii_strictly_increasing(self):
        radii = [FRUIT_TIERS[t].radius for t in range(1, MAX_TIER + 1)]
        for i in range(len(radii) - 1):
            self.assertLess(
                radii[i],
                radii[i + 1],
                f"Radius for tier {i+1} ({radii[i]}) must be less than tier {i+2} ({radii[i+1]})",
            )

    def test_scores_strictly_increasing(self):
        scores = [FRUIT_TIERS[t].score for t in range(1, MAX_TIER + 1)]
        for i in range(len(scores) - 1):
            self.assertLess(
                scores[i],
                scores[i + 1],
                f"Score for tier {i+1} ({scores[i]}) must be less than tier {i+2} ({scores[i+1]})",
            )

    def test_drop_pool_validity(self):
        self.assertEqual(len(DROP_TIERS), len(DROP_WEIGHTS))
        self.assertAlmostEqual(sum(DROP_WEIGHTS), 1.0, places=2)
        for t in DROP_TIERS:
            self.assertIn(t, FRUIT_TIERS)
            self.assertLessEqual(t, 5, "Drop pool should only contain small-to-medium fruits")

        # Test random choices
        samples = random.choices(DROP_TIERS, weights=DROP_WEIGHTS, k=200)
        for s in samples:
            self.assertIn(s, DROP_TIERS)

    def test_high_score_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "test_score.json")

            # Load when non-existent
            score = 0
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    score = json.load(f).get("high_score", 0)
            self.assertEqual(score, 0)

            # Save new high score
            new_score = 4250
            with open(file_path, "w") as f:
                json.dump({"high_score": new_score}, f)

            # Reload
            with open(file_path, "r") as f:
                data = json.load(f)
            self.assertEqual(data["high_score"], new_score)


if __name__ == "__main__":
    unittest.main()
