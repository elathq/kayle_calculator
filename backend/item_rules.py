"""Shared item-build legality rules.

The public API, simulation engine, and frontend bootstrap all use this module
so an illegal build is rejected instead of being silently changed.
"""

from __future__ import annotations

from collections.abc import Sequence

from .data.items_data import ITEMS


EXCLUSIVE_ITEM_GROUPS = {
    "spellblade": "Spellblade",
    "blight": "Blight",
    "fatality": "Fatality",
    "boots": "Boots",
    "starter": "Starter",
}

ITEM_TAG_LEVEL_LIMITS = {
    "mid_role_quest": {
        "max_level": 18,
        "reason": "mid-role quest rewards cannot be combined with levels 19–20",
    },
}


class ItemBuildValidationError(ValueError):
    """Describe the first illegal item without exposing internal state."""

    def __init__(self, item_index: int, message: str) -> None:
        self.item_index = item_index
        super().__init__(message)


def validate_item_build(level: int, item_keys: Sequence[str]) -> list[str]:
    """Return ``item_keys`` unchanged when the item combination is legal."""
    seen_items: set[str] = set()
    occupied_groups: dict[str, str] = {}

    for item_index, key in enumerate(item_keys):
        if key not in ITEMS:
            raise ItemBuildValidationError(
                item_index, "is not a known item")

        item = ITEMS[key]
        if key in seen_items:
            raise ItemBuildValidationError(
                item_index,
                f"duplicates {item['name']}; each item can only be equipped once",
            )

        for tag, rule in ITEM_TAG_LEVEL_LIMITS.items():
            if tag in item["tags"] and level > rule["max_level"]:
                raise ItemBuildValidationError(
                    item_index,
                    f"cannot use {item['name']} at level {level}: {rule['reason']}",
                )

        groups = [
            group for group in EXCLUSIVE_ITEM_GROUPS
            if group in item["tags"]
        ]
        conflicting_group = next(
            (group for group in groups if group in occupied_groups),
            None,
        )
        if conflicting_group:
            previous_key = occupied_groups[conflicting_group]
            label = EXCLUSIVE_ITEM_GROUPS[conflicting_group]
            raise ItemBuildValidationError(
                item_index,
                f"cannot combine {item['name']} with "
                f"{ITEMS[previous_key]['name']}; only one {label} item is allowed",
            )

        seen_items.add(key)
        for group in groups:
            occupied_groups[group] = key

    return list(item_keys)


def item_rules_for_api() -> dict:
    """Return the subset of legality rules needed by the item picker."""
    return {
        "exclusive_groups": dict(EXCLUSIVE_ITEM_GROUPS),
        "level_limits": {
            tag: dict(rule)
            for tag, rule in ITEM_TAG_LEVEL_LIMITS.items()
        },
    }
