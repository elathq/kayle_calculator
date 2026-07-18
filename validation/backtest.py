"""Compare captured Practice Tool totals with the current simulation.

Run from the project root:
    python -B validation/backtest.py
"""

import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.engine import simulate_build  # noqa: E402


def main():
    fixture_path = Path(__file__).with_name("practice_tool_cases.json")
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    setup = fixture["setup"]
    print(f"Practice Tool backtest - patch {fixture['metadata']['patch']}")
    print(f"Status: {fixture['metadata']['status']}")
    print()
    print(f"{'Case':<24} {'Dummy':>8} {'HP delta':>10} {'Sim exact':>12} {'Delta':>10}")
    print("-" * 70)

    for case in fixture["cases"]:
        result = simulate_build(
            level=setup["level"],
            ranks=setup["ability_ranks"],
            item_keys=setup["items"],
            enemy=setup["enemy"],
            combo=case["combo"],
            options={
                **setup["options"],
                "rune_ids": setup["runes"],
                "shards": setup["shards"],
            },
        )
        observed = float(case["observed_total"])
        hp_delta = float(case["hp_before"] - case["hp_after"])
        simulated = result["total_damage"]
        print(
            f"{case['label']:<24} {observed:>8.2f} {hp_delta:>10.2f} "
            f"{simulated:>12.2f} {simulated - observed:>+10.2f}"
        )


if __name__ == "__main__":
    main()
