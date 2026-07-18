"""Pure damage-resolution helpers.

League keeps combat statistics at fractional precision even when parts of the
UI show whole numbers.  The simulator therefore resolves and applies exact
post-mitigation damage.  Rounding belongs only to presentation and must never
feed back into HP, missing-health ratios, threshold effects, or healing.

Keeping this pipeline pure makes each stage independently testable against
Practice Tool observations:

    raw -> outgoing modifiers -> resistance mitigation -> applied damage
"""

from dataclasses import dataclass
import math


DAMAGE_TYPES = frozenset({"physical", "magic", "true"})


@dataclass(frozen=True)
class DamageCalculation:
    """The complete calculation for one engine-level damage instance."""

    raw: float
    outgoing_multiplier: float
    amplified: float
    effective_resistance: float | None
    mitigation_multiplier: float
    applied: float


def resistance_multiplier(resistance: float) -> float:
    """Return League's damage multiplier for an effective resistance value."""
    resistance = float(resistance)
    if resistance >= 0:
        return 100.0 / (100.0 + resistance)
    return 2.0 - 100.0 / (100.0 - resistance)


def effective_resistance(
    resistance: float,
    *,
    reduction_pct: float = 0.0,
    penetration_pct: float = 0.0,
    flat_penetration: float = 0.0,
) -> float:
    """Apply reduction, percentage penetration, then flat penetration.

    Penetration cannot push a positive resistance below zero.  A resistance
    which is already negative remains negative and is not affected by
    penetration, matching the engine's existing ordering.
    """
    result = float(resistance) * (1.0 - float(reduction_pct))
    if result > 0:
        result *= 1.0 - float(penetration_pct)
        result = max(0.0, result - float(flat_penetration))
    return result


def resolve_damage(
    raw: float,
    damage_type: str,
    *,
    outgoing_multiplier: float = 1.0,
    resistance: float | None = None,
) -> DamageCalculation:
    """Resolve one damage instance without mutating simulation state.

    ``resistance`` must already include reductions and penetration.  True
    damage ignores it.  No stage rounds or truncates the value.
    """
    if damage_type not in DAMAGE_TYPES:
        raise ValueError(f"unknown damage type: {damage_type!r}")

    raw = float(raw)
    outgoing_multiplier = float(outgoing_multiplier)
    if not math.isfinite(raw) or raw < 0:
        raise ValueError(f"damage must be a finite non-negative number, got {raw!r}")
    if not math.isfinite(outgoing_multiplier) or outgoing_multiplier < 0:
        raise ValueError(
            "outgoing damage multiplier must be a finite non-negative number, "
            f"got {outgoing_multiplier!r}"
        )

    amplified = raw * outgoing_multiplier
    if damage_type == "true":
        effective = None
        mitigation = 1.0
    else:
        effective = float(0.0 if resistance is None else resistance)
        mitigation = resistance_multiplier(effective)

    return DamageCalculation(
        raw=raw,
        outgoing_multiplier=outgoing_multiplier,
        amplified=amplified,
        effective_resistance=effective,
        mitigation_multiplier=mitigation,
        applied=amplified * mitigation,
    )
