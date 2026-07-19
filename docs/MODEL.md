# Simulation model

This document is the engine specification. It describes formulas, event order,
snapshots, and deliberate assumptions. Practice Tool evidence belongs in
[Validation and backtesting](VALIDATION.md); external references belong in
[Data and icon sources](SOURCES.md).

## Outputs

Every build receives the same champion setup, target, scenario, and action
sequence. The engine returns damage by type, total damage, DPS, burst, healing,
kill time, remaining target HP, final stats, the event timeline, and warnings.
Cooldown conflicts are also returned as structured errors with the ability,
combo index, attempted-use time, and ready time.

```text
damage window = last damage timestamp - first damage timestamp

if the combo has multiple damage timestamps:
    combo DPS = total applied damage / damage window

if all damage lands at one timestamp:
    combo DPS = total applied damage

burst = maximum applied damage in any rolling 1.0 s window
```

This matches the Practice Tool target dummy: setup time before the first hit
and recovery time after the final hit are excluded. Delayed damage extends the
ending timestamp. The API also returns `timeline_duration` for auditing the
complete action and recovery timeline separately.

The engine evaluates the entered sequence and records invalid Q/W/E/R casts in
`cooldown_errors`. The UI blocks the result, shows an ability-readiness popup,
and outlines every invalid sequence action in red.

## Precision and damage pipeline

All calculations remain fractional. The UI may shorten displayed values, but
HP, thresholds, healing, totals, DPS, and later snapshots use exact values.

```text
raw damage
  -> outgoing modifiers
  -> resistance reduction
  -> percentage penetration
  -> flat penetration
  -> resistance multiplier
  -> exact applied damage
```

League can round floating combat text, target HP, and the Practice Tool total
independently. The simulator does not maintain a second integer-damage model.

## Champion progression

### Base-stat growth

```text
n = level - 1
stat(level) = base + growth * n * (0.7025 + 0.0175 * n)

supported level = 1..20
```

Kayle's base data:

```text
health             = 670 + 92 growth
mana               = 330 + 50 growth
health regen       = 5 + 0.5 growth
mana regen         = 8 + 0.8 growth
attack damage      = 50 + 2.5 growth
armor              = 26 + 4.2 growth
magic resistance   = 22 + 1.3 growth
base attack speed  = 0.625
attack-speed ratio = 0.667
attack speed growth= 1.5%
windup fraction    = 0.19355
base crit modifier = 2.0
movement speed     = 335
base attack range  = 175
```

Attack speed:

```text
total AS = 0.625 + 0.667 * bonus AS percentage / 100
normal cap = 2.50
attack interval = 1 / total AS
```

Hail of Blades may exceed the normal cap. Attack speed controls attack spacing,
the first-to-last damage window, and DPS.

Default rank path:

```text
level:  1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18
rank:   E Q W Q Q R Q E Q E  R  E  E  W  W  R  W  W
```

Role-quest extension:

```text
levels 19..20 = top-lane quest extension
level-scaled effects preserve their original per-level slope
```

### Passive

```text
Zeal AS per stack       = 6%
Zeal maximum stacks     = 5
Exalted movement speed  = 10%

level 1  = Zeal
level 6  = range 525
level 11 = Aflame fire wave
level 16 = range 625 and permanent Exalted

fire-wave base(level) = 20 + 3 * max(0, level - 11)
fire-wave raw magic   = fire-wave base + 0.10 * bonus AD + 0.25 * AP
```

### Q — Radiant Blast

```text
rank                       = 1      2      3      4      5
base magic                 = 60     90     120    150    180
cooldown                   = 12     11     10     9      8 s
mana                       = 60     70     80     90     100

raw magic = base + 0.60 * bonus AD + 0.50 * AP
armor reduction = 15%
MR reduction    = 15%
reduction duration = 4 s
cast time = windup fraction / total AS
```

Q damage uses pre-hit resistance. Its reduction begins after its damage frame.
When Q precedes E, the model assumes Q has already landed.

### W — Celestial Blessing

```text
rank                    = 1      2      3      4      5
base heal               = 55     80     105    130    155
base movement bonus     = 24%    28%    32%    36%    40%
mana                    = 70     75     80     85     90

heal = base heal + 0.25 * AP
movement bonus = base movement bonus + 8 percentage points * AP / 100
buff duration = 2 s
cooldown = 15 s
cast time = 0.25 s
```

Later actions recalculate movement speed, adaptive force, and AP at their own
timestamps. The bonus disappears automatically after expiry.

### E — Starfire Spellblade

```text
rank                         = 1       2       3       4       5
passive base magic           = 15      20      25      30      35
missing-HP base              = 8%      8.5%    9%      9.5%    10%
cooldown                     = 8       7.5     7       6.5     6 s

passive raw magic = base + 0.10 * bonus AD + 0.20 * AP
active missing-HP rate = base rate + 1.5 percentage points * AP / 100
active raw magic = target missing HP * active missing-HP rate
cast time = 0 s
```

E is one empowered basic attack and attack reset. It includes the physical hit,
one normal on-hit package, and the active missing-health damage. It primes and
may consume Spellblade.

The shared **Use E for AA cancel** condition controls the timing only when an E
directly follows an AA:

```text
game tick          = 1 / 30 s
attack timer       = 1 / live post-hit attack speed
AA or E windup     = 0.193555 / current attack speed
E hit time         = windup rounded up to a game tick + one projectile tick

enabled  = skip the preceding AA's remaining cooldown, then resolve E hit time
disabled = finish that cooldown, then resolve E hit time
```

This affects combo duration and can change whether a Spellblade cooldown is
ready. It does not create a second E damage formula.

E is still an empowered basic attack after it lands. If an ordinary AA follows
E, that AA waits for the full post-E attack interval. Lich Bane's attack-speed
bonus while Spellblade is primed is included in E's windup, then disappears
from the following interval when the proc is consumed. Spellblade readiness is
checked when E is pressed, not when its projectile lands.

Q is always modeled at point-blank range. It adds no projectile travel time;
only its attack-speed-scaled cast/windup remains, rounded up to a game tick.
Ordinary `1 / attack speed` timers remain continuous and are not independently
rounded upward, avoiding cumulative timing drift across long attack sequences.

```text
without Rageblade:
  missing-HP snapshot = before empowered attack

with Rageblade, no Phantom trigger:
  missing-HP snapshot = after physical hit

with Rageblade, fast Phantom-triggering reset:
  missing-HP snapshot = after physical hit + normal on-hit package
```

The explosion does not create a second on-hit package or another PTA stack.
Same-frame damage does not receive an amplifier triggered by that frame. A
waited ordering exists only as an internal regression case; the UI exposes one
E action.

### R — Divine Judgment

```text
rank                  = 1      2      3
base magic            = 200    300    400
cooldown              = 160    120    80 s
mana                  = 100    50     0

raw magic = base + 1.00 * bonus AD + 0.70 * AP
cast time = 0.5 s
impact time = cast start + 2.5 s
```

The combo continues after the cast completes. Delayed R damage and other queued
effects resolve even after the last entered action. The selected combo labels
the action as `R cast`; the result timeline records the cast separately from
the damage event.

```text
short sequence example:
R cast                 = 0.00 s
following attack       = 0.50 s
entered actions end    ≈ 1.50 s
R damage               = 2.50 s
timeline duration      = 2.50 s
```

## Attack event order

A normal attack resolves these layers:

- Basic physical hit using total AD.
- Passive fire wave while eligible.
- Item on-hits.
- E passive on-hit.
- Primed Spellblade.
- Phantom Hit repeat when due.

Attack-frame-gated stacks and amplifiers use the state captured at that frame's
start. Stacks or amplifiers earned there affect later eligible frames.
Shadowflame is the exception: it reads live HP before every damage instance, so
an earlier component can enable the crit for later components of the same hit.

## Target, resistance, and penetration

The target stores maximum HP, current HP, and bonus HP separately. Thresholds
read maximum HP, missing-health effects read current HP, and LDR reads bonus HP.

```text
R0 = listed resistance
R1 = R0 * (1 - percentage reduction)

if R1 >= 0:
  R2 = R1 * (1 - percentage penetration)
  effective resistance = max(0, R2 - flat penetration)
else:
  effective resistance = R1

if effective resistance >= 0:
  resistance multiplier = 100 / (100 + effective resistance)
else:
  resistance multiplier = 2 - 100 / (100 - effective resistance)

applied damage = raw damage * outgoing multiplier * resistance multiplier
true-damage resistance multiplier = 1
```

Shadowflame reads live HP immediately before each eligible instance:

```text
condition = current HP < 0.40 * maximum HP
eligible magic/true multiplier = 1.20
```

Crossing the threshold during an attack does not retroactively change earlier
components, but later magic or true-damage components can crit immediately.

## Movement speed and adaptive force

```text
uncapped MS = (base MS + flat MS) * (1 + additive MS%)
uncapped MS = uncapped MS * multiplicative total-MS effects

if 415 < uncapped MS <= 490:
  displayed MS = 415 + 0.80 * (uncapped MS - 415)

if uncapped MS > 490:
  displayed MS = 415 + 0.80 * 75 + 0.50 * (uncapped MS - 490)
```

Celerity modifies eligible movement bonuses before the soft cap:

```text
personal MS multiplier = 1.01
eligible flat/additive/multiplicative bonuses *= 1.07
```

Adaptive conversion:

```text
1 adaptive-force point = 1 AP or 0.6 AD

if item AD > item AP:
  adaptive force -> AD
else if item AP > item AD:
  adaptive force -> AP
else:
  zero-stat tie -> AD for Kayle
```

Rabadon's multiplier also applies to adaptive AP. Percentage AP modifiers add
together before multiplying the raw AP pool:

```text
final AP = raw AP * (1 + Rabadon 30% + mid-role 8%)
         = raw AP * 1.38
```

Swiftmarch and the mid-role reward:

```text
Swiftmarch flat MS = 65
Swiftmarch adaptive force = 0.05 * current displayed MS
mid-role bonus AD/AP multiplier = 1.08

Rabadon + mid-role AP multiplier = 1 + 0.30 + 0.08 = 1.38

evolved mid-role boots are illegal at level 19..20
```

Every active movement effect feeds the same timestamped calculation. Fleet's
measured delayed display update is synchronized automatically before the next
action when Fleet is selected.

## Item formulas

Only mechanics that change the simulation are listed here. Static item stats
live in `backend/data/items_data.py` and their external references are in
[Data and icon sources](SOURCES.md).

### Shop families and boots

Only one item from each exclusive family is applied. Extra conflicting items
are ignored with a warning.

```text
exclusive families = Boots, Starter, Spellblade, Blight, Fatality

Boots                 = 25 flat MS
Boots of Swiftness    = 55 flat MS + 25% slow resistance
Berserker's Greaves   = 45 flat MS + 25% attack speed
Gunmetal Greaves      = 45 flat MS + 40% attack speed + 5% life steal
Sorcerer's Shoes      = 45 flat MS + 12 flat magic penetration
Spellslinger's Shoes  = 45 flat MS + 18 flat and 8% magic penetration
Swiftmarch            = 65 flat MS + 5% displayed-MS adaptive force
Magical Footwear      = +10 flat MS to equipped Boots

Gunmetal life-steal healing = 0.05 * post-mitigation basic physical damage
```

Attack speed from Berserker's and Gunmetal shortens basic-attack intervals,
which reduces combo duration and raises DPS without changing the number of
configured attacks. Swifties do not grant attack speed, damage, or Swiftmarch
adaptive force. Incoming slows are outside the current simulation, so their
slow resistance is displayed but does not alter the timeline.

### Spellblade and on-hit items

```text
shared Spellblade cooldown = 1.5 s

Dusk and Dawn raw magic = 0.75 * base AD + 0.10 * AP
Dusk and Dawn heal      = 0.10 * AP + 0.03 * bonus HP
Dusk and Dawn           = repeat eligible on-hits once

Lich Bane raw magic = 0.75 * base AD + 0.45 * AP
Lich Bane primed AS = +50%

Essence Reaver raw physical
  = 1.25 * base AD
  + 0.005 * base AD * total crit percentage points

Nashor's Tooth raw magic = 15 + 0.15 * AP
Wit's End raw magic      = 45
Rageblade raw magic      = 30
```

Rageblade cadence:

```text
Seething AS per stack = 8%
maximum stacks = 4
Phantom Hit = every 3rd attack while fully primed
from zero stacks: attacks 7, 10, 13, ...
repeat delay = 0.15 s
```

### Extended combat and penetration

```text
Riftmaker AP = 0.02 * bonus HP
Riftmaker outgoing bonus = 2% per whole combat second
Riftmaker maximum bonus = 8%
Riftmaker max-stack omnivamp = 10% melee / 6% ranged

Kraken trigger = every 3rd eligible on-hit
Kraken melee base = 150 at level 8 -> 200 at level 18
Kraken melee base(level) = 150 + 5 * (clamp(level, 8, 20) - 8)
Kraken ranged base = 0.80 * melee base
Kraken maximum missing-HP amplification = 75%
Kraken stack duration = 3 s

Terminus sequence = Light, Dark, Light, Dark, ...
Dark penetration per stack = 10% armor and MR
maximum Dark stacks = 3
maximum penetration = 30%
stack duration = 5 s

Bloodletter MR reduction per stack = 7.5%
maximum stacks = 4
maximum reduction = 30%
per-cast gate = 0.3 s
duration = 6 s

LDR outgoing bonus = 1% per 100 target bonus HP
LDR cap = 15% at 1500 target bonus HP

Hexoptics Magnification = 1% per 60 assumed units
Hexoptics cap = 10% at 600 units
assumed attack range = 175 / 525 / 625 by passive stage
```

Kraken reads target HP before the triggering attack frame. Terminus grants a
Dark stack after the triggering attack completes. Bloodletter is gated by cast
instance; E passive and fire wave are separate eligible instances.

### Energized, movement, and delayed effects

Fleet and Energized items share the scenario's ready state.

```text
Statikk Shiv proc       = 60 raw magic
Stormrazor proc         = 100 raw magic
Stormrazor MS           = +45% for 1.5 s
Rapid Firecannon proc   = 40 raw magic
Rapid Firecannon range  = +35%, capped at +150
Cosmic Drive MS         = +20 flat for 4 s

Stormsurge trigger      = 25% target maximum HP within 2.5 s
Stormsurge MS           = +25% for 1.5 s
Stormsurge Squall delay = 2 s
Squall raw magic        = 125 + 0.10 * AP

Hexplate ranged Overdrive AS = +35%
Hexplate ranged Overdrive MS = +14%
Hexplate melee Overdrive AS  = +50%
Hexplate melee Overdrive MS  = +20%
Overdrive duration = 8 s
Overdrive cooldown = 30 s
```

Movement windows recalculate Swiftmarch at each action. Delayed damage remains
in the result after a short combo ends.

### Critical strikes and cooldown modifiers

Random critical strikes use expected damage.

```text
expected crit modifier
  = (1 - crit chance) * 1
  + crit chance * total crit-damage modifier

Infinity Edge crit-damage bonus = +30 percentage points

Fiendhunter attacks after R = 3
Fiendhunter window = 8 s
Fiendhunter AS = +50%
Fiendhunter forced total-crit modifier = 0.80
Fiendhunter natural-crit true branch = 15%

Yun Tal trained crit cap = 25%
training per melee attack = 0.4%
training per ranged attack = 0.2%
Flurry AS = +30% for 6 s
Flurry cooldown = 30 s

Navori remaining Q/W/E cooldown after each attack
  = previous remaining cooldown * 0.85
```

Fiendhunter's natural-crit branch is weighted by natural crit chance. Yun Tal
starts trained unless its scenario option requests an untrained start.

### Other item damage

```text
Shadowflame threshold/multiplier = below 40% HP / 1.20
Gunblade base(level) = 175 + (253 - 175) * (clamp(level, 1, 20) - 1) / 17
Gunblade raw magic = Gunblade base(level) + 0.30 * AP
Gunblade base at level 19 = 257.588235
Gunblade base at level 20 = 262.176471
```

## Rune formulas

Runes that cannot affect this single-target calculation remain visual only.

### Precision

```text
Press the Attack:
  trigger stacks = 3
  proc raw adaptive = 40 at level 1 -> 160 at level 18
  proc raw adaptive at level 20 = 174.117647
  later-damage amplifier = 8%
  stacks stop accumulating while the amplifier is active
  maximum procs in one uninterrupted combo = 1

Lethal Tempo:
  maximum stacks = 6
  AS per stack = 6% melee / 4.8% ranged
  bolt base = 9..30 melee / 6..24 ranged
  bonus-AS ratio = 1.0% melee / 0.8333% ranged per 1% bonus AS

Fleet Footwork:
  MS = 20% melee / 15% ranged
  duration = 1 s

Conqueror:
  maximum stacks = 12
  attack stacks = 2 melee / 1 ranged
  damaging ability stacks = 2
  adaptive per stack = 1.08..2.4 AD or 1.8..4 AP
  max-stack healing = 8% melee / 5% ranged

Legend: Alacrity:
  AS = 3% + 1.5% * configured stacks
  maximum configured stacks = 10
  maximum AS = 18%

Legend: Haste:
  basic-ability haste = 1.5 * configured stacks
  maximum configured stacks = 15

Coup de Grace = +8% damage below 40% target HP
Cut Down      = +8% damage above 60% target HP

Last Stand:
  40% missing HP -> +5%
  50% missing HP -> +7%
  60% missing HP -> +9%
  70% missing HP or more -> +11%
```

PTA's proc frame does not amplify itself. Fire waves share their attack's cast
instance for Conqueror.

### Domination

```text
Electrocute raw adaptive = 70..240 + 0.10 * bonus AD + 0.05 * AP
Electrocute hit window = 3 s
Electrocute cooldown = 20 s

Dark Harvest raw adaptive
  = 30 + 11 * souls + 0.10 * bonus AD + 0.05 * AP
Dark Harvest threshold = below 50% target HP
Dark Harvest cooldown = 35 s

Relentless Hunter = 8 flat out-of-combat MS per stack
maximum Relentless stacks = 5

Hail of Blades AS = 120% melee / 60% ranged
base empowered attacks = 2
extra E-reset attacks = up to 2
raw true per empowered attack = 4..20 + 0.08 * bonus AD + 0.06 * AP
cooldown = 10 s

Cheap Shot raw true = 10..45
Cheap Shot cooldown = 4 s
```

Relentless movement speed ends on the first damage instance. Cheap Shot checks
for existing impairment before the action applies its own slow.

### Sorcery

```text
Aery raw adaptive = 10..50 + 0.10 * bonus AD + 0.05 * AP
Aery effective return cooldown = about 4 s

Comet raw magic = 15..100 + 0.10 * bonus AD + 0.05 * AP
Comet delay = 0.825 s
Comet cooldown = 20..8 s

Stormraider trigger = 25% target maximum HP within 3 s
Stormraider MS = 48% melee / 36% ranged
Stormraider duration = 4 s
Stormraider cooldown = 20..10 s

Deathfire tick raw magic
  = 1.5..6 + 0.035 * bonus AD + 0.0125 * AP
tick interval = 0.5 s
area burn = 2 s
single-target spell burn = 4 s
continuous-burn bonus after 3 s = +75%

Axiom Arcanist R amplifier = 8%

Absolute Focus = 3..30 AP or 1.8..18 AD over levels 1..18
active condition = current HP > 70%

Celerity personal MS = +1%
Celerity eligible-bonus multiplier = 1.07

Waterwalking = +10 flat MS
Waterwalking adaptive = 7.8..18 AD or 13..30 AP

Scorch raw magic = 20..40
Scorch delay = 1 s
Scorch cooldown = 10 s

Transcendence = +5 haste at level 5 and +5 at level 8

Gathering Storm AD by interval
  = [0, 4.8, 14.4, 28.8, 48, 72, 100.8, 134.4]
Gathering Storm AP by interval
  = [0, 8, 24, 48, 80, 120, 168, 224]
```

Comet assumes a point-blank hit. Nimbus Cloak is inactive because Summoner
Spells are not combo actions.

### Resolve and Inspiration

```text
Grasp trigger = attack at 4 combat stacks
Grasp stack rate = 1 per combat second
Grasp raw magic = 3.5% melee / 1.4% ranged of Kayle maximum HP
Grasp heal = 1.3% melee / 0.52% ranged of Kayle maximum HP

First Strike window = 3 s from first hit
First Strike bonus true = 7% of post-mitigation damage

Magical Footwear = +10 flat MS to equipped Boots

Approach Velocity total-MS multiplier = 7.5%
own impairment multiplier = 15%

Jack of All Trades:
  haste = 1 per unique supported stat type
  at 5 stat types = 3.6 AD or 6 AP
  at 10 stat types = 12 AD or 20 AP
```

Grasp gains combat stacks over time. Approach Velocity assumes Kayle moves
toward the impaired target. Unreachable conditions such as Aftershock and
Sudden Impact are visual only.

### Stat shards

```text
Adaptive Force = 5.4 AD or 9 AP
Attack Speed   = 10% bonus AS
Ability Haste  = 8 haste
Health         = 65 bonus HP
Scaling Health = 10..200 HP over levels 1..20
Movement Speed = 2.5%
Tenacity       = visual only
```

Scenario inputs cover game time, Kayle HP, rune stacks, item stacks, Energized
readiness, and river state. Haste changes cooldown validation and therefore
whether the entered sequence is accepted.

## Assumptions and exclusions

Deliberate normalizations:

- Q before E is treated as landed before E.
- Comet uses point-blank damage and is assumed to hit.
- Hexoptics uses current maximum attack range instead of target distance.
- Approach Velocity assumes movement toward the combo target.
- Random crit and crit-based cooldown reduction use expected values.
- Fleet's delayed movement update synchronizes before the next action.
- Cooldown-invalid Q/W/E/R actions are skipped by the engine and rejected by
  the UI with structured action-index feedback.

Not modeled:

- Mana gating and mana restoration.
- Shields and most defensive utility.
- Cryptbloom's takedown heal.
- Takedown-only range and reset effects.
- Statikk secondary targets and Stormsurge death-area damage.
- Zhonya invulnerability; stasis only advances time.
- Rylai slow magnitude; impairment state is retained.
- Transcendence takedown refund.
- Summoner Spells and Nimbus Cloak activation.

Modeled utility duration:

```text
Zhonya stasis timeline advance = 2.5 s
```

## Source and evidence links

- [Validation and backtesting](VALIDATION.md)
- [Data and icon sources](SOURCES.md)
- [Maintaining items](ITEM_MAINTENANCE.md)
