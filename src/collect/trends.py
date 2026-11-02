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

START_DATE = "2021-01-01"
END_DATE = "2026-10-31"

SLEEP_SECONDS = 2

# -------------------------------------------------------------------
# SEARCH TERMS
# -------------------------------------------------------------------

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
# LOCAL DMA MAPPING
# -------------------------------------------------------------------
#
# IMPORTANT:
# Enter the DMA name EXACTLY as it appears in your existing
# wnba_trends_dma_raw.csv file.
#
# We will use these names to discover Google's corresponding
# geographic codes automatically.
#
# Toronto is intentionally excluded for now because our Google
# Trends DMA collection is U.S.-based.
#
# If a team has multiple relevant DMAs, you can add more than one:
#
# "DAL": ["Dallas-Ft. Worth TX", "another DMA"],
#
# For now, use one primary DMA per team.
# -------------------------------------------------------------------

LOCAL_DMAS = {
    "ATL": "Atlanta GA",
    "CHI": "Chicago IL",
    "CON": "Hartford & New Haven CT",
    "DAL": "Dallas-Ft. Worth TX",
    "GSV": "San Francisco-Oakland-San Jose CA",
    "IND": "Indianapolis IN",
    "LVA": "Las Vegas NV",
    "LAS": "Los Angeles CA",
    "MIN": "Minneapolis-St. Paul MN",
    "NYL": "New York NY",
    "PHX": "Phoenix AZ",
    "POR": "Portland OR",
    "SEA": "Seattle-Tacoma WA",
    "WAS": "Washington DC (Hagerstown MD)",
}


# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

def get_dma_lookup(pytrends, search_term):
    """
    Retrieve Google's DMA names and geographic codes for a search term.

    Returns:
        DataFrame with:
            dma_name
            geo_code
            trends_interest
    """

    print(f"Finding DMA codes for: {search_term}")

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
        return pd.DataFrame()

    regional = regional.reset_index()

    geography_column = regional.columns[0]

    regional = regional.rename(
        columns={
            geography_column: "dma_name",
            search_term: "trends_interest",
        }
    )

    # Find the geographic code column.
    geo_code_column = None

    for column in regional.columns:
        if column.lower() == "geocode":
            geo_code_column = column
            break

    if geo_code_column is None:
        raise ValueError(
            "Google Trends did not return a DMA geoCode column."
        )

    regional = regional.rename(
        columns={
            geo_code_column: "geo_code"
        }
    )

    return regional[
        [
            "dma_name",
            "geo_code",
        ]
    ].drop_duplicates()


def find_dma_code(
    pytrends,
    search_term,
    requested_dma,
):
    """
    Find the Google Trends geographic code for a manually specified DMA.
    """

    lookup = get_dma_lookup(
        pytrends=pytrends,
        search_term=search_term,
    )

    if lookup.empty:
        raise ValueError(
            f"No DMA data returned while searching for "
            f"{search_term}."
        )

    match = lookup[
        lookup["dma_name"].str.lower()
        == requested_dma.lower()
    ]

    if match.empty:

        possible_matches = lookup[
            lookup["dma_name"]
            .str.lower()
            .str.contains(
                requested_dma.lower(),
                na=False,
            )
        ]

        if not possible_matches.empty:

            print(
                "\nPossible DMA matches:"
            )

            print(
                possible_matches.to_string(
                    index=False
                )
            )

        raise ValueError(
            f"\nCould not find exact DMA match:\n"
            f"'{requested_dma}'\n\n"
            f"Please use the exact DMA name returned "
            f"by Google Trends."
        )

    return match.iloc[0]["geo_code"]


def collect_local_monthly(
    pytrends,
    team_id,
    search_term,
    dma_name,
    geo_code,
):
    """
    Collect monthly Google Trends interest for one team
    within one specific DMA.

    The entire study period is requested in one query so
    the resulting 0-100 normalization remains internally
    consistent across the full time series.
    """

    timeframe = (
        f"{START_DATE} {END_DATE}"
    )

    print(
        f"\nCollecting local monthly data:"
    )

    print(
        f"  Team: {team_id}"
    )

    print(
        f"  Search term: {search_term}"
    )

    print(
        f"  DMA: {dma_name}"
    )

    print(
        f"  Geo code: {geo_code}"
    )

    print(
        f"  Timeframe: {timeframe}"
    )

    pytrends.build_payload(
        kw_list=[search_term],
        timeframe=timeframe,
        geo=geo_code,
    )

    interest = pytrends.interest_over_time()

    print(
        f"\nReturned data for {team_id}: "
        f"{len(interest)} rows"
    )

    if interest.empty:
        print(f"WARNING: EMPTY RESULT FOR {team_id}")
    else:
        print(f"Columns returned: {interest.columns.tolist()}")
    
    if interest.empty:
        return pd.DataFrame()

    interest = interest.reset_index()

    # Rename the search term column.
    interest = interest.rename(
        columns={
            search_term: "trends_interest"
        }
    )

    # Remove Google's partial-period flag.
    if "isPartial" in interest.columns:
        interest = interest.drop(
            columns=["isPartial"]
        )

    interest["team_id"] = team_id
    interest["team_name"] = search_term
    interest["dma_name"] = dma_name
    interest["geo_code"] = geo_code

    # Convert date to datetime.
    interest["date"] = pd.to_datetime(
        interest["date"]
    )

    # Google Trends should normally provide monthly
    # observations for a sufficiently long timeframe.
    interest["year"] = interest["date"].dt.year
    interest["month"] = interest["date"].dt.month

    interest["trends_interest"] = pd.to_numeric(
        interest["trends_interest"],
        errors="coerce",
    )

    return interest[
        [
            "date",
            "year",
            "month",
            "team_id",
            "team_name",
            "dma_name",
            "geo_code",
            "trends_interest",
        ]
    ]


# -------------------------------------------------------------------
# MAIN COLLECTION
# -------------------------------------------------------------------

def main():

    print("\n" + "=" * 70)
    print("GOOGLE TRENDS — LOCAL MONTHLY COLLECTION")
    print("=" * 70)

    # ---------------------------------------------------------------
    # Validate DMA configuration
    # ---------------------------------------------------------------

    print("\nChecking local DMA configuration...")

    missing_dmas = []

    for team_id in TREND_TERMS:

        if team_id not in LOCAL_DMAS:
            missing_dmas.append(team_id)

        elif LOCAL_DMAS[team_id].startswith(
            "REPLACE_WITH_"
        ):
            missing_dmas.append(team_id)

    if missing_dmas:

        print(
            "\nThe following teams still need DMA names:"
        )

        for team_id in missing_dmas:
            print(
                f"  {team_id}: "
                f"{TREND_TERMS[team_id]}"
            )

        raise ValueError(
            "\nPlease fill in LOCAL_DMAS before "
            "running the collector."
        )

    # ---------------------------------------------------------------
    # Create output directory
    # ---------------------------------------------------------------

    TRENDS_RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Initialize Google Trends
    # ---------------------------------------------------------------

    print(
        "\nInitializing Google Trends connection..."
    )

    pytrends = TrendReq(
        hl="en-US",
        tz=360,
        retries=2,
        backoff_factor=0.5,
    )

    all_results = []

    # ---------------------------------------------------------------
    # Collect each team
    # ---------------------------------------------------------------

    for team_id, search_term in TREND_TERMS.items():

        print("\n" + "-" * 70)
        print(
            f"{team_id}: {search_term}"
        )
        print("-" * 70)

        dma_name = LOCAL_DMAS[team_id]

        try:

            # -------------------------------------------------------
            # Find Google's geographic code
            # -------------------------------------------------------

            geo_code = find_dma_code(
                pytrends=pytrends,
                search_term=search_term,
                requested_dma=dma_name,
            )

            print(
                f"  Matched DMA:"
                f" {dma_name}"
            )

            print(
                f"  Google geo code:"
                f" {geo_code}"
            )

            time.sleep(
                SLEEP_SECONDS
            )

            # -------------------------------------------------------
            # Collect monthly interest
            # -------------------------------------------------------

            result = collect_local_monthly(
                pytrends=pytrends,
                team_id=team_id,
                search_term=search_term,
                dma_name=dma_name,
                geo_code=geo_code,
            )

            if result.empty:

                print(
                    "  No monthly data returned."
                )

            else:

                print(
                    f"  {len(result)} "
                    f"monthly observations collected."
                )

                print(
                    f"Appending {team_id}: "
                    f"{len(result)} rows"
                )

                all_results.append(
                    result
                )

        except Exception as exc:

            print(
                f"\n  ERROR -> {exc}"
            )

        time.sleep(
            SLEEP_SECONDS
        )

    # ---------------------------------------------------------------
    # Combine
    # ---------------------------------------------------------------

    if not all_results:

        raise RuntimeError(
            "No local Google Trends data "
            "was collected."
        )

    print("\n" + "=" * 70)
    print("COLLECTION RESULTS BEFORE CONCAT")
    print("=" * 70)

    print(f"Number of result objects: {len(all_results)}")

    for i, result in enumerate(all_results):
        print(
            f"Result {i}: "
            f"type={type(result).__name__}, "
            f"rows={len(result)}"
        )

        if isinstance(result, pd.DataFrame) and not result.empty:
            print(
                f"  teams: "
                f"{result['team_id'].unique().tolist()}"
            )

    print("\nExpected teams:")
    print(sorted(LOCAL_DMAS.keys()))


    trends = pd.concat(
        all_results,
        ignore_index=True,
    )

    # ---------------------------------------------------------------
    # Clean
    # ---------------------------------------------------------------

    trends["date"] = pd.to_datetime(
        trends["date"],
        errors="coerce",
    )

    trends["year"] = pd.to_numeric(
        trends["year"],
        errors="coerce",
    )

    trends["month"] = pd.to_numeric(
        trends["month"],
        errors="coerce",
    )

    trends["trends_interest"] = pd.to_numeric(
        trends["trends_interest"],
        errors="coerce",
    )

    trends = trends.dropna(
        subset=[
            "date",
            "team_id",
            "dma_name",
            "trends_interest",
        ]
    )

    trends["year"] = trends[
        "year"
    ].astype(int)

    trends["month"] = trends[
        "month"
    ].astype(int)

    # ---------------------------------------------------------------
    # Remove duplicates
    # ---------------------------------------------------------------

    trends = trends.drop_duplicates(
        subset=[
            "date",
            "team_id",
            "dma_name",
        ]
    )

    trends = trends.sort_values(
        [
            "team_id",
            "date",
        ]
    ).reset_index(
        drop=True
    )

    # ---------------------------------------------------------------
    # Save
    # ---------------------------------------------------------------

    output_path = (
        TRENDS_RAW_DIR
        / "wnba_trends_local_monthly.csv"
    )

    # ---------------------------------------------------------------
    # Missing teams debugging
    # ---------------------------------------------------------------

    print("\nFinal data before saving:")
    print(f"Rows: {len(trends):,}")
    print(f"Teams: {trends['team_id'].nunique()}")

    print("\nTeams in final dataframe:")
    print(
        trends[
            ["team_id", "team_name", "dma_name"]
        ]
        .drop_duplicates()
        .sort_values("team_id")
        .to_string(index=False)
    )

    print("\nRows by team:")
    print(
        trends.groupby("team_id")
        .size()
        .sort_index()
    )

    trends.to_csv(
        output_path,
        index=False,
    )

    # ---------------------------------------------------------------
    # Validation
    # ---------------------------------------------------------------

    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)

    print(
        f"\nRows collected: "
        f"{len(trends):,}"
    )

    print(
        f"Teams collected: "
        f"{trends['team_id'].nunique()}"
    )

    print(
        f"Date range: "
        f"{trends['date'].min().date()} "
        f"to "
        f"{trends['date'].max().date()}"
    )

    print(
        f"Unique months: "
        f"{trends['date'].nunique()}"
    )

    print("\nRows by team:")

    print(
        trends.groupby("team_id")
        .size()
        .sort_values(
            ascending=False
        )
        .to_string()
    )

    print("\nDMA mapping:")

    print(
        trends[
            [
                "team_id",
                "team_name",
                "dma_name",
                "geo_code",
            ]
        ]
        .drop_duplicates()
        .sort_values("team_id")
        .to_string(
            index=False
        )
    )

    print(
        "\nInterest summary:"
    )

    print(
        trends[
            "trends_interest"
        ].describe().to_string()
    )

    print(
        "\nSample rows:"
    )

    print(
        trends.head(20)
        .to_string(index=False)
    )

    print(
        f"\nSaved to:\n"
        f"{output_path}"
    )

    print(
        "\nLocal monthly Google Trends "
        "collection complete."
    )


if __name__ == "__main__":
    main()