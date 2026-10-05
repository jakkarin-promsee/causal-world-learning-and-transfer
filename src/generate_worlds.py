"""Command-line entry point for materializing the structural world space."""

import argparse

from core.storage import save_world_dataset
from core.types import WorldSpec
from core.worldgen import world_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", help="new or empty output directory")
    parser.add_argument("--d", type=int, default=4, help="number of X variables")
    parser.add_argument("--m", type=int, default=4, help="number of Y variables")
    parser.add_argument("--shard-size", type=int, default=100_000)
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="write plain JSONL instead of gzip-compressed JSONL",
    )
    args = parser.parse_args()

    spec = WorldSpec(d=args.d, m=args.m)
    count = world_count(spec)
    print(f"Generating {count:,} canonical structural worlds...")
    manifest = save_world_dataset(
        args.output,
        spec,
        shard_size=args.shard_size,
        compressed=not args.no_compress,
    )
    print(f"Complete: {manifest}")


if __name__ == "__main__":
    main()
