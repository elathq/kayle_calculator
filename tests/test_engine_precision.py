import unittest

from backend.data.kayle_data import default_ability_ranks as live_default_ability_ranks
from backend.engine import Simulation, simulate_build


LEVEL = 12
PRACTICE_RANKS = {"Q": 5, "W": 0, "E": 5, "R": 2}
ITEMS = ["nashors_tooth", "dusk_and_dawn", "rabadons_deathcap"]
ENEMY = {"hp": 3500, "armor": 100, "mr": 100}
BASE_OPTIONS = {"rune_ids": [8005], "pre_stacked_zeal": False}


def default_ability_ranks(level):
    """Keep the calibrated level-12 Practice Tool setup explicit.

    The simulator's live auto-assignment now follows E -> Q -> W, but these
    historical backtests were recorded with Q5/E5/W0 at level 12.
    """
    if level == LEVEL:
        return PRACTICE_RANKS.copy()
    return live_default_ability_ranks(level)


def simulate(combo, **option_overrides):
    return simulate_build(
        level=LEVEL,
        ranks=default_ability_ranks(LEVEL),
        item_keys=ITEMS,
        enemy=ENEMY,
        combo=combo,
        options={**BASE_OPTIONS, **option_overrides},
    )


class EnginePrecisionTests(unittest.TestCase):
    def test_single_attack_preserves_fractional_damage(self):
        result = simulate([{"type": "AA"}])
        self.assertEqual(result["calculation_model"], "full_precision_v1")
        self.assertEqual(result["total_damage"], 123.73)
        self.assertEqual(result["burst_damage_1s"], 123.73)
        self.assertEqual(result["burst_window_1s"], {"start": 0.0, "end": 1.0})
        self.assertEqual(result["enemy"]["remaining_hp"], 3376.27)

    def test_one_second_burst_uses_the_highest_rolling_window(self):
        sim = Simulation(
            1, {"Q": 0, "W": 0, "E": 0, "R": 0}, [],
            {"hp": 10000, "current_hp": 10000, "armor": 0, "mr": 0},
            [], {},
        )
        sim._deal(100, "true", "early", 0.0)
        sim._deal(150, "true", "middle", 0.75)
        sim._deal(200, "true", "peak", 1.5)
        sim._deal(50, "true", "late", 3.0)
        result = sim.run()

        self.assertEqual(result["total_damage"], 500.0)
        self.assertEqual(result["burst_damage_1s"], 350.0)
        self.assertEqual(
            result["burst_window_1s"], {"start": 0.75, "end": 1.75})

    def test_damage_event_contains_auditable_stages(self):
        event = simulate([{"type": "AA"}])["events"][0]
        self.assertEqual(event["source"], "Basic attack")
        self.assertIn("raw", event)
        self.assertIn("multiplier", event)
        self.assertIn("effective_resistance", event)
        self.assertIn("mitigation_multiplier", event)
        self.assertIn("hp_before", event)
        self.assertIn("hp_after", event)
        self.assertAlmostEqual(event["hp_before"] - event["hp_after"], event["dealt"], 3)

    def test_clean_e_uses_exact_hp_damage(self):
        result = simulate([{"type": "E"}])
        self.assertEqual(result["total_damage"], 255.69)
        sources = {event["source"] for event in result["events"]}
        self.assertIn("Basic attack (E)", sources)
        self.assertIn("Dusk and Dawn Spellblade", sources)
        self.assertAlmostEqual(
            result["enemy"]["max_hp"] - result["enemy"]["remaining_hp"],
            result["total_damage"],
            delta=0.01,
        )

    def test_practice_tool_setup_matches_stats_and_four_observations(self):
        options = {
            "rune_ids": [8005, 8009, 9104, 8299, 8226, 8234],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
        }
        from backend.engine import Simulation

        sim = Simulation(
            LEVEL, default_ability_ranks(LEVEL), ITEMS, ENEMY,
            [{"type": "AA"}], options,
        )
        self.assertAlmostEqual(sim.total_ad, 74.6125)
        self.assertAlmostEqual(sim.ap, 362.7)
        self.assertAlmostEqual(sim.attack_speed(), 1.277109, places=5)
        self.assertAlmostEqual(sim.kayle_max_hp, 1995.74, places=2)

        cases = [
            ([{"type": "AA"}], 125.78),
            ([{"type": "E"}], 260.37),
            ([{"type": "AA"}, {"type": "E"}], 454.68),
            ([{"type": "AA"}, {"type": "E"}, {"type": "AA"}], 590.52),
        ]
        for combo, expected in cases:
            result = simulate_build(
                LEVEL, default_ability_ranks(LEVEL), ITEMS, ENEMY, combo, options)
            self.assertEqual(result["total_damage"], expected)

    def test_e_without_dusk_and_dawn_matches_isolation_sources(self):
        options = {
            "rune_ids": [8005, 8009, 9104, 8299, 8226, 8234],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
        }
        items = ["nashors_tooth", "rabadons_deathcap"]

        clean_e = simulate_build(
            LEVEL, default_ability_ranks(LEVEL), items, ENEMY,
            [{"type": "E"}], options)
        self.assertEqual(clean_e["total_damage"], 112.13)

        aa_e = simulate_build(
            LEVEL, default_ability_ranks(LEVEL), items, ENEMY,
            [{"type": "AA"}, {"type": "E"}], options)
        self.assertEqual(aa_e["total_damage"], 232.26)
        e_events = [event for event in aa_e["events"]
                    if event["source"].endswith("(E)")
                    or event["source"].startswith("E active")]
        e_magic = sum(event["dealt"] for event in e_events if event["type"] == "magic")
        self.assertAlmostEqual(e_magic, 82.82, places=2)
        self.assertFalse(any(event["source"] == "Press the Attack"
                             for event in aa_e["events"]))

        three_aa = simulate_build(
            LEVEL, default_ability_ranks(LEVEL), items, ENEMY,
            [{"type": "AA"}, {"type": "AA"}, {"type": "AA"}], options)
        self.assertEqual(three_aa["total_damage"], 395.21)
        pta = next(event for event in three_aa["events"]
                   if event["source"] == "Press the Attack")
        self.assertAlmostEqual(pta["raw"], 117.65, places=2)

        four_aa = simulate_build(
            LEVEL, default_ability_ranks(LEVEL), items, ENEMY,
            [{"type": "AA"}, {"type": "AA"}, {"type": "AA"}, {"type": "AA"}],
            options)
        self.assertEqual(four_aa["total_damage"], 516.31)

    def test_e_missing_health_uses_hp_before_the_empowered_attack(self):
        options = {
            "rune_ids": [8021, 8009, 9104, 8299, 8226, 8234],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
        }
        result = simulate_build(
            LEVEL, default_ability_ranks(LEVEL),
            ["nashors_tooth", "rabadons_deathcap"],
            {"hp": 1000, "armor": 100, "mr": 100},
            [{"type": "AA"}] * 3 + [{"type": "E"}], options)

        self.assertEqual(result["total_damage"], 472.52)
        self.assertEqual(result["enemy"]["remaining_hp"], 527.48)

        e_physical = next(event for event in result["events"]
                          if event["source"] == "Basic attack (E)")
        e_missing = next(event for event in result["events"]
                         if event["source"] == "E active (missing HP)")
        self.assertAlmostEqual(e_physical["hp_before"], 663.6138, places=4)
        self.assertAlmostEqual(e_missing["raw"], 48.004, places=3)
        self.assertAlmostEqual(e_missing["dealt"], 24.002, places=3)

    def test_rune_scaling_uses_top_quest_level_20_endpoint(self):
        from backend.engine import Simulation

        level_12 = Simulation(
            12, default_ability_ranks(12), [], ENEMY, [], BASE_OPTIONS)
        level_20 = Simulation(
            20, default_ability_ranks(20), [], ENEMY, [], BASE_OPTIONS)
        self.assertAlmostEqual(level_12._lerp(40, 160), 117.6471, places=4)
        self.assertAlmostEqual(level_20._lerp(40, 160), 174.1176, places=4)

    def test_fire_wave_uses_its_level_12_breakpoint_through_level_20(self):
        options = {
            "rune_ids": [8005, 8009, 9104, 8299, 8226, 8234],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
        }
        items = ["nashors_tooth", "rabadons_deathcap"]

        expected = {
            18: {"raw_wave": 112.175, "wave": 56.0875,
                 "one_aa": 177.16, "three_aa": 611.48},
            20: {"raw_wave": 118.175, "wave": 59.0875,
                 "one_aa": 183.49, "three_aa": 637.53},
        }
        for level, values in expected.items():
            one = simulate_build(
                level, default_ability_ranks(level), items, ENEMY,
                [{"type": "AA"}], options)
            wave = next(event for event in one["events"]
                        if event["source"] == "Passive fire wave")
            self.assertAlmostEqual(wave["raw"], values["raw_wave"], places=3)
            self.assertAlmostEqual(wave["dealt"], values["wave"], places=3)
            self.assertEqual(one["total_damage"], values["one_aa"])

            three = simulate_build(
                level, default_ability_ranks(level), items, ENEMY,
                [{"type": "AA"}, {"type": "AA"}, {"type": "AA"}], options)
            self.assertEqual(three["total_damage"], values["three_aa"])

    def test_q_damage_and_post_hit_shred_match_practice_tool(self):
        options = {
            "rune_ids": [8005, 8009, 9104, 8299, 8226, 8234],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
        }
        items = ["nashors_tooth", "rabadons_deathcap"]

        for resistance, expected in {
                0: 322.35, 50: 214.90, 100: 161.18, 200: 107.45}.items():
            q = simulate_build(
                LEVEL, default_ability_ranks(LEVEL), items,
                {"hp": 3500, "armor": resistance, "mr": resistance},
                [{"type": "Q"}], options)
            self.assertEqual(q["total_damage"], expected)

        q_aa = simulate_build(
            LEVEL, default_ability_ranks(LEVEL), items, ENEMY,
            [{"type": "Q"}, {"type": "AA"}], options)
        self.assertEqual(q_aa["total_damage"], 282.40)
        q_event = next(event for event in q_aa["events"]
                       if event["source"].startswith("Q"))
        aa_events = [event for event in q_aa["events"]
                     if event["source"] == "Basic attack"
                     or "on-hit" in event["source"]]
        self.assertEqual(q_event["effective_resistance"], 100.0)
        self.assertTrue(all(event["effective_resistance"] == 85.0
                            for event in aa_events))

    def test_q_shred_percent_pen_and_flat_pen_order_matches_practice_tool(self):
        options = {
            "rune_ids": [8005, 8009, 9104, 8299, 8226, 8234],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
        }
        cases = [
            (["nashors_tooth", "rabadons_deathcap", "void_staff"],
             408.12, 60.0, 51.0),
            (["nashors_tooth", "rabadons_deathcap", "shadowflame"],
             370.69, 85.0, 70.0),
            (["nashors_tooth", "rabadons_deathcap", "void_staff", "shadowflame"],
             533.16, 45.0, 36.0),
        ]
        for items, expected_total, q_mr, aa_mr in cases:
            result = simulate_build(
                LEVEL, default_ability_ranks(LEVEL), items, ENEMY,
                [{"type": "Q"}, {"type": "AA"}], options)
            self.assertEqual(result["total_damage"], expected_total)
            q_event = next(event for event in result["events"]
                           if event["source"].startswith("Q"))
            magic_aa = [event for event in result["events"]
                        if event["type"] == "magic"
                        and (event["source"] == "Basic attack"
                             or "on-hit" in event["source"])]
            self.assertEqual(q_event["effective_resistance"], q_mr)
            self.assertTrue(all(event["effective_resistance"] == aa_mr
                                for event in magic_aa))

    def test_q_before_e_is_assumed_to_have_hit(self):
        options = {
            "rune_ids": [8021, 8009, 9104, 8299, 8226, 8234],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
        }
        items = ["nashors_tooth", "rabadons_deathcap"]
        result = simulate_build(
            LEVEL, default_ability_ranks(LEVEL), items, ENEMY,
            [{"type": "Q"}, {"type": "E"}], options)
        self.assertEqual(result["total_damage"], 294.83)
        self.assertEqual(result["events"][0]["source"], "Q — Radiant Blast")

    def test_starting_enemy_hp_and_shadowflame_crit_threshold(self):
        options = {
            "rune_ids": [8005, 8009, 9104, 8299, 8226, 8234],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
        }
        items = ["nashors_tooth", "rabadons_deathcap", "shadowflame"]

        cases = [
            (1435, 212.89, 1.0),   # 41%: inactive
            (1400, 212.89, 1.0),   # exactly 40%: still inactive
            (1365, 255.47, 1.2),   # 39%: active
        ]
        for current_hp, expected, multiplier in cases:
            result = simulate_build(
                LEVEL, default_ability_ranks(LEVEL), items,
                {"hp": 3500, "current_hp": current_hp,
                 "armor": 100, "mr": 100},
                [{"type": "Q"}], options)
            self.assertEqual(result["total_damage"], expected)
            event = next(event for event in result["events"]
                         if event["source"].startswith("Q"))
            self.assertEqual(event["multiplier"], multiplier)

        clamped = simulate_build(
            LEVEL, default_ability_ranks(LEVEL), items,
            {"hp": 3500, "current_hp": 9999, "armor": 100, "mr": 100},
            [], options)
        self.assertEqual(clamped["enemy"]["remaining_hp"], 3500.0)

    def test_shadowflame_crit_snapshots_hp_for_the_whole_damage_frame(self):
        options = {
            "rune_ids": [8021, 8009, 9104, 8299, 8226, 8234],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
        }
        items = ["nashors_tooth", "rabadons_deathcap", "shadowflame"]
        enemy = {"hp": 1200, "armor": 100, "mr": 100}

        above = simulate_build(
            LEVEL, default_ability_ranks(LEVEL), items, enemy,
            [{"type": "AA"}] * 4 + [{"type": "Q"}], options)
        self.assertEqual(above["total_damage"], 793.89)

        crossing = simulate_build(
            LEVEL, default_ability_ranks(LEVEL), items, enemy,
            [{"type": "AA"}] * 5 + [{"type": "Q"}], options)
        self.assertEqual(crossing["total_damage"], 1051.95)
        wave = next(event for event in crossing["events"]
                    if event["source"].startswith("Passive fire wave"))
        q_event = next(event for event in crossing["events"]
                       if event["source"].startswith("Q"))
        self.assertEqual(wave["multiplier"], 1.0)
        self.assertNotIn("Shadowflame crit", wave["source"])
        self.assertEqual(q_event["hp_before"], 403.5228)
        self.assertEqual(q_event["multiplier"], 1.2)
        self.assertIn("Shadowflame crit", q_event["source"])

    def test_rageblade_first_phantom_hit_is_attack_seven_from_zero_stacks(self):
        options = {
            "rune_ids": [8021, 8009, 9104, 8299, 8226, 8234],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
            "pre_stacked_rageblade": False,
        }
        items = ["nashors_tooth", "guinsoos_rageblade", "rabadons_deathcap"]

        six = simulate_build(
            LEVEL, default_ability_ranks(LEVEL), items, ENEMY,
            [{"type": "AA"}] * 6, options)
        self.assertEqual(six["total_damage"], 1009.65)
        self.assertFalse(any("Phantom Hit" in event["source"]
                             for event in six["events"]))

        seven = simulate_build(
            LEVEL, default_ability_ranks(LEVEL), items, ENEMY,
            [{"type": "AA"}] * 7, options)
        phantom = [event for event in seven["events"]
                   if "Phantom Hit" in event["source"]]
        self.assertEqual(len(phantom), 3)

    def test_rageblade_e_snapshot_changes_with_attack_reset_timing(self):
        options = {
            "rune_ids": [8021, 8009, 9104, 8299, 8226, 8234],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
            "pre_stacked_rageblade": False,
        }
        items = ["nashors_tooth", "guinsoos_rageblade", "rabadons_deathcap"]

        # E is attack five, so no Phantom Hit occurs. The 854 Practice Tool
        # total proves Rageblade E reads missing HP after its physical hit.
        fifth_e = simulate_build(
            LEVEL, default_ability_ranks(LEVEL), items, ENEMY,
            [{"type": "AA"}] * 4 + [{"type": "E"}], options)
        self.assertEqual(fifth_e["total_damage"], 854.32)
        self.assertEqual(fifth_e["enemy"]["remaining_hp"], 2645.68)

        # Attack seven triggers Phantom Hit. Waiting preserves the post-physical
        # read, while the fast reset reads after E's normal on-hit package.
        waited = simulate_build(
            LEVEL, default_ability_ranks(LEVEL), items, ENEMY,
            [{"type": "AA"}] * 6 + [{"type": "E", "timing": "delayed"}],
            options)
        instant = simulate_build(
            LEVEL, default_ability_ranks(LEVEL), items, ENEMY,
            [{"type": "AA"}] * 6 + [{"type": "E"}], options)
        self.assertEqual(waited["total_damage"], 1390.59)
        self.assertEqual(waited["enemy"]["remaining_hp"], 2109.41)
        self.assertEqual(instant["total_damage"], 1397.88)
        self.assertEqual(instant["enemy"]["remaining_hp"], 2102.12)

        waited_e = next(event for event in waited["events"]
                        if event["source"] == "E active (missing HP)")
        instant_e = next(event for event in instant["events"]
                         if event["source"] == "E active (missing HP)")
        self.assertAlmostEqual(waited_e["dealt"], 78.8793, places=4)
        self.assertAlmostEqual(instant_e["dealt"], 86.1694, places=4)

        # The same fast-reset ordering repeats on the second Phantom Hit.
        tenth_instant = simulate_build(
            LEVEL, default_ability_ranks(LEVEL), items, ENEMY,
            [{"type": "AA"}] * 9 + [{"type": "E"}], options)
        self.assertEqual(tenth_instant["total_damage"], 2160.51)
        self.assertEqual(tenth_instant["enemy"]["remaining_hp"], 1339.49)

    def test_last_stand_documented_missing_health_brackets(self):
        base_options = {
            "rune_ids": [8005, 8009, 9104, 8299, 8226, 8234],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "pre_stacked_zeal": False,
        }
        items = ["nashors_tooth", "rabadons_deathcap"]
        cases = [
            (100, 1.00, 112.13),
            (61, 1.00, 112.13),
            (60, 1.05, 117.74),
            (50, 1.07, 119.98),
            (45, 1.08, 121.10),
            (40, 1.09, 122.22),
            (30, 1.11, 124.46),
            (20, 1.11, 124.46),
        ]
        for hp_pct, multiplier, expected_total in cases:
            result = simulate_build(
                LEVEL, default_ability_ranks(LEVEL), items, ENEMY,
                [{"type": "AA"}],
                {**base_options, "kayle_hp_pct": hp_pct})
            self.assertEqual(result["total_damage"], expected_total)
            self.assertTrue(all(event["multiplier"] == multiplier
                                for event in result["events"]
                                if event["type"] in ("physical", "magic", "true")))

    def test_rank_two_r_damage_matches_practice_tool(self):
        options = {
            "rune_ids": [8005, 8009, 9104, 8299, 8226, 8234],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
        }
        result = simulate_build(
            LEVEL, default_ability_ranks(LEVEL),
            ["nashors_tooth", "rabadons_deathcap"], ENEMY,
            [{"type": "R"}], options)
        self.assertEqual(result["total_damage"], 249.64)
        event = next(event for event in result["events"]
                     if event["source"].startswith("R"))
        self.assertAlmostEqual(event["raw"], 499.29, places=2)
        self.assertAlmostEqual(event["dealt"], 249.645, places=3)

    def test_level_twelve_gunblade_active_matches_practice_tool(self):
        options = {
            "rune_ids": [8005, 8009, 9104, 8299, 8226, 8234],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
        }
        result = simulate_build(
            LEVEL, default_ability_ranks(LEVEL),
            ["hextech_gunblade", "rabadons_deathcap"], ENEMY,
            [{"type": "ITEM_ACTIVE", "item": "hextech_gunblade"}], options)
        self.assertEqual(result["total_damage"], 155.44)
        event = next(event for event in result["events"]
                     if event["source"] == "Hextech Gunblade active")
        self.assertAlmostEqual(event["raw"], 310.8806, places=4)
        self.assertAlmostEqual(event["dealt"], 155.4403, places=4)

        # Wiki post-18 base values: 257.59 at level 19 and 262.18 at level 20.
        for level, base_damage, expected_total in [
                (19, 257.5882, 171.50), (20, 262.1765, 173.79)]:
            scaled = simulate_build(
                level, default_ability_ranks(level),
                ["hextech_gunblade", "rabadons_deathcap"], ENEMY,
                [{"type": "ITEM_ACTIVE", "item": "hextech_gunblade"}], options)
            scaled_event = next(event for event in scaled["events"]
                                if event["source"] == "Hextech Gunblade active")
            self.assertAlmostEqual(
                scaled_event["raw"] - 0.30 * scaled["stats"]["ap"],
                base_damage, places=3)
            self.assertEqual(scaled["total_damage"], expected_total)

    def test_lich_bane_spellblade_e_matches_practice_tool(self):
        options = {
            "rune_ids": [8005, 8009, 9104, 8299, 8226, 8234],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
        }
        result = simulate_build(
            LEVEL, default_ability_ranks(LEVEL),
            ["nashors_tooth", "lich_bane", "rabadons_deathcap"], ENEMY,
            [{"type": "E"}], options)
        self.assertEqual(result["total_damage"], 256.17)
        lich = next(event for event in result["events"]
                    if event["source"] == "Lich Bane Spellblade")
        self.assertAlmostEqual(lich["raw"], 242.5744, places=4)
        self.assertAlmostEqual(lich["dealt"], 121.2872, places=4)

    def test_dusk_and_dawn_q_attack_fast_e_stays_on_spellblade_cooldown(self):
        options = {
            "rune_ids": [8021, 8009, 9104, 8299, 8226, 8234],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
        }
        result = simulate_build(
            LEVEL, default_ability_ranks(LEVEL),
            ["nashors_tooth", "dusk_and_dawn", "rabadons_deathcap"], ENEMY,
            [{"type": "Q"}, {"type": "AA"}, {"type": "E"}], options)

        self.assertEqual(result["total_damage"], 636.70)
        self.assertEqual(result["enemy"]["remaining_hp"], 2863.30)
        spellblades = [event for event in result["events"]
                       if event["source"] == "Dusk and Dawn Spellblade"]
        self.assertEqual(len(spellblades), 1)

        waited = simulate_build(
            LEVEL, default_ability_ranks(LEVEL),
            ["nashors_tooth", "dusk_and_dawn", "rabadons_deathcap"], ENEMY,
            [{"type": "Q"}, {"type": "AA"},
             {"type": "E", "timing": "delayed"}], options)
        self.assertEqual(waited["total_damage"], 636.70)

        without_dusk = simulate_build(
            LEVEL, default_ability_ranks(LEVEL),
            ["nashors_tooth", "rabadons_deathcap"], ENEMY,
            [{"type": "Q"}, {"type": "AA"},
             {"type": "E", "timing": "delayed"}], options)
        self.assertEqual(without_dusk["total_damage"], 425.40)

    def test_removed_legacy_truncation_option_cannot_change_combat(self):
        combo = [{"type": "AA"}, {"type": "E"}, {"type": "AA"}]
        with_legacy_true = simulate(combo, truncate_damage=True)
        with_legacy_false = simulate(combo, truncate_damage=False)
        self.assertEqual(with_legacy_true["total_damage"], with_legacy_false["total_damage"])
        self.assertEqual(
            with_legacy_true["enemy"]["remaining_hp"],
            with_legacy_false["enemy"]["remaining_hp"],
        )

    def test_boots_are_limited_and_magic_penetration_profiles_apply(self):
        options = {
            "rune_ids": [8021, 8009, 9104, 8299, 8226],
            "shards": ["attack_speed", "adaptive", "health_scaling"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
        }
        ranks = default_ability_ranks(LEVEL)

        spellslinger = simulate_build(
            LEVEL, ranks, ["spellslingers_shoes"], ENEMY,
            [{"type": "Q"}], options)
        q = next(event for event in spellslinger["events"]
                 if event["source"].startswith("Q"))
        self.assertEqual(spellslinger["stats"]["magic_pen_pct"], 8.0)
        self.assertEqual(spellslinger["stats"]["magic_pen_flat"], 18.0)
        self.assertEqual(q["effective_resistance"], 74.0)

        sorcerers = simulate_build(
            LEVEL, ranks, ["sorcerers_shoes"], ENEMY,
            [{"type": "Q"}], options)
        q = next(event for event in sorcerers["events"]
                 if event["source"].startswith("Q"))
        self.assertEqual(sorcerers["stats"]["magic_pen_flat"], 12.0)
        self.assertEqual(q["effective_resistance"], 88.0)

        limited = simulate_build(
            LEVEL, ranks, ["swiftmarch", "sorcerers_shoes"], ENEMY,
            [], options)
        self.assertTrue(any("Limited to 1 Boots item" in warning
                            for warning in limited["warnings"]))
        self.assertEqual(limited["stats"]["movement_speed"], 400.0)

    def test_swiftmarch_recalculates_during_two_second_w_buff(self):
        options = {
            "rune_ids": [8021, 8009, 9104, 8299, 8226],
            "shards": ["attack_speed", "adaptive", "move_speed"],
            "legend_stacks": 0,
            "kayle_hp_pct": 100,
            "pre_stacked_zeal": False,
            "fleet_starts_energized": False,
        }
        ranks = {"Q": 5, "W": 1, "E": 4, "R": 2}
        items = ["swiftmarch", "nashors_tooth", "rabadons_deathcap"]

        idle = simulate_build(LEVEL, ranks, items, ENEMY, [], options)
        self.assertEqual(idle["stats"]["movement_speed"], 410.0)
        self.assertEqual(idle["stats"]["swiftmarch_adaptive_force"], 20.5)
        self.assertEqual(idle["stats"]["ap"], 336.3)

        result = simulate_build(
            LEVEL, ranks, items, ENEMY,
            [{"type": "W"}] + [{"type": "AA"}] * 4, options)
        w_note = next(event for event in result["events"]
                      if event["source"].startswith("W movement speed"))
        self.assertIn("538.24 total", w_note["source"])
        self.assertIn("+26.91 adaptive force", w_note["source"])

        nashor_hits = [event for event in result["events"]
                       if event["source"] == "Nashor's Tooth on-hit"]
        self.assertEqual(len(nashor_hits), 4)
        self.assertTrue(all(hit["t"] < 2.0 for hit in nashor_hits[:3]))
        self.assertGreater(nashor_hits[3]["t"], 2.0)
        self.assertAlmostEqual(nashor_hits[0]["raw"], 66.7891, places=4)
        self.assertAlmostEqual(nashor_hits[2]["raw"], 66.7891, places=4)
        self.assertAlmostEqual(nashor_hits[3]["raw"], 65.4387, places=4)

    def test_swiftmarch_static_movement_runes_stack_in_correct_layers(self):
        ranks = default_ability_ranks(18)
        celerity = simulate_build(
            18, ranks, ["swiftmarch"], ENEMY, [], {
                "rune_ids": [8234, 8304],
                "shards": ["adaptive", "move_speed", "health"],
                "pre_stacked_zeal": False,
            })
        # Swiftmarch + Magical Footwear are flat bonuses, the movement shard
        # and Exalted are additive %, and Celerity strengthens both layers.
        self.assertEqual(celerity["stats"]["movement_speed"], 462.95)
        self.assertEqual(celerity["stats"]["swiftmarch_adaptive_force"], 23.15)
        self.assertEqual(celerity["stats"]["ap"], 0.0)
        self.assertEqual(celerity["stats"]["bonus_ad"], 20.8)

        river = simulate_build(
            18, ranks, ["swiftmarch"], ENEMY, [], {
                "rune_ids": [8232],
                "assume_river": True,
                "shards": ["adaptive", "attack_speed", "health"],
            })
        self.assertEqual(river["stats"]["movement_speed"], 443.8)
        self.assertEqual(river["stats"]["swiftmarch_adaptive_force"], 22.19)
        self.assertEqual(river["stats"]["ap"], 0.0)
        self.assertEqual(river["stats"]["bonus_ad"], 39.7)

    def test_fleet_footwork_swiftmarch_window_affects_following_attack_only(self):
        result = simulate_build(
            18, default_ability_ranks(18),
            ["swiftmarch", "nashors_tooth", "rabadons_deathcap"], ENEMY,
            [{"type": "AA"}, {"type": "AA"}, {"type": "AA"}], {
                "rune_ids": [8021],
                "shards": ["attack_speed", "adaptive", "health"],
                "fleet_starts_energized": True,
            })
        note = next(event for event in result["events"]
                    if (event["source"].startswith("Fleet Footwork movement")
                        and "total" in event["source"]))
        self.assertIn("480.00 total", note["source"])
        nashor_hits = [event for event in result["events"]
                       if event["source"] == "Nashor's Tooth on-hit"]
        self.assertAlmostEqual(nashor_hits[0]["raw"], 65.7019, places=4)
        self.assertAlmostEqual(nashor_hits[1]["raw"], 66.1758, places=4)
        self.assertAlmostEqual(nashor_hits[2]["raw"], 65.7019, places=4)
        self.assertLess(nashor_hits[1]["t"], 1.0)
        self.assertGreater(nashor_hits[2]["t"], 1.0)

    def test_damage_activated_movement_runes_feed_swiftmarch(self):
        ranks = default_ability_ranks(18)
        approach = simulate_build(
            18, ranks, ["swiftmarch", "nashors_tooth"], ENEMY,
            [{"type": "Q"}, {"type": "AA"}], {
                "rune_ids": [8410],
                "shards": ["attack_speed", "adaptive", "health"],
            })
        q = next(event for event in approach["events"]
                 if event["source"].startswith("Q"))
        nashor = next(event for event in approach["events"]
                      if event["source"] == "Nashor's Tooth on-hit")
        self.assertAlmostEqual(q["raw"], 239.8050, places=4)
        self.assertAlmostEqual(nashor["raw"], 33.3303, places=4)
        self.assertEqual(approach["stats"]["movement_speed"], 483.0)

        storm = simulate_build(
            18, ranks,
            ["swiftmarch", "nashors_tooth", "rabadons_deathcap"],
            {"hp": 1000, "current_hp": 1000, "armor": 0, "mr": 0},
            [{"type": "Q"}, {"type": "AA"}], {
                "rune_ids": [8230],
                "shards": ["attack_speed", "adaptive", "health"],
            })
        storm_note = next(event for event in storm["events"]
                          if event["source"].startswith("Stormraider's Surge"))
        self.assertIn("522.00 total MS", storm_note["source"])
        storm_nashor = next(event for event in storm["events"]
                            if event["source"] == "Nashor's Tooth on-hit")
        self.assertAlmostEqual(storm_nashor["raw"], 66.6181, places=4)

    def test_w_and_celerity_recalculate_each_action_in_their_windows(self):
        result = simulate_build(
            12, {"Q": 5, "W": 1, "E": 4, "R": 2},
            ["swiftmarch", "nashors_tooth", "rabadons_deathcap"], ENEMY,
            [{"type": "W"}] + [{"type": "AA"}] * 4, {
                "rune_ids": [8234],
                "shards": ["attack_speed", "adaptive", "move_speed"],
                "legend_stacks": 0,
                "pre_stacked_zeal": False,
                "fleet_starts_energized": False,
            })
        w_note = next(event for event in result["events"]
                      if event["source"].startswith("W movement speed"))
        self.assertIn("551.60 total", w_note["source"])
        self.assertIn("+27.58 adaptive force", w_note["source"])
        hits = [event for event in result["events"]
                if event["source"] == "Nashor's Tooth on-hit"]
        self.assertEqual([hit["raw"] for hit in hits],
                         [66.9297, 66.9297, 66.9297, 65.5286])
        self.assertTrue(all(hit["t"] < 2.0 for hit in hits[:3]))
        self.assertGreater(hits[3]["t"], 2.0)

    def test_relentless_hunter_only_feeds_first_out_of_combat_damage(self):
        options = {
            "rune_ids": [8105],
            "relentless_stacks": 5,
            "shards": ["adaptive", "attack_speed", "health"],
        }
        with_stacks = simulate_build(
            18, default_ability_ranks(18),
            ["swiftmarch", "rabadons_deathcap"], ENEMY,
            [{"type": "Q"}], options)
        without_stacks = simulate_build(
            18, default_ability_ranks(18),
            ["swiftmarch", "rabadons_deathcap"], ENEMY,
            [{"type": "Q"}], {**options, "relentless_stacks": 0})
        q_with = next(event for event in with_stacks["events"]
                      if event["source"].startswith("Q"))
        q_without = next(event for event in without_stacks["events"]
                         if event["source"].startswith("Q"))
        self.assertGreater(q_with["raw"], q_without["raw"])
        # Once the Q deals damage, both simulations are in combat and return
        # to the same Swiftmarch stats.
        self.assertEqual(with_stacks["stats"]["movement_speed"],
                         without_stacks["stats"]["movement_speed"])
        self.assertEqual(with_stacks["stats"]["ap"], without_stacks["stats"]["ap"])


if __name__ == "__main__":
    unittest.main()
