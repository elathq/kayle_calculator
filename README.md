# Kayle Damage Simulator

A browser-based League of Legends combat simulator for comparing Kayle builds
against the same target and action sequence. It reports total damage, full-combo
DPS, and the strongest rolling burst window.

This is an independent, fan-made project. It is not endorsed by Riot Games.
Game rules are labelled as Practice Tool-confirmed, source-confirmed, assumed,
or not modeled.

## Use the calculator

Use the hosted application:

**[kayle-calculator.onrender.com](https://kayle-calculator.onrender.com/)**

No local installation is required. This repository exists for documentation,
code transparency, and review of the simulator's formulas and evidence.

## What it provides

- Side-by-side build comparison with independent items, runes, and shards.
- A drag-and-drop attack, ability, and item-active sequence.
- Target HP, bonus HP, armor, and magic-resistance controls.
- A full timeline with raw, resisted, and applied damage.
- Stable expected-value critical strikes.
- Timed buffs, delayed hits, penetration, missing-health snapshots, and
  movement-speed interactions.

Public comparison limits:

```text
builds              <= 8
items per build     <= 6
combo actions       <= 100
```

## Core calculations

The engine resolves every physical, magic, and true-damage component as its
own full-precision timeline instance. Source-specific formulas supply the raw
value; the following pipeline produces the final comparison metrics.

For damage instance $i$ at timestamp $t_i$, its source value and raw damage are

$$
S_i = B_i + \sum_k (X_{ik} \cdot R_{ik}) + H_i
$$

$$
D_i^{\mathrm{raw}} = S_i \cdot \prod_k M_{ik}^{\mathrm{source}}
$$

where $B_i$ is base damage, $X_{ik}R_{ik}$ contains relevant AD, AP, or HP
scalings, $H_i$ contains on-hit, missing-health, stack, and level terms, and
$M_{ik}^{\mathrm{source}}$ contains eligible source modifiers such as expected
critical strikes, Axiom Arcanist, or Hexoptics.

Percentage resistance reductions and percentage penetration stack
multiplicatively:

$$
q_i = 1 - \prod_j (1-q_{ij}),
\qquad
p_i = 1 - \prod_j (1-p_{ij})
$$

Here, $q_{ij}$ includes effects such as Q and Bloodletter, while $p_{ij}$
includes item penetration and Terminus. Effective resistance is

$$
R_i^{(1)} = R_i^{\mathrm{listed}}(1-q_i)
$$

$$
R_i^{\mathrm{effective}} =
\begin{cases}
\max\!\left(0,\ R_i^{(1)}(1-p_i)-F_i\right), & R_i^{(1)} > 0 \\
R_i^{(1)}, & R_i^{(1)} \le 0
\end{cases}
$$

where $F_i$ is eligible flat penetration. The resistance multiplier is

$$
G_i =
\begin{cases}
1, & \text{true damage} \\
\dfrac{100}{100+R_i^{\mathrm{effective}}},
  & R_i^{\mathrm{effective}} \ge 0 \\
2-\dfrac{100}{100-R_i^{\mathrm{effective}}},
  & R_i^{\mathrm{effective}} < 0
\end{cases}
$$

All eligible outgoing amplifiers multiply together:

$$
A_i = \prod_j (1+a_{ij})
$$

$a_{ij}$ includes Press the Attack, Coup de Grace, Cut Down, Last Stand,
Riftmaker, and Lord Dominik's Regards when their conditions are active.
Shadowflame contributes

$$
C_i =
\begin{cases}
1.20, & \text{magic or true damage and frame-start HP}<0.40H_{\max} \\
1, & \text{otherwise}
\end{cases}
$$

The final applied damage for one instance and the complete combo are

$$
D_i^{\mathrm{applied}}
=D_i^{\mathrm{raw}}\cdot A_i\cdot C_i\cdot G_i
$$

$$
\boxed{D_{\mathrm{total}}=\sum_i D_i^{\mathrm{applied}}}
$$

First Strike creates a separate, non-recursive true-damage instance equal to
$0.07D_i^{\mathrm{applied}}$, which is included in the total above.

Let $t_{\min}$ and $t_{\max}$ be the first and last damage timestamps. The DPS
formula matched against the Practice Tool is

$$
\boxed{
\mathrm{DPS}=
\begin{cases}
0, & \text{no damage instances} \\
D_{\mathrm{total}}, & t_{\min}=t_{\max} \\
\dfrac{D_{\mathrm{total}}}{t_{\max}-t_{\min}}, & t_{\min}<t_{\max}
\end{cases}}
$$

Setup before the first hit and recovery after the final hit are excluded.
Delayed damage moves $t_{\max}$ and extends the DPS window.

The strongest rolling one-second burst is

$$
\boxed{
B_{1\mathrm{s}}
=\max_s\left(\sum_{i:\ s\le t_i\le s+1\mathrm{s}}
D_i^{\mathrm{applied}}\right)}
$$

## Accuracy and evidence

The engine uses one full-precision damage path. League can round floating text,
target HP, and the Practice Tool total independently, so a display difference
does not automatically imply a calculation error.

Evidence labels:

| Label | Meaning |
|---|---|
| Practice Tool-confirmed | Reproduced in a controlled in-game isolation. |
| Source-confirmed | Based on Riot or League Wiki data and covered by tests. |
| Simulator assumption | A documented normalization for an ambiguous interaction. |
| Inconsistent capture | Preserved, but not used as a regression target. |
| Not modeled | Explicitly outside the current calculation. |

Documentation snapshot:

```text
review date                    = 2026-07-18
local Riot asset set           = Data Dragon 16.14.1
baseline Practice Tool patch   = confirmation pending
automated tests                = 77 passing
```

The calculator is not automatically synchronized to live patches. A changed
mechanic requires a source review, code update, regression run, and affected
Practice Tool isolation.

## Documentation

| Document | Purpose |
|---|---|
| [Simulation model](docs/MODEL.md) | Formulas, event ordering, assumptions, and exclusions. |
| [Validation and backtesting](docs/VALIDATION.md) | Practice Tool observations and exact simulator comparisons. |
| [Data and icon sources](docs/SOURCES.md) | External references, version pins, and asset provenance. |
| [Maintaining items](docs/ITEM_MAINTENANCE.md) | Item schema and patch-update workflow. |

Each fact has one home: the model says what is calculated, validation records
why it is trusted, sources identify the external reference, and maintenance
explains how to update it.

## Project structure

| Path | Responsibility |
|---|---|
| `backend/data/kayle_data.py` | Kayle stats, growth, ranks, and ability data. |
| `backend/data/items_data.py` | Selectable item catalog and effect data. |
| `backend/data/runes_data.py` | Rune and shard catalog. |
| `backend/data/enemy_data.py` | Target presets and scaling. |
| `backend/damage.py` | Resistance and damage-pipeline helpers. |
| `backend/engine.py` | Stateful timeline simulation. |
| `backend/main.py` | HTTP server, API validation, and static files. |
| `frontend/` | Browser interface and local icons. |
| `tests/` | Automated regressions. |
| `validation/` | Machine-readable Practice Tool fixture and backtest. |
| `tools/` | Optional maintenance utilities. |

Catalog snapshot:

```text
selectable items = 42
```

## API overview

| Route | Purpose |
|---|---|
| `GET /healthz` | Lightweight health check. |
| `GET /api/bootstrap?level=N&preset=K` | Initial UI data. |
| `GET /api/champion?level=N` | Kayle stats and default ranks. |
| `GET /api/items` | Item catalog. |
| `GET /api/runes` | Rune and shard catalog. |
| `GET /api/enemy_presets` | Target presets. |
| `GET /api/enemy_preset?preset=K&level=N` | One scaled target. |
| `POST /api/simulate` | Validate and simulate a build comparison. |

Maximum HP, starting HP, and bonus HP are separate because different mechanics
read different target values.

## Public-hosting safeguards

The UI prevents oversized comparisons. The API independently validates the
same limits and rejects non-finite or out-of-range inputs.

```text
builds                         <= 8
items per build                <= 6
combo actions                  <= 100
build-name length              <= 60 characters
one wait action                <= 60 seconds
request body                   <= 256 KiB
simulation rate               <= 30 requests / client / minute
concurrent simulations         = 2 by default
configurable concurrency range = 1..4
```

Responses include a restrictive Content Security Policy and defensive browser
headers. Public errors omit tracebacks and runtime versions. Deployment secrets
belong in environment variables; local secrets, logs, environments, editor
state, and caches are ignored by Git.

These controls reduce accidental and low-cost abuse. Platform monitoring and
denial-of-service protection remain the host's responsibility.

## Deployment and assets

Bootstrap data is compressed. Versioned scripts, styles, and icons use
long-lived browser caching, while the HTML entry point revalidates on deploy.
Render supplies the Git commit for asset versioning.

When local icon bytes change, increment this value:

```text
backend/data/__init__.py -> ICON_VERSION
```

The icon optimizer is maintenance-only and is not part of the hosted runtime.
Render Free services can sleep when idle; a paid instance is the supported
always-on option. See [Render's Free service documentation](https://render.com/docs/free).

## Known scope limits

- Cooldown-invalid actions remain in the entered combo and produce warnings.
- Random critical strikes use expected damage.
- Q before E is assumed to hit before E; target distance is not an input.
- Mana, multi-target chains, takedown-only effects, shields, and selected
  utility effects are outside the model.
- Top-lane quest levels and evolved mid-lane boots are mutually exclusive.

Role restriction:

```text
top-lane quest levels = 19..20
illegal at those levels:
  - Swiftmarch
  - Spellslinger's Shoes
  - Gunmetal Greaves
```

The complete list is in [Simulation model](docs/MODEL.md#assumptions-and-exclusions).

## Attribution

League of Legends and Riot Games are trademarks or registered trademarks of
Riot Games, Inc. Riot and CommunityDragon assets identify in-game items and
runes. Full provenance is recorded in [Data and icon sources](docs/SOURCES.md).
