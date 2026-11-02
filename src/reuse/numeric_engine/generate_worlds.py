"""Generate the main numeric world dataset from canonical enumeration.

Run from src: python -m reuse.numeric_engine.generate_worlds OUTPUT
"""

import argparse

from core.types import WorldSpec
from core.worldgen import world_count
from reuse.numeric_engine.worlds import save_numeric_worlds


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="new or empty output directory")
    parser.add_argument("--d", type=int, default=4)
    parser.add_argument("--m", type=int, default=4)
    args = parser.parse_args()

    spec = WorldSpec(d=args.d, m=args.m)
    print(f"Generating {world_count(spec):,} numeric worlds...", flush=True)
    manifest = save_numeric_worlds(args.output, spec)
    print(f"Complete: {manifest}", flush=True)


if __name__ == "__main__":
    main()
