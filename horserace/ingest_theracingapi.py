from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .data_sources.theracingapi import TheRacingAPIClient


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Fetch data from TheRacingAPI into CSV")
    sub = ap.add_subparsers(dest="mode", required=True)

    res = sub.add_parser("results", help="Fetch historical results for training")
    res.add_argument("--start_date", required=True, help="YYYY-MM-DD")
    res.add_argument("--end_date", help="YYYY-MM-DD (defaults to start_date)")
    res.add_argument("--region", help="Region code if supported")
    res.add_argument("--distance_unit", default="m", help="m|f|y|km")
    res.add_argument("--weight_unit", default="kg", help="kg|lb")
    res.add_argument("--out_csv", required=True)

    card = sub.add_parser("racecard", help="Fetch upcoming races for prediction")
    card.add_argument("--date", required=True, help="YYYY-MM-DD")
    card.add_argument("--region", help="Region code if supported")
    card.add_argument("--distance_unit", default="m", help="m|f|y|km")
    card.add_argument("--weight_unit", default="kg", help="kg|lb")
    card.add_argument("--out_csv", required=True)

    return ap.parse_args()


def main() -> None:
    args = parse_args()
    client = TheRacingAPIClient()
    if args.mode == "results":
        df = client.fetch_results(
            start_date=args.start_date,
            end_date=args.end_date,
            region=args.region,
            distance_unit=args.distance_unit,
            weight_unit=args.weight_unit,
        )
    else:
        df = client.fetch_racecard(
            date=args.date,
            region=args.region,
            distance_unit=args.distance_unit,
            weight_unit=args.weight_unit,
        )

    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out_csv, index=False)
    print(f"Wrote {len(df)} rows to {args.out_csv}")


if __name__ == "__main__":
    main()

