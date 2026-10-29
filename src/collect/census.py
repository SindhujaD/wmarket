import sys
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
import os


# ---------------------------------------------------------
# PROJECT PATH
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

from src.config import (
    CENSUS_BASE_URL,
    CENSUS_RAW_DIR,
    CENSUS_YEAR,
)


# Load environment variables from .env
load_dotenv(PROJECT_ROOT / ".env")

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")


# ---------------------------------------------------------
# CENSUS VARIABLES
# ---------------------------------------------------------

CENSUS_VARIABLES = {
    "population": "DP05_0001E",
    "median_age": "DP05_0018E",
    "median_household_income": "DP03_0062E",
    "per_capita_income": "DP03_0088E",
    "poverty_rate": "DP03_0128PE",
    "bachelors_plus": "DP02_0068PE",
    "labor_force_participation": "DP03_0002PE",
    "unemployment_rate": "DP03_0009PE",
    "households": "DP02_0001E",
    "households_with_children": "DP02_0016E",
}


# ---------------------------------------------------------
# DOWNLOAD CENSUS DATA
# ---------------------------------------------------------

def get_census_data():

    if not CENSUS_API_KEY:
        raise ValueError(
            "CENSUS_API_KEY was not found.\n\n"
            "Make sure you have a .env file in the project root "
            "containing:\n\n"
            "CENSUS_API_KEY=your_key_here"
        )

    variables = [
        "NAME",
        *CENSUS_VARIABLES.values(),
    ]

    params = {
        "get": ",".join(variables),
        "for": "metropolitan statistical area/micropolitan statistical area:*",
        "key": CENSUS_API_KEY,
    }

    print("Sending request to Census API...")

    response = requests.get(
        CENSUS_BASE_URL,
        params=params,
        timeout=60,
    )

    # -----------------------------------------------------
    # Better error handling
    # -----------------------------------------------------

    if response.status_code != 200:

        print("\nCensus API request failed.")
        print(f"Status code: {response.status_code}")
        print("\nResponse from Census:")
        print(response.text[:2000])

        response.raise_for_status()

    try:
        data = response.json()

    except ValueError:

        print("\nCensus API did not return valid JSON.")
        print("\nResponse:")
        print(response.text[:2000])

        raise

    if len(data) < 2:
        raise ValueError(
            "Census API returned no data rows."
        )

    # -----------------------------------------------------
    # Convert response to DataFrame
    # -----------------------------------------------------

    df = pd.DataFrame(
        data[1:],
        columns=data[0],
    )

    return df


# ---------------------------------------------------------
# RENAME COLUMNS
# ---------------------------------------------------------

def rename_columns(df):

    reverse_mapping = {
        value: key
        for key, value in CENSUS_VARIABLES.items()
    }

    reverse_mapping["NAME"] = "cbsa_name"

    return df.rename(
        columns=reverse_mapping
    )


# ---------------------------------------------------------
# CONVERT NUMERIC COLUMNS
# ---------------------------------------------------------

def convert_numeric(df):

    geography_column = (
        "metropolitan statistical area/"
        "micropolitan statistical area"
    )

    numeric_columns = [
        column
        for column in df.columns
        if column not in [
            "cbsa_name",
            geography_column,
        ]
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df


# ---------------------------------------------------------
# SAVE RAW DATA
# ---------------------------------------------------------

def save_raw_data(df):

    CENSUS_RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        CENSUS_RAW_DIR
        / f"acs5_{CENSUS_YEAR}_metro_raw.csv"
    )

    df.to_csv(
        output_path,
        index=False,
    )

    print(
        f"\nSaved Census data to:\n"
        f"{output_path}"
    )

    return output_path


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print(
        f"Downloading ACS {CENSUS_YEAR} "
        f"5-year metropolitan data..."
    )

    df = get_census_data()

    print(
        f"Downloaded {len(df):,} "
        f"metropolitan/micropolitan areas."
    )

    df = rename_columns(df)

    df = convert_numeric(df)

    save_raw_data(df)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst five rows:")
    print(df.head())


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

if __name__ == "__main__":
    main()