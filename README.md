# Kayle Damage Simulator

A browser-based League of Legends combat simulator for comparing Kayle builds
against the same target and action sequence. It reports total damage, full-combo
DPS, and the strongest rolling burst window.

This is an independent, fan-made project. It is not endorsed by Riot Games.
Game rules are labelled as Practice Tool-confirmed, source-confirmed, assumed,
or not modeled.

## Use the calculator

Use the hosted application:

**[kayle-calculator.web.app](https://kayle-calculator.web.app/)**

No local installation is required. This repository exists for documentation,
code transparency, and review of the simulator's formulas and evidence.

## What it provides

- Side-by-side build comparison with independent items, runes, and shards.
- Downloadable PNG share images for the current build comparison.
- Item selection grouped into Starter Item, Boots, AP, and AD tabs.
- A drag-and-drop attack, ability, and item-active sequence.
- Combo execution stops after the AA, ability, or item active that kills the
  target; later actions and unresolved delayed effects are omitted.
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

## Share images

After a successful calculation, the **Share** button downloads a compact PNG
styled like the calculator's result cards. It includes Kayle's level and
ranks, the target, combo, item icons, damage KPIs, damage composition, core
combat stats, and remaining target HP.

The image is rendered locally in the browser. No comparison data is uploaded
or stored in a database, and the share action is disabled as soon as the
setup changes so an image cannot silently mix old results with new inputs.

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
1.20, & \text{magic or true damage and live HP before the instance}<0.40H_{\max} \\
1, & \text{otherwise}
\end{cases}
$$

The final applied damage for one instance and the complete combo are

$$
D_i^{\mathrm{applied}}
=D_i^{\mathrm{raw}}\cdot A_i\cdot C_i\cdot G_i
$$

$$
D_{\mathrm{total}}=\sum_i D_i^{\mathrm{applied}}
$$

First Strike creates a separate, non-recursive true-damage instance equal to
$0.07D_i^{\mathrm{applied}}$, which is included in the total above.

Let $t_{\min}$ and $t_{\max}$ be the first and last damage timestamps. The DPS
formula matched against the Practice Tool is

$$
\mathrm{DPS}=
\begin{cases}
0, & \text{no damage instances} \\
D_{\mathrm{total}}, & t_{\min}=t_{\max} \\
\dfrac{D_{\mathrm{total}}}{t_{\max}-t_{\min}}, & t_{\min}\lt t_{\max}
\end{cases}
$$

Setup before the first hit and recovery after the final hit are excluded.
Delayed damage moves $t_{\max}$ and extends the DPS window.

The strongest rolling one-second burst is

$$
B_{1\mathrm{s}}
=\max_s\left(\sum_{i:\ s\le t_i\le s+1\mathrm{s}}
D_i^{\mathrm{applied}}\right)
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
review date                    = 2026-07-29
local Riot asset set           = Data Dragon 16.14.1
live numeric catalog           = Data Dragon 16.15.1
baseline Practice Tool patch   = confirmation pending
automated tests                = 122 Python + 3 frontend passing
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
| [API guide](docs/API.md) | Endpoints, readable keys, request payloads, responses, limits, and errors. |

Each fact has one home: the model says what is calculated, validation records
why it is trusted, sources identify the external reference, and maintenance
explains how to update it.

## Local verification

The repository has no third-party runtime dependencies. From the project
directory, run:

```text
python -m compileall -q backend tests validation tools
python -B -m unittest discover -s tests -v
python -B validation/backtest.py
node --check frontend/snapshot.js
node --check frontend/app.js
node --test tests_js/snapshot.test.js
```

The `Verify` GitHub Actions workflow runs the same checks on pushes and pull
requests so engine, documentation, and frontend changes are reviewed together.

## Project structure

| Path | Responsibility |
|---|---|
| `backend/data/kayle_data.py` | Kayle stats, growth, ranks, and ability data. |
| `backend/data/items_data.py` | Selectable item catalog and effect data. |
| `backend/data/runes_data.py` | Rune and shard catalog. |
| `backend/data/enemy_data.py` | Target presets and scaling. |
| `backend/damage.py` | Resistance and damage-pipeline helpers. |
| `backend/engine.py` | Stateful timeline simulation. |
| `backend/item_rules.py` | Shared item-build legality rules and UI metadata. |
| `backend/main.py` | HTTP server, API validation, and static files. |
| `frontend/` | Browser interface and local icons. |
| `frontend/snapshot.js` | Dependency-free PNG snapshot model and renderer. |
| `tests/` | Automated regressions. |
| `tests_js/` | Dependency-free frontend snapshot regressions. |
| `validation/` | Machine-readable Practice Tool fixture and backtest. |
| `tools/` | Optional maintenance utilities. |

Catalog snapshot:

```text
selectable items = 45
```

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
simulation rate               <= 30 requests / network-peer bucket / minute
concurrent simulations         = 2 by default
configurable concurrency range = 1..4
```

Responses include a restrictive Content Security Policy and defensive browser
headers. Public errors omit tracebacks and runtime versions. Deployment secrets
belong in environment variables; local secrets, logs, environments, editor
state, and caches are ignored by Git.

These controls reduce accidental and low-cost abuse. Platform monitoring and
denial-of-service protection remain the host's responsibility.

The application does not trust forwarding headers to identify clients. On
Cloud Run, the in-process limiter therefore uses the immediate network peer as
a coarse safety bucket; production-grade per-user or per-IP enforcement belongs
at a trusted Google Cloud edge or authenticated API layer.

## Deployment and assets

Bootstrap data is compressed. Versioned scripts, styles, and icons use
long-lived browser caching, while the HTML entry point revalidates on deploy.
Cloud Run supplies the revision identifier used for asset versioning.

When local icon bytes change, increment this value:

```text
backend/data/__init__.py -> ICON_VERSION
```

The icon optimizer is maintenance-only and is not part of the hosted runtime.
Firebase Hosting provides the public `web.app` address and forwards requests to
Cloud Run. Pushing `main` triggers Cloud Build and deploys a new Cloud Run
revision automatically. Firebase only needs redeployment when its routing
configuration changes. Cloud Run may scale to zero while the application is
idle.

## Known scope limits

- Cooldown-invalid Q/W/E/R actions block UI results, open a readiness message,
  and receive a red outline at the exact invalid sequence position.
- Random critical strikes use expected damage.
- Q before E is assumed to hit before E; target distance is not an input.
  Hexoptics therefore uses a fixed 250-unit midpoint for 5% Magnification.
- **Use E for AA cancel** switches a directly following `AA -> E` between the
  fast reset and the normal full attack interval. Windups use Kayle's current
  attack speed and align to the game's 30 Hz clock; ordinary attack timers stay
  continuous. Q is always treated as a point-blank hit with no travel time.
- Mana, multi-target chains, automatic takedown events, incoming shields, and
  selected utility effects are outside the model. Gluttonous Slay stacks are
  supplied explicitly under Advanced Conditions.
- Top-lane quest levels and evolved mid-lane boots are mutually exclusive.

Role restriction:

```text
top-lane quest levels = 19..20
illegal at those levels:
  - Swiftmarch
  - Spellslinger's Shoes
  - Gunmetal Greaves
  - Immortal Path
  - Chainlaced Crushers
  - Armored Advance
```

The complete list is in [Simulation model](docs/MODEL.md#assumptions-and-exclusions).

## Attribution

League of Legends and Riot Games are trademarks or registered trademarks of
Riot Games, Inc. Riot and CommunityDragon assets identify in-game items and
runes. Full provenance is recorded in [Data and icon sources](docs/SOURCES.md).
