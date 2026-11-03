"""
Digital Engagement Analysis
===========================

Calculates the Local Digital Engagement Score (LDES) for WNBA markets
using local Google Trends data.

LDES methodology
-----------------
Historical period:
    2021-2024

Recent period:
    2025 through the latest available month

Momentum baseline:
    2023-2024

Components:
    Growth      = 40%
    Persistence = 40%
    Momentum    = 20%

Each component is percentile-ranked across established WNBA markets
before calculating the final LDES.

Newer franchises without sufficient historical data are retained in
the raw Trends dataset but excluded from the core LDES benchmark.

Outputs
-------
data/processed/wnba_local_digital_engagement.csv
data/processed/wnba_trends_local_metrics.csv
outputs/tables/digital_engagement_summary.csv
"""


from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

TRENDS_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "trends"
    / "wnba_trends_local_monthly.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

TABLE_OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "tables"
)

LDES_OUTPUT = (
    OUTPUT_DIR
    / "wnba_local_digital_engagement.csv"
)

LOCAL_METRICS_OUTPUT = (
    OUTPUT_DIR
    / "wnba_trends_local_metrics.csv"
)

SUMMARY_OUTPUT = (
    TABLE_OUTPUT_DIR
    / "digital_engagement_summary.csv"
)


# ============================================================
# METHODOLOGY SETTINGS
# ============================================================

HISTORICAL_START = 2021
HISTORICAL_END = 2024

MOMENTUM_START = 2023
MOMENTUM_END = 2024

RECENT_START = 2025

PERSISTENCE_WINDOW = 3

GROWTH_WEIGHT = 0.40
PERSISTENCE_WEIGHT = 0.40
MOMENTUM_WEIGHT = 0.20


# These are the established franchises used for the
# longitudinal LDES benchmark.
#
# Golden State and Portland are retained in the underlying
# Trends data but excluded because they do not have enough
# franchise history for the same longitudinal comparison.

ESTABLISHED_TEAMS = [
    "ATL",
    "CHI",
    "CON",
    "DAL",
    "IND",
    "LVA",
    "LAS",
    "MIN",
    "NYL",
    "PHX",
    "SEA",
    "WAS",
]


# ============================================================
# LOAD DATA
# ============================================================

def load_trends():
    """Load the local monthly Google Trends dataset."""

    if not TRENDS_PATH.exists():
        raise FileNotFoundError(
            f"Google Trends file not found:\n{TRENDS_PATH}"
        )

    df = pd.read_csv(TRENDS_PATH)

    print(
        f"Loaded Google Trends data: "
        f"{len(df):,} rows"
    )

    return df


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(df):
    """
    Standardize the Google Trends dataset.

    The function attempts to identify the team, date, and
    Trends score columns from the current dataset structure.
    """

    df = df.copy()

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
    )

    # --------------------------------------------------------
    # Identify required columns
    # --------------------------------------------------------

    team_candidates = [
        "team_id",
        "team",
        "team_code",
    ]

    date_candidates = [
        "date",
        "month",
    ]

    score_candidates = [
        "trend_score",
        "trends_score",
        "trends_interest",
        "value",
        "score",
    ]

    team_column = next(
        (
            column
            for column in team_candidates
            if column in df.columns
        ),
        None,
    )

    date_column = next(
        (
            column
            for column in date_candidates
            if column in df.columns
        ),
        None,
    )

    score_column = next(
        (
            column
            for column in score_candidates
            if column in df.columns
        ),
        None,
    )

    if team_column is None:
        raise ValueError(
            "Could not identify the team column. "
            f"Available columns: {list(df.columns)}"
        )

    if date_column is None:
        raise ValueError(
            "Could not identify the date column. "
            f"Available columns: {list(df.columns)}"
        )

    if score_column is None:
        raise ValueError(
            "Could not identify the Google Trends score column. "
            f"Available columns: {list(df.columns)}"
        )

    # --------------------------------------------------------
    # Rename to canonical names
    # --------------------------------------------------------

    df = df.rename(
        columns={
            team_column: "team_id",
            date_column: "date",
            score_column: "trend_score",
        }
    )

    # --------------------------------------------------------
    # Clean values
    # --------------------------------------------------------

    df["team_id"] = (
        df["team_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    df["trend_score"] = pd.to_numeric(
        df["trend_score"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Remove invalid rows
    # --------------------------------------------------------

    df = df.dropna(
        subset=[
            "team_id",
            "date",
            "trend_score",
        ]
    ).copy()

    # --------------------------------------------------------
    # Add year/month
    # --------------------------------------------------------

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    df = df.sort_values(
        [
            "team_id",
            "date",
        ]
    ).reset_index(drop=True)

    return df


# ============================================================
# VALIDATE RAW TRENDS DATA
# ============================================================

def validate_trends(df):
    """Validate the local monthly Trends dataset."""

    print("\n" + "=" * 60)
    print("GOOGLE TRENDS VALIDATION")
    print("=" * 60)

    print(
        f"\nRows: {len(df):,}"
    )

    print(
        f"Teams: {df['team_id'].nunique()}"
    )

    print(
        f"Date range: "
        f"{df['date'].min().date()} "
        f"to "
        f"{df['date'].max().date()}"
    )

    print(
        "\nRows by team:"
    )

    print(
        df.groupby("team_id")
        .size()
        .sort_index()
        .to_string()
    )

    # --------------------------------------------------------
    # Check duplicates
    # --------------------------------------------------------

    duplicates = df.duplicated(
        subset=[
            "team_id",
            "date",
        ]
    ).sum()

    print(
        f"\nDuplicate team-month rows: {duplicates}"
    )

    if duplicates > 0:
        raise ValueError(
            "Duplicate team-month rows detected."
        )

    # --------------------------------------------------------
    # Check Trends score range
    # --------------------------------------------------------

    invalid_scores = (
        (df["trend_score"] < 0)
        | (df["trend_score"] > 100)
    ).sum()

    print(
        f"Invalid Trends scores: {invalid_scores}"
    )

    if invalid_scores > 0:
        raise ValueError(
            "Google Trends scores outside 0-100 detected."
        )

    # --------------------------------------------------------
    # Check established teams
    # --------------------------------------------------------

    available_teams = set(
        df["team_id"].unique()
    )

    missing_established = sorted(
        set(ESTABLISHED_TEAMS)
        - available_teams
    )

    if missing_established:
        raise ValueError(
            "Established teams missing from Trends data: "
            f"{missing_established}"
        )

    print(
        "\nEstablished-market benchmark teams:"
    )

    print(
        ", ".join(ESTABLISHED_TEAMS)
    )


# ============================================================
# CALCULATE TEAM METRICS
# ============================================================

def calculate_team_metrics(df):
    """
    Calculate the three longitudinal digital engagement
    components for each team.
    """

    results = []

    latest_date = df["date"].max()

    for team_id, team_data in df.groupby("team_id"):

        team_data = team_data.sort_values(
            "date"
        ).copy()

        # ----------------------------------------------------
        # Historical period
        # ----------------------------------------------------

        historical = team_data[
            (
                team_data["year"]
                >= HISTORICAL_START
            )
            &
            (
                team_data["year"]
                <= HISTORICAL_END
            )
        ]

        # ----------------------------------------------------
        # Momentum baseline
        # ----------------------------------------------------

        momentum_baseline = team_data[
            (
                team_data["year"]
                >= MOMENTUM_START
            )
            &
            (
                team_data["year"]
                <= MOMENTUM_END
            )
        ]

        # ----------------------------------------------------
        # Recent period
        # ----------------------------------------------------

        recent = team_data[
            team_data["year"]
            >= RECENT_START
        ]

        # ----------------------------------------------------
        # Means
        # ----------------------------------------------------

        historical_mean = historical[
            "trend_score"
        ].mean()

        recent_mean = recent[
            "trend_score"
        ].mean()

        momentum_baseline_mean = (
            momentum_baseline[
                "trend_score"
            ].mean()
        )

        # ----------------------------------------------------
        # Growth
        #
        # Log transformation reduces the influence of large
        # absolute differences in Trends scores.
        # ----------------------------------------------------

        if (
            pd.notna(historical_mean)
            and pd.notna(recent_mean)
        ):
            growth = (
                np.log1p(recent_mean)
                - np.log1p(historical_mean)
            )
        else:
            growth = np.nan

        # ----------------------------------------------------
        # Persistence
        #
        # A three-month rolling average is compared with the
        # historical mean.
        #
        # Persistence = percentage of valid recent rolling
        # windows above the historical baseline.
        # ----------------------------------------------------

        recent_scores = recent[
            ["date", "trend_score"]
        ].copy()

        recent_scores = recent_scores.sort_values(
            "date"
        )

        if len(recent_scores) >= PERSISTENCE_WINDOW:

            recent_scores[
                "rolling_mean"
            ] = (
                recent_scores["trend_score"]
                .rolling(
                    PERSISTENCE_WINDOW
                )
                .mean()
            )

            valid_windows = recent_scores[
                "rolling_mean"
            ].dropna()

            if len(valid_windows) > 0:

                persistence = (
                    (
                        valid_windows
                        > historical_mean
                    ).mean()
                )

            else:
                persistence = np.nan

        else:
            persistence = np.nan

        # ----------------------------------------------------
        # Momentum
        #
        # Recent average relative to the 2023–2024 baseline.
        # ----------------------------------------------------

        if (
            pd.notna(recent_mean)
            and pd.notna(momentum_baseline_mean)
            and momentum_baseline_mean != 0
        ):
            momentum = (
                (
                    recent_mean
                    - momentum_baseline_mean
                )
                / momentum_baseline_mean
            )
        else:
            momentum = np.nan

        # ----------------------------------------------------
        # Store results
        # ----------------------------------------------------

        results.append(
            {
                "team_id": team_id,

                "historical_mean":
                    historical_mean,

                "recent_mean":
                    recent_mean,

                "momentum_baseline_mean":
                    momentum_baseline_mean,

                "growth":
                    growth,

                "persistence":
                    persistence,

                "momentum":
                    momentum,

                "historical_months":
                    len(historical),

                "momentum_months":
                    len(momentum_baseline),

                "recent_months":
                    len(recent),

                "latest_available_month":
                    latest_date,
            }
        )

    return pd.DataFrame(results)


# ============================================================
# PERCENTILE SCORING
# ============================================================

def calculate_percentiles(metrics):
    """
    Convert the three LDES components into percentile scores.

    Percentiles are calculated ONLY across established
    WNBA markets.
    """

    metrics = metrics.copy()

    benchmark_mask = metrics[
        "team_id"
    ].isin(ESTABLISHED_TEAMS)

    for metric in [
        "growth",
        "persistence",
        "momentum",
    ]:

        percentile_column = (
            f"{metric}_percentile"
        )

        metrics[
            percentile_column
        ] = np.nan

        benchmark_values = metrics.loc[
            benchmark_mask,
            metric,
        ]

        metrics.loc[
            benchmark_mask,
            percentile_column,
        ] = (
            benchmark_values
            .rank(
                pct=True,
                method="average",
            )
            * 100
        )

    return metrics


# ============================================================
# CALCULATE LDES
# ============================================================

def calculate_ldes(metrics):
    """
    Calculate the final Local Digital Engagement Score.

    LDES =
        40% Growth
        40% Persistence
        20% Momentum
    """

    metrics = metrics.copy()

    percentile_columns = [
        "growth_percentile",
        "persistence_percentile",
        "momentum_percentile",
    ]

    metrics["ldes"] = np.nan

    benchmark_mask = metrics[
        "team_id"
    ].isin(ESTABLISHED_TEAMS)

    metrics.loc[
        benchmark_mask,
        "ldes",
    ] = (
        metrics.loc[
            benchmark_mask,
            "growth_percentile",
        ]
        * GROWTH_WEIGHT
        +
        metrics.loc[
            benchmark_mask,
            "persistence_percentile",
        ]
        * PERSISTENCE_WEIGHT
        +
        metrics.loc[
            benchmark_mask,
            "momentum_percentile",
        ]
        * MOMENTUM_WEIGHT
    )

    # --------------------------------------------------------
    # Rank established markets
    # --------------------------------------------------------

    metrics["ldes_rank"] = np.nan

    metrics.loc[
        benchmark_mask,
        "ldes_rank",
    ] = (
        metrics.loc[
            benchmark_mask,
            "ldes",
        ]
        .rank(
            ascending=False,
            method="min",
        )
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    metrics = metrics.sort_values(
        [
            "ldes_rank",
            "team_id",
        ],
        na_position="last",
    ).reset_index(drop=True)

    return metrics


# ============================================================
# SENSITIVITY ANALYSIS
# ============================================================

def calculate_sensitivity(df):
    """
    Compare the primary all-month methodology with a
    Jan–October-only methodology.

    This checks whether partial 2026 availability materially
    changes the LDES rankings.
    """

    latest_year = df["year"].max()

    # If the latest year isn't partial, the sensitivity
    # analysis is still valid but won't be particularly
    # informative.
    print(
        f"\nSensitivity analysis uses January–October "
        f"for every year."
    )

    jan_oct = df[
        df["month"] <= 10
    ].copy()

    metrics = calculate_team_metrics(
        jan_oct
    )

    metrics = calculate_percentiles(
        metrics
    )

    metrics = calculate_ldes(
        metrics
    )

    sensitivity = metrics[
        [
            "team_id",
            "ldes",
            "ldes_rank",
        ]
    ].copy()

    sensitivity = sensitivity.rename(
        columns={
            "ldes": "jan_oct_ldes",
            "ldes_rank": "jan_oct_rank",
        }
    )

    return sensitivity


# ============================================================
# COMBINE SENSITIVITY
# ============================================================

def add_sensitivity_results(
    metrics,
    sensitivity,
):
    """Add sensitivity results to the main LDES table."""

    metrics = metrics.merge(
        sensitivity,
        on="team_id",
        how="left",
        validate="one_to_one",
    )

    # --------------------------------------------------------
    # Rank difference
    # --------------------------------------------------------

    metrics["rank_difference"] = (
        metrics["jan_oct_rank"]
        - metrics["ldes_rank"]
    )

    # --------------------------------------------------------
    # Score difference
    # --------------------------------------------------------

    metrics["ldes_difference"] = (
        metrics["jan_oct_ldes"]
        - metrics["ldes"]
    )

    metrics["ldes_sensitivity"] = (
        metrics["ldes_difference"]
        .abs()
    )

    metrics["ldes_sensitivity_rank"] = (
        metrics["ldes_sensitivity"]
        .rank(
            ascending=True,
            method="min",
        )
    )

    return metrics


# ============================================================
# ADD METHODOLOGY METADATA
# ============================================================

def add_methodology_columns(metrics):
    """Add human-readable methodology information."""

    metrics = metrics.copy()

    metrics["historical_period"] = (
        f"{HISTORICAL_START}-{HISTORICAL_END}"
    )

    metrics["recent_period"] = (
        f"{RECENT_START}-latest"
    )

    metrics["momentum_period"] = (
        f"{MOMENTUM_START}-{MOMENTUM_END}"
    )

    metrics["persistence_window_months"] = (
        PERSISTENCE_WINDOW
    )

    metrics["growth_weight"] = (
        GROWTH_WEIGHT
    )

    metrics["persistence_weight"] = (
        PERSISTENCE_WEIGHT
    )

    metrics["momentum_weight"] = (
        MOMENTUM_WEIGHT
    )

    metrics["benchmark_group"] = np.where(
        metrics["team_id"].isin(
            ESTABLISHED_TEAMS
        ),
        "established",
        "newer_franchise",
    )

    return metrics


# ============================================================
# SAVE OUTPUTS
# ============================================================

def save_outputs(
    raw_metrics,
    ldes_metrics,
):
    """Save digital engagement outputs."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    TABLE_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Local metric output
    # --------------------------------------------------------

    raw_metrics.to_csv(
        LOCAL_METRICS_OUTPUT,
        index=False,
    )

    # --------------------------------------------------------
    # Final LDES output
    # --------------------------------------------------------

    ldes_metrics.to_csv(
        LDES_OUTPUT,
        index=False,
    )

    # --------------------------------------------------------
    # Dashboard-friendly summary
    # --------------------------------------------------------

    summary_columns = [
        "team_id",
        "ldes",
        "ldes_rank",
        "growth",
        "growth_percentile",
        "persistence",
        "persistence_percentile",
        "momentum",
        "momentum_percentile",
        "ldes_sensitivity",
        "rank_difference",
        "benchmark_group",
    ]

    summary = ldes_metrics[
        [
            column
            for column in summary_columns
            if column in ldes_metrics.columns
        ]
    ].copy()

    summary.to_csv(
        SUMMARY_OUTPUT,
        index=False,
    )

    print("\nSaved outputs:")
    print(
        f"  {LOCAL_METRICS_OUTPUT}"
    )
    print(
        f"  {LDES_OUTPUT}"
    )
    print(
        f"  {SUMMARY_OUTPUT}"
    )


# ============================================================
# VALIDATION / REPORT
# ============================================================

def print_results(metrics):
    """Print a readable LDES summary."""

    print("\n" + "=" * 60)
    print("LOCAL DIGITAL ENGAGEMENT RESULTS")
    print("=" * 60)

    established = metrics[
        metrics["team_id"].isin(
            ESTABLISHED_TEAMS
        )
    ].copy()

    established = established.sort_values(
        "ldes_rank"
    )

    display_columns = [
        "team_id",
        "ldes",
        "ldes_rank",
        "growth",
        "persistence",
        "momentum",
    ]

    print(
        "\nEstablished-market LDES ranking:\n"
    )

    print(
        established[
            display_columns
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}",
        )
    )

    # --------------------------------------------------------
    # Dallas
    # --------------------------------------------------------

    dallas = established[
        established["team_id"] == "DAL"
    ]

    if not dallas.empty:

        row = dallas.iloc[0]

        print(
            "\nDallas:"
        )

        print(
            f"  LDES: {row['ldes']:.2f}"
        )

        print(
            f"  Rank: "
            f"{int(row['ldes_rank'])} "
            f"of {len(established)}"
        )

        print(
            f"  Growth component: "
            f"{row['growth']:.4f}"
        )

        print(
            f"  Persistence component: "
            f"{row['persistence']:.4f}"
        )

        print(
            f"  Momentum component: "
            f"{row['momentum']:.4f}"
        )

    # --------------------------------------------------------
    # Sensitivity
    # --------------------------------------------------------

    sensitivity = established[
        [
            "team_id",
            "ldes",
            "jan_oct_ldes",
            "ldes_sensitivity",
            "rank_difference",
        ]
    ].copy()

    print(
        "\nJan–October sensitivity:\n"
    )

    print(
        sensitivity.to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}",
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("WNBA DIGITAL ENGAGEMENT ANALYSIS")
    print("=" * 60)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    trends = load_trends()

    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    trends = prepare_data(
        trends
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validate_trends(
        trends
    )

    # --------------------------------------------------------
    # Calculate raw metrics
    # --------------------------------------------------------

    metrics = calculate_team_metrics(
        trends
    )

    # --------------------------------------------------------
    # Percentile normalization
    # --------------------------------------------------------

    metrics = calculate_percentiles(
        metrics
    )

    # --------------------------------------------------------
    # LDES
    # --------------------------------------------------------

    metrics = calculate_ldes(
        metrics
    )

    # --------------------------------------------------------
    # Sensitivity
    # --------------------------------------------------------

    sensitivity = calculate_sensitivity(
        trends
    )

    metrics = add_sensitivity_results(
        metrics,
        sensitivity,
    )

    # --------------------------------------------------------
    # Methodology metadata
    # --------------------------------------------------------

    metrics = add_methodology_columns(
        metrics
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_outputs(
        trends,
        metrics,
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    print_results(
        metrics
    )

    print(
        "\nDigital engagement analysis complete."
    )


if __name__ == "__main__":
    main()