# Maintaining items

This guide is for manually updating the calculator after a League patch. The
editable catalog is `backend/data/items_data.py`; every selectable item is one
entry in the `ITEMS` dictionary.

Before changing a value, record its source in [Data and icon sources](SOURCES.md).
After changing behavior, document the evidence and result in
[Validation and backtesting](VALIDATION.md). The supported ordering and explicit
scope belong in the [simulation model](MODEL.md).

## Patch-update workflow

- Record the League patch and review date in `SOURCES.md`.
- Check Riot patch notes first, then the current item page.
- Update the catalog entry without changing its stable internal key.
- Implement new behavior at its real trigger point in `backend/engine.py`.
- Add or update a focused automated test.
- Run the complete suite and baseline backtest.
- Repeat affected Practice Tool isolations and record the evidence.
- Update `ICON_VERSION` only when local icon bytes changed.

## Do I need to edit `engine.py`?

| Change | Edit `engine.py`? |
|---|---|
| Name, ID, price, description, or icon | No |
| AD, AP, AS, HP, haste, resistances, penetration, movement speed, crit, tenacity, or omnivamp | No |
| Stats-only new item | No |
| Flat magic on-hit | No |
| Flat + AP-scaling magic on-hit | No |
| Existing generic Spellblade formula | No |
| Existing damage or stasis active shape | No |
| Passive that does not affect champion damage | No; describe it in `passive_text` |
| A completely new stacking, trigger, transformation, execute, proc, or timing rule | Yes |
| A new active kind other than `damage` or `stasis` | Yes |
| A new mutually exclusive shop family | Yes, once, to register the new family |

The frontend item picker is automatic. Adding a valid catalog entry makes it
selectable without editing HTML or JavaScript.

## Required fields

```python
"readable_snake_case_key": {
    "id": 1234,
    "name": "Displayed Item Name",
    "cost": 3000,
    "stats": {},
    "tags": [],
    "passive_text": "Text displayed in the calculator.",
},
```

Use a unique positive Riot item ID. The key is internal and should remain
stable even if Riot changes the displayed name.

## Supported stat names

```python
"stats": {
    "ad": 50,
    "ap": 80,
    "attack_speed": 25,
    "ability_haste": 20,
    "ultimate_haste": 30,
    "health": 350,
    "armor": 50,
    "mr": 45,
    "magic_pen_flat": 15,
    "magic_pen_pct": 0.30,
    "armor_pen_pct": 0.35,
    "move_speed_flat": 45,
    "move_speed_pct": 4,
    "crit_chance": 25,
    "crit_damage_bonus": 30,
    "tenacity": 20,
    "omnivamp": 0.10,
},
```

Percentage conventions:

```text
attack_speed: 25    = 25% attack speed
crit_chance: 25     = 25% critical strike chance
move_speed_pct: 4   = 4% movement speed

magic_pen_pct: 0.30 = 30% magic penetration
omnivamp: 0.10      = 10% omnivamp
ap_ratio: 0.15      = 15% AP scaling
```

The server validates these names at startup. A typo such as `attackspeed` now
produces a readable error instead of silently contributing zero.

## Copy/paste templates

### Stats-only item

```python
"new_item": {
    "id": 1234,
    "name": "New Item",
    "cost": 3000,
    "stats": {"ad": 50, "attack_speed": 25, "crit_chance": 25},
    "tags": [],
    "passive_text": "Its non-damage passive is shown but not simulated.",
},
```

### Flat magic on-hit

```python
"new_onhit_item": {
    "id": 1234,
    "name": "New On-hit Item",
    "cost": 3000,
    "stats": {"attack_speed": 40},
    "tags": [],
    "passive_text": "Attacks deal 45 bonus magic damage on-hit.",
    "onhit_magic_flat": 45.0,
},
```

### Flat plus AP-scaling magic on-hit

```python
"new_scaling_onhit_item": {
    "id": 1234,
    "name": "New Scaling On-hit Item",
    "cost": 3000,
    "stats": {"ap": 80, "attack_speed": 50},
    "tags": [],
    "passive_text": "Attacks deal 15 (+15% AP) bonus magic damage.",
    "onhit_magic": {"flat": 15.0, "ap_ratio": 0.15},
},
```

### Generic Spellblade

`spellblade` must also appear in `tags`. Only one Spellblade item can be used
in a build.

```python
"new_spellblade": {
    "id": 1234,
    "name": "New Spellblade",
    "cost": 3000,
    "stats": {"ap": 80, "ability_haste": 15},
    "tags": ["spellblade"],
    "passive_text": "After an ability, the next attack deals bonus magic damage.",
    "spellblade": {
        "base_ad_ratio": 0.75,
        "ap_ratio": 0.40,
        "damage_type": "magic",
        "repeats_onhits": False,
    },
},
```

### Generic damage active

```python
"new_active_item": {
    "id": 1234,
    "name": "New Active Item",
    "cost": 3000,
    "stats": {"ap": 80},
    "tags": ["active"],
    "passive_text": "Active: deal level-scaled magic damage.",
    "active": {
        "kind": "damage",
        "base_lo": 100.0,
        "base_hi": 200.0,
        "ap_ratio": 0.30,
        "cooldown": 60,
    },
},
```

## Tags and shop restrictions

- `boots`: limited to one Boots item.
- `starter`: limited to one Starter item.
- `spellblade`: limited to one Spellblade item and enables the generic proc.
- `blight`: limited to one Blight item.
- `fatality`: limited to one Fatality item.
- `mid_role_quest`: activates the mid-role reward and enforces the role-quest
  level restriction.
- `active`: descriptive; the `active` object makes the button appear.

```text
mid-role bonus AD/AP multiplier = 1.08
evolved mid-role boots are illegal at levels 19..20
```

Other tags identify custom mechanics already implemented in `engine.py`.

## When a new mechanic needs engine work

Do not put formulas into `passive_text`; that text is display-only. For a new
mechanic:

- Add a clearly named effect object, such as `"new_passive": {...}`.
- Register it in `CUSTOM_EFFECT_FIELDS`.
- Initialize stacks, cooldowns, durations, and ready state in `engine.py`.
- Call it from its real attack, cast, damage, or timeline trigger.
- Send damage through `_deal(...)`; do not round inside the mechanic.
- Add a focused test and, when possible, a Practice Tool record.

Searching `engine.py` for an existing effect field such as `bring_it_down`,
`spelldance`, or `opening_barrage` shows complete examples.

## Icons

The preferred local icon path is:

```text
frontend/icons/<item-id>.png
```

If that PNG is missing, the UI automatically requests the item ID from the
CommunityDragon fallback. Therefore an icon file is helpful but not required
for a manually added item to work.

## Verification

From the project directory, run:

```text
python -B -m unittest discover -s tests -v
```

Then restart the calculator server and confirm the item appears in the picker.

If the mechanic is source-confirmed but not yet Practice Tool-confirmed, label
it that way in `VALIDATION.md`; do not imply that automated agreement with the
implementation is independent gameplay evidence.
