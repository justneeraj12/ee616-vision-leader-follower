from __future__ import annotations

import csv
import json
from pathlib import Path

from toy_swarm.warehouse import simulate_warehouse


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / 'work' / 'toy_simulation' / 'warehouse_results'


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows, summary = simulate_warehouse()
    with (RESULTS / 'warehouse_multi_timeseries.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (RESULTS / 'warehouse_multi_summary.json').open('w', encoding='utf-8') as stream:
        json.dump(summary, stream, indent=2, sort_keys=True)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
