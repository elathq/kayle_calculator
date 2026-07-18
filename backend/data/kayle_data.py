"""Kayle champion data — transcribed from LoL Wiki screenshots provided by the user.

All scaling stats use Riot's standard growth formula:
    stat(n) = base + growth * (n-1) * (0.7025 + 0.0175 * (n-1))
"""


def growth_factor(level: int) -> float:
    """Riot's per-level growth multiplier for level n (n >= 1)."""
    return (level - 1) * (0.7025 + 0.0175 * (level - 1))


def stat_at_level(base: float, growth: float, level: int) -> float:
    return base + growth * growth_factor(level)


def lerp_by_level(
        lo: float, hi: float, level: int, lo_lvl: int = 1,
        hi_lvl: int = 18, cap_lvl: int | None = None) -> float:
    """Interpolate a level-scaled value, optionally extrapolating to a new cap.

    Most League data gives the original level-1 and level-18 reference values.
    Top quest effects keep that same per-level slope through levels 19 and 20,
    so callers use ``cap_lvl=20`` without replacing the level-18 reference.
    """
    cap_lvl = hi_lvl if cap_lvl is None else cap_lvl
    level = max(lo_lvl, min(cap_lvl, level))
    return lo + (hi - lo) * (level - lo_lvl) / (hi_lvl - lo_lvl)


KAYLE_BASE = {
    "hp":        {"base": 670.0, "growth": 92.0},
    "mana":      {"base": 330.0, "growth": 50.0},
    "hp5":       {"base": 5.0,   "growth": 0.5},
    "mp5":       {"base": 8.0,   "growth": 0.8},
    "ad":        {"base": 50.0,  "growth": 2.5},
    "armor":     {"base": 26.0,  "growth": 4.2},
    "mr":        {"base": 22.0,  "growth": 1.3},
    # Bonus AS growth is % bonus attack speed, also using the growth formula
    "bonus_as":  {"base": 0.0,   "growth": 1.5},
}

KAYLE_AS = {
    "base_as": 0.625,
    "as_ratio": 0.667,    # bonus AS is multiplied by this ratio, not by base AS
    "windup_percent": 0.19355,
    "crit_damage": 2.0,
    "ms": 335,
    "range_base": 175,
}

# Passive — Divine Ascent
PASSIVE = {
    "zeal_as_per_stack": 6.0,      # % bonus AS per Zeal stack
    "zeal_max_stacks": 5,
    "exalted_ms": 10.0,
    "arisen_level": 6,             # +350 range (525 total)
    "aflame_level": 11,            # Exalted attacks launch fire waves
    "transcendent_level": 16,      # permanently Exalted, range 625
    # Fire wave base damage is breakpoint-scaled in the game data: it remains
    # 20 through level 11, then gains 3 per level from level 12 onward.
    # This produces 41 at level 18 and 47 at top-quest level 20.
    "wave_base": 20.0,
    "wave_growth_start_level": 12,
    "wave_growth_per_level": 3.0,
    "wave_bonus_ad_ratio": 0.10,
    "wave_ap_ratio": 0.25,
}

# Q — Radiant Blast
Q = {
    "base": [60, 90, 120, 150, 180],
    "bonus_ad_ratio": 0.60,
    "ap_ratio": 0.50,
    "shred": 0.15,                 # 15% armor & MR reduction
    "shred_duration": 4.0,
    "cooldown": [12, 11, 10, 9, 8],
    "mana": [60, 70, 80, 90, 100],
    # Cast time equals attack windup: windup_percent / total AS
}

# W — Celestial Blessing
W = {
    "heal": [55, 80, 105, 130, 155],
    "heal_ap_ratio": 0.25,
    "ms_pct": [24, 28, 32, 36, 40],
    "ms_ap_per100": 8.0,
    "ms_duration": 2.0,
    "cooldown": [15, 15, 15, 15, 15],
    "mana": [70, 75, 80, 85, 90],
    "cast_time": 0.25,
}

# E — Starfire Spellblade
E = {
    # Passive on-hit magic damage
    "onhit_base": [15, 20, 25, 30, 35],
    "onhit_bonus_ad_ratio": 0.10,
    "onhit_ap_ratio": 0.20,
    # Active: % missing health bonus magic damage (dealt at cast)
    "active_missing_hp_pct": [8.0, 8.5, 9.0, 9.5, 10.0],
    # Practice Tool AA -> E isolation confirms +1.5% per 100 AP.
    "active_missing_hp_per100ap": 1.5,
    "cooldown": [8, 7.5, 7, 6.5, 6],
    "cast_time": 0.0,              # no cast time, resets attack timer
}

# R — Divine Judgment
R = {
    "base": [200, 300, 400],
    "bonus_ad_ratio": 1.00,
    "ap_ratio": 0.70,
    "cooldown": [160, 120, 80],
    "mana": [100, 50, 0],
    "cast_time": 0.5,
    "impact_delay": 2.5,           # swords rain down 2.5s after cast start
}


def default_ability_ranks(level: int) -> dict:
    """Default skill order: E, Q, W, then max Q > E > W with R at 6/11/16."""
    skill_order = (
        "E", "Q", "W", "Q", "Q", "R", "Q", "E", "Q",
        "E", "R", "E", "E", "W", "W", "R", "W", "W",
    )
    ranks = {"Q": 0, "W": 0, "E": 0, "R": 0}
    for ability in skill_order[:max(0, min(18, level))]:
        ranks[ability] += 1
    return ranks


def kayle_stats_at(level: int) -> dict:
    return {
        "level": level,
        "hp": stat_at_level(**KAYLE_BASE["hp"], level=level),
        "mana": stat_at_level(**KAYLE_BASE["mana"], level=level),
        "base_ad": stat_at_level(**KAYLE_BASE["ad"], level=level),
        "armor": stat_at_level(**KAYLE_BASE["armor"], level=level),
        "mr": stat_at_level(**KAYLE_BASE["mr"], level=level),
        "level_bonus_as": stat_at_level(**KAYLE_BASE["bonus_as"], level=level),  # in %
        "base_as": KAYLE_AS["base_as"],
        "as_ratio": KAYLE_AS["as_ratio"],
        "windup_percent": KAYLE_AS["windup_percent"],
    }
