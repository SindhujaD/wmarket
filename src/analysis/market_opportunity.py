import sys
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.config import PROCESSED_DIR


OPPORTUNITY_VARIABLES = [
    "population",
    "median_household_income",
    "per_capita_income",
    "youth_share",
    "young_adult_share",
    "households_with_children_share",
    "bachelors_plus",
    "labor_force_participation",
]


def load_data():

    path = (
        PROCESSED_DIR /
        "wnba_market_demographics.csv"
    )

    return pd.read_csv(path)


def calculate_index(df):

    df = df.copy()

    available_variables = [
        column
        for column in OPPORTUNITY_VARIABLES
        if column in df.columns
    ]

    valid = (
        df[available_variables]
        .notna()
        .all(axis=1)
    )

    scaler = StandardScaler()

    z_values = scaler.fit_transform(
        df.loc[
            valid,
            available_variables
        ]
    )

    z_columns = [
        f"{column}_z"
        for column in available_variables
    ]

    df.loc[
        valid,
        z_columns
    ] = z_values

    df["market_opportunity_index"] = (
        df[z_columns]
        .mean(axis=1)
    )

    df["market_opportunity_rank"] = (
        df["market_opportunity_index"]
        .rank(
            ascending=False,
            method="min"
        )
    )

    return df


def main():

    df = load_data()

    df = calculate_index(df)

    output_path = (
        PROCESSED_DIR /
        "market_opportunity.csv"
    )

    df.to_csv(
        output_path,
        index=False
    )

    print(
        "\n--- MARKET OPPORTUNITY ---\n"
    )

    print(
        df[
            [
                "team_name",
                "market_opportunity_index",
                "market_opportunity_rank"
            ]
        ]
        .sort_values(
            "market_opportunity_rank"
        )
        .to_string(index=False)
    )

    print(
        f"\nSaved:\n{output_path}"
    )


if __name__ == "__main__":
    main()