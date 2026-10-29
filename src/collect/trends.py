import sys
import time
from pathlib import Path

import pandas as pd
from pytrends.request import TrendReq

# -------------------------------------------------------------------
# PROJECT PATHS
# -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.config import CONFIG_DIR, TRENDS_RAW_DIR


# -------------------------------------------------------------------
# SETTINGS
# -------------------------------------------------------------------

START_YEAR = 2021
END_YEAR = 2026

# Google Trends works best when requests are kept relatively small.
# We will collect one team at a time.
SLEEP_SECONDS = 2

# Search terms used for each franchise.
#
# We want the team itself rather than generic searches such as
# "Wings", which could produce unrelated results.
#
# These are deliberately kept simple for the first collection pass.
TREND_TERMS = {
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
    "WAS": "Washington Mystics",
}


# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

def load_markets():
    """
    Load market configuration.

    The markets file contains the DMA/CBSA information that will
    eventually be used to connect teams to their local markets.
    """
    markets_path = CONFIG_DIR / "markets.csv"

    markets = pd.read_csv(markets_path)

    return markets


def get_dma_name(pytrends, search_term):
    """
    Find the Google Trends DMA associated with a search term.

    This is a discovery step rather than something we should hard-code
    based solely on the team's city.
    """

    print(f"\nFinding DMA for: {search_term}")

    pytrends.build_payload(
        kw_list=[search_term],
        timeframe="today 5-y",
        geo="US",
    )

    regional = pytrends.interest_by_region(
        resolution="DMA",
        inc_low_vol=True,
        inc_geo_code=True,
    )

    if regional.empty:
        print("  No DMA results returned.")
        return regional

    regional = regional.reset_index()

    return regional


def collect_dma_interest(pytrends, search_term, timeframe):
    """
    Collect Google Trends interest by DMA for a search term.

    Returns one row per DMA.
    """

    print(
        f"Collecting Trends data | "
        f"term='{search_term}' | "
        f"timeframe='{timeframe}'"
    )

    pytrends.build_payload(
        kw_list=[search_term],
        timeframe=timeframe,
        geo="US",
    )

    regional = pytrends.interest_by_region(
        resolution="DMA",
        inc_low_vol=True,
        inc_geo_code=True,
    )

    if regional.empty:
        return pd.DataFrame()

    regional = regional.reset_index()

    # Rename the geography column consistently.
    geography_column = regional.columns[0]

    regional = regional.rename(
        columns={
            geography_column: "dma_name",
            search_term: "trends_interest",
        }
    )

    regional["search_term"] = search_term
    regional["timeframe"] = timeframe

    return regional


def collect_team_year(pytrends, team_id, search_term, year):
    """
    Collect annual DMA-level Trends data for one team.
    """

    timeframe = f"{year}-01-01 {year}-12-31"

    regional = collect_dma_interest(
        pytrends=pytrends,
        search_term=search_term,
        timeframe=timeframe,
    )

    if regional.empty:
        return pd.DataFrame()

    regional["team_id"] = team_id
    regional["season"] = year

    return regional[
        [
            "season",
            "team_id",
            "search_term",
            "dma_name",
            "trends_interest",
        ]
    ]


# -------------------------------------------------------------------
# MAIN COLLECTION
# -------------------------------------------------------------------

def main():

    print("\n" + "=" * 70)
    print("GOOGLE TRENDS COLLECTION")
    print("=" * 70)

    # Create output directory if needed.
    TRENDS_RAW_DIR.mkdir(parents=True, exist_ok=True)

    print("\nInitializing Google Trends connection...")

    pytrends = TrendReq(
        hl="en-US",
        tz=360,
        retries=2,
        backoff_factor=0.5,
    )

    all_results = []

    for team_id, search_term in TREND_TERMS.items():

        print("\n" + "-" * 70)
        print(f"{team_id}: {search_term}")
        print("-" * 70)

        for year in range(START_YEAR, END_YEAR + 1):

            try:

                result = collect_team_year(
                    pytrends=pytrends,
                    team_id=team_id,
                    search_term=search_term,
                    year=year,
                )

                if result.empty:
                    print(
                        f"  {year}: No data returned."
                    )
                else:
                    print(
                        f"  {year}: "
                        f"{len(result)} DMA rows collected."
                    )

                    all_results.append(result)

            except Exception as exc:

                print(
                    f"  {year}: ERROR -> {exc}"
                )

            # Give Google Trends some breathing room.
            time.sleep(SLEEP_SECONDS)

    # ----------------------------------------------------------------
    # COMBINE RESULTS
    # ----------------------------------------------------------------

    if not all_results:
        raise RuntimeError(
            "No Google Trends data was collected."
        )

    trends = pd.concat(
        all_results,
        ignore_index=True,
    )

    # ----------------------------------------------------------------
    # BASIC CLEANING
    # ----------------------------------------------------------------

    trends["season"] = pd.to_numeric(
        trends["season"],
        errors="coerce",
    )

    trends["trends_interest"] = pd.to_numeric(
        trends["trends_interest"],
        errors="coerce",
    )

    trends = trends.dropna(
        subset=[
            "season",
            "team_id",
            "dma_name",
        ]
    )

    trends["season"] = trends["season"].astype(int)

    # Remove duplicate team/year/DMA observations.
    trends = trends.drop_duplicates(
        subset=[
            "season",
            "team_id",
            "dma_name",
        ]
    )

    # ----------------------------------------------------------------
    # SAVE
    # ----------------------------------------------------------------

    output_path = (
        TRENDS_RAW_DIR /
        "wnba_trends_dma_raw.csv"
    )

    trends.to_csv(
        output_path,
        index=False,
    )

    # ----------------------------------------------------------------
    # VALIDATION
    # ----------------------------------------------------------------

    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)

    print(
        f"\nRows collected: {len(trends):,}"
    )

    print(
        f"Teams collected: "
        f"{trends['team_id'].nunique()}"
    )

    print(
        f"Years collected: "
        f"{sorted(trends['season'].unique())}"
    )

    print(
        f"DMAs represented: "
        f"{trends['dma_name'].nunique()}"
    )

    print("\nRows by team:")

    print(
        trends.groupby("team_id")
        .size()
        .sort_values(ascending=False)
        .to_string()
    )

    print("\nRows by year:")

    print(
        trends.groupby("season")
        .size()
        .to_string()
    )

    print("\nSample rows:")

    print(
        trends.head(20).to_string(index=False)
    )

    print(
        f"\nSaved to:\n{output_path}"
    )

    print("\nGoogle Trends collection complete.")


if __name__ == "__main__":
    main()