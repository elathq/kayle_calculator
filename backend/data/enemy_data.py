"""Enemy simulation presets.

The scalable presets are unweighted averages from Riot Data Dragon 16.14.1.
"Squishy" includes champions tagged Marksman or Mage, "tank" includes Tank or
Fighter, and "average" includes the complete champion catalog. They model base
stats only; items and bonus health remain explicit UI inputs.
"""

from .kayle_data import growth_factor

ENEMY_PRESETS = {
    "dummy": {
        "name": "Target Dummy (100/100)",
        "scaling": False,
        "hp": 3500.0, "armor": 100.0, "mr": 100.0,
    },
    "squishy": {
        "name": "Squishy average (Marksman / Mage)",
        "scaling": True,
        "hp":    {"base": 604.11, "growth": 102.62},
        "armor": {"base": 25.97,  "growth": 4.51},
        "mr":    {"base": 30.06,  "growth": 1.41},
    },
    "average": {
        "name": "All-champion average",
        "scaling": True,
        "hp":    {"base": 617.08, "growth": 103.93},
        "armor": {"base": 29.57,  "growth": 4.54},
        "mr":    {"base": 30.73,  "growth": 1.68},
    },
    "tank": {
        "name": "Tank / Fighter average",
        "scaling": True,
        "hp":    {"base": 632.42, "growth": 105.46},
        "armor": {"base": 34.02,  "growth": 4.57},
        "mr":    {"base": 31.36,  "growth": 1.99},
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
