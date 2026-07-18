import unittest

from backend.data.items_data import item_list_for_api
from backend.data.kayle_data import default_ability_ranks
from backend.engine import Simulation


ENEMY = {"hp": 3500, "armor": 100, "mr": 100}


class ProgressionAndStarterItemTests(unittest.TestCase):
    def test_default_skill_order_starts_e_q_w_then_maxes_q_e_w(self):
        expected = {
            1: {"Q": 0, "W": 0, "E": 1, "R": 0},
            2: {"Q": 1, "W": 0, "E": 1, "R": 0},
            3: {"Q": 1, "W": 1, "E": 1, "R": 0},
            9: {"Q": 5, "W": 1, "E": 2, "R": 1},
            13: {"Q": 5, "W": 1, "E": 5, "R": 2},
            18: {"Q": 5, "W": 5, "E": 5, "R": 3},
            20: {"Q": 5, "W": 5, "E": 5, "R": 3},
        }
        for level, ranks in expected.items():
            self.assertEqual(default_ability_ranks(level), ranks)

    def test_absolute_focus_uses_linear_level_scaling_above_70_percent_hp(self):
        for level, adaptive_ap_reference in {
                1: 3.0,
                10: 17.2941176471,
                18: 30.0,
                20: 33.1764705882,
        }.items():
            sim = Simulation(
                level, default_ability_ranks(level), [], ENEMY, [],
                {"rune_ids": [8233], "kayle_hp_pct": 100},
            )
            self.assertEqual(sim.ap, 0)
            self.assertAlmostEqual(
                sim.bonus_ad, adaptive_ap_reference * 0.6, places=8)

        inactive = Simulation(
            18, default_ability_ranks(18), [], ENEMY, [],
            {"rune_ids": [8233], "kayle_hp_pct": 70},
        )
        self.assertEqual(inactive.ap, 0)
        self.assertEqual(inactive.bonus_ad, 0)

    def test_boots_and_starter_items_apply_current_stats(self):
        boots = Simulation(
            1, default_ability_ranks(1), ["boots"], ENEMY, [],
            {"pre_stacked_zeal": False})
        self.assertEqual(boots.current_movement_speed, 360.0)

        ring = Simulation(
            18, default_ability_ranks(18), ["dorans_ring"], ENEMY, [], {})
        self.assertEqual(ring.ap, 18)
        self.assertEqual(ring.bonus_hp, 90)

        bow = Simulation(
            18, default_ability_ranks(18), ["dorans_bow"], ENEMY, [], {})
        self.assertEqual(bow.bonus_ad, 8)
        self.assertEqual(bow.item_as, 15)
        self.assertEqual(bow.omnivamp, 0.015)

        blade = Simulation(
            18, default_ability_ranks(18), ["dorans_blade"], ENEMY, [], {})
        self.assertEqual(blade.bonus_ad, 10)
        self.assertEqual(blade.bonus_hp, 80)
        self.assertEqual(blade.omnivamp, 0.025)

        # Swiftmarch and Spellslinger's Shoes are mid-lane quest rewards. The
        # top-lane quest is what unlocks levels 19-20, so both states cannot
        # exist in one legal build.
        top_quest = Simulation(
            20, default_ability_ranks(20),
            ["swiftmarch", "spellslingers_shoes"], ENEMY, [], {},
        )
        self.assertEqual(top_quest.items, [])
        self.assertTrue(any("mid role quest" in warning
                            for warning in top_quest.warnings))


    def test_dark_seal_glory_is_configurable_and_capped_at_ten(self):
        empty = Simulation(
            18, default_ability_ranks(18), ["dark_seal"], ENEMY, [],
            {"dark_seal_stacks": 0},
        )
        full = Simulation(
            18, default_ability_ranks(18), ["dark_seal"], ENEMY, [],
            {"dark_seal_stacks": 10},
        )
        clamped = Simulation(
            18, default_ability_ranks(18), ["dark_seal"], ENEMY, [],
            {"dark_seal_stacks": 99},
        )
        with_rabadon = Simulation(
            18, default_ability_ranks(18),
            ["dark_seal", "rabadons_deathcap"], ENEMY, [],
            {"dark_seal_stacks": 10},
        )
        self.assertEqual(empty.ap, 15)
        self.assertEqual(full.ap, 55)
        self.assertEqual(clamped.ap, 55)
        self.assertEqual(with_rabadon.ap, 240.5)

    def test_only_one_starter_item_is_applied(self):
        sim = Simulation(
            18, default_ability_ranks(18),
            ["dorans_ring", "dorans_bow"], ENEMY, [], {},
        )
        self.assertEqual(sim.items, ["dorans_ring"])
        self.assertTrue(any("Limited to 1 Starter item" in warning
                            for warning in sim.warnings))

    def test_all_requested_items_are_exposed_to_the_picker(self):
        keys = {item["key"] for item in item_list_for_api()}
        self.assertTrue({
            "boots", "dorans_ring", "dorans_bow", "dorans_blade", "dark_seal",
        }.issubset(keys))


if __name__ == "__main__":
    unittest.main()
