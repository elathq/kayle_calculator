# Kayle AD Crit Build

## Recommended Build

### Purchase order

1. **Kraken Slayer**
2. **Stormrazor**
3. **Infinity Edge** by default, or **Lord Dominik's Regards** into real armor and bonus-HP stacking
4. Build whichever of **Infinity Edge / Lord Dominik's Regards** was not purchased third
5. **Yun Tal Wildarrows**
6. **Gluttonous Greaves**

Completed build:

> Kraken Slayer / Stormrazor / Infinity Edge / Lord Dominik's Regards / Yun Tal Wildarrows / Gluttonous Greaves

Gluttonous Greaves can be completed earlier when sustain or movement is needed. On a recall that cannot afford Stormrazor's B. F. Sword, finishing the boots is a practical purchase rather than waiting with unspent gold.

### Why these items

- **Kraken Slayer** is the smooth first-item purchase and supplies AD, attack speed and permanent movement speed.
- **Stormrazor** supplies crit and an Energized movement-speed burst for repositioning after the first attack.
- **Infinity Edge** is the default third legendary because its AD and crit-damage increase outperform early armor penetration against ordinary targets.
- **Lord Dominik's Regards** becomes the better early purchase when the relevant enemy combines armor with meaningful bonus health.
- **Yun Tal Wildarrows** restores the attack speed missing from Gluttonous Greaves and completes 100% trained crit.
- **Gluttonous Greaves** preserve 45 flat movement speed and provide 4% omnivamp immediately. Takedowns add 0.6% omnivamp each, up to 10% total.

At level 18 with Alacrity and Yun Tal active, the build reaches approximately:

- **2.082 combat attack speed**
- **429.56 movement speed normally**
- **532.1 movement speed during Stormrazor**
- About **106 / 101 healing** against the Squishy / Fighter averages at zero Gluttonous stacks
- About **265 / 253 healing** at maximum Gluttonous stacks

## Primary Runes

| Slot | Rune | Reason |
|---|---|---|
| Keystone | **Press the Attack** | Best overall damage, burst and realistic-target consistency |
| Row 1 | **Presence of Mind** | Supports repeated Q, W and E usage |
| Legend | **Legend: Alacrity** | Replaces the attack speed lost by not using Berserker's Greaves |
| Combat | **Last Stand** | Retained as the chosen combat rune; it is inactive in full-health damage tests |

Test shards:

> Attack Speed / Adaptive Force / Scaling Health

The comparison baseline uses no secondary runes.

## Press the Attack vs. Lethal Tempo

**Recommendation: keep Press the Attack.**

Level-18 full-build medium combo:

> Q -> AA -> AA -> E -> AA -> AA -> AA -> AA

| Target | PTA DPS | LT DPS | PTA 1s burst | LT 1s burst | PTA TTK | LT TTK |
|---|---:|---:|---:|---:|---:|---:|
| Squishy average | **3549.9** | 3441.2 | **2651.4** | 2549.3 | 0.747s | **0.741s** |
| Tank/Fighter average | **3392.8** | 3287.0 | **2534.0** | 2435.1 | 0.747s | **0.741s** |

Lethal Tempo attacks slightly sooner and therefore reaches the same lethal attack one game frame earlier. However, it loses approximately:

- **3.1% DPS**
- **3.9% 1-second burst**
- Roughly **2-4% damage** across the level-16 and level-18 short, medium and all-in tests

Lethal Tempo needs six attacks before its bolt becomes available. The realistic average targets die before that payoff matters. Even against an extreme 5,000-HP, 2,500-bonus-HP, 250-armor and 140-MR frontline target, Lethal Tempo was only about 0.5% ahead in front-to-back DPS and had a slower TTK because it required an additional attack.

Use Lethal Tempo only when the enemy composition reliably allows uninterrupted attacking into exceptionally durable frontliners. PTA is the general-purpose keystone.

## Infinity Edge or LDR Third?

### Default rule

Build **Infinity Edge third** unless an important enemy is purchasing both armor and bonus health.

The ordinary Squishy and Tank/Fighter averages have approximately 100-112 armor and no modeled bonus health. Infinity Edge wins comfortably against both. A naturally tanky champion, Plated Steelcaps, or one small armor component is not automatically enough to justify LDR third.

### Approximate crossover points

These are level-11, three-legendary medium-combo crossover points for total damage. The values use Kraken Slayer and Stormrazor as the first two items.

| Target bonus health | Approximate armor where LDR overtakes IE |
|---:|---:|
| 0 | **340 armor** |
| 300 | **180 armor** |
| 600 | **120 armor** |
| 1,000 | **70 armor** |

Practical interpretation:

- **100-120 armor and little bonus HP:** Infinity Edge third.
- **Around 180 armor and 300 bonus HP:** LDR third becomes reasonable.
- **Around 120 armor and 600 bonus HP:** LDR third is favored.
- **Dedicated armor-and-health stacker:** LDR third.

LDR can overtake slightly earlier for the isolated 1-second burst metric, but Infinity Edge remains better for total combo damage and TTK until the listed approximate crossover.

### Calculator requirement

The target's purchased health must be entered as **bonus HP**. The scalable Squishy and Tank/Fighter presets currently use zero bonus HP. Leaving that value at zero substantially undervalues LDR against an itemized frontline.

## Test Assumptions

- Kayle at full health, so Last Stand contributes no damage
- Press the Attack or Lethal Tempo
- Presence of Mind
- Legend: Alacrity at maximum stacks
- No secondary runes
- Attack Speed / Adaptive Force / Scaling Health shards
- Zero initial Kayle passive and Rageblade stacks
- Yun Tal fully trained when included
- Energized effects ready at the start
- Instant E attack reset enabled
- Squishy and Tank/Fighter averages used instead of relying on a 100/100 target dummy

## Calculator Support

Gluttonous Greaves and its mid-lane quest evolution, Immortal Path, are now
implemented directly in the calculator. Set **Gluttonous Slay stacks** under
Advanced Conditions from 0 to 10. Immortal Path also reads **Kayle HP %**:

- Above 50% HP: 4% increased damage
- Below 50% HP: 12% increased healing
- Exactly 50% HP: neither conditional effect is active

Mercury's Treads / Chainlaced Crushers and Plated Steelcaps / Armored Advance
are also available. Their movement speed and defensive stats are displayed,
but incoming attack reduction and defensive shields do not change this
outgoing-damage calculator's DPS, burst, or TTK.

## Sources

- [Riot Games Patch 26.9 Notes - Gluttonous Greaves introduction](https://www.leagueoflegends.com/en-gb/news/game-updates/league-of-legends-patch-26-9-notes/)
- [Riot Games Patch 26.10 Notes - Gluttonous Greaves stacking adjustment](https://www.leagueoflegends.com/en-us/news/game-updates/league-of-legends-patch-26-10-notes/)
- [Riot Games Patch 26.14 Notes - Immortal Path 4% / 12% adjustment](https://www.leagueoflegends.com/en-gb/news/game-updates/league-of-legends-patch-26-14-notes/)
- [League Wiki - Gluttonous Greaves](https://wiki.leagueoflegends.com/en-us/Gluttonous_Greaves)
- [League Wiki - Immortal Path](https://wiki.leagueoflegends.com/en-us/Immortal_Path)
