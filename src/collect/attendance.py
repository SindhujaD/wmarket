import sys
from pathlib import Path
import pandas as pd

# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.config import WNBA_RAW_DIR


# ---------------------------------------------------------
# TEAM INFORMATION
# ---------------------------------------------------------

TEAM_INFO = {
    "ATL": "Atlanta Dream",
    "CHI": "Chicago Sky",
    "CON": "Connecticut Sun",
    "DAL": "Dallas Wings",
    "GSV": "Golden State Valkyries",
    "IND": "Indiana Fever",
    "LVA": "Las Vegas Aces",
    "LAS": "Los Angeles Sparks",
    "MIN": "Minnesota Lynx",
    "NYL": "New York Liberty",
    "PHX": "Phoenix Mercury",
    "POR": "Portland Fire",
    "SEA": "Seattle Storm",
    "TOR": "Toronto Tempo",
    "WAS": "Washington Mystics",
}


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

START_YEAR = 2021
END_YEAR = 2026

INPUT_FILE = WNBA_RAW_DIR / "wnba_attendance_source.csv"
OUTPUT_FILE = WNBA_RAW_DIR / "wnba_attendance.csv"


# ---------------------------------------------------------
# LOAD SOURCE DATA
# ---------------------------------------------------------

def load_source_data():
    """
    Load the manually/source-collected attendance data.

    Expected columns:

        season
        team_id
        team_name
        average_attendance
        arena_capacity
    """

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"\nAttendance source file not found:\n{INPUT_FILE}\n\n"
            "Create the file first and populate it with attendance data."
        )

    df = pd.read_csv(INPUT_FILE)

    return df


# ---------------------------------------------------------
# STANDARDIZE TEAM NAMES
# ---------------------------------------------------------

def standardize_team_names(df):

    df = df.copy()

    # Fill team_name from team_id when possible
    df["team_name"] = df["team_id"].map(TEAM_INFO)

    return df


# ---------------------------------------------------------
# CLEAN DATA TYPES
# ---------------------------------------------------------

def clean_data(df):

    df = df.copy()

    # Convert numeric fields
    df["season"] = pd.to_numeric(
        df["season"],
        errors="coerce"
    )

    df["average_attendance"] = pd.to_numeric(
        df["average_attendance"],
        errors="coerce"
    )

    df["arena_capacity"] = pd.to_numeric(
        df["arena_capacity"],
        errors="coerce"
    )

    # Keep only requested seasons
    df = df[
        df["season"].between(
            START_YEAR,
            END_YEAR
        )
    ]

    # Invalid attendance values
    df.loc[
        df["average_attendance"] < 0,
        "average_attendance"
    ] = pd.NA

    # Invalid arena capacities
    df.loc[
        df["arena_capacity"] <= 0,
        "arena_capacity"
    ] = pd.NA

    return df


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_data(df):

    print("\n" + "=" * 60)
    print("ATTENDANCE DATA VALIDATION")
    print("=" * 60)

    print(f"\nRows: {len(df):,}")

    print("\nSeasons:")
    print(
        sorted(
            df["season"]
            .dropna()
            .astype(int)
            .unique()
            .tolist()
        )
    )

    print("\nTeams:")
    print(
        df["team_id"]
        .dropna()
        .unique()
        .tolist()
    )

    print("\nMissing values:")
    print(
        df[
            [
                "season",
                "team_id",
                "team_name",
                "average_attendance",
                "arena_capacity",
            ]
        ].isna().sum()
    )

    # Check for duplicate team-season combinations
    duplicates = df[
        df.duplicated(
            subset=["season", "team_id"],
            keep=False
        )
    ]

    print(
        f"\nDuplicate team-season rows: "
        f"{len(duplicates)}"
    )

    if len(duplicates) > 0:
        print(duplicates)

    # Check attendance against capacity
    df["capacity_utilization"] = (
        df["average_attendance"]
        / df["arena_capacity"]
    )

    print("\nCapacity utilization summary:")
    print(
        df["capacity_utilization"]
        .describe()
    )

    # Flag suspicious values
    suspicious = df[
        df["capacity_utilization"] > 1.10
    ]

    print(
        "\nAttendance > 110% of listed arena capacity:"
    )

    if suspicious.empty:
        print("None")
    else:
        print(
            suspicious[
                [
                    "season",
                    "team_id",
                    "team_name",
                    "average_attendance",
                    "arena_capacity",
                    "capacity_utilization",
                ]
            ].to_string(index=False)
        )


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

def save_data(df):

    # Remove validation-only column
    if "capacity_utilization" in df.columns:
        df = df.drop(
            columns=["capacity_utilization"]
        )

    WNBA_RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"\nSaved attendance data to:\n"
        f"{OUTPUT_FILE}"
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("\nCollecting WNBA attendance data...")

    df = load_source_data()

    df = standardize_team_names(df)

    df = clean_data(df)

    validate_data(df)

    save_data(df)

    print("\nAttendance collection complete.")


if __name__ == "__main__":
    main()