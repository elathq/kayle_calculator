import copy
import unittest

from backend.data import ICON_VERSION
from backend.data.items_data import ITEMS, item_list_for_api, validate_item_catalog
from backend.data.kayle_data import KAYLE_AS, default_ability_ranks, kayle_stats_at
from backend.engine import Simulation, simulate_build
from backend.item_rules import ItemBuildValidationError


NEW_ITEMS = {
    "cosmic_drive": 4629,
    "riftmaker": 4633,
    "kraken_slayer": 6672,
    "terminus": 3302,
    "infinity_edge": 3031,
    "blade_of_the_ruined_king": 3153,
    "bloodthirster": 3072,
    "bloodletters_curse": 8010,
    "hexoptics_c44": 2523,
    "phantom_dancer": 3046,
    "rapid_firecannon": 3094,
    "experimental_hexplate": 3073,
    "essence_reaver": 3508,
    "yun_tal_wildarrows": 3032,
    "navori_flickerblade": 6675,
    "lord_dominiks_regards": 3036,
    "mortal_reminder": 3033,
    "wits_end": 3091,
    "statikk_shiv": 3087,
    "stormrazor": 3097,
    "fiendhunter_bolts": 2512,
    "stormsurge": 4646,
}


def run(items, combo, *, level=18, enemy=None, ranks=None, options=None):
    enemy = enemy or {
        "hp": 5000, "current_hp": 5000, "bonus_hp": 0,
        "armor": 100, "mr": 100,
    }
    options = {
        "pre_stacked_zeal": True,
        "fleet_starts_energized": True,
        **(options or {}),
    }
    return simulate_build(
        level,
        ranks or default_ability_ranks(level),
        items,
        enemy,
        combo,
        options,
    )


class AddedItemTests(unittest.TestCase):
    def test_item_catalog_schema_is_valid(self):
        self.assertTrue(validate_item_catalog())
        invalid = copy.deepcopy(ITEMS)
        invalid["blade_of_the_ruined_king"]["onhit_current_hp"][
            "ranged_ratio"] = "6%"
        with self.assertRaisesRegex(ValueError, "ranged_ratio"):
            validate_item_catalog(invalid)

    def test_all_added_items_are_in_the_picker_with_current_ids(self):
        api = {item["key"]: item for item in item_list_for_api()}
        for key, item_id in NEW_ITEMS.items():
            self.assertIn(key, ITEMS)
            self.assertIn(key, api)
            self.assertEqual(api[key]["id"], item_id)
            self.assertEqual(
                api[key]["icon"],
                f"icons/{item_id}.png?v={ICON_VERSION}",
            )

    def test_current_base_stats_and_item_families(self):
        self.assertEqual(ITEMS["cosmic_drive"]["stats"], {
            "ap": 70, "health": 350, "ability_haste": 25,
            "move_speed_pct": 4,
        })
        self.assertEqual(ITEMS["terminus"]["stats"], {"ad": 30, "attack_speed": 35})
        self.assertEqual(ITEMS["statikk_shiv"]["stats"]["ap"], 45)
        self.assertEqual(ITEMS["wits_end"]["stats"]["attack_speed"], 50)
        self.assertEqual(ITEMS["rapid_firecannon"]["stats"], {
            "attack_speed": 35, "crit_chance": 25, "move_speed_pct": 4,
        })
        self.assertEqual(ITEMS["experimental_hexplate"]["stats"], {
            "ad": 40, "attack_speed": 20, "health": 450,
            "ultimate_haste": 30,
        })
        self.assertEqual(ITEMS["essence_reaver"]["stats"], {
            "ad": 50, "ability_haste": 20, "crit_chance": 25,
        })
        self.assertEqual(ITEMS["yun_tal_wildarrows"]["stats"], {
            "ad": 50, "attack_speed": 40, "crit_chance": 0,
        })
        self.assertEqual(ITEMS["navori_flickerblade"]["stats"], {
            "attack_speed": 40, "crit_chance": 25, "move_speed_pct": 4,
        })
        self.assertEqual(ITEMS["bloodthirster"]["stats"], {
            "ad": 80, "life_steal": 0.15,
        })
        self.assertEqual(ITEMS["blade_of_the_ruined_king"]["stats"], {
            "ad": 40, "attack_speed": 25, "life_steal": 0.10,
        })
        self.assertEqual(ITEMS["blade_of_the_ruined_king"]["cost"], 3200)
        self.assertEqual(ITEMS["mortal_reminder"]["stats"], {
            "ad": 35, "armor_pen_pct": 0.30, "crit_chance": 25,
        })
        self.assertEqual(ITEMS["stormsurge"]["stats"], {
            "ap": 90, "magic_pen_flat": 15, "move_speed_pct": 6,
        })

        with self.assertRaisesRegex(ItemBuildValidationError, "Fatality"):
            Simulation(
                18, default_ability_ranks(18),
                ["terminus", "lord_dominiks_regards"],
                {"hp": 5000, "armor": 100, "mr": 100}, [], {},
            )
        with self.assertRaisesRegex(ItemBuildValidationError, "Fatality"):
            Simulation(
                18, default_ability_ranks(18),
                ["mortal_reminder", "lord_dominiks_regards"],
                {"hp": 5000, "armor": 100, "mr": 100}, [], {},
            )
        with self.assertRaisesRegex(ItemBuildValidationError, "Blight"):
            Simulation(
                18, default_ability_ranks(18),
                ["terminus", "bloodletters_curse"],
                {"hp": 5000, "armor": 100, "mr": 100}, [], {},
            )
        with self.assertRaisesRegex(ItemBuildValidationError, "Spellblade"):
            Simulation(
                18, default_ability_ranks(18),
                ["lich_bane", "essence_reaver"],
                {"hp": 5000, "armor": 100, "mr": 100}, [], {},
            )

    def test_infinity_edge_uses_expected_crit_damage(self):
        level = 10
        result = run(
            ["infinity_edge"], [{"type": "AA"}], level=level,
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0},
            enemy={"hp": 5000, "armor": 0, "mr": 0},
        )
        event = next(e for e in result["events"] if e["type"] == "physical")
        total_ad = kayle_stats_at(level)["base_ad"] + 75
        expected_multiplier = 1 + 0.25 * ((KAYLE_AS["crit_damage"] + 0.30) - 1)
        self.assertAlmostEqual(event["raw"], total_ad * expected_multiplier, places=3)
        self.assertEqual(result["stats"]["crit_chance"], 25.0)
        self.assertEqual(result["stats"]["crit_damage"], 230.0)

    def test_bloodthirster_applies_ad_and_life_steal(self):
        level = 1
        result = run(
            ["bloodthirster"], [{"type": "AA"}], level=level,
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0},
            enemy={"hp": 5000, "armor": 0, "mr": 0},
        )
        attack = next(
            event for event in result["events"]
            if event["type"] == "physical"
        )
        expected_attack = kayle_stats_at(level)["base_ad"] + 80
        self.assertAlmostEqual(attack["raw"], expected_attack, places=3)
        self.assertEqual(result["stats"]["life_steal"], 15.0)
        self.assertEqual(result["healing"], round(attack["dealt"] * 0.15, 1))

    def test_blade_uses_pre_attack_current_hp_and_melee_ranged_ratios(self):
        no_ranks = {"Q": 0, "W": 0, "E": 0, "R": 0}

        def mist_hit(level, current_hp):
            result = run(
                ["blade_of_the_ruined_king"],
                [{"type": "AA"}],
                level=level,
                ranks=no_ranks,
                enemy={
                    "hp": 10_000, "current_hp": current_hp,
                    "bonus_hp": 0, "armor": 0, "mr": 0,
                },
            )
            basic = next(
                event for event in result["events"]
                if event["source"] == "Basic attack"
            )
            mist = next(
                event for event in result["events"]
                if "Mist's Edge" in event["source"]
                and event["type"] == "physical"
            )
            return basic, mist

        melee_basic, melee_mist = mist_hit(5, 1000)
        ranged_basic, ranged_mist = mist_hit(6, 1000)
        _, low_hp_mist = mist_hit(6, 100)
        _, high_hp_mist = mist_hit(6, 5000)

        self.assertEqual(melee_mist["raw"], 90.0)
        self.assertEqual(ranged_mist["raw"], 60.0)
        self.assertEqual(low_hp_mist["raw"], 6.0)
        self.assertEqual(high_hp_mist["raw"], 300.0)
        self.assertEqual(
            melee_mist["raw"], melee_basic["hp_before"] * 0.09)
        self.assertEqual(
            ranged_mist["raw"], ranged_basic["hp_before"] * 0.06)
        self.assertLess(ranged_mist["hp_before"], ranged_basic["hp_before"])

    def test_blade_trigger_matrix_for_kayle_abilities_and_passives(self):
        enemy = {
            "hp": 1000, "current_hp": 800, "bonus_hp": 0,
            "armor": 0, "mr": 0,
        }
        pre_arisen_e = run(
            ["blade_of_the_ruined_king"],
            [{"type": "E"}],
            level=5,
            ranks={"Q": 0, "W": 0, "E": 1, "R": 0},
            enemy=enemy,
        )
        pre_arisen_mist = [
            event for event in pre_arisen_e["events"]
            if "Mist's Edge" in event["source"]
            and event["type"] == "physical"
        ]
        self.assertEqual(len(pre_arisen_mist), 1)
        self.assertEqual(pre_arisen_mist[0]["raw"], 48.0)

        aflame_e = run(
            ["blade_of_the_ruined_king"],
            [{"type": "E"}],
            level=11,
            ranks={"Q": 0, "W": 0, "E": 1, "R": 0},
            enemy=enemy,
        )
        self.assertEqual(sum(
            "Mist's Edge" in event["source"]
            and event["type"] == "physical"
            for event in aflame_e["events"]
        ), 1)
        self.assertTrue(any(
            event["source"] == "E passive on-hit (E)"
            for event in aflame_e["events"]
        ))
        self.assertTrue(any(
            event["source"].startswith("Passive fire wave")
            for event in aflame_e["events"]
        ))
        self.assertTrue(any(
            event["source"] == "E active (missing HP)"
            for event in aflame_e["events"]
        ))

        spells_only = run(
            ["blade_of_the_ruined_king"],
            [{"type": "Q"}, {"type": "W"}, {"type": "R"}],
            level=11,
            ranks={"Q": 1, "W": 1, "E": 1, "R": 1},
            enemy=enemy,
        )
        self.assertFalse(any(
            "Mist's Edge" in event["source"]
            and event["type"] == "physical"
            for event in spells_only["events"]
        ))

        killing_onhit = run(
            ["blade_of_the_ruined_king"],
            [{"type": "AA"}, {"type": "AA"}],
            level=18,
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0},
            enemy={
                "hp": 140, "current_hp": 140, "bonus_hp": 0,
                "armor": 0, "mr": 0,
            },
        )
        self.assertTrue(killing_onhit["enemy"]["killed"])
        self.assertEqual(sum(
            event["source"] == "Basic attack"
            for event in killing_onhit["events"]
        ), 1)
        killing_basic = next(
            event for event in killing_onhit["events"]
            if event["source"] == "Basic attack"
        )
        killing_mist = next(
            event for event in killing_onhit["events"]
            if "Mist's Edge" in event["source"]
            and event["type"] == "physical"
        )
        self.assertGreater(killing_basic["hp_after"], 0)
        self.assertLessEqual(killing_mist["hp_after"], 0)

    def test_blade_proc_does_not_crit_or_gain_hexoptics_basic_damage(self):
        enemy = {
            "hp": 5000, "current_hp": 5000, "bonus_hp": 0,
            "armor": 100, "mr": 0,
        }
        no_ranks = {"Q": 0, "W": 0, "E": 0, "R": 0}
        result = run(
            [
                "blade_of_the_ruined_king",
                "infinity_edge",
                "hexoptics_c44",
            ],
            [{"type": "AA"}],
            ranks=no_ranks,
            enemy=enemy,
        )
        mist = next(
            event for event in result["events"]
            if "Mist's Edge" in event["source"]
            and event["type"] == "physical"
        )
        self.assertEqual(mist["raw"], 300.0)
        self.assertEqual(mist["effective_resistance"], 100.0)
        self.assertEqual(mist["dealt"], 150.0)
        self.assertEqual(result["stats"]["life_steal"], 10.0)
        mist_heal = next(
            event for event in result["events"]
            if event["source"].endswith("Mist's Edge life steal")
        )
        self.assertEqual(mist_heal["dealt"], 15.0)

        penetrated = run(
            ["blade_of_the_ruined_king", "mortal_reminder"],
            [{"type": "AA"}],
            ranks=no_ranks,
            enemy=enemy,
        )
        penetrated_mist = next(
            event for event in penetrated["events"]
            if "Mist's Edge" in event["source"]
            and event["type"] == "physical"
        )
        self.assertEqual(penetrated_mist["raw"], 300.0)
        self.assertEqual(penetrated_mist["effective_resistance"], 70.0)

    def test_dusk_and_dawn_repeats_blade_after_point_two_seconds(self):
        result = run(
            ["blade_of_the_ruined_king", "dusk_and_dawn"],
            [{"type": "Q"}, {"type": "AA"}],
            ranks={"Q": 1, "W": 0, "E": 0, "R": 0},
            enemy={
                "hp": 10_000, "current_hp": 10_000, "bonus_hp": 0,
                "armor": 0, "mr": 0,
            },
        )
        basics = [
            event for event in result["events"]
            if event["source"] == "Basic attack"
        ]
        mist = [
            event for event in result["events"]
            if "Mist's Edge" in event["source"]
            and event["type"] == "physical"
        ]
        self.assertEqual(len(mist), 2)
        self.assertEqual(mist[0]["raw"], basics[0]["hp_before"] * 0.06)
        self.assertAlmostEqual(mist[1]["t"] - mist[0]["t"], 0.20, places=3)
        self.assertAlmostEqual(
            mist[1]["raw"], mist[1]["hp_before"] * 0.06, places=3)
        self.assertLess(mist[1]["raw"], mist[0]["raw"])

    def test_rageblade_phantom_hit_repeats_blade_from_live_hp(self):
        result = run(
            ["blade_of_the_ruined_king", "guinsoos_rageblade"],
            [{"type": "AA"}] * 3,
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0},
            enemy={
                "hp": 10_000, "current_hp": 10_000, "bonus_hp": 0,
                "armor": 0, "mr": 0,
            },
            options={"pre_stacked_rageblade": True},
        )
        mist = [
            event for event in result["events"]
            if "Mist's Edge" in event["source"]
            and event["type"] == "physical"
        ]
        self.assertEqual(len(mist), 4)
        phantom = next(
            event for event in mist
            if "Phantom Hit" in event["source"]
        )
        triggering = [
            event for event in mist
            if "Phantom Hit" not in event["source"]
        ][-1]
        self.assertAlmostEqual(phantom["t"] - triggering["t"], 0.15, places=3)
        self.assertAlmostEqual(
            phantom["raw"], phantom["hp_before"] * 0.06, places=3)

    def test_mortal_reminder_applies_expected_crit_and_armor_penetration(self):
        level = 1
        result = run(
            ["mortal_reminder"], [{"type": "AA"}], level=level,
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0},
            enemy={"hp": 5000, "armor": 100, "mr": 0},
        )
        attack = next(
            event for event in result["events"]
            if event["type"] == "physical"
        )
        expected_raw = (
            (kayle_stats_at(level)["base_ad"] + 35)
            * (1 + 0.25 * (KAYLE_AS["crit_damage"] - 1))
        )
        self.assertAlmostEqual(attack["raw"], expected_raw, places=3)
        self.assertEqual(attack["effective_resistance"], 70.0)
        self.assertEqual(result["stats"]["armor_pen_pct"], 30.0)
        self.assertEqual(result["stats"]["crit_chance"], 25.0)

    def test_hexoptics_uses_current_50_unit_scaling_and_500_unit_cap(self):
        magnification = ITEMS["hexoptics_c44"]["magnification"]
        self.assertAlmostEqual(magnification["amp_per_unit"], 0.01 / 50.0)
        self.assertEqual(magnification["max_amp"], 0.10)

        level = 10  # ranged Kayle: 525 range reaches the current 500-unit cap
        result = run(
            ["hexoptics_c44"], [{"type": "AA"}], level=level,
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0},
            enemy={"hp": 5000, "armor": 0, "mr": 0},
        )
        event = next(e for e in result["events"] if e["type"] == "physical")
        total_ad = kayle_stats_at(level)["base_ad"] + 55
        self.assertAlmostEqual(event["raw"], total_ad * 1.25 * 1.10, places=3)

    def test_rapid_firecannon_extends_hexoptics_range_only_while_energized(self):
        # Melee Kayle has 175 range: 3.5% Magnification normally and 4.725%
        # on RFC's 236.25-range Energized attack.
        level = 5
        result = run(
            ["hexoptics_c44", "rapid_firecannon"],
            [{"type": "AA"}, {"type": "AA"}], level=level,
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0},
            enemy={"hp": 5000, "armor": 0, "mr": 0},
        )
        basics = [e for e in result["events"] if e["type"] == "physical"]
        total_ad = kayle_stats_at(level)["base_ad"] + 55
        expected_crit = 1 + 0.50 * (KAYLE_AS["crit_damage"] - 1)
        self.assertAlmostEqual(
            basics[0]["raw"], total_ad * expected_crit * 1.04725, places=3)
        self.assertAlmostEqual(
            basics[1]["raw"], total_ad * expected_crit * 1.035, places=3)

    def test_hexoptics_amplifies_kraken_basic_damage(self):
        level = 10
        enemy = {
            "hp": 5000, "current_hp": 5000, "bonus_hp": 0,
            "armor": 0, "mr": 0,
        }
        result = run(
            ["hexoptics_c44", "kraken_slayer"],
            [{"type": "AA"}] * 3,
            level=level,
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0},
            enemy=enemy,
        )
        basics = [
            event for event in result["events"]
            if event["source"].startswith("Basic attack")
        ]
        proc = next(
            event for event in result["events"]
            if "Kraken Slayer" in event["source"]
        )
        missing_fraction = (
            enemy["hp"] - basics[2]["hp_before"]
        ) / enemy["hp"]
        ranged_level_10_base = 160.0 * 0.8
        expected = (
            ranged_level_10_base
            * (1.0 + 0.75 * missing_fraction)
            * 1.10
        )
        self.assertAlmostEqual(proc["raw"], expected, places=3)

    def test_rageblade_seething_expires_after_three_seconds(self):
        sim = Simulation(
            18,
            {"Q": 0, "W": 0, "E": 0, "R": 0},
            ["guinsoos_rageblade"],
            {"hp": 1_000_000, "current_hp": 1_000_000,
             "armor": 0, "mr": 0},
            [],
            {"pre_stacked_rageblade": False},
        )
        baseline = sim.attack_speed()
        sim.do_attack()
        self.assertGreater(sim.attack_speed(), baseline)
        sim.do_wait(3.1)
        self.assertAlmostEqual(sim.attack_speed(), baseline, places=6)

    def test_rageblade_phantom_progress_expires_after_six_seconds(self):
        result = run(
            ["guinsoos_rageblade"],
            ([{"type": "AA"}] * 5
             + [{"type": "WAIT", "duration": 6.1}, {"type": "AA"}]),
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0},
            enemy={"hp": 1_000_000, "current_hp": 1_000_000,
                   "armor": 0, "mr": 0},
            options={"pre_stacked_rageblade": False},
        )
        self.assertFalse(any(
            "Phantom Hit" in event["source"] for event in result["events"]
        ))

    def test_riftmaker_converts_bonus_health_and_stacks_damage_by_second(self):
        result = run(["riftmaker"], [{"type": "AA"}] * 5)
        self.assertEqual(result["stats"]["ap"], 77.0)  # 70 + 2% of 350 HP
        physical = [e for e in result["events"] if e["source"] == "Basic attack"]
        self.assertEqual([e["multiplier"] for e in physical], [1.0, 1.02, 1.04, 1.06, 1.08])
        self.assertGreater(result["healing"], 0)  # ranged 6% omnivamp at four stacks

        practice = run(
            ["riftmaker"], [{"type": "AA"}] * 6,
            enemy={"hp": 3500, "current_hp": 3500, "bonus_hp": 0,
                   "armor": 100, "mr": 100},
            options={
                "rune_ids": [9104], "legend_stacks": 0,
                "shards": ["adaptive", "attack_speed", "health_scaling"],
            },
        )
        self.assertEqual(practice["stats"]["ap"], 89.6)
        self.assertEqual(practice["stats"]["max_hp"], 2764.0)
        self.assertEqual(practice["stats"]["attack_speed_final"], 1.082)
        self.assertEqual(practice["total_damage"], 647.34)
        self.assertEqual(practice["enemy"]["remaining_hp"], 2852.66)
        practice_basics = [e for e in practice["events"]
                           if e["source"] == "Basic attack"]
        self.assertEqual(
            [e["multiplier"] for e in practice_basics],
            [1.0, 1.0, 1.02, 1.04, 1.06, 1.08],
        )
        final_magic = []
        for basic in practice_basics[-2:]:
            final_magic.append(sum(
                e["dealt"] for e in practice["events"]
                if e["t"] == basic["t"] and e["type"] == "magic"
            ))
        self.assertEqual([int(value) for value in final_magic], [61, 62])
        self.assertEqual([int(e["dealt"]) for e in practice_basics[-2:]],
                         [49, 49])

    def test_kraken_third_hit_uses_level_and_live_missing_health(self):
        result = run(["kraken_slayer"], [{"type": "AA"}] * 3)
        proc = next(e for e in result["events"] if "Bring It Down" in e["source"])
        basics = [e for e in result["events"] if e["source"] == "Basic attack"]
        missing = (5000 - basics[2]["hp_before"]) / 5000
        self.assertAlmostEqual(proc["raw"], 160 * (1 + 0.75 * missing), places=3)

        practice = run(
            ["kraken_slayer"], [{"type": "AA"}] * 3,
            enemy={"hp": 3500, "current_hp": 3500, "bonus_hp": 0,
                   "armor": 100, "mr": 100},
            options={
                "rune_ids": [9104], "legend_stacks": 0,
                "shards": ["adaptive", "attack_speed", "health"],
            },
        )
        self.assertEqual(practice["stats"]["total_ad"], 142.9)
        self.assertEqual(practice["stats"]["attack_speed_final"], 1.349)
        self.assertEqual(practice["total_damage"], 427.4)
        self.assertEqual(practice["enemy"]["remaining_hp"], 3072.6)
        practice_events = practice["events"]
        third_basic = [e for e in practice_events
                       if e["source"] == "Basic attack"][2]
        practice_proc = next(e for e in practice_events
                             if "Bring It Down" in e["source"])
        third_physical = third_basic["dealt"] + practice_proc["dealt"]
        third_magic = sum(
            e["dealt"] for e in practice_events
            if e["t"] == third_basic["t"] and e["type"] == "magic"
        )
        self.assertEqual(round(third_physical), 155)
        self.assertEqual(round(third_magic), 43)

        practice_e = run(
            ["kraken_slayer"],
            [{"type": "AA"}, {"type": "AA"}, {"type": "E"}],
            enemy={"hp": 3500, "current_hp": 3500, "bonus_hp": 0,
                   "armor": 100, "mr": 100},
            options={
                "rune_ids": [9104], "legend_stacks": 0,
                "shards": ["adaptive", "attack_speed", "health"],
            },
        )
        e_proc = next(e for e in practice_e["events"]
                      if "Bring It Down (E)" in e["source"])
        self.assertAlmostEqual(e_proc["raw"], 167.8507, places=4)
        self.assertEqual(practice_e["total_damage"], 438.84)
        self.assertEqual(practice_e["enemy"]["remaining_hp"], 3061.16)
        e_basic = next(e for e in practice_e["events"]
                       if e["source"] == "Basic attack (E)")
        self.assertEqual(round(e_basic["dealt"] + e_proc["dealt"]), 155)

    def test_terminus_alternates_light_dark_and_reaches_thirty_percent_pen(self):
        result = run(["terminus"], [{"type": "AA"}] * 7)
        waves = [e for e in result["events"] if e["source"].startswith("Passive fire wave")]
        self.assertEqual(
            [e["effective_resistance"] for e in waves],
            [100.0, 100.0, 90.0, 90.0, 80.0, 80.0, 70.0],
        )
        onhits = [e for e in result["events"] if e["source"] == "Terminus on-hit"]
        self.assertEqual(len(onhits), 7)
        self.assertTrue(all(e["raw"] == 30.0 for e in onhits))

        practice = run(
            ["terminus"], [{"type": "AA"}] * 7,
            enemy={"hp": 3500, "current_hp": 3500, "bonus_hp": 0,
                   "armor": 100, "mr": 100},
            options={
                "rune_ids": [9104], "legend_stacks": 0,
                "shards": ["adaptive", "attack_speed", "health"],
            },
        )
        self.assertEqual(practice["stats"]["total_ad"], 127.9)
        self.assertEqual(practice["stats"]["attack_speed_final"], 1.315)
        self.assertEqual(practice["total_damage"], 904.15)
        self.assertEqual(practice["enemy"]["remaining_hp"], 2595.85)
        basics = [e for e in practice["events"]
                  if e["source"] == "Basic attack"]
        self.assertEqual(
            [e["effective_resistance"] for e in basics],
            [100.0, 100.0, 90.0, 90.0, 80.0, 80.0, 70.0],
        )

    def test_bloodletter_reduces_mr_after_each_eligible_cast_instance(self):
        result = run(["bloodletters_curse"], [{"type": "AA"}] * 4)
        waves = [e for e in result["events"] if e["source"].startswith("Passive fire wave")]
        self.assertEqual(
            [e["effective_resistance"] for e in waves],
            [100.0, 85.0, 70.0, 70.0],
        )

        practice = run(
            ["bloodletters_curse"], [{"type": "AA"}] * 4,
            enemy={"hp": 3500, "current_hp": 3500, "bonus_hp": 0,
                   "armor": 100, "mr": 100},
            options={
                "rune_ids": [9104], "legend_stacks": 0,
                "shards": ["adaptive", "attack_speed", "health"],
            },
        )
        self.assertEqual(practice["stats"]["ap"], 74.0)
        self.assertEqual(practice["stats"]["attack_speed_final"], 1.082)
        self.assertEqual(practice["total_damage"], 427.32)
        self.assertEqual(practice["enemy"]["remaining_hp"], 3072.68)
        passive_resists = [
            e["effective_resistance"] for e in practice["events"]
            if e["source"] == "E passive on-hit"
        ]
        self.assertEqual(passive_resists, [100.0, 85.0, 70.0, 70.0])

    def test_ldr_uses_explicit_target_bonus_health(self):
        base_enemy = {"hp": 5000, "armor": 100, "mr": 100}
        zero = run(
            ["lord_dominiks_regards"], [{"type": "AA"}],
            enemy={**base_enemy, "bonus_hp": 0},
        )
        capped = run(
            ["lord_dominiks_regards"], [{"type": "AA"}],
            enemy={**base_enemy, "bonus_hp": 1500},
        )
        self.assertAlmostEqual(capped["total_damage"] / zero["total_damage"], 1.15, places=3)
        physical = next(e for e in capped["events"] if e["type"] == "physical")
        self.assertEqual(physical["effective_resistance"], 65.0)

    def test_wits_statikk_and_stormrazor_onhit_windows(self):
        wits = run(["wits_end"], [{"type": "AA"}])
        self.assertEqual(
            next(e for e in wits["events"] if e["source"] == "Wit's End on-hit")["raw"],
            45.0,
        )

        statikk = run(["statikk_shiv"], [{"type": "AA"}] * 4)
        sparks = [e for e in statikk["events"] if "Electrospark" in e["source"]]
        self.assertEqual(len(sparks), 1)
        self.assertTrue(all(e["raw"] == 60.0 for e in sparks))

        uncharged_statikk = run(
            ["statikk_shiv"], [{"type": "AA"}],
            options={"fleet_starts_energized": False},
        )
        self.assertFalse(any(
            "Electrospark" in e["source"] for e in uncharged_statikk["events"]
        ))

        storm = run(["stormrazor", "swiftmarch"], [{"type": "AA"}, {"type": "AA"}])
        bolts = [e for e in storm["events"] if "Stormrazor" in e["source"]]
        self.assertEqual(len(bolts), 1)
        self.assertEqual(bolts[0]["raw"], 100.0)
        basics = [e for e in storm["events"] if e["source"].startswith("Basic attack")]
        self.assertGreater(basics[1]["raw"], basics[0]["raw"])

    def test_statikk_matches_practice_tool_four_attack_isolation(self):
        practice_statikk = run(
            ["statikk_shiv"], [{"type": "AA"}] * 4,
            enemy={"hp": 3500, "current_hp": 3500, "bonus_hp": 0,
                   "armor": 100, "mr": 100},
            options={
                "fleet_starts_energized": True,
                "rune_ids": [9104], "legend_stacks": 0,
                "shards": ["adaptive", "attack_speed", "health_scaling"],
            },
        )
        self.assertEqual(practice_statikk["stats"]["total_ad"], 142.9)
        self.assertEqual(practice_statikk["stats"]["ap"], 45.0)
        self.assertEqual(practice_statikk["stats"]["attack_speed_final"], 1.282)
        self.assertAlmostEqual(practice_statikk["total_damage"], 528.46, places=3)
        self.assertAlmostEqual(
            practice_statikk["enemy"]["remaining_hp"], 2971.54, places=3)
        practice_sparks = [
            e for e in practice_statikk["events"] if "Electrospark" in e["source"]
        ]
        self.assertEqual([e["dealt"] for e in practice_sparks], [30.0])

    def test_stormrazor_fleet_swiftmarch_practice_snapshot(self):
        automatic = run(
            ["stormrazor", "swiftmarch"],
            [{"type": "AA"}, {"type": "E"}],
            enemy={"hp": 3500, "current_hp": 3500, "bonus_hp": 0,
                   "armor": 100, "mr": 100},
            options={
                "fleet_starts_energized": True,
                "rune_ids": [8021, 9104], "legend_stacks": 3,
                "shards": ["adaptive", "attack_speed", "health_scaling"],
            },
        )
        automatic_e = next(
            e for e in automatic["events"]
            if e["source"].startswith("Basic attack (E)")
        )
        self.assertEqual(automatic["stats"]["attack_speed_final"], 1.245)
        self.assertAlmostEqual(automatic_e["raw"], 213.5, places=3)
        # Remove the simulator's 1.25 expected-crit multiplier. Against 100
        # armor this is 85.4 damage, displayed as 85 in Practice Tool.
        self.assertAlmostEqual(automatic_e["dealt"] / 1.25, 85.4, places=3)
        fleet_note = next(
            e for e in automatic["events"]
            if e["source"].startswith("Fleet Footwork movement")
            and "570.00 total" in e["source"]
        )
        self.assertEqual(fleet_note["dealt"], 0)

    def test_rapid_firecannon_stacks_with_other_energized_effects(self):
        ready = run(
            ["rapid_firecannon", "stormrazor"],
            [{"type": "AA"}, {"type": "AA"}],
        )
        rfc = [e for e in ready["events"] if "Rapid Firecannon" in e["source"]]
        storm = [e for e in ready["events"] if "Stormrazor" in e["source"]]
        self.assertEqual([e["raw"] for e in rfc], [40.0])
        self.assertEqual([e["raw"] for e in storm], [100.0])

        uncharged = run(
            ["rapid_firecannon"], [{"type": "AA"}],
            options={"fleet_starts_energized": False},
        )
        self.assertFalse(any(
            "Rapid Firecannon" in e["source"] for e in uncharged["events"]
        ))

        practice = run(
            ["rapid_firecannon"], [{"type": "AA"}, {"type": "AA"}],
            enemy={"hp": 3500, "current_hp": 3500, "bonus_hp": 0,
                   "armor": 100, "mr": 100},
            options={
                "fleet_starts_energized": True,
                "rune_ids": [9104], "legend_stacks": 0,
                "shards": ["adaptive", "attack_speed", "health_scaling"],
            },
        )
        self.assertEqual(practice["stats"]["total_ad"], 97.9)
        self.assertEqual(practice["stats"]["ap"], 0.0)
        self.assertEqual(practice["stats"]["attack_speed_final"], 1.315)
        self.assertEqual(practice["stats"]["crit_chance"], 25.0)
        rfc_proc = next(e for e in practice["events"]
                        if "Rapid Firecannon" in e["source"])
        self.assertEqual(rfc_proc["raw"], 40.0)
        self.assertEqual(rfc_proc["dealt"], 20.0)

    def test_energized_recharges_from_six_stacks_per_attack(self):
        enemy = {
            "hp": 1_000_000, "current_hp": 1_000_000, "bonus_hp": 0,
            "armor": 0, "mr": 0,
        }
        ranks = {"Q": 0, "W": 0, "E": 0, "R": 0}
        sixteen = run(
            ["rapid_firecannon"], [{"type": "AA"}] * 16,
            ranks=ranks, enemy=enemy,
            options={"fleet_starts_energized": False},
        )
        seventeen = run(
            ["rapid_firecannon"], [{"type": "AA"}] * 17,
            ranks=ranks, enemy=enemy,
            options={"fleet_starts_energized": False},
        )
        self.assertFalse(any(
            "Rapid Firecannon" in event["source"]
            for event in sixteen["events"]
        ))
        self.assertEqual(sum(
            "Rapid Firecannon" in event["source"]
            for event in seventeen["events"]
        ), 1)

    def test_statikk_adds_nine_bonus_energize_stacks_per_attack(self):
        enemy = {
            "hp": 1_000_000, "current_hp": 1_000_000, "bonus_hp": 0,
            "armor": 0, "mr": 0,
        }
        ranks = {"Q": 0, "W": 0, "E": 0, "R": 0}
        six = run(
            ["statikk_shiv"], [{"type": "AA"}] * 6,
            ranks=ranks, enemy=enemy,
            options={"fleet_starts_energized": False},
        )
        seven = run(
            ["statikk_shiv"], [{"type": "AA"}] * 7,
            ranks=ranks, enemy=enemy,
            options={"fleet_starts_energized": False},
        )
        self.assertFalse(any(
            "Electrospark" in event["source"] for event in six["events"]
        ))
        self.assertEqual(sum(
            "Electrospark" in event["source"] for event in seven["events"]
        ), 1)

    def test_all_energized_items_proc_together_and_recharge_after_ready_start(self):
        result = run(
            ["rapid_firecannon", "statikk_shiv", "stormrazor"],
            [{"type": "AA"}] * 8,
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0},
            enemy={"hp": 1_000_000, "current_hp": 1_000_000,
                   "bonus_hp": 0, "armor": 0, "mr": 0},
            options={"fleet_starts_energized": True},
        )
        proc_times = {
            "rfc": [
                event["t"] for event in result["events"]
                if "Rapid Firecannon" in event["source"]
            ],
            "statikk": [
                event["t"] for event in result["events"]
                if "Electrospark" in event["source"]
            ],
            "stormrazor": [
                event["t"] for event in result["events"]
                if "Stormrazor" in event["source"]
            ],
        }
        self.assertEqual(len(proc_times["rfc"]), 2)
        self.assertEqual(proc_times["statikk"], proc_times["rfc"])
        self.assertEqual(proc_times["stormrazor"], proc_times["rfc"])

    def test_tagged_on_hit_and_spellblade_damage_benefit_from_life_steal(self):
        enemy = {
            "hp": 1_000_000, "current_hp": 1_000_000, "bonus_hp": 0,
            "armor": 0, "mr": 0,
        }
        no_ability_ranks = {"Q": 0, "W": 0, "E": 0, "R": 0}
        cases = (
            (
                "guinsoos_rageblade",
                [{"type": "AA"}],
                no_ability_ranks,
                lambda source: source == "Guinsoo's Rageblade on-hit",
            ),
            (
                "kraken_slayer",
                [{"type": "AA"}] * 3,
                no_ability_ranks,
                lambda source: "Bring It Down" in source,
            ),
            (
                "terminus",
                [{"type": "AA"}],
                no_ability_ranks,
                lambda source: source == "Terminus on-hit",
            ),
            (
                "wits_end",
                [{"type": "AA"}],
                no_ability_ranks,
                lambda source: source == "Wit's End on-hit",
            ),
            (
                "essence_reaver",
                [{"type": "Q"}, {"type": "AA"}],
                {"Q": 1, "W": 0, "E": 0, "R": 0},
                lambda source: source == "Essence Reaver Spellblade",
            ),
            (
                "lich_bane",
                [{"type": "Q"}, {"type": "AA"}],
                {"Q": 1, "W": 0, "E": 0, "R": 0},
                lambda source: source == "Lich Bane Spellblade",
            ),
            (
                "dusk_and_dawn",
                [{"type": "Q"}, {"type": "AA"}],
                {"Q": 1, "W": 0, "E": 0, "R": 0},
                lambda source: source == "Dusk and Dawn Spellblade",
            ),
        )
        for item, combo, ranks, is_item_life_steal in cases:
            with self.subTest(item=item):
                result = run(
                    ["gunmetal_greaves", item],
                    combo,
                    level=18,
                    ranks=ranks,
                    enemy=enemy,
                )
                eligible_events = [
                    event for event in result["events"]
                    if event["type"] in {"physical", "magic"}
                    and (
                        event["source"].startswith("Basic attack")
                        or is_item_life_steal(event["source"])
                    )
                ]
                for damage_event in eligible_events:
                    life_steal = [
                        event for event in result["events"]
                        if event["type"] == "heal"
                        and event["t"] == damage_event["t"]
                        and event["source"] == (
                            f"{damage_event['source']} life steal")
                    ]
                    self.assertEqual(len(life_steal), 1)
                    self.assertAlmostEqual(
                        life_steal[0]["dealt"],
                        round(damage_event["dealt"] * 0.05, 1),
                        places=1,
                    )

    def test_experimental_hexplate_overdrive_starts_on_r_and_feeds_swiftmarch(self):
        sim = Simulation(
            18, default_ability_ranks(18),
            ["experimental_hexplate", "swiftmarch"],
            {"hp": 5000, "armor": 100, "mr": 100}, [],
            {
                "pre_stacked_zeal": True,
                "rune_ids": [9104],
                # The captured Practice Tool page had one 1.5% Alacrity
                # stack: this accounts for the 1.225 absolute AS reading.
                "legend_stacks": 1,
                "shards": ["adaptive", "attack_speed", "health"],
            },
        )
        before_as = sim.attack_speed()
        before_ms = sim.current_movement_speed
        before_ad = sim.total_ad
        self.assertAlmostEqual(before_ad, 155.626, places=3)
        self.assertEqual(round(before_as, 3), 1.225)
        self.assertAlmostEqual(before_ms, 435.0, places=8)
        sim.do_r()
        self.assertEqual(sim.ultimate_haste, 30)
        self.assertAlmostEqual(
            sim.attack_speed() - before_as, KAYLE_AS["as_ratio"] * 0.35,
            places=5,
        )
        self.assertEqual(round(sim.attack_speed(), 3), 1.459)
        self.assertAlmostEqual(sim.current_movement_speed, 478.0, places=8)
        self.assertAlmostEqual(sim.total_ad, 157.0192, places=4)
        self.assertEqual(sim.hexplate_overdrive_until, 8.0)

    def test_essence_reaver_spellblade_is_physical_and_scales_with_total_crit(self):
        level = 10
        cases = (
            (["essence_reaver"], 25.0),
            (["essence_reaver", "infinity_edge"], 50.0),
        )
        for items, crit_chance in cases:
            with self.subTest(crit_chance=crit_chance):
                result = run(
                    items, [{"type": "Q"}, {"type": "AA"}],
                    level=level, ranks={"Q": 1, "W": 0, "E": 0, "R": 0},
                    enemy={"hp": 5000, "armor": 0, "mr": 0},
                )
                proc = next(
                    e for e in result["events"]
                    if e["source"] == "Essence Reaver Spellblade"
                )
                expected = (
                    1.25 * kayle_stats_at(level)["base_ad"]
                    + 0.5 * crit_chance
                )
                self.assertEqual(proc["type"], "physical")
                self.assertAlmostEqual(proc["raw"], expected, places=3)

    def test_spellblade_expires_after_ten_seconds_and_recast_refreshes_window(self):
        enemy = {
            "hp": 1_000_000, "current_hp": 1_000_000, "bonus_hp": 0,
            "armor": 0, "mr": 0,
        }
        ranks = {"Q": 1, "W": 1, "E": 0, "R": 0}
        expired = run(
            ["essence_reaver"],
            [
                {"type": "W"},
                {"type": "WAIT", "duration": 10.1},
                {"type": "AA"},
            ],
            ranks=ranks,
            enemy=enemy,
        )
        self.assertFalse(any(
            event["source"] == "Essence Reaver Spellblade"
            for event in expired["events"]
        ))

        refreshed = run(
            ["essence_reaver"],
            [
                {"type": "W"},
                {"type": "WAIT", "duration": 6.0},
                {"type": "Q"},
                {"type": "WAIT", "duration": 5.0},
                {"type": "AA"},
            ],
            ranks=ranks,
            enemy=enemy,
        )
        procs = [
            event for event in refreshed["events"]
            if event["source"] == "Essence Reaver Spellblade"
        ]
        self.assertEqual(len(procs), 1)
        self.assertGreater(procs[0]["t"], 10.0)

    def test_yun_tal_can_start_trained_or_build_expected_crit_in_combo(self):
        trained = run(
            ["yun_tal_wildarrows"], [{"type": "AA"}],
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0},
        )
        self.assertEqual(trained["stats"]["crit_chance"], 25.0)

        untrained = run(
            ["yun_tal_wildarrows"], [{"type": "AA"}, {"type": "AA"}],
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0},
            enemy={"hp": 5000, "armor": 0, "mr": 0},
            options={"pre_stacked_yun_tal": False},
        )
        basics = [
            e for e in untrained["events"]
            if e["source"].startswith("Basic attack")
        ]
        self.assertGreater(basics[1]["raw"], basics[0]["raw"])
        self.assertEqual(untrained["stats"]["crit_chance"], 0.4)

    def test_yun_tal_zero_crit_stat_counts_for_jack_of_all_trades(self):
        self.assertIn("crit_chance", ITEMS["yun_tal_wildarrows"]["stats"])
        self.assertEqual(ITEMS["yun_tal_wildarrows"]["stats"]["crit_chance"], 0)

        level = 18
        sim = Simulation(
            level,
            {"Q": 0, "W": 0, "E": 0, "R": 0},
            ["yun_tal_wildarrows", "boots_of_swiftness"],
            {"hp": 5000, "current_hp": 5000, "bonus_hp": 0,
             "armor": 0, "mr": 0},
            [],
            {
                "rune_ids": [8316],
                "pre_stacked_yun_tal": False,
            },
        )
        self.assertEqual(sim.haste, 5.0)
        self.assertAlmostEqual(
            sim.total_ad,
            kayle_stats_at(level)["base_ad"] + 50.0 + 3.6,
            places=4,
        )

    def test_navori_reduces_remaining_basic_ability_cooldowns(self):
        sim = Simulation(
            10, {"Q": 1, "W": 0, "E": 0, "R": 0},
            ["navori_flickerblade"],
            {"hp": 5000, "armor": 0, "mr": 0}, [],
            {"pre_stacked_zeal": True},
        )
        sim.do_q()
        ready_before = sim.cooldowns["Q"]
        attack_time = sim.time
        sim.do_attack()
        expected = attack_time + (ready_before - attack_time) * 0.85
        self.assertAlmostEqual(sim.cooldowns["Q"], expected, places=6)

    def test_cosmic_drive_movement_buff_feeds_swiftmarch(self):
        sim = Simulation(
            18, default_ability_ranks(18), ["cosmic_drive", "swiftmarch"],
            {"hp": 5000, "armor": 100, "mr": 100},
            [{"type": "AA"}], {"pre_stacked_zeal": True},
        )
        before = sim.current_movement_speed
        sim.run()
        self.assertGreater(sim.cosmic_ms_until, 0)
        self.assertGreater(sim.current_movement_speed, before)

    def test_stormsurge_threshold_delayed_squall_and_swiftmarch_window(self):
        enemy = {"hp": 1000, "current_hp": 1000, "bonus_hp": 0,
                 "armor": 0, "mr": 0}
        result = run(
            ["stormsurge"], [{"type": "AA"}] * 3,
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0}, enemy=enemy,
        )
        squall = next(
            e for e in result["events"] if e["source"] == "Stormsurge - Squall"
        )
        applied = next(
            e for e in result["events"]
            if e["source"].startswith("Stormsurge - Stormraider")
        )
        self.assertAlmostEqual(squall["t"] - applied["t"], 2.0, places=3)
        self.assertEqual(squall["raw"], 134.0)  # 125 + 10% of 90 AP

        sim = Simulation(
            18, {"Q": 0, "W": 0, "E": 0, "R": 0},
            ["stormsurge", "swiftmarch"], enemy, [],
            {"pre_stacked_zeal": True},
        )
        base_ms, base_ap = sim.current_movement_speed, sim.ap
        sim.do_attack()
        sim.do_attack()
        self.assertGreater(sim.current_movement_speed, base_ms)
        self.assertGreater(sim.ap, base_ap)
        self.assertLess(sim.time, sim.stormsurge_ms_until)

    def test_stormsurge_squall_resolves_after_a_short_combo_ends(self):
        result = run(
            ["stormsurge"], [{"type": "Q"}],
            ranks={"Q": 5, "W": 0, "E": 0, "R": 0},
            enemy={"hp": 800, "current_hp": 800, "bonus_hp": 0,
                   "armor": 0, "mr": 0},
        )
        q = next(e for e in result["events"] if e["source"].startswith("Q "))
        squall = next(
            e for e in result["events"] if e["source"] == "Stormsurge - Squall"
        )
        self.assertEqual(q["t"], 0.0)
        self.assertEqual(squall["t"], 2.0)
        self.assertEqual(squall["dealt"], 134.0)
        self.assertEqual(result["total_damage"], 359.0)
        # Squall lands two seconds after Q, so it is included in total damage
        # but cannot share Q's winning rolling one-second burst window.
        self.assertEqual(result["burst_damage_1s"], 225.0)
        self.assertEqual(result["burst_window_1s"], {"start": 0.0, "end": 1.0})
        self.assertEqual(result["duration"], 2.0)

    def test_stormsurge_window_and_dead_target_aoe_rules(self):
        no_proc = run(
            ["stormsurge"],
            [{"type": "AA"}, {"type": "WAIT", "duration": 2.6},
             {"type": "AA"}],
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0},
            enemy={"hp": 1000, "current_hp": 1000, "bonus_hp": 0,
                   "armor": 0, "mr": 0},
        )
        self.assertFalse(any(
            e["source"] == "Stormsurge - Squall" for e in no_proc["events"]
        ))

        killed_before_squall = run(
            ["stormsurge"], [{"type": "AA"}] * 3,
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0},
            enemy={"hp": 260, "current_hp": 260, "bonus_hp": 0,
                   "armor": 0, "mr": 0},
        )
        self.assertFalse(any(
            e["source"] == "Stormsurge - Squall"
            for e in killed_before_squall["events"]
        ))
        self.assertFalse(any(
            "nearby AoE omitted" in e["source"]
            for e in killed_before_squall["events"]
        ))
        self.assertTrue(all(
            e["t"] <= killed_before_squall["kill_time"]
            for e in killed_before_squall["events"]
        ))

    def test_fiendhunter_primes_three_attacks_and_adds_ultimate_haste(self):
        result = run(
            ["fiendhunter_bolts"],
            [{"type": "R"}] + [{"type": "AA"}] * 4,
        )
        basics = [e for e in result["events"] if e["source"].startswith("Basic attack")]
        self.assertEqual(sum("Fiendhunter" in e["source"] for e in basics), 3)
        self.assertNotIn("Fiendhunter", basics[3]["source"])
        true_hits = [e for e in result["events"] if "natural-crit bonus" in e["source"]]
        self.assertEqual(len(true_hits), 3)
        expected_true = (
            result["stats"]["total_ad"]
            * result["stats"]["crit_damage"] / 100.0
            * result["stats"]["crit_chance"] / 100.0
            * ITEMS["fiendhunter_bolts"]["opening_barrage"][
                "natural_crit_true_ratio"]
        )
        for hit in true_hits:
            self.assertEqual(hit["type"], "true")
            self.assertIsNone(hit["effective_resistance"])
            self.assertAlmostEqual(hit["raw"], expected_true, places=4)
            self.assertAlmostEqual(hit["dealt"], expected_true, places=4)
        self.assertEqual(result["stats"]["ultimate_haste"], 30.0)


if __name__ == "__main__":
    unittest.main()
