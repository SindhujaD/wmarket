import sys
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.append(str(PROJECT_ROOT))

from src.config import (
    CENSUS_RAW_DIR,
    PROCESSED_DIR,
    TEAM_MARKET_PATH,
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

def load_census_data():

    path = (
        CENSUS_RAW_DIR
        / "acs5_2024_metro_raw.csv"
    )

    return pd.read_csv(path)


def load_markets():

    return pd.read_csv(
        TEAM_MARKET_PATH
    )


# ---------------------------------------------------------
# CLEAN CENSUS DATA
# ---------------------------------------------------------

def clean_census_data(df):

    df = df.copy()

    # Remove ACS missing/sentinel values
    sentinel_values = [
        -666666666,
        -666666667,
        -999999999,
    ]

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns

    for column in numeric_columns:

        df[column] = df[column].replace(
            sentinel_values,
            pd.NA,
        )

    # Convert percentages to decimal proportions
    percentage_columns = [
        "poverty_rate",
        "bachelors_plus",
        "labor_force_participation",
        "unemployment_rate",
    ]

    for column in percentage_columns:

        if column in df.columns:

            df[column] = df[column] / 100

    return df


# ---------------------------------------------------------
# MATCH WNBA MARKETS
# ---------------------------------------------------------

def match_markets(
    census_df,
    market_df,
):

    census_df = census_df.copy()
    market_df = market_df.copy()

    census_df["cbsa_code"] = (
        census_df[
            "metropolitan statistical area/micropolitan statistical area"
        ]
        .astype(str)
        .str.zfill(5)
    )

    market_df["cbsa_code"] = (
        market_df["cbsa_code"]
        .fillna("")
        .astype(str)
        .str.replace(
            ".0",
            "",
            regex=False,
        )
        .str.zfill(5)
    )

    matched = market_df.merge(
        census_df,
        on="cbsa_code",
        how="left",
        suffixes=("", "_census"),
    )

    return matched

def create_derived_metrics(df):
    df = df.copy()

    # -------------------------------------------------
    # Demographic shares
    # -------------------------------------------------

    if "population" in df.columns:
        if "youth_population" in df.columns:
            df["youth_share"] = (
                df["youth_population"] /
                df["population"]
            )

        if "age_18_24" in df.columns:
            df["young_adult_share"] = (
                df["age_18_24"] /
                df["population"]
            )

    # -------------------------------------------------
    # Household characteristics
    # -------------------------------------------------

    if "households" in df.columns:
        if "households_with_children" in df.columns:
            df["households_with_children_share"] = (
                df["households_with_children"] /
                df["households"]
            )

    # -------------------------------------------------
    # Income per household
    # -------------------------------------------------

    if "median_household_income" in df.columns:
        df["median_household_income"] = pd.to_numeric(
            df["median_household_income"],
            errors="coerce"
        )

    # -------------------------------------------------
    # Housing density
    # -------------------------------------------------

    if "housing_units" in df.columns:
        df["housing_units_per_100k"] = (
            df["housing_units"] /
            df["population"] *
            100_000
        )

    return df


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_market_data(df):

    print("\n--- MARKET DATA VALIDATION ---")

    print(
        f"Number of WNBA teams: {len(df)}"
    )

    print(
        f"Teams matched to Census: "
        f"{df['population'].notna().sum()}"
    )

    print(
        f"Teams missing Census data: "
        f"{df['population'].isna().sum()}"
    )

    print("\nMissing values:")

    print(
        df[
            [
                "team_name",
                "population",
                "median_household_income",
                "households",
            ]
        ]
        .isna()
        .sum()
    )

    print("\nMarket populations:")

    print(
        df[
            [
                "team_name",
                "cbsa_name",
                "population",
            ]
        ]
        .sort_values(
            "population",
            ascending=False,
        )
        .to_string(index=False)
    )


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

def save_processed_data(df):

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        PROCESSED_DIR
        / "wnba_market_demographics.csv"
    )

    df.to_csv(
        output_path,
        index=False,
    )

    print(
        f"\nSaved processed data to:\n{output_path}"
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    census_df = load_census_data()

    market_df = load_markets()

    census_df = clean_census_data(
        census_df
    )

    matched_df = match_markets(
        census_df,
        market_df,
    )

    matched_df = create_derived_metrics(
        matched_df
    )

    validate_market_data(
        matched_df
    )

    save_processed_data(
        matched_df
    )


if __name__ == "__main__":
    main()