"""Rune tree — structure transcribed from the user's rune overview screenshot,
IDs/icons matched against Data Dragon 16.14.1 (identical tree).

`dmg` marks runes that amplify or deal damage (or grant combat stats) and will
be wired into the engine once the user provides each rune's math.
`math` stays None until then — runes without math contribute nothing yet.
Everything else is selectable in the UI but purely visual.
"""

RUNE_PATHS = [
    {
        "id": 8000, "key": "Precision", "name": "Precision",
        "slots": [
            [
                {"id": 8005, "name": "Press the Attack", "dmg": True,
                 "note": "proc damage + damage amp window"},
                {"id": 8008, "name": "Lethal Tempo", "dmg": True,
                 "note": "stacking AS, interacts with the 2.5 AS cap"},
                {"id": 8021, "name": "Fleet Footwork", "dmg": True,
                 "note": "Energized attack grants timed MS; feeds Swiftmarch"},
                {"id": 8010, "name": "Conqueror", "dmg": True,
                 "note": "stacking adaptive force"},
            ],
            [
                {"id": 9101, "name": "Absorb Life", "dmg": False, "note": "healing"},
                {"id": 9111, "name": "Triumph", "dmg": False, "note": "heal on takedown"},
                {"id": 8009, "name": "Presence of Mind", "dmg": False, "note": "mana"},
            ],
            [
                {"id": 9104, "name": "Legend: Alacrity", "dmg": True, "note": "attack speed"},
                {"id": 9105, "name": "Legend: Haste", "dmg": True, "note": "ability haste"},
                {"id": 9103, "name": "Legend: Bloodline", "dmg": False, "note": "lifesteal (sustain)"},
            ],
            [
                {"id": 8014, "name": "Coup de Grace", "dmg": True, "note": "amp vs low-HP enemies"},
                {"id": 8017, "name": "Cut Down", "dmg": True, "note": "amp vs high-max-HP enemies"},
                {"id": 8299, "name": "Last Stand", "dmg": True, "note": "amp while own HP low"},
            ],
        ],
    },
    {
        "id": 8100, "key": "Domination", "name": "Domination",
        "slots": [
            [
                {"id": 8112, "name": "Electrocute", "dmg": True, "note": "proc damage"},
                {"id": 8128, "name": "Dark Harvest", "dmg": True, "note": "stacking proc damage"},
                {"id": 9923, "name": "Hail of Blades", "dmg": True, "note": "burst attack speed"},
            ],
            [
                {"id": 8126, "name": "Cheap Shot", "dmg": True,
                 "note": "true damage vs impaired (Q slow / Rylai's enable it)"},
                {"id": 8139, "name": "Taste of Blood", "dmg": False, "note": "healing"},
                {"id": 8143, "name": "Sudden Impact", "dmg": False,
                 "note": "needs dash/blink/stealth — Kayle has none (visual only)"},
            ],
            [
                {"id": 8137, "name": "Sixth Sense", "dmg": False, "note": "vision"},
                {"id": 8140, "name": "Grisly Mementos", "dmg": False, "note": "utility"},
                {"id": 8141, "name": "Deep Ward", "dmg": False, "note": "vision"},
            ],
            [
                {"id": 8135, "name": "Treasure Hunter", "dmg": False, "note": "gold"},
                {"id": 8105, "name": "Relentless Hunter", "dmg": True,
                 "note": "out-of-combat MS per configured Bounty Hunter stack; feeds Swiftmarch"},
                {"id": 8106, "name": "Ultimate Hunter", "dmg": False, "note": "R haste (cooldown only)"},
            ],
        ],
    },
    {
        "id": 8200, "key": "Sorcery", "name": "Sorcery",
        "slots": [
            [
                {"id": 8214, "name": "Summon Aery", "dmg": True, "note": "proc damage"},
                {"id": 8229, "name": "Arcane Comet", "dmg": True, "note": "proc damage"},
                {"id": 8230, "name": "Stormraider's Surge", "dmg": True,
                 "note": "triggers after dealing 25% max HP in 3s; timed MS feeds Swiftmarch"},
                {"id": 8992, "name": "Deathfire Touch", "dmg": True, "note": "damage over time"},
            ],
            [
                {"id": 8224, "name": "Axiom Arcanist", "dmg": True, "note": "ultimate damage amp"},
                {"id": 8226, "name": "Manaflow Band", "dmg": False, "note": "mana"},
                {"id": 8275, "name": "Nimbus Cloak", "dmg": False,
                 "note": "requires a Summoner Spell action; not triggered by this combo simulator"},
            ],
            [
                {"id": 8210, "name": "Transcendence", "dmg": True,
                 "note": "+5 AH at lvl 5 and 8 (lvl-11 takedown refund not simulated)"},
                {"id": 8234, "name": "Celerity", "dmg": True,
                 "note": "+1% MS and 7% stronger MS bonuses; feeds Swiftmarch"},
                {"id": 8233, "name": "Absolute Focus", "dmg": True,
                 "note": "3-30 AP or 1.8-18 AD, scaling linearly by level while above 70% HP"},
            ],
            [
                {"id": 8237, "name": "Scorch", "dmg": True, "note": "bonus proc damage"},
                {"id": 8232, "name": "Waterwalking", "dmg": True,
                 "note": "optional river MS and adaptive stats; feeds Swiftmarch"},
                {"id": 8236, "name": "Gathering Storm", "dmg": True, "note": "scaling AP/AD over game time"},
            ],
        ],
    },
    {
        "id": 8400, "key": "Resolve", "name": "Resolve",
        "slots": [
            [
                {"id": 8437, "name": "Grasp of the Undying", "dmg": True, "note": "on-attack magic proc"},
                {"id": 8439, "name": "Aftershock", "dmg": False,
                 "note": "needs an immobilize — Kayle has none; the client swaps it for Grasp (visual only)"},
                {"id": 8465, "name": "Guardian", "dmg": False, "note": "shield"},
            ],
            [
                {"id": 8446, "name": "Demolish", "dmg": False, "note": "structures only"},
                {"id": 8463, "name": "Font of Life", "dmg": False, "note": "ally healing"},
                {"id": 8401, "name": "Shield Bash", "dmg": False,
                 "note": "needs a shield — Kayle has none"},
            ],
            [
                {"id": 8429, "name": "Conditioning", "dmg": False, "note": "resists"},
                {"id": 8444, "name": "Second Wind", "dmg": False, "note": "healing"},
                {"id": 8473, "name": "Bone Plating", "dmg": False, "note": "damage reduction"},
            ],
            [
                {"id": 8451, "name": "Overgrowth", "dmg": False, "note": "HP"},
                {"id": 8453, "name": "Revitalize", "dmg": False, "note": "heal/shield amp"},
                {"id": 8242, "name": "Unflinching", "dmg": False, "note": "tenacity"},
            ],
        ],
    },
    {
        "id": 8300, "key": "Inspiration", "name": "Inspiration",
        "slots": [
            [
                {"id": 8351, "name": "Glacial Augment", "dmg": False, "note": "slow/utility"},
                {"id": 8360, "name": "Unsealed Spellbook", "dmg": False, "note": "summoner swaps"},
                {"id": 8369, "name": "First Strike", "dmg": True, "note": "damage amp + gold"},
            ],
            [
                {"id": 8306, "name": "Hextech Flashtraption", "dmg": False, "note": "utility"},
                {"id": 8304, "name": "Magical Footwear", "dmg": True,
                 "note": "+10 MS when a Boots item is equipped; feeds Swiftmarch"},
                {"id": 8321, "name": "Cash Back", "dmg": False, "note": "gold"},
            ],
            [
                {"id": 8313, "name": "Triple Tonic", "dmg": False, "note": "consumables"},
                {"id": 8352, "name": "Time Warp Tonic", "dmg": False, "note": "consumables"},
                {"id": 8345, "name": "Biscuit Delivery", "dmg": False, "note": "sustain"},
            ],
            [
                {"id": 8347, "name": "Cosmic Insight", "dmg": False, "note": "summoner/item haste"},
                {"id": 8410, "name": "Approach Velocity", "dmg": True,
                 "note": "15% total MS toward targets impaired by Kayle; feeds Swiftmarch"},
                {"id": 8316, "name": "Jack of All Trades", "dmg": True,
                 "note": "stats per unique item stat"},
            ],
        ],
    },
]

# Rune math, keyed by rune id — transcribed from the user's wiki screenshots.
# "Based on level" pairs store the exact level-1 and level-18 references.
# The engine preserves that slope at top-quest levels 19-20 instead of clamping.
# "Adaptive" damage/stats resolve to physical/AD if bonus AD > AP, else magic/AP.
RUNE_MATH = {
    # Fleet Footwork: a fully Energized attack grants 20% melee / 15% ranged
    # bonus movement speed for 1 second. The simulator can start Energized.
    8021: {"ms_melee": 20.0, "ms_ranged": 15.0, "duration": 1.0},
    # Press the Attack: on-hit stacks; 3rd consumes all → proc + 8% amp until
    # 5s after exiting combat (lasts the rest of the combo here). CD 6s.
    # 40 at level 1, 160 at level 18, and 174.117647... at level 20.
    8005: {"stacks": 3, "proc_lo": 40, "proc_hi": 160, "amp": 0.08, "cd": 6.0},
    # Lethal Tempo: on-attack stacks (6s), 6%/4.8% AS (melee/ranged), max 6.
    # At max stacks each attack fires a bolt: adaptive, increased per 1% bonus
    # AS by 1% (melee) / 0.8333% (ranged — wiki-documented 1/6-reduction bug).
    8008: {"max_stacks": 6, "as_melee": 6.0, "as_ranged": 4.8,
           "bolt_melee": (9, 30), "bolt_ranged": (6, 24),
           "bolt_amp_melee": 0.01, "bolt_amp_ranged": 0.008333},
    # Conqueror: 2 stacks per melee on-attack / 1 ranged / 2 per ability cast
    # instance (Kayle's fire wave shares the attack's cast instance → no extra).
    # Max 12; adaptive stats per stack; heal 8%/5% post-mit at max stacks.
    8010: {"max_stacks": 12, "per_attack_melee": 2, "per_attack_ranged": 1,
           "per_ability": 2, "ad_per": (1.08, 2.4), "ap_per": (1.8, 4.0),
           "heal_melee": 0.08, "heal_ranged": 0.05},
    # Electrocute: 3 stacks (1 per cast instance) within 3s → proc. CD 20s.
    8112: {"lo": 70, "hi": 240, "bonus_ad": 0.10, "ap": 0.05,
           "window": 3.0, "cd": 20.0},
    # Dark Harvest: proc vs enemies below 50% max HP. CD 35s (reset on takedown).
    8128: {"base": 30, "per_soul": 11, "bonus_ad": 0.10, "ap": 0.05,
           "threshold": 0.50, "cd": 35.0},
    # Relentless Hunter: 8 flat out-of-combat MS per Bounty Hunter stack.
    8105: {"flat_per_stack": 8.0, "max_stacks": 5},
    # Hail of Blades: first windup grants 2 stacks (+1 per attack-reset cast,
    # up to 2); 120%/60% AS while stacks remain, exceeds the AS cap; empowered
    # attacks deal bonus true damage; 1 stack consumed per attack. CD 10s.
    9923: {"stacks": 2, "extra_stacks": 2, "as_melee": 120.0, "as_ranged": 60.0,
           "true_lo": 4, "true_hi": 20, "bonus_ad": 0.08, "ap": 0.06},
    # Summon Aery: adaptive proc; unavailable until she returns (~4s modeled).
    8214: {"lo": 10, "hi": 50, "bonus_ad": 0.10, "ap": 0.05, "cd": 4.0},
    # Arcane Comet: adaptive proc on ability damage, lands after 0.825s
    # (assumed to hit, point-blank values). CD 20-6.59 by level.
    8229: {"lo": 15, "hi": 100, "bonus_ad": 0.10, "ap": 0.05,
           "delay": 0.825, "cd_lo": 20.0, "cd_hi": 8.0},
    # Stormraider's Surge (26.10): deal 25% target max HP within 3 seconds to
    # gain 48% melee / 36% ranged MS for 4 seconds.
    8230: {"threshold": 0.25, "window": 3.0, "ms_melee": 48.0,
           "ms_ranged": 36.0, "duration": 4.0, "cd_lo": 20.0, "cd_hi": 10.0},
    # Celerity: +1% additive MS and all other flat, additive, and
    # multiplicative MS bonuses are 7% more effective.
    8234: {"base_pct": 1.0, "bonus_effectiveness": 0.07},
    # Deathfire Touch: burn ticking every 0.5s; duration 4s for spell damage,
    # 2s for area damage (Q, R and fire waves are area damage). +75% damage
    # after burning 3s continuously.
    8992: {"tick_lo": 1.5, "tick_hi": 6.0, "bonus_ad": 0.035, "ap": 0.0125,
           "interval": 0.5, "dur_area": 2.0, "dur_spell": 4.0,
           "linger_amp": 0.75, "linger_time": 3.0},
    # Grasp of the Undying: 1 stack/second in combat (max 4); at 4 the next
    # attack deals % max HP magic on-hit and heals (% max HP).
    8437: {"stacks": 4, "dmg_melee": 0.035, "dmg_ranged": 0.014,
           "heal_melee": 0.013, "heal_ranged": 0.0052},
    # First Strike: first hit opens a 3s window; +7% of post-mitigation damage
    # as bonus true damage (gold not simulated). CD 25-15 by level.
    8369: {"amp": 0.07, "duration": 3.0},
    # Coup de Grace / Cut Down / Last Stand
    8014: {"amp": 0.08, "below_pct": 0.40},
    8017: {"amp": 0.08, "above_pct": 0.60},
    # Last Stand by missing HP: 5% at 40% missing, +2% per additional
    # 10% missing, and 11% at 70% missing or more.
    8299: {"amp_lo": 0.05, "amp_hi": 0.11, "hp_hi": 0.60, "hp_lo": 0.30},
    # Cheap Shot: true damage vs already-impaired targets. CD 4s.
    8126: {"lo": 10, "hi": 45, "cd": 4.0},
    # Scorch: bonus magic on ability damage after 1s. CD 10s.
    8237: {"lo": 20, "hi": 40, "delay": 1.0, "cd": 10.0},
    # Waterwalking: while in river, +10 flat MS and level-scaled adaptive stats.
    8232: {"flat_ms": 10.0, "ad_lo": 7.8, "ad_hi": 18.0,
           "ap_lo": 13.0, "ap_hi": 30.0},
    # Gathering Storm: cumulative adaptive per 10 minutes (index = min//10).
    8236: {"ad": [0, 4.8, 14.4, 28.8, 48, 72, 100.8, 134.4],
           "ap": [0, 8, 24, 48, 80, 120, 168, 224]},
    # Absolute Focus: linear level scaling (the level-10 AP value is 17.2941),
    # active only while strictly above 70% maximum health.
    8233: {"ad_lo": 1.8, "ad_hi": 18.0, "ap_lo": 3.0, "ap_hi": 30.0,
           "hp_threshold": 0.70},
    # Legend: Alacrity: 3% +1.5% per Legend stack (max 10 stacks → 18%).
    9104: {"base": 3.0, "per_stack": 1.5, "max_stacks": 10},
    # Legend: Haste: 1.5 BASIC ability haste per Legend stack (Q/W/E only), max 15.
    9105: {"per_stack": 1.5, "max": 15.0},
    # Transcendence: +5 ability haste at levels 5 and 8. The level-11 takedown
    # cooldown refund is takedown-gated and not simulated.
    8210: {"lvl5": 5.0, "lvl8": 5.0},
    # Magical Footwear: all acquired/upgraded Boots retain +10 flat MS.
    8304: {"flat_ms": 10.0},
    # Approach Velocity: 7.5% multiplicative total MS toward an impaired
    # champion, doubled when Kayle supplied the impairment (Q/Rylai/Gunblade).
    8410: {"other_impairment": 0.075, "own_impairment": 0.15},
    # Axiom Arcanist: +12% ultimate damage, reduced to +8% for AoE ults
    # (Kayle's R is area damage → 8%).
    8224: {"amp": 0.12, "amp_aoe": 0.08},
    # Jack of All Trades: 1 AH per unique item stat type; adaptive bonus at
    # 5 (3.6 AD / 6 AP) and 10 (total 12 AD / 20 AP) stacks.
    8316: {"haste_per": 1.0, "ad_5": 3.6, "ap_5": 6.0, "ad_10": 12.0, "ap_10": 20.0},
}


# Stat shards — values from the user's wiki screenshot. One pick per slot.
# "combat": whether the shard affects the simulation (others are visual only).
SHARDS = [
    {   # Slot 1 — Offense
        "name": "Offense",
        "options": [
            {"key": "adaptive", "name": "Adaptive Force",
             "text": "5.4 AD or 9 AP (Adaptive)", "combat": True,
             "icon": "StatModsAdaptiveForceIcon"},
            {"key": "attack_speed", "name": "Attack Speed",
             "text": "10% bonus attack speed", "combat": True,
             "icon": "StatModsAttackSpeedIcon"},
            {"key": "haste", "name": "Ability Haste",
             "text": "8 ability haste", "combat": True,
             "icon": "StatModsCDRScalingIcon"},
        ],
    },
    {   # Slot 2 — Flex
        "name": "Flex",
        "options": [
            {"key": "adaptive", "name": "Adaptive Force",
             "text": "5.4 AD or 9 AP (Adaptive)", "combat": True,
             "icon": "StatModsAdaptiveForceIcon"},
            {"key": "move_speed", "name": "Movement Speed",
             "text": "2.5% bonus movement speed", "combat": True,
             "icon": "StatModsMovementSpeedIcon"},
            {"key": "health_scaling", "name": "Scaling Health",
             "text": "10-200 bonus health (based on level)", "combat": True,
             "icon": "StatModsHealthScalingIcon"},
        ],
    },
    {   # Slot 3 — Defense
        "name": "Defense",
        "options": [
            {"key": "health", "name": "Health",
             "text": "65 bonus health", "combat": True,
             "icon": "StatModsHealthPlusIcon"},
            {"key": "tenacity", "name": "Tenacity & Slow Resist",
             "text": "15% tenacity and slow resist (visual only)", "combat": False,
             "icon": "StatModsTenacityIcon"},
            {"key": "health_scaling", "name": "Scaling Health",
             "text": "10-200 bonus health (based on level)", "combat": True,
             "icon": "StatModsHealthScalingIcon"},
        ],
    },
]

SHARD_VALUES = {
    "adaptive_ad": 5.4, "adaptive_ap": 9.0,
    "attack_speed": 10.0, "haste": 8.0,
    "move_speed_pct": 2.5,
    "health": 65.0, "health_scaling_lo": 10.0, "health_scaling_hi": 200.0,
}


def runes_for_api():
    shards = [
        {
            "name": slot["name"],
            "options": [{**o, "icon": f"icons/runes/{o['icon']}.png"}
                        for o in slot["options"]],
        }
        for slot in SHARDS
    ]
    out = []
    for p in RUNE_PATHS:
        out.append({
            "id": p["id"], "key": p["key"], "name": p["name"],
            "icon": f"icons/runes/path_{p['id']}.png",
            "slots": [
                [{
                    "id": r["id"], "name": r["name"], "dmg": r["dmg"],
                    "note": r["note"],
                    "icon": f"icons/runes/{r['id']}.png",
                    "has_math": r["id"] in RUNE_MATH,
                } for r in slot]
                for slot in p["slots"]
            ],
        })
    return {"paths": out, "shards": shards}
