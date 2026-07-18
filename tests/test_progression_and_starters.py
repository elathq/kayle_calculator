import unittest

from backend.data.enemy_data import ENEMY_PRESETS, enemy_stats
from backend.data.items_data import item_list_for_api
from backend.data.kayle_data import default_ability_ranks
from backend.engine import Simulation


ENEMY = {"hp": 3500, "armor": 100, "mr": 100}


class ProgressionAndStarterItemTests(unittest.TestCase):
    def test_enemy_presets_use_pinned_data_dragon_class_averages(self):
        source_values = {
            "squishy": {
                "hp": (604.11, 102.62),
                "armor": (25.97, 4.51),
                "mr": (30.06, 1.41),
            },
            "average": {
                "hp": (617.08, 103.93),
                "armor": (29.57, 4.54),
                "mr": (30.73, 1.68),
            },
            "tank": {
                "hp": (632.42, 105.46),
                "armor": (34.02, 4.57),
                "mr": (31.36, 1.99),
            },
        }
        level_eighteen = {
            "squishy": {"hp": 2348.7, "armor": 102.6, "mr": 54.0},
            "average": {"hp": 2383.9, "armor": 106.8, "mr": 59.3},
            "tank": {"hp": 2425.2, "armor": 111.7, "mr": 65.2},
        }

        for key, stats in source_values.items():
            for stat, (base, growth) in stats.items():
                self.assertEqual(ENEMY_PRESETS[key][stat]["base"], base)
                self.assertEqual(ENEMY_PRESETS[key][stat]["growth"], growth)
            scaled = enemy_stats(key, 18)
            for stat, expected in level_eighteen[key].items():
                self.assertEqual(scaled[stat], expected)
            self.assertEqual(scaled["bonus_hp"], 0.0)

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
            ["swiftmarch", "spellslingers_shoes", "gunmetal_greaves"],
            ENEMY, [], {},
        )
        self.assertEqual(top_quest.items, [])
        self.assertTrue(any("mid role quest" in warning
                            for warning in top_quest.warnings))

    def test_attack_speed_boots_shorten_combos_but_swifties_do_not_add_damage(self):
        combo = [{"type": "AA"}, {"type": "AA"}, {"type": "AA"}]
        ranks = default_ability_ranks(18)

        baseline = Simulation(18, ranks, [], ENEMY, combo, {}).run()
        swifties_sim = Simulation(
            18, ranks, ["boots_of_swiftness"], ENEMY, combo, {})
        berserkers_sim = Simulation(
            18, ranks, ["berserkers_greaves"], ENEMY, combo, {})
        gunmetal_sim = Simulation(
            18, ranks, ["gunmetal_greaves"], ENEMY, combo, {})

        swifties = swifties_sim.run()
        berserkers = berserkers_sim.run()
        gunmetal = gunmetal_sim.run()

        self.assertEqual(swifties_sim.item_as, 0)
        self.assertEqual(swifties_sim.slow_resist, 25)
        self.assertAlmostEqual(swifties_sim.current_movement_speed, 426.2)
        self.assertFalse(swifties_sim.has_swiftmarch)
        self.assertEqual(swifties_sim.swiftmarch_force, 0)
        self.assertEqual(swifties["total_damage"], baseline["total_damage"])
        self.assertEqual(swifties["duration"], baseline["duration"])

        self.assertEqual(berserkers_sim.item_as, 25)
        self.assertAlmostEqual(berserkers_sim.current_movement_speed, 417.4)
        self.assertEqual(berserkers["total_damage"], baseline["total_damage"])
        self.assertLess(berserkers["duration"], baseline["duration"])
        self.assertGreater(berserkers["dps"], baseline["dps"])

        self.assertEqual(gunmetal_sim.item_as, 40)
        self.assertEqual(gunmetal_sim.life_steal, 0.05)
        self.assertTrue(gunmetal_sim.mid_role_quest_completed)
        self.assertEqual(gunmetal["total_damage"], baseline["total_damage"])
        self.assertLess(gunmetal["duration"], berserkers["duration"])
        self.assertGreater(gunmetal["dps"], berserkers["dps"])
        self.assertGreater(gunmetal["healing"], 0)

    def test_berserkers_dps_matches_level_six_practice_tool_window(self):
        enemy = {
            "hp": 1000, "current_hp": 1000, "bonus_hp": 0,
            "armor": 30, "mr": 30,
        }
        options = {
            "rune_ids": [8021, 9104],
            "shards": ["attack_speed", "adaptive", "health"],
            "legend_stacks": 0,
            "pre_stacked_zeal": False,
            "fleet_starts_energized": True,
        }
        ranks = default_ability_ranks(6)
        items = ["nashors_tooth", "berserkers_greaves"]

        single = Simulation(
            6, ranks, items, enemy, [{"type": "AA"}], options).run()
        six = Simulation(
            6, ranks, items, enemy, [{"type": "AA"}] * 6, options).run()

        # Practice Tool isolation: one AA displays 93 total / 93 DPS. Six AAs
        # display 559 total / 153 DPS because the trailing recovery after AA 6
        # is excluded from its first-to-last-hit timer.
        self.assertEqual(single["total_damage"], 93.1)
        self.assertEqual(single["duration"], 1.0)
        self.assertEqual(single["dps"], 93.1)
        self.assertEqual(six["total_damage"], 558.58)
        self.assertEqual(six["duration"], 3.652)
        self.assertEqual(six["dps"], 153.0)
        self.assertGreater(six["timeline_duration"], six["duration"])


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
            "boots_of_swiftness", "berserkers_greaves", "gunmetal_greaves",
        }.issubset(keys))


if __name__ == "__main__":
    unittest.main()
