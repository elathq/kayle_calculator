# Kayle Damage Simulator & Build Optimizer

Interactive DPS calculator for Kayle: compare multiple item builds side by side
against a simulated enemy, using a freely composable combo sequence.

**Zero dependencies** — pure Python standard library + vanilla HTML/CSS/JS.

## Run

```
python run.py
```

Then open http://127.0.0.1:8000

## Structure

- `backend/data/kayle_data.py` — base stats + growth formula, passive breakpoints (1/6/11/16), Q/W/E/R data
- `backend/data/items_data.py` — the 39-item pool (stats, passives, actives, icon paths)
- `backend/data/enemy_data.py` — enemy presets scaled to level via the growth formula
- `backend/engine.py` — combat simulation (timeline-based)
- `backend/main.py` — stdlib HTTP server: API + static frontend
- `frontend/` — dashboard UI (`icons/` holds local item icons from Data Dragon 16.14.1)
- `tests/` — maintained regression coverage for damage, timing, progression, boots, and starters
- `validation/` — machine-readable Practice Tool fixture and baseline backtest runner

## Documentation

- [`ITEM_EDITING_GUIDE.md`](ITEM_EDITING_GUIDE.md) — copy/paste templates for
  adding or updating items and the exact boundary for `engine.py` changes.

- [`BACKTESTING_AND_FINDINGS.md`](BACKTESTING_AND_FINDINGS.md) — complete
  Practice Tool evidence, conclusions, confidence levels, and remaining limits.
- [`PRACTICE_TOOL_VALIDATION.md`](PRACTICE_TOOL_VALIDATION.md) — concise
  checklist for a new isolation pass.
- [`SOURCES_README.md`](SOURCES_README.md) — League Wiki, Riot data, patch-note,
  and icon-source ledger.

## API

- `GET /api/champion?level=N` — Kayle stats + default ability ranks
- `GET /api/items` — item catalog
- `GET /api/enemy_presets`, `GET /api/enemy_preset?preset=K&level=N`
- `POST /api/simulate` — `{level, ability_ranks, builds, enemy, combo, options}` → per-build results.
  Enemy accepts `hp` (maximum HP), optional `current_hp` (starting HP), and
  optional `bonus_hp` (used by Lord Dominik's Regards).

## Combat model notes

- Total AS = `0.625 + 0.667 × (bonus AS %)/100`, capped at 2.50.
- On-hit layering per attack: total AD (physical) → item on-hits → E passive →
  Spellblade proc → passive fire wave (Aflame + Exalted)
  → Rageblade Phantom Hit (attacks 7, 10, 13… from zero stacks; reapply
  on-hits after 0.15 s).
- **Fire wave level scaling**: 20 base damage through level 11, then +3 per
  level beginning at level 12: 41 at level 18 and 47 at level 20. This is a
  breakpoint formula, not a level-1-to-18 interpolation.
- **E (Practice Tool isolated 2026-07-17)**: E is a full empowered basic attack
  and reset: physical hit + one normal on-hit package. At level 11+, its
  explosion does not add another PTA application or duplicate the on-hit
  package. E primes and consumes Spellblade; Dusk and Dawn deals its Spellblade
  damage/heal and repeats on-hits once, including a PTA application. E uses the
  listed +1.5% per 100 AP missing-health scaling. Without Rageblade it snapshots
  before the attack. With Rageblade it reads after E's physical hit; a fast E
  reset that triggers Phantom Hit reads after the normal on-hit package. The
  combo palette exposes one E action and there is only one E formula. Same-frame
  components are not affected by the PTA amp they trigger.
- **Q before E**: the simulator assumes Q hits before the later E action. Q's
  damage, resistance reduction, and contribution to missing HP are applied;
  projectile distance is intentionally not an input.
- **Boots**: builds are limited to one Boots item. Sorcerer's Shoes grant 12
  flat magic penetration. Spellslinger's Shoes grant 18 flat and 8% magic
  penetration. Swiftmarch grants 65 movement speed and adaptive force equal to
  5% of Kayle's current total movement speed (1 AP or 0.6 AD per point of
  adaptive force). Movement-speed soft caps are applied before Swiftmarch reads
  the total; Rabadon's multiplies AP gained from Swiftmarch. Completing the
  mid-lane role quest also increases all bonus AD and AP by 8%. Swiftmarch and
  Spellslinger's Shoes therefore cannot coexist with levels 19-20, which require
  the mutually exclusive top-lane role quest; the simulator ignores that illegal
  combination and reports a warning. The reward is activated strictly by an
  equipped evolved mid-role boot; there is no independent scenario toggle.
- **W and Swiftmarch**: W's movement-speed bonus uses W rank and current AP and
  lasts 2 seconds. Later attacks and abilities use the boosted Swiftmarch force
  only while that buff is active. The combo timeline uses real action/cast and
  attack-speed timing, so a sufficiently late action automatically loses the
  bonus. Every active item, passive, shard, and rune movement-speed layer is
  recalculated at the timestamp of each action.
- **Automatic Fleet synchronization**: selecting Fleet enables its measured
  0.1-second movement-speed update automatically. After an Energized attack,
  the next action uses the Fleet-boosted movement-speed snapshot and feeds it
  into Swiftmarch; no timing utility is exposed in the combo palette.
- Spellblade: primed by any ability cast, consumed by the next attack, 1.5 s
  internal cooldown. Lich Bane grants its 50% AS while primed; Dusk and Dawn
  re-applies on-hit effects on the proc frame and heals. Limited to 1
  Spellblade / 1 Blight item per build (extra ones are ignored with a warning).
  Essence Reaver's Spellblade deals physical damage equal to 125% base AD plus
  0.5% base AD per percentage point of total crit chance; mana is not modeled.
- Resistances: percentage reductions (Q and Bloodletter) → percentage armor or
  magic penetration (including Terminus) → flat magic penetration → floor at 0;
  mitigation = `100/(100+resist)`. Shadowflame crit multiplies magic/true
  damage by 1.2 while the enemy is below 40% max HP (HP is tracked live).
- Maximum and starting enemy HP are separate inputs, allowing direct tests of
  missing-health damage and strict HP thresholds such as Shadowflame crit.
  Target bonus HP is a separate input for LDR's 1% damage per 100 bonus HP,
  capped at 15% / 1500 bonus HP.
- Damage is resolved at full precision through one pipeline: raw damage ->
  outgoing modifiers -> effective resistance -> applied damage. Applied damage
  remains fractional for HP, missing-health scaling, threshold checks, healing,
  totals, and DPS. Whole-number combat text is treated as presentation rather
  than a second combat model. The result timeline exposes raw damage, effective
  resistance, and exact applied damage for Practice Tool calibration.
- Build results show total damage, whole-combo DPS, and **1s burst**. The burst
  metric is the largest sum of applied damage found in any rolling one-second
  window across the completed timeline, including delayed effects. Its winning
  start/end timestamps are returned for auditability.
- R impact lands 2.5 s after its 0.5 s cast; the combo continues in between.
- **Critical strikes**: random item crit chance is represented as expected
  damage, so build comparisons are stable instead of depending on a random
  roll. Infinity Edge adds 30 percentage points to total crit damage. Kayle's
  basic hit and fire wave share the expected crit modifier. Fiendhunter's first
  three attacks after R use its separate 80%-total-crit rule and expected
  natural-crit 15% true-damage branch. Yun Tal starts fully trained by default;
  its scenario toggle can instead start at zero and add 0.4% crit per melee or
  0.2% per ranged attack, capped at 25%.
- **Extended-fight items**: Riftmaker gains 2% damage per whole second after the
  first champion damage instance (8% at four stacks), adds AP equal to 2% bonus
  HP, and gains 10% melee / 6% ranged omnivamp at maximum stacks. Kraken tracks
  three-second on-hit stacks and calculates its third hit from live missing HP.
  Terminus starts with Light, alternates Light/Dark, and reaches 30% armor/MR
  penetration after three Dark hits. Bloodletter applies one 7.5% MR-reduction
  stack per eligible cast instance, with its 0.3-second gate and six-second
  duration.
- **Energized items**: Statikk, Stormrazor, and Rapid Firecannon share the
  “Energized effects start ready” scenario control with Fleet. Statikk deals
  60 magic damage to champions on that Energized attack. Stormrazor deals 100
  magic and grants its 45%
  movement-speed window, while Rapid Firecannon deals 40 magic and grants 35%
  bonus range capped at +150. Cosmic Drive grants 20 flat MS for four seconds
  after magic/true damage. All movement effects feed
  Swiftmarch immediately and expire from later actions using timeline time.
  This includes Fleet Footwork while its one-second movement window is active.
  Experimental Hexplate's R-triggered Overdrive grants ranged Kayle 35% AS and
  14% movement speed for eight seconds and feeds Swiftmarch during that window.
  The 50% AS / 20% MS values are melee-only after patch 26.11.
- **Cooldown items**: Navori reduces the live remaining Q/W/E cooldown by 15%
  on every attack, including E. Yun Tal's six-second Flurry grants 30% AS; its
  30-second cooldown is reduced by attacks using expected crit probability.
- **Kraken Slayer**: every third on-hit application procs Bring It Down. Its
  missing-health scaling snapshots target HP before the triggering attack's
  damage frame, matching the Practice Tool isolation.
- **Adaptive stats**: item AD and AP determine whether shards, runes, and
  Swiftmarch become AD or AP. A zero-AD/zero-AP item-stat tie resolves to AD on
  Kayle, as confirmed with Rapid Firecannon in Practice Tool.
- **Terminus**: attacks alternate Light then Dark. Dark grants 10% armor and
  magic penetration after the complete triggering attack, so the attacks at
  stacks 0/1/2/3 are 1-2 / 3-4 / 5-6 / 7; the triggering fire wave does not
  receive its newly earned stack.
- **Bloodletter's Curse**: Vile Decay is gated per cast instance. Kayle's E
  passive and fire wave are separate eligible passive instances, so a normal
  exalted attack adds two stacks. All damage on one frame uses the stack count
  from that frame's start; four stacks / 30% MR reduction are active from the
  third attack onward.
- **Hexoptics**: target distance remains intentionally absent. Magnification
  assumes attacks occur at Kayle's current maximum attack range (175 / 525 /
  625), capped by the item's 600-unit / 10% formula. A ready Rapid Firecannon
  temporarily extends that assumed range for the Energized attack only.
- Cooldowns are tracked (with ability haste and Navori reductions) but only
  produce warnings — the combo you define is always executed as written.
- Not simulated: mana; Cryptbloom's takedown heal; takedown-only range/reset
  effects on Hexoptics and Fiendhunter; Statikk's secondary chain targets;
  Zhonya's stasis
  (advances time by 2.5 s only); and Rylai's slow amount.

## Runes

Each build has its own rune page (keystone + 3 primary + 2 secondary from
different rows). Damage-relevant runes are marked with a gold dot and are
fully simulated; the rest are visual only. Notes on the model
(`backend/data/runes_data.py` holds all numbers):

- **Adaptive** effects deal/grant physical/AD if bonus AD > AP, else magic/AP
  (resolved from item stats). Rabadon's Opus multiplies rune-granted AP too.
- **PTA**: on-hit stacks (Phantom Hit / D&D repeats add stacks per the wiki);
  the 8% amp lasts the rest of the combo once procced. Its level scaling keeps
  the original per-level slope through top-quest levels 19 and 20.
- **Lethal Tempo**: bolt at 6 stacks; ranged bolt scales 0.8333%/1% bonus AS
  (the wiki-documented 1/6-reduction bug), melee 1%/1%.
- **Conqueror**: 2 stacks per melee attack / 1 ranged / 2 per damaging ability
  cast; Kayle's fire wave shares the attack's cast instance → no extra stack.
  Stack stats apply mid-combo; 8%/5% post-mit heal at 12 stacks.
- **Hail of Blades**: 120%/60% AS that may exceed the 2.5 cap; E's attack
  reset grants extra stacks (up to 2); bonus true damage per empowered attack.
- **Deathfire Touch**: Q/R/fire waves are area damage → 2 s burn, ticks every
  0.5 s, +75% after burning 3 s continuously.
- **Aery** is modeled with a ~4 s effective cooldown (travel approximation).
- **Comet** is assumed to always hit at point-blank values (no distance bonus).
- **Cheap Shot** triggers off Q's 2 s slow, Rylai's 1 s ability slow, or
  Gunblade's 1.5 s slow — impairment is checked before the action's own slow.
- **First Strike**: 3 s window from the first hit, +7% post-mitigation true.
- **Grasp**: 1 stack/second in combat, procs on the attack at 4 stacks.
- **Axiom Arcanist**: +8% on R (area-of-effect ultimate).
- **Movement-speed stacking for Swiftmarch** follows the game formula: base +
  flat bonuses, additive percentage bonuses, multiplicative bonuses, then the
  415/490 soft caps. Swiftmarch reads 5% of that final displayed speed.
- **Celerity / Magical Footwear / Waterwalking**: Celerity grants 1% MS and
  makes flat, additive, and multiplicative bonuses 7% stronger. Magical
  Footwear adds 10 flat MS to any equipped Boots upgrade. The river option
  enables Waterwalking's 10 flat MS and level-scaled adaptive stats.
- **Fleet / Stormraider**: a pre-Energized Fleet attack grants 20%
  melee or 15% ranged MS for 1 second. Practice Tool shows its visible MS
  update shortly after Stormrazor. The simulator automatically synchronizes
  that delayed update before the following action when Fleet is selected.
  Stormraider triggers after 25% target max-HP damage within 3 seconds and uses
  its current 48% melee / 36% ranged, 4-second window. Nimbus Cloak stays
  inactive because Summoner Spells are not actions in this combo simulator.
- **Relentless / Approach Velocity**: configured Relentless stacks grant 8
  flat out-of-combat MS each and fall off on the first damage instance.
  Approach Velocity applies its 15% total-MS multiplier after Kayle impairs the
  target with Q, Rylai, or Gunblade; the simulator assumes Kayle is facing the
  combo target and does not add a target-distance input.
- **Aftershock / Sudden Impact**: conditions unreachable for Kayle → visual only.
- **Stat shards** (one per row): Adaptive (5.4 AD / 9 AP), 10% AS, 8 haste,
  65 HP, 10–200 scaling HP over levels 1–20, and 2.5% movement speed. HP
  shards raise Kayle's max HP (Grasp, D&D heal); the movement-speed shard feeds
  Swiftmarch. Tenacity is visual only. Rabadon amplifies shard AP.
- Config inputs: game time (Gathering Storm), Kayle HP % (Last Stand /
  Absolute Focus), Dark Harvest souls, Legend stacks (Alacrity / Legend: Haste),
  Relentless Hunter stacks, Fleet Energized state, and Waterwalking location.
- **Haste**: Legend: Haste (1.5/stack, basic abilities only) and Transcendence
  (+5 AH at levels 5 and 8) feed cooldown tracking. Haste never changes a
  single combo's damage — the combo is a fixed sequence — it only affects the
  cooldown-warning checks. Transcendence's level-11 takedown refund is not
  simulated. Attack speed, by contrast, fully drives combo duration and DPS.

## Data provenance

Champion, item, rune, combat-rule, and icon references are listed in
[`SOURCES_README.md`](SOURCES_README.md). Practice Tool measurements and exact
simulator comparisons are recorded in
[`BACKTESTING_AND_FINDINGS.md`](BACKTESTING_AND_FINDINGS.md). Level-scaled runes
use their level-1/18 reference values and preserve the same slope through levels
19-20. Kayle's fire wave uses its game-data breakpoint formula separately.
