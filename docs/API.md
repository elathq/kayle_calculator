# API guide

Use the hosted API at:

```text
https://kayle-calculator.web.app
```

`POST /api/simulate` requires:

```http
Content-Type: application/json
```

Items, rune paths, runes, shards, presets, and active items are submitted with
the string keys shown in the tables below. Numeric Riot IDs returned by catalog
endpoints are metadata only.

## Key tables

### Items

Use the value from the `key` column inside `builds[].items`.

| Key | Item | Active action |
|---|---|---|
| `boots` | Boots | — |
| `boots_of_swiftness` | Boots of Swiftness | — |
| `berserkers_greaves` | Berserker's Greaves | — |
| `gunmetal_greaves` | Gunmetal Greaves | — |
| `dorans_ring` | Doran's Ring | — |
| `dorans_bow` | Doran's Bow | — |
| `dorans_blade` | Doran's Blade | — |
| `dark_seal` | Dark Seal | — |
| `swiftmarch` | Swiftmarch | — |
| `spellslingers_shoes` | Spellslinger's Shoes | — |
| `sorcerers_shoes` | Sorcerer's Shoes | — |
| `dusk_and_dawn` | Dusk and Dawn | — |
| `guinsoos_rageblade` | Guinsoo's Rageblade | — |
| `lich_bane` | Lich Bane | — |
| `rylais_crystal_scepter` | Rylai's Crystal Scepter | — |
| `shadowflame` | Shadowflame | — |
| `zhonyas_hourglass` | Zhonya's Hourglass | `ITEM_ACTIVE` |
| `banshees_veil` | Banshee's Veil | — |
| `rabadons_deathcap` | Rabadon's Deathcap | — |
| `cryptbloom` | Cryptbloom | — |
| `void_staff` | Void Staff | — |
| `hextech_gunblade` | Hextech Gunblade | `ITEM_ACTIVE` |
| `nashors_tooth` | Nashor's Tooth | — |
| `cosmic_drive` | Cosmic Drive | — |
| `stormsurge` | Stormsurge | — |
| `riftmaker` | Riftmaker | — |
| `kraken_slayer` | Kraken Slayer | — |
| `terminus` | Terminus | — |
| `infinity_edge` | Infinity Edge | — |
| `bloodletters_curse` | Bloodletter's Curse | — |
| `hexoptics_c44` | Hexoptics C44 | — |
| `phantom_dancer` | Phantom Dancer | — |
| `rapid_firecannon` | Rapid Firecannon | — |
| `experimental_hexplate` | Experimental Hexplate | — |
| `essence_reaver` | Essence Reaver | — |
| `yun_tal_wildarrows` | Yun Tal Wildarrows | — |
| `navori_flickerblade` | Navori Flickerblade | — |
| `lord_dominiks_regards` | Lord Dominik's Regards | — |
| `wits_end` | Wit's End | — |
| `statikk_shiv` | Statikk Shiv | — |
| `stormrazor` | Stormrazor | — |
| `fiendhunter_bolts` | Fiendhunter Bolts | — |

The live source of truth is `GET /api/items`.

### Rune paths

Use these values in `builds[].runes.primary` and
`builds[].runes.secondary`.

| Key | Path |
|---|---|
| `precision` | Precision |
| `domination` | Domination |
| `sorcery` | Sorcery |
| `resolve` | Resolve |
| `inspiration` | Inspiration |

### Runes

Use rune keys inside `builds[].runes.selected`. `Yes` in the Simulated column
means the rune currently changes the combat result. Other runes are accepted
and returned but are visual selections only.

| Path | Key | Rune | Simulated |
|---|---|---|---|
| Precision | `press_the_attack` | Press the Attack | Yes |
| Precision | `lethal_tempo` | Lethal Tempo | Yes |
| Precision | `fleet_footwork` | Fleet Footwork | Yes |
| Precision | `conqueror` | Conqueror | Yes |
| Precision | `absorb_life` | Absorb Life | No |
| Precision | `triumph` | Triumph | No |
| Precision | `presence_of_mind` | Presence of Mind | No |
| Precision | `legend_alacrity` | Legend: Alacrity | Yes |
| Precision | `legend_haste` | Legend: Haste | Yes |
| Precision | `legend_bloodline` | Legend: Bloodline | No |
| Precision | `coup_de_grace` | Coup de Grace | Yes |
| Precision | `cut_down` | Cut Down | Yes |
| Precision | `last_stand` | Last Stand | Yes |
| Domination | `electrocute` | Electrocute | Yes |
| Domination | `dark_harvest` | Dark Harvest | Yes |
| Domination | `hail_of_blades` | Hail of Blades | Yes |
| Domination | `cheap_shot` | Cheap Shot | Yes |
| Domination | `taste_of_blood` | Taste of Blood | No |
| Domination | `sudden_impact` | Sudden Impact | No |
| Domination | `sixth_sense` | Sixth Sense | No |
| Domination | `grisly_mementos` | Grisly Mementos | No |
| Domination | `deep_ward` | Deep Ward | No |
| Domination | `treasure_hunter` | Treasure Hunter | No |
| Domination | `relentless_hunter` | Relentless Hunter | Yes |
| Domination | `ultimate_hunter` | Ultimate Hunter | No |
| Sorcery | `summon_aery` | Summon Aery | Yes |
| Sorcery | `arcane_comet` | Arcane Comet | Yes |
| Sorcery | `stormraiders_surge` | Stormraider's Surge | Yes |
| Sorcery | `deathfire_touch` | Deathfire Touch | Yes |
| Sorcery | `axiom_arcanist` | Axiom Arcanist | Yes |
| Sorcery | `manaflow_band` | Manaflow Band | No |
| Sorcery | `nimbus_cloak` | Nimbus Cloak | No |
| Sorcery | `transcendence` | Transcendence | Yes |
| Sorcery | `celerity` | Celerity | Yes |
| Sorcery | `absolute_focus` | Absolute Focus | Yes |
| Sorcery | `scorch` | Scorch | Yes |
| Sorcery | `waterwalking` | Waterwalking | Yes |
| Sorcery | `gathering_storm` | Gathering Storm | Yes |
| Resolve | `grasp_of_the_undying` | Grasp of the Undying | Yes |
| Resolve | `aftershock` | Aftershock | No |
| Resolve | `guardian` | Guardian | No |
| Resolve | `demolish` | Demolish | No |
| Resolve | `font_of_life` | Font of Life | No |
| Resolve | `shield_bash` | Shield Bash | No |
| Resolve | `conditioning` | Conditioning | No |
| Resolve | `second_wind` | Second Wind | No |
| Resolve | `bone_plating` | Bone Plating | No |
| Resolve | `overgrowth` | Overgrowth | No |
| Resolve | `revitalize` | Revitalize | No |
| Resolve | `unflinching` | Unflinching | No |
| Inspiration | `glacial_augment` | Glacial Augment | No |
| Inspiration | `unsealed_spellbook` | Unsealed Spellbook | No |
| Inspiration | `first_strike` | First Strike | Yes |
| Inspiration | `hextech_flashtraption` | Hextech Flashtraption | No |
| Inspiration | `magical_footwear` | Magical Footwear | Yes |
| Inspiration | `cash_back` | Cash Back | No |
| Inspiration | `triple_tonic` | Triple Tonic | No |
| Inspiration | `time_warp_tonic` | Time Warp Tonic | No |
| Inspiration | `biscuit_delivery` | Biscuit Delivery | No |
| Inspiration | `cosmic_insight` | Cosmic Insight | No |
| Inspiration | `approach_velocity` | Approach Velocity | Yes |
| Inspiration | `jack_of_all_trades` | Jack of All Trades | Yes |

The live source of truth is `GET /api/runes`.

### Stat shards

Select one key from each row and keep them in row order.

| Row | Key | Shard | Simulated |
|---|---|---|---|
| Offense | `adaptive` | Adaptive Force | Yes |
| Offense | `attack_speed` | Attack Speed | Yes |
| Offense | `haste` | Ability Haste | Yes |
| Flex | `adaptive` | Adaptive Force | Yes |
| Flex | `move_speed` | Movement Speed | Yes |
| Flex | `health_scaling` | Scaling Health | Yes |
| Defense | `health` | Health | Yes |
| Defense | `tenacity` | Tenacity and Slow Resist | No |
| Defense | `health_scaling` | Scaling Health | Yes |

### Enemy presets

| Key | Preset |
|---|---|
| `dummy` | Target Dummy |
| `squishy` | Squishy average: Marksman and Mage |
| `average` | All-champion average |
| `tank` | Tank and Fighter average |

Use preset keys with `GET /api/enemy_preset`. A POST payload sends the returned
enemy numbers, not the preset key itself.

### Combo actions

| Action | Payload object |
|---|---|
| Basic attack | `{ "type": "AA" }` |
| Q | `{ "type": "Q" }` |
| W | `{ "type": "W" }` |
| E | `{ "type": "E" }` |
| R | `{ "type": "R" }` |
| Wait | `{ "type": "WAIT", "duration": 0.5 }` |
| Item active | `{ "type": "ITEM_ACTIVE", "item": "hextech_gunblade" }` |

The wait duration is measured in seconds. Use only the unified E action. Active
item keys must come from the Active action column in the item table.

## GET structure

### Endpoint summary

| Request | Response |
|---|---|
| `GET /healthz` | Service status object |
| `GET /api/items` | Array of item objects |
| `GET /api/runes` | Rune paths and shard rows |
| `GET /api/champion?level=18` | Kayle stats and default ability ranks |
| `GET /api/enemy_presets` | Array of preset descriptions |
| `GET /api/enemy_preset?preset=average&level=18` | One calculated enemy object |
| `GET /api/bootstrap?level=18&preset=dummy` | All initial UI catalogs and setup data |

### `GET /healthz`

```json
{
  "status": "ok"
}
```

### `GET /api/items`

```json
[
  {
    "key": "nashors_tooth",
    "id": 3115,
    "name": "Nashor's Tooth",
    "cost": 2900,
    "stats": {},
    "tags": [],
    "passive_text": "...",
    "icon": "icons/3115.png?v=...",
    "icon_fallback": "https://...",
    "has_active": false,
    "active_kind": null
  }
]
```

### `GET /api/runes`

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

### `GET /api/champion`

```json
{
  "stats": {
    "level": 18,
    "hp": 2234.0,
    "mana": 1180.0,
    "base_ad": 92.5,
    "armor": 97.4,
    "mr": 44.1,
    "level_bonus_as": 25.5,
    "base_as": 0.625,
    "as_ratio": 0.667,
    "windup_percent": 0.19355
  },
  "default_ranks": {
    "Q": 5,
    "W": 5,
    "E": 5,
    "R": 3
  }
}
```

### `GET /api/enemy_presets`

```json
[
  {
    "key": "average",
    "name": "All-champion average",
    "scaling": true
  }
]
```

### `GET /api/enemy_preset`

```json
{
  "hp": 2383.9,
  "bonus_hp": 0.0,
  "armor": 106.8,
  "mr": 59.3,
  "name": "All-champion average"
}
```

### `GET /api/bootstrap`

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
    "default_ranks": {}
  },
  "enemy": {}
}
```

## Build the POST payload

The payload has six top-level fields:

| Field | Value |
|---|---|
| `level` | Kayle level |
| `ability_ranks` | Q, W, E, and R ranks |
| `enemy` | Target HP and resistances |
| `builds` | Item and rune setups to compare |
| `combo` | Ordered actions from the action table |
| `options` | Shared scenario state |

### Enemy structure

```json
{
  "hp": 1000,
  "current_hp": 1000,
  "bonus_hp": 0,
  "armor": 30,
  "mr": 30
}
```

| Field | Meaning |
|---|---|
| `hp` | Maximum HP used for percentage thresholds |
| `current_hp` | Starting HP used for missing-health effects |
| `bonus_hp` | Target bonus HP used by effects such as Giant Slayer |
| `armor` | Target armor |
| `mr` | Target magic resistance |

### Build structure

Use item, rune-path, rune, and shard keys from the tables above.

```json
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
```

Empty item slots are omitted instead of being sent as `null`. Numeric item and
rune IDs are rejected.

### Options

| Key | Default | Accepted value |
|---|---:|---|
| `game_time_min` | `25` | `0..1000` |
| `kayle_hp_pct` | `100` | `0..100` |
| `dh_souls` | `0` | Whole number from `0..10000` |
| `dark_seal_stacks` | `0` | Whole number from `0..10` |
| `legend_stacks` | `10` | Whole number from `0..10` |
| `relentless_stacks` | `0` | Whole number from `0..5` |
| `pre_stacked_zeal` | `true` | Boolean |
| `pre_stacked_rageblade` | `false` | Boolean |
| `pre_stacked_yun_tal` | `true` | Boolean |
| `fleet_starts_energized` | `true` | Boolean |
| `assume_river` | `false` | Boolean |

### Complete payload

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

Send it to:

```http
POST /api/simulate
Content-Type: application/json
```

## POST response structure

```json
{
  "results": [
    {
      "build_name": "Nashor Berserker",
      "items": ["nashors_tooth", "berserkers_greaves"],
      "runes": {},
      "stats": {},
      "ranks": {},
      "calculation_model": "full_precision_v1",
      "critical_strike_model": "expected_damage",
      "totals": {
        "physical": 0,
        "magic": 0,
        "true": 0
      },
      "total_damage": 0,
      "pre_mitigation_total": 0,
      "mitigated_pct": 0,
      "duration": 0,
      "timeline_duration": 0,
      "damage_window": {
        "start": 0,
        "end": 0
      },
      "dps": 0,
      "burst_damage_1s": 0,
      "burst_window_1s": {
        "start": 0,
        "end": 1
      },
      "attack_count": 0,
      "kill_time": null,
      "gold_cost": 0,
      "damage_per_1k_gold": null,
      "healing": 0,
      "enemy": {},
      "events": [],
      "warnings": []
    }
  ]
}
```

One result is returned for every submitted build. `events` contains the
auditable damage timeline, including non-damage notes such as the R cast and
its scheduled impact time. `duration` is the Practice Tool damage window;
`timeline_duration` includes later queued effects such as Divine Judgment.
The damage, DPS, and burst formulas are in the
[README](../README.md#core-calculations).

## Limits and errors

```text
builds                      <= 8
items per build             <= 6
selected runes per build    <= 6
shards per build            <= 3
combo actions               <= 100
one WAIT                    <= 60 seconds
request body                <= 256 KiB
requests                    <= 30 simulations per client per minute
```

Errors return:

```json
{
  "error": "validation message"
}
```

The live catalog endpoints are always the final source of truth if the tables
and a newer deployment differ.
