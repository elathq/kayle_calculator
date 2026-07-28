# Validation and backtesting

This is the canonical evidence record. It stores Practice Tool observations,
exact simulator comparisons, inconsistent captures, regression coverage, and
remaining gaps. Implemented formulas are not repeated here; see the
[Simulation model](MODEL.md).

## Evidence labels

| Label | Standard |
|---|---|
| Practice Tool-confirmed | Reproduced in a controlled in-game isolation. |
| Source-confirmed | Taken from Riot or the League Wiki and covered by tests. |
| Simulator assumption | A documented normalization for ambiguous game timing. |
| Inconsistent capture | Preserved but excluded from regression targets. |
| Not modeled | Explicitly outside the simulator's scope. |

## Current status

```text
documentation review       = 2026-07-28
fixture asset version      = Data Dragon 16.14.1
live Wiki rules patch      = 26.14
original capture patch     = confirmation pending
automated suite            = 120 Python + 3 frontend passing tests
```

| Area | Status |
|---|---|
| Precision, attacks, E, PTA, fire wave | Practice Tool-confirmed |
| Q, resistance order, penetration, Shadowflame crit | Practice Tool-confirmed |
| Rageblade E snapshot and fast-reset ordering | Practice Tool-confirmed |
| Rageblade durations and Phantom Hit cadence | Patch 26.14 source-confirmed; prior attack-7 capture superseded |
| R, Gunblade, Lich Bane | Practice Tool-confirmed |
| Dusk and Dawn repeat timing | Patch 26.14 source-confirmed; fresh exact-total isolation needed |
| Blade of the Ruined King | Patch 26.14 source-confirmed and regression-tested |
| Selected extended-combat and Energized items | Practice Tool-confirmed |
| Last Stand | Source-confirmed |
| W, Swiftmarch, boots, starters, progression | Source-confirmed and regression-tested |

The first Practice Tool patch was not recorded. The fixture therefore keeps
the honest status `patch confirmation pending`; this is separate from the
dated live-Wiki rules audit performed for patch 26.14.

## Practice Tool protocol

Before a pass, record:

- Patch, map, and date.
- Kayle level, ranks, items, runes, shards, displayed stats, maximum HP, and
  current HP.
- Dummy maximum HP, current HP, bonus HP, armor, and magic resistance.
- Every stack, ready effect, and timed state present before the sequence.

For each case:

- Reset target, cooldowns, and stacks.
- Write the exact action order and waits.
- Record target HP before and after.
- Record the dummy total.
- Record every floating component and damage type.
- Record temporary Kayle stats when testing a buff.
- Repeat the case and preserve timing branches separately.
- Compare the first differing timeline event, not only the aggregate.

Presentation tolerance:

```text
normal integer-display tolerance ~= 1 point
engine precision = fractional at every stage
```

Baseline commands:

```text
python -B validation/backtest.py
python -B -m unittest discover -s tests -v
```

Recommended isolation order:

- Basic attacks and Q across several resistance values.
- Q followed by the same hit to confirm post-damage shred.
- Percentage penetration, flat penetration, then both.
- Threshold effects from both sides of the threshold.
- E at full and reduced target HP.
- PTA, Spellblade, and Rageblade separately before combinations.
- W and movement effects around expiry.
- On-hit and Energized items one at a time.
- R-triggered and cooldown items one at a time.
- Extended-fight ramps at exact time boundaries.
- Natural crit and non-crit samples recorded separately.

Suggested resistance and timing checkpoints:

```text
resistance cases = 0, 50, 100, 200
Riftmaker times  = 0, 1, 2, 3, 4 s
```

## Baseline fixture

The machine-readable fixture is
[`validation/practice_tool_cases.json`](../validation/practice_tool_cases.json).

Setup:

```text
Kayle level/ranks = level 12, Q5 W0 E5 R2
items             = Nashor's Tooth, Dusk and Dawn, Rabadon's Deathcap
runes             = PTA, Presence of Mind, Alacrity, Last Stand,
                    Manaflow Band, Celerity
shards            = attack speed, adaptive force, scaling health
starting state    = full HP, zero Legend stacks, zero Zeal stacks
dummy             = 3500 current/max HP, 100 armor, 100 MR

displayed Kayle:
  AD              = 75
  AP              = 363
  attack speed    = 1.277
  maximum HP      = 1996
```

Results:

```text
case             dummy total   HP delta   exact simulation   exact - dummy
AA               126           125        125.78             -0.22
E                260           260        260.37             +0.37
AA -> E          455           454        454.68             -0.32
AA -> E -> AA    591           590        590.52             -0.48

floating components:
AA               physical 37              magic 88
E                physical 37              magic 134 + 88
AA -> E          physical 37 + 37         magic 88 + 144 + 147
AA -> E -> AA    physical 37 + 37 + 40    magic 88 + 144 + 147 + 95
```

This confirms the basic hit, on-hit package, E reset, Dusk and Dawn repeat, PTA
stacking, and post-proc amplification.

## Core combat findings

### Press the Attack

Setup used Nashor's Tooth and Rabadon's Deathcap without Dusk and Dawn.

```text
sequence   exact    Practice Tool                 important component
3 AA       395.21   395; HP 3500 -> 3105         third: 37 physical + 133 magic
4 AA       516.31   516; HP 3500 -> 2984         fourth: 40 physical + 80 magic

level 12 PTA raw       = 117.6471
after 100 MR           = 58.8235
level 20 PTA raw       = 174.1176
later-damage amplifier = 8%
```

The triggering frame is not amplified. The level-scaling slope continues
through the top-quest extension.

#### Dusk and Dawn proc lockout

This test isolated whether Dusk and Dawn's repeated on-hit package can trigger
PTA again after PTA has already activated.

```text
level                    = 18
target                   = 3500 HP, 60 armor, 60 MR
displayed stats          = 93 AD, 744 AP, 1.482 attack speed
items                    = Deathcap, Dusk and Dawn, Swiftmarch,
                           Nashor's Tooth, Shadowflame, Void Staff
Gathering Storm          = 20 minutes
E AA cancel              = off

Q -> AA -> AA -> AA
Practice Tool total      = 2685
simulator before fix     = 2708.74
difference               = +0.88%

Q -> AA -> AA -> AA -> E
Practice Tool total      = 4500
simulator before fix     = 4708.73
second simulated PTA     = 179.38
legacy same-frame model  = 4529.36
current 0.20 s model     = 4181.31
current difference       = -7.08%
```

The first Dusk and Dawn repeat helps reach the initial PTA trigger on the
second basic attack. Once PTA is active, the third attack, E, and E's repeated
on-hit package do not build or trigger PTA again. Its 8% outgoing amplifier
continues to affect later frames. The live Wiki now explicitly places Dusk and
Dawn's repeat 0.20 seconds after the triggering attack. The historical
Practice Tool total was captured without a recorded patch, so it is preserved
but is no longer the exact regression target; this case needs a fresh capture.

### Fire wave and top-quest levels

```text
fire-wave base = 20 through level 11
fire-wave base = 20 + 3 * (level - 11) afterward

level 18 base = 41
level 20 base = 47

level 18:
  attacks one/two = 56 wave + 74 on-hit magic + 46 physical
  attack three    = 56 wave + 154 magic + 46 physical
  target          = 3500 -> 2889

level 20:
  attacks one/two = 59 wave + 74 on-hit magic + 49 physical
  attack three    = 59 wave + 161 magic + 49 physical

clean level-20 attack:
  components      = 59 magic + 74 magic + 49 physical
  dummy total     = 183
  target          = 3500 -> 3317
  exact           = 183.49
```

One multi-attack capture reported a final HP inconsistent with its component
text. It is retained but excluded from regression.

```text
inconsistent capture final HP = 2868
current exact three-attack result = 637.53
component-text implied total ~= 633
```

### Q, shred, and penetration

Q matched at every recorded resistance case. It deals damage before applying
its reduction.

```text
confirmed order:
  Q damage against pre-hit resistance
  -> 15% armor/MR reduction
  -> percentage penetration
  -> flat penetration
  -> mitigation

tested MR = 0, 50, 100, 200
```

Void Staff, Shadowflame, and their combination matched Q into attack cases.

### Shadowflame crit

The mechanic is called **Shadowflame crit** in this project.

```text
condition = live current HP before the damage instance < 40% maximum HP
multiplier = 1.20 to eligible magic and true damage

dummy maximum HP = 1200
above threshold:
  Q displayed magic = 212

below threshold after five attacks:
  HP before Q         = 404
  Q displayed magic   = 255
  final HP            = 149
  dummy total         = 1052
```

The level-18 Dusk and Dawn build isolated the within-attack ordering:

```text
setup      = Dusk and Dawn, Nashor's, Deathcap, Void Staff, Shadowflame,
             Swiftmarch; PTA; 10 Alacrity; Celerity; Gathering Storm at 25 min
dummy      = 3500 HP, 60 armor, 60 MR
sequence   = Q -> AA -> AA -> AA

Practice Tool total = 2636
simulator total     = 2635.68

third AA physical             = 66
third AA combined magic       = 552 (Shadowflame crit)
resolved order                = physical -> fire wave -> normal on-hits
```

The physical hit leaves the target above the threshold. The non-critical fire
wave crosses it, then Nashor's and E passive crit immediately. Earlier
components are not changed retroactively.

### Natural crit and Kayle E component boundary

The 2026-07-26 League Wiki review separates Starfire Spellblade into basic
attack damage, passive proc damage, and active spell damage. It identifies the
Aflame attack/explosion and Divine Ascent fire wave as crit-capable, while the
separate E passive on-hit and active missing-health magic instances have no
natural crit modifier.

The automated regression compares an otherwise identical level-18 E with 0%
and 25% crit chance:

```text
physical basic-attack component = expected-crit scaled
Divine Ascent fire wave         = expected-crit scaled
E passive magic on-hit          = unchanged
E active missing-health magic   = unchanged
```

Shadowflame remains deliberately separate: its conditional magic/true-damage
modifier can amplify E passive or active damage below 40% target HP without
making either component respond to Kayle's ordinary crit chance.

### Q into E timing policy

```text
Q allowed to land, then E       = 295 total
point-blank Q, immediate E      = 285 total
maximum E range, immediate E    = 273 total
```

These are projectile timing branches, not different E formulas. The simulator
always treats an entered Q before E as landed before E.

### E missing-health snapshot

```text
setup:
  level/items = level 12, Nashor's Tooth, Rabadon's Deathcap
  rune        = Fleet Footwork
  dummy       = 1000 HP, 100 armor, 100 MR
  sequence    = AA -> AA -> AA -> E

HP before E        = 664 displayed / 663.6138 exact
E components       = 37 physical + 98 magic
dummy total        = 473
final HP           = 528
exact total/final  = 472.52 / 527.48
missing raw/postMR = 48.004 / 24.002
```

Without Rageblade, E reads missing HP before its empowered attack.

### Rageblade and Phantom Hit

The original unknown-patch capture began at zero stacks with Nashor's Tooth,
Rageblade, and Rabadon's. It reported the following cadence:

```text
historic capture: first Phantom Hit = attack 7
```

That attack-7 interpretation is superseded and is no longer a current
regression authority. The live patch 26.14 Wiki defines a 3-second Seething
duration, a 6-second Phantom Hit count duration, and counts the attack that
reaches maximum Seething toward the three-hit cadence:

```text
maximum Seething reached = attack 4
first Phantom Hit        = attack 6
continuing cadence       = attacks 6, 9, 12, ...
```

### Rageblade with E reset

The UI exposes one E action and a **Use E for AA cancel** condition. Enabled
uses the fast-reset branch; disabled waits for the preceding AA's complete
attack interval. This preserves one E formula while allowing both observed
execution timings to be backtested.

Practice Tool isolated the E missing-health ordering: an ordinary Rageblade E
reads after its physical hit, while a fast Phantom-triggering E reads after its
normal on-hit package. The old exact totals used the superseded attack-7
cadence and are no longer regression targets. From zero stacks on current
rules, `4 AA -> E` is attack five without Phantom Hit, while `5 AA -> E` makes
E attack six and the first Phantom Hit.

Level-6 `AA -> E` isolation established that attack windups resolve in whole
game ticks. Ordinary attack timers stay continuous. The model uses the
documented Kayle windup instead of manually entered Practice Tool DPS:

```text
game tick      = 1 / 30 s
Kayle windup   = 0.193555 / total attack speed
fast E hit     = ceil(windup / game tick) * game tick + one projectile tick
waited E hit   = remaining AA cooldown + fast E hit
```

An `AA -> E -> AA -> AA` Lich Bane isolation also confirmed that E cannot place
the following ordinary attack on the next game tick. The post-E attack waits
for its normal `1 / attack speed` cadence. E itself receives Lich Bane's primed
attack-speed bonus during its windup; after Spellblade is consumed, later
attacks use the lower unprimed speed.

The level-18 point-blank `Q -> AA -> AA -> AA -> E` isolation additionally
confirmed that Spellblade readiness must be sampled when E is pressed. Q has
no modeled travel time, but its windup is aligned to the game clock.

```text
items       = Lich Bane, Deathcap, Shadowflame, Nashor's, Void Staff, Swiftmarch
target      = 3500 HP, 30 armor, 30 MR
displayed   = 93 AD, 755 AP, 1.415 AS
fast total  = 4734.39
fast time   = 1.780 s
fast DPS    = 2660.2
```

### Dusk and Dawn cooldown

```text
setup    = level 12, Nashor's, Dusk and Dawn, Rabadon's, Fleet
sequence = Q -> AA -> immediate E

HP after Q                 = 3320
historical dummy total     = 637
current exact total        = 628.72
current final HP           = 2871.28
current difference         = -1.30%
Spellblade cooldown    = 1.5 s

controlled 0.5 s waits:
  with Dusk and Dawn    = 637
  without Dusk and Dawn = 425

non-reproduced captures:
  with Dusk and Dawn    = 622
  without Dusk and Dawn = 416
```

The immediate E occurs inside the Spellblade cooldown, so only the first attack
consumes the proc. The delayed repeat can land after E and therefore changes
E's missing-health snapshot relative to the former same-frame model. The
cooldown conclusion remains covered; the exact total needs a fresh capture.
Non-reproduced totals are excluded.

### Lich Bane

```text
setup = level 12, Nashor's, Lich Bane, Rabadon's, 414.7 exact AP
case  = clean E into 100 resistance

components                     = 37 physical + 218 magic
dummy total / remaining HP     = 256 / 3244
exact Spellblade post-mitigation = 121.2872
```

### Divine Judgment

```text
setup = level 12, rank-two R, Nashor's, Rabadon's, 284.7 exact AP
dummy = 3500 HP, 100 MR

floating magic   = 249
dummy total      = 250
target HP        = 3500 -> 3251
exact simulation = 249.645
```

### Hextech Gunblade

```text
setup = level 12, Gunblade, Rabadon's, 284.7 exact AP
dummy = 3500 HP, 100 MR

floating / total = 155 magic / 155
target HP        = 3500 -> 3345
exact simulation = 155.4403

base at level 19 = 257.59
base at level 20 = 262.18
```

The supplied level slope continues through the top-quest extension.

## Source-confirmed findings

### Last Stand

Own HP could not be controlled cleanly in Practice Tool. The wiki curve and
automated boundary tests are the current evidence.

```text
missing HP   current HP   damage increase
40%          60%          5%
50%          50%          7%
60%          40%          9%
>= 70%       <= 30%       11%
```

### W, movement speed, and Swiftmarch

The formulas are source-confirmed and their timing layers have automated
coverage.

```text
W duration = 2 s
W AP movement scaling = 8 percentage points per 100 AP
Swiftmarch force = 5% of final displayed MS
movement soft-cap breakpoints = 415 / 490
Fleet visible-update delay ~= 0.1 s
```

Fleet synchronization is automatic. No special wait action is exposed.
Nimbus Cloak remains inactive because the combo has no Summoner Spell actions.

### Progression, starters, and boots

```text
default path = E, Q, W, then Q > E > W
R ranks      = champion levels 6, 11, 16

Absolute Focus = 3..30 AP or 1.8..18 AD across levels 1..18
active only when current HP > 70%
slope continues through levels 19..20

Starter limit = 1
Boots limit   = 1
Dark Seal Glory cap = 10
mid-role bonus AD/AP multiplier = 1.08
evolved mid-role boots illegal at levels 19..20
```

Covered entries include base and evolved boots, every starter, and Dark Seal.

## Item interaction isolations

The following direct captures are regression authorities for their isolated
mechanics. Other newly added item formulas remain source-confirmed until they
receive an equivalent capture.

### Essence Reaver

```text
setup = level 20 top-lane, adaptive shard, no Swiftmarch
displayed AD / crit = 155 / 25%

clean non-crit AA:
  target            = 3500 -> 3377
  dummy total       = 124
  components        = 26 magic + 20 magic + 77 physical

W -> non-crit AA:
  target            = 3500 -> 3308
  dummy total       = 192
  components        = 26 magic + 20 magic + 145 physical
  extra Spellblade  = 68 displayed physical

live source formula:
  raw Spellblade = 1.25 * base AD + 0.5 * total crit percentage points
  25% crit contributes 12.5 flat physical damage
```

The capture confirms the physical Spellblade branch and adaptive shard
inclusion, but its rounded display does not distinguish the exact crit-scaling
formula. The patch 26.14 source audit supplies the flat `0..50` term; it is not
an additional base-AD ratio. The same audit confirms a 10-second priming
window, refreshed by later eligible casts, and that the proc applies life
steal.

### Experimental Hexplate with Swiftmarch

```text
setup = level 18 mid-lane

before R:
  AD          = 156 (93 base + 63 bonus)
  attack speed= 1.225
  movement    = 435
  R cooldown  = 61.54 s

Overdrive:
  AD          = 157 (93 base + 65 bonus)
  attack speed= 1.459
  movement    = 478

observed AS delta = 0.234
expected delta    = 0.667 * 35% = 0.23345

zero-Alacrity simulator pair = 1.215 -> 1.449
capture Alacrity stacks      = 1
```

This confirms ranged Overdrive, movement soft caps, the mid-role multiplier,
and live Swiftmarch recalculation.

### Kraken Slayer

```text
setup = level 18, adaptive and AS shards, zero Legend stacks
displayed AD / AS = 143 / 1.349
dummy = 3500 HP, 100 armor, 100 MR

AA -> AA -> AA:
  target          = 3500 -> 3073
  dummy total     = 428
  attack one/two  = 43 magic + 71 physical
  attack three    = 43 magic + 155 physical
  exact           = 427.40 damage / 3072.60 HP

AA -> AA -> E:
  target          = 3500 -> 3060
  dummy total     = 440
  attack one/two  = 23 magic + 20 magic + 71 physical
  E               = 23 magic + 32 magic + 155 physical
  exact           = 438.84 damage / 3061.16 HP
```

Kraken reads missing HP before the triggering attack and E consumes an on-hit
stack. Aggregate display differences are not used to round the engine. The
patch 26.14 Wiki audit additionally classifies Bring It Down as basic damage,
so Hexoptics Magnification applies to it, and as life-steal-applying item
damage.

### Terminus

```text
setup = level 18, 128 AD, 1.315 AS
dummy = 3500 HP, 100 armor, 100 MR
sequence = seven attacks

target / dummy total = 2596 HP / 904
physical sequence    = 63, 63, 67, 67, 71, 71, 75
magic groups         = 22+34, 22+34, 23+36, 23+36,
                       24+38, 24+38, 26+40

Dark stacks granted after attacks = 2, 4, 6
simulator before ordering fix = 908.08
simulator after ordering fix  = 904.15 damage / 2595.85 HP
```

The triggering fire wave uses the previous penetration state. Terminus'
30-magic-damage Shadow on-hit also applies life steal when the build has a
life-steal source.

### Bloodletter's Curse

```text
capture displayed stats = 93 AD, 80 AP, 1.082 AS
dummy = 3500 HP, 100 armor, 100 MR
sequence = four attacks

target / dummy total = 3067 HP / 433
physical             = 46 each attack
magic groups         = 30+25, 32+27, 35+29, 35+29

MR by attack = 100, 85, 70, 70
stacks per attack = 2
maximum stacks = 4
```

E passive and fire wave are separate eligible cast instances. The unexplained
AP source is retained as a setup gap; the ordering evidence remains valid.

```text
known no-boot calculation:
  item AP           = 65
  adaptive shard AP = 9
  total AP          = 74
  exact result      = 427.32 damage / 3072.68 HP
```

### Riftmaker

```text
setup = level 18 without evolved boots
displayed = 93 AD, 90 AP, 1.082 AS

bonus HP = 350 item + 180 shard = 530
calculated AP = 70 + 9 + 0.02 * 530 = 89.6

four attacks:
  target / total = 3077 HP / 424
  components     = 31+26+46, 31+26+46, 32+26+47, 32+27+48
  exact          = 423.90 damage / 3076.10 HP
  damage stages  = 0%, 0%, 2%, 4%

six-attack continuation:
  attack five    = 61 magic + 49 physical
  attack six     = 62 magic + 49 physical
  dummy total    = 647
  exact          = 647.34 damage / 2852.66 HP
  final stages   = 6%, 8%
```

This confirms bonus-HP conversion and the whole-second combat ramp.

### Rapid Firecannon

```text
setup = level 18, 98 AD, 0 AP, 1.315 AS, 25% crit

charged non-crit:
  Dummy A         = 3500 -> 3393
  components      = 58 magic + 48 physical

uncharged non-crit:
  Dummy B         = 3500 -> 3413
  components      = 20 magic + 17 magic + 48 physical

post-mitigation RFC difference = 20
raw RFC proc                  = 40 magic
adaptive tie result           = 5.4 AD
exact total AD / AP           = 97.9 / 0
```

This confirms an Energized proc from the ready-start scenario option and the
zero-item-stat adaptive tie. The simulator still reports expected crit damage.

### Statikk Shiv

```text
setup = level 18, 143 AD, 45 AP, 1.282 AS
dummy = 3500 HP, 100 armor, 100 MR
sequence = four attacks

target / dummy total = 2972 HP / 528
attack one          = 28 magic + 54 magic + 71 physical
attacks two..four   = 28 magic + 24 magic + 71 physical
raw Energized proc = 60 magic
exact               = 528.46 damage / 2971.54 HP
```

The capture confirms the preloaded proc selected by the ready-start option.
The live patch 26.14 source audit supplies the shared recharge rules after that
proc: each basic attack or on-hit-applying ability grants 6 charge, and
Statikk grants 9 additional charge per eligible action. Movement-generated
charge remains intentionally outside the model.

### Stormrazor, Swiftmarch, and Fleet

```text
setup = level 18, Alacrity stacks later clarified as 3 / 10

before attack:
  AD / AP       = 166 / 0
  attack speed  = 1.235 recorded
  movement      = 435

first non-crit:
  components    = 95 magic + 83 physical
  post-proc AD  = 170
  post-proc MS  = 570

immediate next non-crit:
  components    = 24 magic + 21 magic + 84 physical
  total / HP    = 309 / 3191

E at expired Fleet state:
  movement      = 540
  components    = 24 magic + 31 magic + 84 physical

E inside Fleet state:
  movement      = 570
  components    = 24 magic + 45 magic + 85 physical

Swiftmarch force:
  Stormrazor-only = 27
  with Fleet      = 28.5
  exact total AD  = 169.828 -> 170.8

Alacrity clarification:
  3 / 10 simulator AS = 1.245
  recorded 1.235 corresponds to adjacent 2 / 10 state
```

Fleet feeds Swiftmarch after its visible update. An immediately queued command
can snapshot before that update; waiting for the displayed movement jump gives
the higher physical result.

### Berserker's Greaves and DPS timing

```text
setup:
  Kayle level      = 6
  ranks            = Q3 / W1 / E1 / R1
  runes            = Fleet Footwork, Alacrity 0 / 10
  shards           = 10% attack speed, adaptive, health
  target           = 1000 HP / 30 armor / 30 MR
  items            = Nashor's Tooth, then Berserker's Greaves

displayed attack speed:
  Nashor's, zero Zeal stacks             = 1.085
  Nashor's + Berserker's, zero stacks    = 1.251
  Nashor's + Berserker's, five stacks    = 1.452

one basic attack:
  displayed AD / AP = 60 / 89
  damage            = 47 magic + 46 physical
  total / DPS       = 93 / 93
  Berserker's does not change hit damage

six basic attacks, Nashor's only:
  target HP / total = 442 / 559
  Practice Tool DPS = 134

six basic attacks, with Berserker's:
  target HP / total = 442 / 559
  Practice Tool DPS = 153

two basic attacks with Berserker's:
  total / DPS       = 186 / 242
```

The dummy starts its DPS window on the first damage timestamp and ends it on
the last. It excludes recovery after the final attack. When every component
lands at one timestamp, it reports total damage as DPS. The simulator now uses
the same rule; the six-attack Berserker's result is:

```text
exact damage       = 558.58
damage window      = 3.652 s
DPS                = 153.0
full action window = 4.341 s (audit field only)
```

### Level-6 Lethal Tempo cadence

The live client data specifies 4% attack speed per ranged Lethal Tempo stack.
An earlier 4.8% value made Kayle's ramping attack cadence too fast.

```text
setup:
  Kayle level/ranks = level 6, Q1 W1 E3 R1
  runes             = Lethal Tempo, Alacrity 0 / 10, full-health Last Stand
  shards            = attack speed, adaptive force, scaling health
  target            = 1000 HP / 0 armor / 0 MR
  item              = Berserker's Greaves
  sequence          = AA -> E -> AA -> AA -> AA -> AA -> AA -> AA -> AA
  E AA cancel       = on

zero-stack attack speed = 0.918
full-stack attack speed = 1.278
exact damage            = 907.55
ideal damage window     = 6.069 s
ideal DPS               = 149.5
observed dummy total    = 907..908
observed manual DPS     = 145..146
```

The exact damage now agrees with the dummy. The simulator's DPS is an ideal
first-hit-to-last-hit result with each attack issued as soon as its timer is
ready. Human input and the dummy's display sampling can make a manually
executed sequence slightly slower without changing its total damage.

## Source-backed item coverage still awaiting isolation

Automated tests cover the implemented timing, stacking, expected-crit, and
target-state rules for the remaining catalog. Direct Practice Tool captures
are still required before relabelling them.

The 2026-07-26 patch 26.14 Wiki audit corrected Hexoptics from the former
1%-per-60, 600-unit model to 1% per 50 units capped at 500, including its
basic-damage interaction with Kraken. Wiki effect tags and Notes also establish
that Rageblade, Kraken, Terminus, and Wit's End on-hit damage, plus Essence
Reaver's Spellblade, benefit from life steal. These remain source-confirmed
until isolated in the Practice Tool.

### Blade of the Ruined King

The 2026-07-28 live Wiki and pinned Data Dragon review established 40 AD, 25%
attack speed, 10% life steal, and a 9% melee / 6% ranged current-health
physical on-hit. The Wiki Notes place the current-HP read before the triggering
basic attack's damage, exclude natural crit, and mark Mist's Edge as
life-steal-applying proc damage.

Regression cases prove:

- Level-5 ordinary attacks use 9%; level-6 attacks use 6%.
- A pre-level-6 E uses its temporary ranged classification and the 6% branch.
- Low-HP champion damage has no artificial 15-damage floor, while high-HP
  champion damage is not capped at 100.
- Armor and armor penetration apply; natural crit and Hexoptics basic-damage
  amplification do not.
- AA and E each create one package. Q, W, R, the fire wave, E passive damage,
  and E active damage do not recursively create another package.
- Dusk and Dawn repeats Mist's Edge at +0.20 seconds and Rageblade Phantom Hit
  repeats it at +0.15 seconds; each repeat reads then-live target HP and applies
  life steal again.

Clawing Shadows' third-hit slow has no outgoing damage, so it remains
display-only. A controlled Practice Tool capture is still needed before these
cases move from source-confirmed to Practice Tool-confirmed.

```text
source-confirmed examples:
  Cosmic Drive
  Stormsurge
  Infinity Edge
  Blade of the Ruined King
  Bloodthirster
  Hexoptics C44
  Phantom Dancer
  Lord Dominik's Regards
  Mortal Reminder
  Wit's End
  Fiendhunter Bolts
  Yun Tal Wildarrows
  Navori Flickerblade
```

## Regression suite

```text
maintained automated tests = 120 Python + 3 frontend passing
```

Coverage includes the precision pipeline, negative resistance, Q ordering,
baseline fixture, E snapshots, Rageblade timing, runes, movement layers,
progression, item restrictions, item IDs, delayed effects, expected crit, and
post-R timelines. Frontend coverage verifies the PNG share-image model, leader
badges, layout sizing, numeric formatting, and invalid input handling.

Run without creating cache files:

```text
python -B -m unittest discover -s tests -v
node --test tests_js/snapshot.test.js
```

## Remaining validation limits

- Record the exact patch for the original Practice Tool fixture on the next
  fresh pass; the separate live-Wiki rules audit is pinned to patch 26.14.
- Last Stand needs a controlled own-HP isolation.
- Preserve raw W, starter, and evolved-boots capture sheets.
- Isolate the remaining source-confirmed item interactions.
- Record random crit branches separately from expected-value comparisons.
- Projectile travel can alter immediate Q into E; the simulator normalizes it.
- Integer displays require presentation tolerance.

```text
normal display tolerance ~= 1 point
```
