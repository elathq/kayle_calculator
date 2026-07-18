# Kayle Damage Simulator

A browser-based League of Legends combat simulator for comparing Kayle builds
against the same target and action sequence. It models damage as a timeline,
shows every applied damage instance, and reports total damage, whole-combo DPS,
and the strongest rolling one-second burst window.

This is an independent, fan-made calculation project. It is not endorsed by
Riot Games. The implementation is validated against controlled Practice Tool
measurements where possible; source-backed assumptions and unresolved limits
are documented instead of being presented as confirmed game behavior.

## Use the calculator

Use the hosted application at
**[kayle-calculator.onrender.com](https://kayle-calculator.onrender.com/)**.

No local installation is required. This GitHub repository is published for
documentation, implementation transparency, and review of the simulator's
formulas and evidence; the hosted website is the intended user interface.

## What it provides

- Up to 8 builds compared in one simulation, with 6 items per build.
- A drag-and-drop sequence of up to 100 attacks, abilities, and item actives.
- Per-build rune pages, stat shards, champion level, ability ranks, and
  advanced combat conditions.
- Target maximum/current HP, bonus HP, armor, and magic resistance inputs.
- A full event timeline showing raw damage, effective resistance, and exact
  post-mitigation damage.
- Stable expected-value critical-strike comparisons rather than random rolls.
- Delayed effects, timed buffs, attack-speed timing, resistance changes,
  missing-health snapshots, and movement-speed interactions.
- A dependency-free production runtime: Python's standard library plus vanilla
  HTML, CSS, and JavaScript.

## Accuracy and evidence

The simulator uses one full-precision damage path. League's floating combat
text, target HP display, and Practice Tool total can round independently, so
integer display differences are evidence to inspect—not a reason to introduce
a second rounded combat model.

Claims in this project use five evidence labels:

| Label | Meaning |
|---|---|
| Practice Tool-confirmed | Reproduced in a controlled in-game isolation and protected by a regression test where practical. |
| Source-confirmed | Taken from Riot data, Riot patch notes, or the League Wiki and covered by automated tests, but not yet isolated in Practice Tool. |
| Simulator assumption | A deliberate normalization required by the tool, documented with its gameplay consequence. |
| Inconsistent capture | Preserved for transparency, but excluded from regression targets because recorded fields conflict or did not reproduce. |
| Not modeled | Explicitly outside the current calculation instead of being approximated silently. |

The complete measurement record, contradictory captures, timing findings, and
remaining validation gaps are in [Validation and backtesting](docs/VALIDATION.md).
The exact formulas and assumptions implemented by the engine are in the
[Simulation model](docs/MODEL.md).

Current documentation snapshot:

| Record | Status |
|---|---|
| Numerical/source review | 2026-07-18 |
| Local Riot asset set | Data Dragon 16.14.1 |
| Original baseline Practice Tool patch | Confirmation pending; it was not written down during capture |
| Automated suite | 74 passing tests |

The calculator is not automatically synchronized to live League patches. A
source review, implementation update, regression run, and affected Practice
Tool isolation are required before claiming support for a changed patch.

## Documentation

| Document | Purpose |
|---|---|
| [Simulation model](docs/MODEL.md) | Implemented combat rules, ordering, snapshots, assumptions, and exclusions. |
| [Validation and backtesting](docs/VALIDATION.md) | Practice Tool protocol, recorded evidence, exact comparisons, confidence, and remaining work. |
| [Data and icon sources](docs/SOURCES.md) | Riot, League Wiki, patch-note, Data Dragon, CommunityDragon, and icon provenance. |
| [Maintaining items](docs/ITEM_MAINTENANCE.md) | Patch-update workflow, item schema, templates, engine boundaries, icons, and verification. |

The documents have intentionally separate responsibilities: the model says
what the program calculates, validation says why those rules are trusted,
sources say where external information came from, and maintenance explains how
to update the implementation without silently changing behavior.

## Project structure

| Path | Responsibility |
|---|---|
| `backend/data/kayle_data.py` | Kayle stats, level growth, passive breakpoints, and ability data. |
| `backend/data/items_data.py` | The 39 selectable items, their stats, effect data, tags, and icon metadata. |
| `backend/data/runes_data.py` | Rune tree, shard catalog, and implemented rune values. |
| `backend/data/enemy_data.py` | Target presets and level scaling. |
| `backend/damage.py` | Shared resistance and damage-pipeline helpers. |
| `backend/engine.py` | Stateful timeline simulation and combat interactions. |
| `backend/main.py` | Standard-library HTTP server, API, validation, limits, and static files. |
| `frontend/` | Browser interface and local item/rune icons. |
| `tests/` | Automated combat, catalog, progression, security, and HTTP regressions. |
| `validation/` | Machine-readable Practice Tool fixture and baseline comparison runner. |
| `tools/` | Optional maintenance utilities such as icon optimization. |

## API overview

| Route | Purpose |
|---|---|
| `GET /healthz` | Lightweight service health check. |
| `GET /api/bootstrap?level=N&preset=K` | Initial item, rune, champion, and target data for the UI. |
| `GET /api/champion?level=N` | Kayle stats and default ability ranks. |
| `GET /api/items` | Selectable item catalog. |
| `GET /api/runes` | Rune and shard catalog. |
| `GET /api/enemy_presets` | Available target presets. |
| `GET /api/enemy_preset?preset=K&level=N` | One scaled target preset. |
| `POST /api/simulate` | Validate and simulate `{level, ability_ranks, builds, enemy, combo, options}`. |

The target payload separates maximum HP, starting HP, and bonus HP because
missing-health effects, threshold effects, and Lord Dominik's Regards use
different values.

## Public-hosting safeguards

The UI and API both enforce a maximum of 8 builds, 6 items per build, and 100
combo actions. The API additionally enforces finite bounded inputs, 60-character
build names, waits of at most 60 seconds, a 256 KiB request body, 30 simulation
requests per client per minute, and a process-wide simulation concurrency cap.
The cap defaults to 2 and can be configured from 1 to 4 with
`MAX_CONCURRENT_SIMULATIONS`.

Responses include a restrictive Content Security Policy and defensive browser
headers. Public failures return a short reference rather than a traceback or
Python version. Secrets belong in deployment environment variables; `.env`
files, local environments, logs, editor state, and generated caches are ignored
by Git.

These controls reduce accidental and low-cost abuse; they are not a substitute
for monitoring and platform-level denial-of-service protection.

## Deployment and asset transparency

The bootstrap data is returned as one compressed response. Versioned JavaScript,
CSS, and icons use long-lived browser caching, while `index.html` revalidates so
new deployments load the current asset version. Text and larger JSON responses
are gzip-compressed when supported by the client.

Render uses `RENDER_GIT_COMMIT` for asset versioning automatically. After
changing icon contents, increment `ICON_VERSION` in
`backend/data/__init__.py`. The optional icon optimizer and its Pillow
dependency are maintenance-only and are not part of the hosted runtime. Details
are in [Maintaining items](docs/ITEM_MAINTENANCE.md#icons).

Render Free services can sleep when idle. An external monitor may request
`/healthz`, but an always-on paid instance is the supported way to avoid free
service spin-down. See Render's [Free service documentation](https://render.com/docs/free).

## Known scope limits

The most important deliberate limits are summarized here; the complete list is
maintained in the [simulation model](docs/MODEL.md#explicit-assumptions-and-exclusions).

- The combo is executed as entered even when a cooldown warning is produced.
- Random critical strikes are represented as expected damage.
- Q entered before E is assumed to hit before E; projectile distance is not an
  input.
- Mana, multi-target chains, takedown-only effects, shields, and several
  non-damage utility effects are outside the current model.
- League's level-19/20 top-lane quest and evolved mid-lane boots are treated as
  mutually exclusive.

## Attribution

League of Legends and Riot Games are trademarks or registered trademarks of
Riot Games, Inc. Riot and CommunityDragon assets are used to identify in-game
items and runes. Detailed provenance and version pinning are recorded in
[Data and icon sources](docs/SOURCES.md).
