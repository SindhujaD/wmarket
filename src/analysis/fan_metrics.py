import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.config import PROCESSED_DIR


def load_data():

    performance = pd.read_csv(
        PROCESSED_DIR /
        "wnba_team_season.csv"
    )

    market = pd.read_csv(
        PROCESSED_DIR /
        "wnba_market_demographics.csv"
    )

    return performance, market


def calculate_metrics(
    performance,
    market
):

    df = performance.merge(
        market[
            [
                "team_id",
                "population"
            ]
        ],
        on="team_id",
        how="left"
    )

    # These will be populated once
    # attendance data is collected.
    #
    # Example formulas:

    if "average_attendance" in df.columns:

        df["attendance_per_100k"] = (
            df["average_attendance"] /
            df["population"] *
            100_000
        )

    if (
        "average_attendance" in df.columns
        and "arena_capacity" in df.columns
    ):

        df["capacity_utilization"] = (
            df["average_attendance"] /
            df["arena_capacity"]
        )

    return df


def main():

    performance, market = load_data()

    df = calculate_metrics(
        performance,
        market
    )

    output_path = (
        PROCESSED_DIR /
        "fan_metrics.csv"
    )

    df.to_csv(
        output_path,
        index=False
    )

    print(
        f"Saved:\n{output_path}"
    )


if __name__ == "__main__":
    main()