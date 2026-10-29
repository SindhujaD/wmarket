import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.config import (
    WNBA_RAW_DIR,
    PROCESSED_DIR,
)


TEAM_NAME_MAPPING = {
    "Atlanta Dream": "ATL",
    "Chicago Sky": "CHI",
    "Connecticut Sun": "CON",
    "Dallas Wings": "DAL",
    "Golden State Valkyries": "GSV",
    "Indiana Fever": "IND",
    "Las Vegas Aces": "LVA",
    "Los Angeles Sparks": "LAS",
    "Minnesota Lynx": "MIN",
    "New York Liberty": "NYL",
    "Phoenix Mercury": "PHX",
    "Portland Fire": "POR",
    "Seattle Storm": "SEA",
    "Toronto Tempo": "TOR",
    "Washington Mystics": "WAS",
}


def load_data():

    path = (
        WNBA_RAW_DIR /
        "wnba_standings_2021_2026_raw.csv"
    )

    return pd.read_csv(path)


def clean_team_name(name):

    if pd.isna(name):
        return None

    name = str(name)

    # Remove playoff marker
    name = name.replace("*", "").strip()

    return name


def clean_data(df):

    df = df.copy()

    # Identify team column
    if "Team" in df.columns:
        df["team_name"] = (
            df["Team"]
            .apply(clean_team_name)
        )

    elif "Team" not in df.columns:
        raise ValueError(
            "Could not find Team column."
        )

    # Map team IDs
    df["team_id"] = (
        df["team_name"]
        .map(TEAM_NAME_MAPPING)
    )

    # Numeric fields
    for column in ["W", "L"]:

        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # Win percentage
    df["win_pct"] = (
        df["W"] /
        (df["W"] + df["L"])
    )

    # Playoff appearance
    df["playoff_appearance"] = (
        df["Team"]
        .astype(str)
        .str.contains("*", regex=False)
        .astype(int)
    )

    return df


def validate(df):

    print("\n--- WNBA VALIDATION ---")

    print(
        f"Rows: {len(df):,}"
    )

    print(
        f"Seasons: "
        f"{df['season'].min()} - "
        f"{df['season'].max()}"
    )

    print(
        "\nTeams per season:"
    )

    print(
        df.groupby("season")
        ["team_id"]
        .nunique()
    )

    print(
        "\nUnmatched teams:"
    )

    print(
        df.loc[
            df["team_id"].isna(),
            "team_name"
        ].unique()
    )


def save(df):

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        PROCESSED_DIR /
        "wnba_team_season.csv"
    )

    df.to_csv(
        output_path,
        index=False
    )

    print(
        f"\nSaved:\n{output_path}"
    )


def main():

    df = load_data()

    df = clean_data(df)

    validate(df)

    save(df)


if __name__ == "__main__":
    main()