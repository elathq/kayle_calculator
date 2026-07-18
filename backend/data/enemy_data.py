"""Enemy simulation presets.

Presets are archetype base stats scaled with Riot's growth formula so the
"average enemy at level X" tracks a real game state. Values are league-wide
approximations of champion base stats per class; all fields stay editable
in the UI after a preset is applied.
"""

from .kayle_data import growth_factor

ENEMY_PRESETS = {
    "dummy": {
        "name": "Target Dummy (100/100)",
        "scaling": False,
        "hp": 3500.0, "armor": 100.0, "mr": 100.0,
    },
    "squishy": {
        "name": "Squishy (ADC / Mage)",
        "scaling": True,
        "hp":    {"base": 630.0, "growth": 104.0},
        "armor": {"base": 26.0,  "growth": 4.2},
        "mr":    {"base": 30.0,  "growth": 1.3},
    },
    "average": {
        "name": "Average Champion",
        "scaling": True,
        "hp":    {"base": 655.0, "growth": 106.0},
        "armor": {"base": 33.0,  "growth": 4.7},
        "mr":    {"base": 32.0,  "growth": 1.55},
    },
    "tank": {
        "name": "Tank / Bruiser",
        "scaling": True,
        "hp":    {"base": 665.0, "growth": 115.0},
        "armor": {"base": 40.0,  "growth": 5.5},
        "mr":    {"base": 32.0,  "growth": 2.05},
    },
}


def enemy_stats(preset_key: str, level: int) -> dict:
    p = ENEMY_PRESETS[preset_key]
    if not p["scaling"]:
        return {
            "hp": p["hp"], "bonus_hp": 0.0,
            "armor": p["armor"], "mr": p["mr"], "name": p["name"],
        }
    g = growth_factor(level)
    return {
        "hp": round(p["hp"]["base"] + p["hp"]["growth"] * g, 1),
        "bonus_hp": 0.0,
        "armor": round(p["armor"]["base"] + p["armor"]["growth"] * g, 1),
        "mr": round(p["mr"]["base"] + p["mr"]["growth"] * g, 1),
        "name": p["name"],
    }
