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
        default="output/economics_journals_daily.xlsx",
        help="Path to the generated Excel workbook.",
    )
    parser.add_argument(
        "--from-date",
        default="",
        metavar="YYYY-MM-DD",
        help="Fetch articles published on or after this date (used for Crossref fallback).",
    )
    parser.add_argument(
        "--until-date",
        default="",
        metavar="YYYY-MM-DD",
        help="Fetch articles published on or before this date (used for Crossref fallback).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    output_path = run_pipeline(
        Path(args.output),
        from_date=args.from_date,
        until_date=args.until_date,
    )
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
