from __future__ import annotations

import argparse
from pathlib import Path

from economics_tracker.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Track major economics journals and export selected/rejected articles to Excel."
    )
    parser.add_argument(
        "--output",
        default="output/economics_journals_monthly.xlsx",
        help="Path to the generated Excel workbook.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    output_path = run_pipeline(Path(args.output))
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
