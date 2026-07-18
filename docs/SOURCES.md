# Data and icon sources

This file is the source ledger for the simulator. It records where champion,
item, rune, combat-rule, and icon information came from and how conflicting
evidence is handled.

Last reviewed: **2026-07-18**. The local Riot asset set is pinned to Data Dragon
**16.14.1**. League Wiki pages are live pages and can change after this review.

Related project records:

- [Simulation model](MODEL.md) — what the engine currently calculates.
- [Validation and backtesting](VALIDATION.md) — controlled observations,
  comparisons, confidence, and unresolved evidence.
- [Maintaining items](ITEM_MAINTENANCE.md) — how to apply a patch update without
  bypassing validation.

## Provenance policy

Pinned numerical values live in the Python data files; this ledger identifies
their external origin. A live link is not treated as an automatic update feed.
When a source changes, the implementation, source review date, automated tests,
and affected Practice Tool cases must be updated together.

## Source priority

When sources disagree, use this order:

1. A controlled, repeatable Practice Tool observation from the target patch.
2. Current Riot patch notes or Riot-published game data.
3. The current League of Legends Wiki page and its notes/patch history.
4. An explicit simulator assumption, clearly documented in
   [the simulation model](MODEL.md) and validation record.

The simulator keeps the wiki formula and the measured exception side by side
when a Practice Tool interaction is timing-sensitive. Values should never be
silently updated from a live page without rerunning the regression suite.

## Champion and combat-system references

| Data used | Source |
|---|---|
| Kayle base stats, passive breakpoints, Q/W/E/R ranks, ratios, timings, range, and cooldowns | [Kayle — League Wiki](https://wiki.leagueoflegends.com/en-us/Kayle) |
| Non-linear per-level stat growth | [Champion statistic](https://wiki.leagueoflegends.com/en-us/Champion_statistic) |
| Attack-speed ratio, cap, windup, and attack timer | [Attack speed](https://wiki.leagueoflegends.com/en-us/Attack_speed) and [Attack timer](https://wiki.leagueoflegends.com/en-us/Attack_timer) |
| Armor and physical mitigation | [Armor](https://wiki.leagueoflegends.com/en-us/Armor) |
| Magic resistance and magic mitigation | [Magic resistance](https://wiki.leagueoflegends.com/en-us/Magic_resistance) |
| Resistance reduction and penetration ordering | [Armor penetration](https://wiki.leagueoflegends.com/en-us/Armor_penetration) and [Magic penetration](https://wiki.leagueoflegends.com/en-us/Magic_penetration) |
| Movement-speed stacking and soft caps | [Movement speed](https://wiki.leagueoflegends.com/en-us/Movement_speed) |
| Adaptive force conversion | [Adaptive force](https://wiki.leagueoflegends.com/en-us/Adaptive_force) |
| Ability haste and cooldown conversion | [Ability haste](https://wiki.leagueoflegends.com/en-us/Ability_haste) |

Practice Tool observations and their exact simulator comparisons are documented
in [Validation and backtesting](VALIDATION.md). The machine-readable baseline is
[`validation/practice_tool_cases.json`](../validation/practice_tool_cases.json).

## Item references

The complete selectable item pool and its source pages are:

| Simulator item | Wiki source |
|---|---|
| Boots | [Boots](https://wiki.leagueoflegends.com/en-us/Boots) |
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

Useful Riot change records for recent or unusual items:

- [League patch 26.9 notes](https://www.leagueoflegends.com/en-gb/news/game-updates/league-of-legends-patch-26-9-notes/) introduced Doran's Bow, documents the Dusk and Dawn healing addition, and records Statikk Shiv's rework to a single Energized trigger dealing 60 magic damage to champions.
- [League patch 26.11 notes](https://www.leagueoflegends.com/en-us/news/game-updates/league-of-legends-patch-26-11-notes/) records the mid-role quest's 8% bonus AD/AP reward and Experimental Hexplate's ranged 35% AS / 14% movement-speed Overdrive values. Practice Tool measurements are the regression authority for their combined Swiftmarch interaction.
- [League patch 25.21 notes](https://www.leagueoflegends.com/en-us/news/game-updates/patch-25-21-notes/) records Doran's Blade's return to omnivamp-style healing and the Doran's Ring sustain change.
- The live wiki page remains the source for the current post-release value when
  a later patch changed an item after its introduction.

Not every passive changes damage. Sustain, stasis, shields, slows, and takedown
effects can be shown in the UI while remaining outside the damage calculation;
the [model exclusions](MODEL.md#explicit-assumptions-and-exclusions) list every
deliberately unsupported or normalized effect.

For the July 17, 2026 item expansion, Riot Data Dragon 16.14.1 was used to
cross-check standard Summoner's Rift item IDs, costs, base stats, names, and
icons. The linked live wiki pages supplied the detailed formulas and cast/on-hit
classification. This prevents similarly named legacy or alternate-mode entries
from being mixed in: Bloodletter's Curse uses SR ID 8010, the current
Stormrazor uses ID 3097, Rapid Firecannon uses ID 3094, Experimental Hexplate
uses ID 3073, Essence Reaver uses ID 3508, Yun Tal uses ID 3032, and Navori
Flickerblade uses ID 6675.

## Rune references

Rune tree names, IDs, slots, and icon paths are matched against Riot's
[`runesReforged.json`](https://ddragon.leagueoflegends.com/cdn/16.14.1/data/en_US/runesReforged.json).
The general reference is the [Rune page](https://wiki.leagueoflegends.com/en-us/Rune).

The following wiki pages are the formula sources for runes that can affect this
simulator's damage, stats, timing, or Swiftmarch adaptive force:

| Path | Rune sources |
|---|---|
| Precision | [Press the Attack](https://wiki.leagueoflegends.com/en-us/Press_the_Attack), [Lethal Tempo](https://wiki.leagueoflegends.com/en-us/Lethal_Tempo), [Fleet Footwork](https://wiki.leagueoflegends.com/en-us/Fleet_Footwork), [Conqueror](https://wiki.leagueoflegends.com/en-us/Conqueror), [Legend: Alacrity](https://wiki.leagueoflegends.com/en-us/Legend:_Alacrity), [Legend: Haste](https://wiki.leagueoflegends.com/en-us/Legend:_Haste), [Coup de Grace](https://wiki.leagueoflegends.com/en-us/Coup_de_Grace), [Cut Down](https://wiki.leagueoflegends.com/en-us/Cut_Down), [Last Stand](https://wiki.leagueoflegends.com/en-us/Last_Stand) |
| Domination | [Electrocute](https://wiki.leagueoflegends.com/en-us/Electrocute), [Dark Harvest](https://wiki.leagueoflegends.com/en-us/Dark_Harvest), [Hail of Blades](https://wiki.leagueoflegends.com/en-us/Hail_of_Blades), [Cheap Shot](https://wiki.leagueoflegends.com/en-us/Cheap_Shot), [Relentless Hunter](https://wiki.leagueoflegends.com/en-us/Relentless_Hunter) |
| Sorcery | [Summon Aery](https://wiki.leagueoflegends.com/en-us/Summon_Aery), [Arcane Comet](https://wiki.leagueoflegends.com/en-us/Arcane_Comet), [Stormraider's Surge](https://wiki.leagueoflegends.com/en-us/Stormraider%27s_Surge), [Deathfire Touch](https://wiki.leagueoflegends.com/en-us/Deathfire_Touch), [Axiom Arcanist](https://wiki.leagueoflegends.com/en-us/Axiom_Arcanist), [Transcendence](https://wiki.leagueoflegends.com/en-us/Transcendence), [Celerity](https://wiki.leagueoflegends.com/en-us/Celerity), [Absolute Focus](https://wiki.leagueoflegends.com/en-us/Absolute_Focus), [Scorch](https://wiki.leagueoflegends.com/en-us/Scorch), [Waterwalking](https://wiki.leagueoflegends.com/en-us/Waterwalking), [Gathering Storm](https://wiki.leagueoflegends.com/en-us/Gathering_Storm) |
| Resolve | [Grasp of the Undying](https://wiki.leagueoflegends.com/en-us/Grasp_of_the_Undying) |
| Inspiration | [First Strike](https://wiki.leagueoflegends.com/en-us/First_Strike), [Magical Footwear](https://wiki.leagueoflegends.com/en-us/Magical_Footwear), [Approach Velocity](https://wiki.leagueoflegends.com/en-us/Approach_Velocity), [Jack of All Trades](https://wiki.leagueoflegends.com/en-us/Jack_of_All_Trades) |

Two important implementation notes:

- Last Stand's four verified reference points are 5% at 40% missing HP, 7% at
  50%, 9% at 60%, and 11% at 70% or more. This was wiki-confirmed because own
  HP could not be controlled cleanly in Practice Tool.
- Absolute Focus uses the wiki's linear 3–30 AP or 1.8–18 AD scaling over
  levels 1–18 and the strict **above 70% current HP** condition. Top-quest
  levels 19–20 preserve the same slope, matching the project's general rule for
  level-scaled runes.

Runes shown as greyed/unselected in the interface still use Riot's names and
icons, but visual-only runes do not contribute hidden combat math.

## Icon sources

### Item icons

Local item PNG files in `frontend/icons/` are Riot client assets downloaded from
Data Dragon 16.14.1 with the item ID as the filename:

```text
https://ddragon.leagueoflegends.com/cdn/16.14.1/img/item/{item-id}.png
```

The supporting item catalog is:

```text
https://ddragon.leagueoflegends.com/cdn/16.14.1/data/en_US/item.json
```

If an icon is not present in the local folder, the frontend falls back to
CommunityDragon:

```text
https://cdn.communitydragon.org/latest/item/{item-id}
```

CommunityDragon's `latest` path is intentionally a display fallback, not a
numerical data source. Item stats and formulas remain pinned in the Python data
file and the wiki ledger above.

### Rune and shard icons

Rune icons in `frontend/icons/runes/` use the Riot perk ID as the local filename.
Their original paths come from Data Dragon 16.14.1's `runesReforged.json` and
are served by Riot with this pattern:

```text
https://ddragon.leagueoflegends.com/cdn/img/{icon-path-from-runesReforged.json}
```

The five `path_*.png` files are the Precision, Domination, Sorcery, Resolve, and
Inspiration path emblems. `StatMods*.png` files are Riot client stat-shard
assets. Local copies avoid UI breakage if a CDN or a live version changes.

Riot's official overview of Data Dragon and its asset conventions is the
[Riot Developer Portal Data Dragon documentation](https://developer.riotgames.com/docs/lol#data-dragon).

## Attribution and maintenance

League of Legends and Riot Games are trademarks or registered trademarks of
Riot Games, Inc. This is an independent fan-made calculation tool and is not
endorsed by Riot Games. Data Dragon and CommunityDragon images are used only to
identify in-game items and runes.

When updating to a new patch:

1. Record the new patch and review date here.
2. Review every linked champion, item, and damage-relevant rune page that
   changed in the patch notes.
3. Update pinned numerical data separately from display icons.
4. Rerun all automated tests and the baseline backtest.
5. Repeat affected Practice Tool isolation cases and update
   [Validation and backtesting](VALIDATION.md) with the new evidence.
