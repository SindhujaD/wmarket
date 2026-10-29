import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.config import WNBA_RAW_DIR


SEASONS = range(2021, 2027)


def get_season_url(season):
    return (
        f"https://www.basketball-reference.com/"
        f"wnba/years/{season}_standings.html"
    )


def collect_season(season):
    url = get_season_url(season)

    print(f"Downloading {season} WNBA standings...")

    tables = pd.read_html(url)

    # Find the table containing W/L%
    standings = None

    for table in tables:
        columns = [
            str(column)
            for column in table.columns
        ]

        if "W" in columns and "L" in columns:
            standings = table
            break

    if standings is None:
        raise ValueError(
            f"Could not find standings table for {season}"
        )

    standings = standings.copy()

    standings["season"] = season

    return standings


def main():

    WNBA_RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    all_seasons = []

    for season in SEASONS:

        try:
            df = collect_season(season)

            output_path = (
                WNBA_RAW_DIR /
                f"wnba_standings_{season}.csv"
            )

            df.to_csv(
                output_path,
                index=False
            )

            all_seasons.append(df)

            print(
                f"Saved {season} data to "
                f"{output_path}"
            )

        except Exception as error:

            print(
                f"ERROR collecting {season}: "
                f"{error}"
            )

    if all_seasons:

        combined = pd.concat(
            all_seasons,
            ignore_index=True
        )

        combined.to_csv(
            WNBA_RAW_DIR /
            "wnba_standings_2021_2026_raw.csv",
            index=False
        )

        print(
            "\nCombined WNBA standings saved."
        )


if __name__ == "__main__":
    main()