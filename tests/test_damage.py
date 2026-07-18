import unittest

from backend.damage import (
    effective_resistance,
    resistance_multiplier,
    resolve_damage,
)


class DamagePipelineTests(unittest.TestCase):
    def test_positive_resistance_multiplier(self):
        self.assertAlmostEqual(resistance_multiplier(100), 0.5)
        self.assertAlmostEqual(resistance_multiplier(50), 2 / 3)

    def test_negative_resistance_multiplier(self):
        self.assertAlmostEqual(resistance_multiplier(-50), 4 / 3)

    def test_reduction_then_percent_then_flat_penetration(self):
        # 100 MR -> Q shred 85 -> Void Staff 51 -> Shadowflame flat pen 36.
        result = effective_resistance(
            100,
            reduction_pct=0.15,
            penetration_pct=0.40,
            flat_penetration=15,
        )
        self.assertAlmostEqual(result, 36)

    def test_true_damage_ignores_resistance(self):
        result = resolve_damage(100, "true", outgoing_multiplier=1.2, resistance=999)
        self.assertIsNone(result.effective_resistance)
        self.assertEqual(result.applied, 120)

    def test_damage_is_not_rounded_inside_pipeline(self):
        result = resolve_damage(247.4625, "physical", resistance=100)
        self.assertAlmostEqual(result.applied, 123.73125)
        self.assertNotEqual(result.applied, int(result.applied))

    def test_invalid_damage_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_damage(-1, "magic", resistance=100)
        with self.assertRaises(ValueError):
            resolve_damage(float("nan"), "magic", resistance=100)


if __name__ == "__main__":
    unittest.main()
