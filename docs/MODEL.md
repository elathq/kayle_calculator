# Simulation model

This document describes what the engine calculates, the ordering it uses, and
the assumptions it makes. It is intentionally separate from the
[validation record](VALIDATION.md): this file documents implementation behavior;
the validation record documents the evidence for that behavior.

## Scope and outputs

Each build receives the same Kayle level, ability ranks, target, scenario
options, and ordered combo. The engine advances a combat timeline and returns:

- exact total physical, magic, and true damage;
- whole-combo DPS using the completed timeline duration;
- the highest applied damage in any rolling one-second window;
- healing, kill time, and remaining target HP;
- final combat stats and penetration;
- every damage/note event in execution order; and
- warnings for cooldown or mutually exclusive item violations.

The engine simulates the combo as entered. A cooldown warning does not remove
an action because the tool is also used to isolate formulas and intentionally
illegal sequences.

## Precision and display rounding

There is one combat pipeline:

```text
raw damage
→ outgoing modifiers
→ resistance reduction
→ percentage penetration
→ flat penetration
→ mitigation
→ exact applied damage
```

No stage rounds damage. Fractional HP is retained for missing-health scaling,
threshold checks, subsequent hits, healing, totals, DPS, and burst. The UI may
format results for readability, but its event timeline exposes the exact raw
damage, effective resistance, and applied damage used by the simulation.

League's floating combat text, target HP display, and Practice Tool total are
independently rounded presentation values. They can disagree with each other by
one point without implying an integer-per-instance damage system. See
[Validation and backtesting](VALIDATION.md#practice-tool-validation-protocol).

## Champion progression and timing

- Kayle's base statistics use League's non-linear per-level growth formula.
- The supported level range is 1–20. Levels 19–20 represent the top-lane role
  quest and preserve the original per-level slope for level-scaled runes.
- Default ability order is E, Q, W, then Q > E > W, with R at levels 6, 11,
  and 16.
- Passive breakpoints occur at levels 1, 6, 11, and 16.
- Total attack speed is `0.625 + 0.667 × bonus AS / 100`, normally capped at
  2.50. Hail of Blades can exceed the normal cap while active.
- Attack speed determines attack spacing, combo duration, and DPS.
- R finishes its 0.5-second cast before the combo continues; its damage lands
  2.5 seconds after the cast begins.
- Delayed effects are resolved after the final user-entered action, including R,
  Stormsurge, Phantom Hit, Comet, Scorch, and burn ticks.

## Basic attacks, passive, and abilities

### Attack ordering

A normal attack resolves the applicable layers in this model:

1. Basic physical hit using total AD.
2. Item on-hit effects.
3. E's passive magic on-hit.
4. A primed Spellblade proc.
5. Kayle's passive fire wave while Aflame and Exalted.
6. A Rageblade Phantom Hit repeat when due.

Effects on the same game frame use the state captured for that frame. A damage
amplifier or resistance stack triggered by the frame begins affecting later
eligible damage, not earlier components retroactively.

### Fire wave

Fire-wave base damage is 20 through level 11 and increases by 3 per level from
level 12. It is 41 at level 18 and 47 at level 20. This is a breakpoint formula,
not a level-1-to-18 interpolation.

### Q — Radiant Blast

Q deals its own damage against the target's pre-hit resistance, then applies
15% armor and magic-resistance reduction for later damage. If Q appears before
E in the combo, the simulator assumes Q has already hit before E: Q damage,
shred, and missing-HP contribution all apply. Projectile distance and travel
time are intentionally not inputs.

### W — Celestial Blessing

W applies its rank- and AP-scaled heal and grants rank-based movement speed plus
8 percentage points per 100 AP for two seconds. Every later action recalculates
AP, movement speed, and Swiftmarch adaptive force at that action's timestamp.
Actions after the window expires lose the bonus automatically.

### E — Starfire Spellblade

The public combo has one E action and one formula. E is an empowered basic
attack and attack reset: it includes the physical hit and one normal on-hit
package, then applies its missing-health damage.

- E primes and may immediately consume Spellblade.
- At level 11+, its explosion does not create another PTA application or a
  second normal on-hit package.
- Its missing-health percentage gains 1.5 percentage points per 100 AP.
- Without Rageblade, missing-health damage reads the target state before the
  empowered attack.
- With Rageblade, it reads after E's physical hit.
- When the fast reset triggers Phantom Hit, it reads after the physical hit and
  normal on-hit package. The Phantom repeat remains a separate later event.
- Same-frame damage is not amplified by the PTA proc that frame triggers.

The waited Rageblade ordering observed during validation remains an internal
regression case, not a second UI action.

### R — Divine Judgment

R uses its area-of-effect damage formula and delayed impact. R-triggered item
effects such as Experimental Hexplate and Fiendhunter begin from the modeled R
cast trigger, while the R damage event lands later.

## Target state, resistance, and penetration

Maximum HP, starting HP, and bonus HP are separate target inputs:

- maximum HP controls thresholds and percentage-of-maximum conditions;
- starting/current HP controls live missing-health damage and kill state; and
- bonus HP controls Lord Dominik's Regards.

Resistance resolution is:

1. Q and Bloodletter percentage reductions.
2. Percentage penetration, including Terminus.
3. Flat penetration.
4. The resistance multiplier.

For non-negative resistance, mitigation uses `100 / (100 + resistance)`.
Negative resistance uses League's separate negative-resistance curve. Effective
resistance and damage remain fractional.

Shadowflame crit multiplies eligible magic and true damage by 1.2 only when the
target is strictly below 40% maximum HP at the frame snapshot. Crossing the
threshold during a multi-component frame does not retroactively change the
other components on that frame.

## Adaptive force and movement speed

Adaptive effects become AD/physical when item AD is greater than item AP;
otherwise they become AP/magic. One point of adaptive force grants 1 AP or 0.6
AD. A zero-item-AD/zero-item-AP tie resolves to AD for Kayle, matching the Rapid
Firecannon Practice Tool isolation. Rabadon's multiplies AP produced by adaptive
effects.

Movement speed is calculated in this order:

1. Base movement speed plus flat bonuses.
2. Additive percentage bonuses.
3. Multiplicative total-movement-speed bonuses.
4. League's 415 and 490 soft caps.

Celerity grants 1% movement speed and makes eligible flat, additive, and
multiplicative bonuses 7% stronger. Magical Footwear adds 10 flat movement speed
to Boots. Waterwalking adds 10 flat movement speed and level-scaled adaptive
stats while the river option is enabled. These effects, the movement-speed
shard, Relentless Hunter, Fleet, Stormraider's Surge, Approach Velocity, W, item
passives, and item actives feed the same timestamped calculation.

Swiftmarch grants 65 movement speed and adaptive force equal to 5% of current
displayed movement speed after the soft caps. It therefore recalculates during
W, Fleet, Stormrazor, Cosmic Drive, Stormsurge, and Experimental Hexplate
windows. The mid-lane role quest also multiplies all bonus AD and AP by 1.08 and
is activated only by an equipped evolved mid-lane boot.

Swiftmarch and Spellslinger's Shoes are illegal at levels 19–20 because those
levels require the mutually exclusive top-lane quest. The engine ignores the
illegal evolved boot and returns a warning.

Fleet's visible movement-speed update is delayed by approximately 0.1 seconds
in the measured interaction. When Fleet is selected, the engine automatically
synchronizes that update before the next user action. There is no public wait
utility solely for Fleet synchronization.

## Item mechanics

### Item families

The engine applies a maximum of one item from each registered exclusive family,
including Boots, Starter, Spellblade, Blight, and Fatality. Extra conflicting
items are ignored with a warning. The UI permits six item slots but cannot make
an otherwise illegal family combination valid.

### Boots and magic penetration

- Sorcerer's Shoes: 12 flat magic penetration.
- Spellslinger's Shoes: 18 flat and 8% magic penetration, plus the mid-role
  quest reward.
- Swiftmarch: 65 movement speed, 5%-of-current-MS adaptive force, and the
  mid-role quest reward.

### Spellblade

An ability primes Spellblade; the next attack consumes it subject to a
1.5-second internal cooldown. Lich Bane grants 50% attack speed while primed.
Dusk and Dawn deals Spellblade damage, heals, and repeats on-hit effects once,
including a PTA application. Essence Reaver deals physical Spellblade damage
equal to 125% base AD plus 0.5% base AD per percentage point of total critical
strike chance. Mana restoration is not modeled.

### Rageblade

Rageblade builds Seething stacks and begins Phantom Hit after two attacks made
while already at maximum stacks. From zero stacks, the first Phantom Hit is on
attack 7 and later repeats are on attacks 10, 13, and so on. Phantom Hit
reapplies the eligible on-hit package after its modeled delay.

### Extended-fight and penetration items

- Riftmaker converts 2% bonus HP to AP, gains 2% damage per whole second after
  entering champion combat up to 8%, and enables 10% melee / 6% ranged
  omnivamp at maximum stacks.
- Kraken Slayer procs every third on-hit application. It reads target missing
  HP at the start of the triggering attack's damage frame.
- Terminus starts with Light and alternates Light/Dark. Dark grants 10% armor
  and magic penetration after attacks 2, 4, and 6, reaching 30%; a triggering
  fire wave still uses the prior stack count.
- Bloodletter's Curse applies one 7.5% MR-reduction stack per eligible cast
  instance, up to 30%, subject to its 0.3-second gate. E passive and fire wave
  are separate eligible instances, while same-frame damage uses the prior
  frame's stack count.
- Lord Dominik's Regards gains 1% damage per 100 target bonus HP, capped at 15%
  for 1500 bonus HP.

### Energized and movement items

Fleet, Statikk Shiv, Stormrazor, and Rapid Firecannon share the “Energized
effects start ready” scenario control.

- Statikk deals one 60-magic-damage champion proc; secondary targets are not
  simulated.
- Stormrazor deals 100 magic damage and grants its movement-speed window.
- Rapid Firecannon deals 40 magic damage and grants 35% bonus range capped at
  +150 for that Energized attack.
- Cosmic Drive grants 20 flat movement speed for four seconds after eligible
  magic or true damage.
- Stormsurge tracks 25% target-maximum-HP damage within 2.5 seconds, grants its
  movement window, and resolves Squall two seconds later even if the entered
  combo has ended.
- Experimental Hexplate grants ranged Kayle 35% attack speed and 14% movement
  speed for eight seconds after R. Its 50%/20% values are melee-only.

All active movement windows feed Swiftmarch at the action timestamp.

### Critical strikes and attack modifiers

Random item critical-strike chance is represented as expected damage so build
comparisons are repeatable. Infinity Edge adds 30 percentage points to total
critical damage. Kayle's basic hit and fire wave share the expected modifier.

Fiendhunter's first three attacks after R gain 50% attack speed and use its
separate 80%-total-crit rule. Attacks that naturally crit use full critical
damage and add 15% true damage; the simulator weights that branch by natural
crit chance. Yun Tal starts fully trained by default; its option can start it at
zero and add 0.4% crit per melee or 0.2% per ranged attack, capped at 25%.

### Cooldown and range mechanics

- Navori reduces live remaining Q/W/E cooldowns by 15% on every attack,
  including E.
- Yun Tal's six-second Flurry grants 30% attack speed; attacks reduce its
  cooldown using expected critical-strike probability.
- Hexoptics assumes attacks occur at Kayle's current maximum attack range
  (175/525/625), capped by its 600-unit/10% formula. A ready Rapid Firecannon
  extends that assumed range for its Energized attack only.

## Rune model

Each build can select a keystone, three primary runes, two secondary runes from
different rows, and one shard from each row. Runes that cannot affect this
single-target damage simulation remain selectable but contribute no hidden
combat math.

### Precision

- Press the Attack receives on-hit stacks from eligible repeats. Its third-hit
  proc frame does not amplify itself; the 8% amplifier affects later damage.
- Lethal Tempo adds 6% melee / 4.8% ranged attack speed per stack, up to six
  stacks. Its bolt increases by 1% per 1% bonus AS for melee and approximately
  0.8333% per 1% bonus AS for ranged Kayle.
- Fleet Footwork grants 20% melee / 15% ranged movement speed for one second
  and therefore can alter Swiftmarch adaptive force.
- Conqueror grants one stack per ranged attack, two per melee attack, and two
  per damaging ability cast. A fire wave belongs to the attack's cast instance
  and does not add a separate stack. Maximum-stack healing uses 8% melee / 5%
  ranged post-mitigation damage.
- Legend: Alacrity grants 3% attack speed plus 1.5% per configured stack, up to
  18%. Legend: Haste reads the same configured stack count separately.
- Coup de Grace grants 8% damage below 40% target HP; Cut Down grants 8% above
  60% target HP. Last Stand grants 5% at 40% missing HP, scales linearly to 11%
  at 70% missing HP, and then remains capped.

### Domination

- Electrocute and Dark Harvest use their modeled hit/soul conditions.
- Relentless Hunter grants 8 flat out-of-combat movement speed per configured
  stack, up to five, and falls off on the first damage instance.
- Hail of Blades grants 120% melee / 60% ranged attack speed and can exceed the
  normal 2.5 cap. E resets can add up to two extra empowered attacks.
- Cheap Shot checks whether the target was already impaired before the action's
  own slow. Q, Rylai, and Gunblade can supply impairment.

### Sorcery

- Summon Aery uses an approximately four-second effective travel cooldown.
- Arcane Comet is assumed to hit at point-blank values.
- Stormraider's Surge triggers after dealing 25% target maximum HP within three
  seconds and grants 48% melee / 36% ranged movement speed for four seconds.
- Deathfire Touch treats Q, R, and fire waves as area damage, burns for two
  seconds, ticks every 0.5 seconds, and gains 75% damage after three seconds of
  continuous burning.
- Axiom Arcanist applies its 8% area-ultimate value to R.
- Absolute Focus scales from 3–30 AP or 1.8–18 AD over levels 1–18, preserves
  that slope at top-quest levels 19–20, and is active only while Kayle is
  strictly above 70% HP.
- Celerity, Waterwalking, Gathering Storm, Scorch, and Transcendence use their
  configured level, time, location, and health inputs.
- Nimbus Cloak remains inactive because Summoner Spells are not combo actions.

### Resolve and Inspiration

- Grasp gains one combat stack per second and procs on an attack at four
  stacks.
- First Strike opens a three-second window from the first hit and adds 7% of
  post-mitigation damage as true damage.
- Magical Footwear adds 10 flat movement speed to an equipped Boots upgrade.
- Approach Velocity applies a 7.5% total-movement-speed multiplier toward an
  impaired target, doubled to 15% when Kayle supplied the impairment. The
  simulator assumes Kayle faces the combo target.
- Jack of All Trades counts unique supported item-stat types and grants its
  threshold stats.
- Conditions Kayle cannot trigger, such as Aftershock and Sudden Impact, are
  visual only.

### Stat shards and configuration

- Adaptive Force: 5.4 AD or 9 AP.
- Attack Speed: 10% bonus attack speed.
- Ability Haste: 8 haste.
- Health: 65 bonus HP.
- Scaling Health: 10–200 HP across levels 1–20.
- Movement Speed: 2.5% movement speed.
- Tenacity/slow resistance is visual only in this damage model.

Scenario inputs include game time, Kayle HP percentage, Dark Harvest souls,
Dark Seal stacks, Legend stacks, Relentless Hunter stacks, Energized readiness,
and whether the fight occurs in the river.

Haste affects cooldown warnings, not the execution of the fixed combo. Legend:
Haste supplies 1.5 basic-ability haste per configured stack. Transcendence
grants 5 ability haste at levels 5 and 8; its level-11 takedown refund is not
modeled.

## Explicit assumptions and exclusions

### Deliberate normalizations

- A Q placed before E is treated as having hit before E, independent of
  projectile travel distance.
- Comet uses point-blank damage and is assumed to hit.
- Hexoptics uses Kayle's current maximum attack range instead of a distance
  input.
- Approach Velocity assumes Kayle is moving toward the impaired combo target.
- Random critical strikes and expected-crit cooldown reduction use expected
  values.
- Fleet's measured delayed movement update is synchronized automatically before
  the following action.
- Cooldown-invalid actions remain in the simulation and generate warnings.

### Not modeled

- Mana costs, mana restoration, and mana-gated casts.
- Shields and most non-damage defensive utility.
- Cryptbloom's takedown heal.
- Takedown-only range/reset behavior from Hexoptics and Fiendhunter.
- Statikk's secondary chain targets and Stormsurge's nearby-enemy death AoE.
- Zhonya's invulnerability; stasis advances the timeline by 2.5 seconds only.
- Rylai's slow magnitude; its impairment state is modeled where relevant.
- Transcendence's level-11 takedown cooldown refund.
- Summoner Spells and therefore Nimbus Cloak activation.

## Where values come from

External formulas, item/rune pages, patch notes, and asset provenance are listed
in [Data and icon sources](SOURCES.md). In-game measurements and exact simulator
comparisons are in [Validation and backtesting](VALIDATION.md). When those
sources disagree, the conflict and chosen behavior should be recorded in the
validation document rather than silently resolved in code.
