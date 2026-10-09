"""Judge: run the LLM judge over recorded outputs and save its verdicts as fixtures.

    uv run judge.py policy-in-user                 # every run under fixtures/policy-in-user
    uv run judge.py policy-in-user system          # several conditions
    uv run judge.py policy-in-user --provider fake # no key, NOT a model

Writes fixtures/<condition>/judge-<run>.jsonl, one line per rationale. Like record.py it
is resumable and never repeats a verdict it already has. The rubric is in harness/judge.py.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from harness import fixtures, golden
from harness.judge import RUBRIC, judge


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("conditions", nargs="+")
    p.add_argument("--provider", choices=["gemini", "fake"], default="gemini")
    args: argparse.Namespace = p.parse_args()

    items: dict[Any, dict] = {i["id"]: i for i in golden.load_golden()}
    for condition in args.conditions:
        for run_name, records in fixtures.runs(condition):
            path: Path = fixtures.judge_path(condition, run_name)
            done: set[str] = fixtures.recorded_ids(path)
            todo: list[dict] = [r for r in records if r["id"] in items and r["id"] not in done]
            print(f"{condition} / {run_name}: {len(done)} judged, {len(todo)} to go ({len(RUBRIC)} question(s), via {args.provider})", flush=True)
            for rec in todo:
                verdicts: dict = judge(item=items[rec["id"]], output=rec, provider=args.provider)
                fixtures.append(path=path, record={"id": rec["id"], "run": rec["run"], "condition": condition, **verdicts})
                print(f"  {rec['id']}  " + "  ".join(f"{k}={'yes' if v else 'no'}" for k, v in verdicts.items()), flush=True)


if __name__ == "__main__":
    main()
