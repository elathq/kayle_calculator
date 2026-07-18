# Validation and backtesting

This is the single canonical validation document for the Kayle damage
simulator. It combines the repeatable Practice Tool protocol, recorded in-game
measurements, exact simulator comparisons, automated regression coverage, and
known evidence gaps.

It deliberately separates what was observed in League from what came from a
published source or simulator assumption. The implemented behavior itself is
documented in the [simulation model](MODEL.md), and external references are
listed in [data and icon sources](SOURCES.md).

## Evidence labels

| Label | Standard used in this document |
|---|---|
| Practice Tool-confirmed | A controlled in-game isolation reproduced the relevant components or aggregate result. |
| Source-confirmed | Riot data, Riot patch notes, or the League Wiki provides the rule; automated coverage exists, but a controlled in-game capture is still missing. |
| Simulator assumption | The game permits ambiguous timing or spatial outcomes, so the calculator uses one explicitly documented normalization. |
| Inconsistent capture | Recorded fields conflict or did not reproduce; the observation is retained for transparency but is not a regression target. |
| Not modeled | The behavior is intentionally outside the current single-target damage scope. |

## Validation status

| Area | Status | Evidence |
|---|---|---|
| Full-precision damage pipeline | Practice Tool-confirmed | Practice Tool totals, displayed HP changes, and 74 automated tests |
| Basic attacks, E, PTA, fire waves | Practice Tool-confirmed | Direct Practice Tool isolation |
| Q damage, shred, penetration, Shadowflame crit | Practice Tool-confirmed | Direct Practice Tool isolation across several resistance and HP setups |
| Rageblade stacks, Phantom Hit, fast E reset | Practice Tool-confirmed | Direct Practice Tool isolation through attacks 4–10 and a two-dummy test |
| R, Gunblade, Lich Bane, Dusk and Dawn | Practice Tool-confirmed | Direct Practice Tool isolation |
| Last Stand curve | Source-confirmed | League Wiki screenshot and automated boundary tests; own-health Practice Tool test was not possible |
| W, movement-speed stacking, Swiftmarch adaptive force | Source-confirmed and regression-tested | Wiki values plus automated timing/layer tests |
| Boots, starter items, default skill order, Absolute Focus | Source-confirmed and regression-tested | Wiki/Riot references plus automated tests |
| Essence Reaver, Experimental Hexplate, Kraken Slayer, Terminus, Bloodletter's Curse, Riftmaker, Rapid Firecannon, Statikk Shiv, and Stormrazor | Practice Tool-confirmed | Direct Practice Tool isolation plus fixed automated regression targets |

The fixture is labelled Data Dragon `16.14.1`. The exact live Practice Tool
patch was not written down during the first capture, so the fixture deliberately
retains the status `patch confirmation pending` instead of overstating certainty.

## Practice Tool validation protocol

Use this protocol for every fresh patch pass and every new mechanic. Do not
merge timing-dependent outcomes into an average; preserve them as separate
observations.

### Before each pass

- Record the exact League patch, map, and date.
- Record Kayle's level, Q/W/E/R ranks, items, runes, shards, displayed AD, AP,
  attack speed, movement speed when relevant, maximum HP, and current HP
  percentage.
- Record the dummy's maximum HP, starting HP, bonus HP if relevant, armor, and
  magic resistance.
- State whether Zeal, PTA, Rageblade, Fleet, Energized, or another effect starts
  stacked or ready.
- Reset the dummy, cooldowns, and stacks between cases.

### For every sequence

1. Write the exact action order and every deliberate wait.
2. Record target HP immediately before and after the sequence.
3. Record the Practice Tool dummy total.
4. Record every floating damage number and its physical, magic, or true-damage
   color.
5. Record transient Kayle stats when the test concerns a timed buff.
6. Repeat at least three times and flag timing-dependent branches separately.
7. Compare the first differing event in the simulator timeline: raw damage,
   modifier, effective resistance, then applied damage. Aggregate totals can
   otherwise hide the cause.

Displayed values are rounded. Exact simulations should normally be compared
with roughly one point of presentation tolerance, while still requiring the
individual damage sources and ordering to make sense.

The simulator therefore keeps one full-precision path from raw damage through
modifiers and resistance to exact applied damage. There is no separate
integer-per-instance combat model.

### Baseline regression pass

Use the setup in `validation/practice_tool_cases.json` and record these four
sequences on a fresh target:

1. AA.
2. E.
3. AA → E.
4. AA → E → AA.

Enter newly confirmed observations in the JSON fixture, then run:

```text
python -B validation/backtest.py
python -B -m unittest discover -s tests -v
```

### Isolation order for changed mechanics

1. Basic attack and Q against 0, 50, 100, and 200 resistance.
2. Q followed by the same hit to verify that Q damages before applying shred.
3. Percentage penetration alone, flat penetration alone, then both together.
4. Shadowflame crit with an action beginning above and below 40% target HP.
5. E against full and reduced target HP.
6. PTA, Spellblade, and Rageblade independently before combining them.
7. W followed by actions around the two-second expiry when testing Swiftmarch
   or movement-speed effects.
8. On-hit items one at a time: Wit's End; Statikk attacks 1–4; Stormrazor and
   Rapid Firecannon with one preloaded Energized attack; Kraken attacks 1–3;
   Terminus attacks 1–7; and Bloodletter eligible hits 1–4.
9. R-triggered and cooldown items independently: Experimental Hexplate inside
   and outside eight seconds; Fiendhunter R followed by four attacks; Essence
   Reaver ability → attack; Yun Tal from zero crit stacks; Navori Q → attacks →
   Q.
10. Extended timing: Riftmaker at 0/1/2/3/4 seconds and Cosmic Drive,
    Stormrazor, Fleet, or Stormsurge immediately before and after expiry.
11. Crit items with natural crit and non-crit samples recorded separately. The
    simulator reports the weighted expected value, not one random outcome.

## Baseline four-case fixture

The reproducible fixture is stored in
`validation/practice_tool_cases.json` and can be checked with:

```text
python -B validation/backtest.py
```

Setup:

- Level 12 Kayle; Q 5, W 0, E 5, R 2.
- Nashor's Tooth, Dusk and Dawn, Rabadon's Deathcap.
- Press the Attack, Presence of Mind, Legend: Alacrity, Last Stand; Manaflow
  Band and Celerity.
- Attack-speed, adaptive-force, and scaling-health shards.
- Kayle at 100% HP, Legend stacks 0, no starting Zeal or Rageblade stacks.
- Dummy: 3500 maximum/current HP, 100 armor, 100 magic resistance.
- Displayed Kayle stats: 75 AD, 363 AP, 1.277 attack speed, 1996 maximum HP.

Current backtest output:

| Case | Dummy total | Displayed HP delta | Exact simulation | Difference vs dummy total |
|---|---:|---:|---:|---:|
| AA | 126 | 125 | 125.78 | -0.22 |
| E | 260 | 260 | 260.37 | +0.37 |
| AA → E | 455 | 454 | 454.68 | -0.32 |
| AA → E → AA | 591 | 590 | 590.52 | -0.48 |

Recorded floating numbers:

| Case | Physical | Magic |
|---|---|---|
| AA | 37 | 88 |
| E | 37 | 134 + 88 |
| AA → E | 37 + 37 | 88 + 144 + 147 |
| AA → E → AA | 37 + 37 + 40 | 88 + 144 + 147 + 95 |

These cases establish the basic physical hit, normal on-hit package, E reset,
Dusk and Dawn repeat, PTA stacking, and the post-proc PTA amplification.

## Confirmed combat findings

### Press the Attack

With Dusk and Dawn removed, Nashor's Tooth plus Rabadon's Deathcap produced:

| Sequence | Exact simulation | Practice Tool | Important floating number |
|---|---:|---:|---|
| 3 AA | 395.21 | 395 damage; HP 3500 → 3105 | Third hit: 37 physical + 133 magic |
| 4 AA | 516.31 | 516 damage; HP 3500 → 2984 | Fourth hit: 40 physical + 80 magic |

At level 12, PTA contributes 117.6471 raw damage and 58.8235 after 100 MR.
The third attack procs it; the 8% vulnerability affects later damage, not the
same frame that triggered PTA. Level-scaled rune values preserve their original
level-1-to-18 slope through top-quest levels 19 and 20. PTA therefore reaches
174.1176 raw damage at level 20 instead of clamping at its level-18 value.

### Kayle fire wave and top-quest levels

The fire wave is breakpoint-scaled: 20 base damage through level 11, then +3
per level from level 12. This gives 41 at level 18 and 47 at level 20.

| Level | Observed attacks | Result |
|---:|---|---|
| 18 | First two: 56 wave + 74 on-hit magic + 46 physical; third: 56 + 154 magic + 46 physical | HP 3500 → 2889 |
| 20 | First two: 59 wave + 74 on-hit magic + 49 physical; third: 59 + 161 magic + 49 physical | One capture recorded HP 3500 → 2868; see note below |

A clean level-20 attack showed 59 magic + 74 magic + 49 physical, 183 dummy
total, and HP 3500 → 3317. The simulator gives 183.49 exact damage. The current
three-attack simulation gives 637.53. The recorded level-20 component text sums
to about 633 after display rounding and supports the level-20 PTA value, but the
recorded final HP of 2868 implies several points less damage than the exact
model. Because those two fields conflict, the 2868 entry is retained
as a transcription/capture inconsistency and is not used as a regression target.

### Q damage, shred, and penetration order

Q alone matched at 0, 50, 100, and 200 MR. Q deals its own damage against the
pre-hit resistance, then applies 15% armor and MR reduction for later hits.
The confirmed order is:

1. Q's 15% resistance reduction.
2. Percentage penetration, such as Void Staff or Spellslinger's Shoes.
3. Flat penetration, such as Shadowflame or Sorcerer's Shoes.
4. Damage mitigation using the resulting effective resistance.

Void Staff alone, Shadowflame alone, and the two together all matched Q → AA
Practice Tool tests.

### Shadowflame crit threshold

The project calls this mechanic **Shadowflame crit**. It is active only when
the target is strictly below 40% maximum HP at the snapshot for a damage frame.
Crossing below 40% during a multi-component frame does not retroactively crit
the other components in that frame.

On a 1200-HP dummy, four attacks left the target above the threshold and Q dealt
212 displayed magic damage. After five attacks, the target was at 404 HP; Q then
crit for 255, leaving 149 HP and 1052 dummy total.

### Q → E ordering policy

The game can resolve an immediate point-blank E before Q's projectile impact:

| Execution | Observed total |
|---|---:|
| Q allowed to hit, then E | 295 |
| Point-blank Q and immediate E | 285 |
| Maximum E range, immediate E | 273 |

These are projectile-timing variations, not three E formulas. The simulator has
one E action and intentionally assumes that a Q placed before E has already hit,
applied its shred, and contributed to missing health. Target distance is not an
input.

### E missing-health snapshot

With level-12 Kayle, Nashor's Tooth, Rabadon's Deathcap, Fleet Footwork, and a
1000-HP/100-resistance dummy, AA → AA → AA → E showed 664 HP before E, 473
total damage, and 528 HP after. E displayed 37 physical + 98 magic.

The exact simulation is 472.52 damage and 527.48 remaining HP. Without
Rageblade, E reads missing health from the pre-attack target state. The exact
pre-E HP was 663.6138; the missing-health component was 48.004 raw and 24.002
after MR.

### Rageblade and Phantom Hit

With Nashor's Tooth, Guinsoo's Rageblade, and Rabadon's Deathcap from zero
stacks:

- Four and five attacks matched.
- Six attacks dealt 1010 and left 2491 HP; there was no Phantom Hit on attack 6.
- Seven attacks dealt 1312 and left 2189 HP; the first separate Phantom Hit was
  98 magic.
- The confirmed continuing cadence is attacks 7, 10, 13, and so on.

Attack 4 reaches maximum Seething stacks. Attacks 5 and 6 are the first two
attacks while already at maximum, so attack 7 is the first Phantom Hit.

### Rageblade plus E reset timing

The following observations isolate a real timing-sensitive interaction:

| Sequence | Execution | Total / final HP | Finding |
|---|---|---|---|
| 4 AA → E | Immediate | 854 / 2646 | E is attack 5; no Phantom Hit; missing HP is read after E's physical hit |
| 6 AA → E | Brief wait | 1391 / 2110 | Phantom-triggering E reads after its physical hit |
| 6 AA → E | Fast reset | 1398 / 2103 | Read occurs after physical plus normal on-hit package |
| Target switch on attack 7 | Brief wait / fast | 306 / 313 on dummy B | Removes accumulated missing HP and confirms the 7-damage ordering difference |
| 9 AA → E | Immediate | 2161 / 1340 | Same fast ordering on attack 10; exact simulation 2160.51 |

The later 98-magic Phantom Hit remains a separate repeated on-hit package. The
public combo builder exposes only one E button and uses the fast attack-reset
behavior. A waited E path remains only as an internal regression case so this
observed edge case is not lost.

### Dusk and Dawn cooldown

At level 12 with Nashor's Tooth, Dusk and Dawn, Rabadon's Deathcap, and Fleet
Footwork, Q → AA → immediate E produced:

- 3320 HP after Q.
- 3038 HP after the Spellblade attack.
- 2864 final HP.
- 637 dummy total versus 636.70 exact simulation.

Only the first attack consumes Dusk and Dawn because immediate E occurs inside
its 1.5-second Spellblade cooldown. Controlled 0.5-second waits reproduced 637
with Dusk and Dawn and 425 without it. Earlier 622 and 416 readings did not
reproduce and are excluded as inconsistent captures, not separate mechanics.

### Lich Bane

At level 12 with Nashor's Tooth, Lich Bane, Rabadon's Deathcap, and 414.7 exact
AP, clean E showed 37 physical + 218 magic, 256 dummy total, and 3244 remaining
HP. Lich Bane's exact post-mitigation Spellblade contribution was 121.2872.

### Divine Judgment

At level 12 with rank-2 R, Nashor's Tooth, Rabadon's Deathcap, 284.7 exact AP,
and a 100-MR dummy, R showed 249 magic, 250 dummy total, and HP 3500 → 3251.
The exact simulation is 249.645.

### Hextech Gunblade

At level 12 with Gunblade, Rabadon's Deathcap, 284.7 exact AP, and a 100-MR
dummy, the active showed 155 magic, 155 dummy total, and HP 3500 → 3345. The
exact simulation is 155.4403.

The supplied level-scaling references give 257.59 base damage at level 19 and
262.18 at level 20. These values continue the original level-1-to-18 slope;
they do not reinterpret level 20 as the old endpoint.

## Source-confirmed findings with automated coverage

### Last Stand

The Practice Tool did not provide a usable way to reduce Kayle's own HP for a
controlled test. The implemented linear curve follows the supplied wiki data:

| Missing HP | Current HP | Damage increase |
|---:|---:|---:|
| 40% | 60% | 5% |
| 50% | 50% | 7% |
| 60% | 40% | 9% |
| 70% or more | 30% or less | 11% |

It affects true damage except Smite. Automated tests cover all four brackets.

### W, movement speed, and Swiftmarch

W grants its rank-based percentage movement speed plus 8% per 100 AP for two
seconds. Each later action recalculates current AP and movement speed at its own
timestamp. Swiftmarch then grants adaptive force equal to 5% of final displayed
movement speed.

The tested stacking order is base plus flat movement speed, additive percentage
bonuses, multiplicative bonuses, and the 415/490 soft caps. Celerity strengthens
eligible bonuses; Magical Footwear, Waterwalking, the movement-speed shard,
Relentless Hunter, Fleet, Stormraider's Surge, Approach Velocity, and W feed the
same model. Nimbus Cloak stays inactive because the combo system has no Summoner
Spell actions. Regression tests confirm the W two-second window and that Fleet
feeds Swiftmarch only after its delayed movement-speed update. Selecting Fleet
now synchronizes that 0.1-second update automatically before the following
action; the public combo builder needs no Wait utility and keeps one E formula.

### Progression, starters, and boots

- Default ability order is E, Q, W, then Q > E > W, with R at 6/11/16.
- Absolute Focus scales linearly from 3 to 30 AP or 1.8 to 18 AD over levels
  1–18 and is active only above 70% HP. The same slope continues at levels 19–20.
- Builds accept a maximum of one Starter item and one Boots item.
- Boots, Sorcerer's Shoes, Spellslinger's Shoes, Swiftmarch, Doran's Ring,
  Doran's Bow, Doran's Blade, and Dark Seal have automated stat/application
  coverage. Dark Seal Glory is configurable and capped at 10.
- The mid-lane role quest multiplies bonus AD and AP by 1.08. Its upgraded
  boots, Swiftmarch and Spellslinger's Shoes, are rejected at levels 19-20
  because those levels require the mutually exclusive top-lane role quest.

### Current item expansion (source-confirmed, isolation in progress)

The calculator now includes Cosmic Drive, Riftmaker, Kraken Slayer, Terminus,
Infinity Edge, Bloodletter's Curse, Hexoptics C44, Phantom Dancer, Lord
Dominik's Regards, Wit's End, Statikk Shiv, Stormrazor, Fiendhunter Bolts, and
Rapid Firecannon. Experimental Hexplate, Essence Reaver, Yun Tal Wildarrows,
and Navori Flickerblade were subsequently added from the same live sources.
Stormsurge was added on July 18 with its current 90 AP, 15 flat magic
penetration, 6% movement speed, Stormraider window, and delayed Squall model.
Their current SR IDs, base stats, formulas, icons, and shop-family restrictions
were checked against the live wiki pages and Riot Data Dragon 16.14.1.

Automated isolation covers the following implementation rules:

- Cosmic Drive and Stormrazor movement windows immediately recalculate
  Swiftmarch adaptive force.
- Stormsurge accumulates damage over 2.5 seconds, applies its 1.5-second
  movement window at 25% target maximum HP, feeds that movement into
  Swiftmarch, and resolves Squall two seconds later even if the user-entered
  combo has already ended; no Wait action is required. If the tracked target
  is already dead, its nearby-enemy AoE is documented but omitted from this
  single-target calculation.
- Riftmaker converts 2% bonus HP to AP, adds 2% damage per whole second in
  champion combat up to 8%, and enables its maximum-stack omnivamp.
- Kraken procs every third on-hit application, uses ranged/melee level scaling
  through top-quest level 20, and reads live target missing HP.
- Terminus begins with Light, alternates Dark, and reaches 30% armor and magic
  penetration after three Dark hits. Bloodletter applies 7.5% MR reduction per
  eligible cast instance, up to 30%, with its 0.3-second gate.
- LDR reads the explicit target bonus-HP input. Wit's End deals 45 magic on-hit.
  Statikk supplies one preloaded 60-magic Energized proc when the scenario
  option is enabled. Stormrazor similarly supplies one preloaded 100-magic
  Energized proc. Rapid
  Firecannon stacks on the same Energized attack for 40 magic and extends the
  assumed attack range by 35%, capped at +150.
- Standard crit chance uses expected damage. Infinity Edge changes total crit
  damage; Fiendhunter separately models the three post-R attacks, their 50% AS,
  80%-total-crit rule, and expected natural-crit true-damage branch.
- Hexoptics has no distance control by design. It assumes Kayle attacks at her
  current maximum attack range and caps Magnification at 600 units / 10%.
- Experimental Hexplate applies its R-triggered ranged 35% AS / 14% MS
  Overdrive for eight seconds, including the Swiftmarch interaction. The
  50% AS / 20% MS profile is melee-only. Essence Reaver uses its
  crit-scaled physical Spellblade formula and the existing Spellblade limit.
- Yun Tal supports fully trained and zero-stack starts, ranged/melee crit gains,
  its Flurry AS window, and expected-crit cooldown reduction. Navori attacks
  reduce the live remaining Q/W/E cooldown by 15%.

These are source-backed and regression-tested. Essence Reaver, Experimental
Hexplate, Kraken Slayer, Terminus, Bloodletter's Curse, Riftmaker, Rapid
Firecannon, Statikk Shiv, and Stormrazor additionally have the following direct Practice
Tool isolation record; the other items are not labeled as Practice
Tool-confirmed yet.

### July 17 Practice Tool item isolation

**Essence Reaver, level 20 top-lane setup (no Swiftmarch):** displayed AD was
155 with 25% crit and one adaptive-force shard. A non-critical clean attack
changed the dummy from 3500 to 3377 and displayed 26 magic + 20 magic + 77
physical (dummy total 124). After W primed Spellblade, the non-critical attack
changed the dummy to 3308 and displayed 26 magic + 20 magic + 145 physical
(dummy total 192). The extra 68 displayed physical damage confirms Essence
Reaver's physical Spellblade branch and that the adaptive shard is included.

**Experimental Hexplate + Swiftmarch, level 18 mid-lane setup:** before R,
Practice Tool displayed 156 AD (93 base + 63 bonus), 1.225 attack speed, 435
movement speed, and a 61.54-second R cooldown. During Overdrive it displayed
157 AD (93 base + 65 bonus), 1.459 attack speed, and 478 movement speed. The
0.234 attack-speed increase is Kayle's 0.667 AS ratio times the ranged 35%
bonus. The absolute AS readings include one 1.5% Legend: Alacrity stack; with
zero stacks the paired simulator readings are 1.215 and 1.449, preserving the
same Hexplate delta. The movement-speed result matches ranged 14% after
League's soft caps.
The AD results also confirm the mid-role quest's 8% bonus-AD/AP multiplier and
Swiftmarch recalculating its 5%-of-current-movement-speed adaptive force during
Overdrive. These exact states are now automated regression targets.

**Kraken Slayer, level 18 top-lane setup:** with one adaptive-force shard, the
attack-speed shard, and zero Legend stacks, Practice Tool displayed 143 AD and
1.349 attack speed. Three normal attacks changed a 3500-HP, 100-armor/100-MR
dummy to 3073 HP; the dummy total displayed 428. Attacks one and two displayed
43 magic + 71 physical. Attack three displayed 43 magic + 155 physical. The
third physical number combines the normal attack with Bring It Down. This
proved that Kraken reads target missing HP at the start of the triggering
attack's damage frame, before that attack's own physical damage. The corrected
full-precision result is 427.40 damage / 3072.60 remaining HP; the observed 428
and 3073 are the dummy's independent integer displays.

The follow-up `AA -> AA -> E` test changed the dummy to 3060 HP with 440 on its
total counter. The first two attacks each displayed 23 magic + 20 magic + 71
physical; E displayed 23 magic + 32 magic + 155 physical. This confirms that E
is an on-hit application, consumes the third Kraken stack, and combines its
normal physical hit with Bring It Down in the 155 display. The exact simulator
result is 438.84 / 3061.16. The isolated floating components match; the roughly
one-point difference in each aggregate integer field is retained as display
rounding uncertainty rather than used to alter the full-precision pipeline.

**Terminus, level 18:** Practice Tool displayed 128 AD and 1.315 attack speed.
Seven continuous attacks changed the 3500-HP, 100-armor/100-MR dummy to 2596
HP with 904 on its total counter. The physical sequence was 63, 63, 67, 67,
71, 71, 75; the two magic groups were 22+34, 22+34, 23+36, 23+36, 24+38,
24+38, and 26+40. This confirms that Dark grants 10% armor and magic
penetration after attacks 2, 4, and 6. Crucially, each triggering attack's fire
wave still uses the previous stack count; the next attack is the first to use
the new penetration. Correcting that order changed the simulator result from
908.08 to 904.15 damage / 2595.85 HP, matching both Practice Tool aggregates.

**Bloodletter's Curse, level 18:** Practice Tool displayed 93 AD, 80 AP, and
1.082 attack speed. Four attacks changed the dummy from 3500 to 3067 HP with
433 on its total counter. The magic groups progressed 30+25, 32+27, 35+29,
and 35+29 while physical damage remained 46. This proves that Kayle's E
passive and fire wave are separate eligible cast instances and add two Vile
Decay stacks per attack. Both magic components snapshot the prior frame's MR:
attack 1 uses 100 MR, attack 2 uses two stacks / 85 MR, and attacks 3-4 use the
four-stack cap / 70 MR.

The 80 AP must not be treated as an independent mid-role quest switch. The user
confirmed that the 8% reward activates only while an evolved mid-role boot is
equipped. Bloodletter (65 AP) plus one adaptive shard (9 AP) is 74 AP without
such boots; the exact no-boot simulator result is 427.32 / 3072.68. The capture
therefore retains an unresolved evolved-boot or other AP-source detail until
that equipped boot is identified, while its Vile Decay ordering remains a
valid confirmed regression.

**Riftmaker, level 18 without evolved boots:** Practice Tool displayed 93 AD,
90 AP, and 1.082 attack speed. The AP is fully explained by the scaling-health
shard rather than a role quest: Riftmaker's 350 HP plus 180 shard HP gives 530
bonus HP, so `70 + 9 adaptive AP + (530 * 2%) = 89.6 AP`. Four attacks changed
the dummy from 3500 to 3077 HP with 424 on its total counter. The floating
groups were 31+26+46, 31+26+46, 32+26+47, and 32+27+48. This confirms that at
1.082 AS, attack 2 lands before one full combat second and remains at 0%;
attacks 3 and 4 use Riftmaker's 2% and 4% damage stages. The simulator gives
423.90 exact damage / 3076.10 HP. Every floating group and the 424 total match;
the final HP field differs by one independent display point.

The six-attack continuation displayed 61 magic + 49 physical on attack 5 and
62 magic + 49 physical on attack 6, with 647 on the dummy total. These are the
6% and capped 8% stages. The simulator produces 647.34 exact damage / 2852.66
HP and the same two floating groups, completing the Riftmaker ramp validation.

**Rapid Firecannon, level 18:** Practice Tool displayed 98 AD, 0 AP, 1.315
attack speed, and 25% crit. A charged non-critical attack changed Dummy A from
3500 to 3393 and displayed 58 magic + 48 physical. The immediately following
uncharged non-critical attack changed Dummy B to 3413 and displayed 20 magic +
17 magic + 48 physical. The 20-damage difference is exactly Rapid
Firecannon's 40 raw magic proc against 100 MR. This also confirmed that Kayle's
zero-item-AD/zero-item-AP adaptive tie resolves to AD: the shard produces 5.4
AD, giving 97.9 total AD / 0 AP. The simulator continues to use expected crit
damage for build comparisons; these observed non-critical branches validate
the underlying uncharged and charged components rather than replacing that
expected-value model.

**Statikk Shiv, level 18:** Practice Tool displayed 143 AD, 45 AP, and 1.282
attack speed. Four attacks changed the 3500-HP, 100-armor/100-MR dummy to
2972 HP with 528 on its total counter. Attack one displayed 28 magic + 54
magic + 71 physical; attacks two through four each displayed 28 magic + 24
magic + 71 physical. The normal 24-magic E on-hit and Statikk's 30
post-mitigation Energized damage combine into the first 54 display only. This
disproves the obsolete three-charge implementation and confirms one preloaded
60-raw-magic Energized proc. The simulator produces 528.46 exact damage /
2971.54 remaining HP and matches every displayed component.

**Stormrazor + Swiftmarch + Fleet Footwork, level 18:** before attacking,
Practice Tool displayed 166 AD, 0 AP, 1.235 attack speed, and 435 movement
speed. The first non-critical attack displayed 95 magic + 83 physical, then
Stormrazor and Fleet together raised the visible state to 170 AD / 570 movement
speed. A following automatic non-critical attack still displayed 24 magic +
21 magic + 84 physical and produced 309 total damage / 3191 remaining HP. An
E sample initially reported as 24 magic + 31 magic + 84 physical was later
identified as having been cast after Fleet expired, at 540 MS. The corrected E
inside the 570-MS window displayed 24 magic + 45 magic + 85 physical. The
physical increase is decisive: Fleet does feed Swiftmarch while active, raising
its force from the Stormrazor-only 27 to 28.5 and exact total AD from 169.828 to
170.8. The 45-magic group includes E's target-missing-health component and is
retained as an observation rather than an exact regression because HP before E
was not recorded. The automatic second attack's 84 is therefore a timing result
where its command snapshot preceded Fleet's visible jump, not a movement-stacking
exception. A later clarification put Alacrity at 3/10, corresponding to 1.245
exact simulator AS; the earlier 1.235 display corresponds to the adjacent 2/10
state and does not affect the damage conclusion. A final high-AS test with
Wit's End still produced 84 physical when the next attack was queued before
the visible jump; waiting for 570 MS before issuing a normal attack produced
85. This confirms command-snapshot ordering rather than an attack-speed cutoff.

## Regression suite

At this documentation revision, the maintained automated suite contains 74
passing tests. It covers:

- Full-precision damage and resistance formulas, including negative resistance.
- Q shred and penetration ordering.
- Every recorded baseline Practice Tool result.
- E missing-health snapshots and the internal Rageblade timing comparison.
- PTA, Shadowflame crit, Rageblade, R, Gunblade, Lich Bane, and Dusk and Dawn.
- Last Stand and level-20 rune scaling.
- W/Swiftmarch timing and movement-speed rune layers.
- Boots/starter restrictions, Dark Seal stacks, Absolute Focus, and default
  ability progression.
- All 19 newly added item IDs and their stat, stacking, penetration, movement,
  expected-crit, target-bonus-HP, and post-R timeline behavior.

Run it without creating cache files:

```text
python -B -m unittest discover -s tests -v
```

## Remaining validation limits

- The exact Practice Tool patch needs to be recorded on the next fresh pass.
- Last Stand still lacks a controlled own-HP Practice Tool measurement.
- W/Swiftmarch and the new starter/boot items are source-confirmed and
  regression-tested, but their raw numeric Practice Tool capture sheet has not
  been preserved.
- The July 17 item expansion is source-confirmed and regression-tested. Essence
  Reaver, Experimental Hexplate, Kraken Slayer, Terminus, Bloodletter's
  Curse, Riftmaker, Rapid Firecannon, Statikk Shiv, and Stormrazor are Practice
  Tool-confirmed; the
  remaining new item interactions still need dedicated isolation. Random crits
  must be recorded as crit and non-crit samples rather than compared directly
  with expected value.
- League's projectile travel time can change an immediate Q → E interaction;
  this is intentionally normalized to Q-first in the simulator.
- Dummy totals and floating numbers are integer displays, so exact simulation
  comparisons should normally tolerate about one point of display difference.
