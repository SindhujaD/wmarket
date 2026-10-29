import sys
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# PROJECT PATH
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.config import (
    PROCESSED_DIR,
    WNBA_RAW_DIR,
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

def load_attendance():

    path = (
        WNBA_RAW_DIR /
        "wnba_attendance_source.csv"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Attendance file not found:\n{path}"
        )

    return pd.read_csv(path)


# ---------------------------------------------------------
# CLEAN DATA
# ---------------------------------------------------------

def clean_attendance(df):

    df = df.copy()

    # -----------------------------------------------------
    # Numeric columns
    # -----------------------------------------------------

    numeric_columns = [
        "season",
        "average_attendance",
        "average_capacity",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # -----------------------------------------------------
    # Restrict analysis period
    # -----------------------------------------------------

    df = df[
        df["season"].between(2021, 2026)
    ].copy()

    # -----------------------------------------------------
    # Validate attendance
    # -----------------------------------------------------

    df.loc[
        df["average_attendance"] < 0,
        "average_attendance"
    ] = pd.NA

    # -----------------------------------------------------
    # Validate capacity
    # -----------------------------------------------------

    df.loc[
        df["average_capacity"] < 0,
        "average_capacity"
    ] = pd.NA

    # -----------------------------------------------------
    # Capacity utilization
    # -----------------------------------------------------

    # A capacity of zero represents a season in which
    # attendance was not available because fans were not
    # admitted, such as Indiana in 2021.
    #
    # We therefore do NOT calculate utilization for
    # capacity == 0.

    df["capacity_utilization"] = pd.NA

    valid_capacity = (
        df["average_capacity"] > 0
    )

    df.loc[
        valid_capacity,
        "capacity_utilization"
    ] = (
        df.loc[
            valid_capacity,
            "average_attendance"
        ]
        /
        df.loc[
            valid_capacity,
            "average_capacity"
        ]
    )

    # Percentage version
    df["capacity_utilization_pct"] = (
        df["capacity_utilization"] * 100
    )

    # -----------------------------------------------------
    # Flag unusual values
    # -----------------------------------------------------

    df["capacity_utilization_flag"] = "normal"

    df.loc[
        df["average_capacity"] == 0,
        "capacity_utilization_flag"
    ] = "no_capacity"

    df.loc[
        df["capacity_utilization"] > 1,
        "capacity_utilization_flag"
    ] = "over_capacity"

    return df


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate(df):

    print("\n" + "=" * 70)
    print("WNBA ATTENDANCE VALIDATION")
    print("=" * 70)

    print(
        f"\nRows: {len(df):,}"
    )

    print("\nSeasons:")

    print(
        sorted(
            df["season"]
            .dropna()
            .astype(int)
            .unique()
        )
    )

    # -----------------------------------------------------
    # Team counts
    # -----------------------------------------------------

    print("\nTeams by season:")

    team_counts = (
        df
        .groupby("season")["team_id"]
        .nunique()
    )

    print(team_counts)

    # -----------------------------------------------------
    # Missing values
    # -----------------------------------------------------

    print("\nMissing values:")

    print(
        df[
            [
                "season",
                "team_id",
                "average_attendance",
                "average_capacity",
                "capacity_utilization",
            ]
        ]
        .isna()
        .sum()
    )

    # -----------------------------------------------------
    # Duplicate team-season rows
    # -----------------------------------------------------

    duplicates = df[
        df.duplicated(
            subset=[
                "season",
                "team_id"
            ],
            keep=False
        )
    ]

    print(
        "\nDuplicate team-season rows:"
    )

    if duplicates.empty:
        print("None")
    else:
        print(
            duplicates[
                [
                    "season",
                    "team_id",
                    "team_name",
                ]
            ]
            .to_string(index=False)
        )

    # -----------------------------------------------------
    # Over-capacity observations
    # -----------------------------------------------------

    print(
        "\nObservations where attendance "
        "exceeds average capacity:"
    )

    over_capacity = df[
        df["capacity_utilization"] > 1
    ]

    if over_capacity.empty:

        print("None")

    else:

        print(
            over_capacity[
                [
                    "season",
                    "team_id",
                    "team_name",
                    "average_attendance",
                    "average_capacity",
                    "capacity_utilization_pct",
                ]
            ]
            .sort_values(
                "capacity_utilization_pct",
                ascending=False
            )
            .to_string(index=False)
        )

    # -----------------------------------------------------
    # Zero-capacity observations
    # -----------------------------------------------------

    print(
        "\nZero-capacity observations:"
    )

    zero_capacity = df[
        df["average_capacity"] == 0
    ]

    if zero_capacity.empty:

        print("None")

    else:

        print(
            zero_capacity[
                [
                    "season",
                    "team_id",
                    "team_name",
                    "average_attendance",
                    "average_capacity",
                ]
            ]
            .to_string(index=False)
        )

    # -----------------------------------------------------
    # Utilization summary
    # -----------------------------------------------------

    print(
        "\nCapacity utilization summary:"
    )

    print(
        df["capacity_utilization"]
        .describe()
    )

    # -----------------------------------------------------
    # Highest utilization
    # -----------------------------------------------------

    print(
        "\nHighest capacity utilization:"
    )

    print(
        df[
            [
                "season",
                "team_name",
                "capacity_utilization_pct",
            ]
        ]
        .dropna()
        .sort_values(
            "capacity_utilization_pct",
            ascending=False
        )
        .head(15)
        .to_string(index=False)
    )


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

def save(df):

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        PROCESSED_DIR /
        "wnba_attendance.csv"
    )

    df.to_csv(
        output_path,
        index=False
    )

    print(
        f"\nSaved cleaned attendance data to:"
        f"\n{output_path}"
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print(
        "\nCleaning WNBA attendance data..."
    )

    df = load_attendance()

    df = clean_attendance(df)

    validate(df)

    save(df)

    print(
        "\nAttendance cleaning complete."
    )


if __name__ == "__main__":
    main()