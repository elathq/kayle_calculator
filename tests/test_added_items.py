import unittest

from backend.data.items_data import ITEMS, item_list_for_api, validate_item_catalog
from backend.data.kayle_data import KAYLE_AS, default_ability_ranks, kayle_stats_at
from backend.engine import Simulation, simulate_build


NEW_ITEMS = {
    "cosmic_drive": 4629,
    "riftmaker": 4633,
    "kraken_slayer": 6672,
    "terminus": 3302,
    "infinity_edge": 3031,
    "bloodletters_curse": 8010,
    "hexoptics_c44": 2523,
    "phantom_dancer": 3046,
    "rapid_firecannon": 3094,
    "experimental_hexplate": 3073,
    "essence_reaver": 3508,
    "yun_tal_wildarrows": 3032,
    "navori_flickerblade": 6675,
    "lord_dominiks_regards": 3036,
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

    def test_all_added_items_are_in_the_picker_with_current_ids(self):
        api = {item["key"]: item for item in item_list_for_api()}
        for key, item_id in NEW_ITEMS.items():
            self.assertIn(key, ITEMS)
            self.assertIn(key, api)
            self.assertEqual(api[key]["id"], item_id)
            self.assertEqual(api[key]["icon"], f"icons/{item_id}.png")

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
            "ad": 50, "attack_speed": 40,
        })
        self.assertEqual(ITEMS["navori_flickerblade"]["stats"], {
            "attack_speed": 40, "crit_chance": 25, "move_speed_pct": 4,
        })
        self.assertEqual(ITEMS["stormsurge"]["stats"], {
            "ap": 90, "magic_pen_flat": 15, "move_speed_pct": 6,
        })

        sim = Simulation(
            18, default_ability_ranks(18),
            ["terminus", "lord_dominiks_regards", "bloodletters_curse"],
            {"hp": 5000, "armor": 100, "mr": 100}, [], {},
        )
        self.assertEqual(sim.items, ["terminus"])
        self.assertEqual(len(sim.warnings), 2)

        spellblades = Simulation(
            18, default_ability_ranks(18),
            ["lich_bane", "essence_reaver"],
            {"hp": 5000, "armor": 100, "mr": 100}, [], {},
        )
        self.assertEqual(spellblades.items, ["lich_bane"])
        self.assertEqual(len(spellblades.warnings), 1)

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

    def test_hexoptics_uses_kayles_max_attack_range_without_distance_input(self):
        level = 10  # ranged Kayle: 525 range -> 8.75% Magnification
        result = run(
            ["hexoptics_c44"], [{"type": "AA"}], level=level,
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0},
            enemy={"hp": 5000, "armor": 0, "mr": 0},
        )
        event = next(e for e in result["events"] if e["type"] == "physical")
        total_ad = kayle_stats_at(level)["base_ad"] + 55
        self.assertAlmostEqual(event["raw"], total_ad * 1.25 * 1.0875, places=3)

    def test_rapid_firecannon_extends_hexoptics_range_only_while_energized(self):
        level = 10  # 525 + capped 150 RFC range reaches Hexoptics' 10% cap
        result = run(
            ["hexoptics_c44", "rapid_firecannon"],
            [{"type": "AA"}, {"type": "AA"}], level=level,
            ranks={"Q": 0, "W": 0, "E": 0, "R": 0},
            enemy={"hp": 5000, "armor": 0, "mr": 0},
        )
        basics = [e for e in result["events"] if e["type"] == "physical"]
        total_ad = kayle_stats_at(level)["base_ad"] + 55
        expected_crit = 1 + 0.50 * (KAYLE_AS["crit_damage"] - 1)
        self.assertAlmostEqual(basics[0]["raw"], total_ad * expected_crit * 1.10, places=3)
        self.assertAlmostEqual(basics[1]["raw"], total_ad * expected_crit * 1.0875, places=3)

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
        result = run(
            ["essence_reaver"], [{"type": "Q"}, {"type": "AA"}],
            level=level, ranks={"Q": 1, "W": 0, "E": 0, "R": 0},
            enemy={"hp": 5000, "armor": 0, "mr": 0},
        )
        proc = next(
            e for e in result["events"]
            if e["source"] == "Essence Reaver Spellblade"
        )
        expected_ratio = 1.25 + 0.005 * 25
        self.assertEqual(proc["type"], "physical")
        self.assertAlmostEqual(
            proc["raw"], kayle_stats_at(level)["base_ad"] * expected_ratio,
            places=3,
        )

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
        self.assertTrue(any(
            "nearby AoE omitted" in e["source"]
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
        self.assertEqual(result["stats"]["ultimate_haste"], 30.0)


if __name__ == "__main__":
    unittest.main()
