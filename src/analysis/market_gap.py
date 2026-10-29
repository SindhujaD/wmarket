import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.config import PROCESSED_DIR


def main():

    opportunity = pd.read_csv(
        PROCESSED_DIR /
        "market_opportunity.csv"
    )

    penetration = pd.read_csv(
        PROCESSED_DIR /
        "fan_penetration.csv"
    )

    df = opportunity.merge(
        penetration[
            [
                "team_id",
                "fan_penetration_index"
            ]
        ],
        on="team_id",
        how="inner"
    )

    df["market_performance_gap"] = (
        df["fan_penetration_index"]
        - df["market_opportunity_index"]
    )

    df["gap_rank"] = (
        df["market_performance_gap"]
        .rank(
            ascending=False,
            method="min"
        )
    )

    output_path = (
        PROCESSED_DIR /
        "market_performance_gap.csv"
    )

    df.to_csv(
        output_path,
        index=False
    )

    print(
        "\n--- MARKET PERFORMANCE GAP ---\n"
    )

    print(
        df[
            [
                "team_id",
                "team_name",
                "market_opportunity_index",
                "fan_penetration_index",
                "market_performance_gap",
                "gap_rank"
            ]
        ]
        .sort_values(
            "gap_rank"
        )
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()