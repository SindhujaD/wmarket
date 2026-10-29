import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.config import (
    TRENDS_RAW_DIR,
    PROCESSED_DIR,
)


def main():

    input_path = (
        TRENDS_RAW_DIR /
        "wnba_google_trends_raw.csv"
    )

    df = pd.read_csv(
        input_path,
        parse_dates=["date"]
    )

    # Remove Google's partial-data flag
    if "isPartial" in df.columns:
        df = df.drop(
            columns=["isPartial"]
        )

    # Rename search score
    search_columns = [
        column
        for column in df.columns
        if column not in [
            "date",
            "team_id",
            "search_term"
        ]
    ]

    if len(search_columns) != 1:
        raise ValueError(
            "Unexpected Trends columns."
        )

    df = df.rename(
        columns={
            search_columns[0]:
            "search_interest"
        }
    )

    # Monthly aggregation
    df["month"] = (
        df["date"]
        .dt.to_period("M")
        .astype(str)
    )

    monthly = (
        df.groupby(
            [
                "team_id",
                "search_term",
                "month"
            ],
            as_index=False
        )
        ["search_interest"]
        .mean()
    )

    output_path = (
        PROCESSED_DIR /
        "wnba_google_trends.csv"
    )

    monthly.to_csv(
        output_path,
        index=False
    )

    print(
        f"Saved:\n{output_path}"
    )


if __name__ == "__main__":
    main()