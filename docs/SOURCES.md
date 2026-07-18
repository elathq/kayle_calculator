# Data and icon sources

This is the external-source ledger. It records provenance and version pins; it
does not duplicate the formulas in the [Simulation model](MODEL.md).

```text
last review          = 2026-07-18
local Riot asset set = Data Dragon 16.14.1
League Wiki pages    = live and may change after review
```

Related records:

- [Simulation model](MODEL.md)
- [Validation and backtesting](VALIDATION.md)
- [Maintaining items](ITEM_MAINTENANCE.md)

## Provenance policy

Pinned values live in the Python data files. A live link is a reference, not an
automatic update feed. Source review, implementation, tests, and affected
Practice Tool cases must change together.

Source priority:

- Repeatable Practice Tool observation from the target patch.
- Current Riot patch notes or Riot-published data.
- Current League Wiki page and patch history.
- Explicit simulator assumption.

Timing-sensitive exceptions remain documented beside the source formula.

## Champion and combat references

| Data | Source |
|---|---|
| Kayle stats, passive, abilities, ranks, ratios, and timings | [Kayle — League Wiki](https://wiki.leagueoflegends.com/en-us/Kayle) |
| Per-level growth | [Champion statistic](https://wiki.leagueoflegends.com/en-us/Champion_statistic) |
| Attack-speed ratio, cap, windup, and timer | [Attack speed](https://wiki.leagueoflegends.com/en-us/Attack_speed), [Attack timer](https://wiki.leagueoflegends.com/en-us/Attack_timer) |
| Physical mitigation | [Armor](https://wiki.leagueoflegends.com/en-us/Armor) |
| Magic mitigation | [Magic resistance](https://wiki.leagueoflegends.com/en-us/Magic_resistance) |
| Reduction and penetration order | [Armor penetration](https://wiki.leagueoflegends.com/en-us/Armor_penetration), [Magic penetration](https://wiki.leagueoflegends.com/en-us/Magic_penetration) |
| Movement stacking and soft caps | [Movement speed](https://wiki.leagueoflegends.com/en-us/Movement_speed) |
| Adaptive conversion | [Adaptive force](https://wiki.leagueoflegends.com/en-us/Adaptive_force) |
| Haste conversion | [Ability haste](https://wiki.leagueoflegends.com/en-us/Ability_haste) |
| Enemy-preset base stats and class tags | [Riot Data Dragon champion catalog](https://ddragon.leagueoflegends.com/cdn/16.14.1/data/en_US/champion.json) |

Enemy presets use unweighted catalog averages and Riot's normal growth formula.
They contain no item stats.

```text
catalog champions = 173

Squishy average:
  filter = Marksman OR Mage
  champions = 96
  HP = 604.11 + 102.62 growth
  armor = 25.97 + 4.51 growth
  MR = 30.06 + 1.41 growth

All-champion average:
  champions = 173
  HP = 617.08 + 103.93 growth
  armor = 29.57 + 4.54 growth
  MR = 30.73 + 1.68 growth

Tank / Fighter average:
  filter = Tank OR Fighter
  champions = 80
  HP = 632.42 + 105.46 growth
  armor = 34.02 + 4.57 growth
  MR = 31.36 + 1.99 growth
```

Practice Tool evidence is in [Validation and backtesting](VALIDATION.md). The
baseline fixture is
[`validation/practice_tool_cases.json`](../validation/practice_tool_cases.json).

## Item references

| Simulator item | Wiki source |
|---|---|
| Boots | [Boots](https://wiki.leagueoflegends.com/en-us/Boots) |
| Boots of Swiftness | [Boots of Swiftness](https://wiki.leagueoflegends.com/en-us/Boots_of_Swiftness) |
| Berserker's Greaves | [Berserker's Greaves](https://wiki.leagueoflegends.com/en-us/Berserker%27s_Greaves) |
| Gunmetal Greaves | [Gunmetal Greaves](https://wiki.leagueoflegends.com/en-us/Gunmetal_Greaves) |
| Doran's Ring | [Doran's Ring](https://wiki.leagueoflegends.com/en-us/Doran%27s_Ring) |
| Doran's Bow | [Doran's Bow](https://wiki.leagueoflegends.com/en-us/Doran%27s_Bow) |
| Doran's Blade | [Doran's Blade](https://wiki.leagueoflegends.com/en-us/Doran%27s_Blade) |
| Dark Seal | [Dark Seal](https://wiki.leagueoflegends.com/en-us/Dark_Seal) |
| Swiftmarch | [Swiftmarch](https://wiki.leagueoflegends.com/en-us/Swiftmarch) |
| Spellslinger's Shoes | [Spellslinger's Shoes](https://wiki.leagueoflegends.com/en-us/Spellslinger%27s_Shoes) |
| Sorcerer's Shoes | [Sorcerer's Shoes](https://wiki.leagueoflegends.com/en-us/Sorcerer%27s_Shoes) |
| Dusk and Dawn | [Dusk and Dawn](https://wiki.leagueoflegends.com/en-us/Dusk_and_Dawn) |
| Guinsoo's Rageblade | [Guinsoo's Rageblade](https://wiki.leagueoflegends.com/en-us/Guinsoo%27s_Rageblade) |
| Lich Bane | [Lich Bane](https://wiki.leagueoflegends.com/en-us/Lich_Bane) |
| Rylai's Crystal Scepter | [Rylai's Crystal Scepter](https://wiki.leagueoflegends.com/en-us/Rylai%27s_Crystal_Scepter) |
| Shadowflame | [Shadowflame](https://wiki.leagueoflegends.com/en-us/Shadowflame) |
| Zhonya's Hourglass | [Zhonya's Hourglass](https://wiki.leagueoflegends.com/en-us/Zhonya%27s_Hourglass) |
| Banshee's Veil | [Banshee's Veil](https://wiki.leagueoflegends.com/en-us/Banshee%27s_Veil) |
| Rabadon's Deathcap | [Rabadon's Deathcap](https://wiki.leagueoflegends.com/en-us/Rabadon%27s_Deathcap) |
| Cryptbloom | [Cryptbloom](https://wiki.leagueoflegends.com/en-us/Cryptbloom) |
| Void Staff | [Void Staff](https://wiki.leagueoflegends.com/en-us/Void_Staff) |
| Hextech Gunblade | [Hextech Gunblade](https://wiki.leagueoflegends.com/en-us/Hextech_Gunblade) |
| Nashor's Tooth | [Nashor's Tooth](https://wiki.leagueoflegends.com/en-us/Nashor%27s_Tooth) |
| Cosmic Drive | [Cosmic Drive](https://wiki.leagueoflegends.com/en-us/Cosmic_Drive) |
| Stormsurge | [Stormsurge](https://wiki.leagueoflegends.com/en-us/Stormsurge) |
| Riftmaker | [Riftmaker](https://wiki.leagueoflegends.com/en-us/Riftmaker) |
| Kraken Slayer | [Kraken Slayer](https://wiki.leagueoflegends.com/en-us/Kraken_Slayer) |
| Terminus | [Terminus](https://wiki.leagueoflegends.com/en-us/Terminus) |
| Infinity Edge | [Infinity Edge](https://wiki.leagueoflegends.com/en-us/Infinity_Edge) |
| Bloodletter's Curse | [Bloodletter's Curse](https://wiki.leagueoflegends.com/en-us/Bloodletter%27s_Curse) |
| Hexoptics C44 | [Hexoptics C44](https://wiki.leagueoflegends.com/en-us/Hexoptics_C44) |
| Phantom Dancer | [Phantom Dancer](https://wiki.leagueoflegends.com/en-us/Phantom_Dancer) |
| Rapid Firecannon | [Rapid Firecannon](https://wiki.leagueoflegends.com/en-us/Rapid_Firecannon) |
| Experimental Hexplate | [Experimental Hexplate](https://wiki.leagueoflegends.com/en-us/Experimental_Hexplate) |
| Essence Reaver | [Essence Reaver](https://wiki.leagueoflegends.com/en-us/Essence_Reaver) |
| Yun Tal Wildarrows | [Yun Tal Wildarrows](https://wiki.leagueoflegends.com/en-us/Yun_Tal_Wildarrows) |
| Navori Flickerblade | [Navori Flickerblade](https://wiki.leagueoflegends.com/en-us/Navori_Flickerblade) |
| Lord Dominik's Regards | [Lord Dominik's Regards](https://wiki.leagueoflegends.com/en-us/Lord_Dominik%27s_Regards) |
| Wit's End | [Wit's End](https://wiki.leagueoflegends.com/en-us/Wit%27s_End) |
| Statikk Shiv | [Statikk Shiv](https://wiki.leagueoflegends.com/en-us/Statikk_Shiv) |
| Stormrazor | [Stormrazor](https://wiki.leagueoflegends.com/en-us/Stormrazor) |
| Fiendhunter Bolts | [Fiendhunter Bolts](https://wiki.leagueoflegends.com/en-us/Fiendhunter_Bolts) |

Relevant Riot change records:

- [Patch 26.9 notes](https://www.leagueoflegends.com/en-gb/news/game-updates/league-of-legends-patch-26-9-notes/)
- [Patch 26.11 notes](https://www.leagueoflegends.com/en-us/news/game-updates/league-of-legends-patch-26-11-notes/)
- [Patch 25.21 notes](https://www.leagueoflegends.com/en-us/news/game-updates/patch-25-21-notes/)

The linked notes support these unusual changes:

```text
patch 26.9:
  - Doran's Bow introduction
  - Dusk and Dawn healing addition
  - Statikk single Energized champion proc = 60 raw magic

patch 26.11:
  - mid-role bonus AD/AP = 8%
  - ranged Hexplate Overdrive = 35% AS / 14% MS

patch 25.21:
  - Doran's Blade omnivamp-style healing return
  - Doran's Ring sustain change
```

The live item page is authoritative when a later patch changed the release
value. Non-damage passives may appear in the UI while remaining outside the
[model scope](MODEL.md#assumptions-and-exclusions).

Catalog cross-check snapshot:

```text
review date        = 2026-07-17
Riot catalog       = Data Dragon 16.14.1
Bloodletter's Curse ID = 8010
Stormrazor ID          = 3097
Rapid Firecannon ID    = 3094
Experimental Hexplate ID = 3073
Essence Reaver ID      = 3508
Yun Tal Wildarrows ID  = 3032
Navori Flickerblade ID = 6675
```

Data Dragon supplied standard names, IDs, prices, stats, and icons. Wiki pages
supplied detailed formulas and trigger classification.

## Rune references

Rune names, slots, IDs, and icon paths are matched against Riot's
[`runesReforged.json`](https://ddragon.leagueoflegends.com/cdn/16.14.1/data/en_US/runesReforged.json).
The general reference is the [Rune page](https://wiki.leagueoflegends.com/en-us/Rune).

| Path | Formula sources |
|---|---|
| Precision | [Press the Attack](https://wiki.leagueoflegends.com/en-us/Press_the_Attack), [Lethal Tempo](https://wiki.leagueoflegends.com/en-us/Lethal_Tempo), [Fleet Footwork](https://wiki.leagueoflegends.com/en-us/Fleet_Footwork), [Conqueror](https://wiki.leagueoflegends.com/en-us/Conqueror), [Legend: Alacrity](https://wiki.leagueoflegends.com/en-us/Legend:_Alacrity), [Legend: Haste](https://wiki.leagueoflegends.com/en-us/Legend:_Haste), [Coup de Grace](https://wiki.leagueoflegends.com/en-us/Coup_de_Grace), [Cut Down](https://wiki.leagueoflegends.com/en-us/Cut_Down), [Last Stand](https://wiki.leagueoflegends.com/en-us/Last_Stand) |
| Domination | [Electrocute](https://wiki.leagueoflegends.com/en-us/Electrocute), [Dark Harvest](https://wiki.leagueoflegends.com/en-us/Dark_Harvest), [Hail of Blades](https://wiki.leagueoflegends.com/en-us/Hail_of_Blades), [Cheap Shot](https://wiki.leagueoflegends.com/en-us/Cheap_Shot), [Relentless Hunter](https://wiki.leagueoflegends.com/en-us/Relentless_Hunter) |
| Sorcery | [Summon Aery](https://wiki.leagueoflegends.com/en-us/Summon_Aery), [Arcane Comet](https://wiki.leagueoflegends.com/en-us/Arcane_Comet), [Stormraider's Surge](https://wiki.leagueoflegends.com/en-us/Stormraider%27s_Surge), [Deathfire Touch](https://wiki.leagueoflegends.com/en-us/Deathfire_Touch), [Axiom Arcanist](https://wiki.leagueoflegends.com/en-us/Axiom_Arcanist), [Transcendence](https://wiki.leagueoflegends.com/en-us/Transcendence), [Celerity](https://wiki.leagueoflegends.com/en-us/Celerity), [Absolute Focus](https://wiki.leagueoflegends.com/en-us/Absolute_Focus), [Scorch](https://wiki.leagueoflegends.com/en-us/Scorch), [Waterwalking](https://wiki.leagueoflegends.com/en-us/Waterwalking), [Gathering Storm](https://wiki.leagueoflegends.com/en-us/Gathering_Storm) |
| Resolve | [Grasp of the Undying](https://wiki.leagueoflegends.com/en-us/Grasp_of_the_Undying) |
| Inspiration | [First Strike](https://wiki.leagueoflegends.com/en-us/First_Strike), [Magical Footwear](https://wiki.leagueoflegends.com/en-us/Magical_Footwear), [Approach Velocity](https://wiki.leagueoflegends.com/en-us/Approach_Velocity), [Jack of All Trades](https://wiki.leagueoflegends.com/en-us/Jack_of_All_Trades) |

Important source interpretations:

```text
Last Stand reference points:
  40% missing HP -> 5%
  50% missing HP -> 7%
  60% missing HP -> 9%
  >= 70% missing HP -> 11%

Absolute Focus:
  scaling = 3..30 AP or 1.8..18 AD over levels 1..18
  active condition = current HP > 70%
  slope continues through levels 19..20
```

Visual-only runes use Riot names and icons but add no hidden combat math.

## Icon sources

### Item icons

Local files use Riot item IDs:

```text
frontend/icons/{item-id}.png
https://ddragon.leagueoflegends.com/cdn/16.14.1/img/item/{item-id}.png
https://ddragon.leagueoflegends.com/cdn/16.14.1/data/en_US/item.json
```

Missing local icons use this display-only fallback:

```text
https://cdn.communitydragon.org/latest/item/{item-id}
```

CommunityDragon's live path is not a numerical-data source.

### Rune and shard icons

Rune files use the Riot perk ID. Their paths come from the pinned rune catalog.

```text
frontend/icons/runes/{perk-id}.png
https://ddragon.leagueoflegends.com/cdn/img/{icon-path}
```

Path emblems and stat-shard assets are also stored locally. Riot documents the
format in the [Data Dragon guide](https://developer.riotgames.com/docs/lol#data-dragon).

## Attribution and update checklist

League of Legends and Riot Games are trademarks or registered trademarks of
Riot Games, Inc. This independent tool is not endorsed by Riot Games. Riot and
CommunityDragon images identify in-game items and runes.

For each patch:

- Record the patch and review date.
- Review changed champion, item, rune, and combat pages.
- Update pinned data separately from display assets.
- Run the complete test suite and baseline backtest.
- Repeat affected Practice Tool isolations.
- Update the validation record and confidence label.
