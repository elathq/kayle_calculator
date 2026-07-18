# Practice Tool validation protocol

The complete test record and all findings are in
[`BACKTESTING_AND_FINDINGS.md`](BACKTESTING_AND_FINDINGS.md). This shorter file
is the checklist for collecting a new Practice Tool pass.

## Before each pass

- Record the exact League patch and map.
- Record Kayle's level, Q/W/E/R ranks, items, runes, shards, displayed AD, AP,
  attack speed, maximum HP, and current HP percentage.
- Record the dummy's maximum HP, starting HP, armor, and magic resistance.
- State whether Zeal, PTA, Rageblade, Fleet, or another effect starts stacked.
- Reset the dummy, cooldowns, and stacks between cases.

## For every sequence

1. Write the exact action order and every deliberate wait.
2. Record dummy HP immediately before and after the sequence.
3. Record the dummy total.
4. Record every floating damage number and its physical/magic/true color.
5. Repeat at least three times; flag timing-dependent results instead of
   averaging them together.

Floating text and displayed HP are rounded presentation values. Compare them to
the simulator's exact event timeline, allowing roughly one point of display
difference. Do not add an integer-per-instance combat model.

## Baseline regression pass

Use the exact setup in `validation/practice_tool_cases.json`:

1. AA.
2. E.
3. AA → E.
4. AA → E → AA.

Enter any newly confirmed observations in the JSON fixture, then run:

```text
python -B validation/backtest.py
python -B -m unittest discover -s tests -v
```

## Isolation order for changed mechanics

1. Basic attack and Q against 0, 50, 100, and 200 resistance.
2. Q followed by the same hit to verify post-Q shred.
3. Percentage penetration alone, flat penetration alone, then both.
4. Shadowflame crit with the action starting above and below 40% target HP.
5. E at full HP and reduced HP.
6. PTA, Spellblade, and Rageblade separately before combining them.
7. W → action at several timestamps around the two-second expiry when testing
   Swiftmarch or movement-speed runes.
8. New items one at a time: Wit's End; Statikk attacks 1–4; Stormrazor and
   Rapid Firecannon with a preloaded Energized attack; Kraken attacks 1–3;
   Terminus attacks 1–6; Bloodletter eligible hits 1–4; Experimental Hexplate
   R into attacks inside/outside eight seconds; Essence Reaver Q → attack;
   Yun Tal from zero crit stacks; and Navori Q → attacks → Q.
9. Extended timing: Riftmaker damage at 0/1/2/3/4 seconds, Cosmic Drive and
   Stormrazor actions just before/after their MS expiry, and Fiendhunter R
   followed by four attacks.
10. Crit items: record natural crit and non-crit attacks separately. The
    simulator reports their weighted expected value, not one random roll.

Find the first event whose raw damage, modifier, effective resistance, or exact
applied damage differs. Later totals will otherwise hide the cause.
