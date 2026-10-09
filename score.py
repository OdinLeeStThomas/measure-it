"""Score: read the fixtures, never the model, and say what happened.

    uv run score.py policy-in-user             # one condition: right action per run, noise floor, by slice
    uv run score.py policy-in-user policy-in-system      # two conditions: the same, then a verdict per slice
    uv run score.py policy-in-user --detail    # every scorer by slice

The scorers are in harness/scorers.py and the report in harness/report.py.
"""
from __future__ import annotations

import argparse
from typing import Any

from harness import fixtures, golden, report


def main() -> None:
    # parse command-line arguments
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("conditions", nargs="*", default=["policy-in-user"])
    p.add_argument("--detail", action="store_true", help="every scorer, by slice")
    args: argparse.Namespace = p.parse_args()

    # attach account info so scorers can check ticket and account amounts
    accounts: dict[str, dict[str, Any]] = golden.load_accounts()
    items: dict[Any, dict] = {
        item["id"]: item | {"account_details": accounts[item["account"]]}
        for item in golden.load_golden()
    }

    # keep each condition's per-run tables for summaries and comparison
    tables_by: dict[str, list[report.Table]] = {}
    for condition in args.conditions:
        runs: list[tuple[str, list[dict]]] = [(name, [r for r in records if r["id"] in items]) for name, records in fixtures.runs(condition)]
        if not runs:
            print(f"no fixtures under {fixtures.FIXTURES / condition}; run record.py first")
            continue
        tables_by[condition] = [report.per_slice(items, records) for _, records in runs]
        report.summary(condition=condition, runs=runs, tables=tables_by[condition], items=items, detail=args.detail)
    if len(tables_by) == 2:
        (a, ta), (b, tb) = tables_by.items()
        report.compare(a=a, tables_a=ta, b=b, tables_b=tb, items=items)


if __name__ == "__main__":
    main()
