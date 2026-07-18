# API guide

This document describes the public HTTP interface used by the hosted Kayle
Damage Simulator. It covers catalog discovery, readable identifiers, request
validation, construction of a simulation payload, and the response timeline.

## Base URL and format

```text
https://kayle-calculator.onrender.com
```

The API does not require authentication. Responses are JSON. Simulation
requests must use an uncompressed JSON body:

```http
Content-Type: application/json
Content-Encoding: identity
```

Normal HTTP libraries add `Content-Length` automatically. Browser requests
from another website require CORS permission; the hosted server currently
supports same-origin UI requests and direct/server-side HTTP clients, but does
not advertise cross-origin browser access.

## Public identifiers

Items, rune paths, runes, and shards use readable string keys in request
payloads:

```json
{
  "item": "nashors_tooth",
  "primary_path": "precision",
  "rune": "fleet_footwork",
  "shard": "attack_speed"
}
```

Catalog responses also contain Riot numeric `id` fields for icons and source
tracking. Numeric IDs are metadata and are not accepted in `POST /api/simulate`.
Use each catalog object's `key` field when building a request.

## Endpoints

| Method and route | Purpose |
|---|---|
| `GET /healthz` | Lightweight service-health response. |
| `GET /api/bootstrap` | Items, runes, presets, champion data, and one target in a single response. |
| `GET /api/champion` | Kayle base stats and default ability ranks for a level. |
| `GET /api/items` | Current selectable item catalog and item keys. |
| `GET /api/runes` | Rune paths, rune keys, shards, icons, and implementation status. |
| `GET /api/enemy_presets` | Available target-preset keys. |
| `GET /api/enemy_preset` | One target preset scaled to a level. |
| `POST /api/simulate` | Validate and simulate one or more builds. |

## Health

Request:

```http
GET /healthz
```

Response:

```json
{
  "status": "ok"
}
```

## Catalog discovery

### Bootstrap

```http
GET /api/bootstrap?level=18&preset=dummy
```

The response combines the data normally obtained from the item, rune,
champion, enemy-preset, and selected-enemy endpoints:

```json
{
  "items": [],
  "runes": {
    "paths": [],
    "shards": []
  },
  "enemy_presets": [],
  "champion": {
    "stats": {},
    "default_ranks": {
      "Q": 5,
      "W": 5,
      "E": 5,
      "R": 3
    }
  },
  "enemy": {}
}
```

Query values:

```text
level  = 1..20; invalid GET values are clamped or replaced by the default
preset = a key returned by GET /api/enemy_presets
```

### Champion

```http
GET /api/champion?level=6
```

```json
{
  "stats": {
    "level": 6,
    "base_ad": 59.875,
    "base_as": 0.625,
    "as_ratio": 0.667
  },
  "default_ranks": {
    "Q": 3,
    "W": 1,
    "E": 1,
    "R": 1
  }
}
```

The actual `stats` object contains the complete champion stat response, not
only the abbreviated fields shown above.

### Items

```http
GET /api/items
```

Each entry has this shape:

```json
{
  "key": "berserkers_greaves",
  "id": 3006,
  "name": "Berserker's Greaves",
  "cost": 1100,
  "stats": {
    "attack_speed": 25,
    "move_speed_flat": 45
  },
  "tags": ["boots"],
  "passive_text": "...",
  "icon": "icons/3006.png?v=...",
  "icon_fallback": "https://...",
  "has_active": false,
  "active_kind": null
}
```

Submit the `key`, never the numeric `id`. Active items expose
`has_active: true`; their key may also be used in an `ITEM_ACTIVE` action.

### Runes and shards

```http
GET /api/runes
```

Abbreviated response:

```json
{
  "paths": [
    {
      "key": "precision",
      "id": 8000,
      "name": "Precision",
      "icon": "icons/runes/path_8000.png?v=...",
      "slots": [
        [
          {
            "key": "fleet_footwork",
            "id": 8021,
            "name": "Fleet Footwork",
            "dmg": true,
            "note": "...",
            "icon": "icons/runes/8021.png?v=...",
            "has_math": true
          }
        ]
      ]
    }
  ],
  "shards": [
    {
      "name": "Offense",
      "options": [
        {
          "key": "attack_speed",
          "name": "Attack Speed",
          "text": "10% bonus attack speed",
          "combat": true,
          "icon": "icons/runes/StatModsAttackSpeedIcon.png?v=..."
        }
      ]
    }
  ]
}
```

Rune path keys are:

```text
precision
domination
sorcery
resolve
inspiration
```

`has_math` tells an API client whether the rune currently changes the combat
calculation. Visual-only runes may still be submitted and echoed, but do not
change the result.

### Enemy presets

```http
GET /api/enemy_presets
GET /api/enemy_preset?preset=average&level=18
```

Preset keys are obtained from the catalog rather than hard-coded. The second
endpoint returns a target object suitable for the `enemy` field of a
simulation request.

## Build a simulation payload

All builds in one request share champion level, ability ranks, enemy, combo,
and scenario options. Each build supplies its own items and rune page.

Complete example:

```json
{
  "level": 6,
  "ability_ranks": {
    "Q": 3,
    "W": 1,
    "E": 1,
    "R": 1
  },
  "enemy": {
    "hp": 1000,
    "current_hp": 1000,
    "bonus_hp": 0,
    "armor": 30,
    "mr": 30
  },
  "builds": [
    {
      "name": "Nashor Berserker",
      "items": [
        "nashors_tooth",
        "berserkers_greaves"
      ],
      "runes": {
        "primary": "precision",
        "secondary": "sorcery",
        "selected": [
          "fleet_footwork",
          "legend_alacrity"
        ],
        "shards": [
          "attack_speed",
          "adaptive",
          "health"
        ]
      }
    }
  ],
  "combo": [
    { "type": "AA" },
    { "type": "AA" },
    { "type": "AA" },
    { "type": "AA" },
    { "type": "AA" },
    { "type": "AA" }
  ],
  "options": {
    "game_time_min": 25,
    "kayle_hp_pct": 100,
    "dh_souls": 0,
    "dark_seal_stacks": 0,
    "legend_stacks": 0,
    "relentless_stacks": 0,
    "pre_stacked_zeal": false,
    "pre_stacked_rageblade": false,
    "pre_stacked_yun_tal": true,
    "fleet_starts_energized": true,
    "assume_river": false
  }
}
```

### Top-level fields

| Field | Meaning |
|---|---|
| `level` | Kayle's champion level. |
| `ability_ranks` | Explicit Q/W/E/R ranks. Omit to use the documented default skill order. |
| `enemy` | Maximum HP, starting HP, bonus HP, armor, and magic resistance. |
| `builds` | Builds compared under the shared scenario. |
| `combo` | Ordered actions executed for every build. |
| `options` | Shared pre-combat and scenario state. |

Every top-level section is syntactically optional:

```text
level             = 18 when omitted
ability_ranks     = Kayle's default skill order when omitted
builds            = [] when omitted
combo             = [] when omitted
enemy and options = defaults documented below
```

Empty builds or combo arrays produce an empty comparison rather than a useful
combat result. If `ability_ranks` is present but a specific ability is absent,
that ability receives rank zero.

Validation ranges:

```text
level                       = 1..20
Q / W / E rank              = 0..5
R rank                      = 0..3
enemy maximum HP            = 1..10,000,000
enemy current HP            = 0..maximum HP
enemy bonus HP              = 0..10,000,000
enemy armor / MR            = -10,000..100,000
builds                      <= 8
items per build             <= 6
selected runes per build    <= 6
shards per build            <= 3
combo actions               <= 100
build name                  <= 60 characters
```

All numeric values must be finite. Ability ranks are bounds-checked but may be
set manually for isolation tests even when the rank distribution would be
illegal in a normal match.

### Enemy fields

```json
{
  "hp": 3500,
  "current_hp": 2100,
  "bonus_hp": 1500,
  "armor": 100,
  "mr": 100
}
```

The HP fields are intentionally separate:

- `hp` is maximum HP and controls percentage thresholds.
- `current_hp` is starting HP and controls missing-health effects.
- `bonus_hp` is target bonus HP and is read by effects such as Giant Slayer.

When omitted, the enemy defaults are:

```text
hp         = 3500
current_hp = hp
bonus_hp   = 0
armor      = 100
mr         = 100
```

### Build fields

```json
{
  "name": "AP build",
  "items": ["nashors_tooth", "rabadons_deathcap"],
  "runes": {
    "primary": "precision",
    "secondary": "sorcery",
    "selected": ["fleet_footwork", "legend_alacrity"],
    "shards": ["attack_speed", "adaptive", "health"]
  }
}
```

Do not send empty item slots as `null`; omit them from the array. Item and rune
keys are case-sensitive. `primary` and `secondary` document the page layout;
`selected` determines which rune effects enter the simulation.

`name`, `items`, and `runes` are individually optional. Their defaults are the
generated build name, an empty item array, and an empty rune selection. Rune
paths are optional metadata, while selected rune and shard arrays default to
empty arrays.

### Combo actions

Basic attacks and abilities:

```json
[
  { "type": "AA" },
  { "type": "Q" },
  { "type": "W" },
  { "type": "E" },
  { "type": "R" }
]
```

Wait:

```json
{ "type": "WAIT", "duration": 0.5 }
```

```text
WAIT duration = 0..60 seconds
default        = 0.1 seconds
```

Item active:

```json
{ "type": "ITEM_ACTIVE", "item": "hextech_gunblade" }
```

The referenced item must exist in the same build and expose
`has_active: true` in the item catalog. E uses one unified instant action; old
`fast`, `waited`, or `delayed` timing variants are rejected.

Cooldown-invalid actions still execute and add warnings. Automatically
scheduled damage such as R impact, Stormsurge, Comet, burns, and Phantom Hit is
resolved after the entered sequence without requiring a trailing wait.

### Options

Omitted options use engine defaults:

```text
game_time_min            = 25
kayle_hp_pct             = 100
dh_souls                 = 0
dark_seal_stacks         = 0
legend_stacks            = 10
relentless_stacks        = 0
pre_stacked_zeal         = true
pre_stacked_rageblade    = false
pre_stacked_yun_tal      = true
fleet_starts_energized   = true
assume_river             = false
```

Accepted ranges:

```text
game_time_min      = 0..1000
kayle_hp_pct       = 0..100
dh_souls           = 0..10,000 whole souls
dark_seal_stacks   = 0..10 whole stacks
legend_stacks      = 0..10 whole stacks
relentless_stacks  = 0..5 whole stacks
```

Boolean options must be JSON booleans, not strings or numbers.

## Send the request

`curl` example:

```bash
curl -X POST "https://kayle-calculator.onrender.com/api/simulate" \
  -H "Content-Type: application/json" \
  --data-binary @payload.json
```

JavaScript example for same-origin use:

```js
const response = await fetch("/api/simulate", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(payload),
});

const data = await response.json();
if (!response.ok) throw new Error(data.error);
```

Python standard-library example:

```python
import json
from urllib.request import Request, urlopen

body = json.dumps(payload).encode("utf-8")
request = Request(
    "https://kayle-calculator.onrender.com/api/simulate",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)

with urlopen(request) as response:
    result = json.load(response)
```

## Simulation response

The top-level object contains one result for each submitted build:

```json
{
  "results": [
    {
      "build_name": "Nashor Berserker",
      "items": ["nashors_tooth", "berserkers_greaves"],
      "runes": {
        "primary": "precision",
        "secondary": "sorcery",
        "selected": ["fleet_footwork", "legend_alacrity"],
        "shards": ["attack_speed", "adaptive", "health"]
      },
      "total_damage": 558.58,
      "dps": 153.0,
      "duration": 3.652,
      "timeline_duration": 4.341,
      "burst_damage_1s": 186.19,
      "burst_window_1s": {
        "start": 0.0,
        "end": 1.0
      },
      "damage_window": {
        "start": 0.0,
        "end": 3.652
      },
      "totals": {
        "physical": 276.35,
        "magic": 282.23,
        "true": 0.0
      },
      "stats": {},
      "enemy": {},
      "events": [],
      "warnings": []
    }
  ]
}
```

The numeric example is abbreviated and rounded like the API response. Use the
live response rather than copying it as a future regression fixture.

Important result fields:

| Field | Meaning |
|---|---|
| `total_damage` | Sum of all full-precision applied damage instances. |
| `totals` | Applied damage separated into physical, magic, and true damage. |
| `dps` | Practice Tool-style first-to-last damage DPS. |
| `duration` | DPS denominator; a single-timestamp combo uses the documented single-hit fallback. |
| `timeline_duration` | Full action timeline including final recovery, retained for auditing. |
| `burst_damage_1s` | Highest damage in any rolling one-second window. |
| `burst_window_1s` | Winning burst-window timestamps. |
| `damage_window` | First and last damage timestamps. |
| `stats` | Final calculated build stats and penetration values. |
| `enemy` | Maximum HP, bonus HP, remaining HP, and killed state. |
| `events` | Auditable execution-order timeline. |
| `warnings` | Cooldown conflicts, illegal item combinations, and unsupported rune math. |

Damage events expose each calculation stage:

```json
{
  "t": 0.0,
  "source": "Basic attack",
  "type": "physical",
  "raw": 59.875,
  "multiplier": 1.0,
  "pre": 59.875,
  "effective_resistance": 30.0,
  "mitigation_multiplier": 0.769231,
  "dealt": 46.0577,
  "hp_before": 1000.0,
  "hp_after": 953.9423
}
```

Timeline notes omit damage-stage fields and use `type: "note"`. Healing events
use `type: "heal"`.

The DPS and burst formulas are specified in the
[README core calculations](../README.md#core-calculations). Combat ordering and
snapshot rules are specified in the [simulation model](MODEL.md).

## Errors and public limits

Errors use one safe JSON shape:

```json
{
  "error": "human-readable validation message"
}
```

| Status | Meaning |
|---|---|
| `400` | Invalid JSON content or validated field value. |
| `411` | Missing or invalid `Content-Length`. |
| `413` | Request body exceeds the public limit. |
| `415` | Wrong content type or compressed request body. |
| `429` | Per-client rate limit or process concurrency limit reached. |
| `500` | Unexpected simulation failure; response includes a short reference. |

Public resource limits:

```text
request body                   <= 256 KiB
simulations                    <= 30 per client per minute
concurrent simulations         = 2 by default
configurable concurrency       = 1..4
builds                         <= 8
items per build                <= 6
combo actions                  <= 100
```

When a temporary limit is reached, respect the `Retry-After` response header.

## Compatibility notes

- The API is currently unversioned and follows the deployed simulator model.
- Catalog keys are the source of truth for payload identifiers.
- Numeric Riot rune IDs were replaced by readable keys in public payloads.
- Existing direct engine tests may still use numeric IDs internally; that is
  not part of the HTTP contract.
- The service can sleep on its hosting tier, so the first request after an idle
  period may take longer.
