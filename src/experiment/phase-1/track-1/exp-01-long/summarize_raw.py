"""Print and save numerical summaries from the completed Exp 01 long raw run.

From src/: python experiment/phase-1/track-1/exp-01-long/summarize_raw.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from exp01_summary import format_report, summarize


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=HERE / "runs" / "20261103T062244Z")
    parser.add_argument("--output", type=Path, default=HERE / "numeric-summary.json")
    args = parser.parse_args()
    result = summarize(args.run, expected_run_name="exp-01-long")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(format_report(result))
    print(f"\nSaved machine-readable summary: {args.output.resolve()}")


if __name__ == "__main__":
    main()
