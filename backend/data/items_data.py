"""Item data — transcribed from the sources in docs/SOURCES.md.

Icons are served locally from frontend/icons/<id>.png (downloaded from Data
Dragon 16.14.1 using the item IDs); the frontend falls back to the
Community Dragon CDN if a local icon is missing.
Stats keys: ad, ap, attack_speed (%), ability_haste, ultimate_haste, health,
armor, mr, magic_pen_flat, magic_pen_pct (fraction), armor_pen_pct (fraction),
move_speed_flat, move_speed_pct, crit_chance (%), crit_damage_bonus (%),
tenacity (%), slow_resist (%), omnivamp (fraction), life_steal (fraction).
"""

from . import ICON_VERSION

ICON_CDN = "https://cdn.communitydragon.org/latest/item/{id}"

# ---------------------------------------------------------------------------
# MANUAL PATCH EDITING QUICK REFERENCE
# ---------------------------------------------------------------------------
# Every item needs: id, name, cost, stats, tags, passive_text.
#
# Percent conventions:
#   attack_speed=25   -> 25%
#   move_speed_pct=4  -> 4%
#   magic_pen_pct=.30 -> 30%
#   ap_ratio=.15      -> 15% AP scaling
#
# Adding or changing normal stats requires NO engine.py change.
# Supported reusable damage fields also require NO engine.py change:
#   onhit_magic_flat: 45.0
#   onhit_magic: {"flat": 15.0, "ap_ratio": 0.15}
#   spellblade: {...}
#   active: {...}
#
# See docs/ITEM_MAINTENANCE.md for templates and the exact rule
# for when a genuinely new mechanic needs an engine hook.

SUPPORTED_STAT_KEYS = {
    "ad", "ap", "attack_speed", "ability_haste", "ultimate_haste",
    "health", "armor", "mr", "magic_pen_flat", "magic_pen_pct",
    "armor_pen_pct", "move_speed_flat", "move_speed_pct", "crit_chance",
    "crit_damage_bonus", "tenacity", "slow_resist", "omnivamp", "life_steal",
}

# These effect shapes are reusable for newly added items without engine edits.
GENERIC_EFFECT_FIELDS = {
    "onhit_magic_flat", "onhit_magic", "spellblade", "active",
}

# These are custom mechanics. Their numbers are still edited in this file. A
# completely new effect shape needs code in engine.py and a regression test.
CUSTOM_EFFECT_FIELDS = {
    "adaptive_force_from_total_ms", "glory_ap_per_stack", "glory_max_stacks",
    "ap_multiplier", "shadowflame_crit", "seething", "spelldance",
    "void_corruption", "void_infusion_bonus_hp_ratio", "bring_it_down",
    "juxtaposition", "vile_decay", "magnification", "sharpshooter",
    "overdrive", "practice_makes_lethal", "flurry", "transcendence",
    "giant_slayer", "electrospark", "bolt", "opening_barrage",
    "stormsurge",
}

ITEMS = {
    # === Starter items and boots ===========================================
    "boots": {
        "id": 1001,
        "name": "Boots",
        "cost": 300,
        "stats": {"move_speed_flat": 25},
        "tags": ["boots"],
        "passive_text": "25 movement speed. Limited to 1 Boots item.",
    },
    "boots_of_swiftness": {
        "id": 3009,
        "name": "Boots of Swiftness",
        "cost": 1000,
        "stats": {"move_speed_flat": 55, "slow_resist": 25},
        "tags": ["boots"],
        "passive_text": (
            "55 movement speed. Fleetfooted: 25% slow resist. Incoming slows "
            "are not modeled, and these boots do not grant Swiftmarch's "
            "adaptive-force conversion."),
    },
    "berserkers_greaves": {
        "id": 3006,
        "name": "Berserker's Greaves",
        "cost": 1100,
        "stats": {"attack_speed": 25, "move_speed_flat": 45},
        "tags": ["boots"],
        "passive_text": (
            "25% attack speed and 45 movement speed. Attack speed shortens "
            "basic-attack intervals and therefore combo duration."),
    },
    "gunmetal_greaves": {
        "id": 3172,
        "name": "Gunmetal Greaves",
        "cost": 1100,
        "stats": {
            "attack_speed": 40, "move_speed_flat": 45, "life_steal": 0.05,
        },
        "tags": ["boots", "mid_role_quest"],
        "passive_text": (
            "40% attack speed, 45 movement speed, and 5% life steal. Equipping "
            "this evolved mid-role boot activates the completed quest reward, "
            "which also increases bonus AD and AP by 8%."),
    },
    "dorans_ring": {
        "id": 1056,
        "name": "Doran's Ring",
        "cost": 400,
        "stats": {"ap": 18, "health": 90},
        "tags": ["starter"],
        "passive_text": (
            "Drain restores mana, or health for manaless champions. Helping Hand "
            "deals 5 bonus physical damage to minions (neither affects champion damage). "
            "Limited to 1 Starter item."),
    },
    "dorans_bow": {
        "id": 1086,
        "name": "Doran's Bow",
        "cost": 400,
        "stats": {"ad": 8, "attack_speed": 15, "omnivamp": 0.015},
        "tags": ["starter"],
        "passive_text": (
            "8 attack damage, 15% attack speed, and 1.5% omnivamp. "
            "Limited to 1 Starter item."),
    },
    "dorans_blade": {
        "id": 1055,
        "name": "Doran's Blade",
        "cost": 450,
        "stats": {"ad": 10, "health": 80, "omnivamp": 0.025},
        "tags": ["starter"],
        "passive_text": (
            "10 attack damage, 80 health, and 2.5% omnivamp. "
            "Limited to 1 Starter item."),
    },
    "dark_seal": {
        "id": 1082,
        "name": "Dark Seal",
        "cost": 350,
        "stats": {"ap": 15, "health": 50},
        "tags": ["starter", "dark_seal"],
        "passive_text": (
            "Glory: gain 4 ability power per Glory stack, up to 10. "
            "Five stacks are lost on death. Limited to 1 Starter item."),
        "glory_ap_per_stack": 4.0,
        "glory_max_stacks": 10,
    },
    "swiftmarch": {
        "id": 3170,
        "name": "Swiftmarch",
        "cost": 1000,
        "stats": {"move_speed_flat": 65},
        "tags": ["boots", "swiftmarch", "mid_role_quest"],
        "passive_text": (
            "Fleetfooted: 40% slow resist. Noxian Fervor: gain adaptive force "
            "equal to 5% of total movement speed. Completing the mid role "
            "quest also increases bonus AD and AP by 8%."),
        "adaptive_force_from_total_ms": 0.05,
    },
    "spellslingers_shoes": {
        "id": 3175,
        "name": "Spellslinger's Shoes",
        "cost": 1100,
        "stats": {
            "magic_pen_pct": 0.08, "magic_pen_flat": 18,
            "move_speed_flat": 45,
        },
        "tags": ["boots", "mid_role_quest"],
        "passive_text": (
            "8% magic penetration, 18 flat magic penetration, and 45 movement "
            "speed. Completing the mid role quest also increases bonus AD and "
            "AP by 8%."),
    },
    "sorcerers_shoes": {
        "id": 3020,
        "name": "Sorcerer's Shoes",
        "cost": 1100,
        "stats": {"magic_pen_flat": 12, "move_speed_flat": 45},
        "tags": ["boots"],
        "passive_text": "12 flat magic penetration and 45 movement speed.",
    },
    # === Core AP / hybrid items ============================================
    "dusk_and_dawn": {
        "id": 2510,
        "name": "Dusk and Dawn",
        "cost": 3100,
        "stats": {"ap": 60, "ability_haste": 20, "attack_speed": 20, "health": 300},
        "tags": ["spellblade"],
        "passive_text": ("Spellblade: after an ability, next basic attack within 10s deals "
                         "75% base AD (+10% AP) bonus magic damage, heals for 10% AP (+3% bonus HP) "
                         "and immediately applies on-hit effects again (1.5s cooldown)."),
        "spellblade": {
            "base_ad_ratio": 0.75, "ap_ratio": 0.10,
            "heal_ap_ratio": 0.10, "heal_bonus_hp_ratio": 0.03,
            "repeats_onhits": True,
        },
    },
    "guinsoos_rageblade": {
        "id": 3124,
        "name": "Guinsoo's Rageblade",
        "cost": 3000,
        "stats": {"ad": 30, "ap": 30, "attack_speed": 25},
        "tags": ["rageblade"],
        "passive_text": ("Wrath: attacks deal 30 bonus magic on-hit. Seething Strike: attacks grant "
                         "8% bonus AS (stacks 4x). At max stacks every 3rd attack triggers a Phantom Hit "
                         "that applies on-hit effects again."),
        "onhit_magic_flat": 30.0,
        "seething": {"as_per_stack": 8.0, "max_stacks": 4},
    },
    "lich_bane": {
        "id": 3100,
        "name": "Lich Bane",
        "cost": 2900,
        "stats": {"ap": 100, "ability_haste": 10, "move_speed_pct": 6},
        "tags": ["spellblade"],
        "passive_text": ("Spellblade: after an ability, next basic attack within 10s gains 50% bonus "
                         "attack speed and deals 75% base AD (+45% AP) bonus magic damage on-hit "
                         "(1.5s cooldown)."),
        "spellblade": {
            "base_ad_ratio": 0.75, "ap_ratio": 0.45,
            "bonus_as_while_primed": 50.0,
            "repeats_onhits": False,
        },
    },
    "rylais_crystal_scepter": {
        "id": 3116,
        "name": "Rylai's Crystal Scepter",
        "cost": 2600,
        "stats": {"ap": 65, "health": 400},
        "tags": [],
        "passive_text": "Rimefrost: ability damage slows affected units by 30% for 1 second.",
    },
    "shadowflame": {
        "id": 4645,
        "name": "Shadowflame",
        "cost": 3200,
        "stats": {"ap": 110, "magic_pen_flat": 15},
        "tags": ["shadowflame_crit"],
        "passive_text": ("Shadowflame crit: magic and true damage critically strike for 120% damage against "
                         "enemies below 40% maximum health."),
        "shadowflame_crit": {"threshold": 0.40, "amp": 1.20},
    },
    "zhonyas_hourglass": {
        "id": 3157,
        "name": "Zhonya's Hourglass",
        "cost": 3250,
        "stats": {"ap": 105, "armor": 50},
        "tags": ["active"],
        "passive_text": "Time Stop (active): stasis for 2.5s (120s cooldown). Deals no damage.",
        "active": {"kind": "stasis", "duration": 2.5, "cooldown": 120},
    },
    "banshees_veil": {
        "id": 3102,
        "name": "Banshee's Veil",
        "cost": 3000,
        "stats": {"ap": 105, "mr": 40},
        "tags": [],
        "passive_text": "Annul: spell shield blocking the next hostile ability (40s cooldown).",
    },
    "rabadons_deathcap": {
        "id": 3089,
        "name": "Rabadon's Deathcap",
        "cost": 3500,
        "stats": {"ap": 130},
        "tags": ["rabadon"],
        "passive_text": "Magical Opus: increases total ability power by 30%.",
        "ap_multiplier": 1.30,
    },
    "cryptbloom": {
        "id": 3137,
        "name": "Cryptbloom",
        "cost": 3000,
        "stats": {"ap": 75, "ability_haste": 20, "magic_pen_pct": 0.30},
        "tags": ["blight"],
        "passive_text": ("Life From Death: takedowns summon a healing nova (100 +20% AP, 60s cooldown). "
                         "Not simulated (takedown-gated). Limited to 1 Blight item."),
    },
    "void_staff": {
        "id": 3135,
        "name": "Void Staff",
        "cost": 3000,
        "stats": {"ap": 95, "magic_pen_pct": 0.40},
        "tags": ["blight"],
        "passive_text": "40% magic penetration. Limited to 1 Blight item.",
    },
    "hextech_gunblade": {
        "id": 3146,
        "name": "Hextech Gunblade",
        "cost": 3000,
        "stats": {"ad": 40, "ap": 80, "omnivamp": 0.10},
        "tags": ["active"],
        "passive_text": ("Lightning Bolt (active): 175-253 (based on level) (+30% AP) magic damage "
                         "and 25% slow for 1.5s (60s cooldown, 700 range)."),
        "active": {
            "kind": "damage",
            "base_lo": 175.0, "base_hi": 253.0, "ap_ratio": 0.30,
            "cooldown": 60,
        },
    },
    "nashors_tooth": {
        "id": 3115,
        "name": "Nashor's Tooth",
        "cost": 2900,
        "stats": {"ap": 80, "ability_haste": 15, "attack_speed": 50},
        "tags": [],
        "passive_text": "Icathian Bite: basic attacks deal 15 (+15% AP) bonus magic damage on-hit.",
        "onhit_magic": {"flat": 15.0, "ap_ratio": 0.15},
    },
    # === Extended current-patch item pool =================================
    "cosmic_drive": {
        "id": 4629,
        "name": "Cosmic Drive",
        "cost": 3000,
        "stats": {
            "ap": 70, "health": 350, "ability_haste": 25,
            "move_speed_pct": 4,
        },
        "tags": ["cosmic_drive"],
        "passive_text": (
            "Spelldance: magic or true damage to a champion grants 20 bonus "
            "movement speed for 4 seconds."),
        "spelldance": {"move_speed_flat": 20.0, "duration": 4.0},
    },
    "stormsurge": {
        "id": 4646,
        "name": "Stormsurge",
        "cost": 2800,
        "stats": {"ap": 90, "magic_pen_flat": 15, "move_speed_pct": 6},
        "tags": ["stormsurge"],
        "passive_text": (
            "Stormraider: dealing 25% of a champion's maximum health within "
            "2.5 seconds applies Squall and grants 25% movement speed for "
            "1.5 seconds (30-second cooldown). Squall: after 2 seconds, deal "
            "125 (+10% AP) magic damage."),
        "stormsurge": {
            "threshold": 0.25,
            "window": 2.5,
            "move_speed_pct": 25.0,
            "move_speed_duration": 1.5,
            "cooldown": 30.0,
            "squall_delay": 2.0,
            "squall_base": 125.0,
            "squall_ap_ratio": 0.10,
        },
    },
    "riftmaker": {
        "id": 4633,
        "name": "Riftmaker",
        "cost": 3100,
        "stats": {"ap": 70, "health": 350, "ability_haste": 15},
        "tags": ["riftmaker"],
        "passive_text": (
            "Void Corruption: gain 2% increased damage per second in champion "
            "combat, up to 8% at 4 stacks; at maximum stacks gain 10% melee / "
            "6% ranged omnivamp. Void Infusion: gain AP equal to 2% bonus HP."),
        "void_corruption": {
            "amp_per_stack": 0.02, "max_stacks": 4,
            "omnivamp_melee": 0.10, "omnivamp_ranged": 0.06,
        },
        "void_infusion_bonus_hp_ratio": 0.02,
    },
    "kraken_slayer": {
        "id": 6672,
        "name": "Kraken Slayer",
        "cost": 3000,
        "stats": {"ad": 45, "attack_speed": 40, "move_speed_pct": 4},
        "tags": ["kraken_slayer"],
        "passive_text": (
            "Bring It Down: every third on-hit application deals 150-200 "
            "melee / 120-160 ranged physical damage (levels 8-18), increased "
            "by up to 75% based on target missing HP. Level scaling keeps its "
            "slope through top-quest levels 19-20."),
        "bring_it_down": {
            "melee_lo": 150.0, "melee_hi": 200.0,
            "ranged_modifier": 0.80, "missing_hp_max_amp": 0.75,
            "stack_duration": 3.0,
        },
    },
    "terminus": {
        "id": 3302,
        "name": "Terminus",
        "cost": 3000,
        "stats": {"ad": 30, "attack_speed": 35},
        "tags": ["terminus", "fatality", "blight"],
        "passive_text": (
            "Shadow: attacks deal 30 magic damage on-hit. Juxtaposition: "
            "champion hits alternate Light and Dark; Dark grants 10% armor "
            "and magic penetration for 5 seconds, stacking 3 times. Limited "
            "to 1 Fatality and 1 Blight item."),
        "onhit_magic_flat": 30.0,
        "juxtaposition": {
            "dark_pen_per_stack": 0.10, "max_stacks": 3,
            "duration": 5.0,
        },
    },
    "infinity_edge": {
        "id": 3031,
        "name": "Infinity Edge",
        "cost": 3500,
        "stats": {"ad": 75, "crit_chance": 25, "crit_damage_bonus": 30},
        "tags": [],
        "passive_text": (
            "75 attack damage, 25% critical strike chance, and 30% critical "
            "strike damage. Random crits use expected damage in the simulator."),
    },
    "bloodletters_curse": {
        "id": 8010,
        "name": "Bloodletter's Curse",
        "cost": 2900,
        "stats": {"ap": 65, "health": 400, "ability_haste": 15},
        "tags": ["bloodletter", "blight"],
        "passive_text": (
            "Vile Decay: champion abilities and passives that deal magic damage "
            "reduce target MR by 7.5% for 6 seconds, up to 4 stacks / 30%, "
            "with a 0.3-second per-cast application gate. Limited to 1 Blight item."),
        "vile_decay": {
            "mr_reduction_per_stack": 0.075, "max_stacks": 4,
            "duration": 6.0, "application_gate": 0.3,
        },
    },
    "hexoptics_c44": {
        "id": 2523,
        "name": "Hexoptics C44",
        "cost": 2800,
        "stats": {"ad": 55, "crit_chance": 25},
        "tags": ["hexoptics"],
        "passive_text": (
            "Magnification: attacks deal 1% increased basic damage per 60 units "
            "to the target, up to 10% at 600. With no distance input, the "
            "simulator assumes Kayle attacks at her current maximum attack range."),
        "magnification": {"amp_per_unit": 0.01 / 60.0, "max_amp": 0.10},
    },
    "phantom_dancer": {
        "id": 3046,
        "name": "Phantom Dancer",
        "cost": 2650,
        "stats": {"attack_speed": 65, "crit_chance": 25, "move_speed_pct": 10},
        "tags": [],
        "passive_text": "Spectral Waltz grants Ghosted movement; it adds no damage instance.",
    },
    "rapid_firecannon": {
        "id": 3094,
        "name": "Rapid Firecannon",
        "cost": 2650,
        "stats": {"attack_speed": 35, "crit_chance": 25, "move_speed_pct": 4},
        "tags": ["rapid_firecannon"],
        "passive_text": (
            "Sharpshooter: a fully Energized attack deals 40 bonus magic "
            "damage on-hit and gains 35% bonus range, capped at +150. The "
            "Energized-start option controls whether the combo begins ready; "
            "the extended range is included in Hexoptics Magnification."),
        "sharpshooter": {
            "damage": 40.0, "bonus_range_pct": 0.35,
            "bonus_range_cap": 150.0,
        },
    },
    "experimental_hexplate": {
        "id": 3073,
        "name": "Experimental Hexplate",
        "cost": 3000,
        "stats": {
            "ad": 40, "attack_speed": 20, "health": 450,
            "ultimate_haste": 30,
        },
        "tags": ["experimental_hexplate"],
        "passive_text": (
            "Hexcharged: gain 30 ultimate haste. Overdrive: casting R grants "
            "35% bonus attack speed and 14% bonus movement speed to ranged "
            "champions for 8 seconds (50% / 20% for melee; 30-second cooldown)."),
        "overdrive": {
            "bonus_attack_speed_melee": 50.0,
            "bonus_attack_speed_ranged": 35.0,
            "move_speed_pct_melee": 20.0,
            "move_speed_pct_ranged": 14.0,
            "duration": 8.0, "cooldown": 30.0,
        },
    },
    "essence_reaver": {
        "id": 3508,
        "name": "Essence Reaver",
        "cost": 3050,
        "stats": {"ad": 50, "ability_haste": 20, "crit_chance": 25},
        "tags": ["spellblade"],
        "passive_text": (
            "Spellblade: after an ability, the next attack within 10 seconds "
            "deals 125% base AD plus 0.5% base AD per 1% total critical strike "
            "chance as bonus physical damage (1.5-second cooldown). Mana "
            "restoration is outside this damage model."),
        "spellblade": {
            "base_ad_ratio": 1.25,
            "base_ad_ratio_per_crit_pct": 0.005,
            "damage_type": "physical",
            "mana_restore_damage_ratio": 0.50,
            "repeats_onhits": False,
        },
    },
    "yun_tal_wildarrows": {
        "id": 3032,
        "name": "Yun Tal Wildarrows",
        "cost": 3100,
        "stats": {"ad": 50, "attack_speed": 40},
        "tags": ["yun_tal"],
        "passive_text": (
            "Practice Makes Lethal: attacks permanently grant 0.4% critical "
            "strike chance while melee or 0.2% while ranged, capped at 25%. "
            "Flurry: attacking a champion grants 30% attack speed for 6 "
            "seconds (30-second cooldown); attacks reduce that cooldown by 1 "
            "second, or an expected 2 seconds when they crit."),
        "practice_makes_lethal": {
            "crit_per_melee_attack": 0.4,
            "crit_per_ranged_attack": 0.2,
            "max_crit_chance": 25.0,
        },
        "flurry": {
            "bonus_attack_speed": 30.0, "duration": 6.0,
            "cooldown": 30.0, "reduction_on_hit": 1.0,
            "extra_reduction_on_crit": 1.0,
        },
    },
    "navori_flickerblade": {
        "id": 6675,
        "name": "Navori Flickerblade",
        "cost": 2650,
        "stats": {"attack_speed": 40, "crit_chance": 25, "move_speed_pct": 4},
        "tags": ["navori"],
        "passive_text": (
            "Transcendence: basic attacks reduce the remaining cooldowns of "
            "Q, W, and E by 15%."),
        "transcendence": {"remaining_cooldown_reduction": 0.15},
    },
    "lord_dominiks_regards": {
        "id": 3036,
        "name": "Lord Dominik's Regards",
        "cost": 3300,
        "stats": {"ad": 35, "armor_pen_pct": 0.35, "crit_chance": 25},
        "tags": ["fatality", "giant_slayer"],
        "passive_text": (
            "Giant Slayer: deal 1% increased damage per 100 target bonus HP, "
            "up to 15% at 1500. Limited to 1 Fatality item."),
        "giant_slayer": {"amp_per_bonus_hp": 0.01 / 100.0, "max_amp": 0.15},
    },
    "wits_end": {
        "id": 3091,
        "name": "Wit's End",
        "cost": 2800,
        "stats": {"attack_speed": 50, "mr": 45, "tenacity": 20},
        "tags": [],
        "passive_text": "Fray: basic attacks deal 45 bonus magic damage on-hit.",
        "onhit_magic_flat": 45.0,
    },
    "statikk_shiv": {
        "id": 3087,
        "name": "Statikk Shiv",
        "cost": 3000,
        "stats": {"ad": 45, "ap": 45, "attack_speed": 30, "move_speed_pct": 4},
        "tags": ["statikk_shiv"],
        "passive_text": (
            "Electrospark: an Energized basic attack deals 60 magic damage to "
            "champions. The scenario's Energized control determines whether "
            "the combo begins ready."),
        "electrospark": {"damage": 60.0},
    },
    "stormrazor": {
        "id": 3097,
        "name": "Stormrazor",
        "cost": 3200,
        "stats": {"ad": 50, "attack_speed": 20, "crit_chance": 25},
        "tags": ["stormrazor"],
        "passive_text": (
            "Bolt: a fully Energized attack deals 100 bonus magic damage on-hit "
            "and grants 45% movement speed for 1.5 seconds."),
        "bolt": {"damage": 100.0, "move_speed_pct": 45.0, "duration": 1.5},
    },
    "fiendhunter_bolts": {
        "id": 2512,
        "name": "Fiendhunter Bolts",
        "cost": 2650,
        "stats": {
            "attack_speed": 45, "crit_chance": 25, "move_speed_pct": 4,
            "ultimate_haste": 30,
        },
        "tags": ["fiendhunter"],
        "passive_text": (
            "Opening Barrage: after R, the next 3 attacks within 8 seconds gain "
            "50% attack speed and crit at 80% total critical damage. Attacks "
            "that would naturally crit use full critical damage and deal 15% "
            "bonus true damage (45-second cooldown)."),
        "opening_barrage": {
            "attacks": 3, "duration": 8.0, "bonus_attack_speed": 50.0,
            "forced_crit_modifier": 0.80, "natural_crit_true_ratio": 0.15,
            "cooldown": 45.0,
        },
    },
}


def validate_item_catalog(items=None):
    """Validate manual item edits and return True when the catalog is valid.

    This deliberately raises a readable ValueError during startup/test runs.
    A misspelled stat must never be accepted as zero without warning.
    """
    items = ITEMS if items is None else items
    required = {"id", "name", "cost", "stats", "tags", "passive_text"}
    allowed = required | GENERIC_EFFECT_FIELDS | CUSTOM_EFFECT_FIELDS
    used_ids = {}

    for key, item in items.items():
        label = f"ITEMS[{key!r}]"
        if not isinstance(key, str) or not key or key.lower() != key \
                or " " in key:
            raise ValueError(
                f"{label}: key must be lowercase snake_case without spaces")
        if not isinstance(item, dict):
            raise ValueError(f"{label}: item must be a dictionary")

        missing = sorted(required - set(item))
        if missing:
            raise ValueError(f"{label}: missing required fields: {missing}")
        unknown = sorted(set(item) - allowed)
        if unknown:
            raise ValueError(
                f"{label}: unknown fields {unknown}. If this is a genuinely "
                "new mechanic, add its engine hook and register the field in "
                "CUSTOM_EFFECT_FIELDS.")

        item_id = item["id"]
        if not isinstance(item_id, int) or item_id <= 0:
            raise ValueError(f"{label}.id must be a positive integer")
        if item_id in used_ids:
            raise ValueError(
                f"{label}.id duplicates {used_ids[item_id]!r}: {item_id}")
        used_ids[item_id] = key

        if not isinstance(item["name"], str) or not item["name"].strip():
            raise ValueError(f"{label}.name must be non-empty text")
        if not isinstance(item["cost"], (int, float)) or item["cost"] < 0:
            raise ValueError(f"{label}.cost must be a non-negative number")
        if not isinstance(item["passive_text"], str):
            raise ValueError(f"{label}.passive_text must be text")
        if not isinstance(item["tags"], list) \
                or not all(isinstance(tag, str) for tag in item["tags"]):
            raise ValueError(f"{label}.tags must be a list of text values")

        stats = item["stats"]
        if not isinstance(stats, dict):
            raise ValueError(f"{label}.stats must be a dictionary")
        bad_stats = sorted(set(stats) - SUPPORTED_STAT_KEYS)
        if bad_stats:
            raise ValueError(
                f"{label}.stats has unsupported keys {bad_stats}. Supported "
                f"keys: {sorted(SUPPORTED_STAT_KEYS)}")
        for stat, value in stats.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"{label}.stats[{stat!r}] must be numeric")

        for fraction_stat in (
                "magic_pen_pct", "armor_pen_pct", "omnivamp", "life_steal"):
            value = stats.get(fraction_stat, 0)
            if not 0 <= value <= 1:
                raise ValueError(
                    f"{label}.stats[{fraction_stat!r}] uses a 0-1 fraction; "
                    f"for example 0.30 means 30%")

        if "onhit_magic" in item:
            onhit = item["onhit_magic"]
            if not isinstance(onhit, dict) or "flat" not in onhit \
                    or "ap_ratio" not in onhit:
                raise ValueError(
                    f"{label}.onhit_magic needs flat and ap_ratio")

    return True


# Validate immediately so manual patch mistakes are visible when the server
# starts, not after the user notices an incorrect damage result.
validate_item_catalog()


def item_list_for_api():
    out = []
    for key, it in ITEMS.items():
        out.append({
            "key": key,
            "id": it["id"],
            "name": it["name"],
            "cost": it["cost"],
            "stats": it["stats"],
            "tags": it["tags"],
            "passive_text": it["passive_text"],
            "icon": f"icons/{it['id']}.png?v={ICON_VERSION}",
            "icon_fallback": ICON_CDN.format(id=it["id"]),
            "has_active": "active" in it,
            "active_kind": it.get("active", {}).get("kind"),
        })
    return out
