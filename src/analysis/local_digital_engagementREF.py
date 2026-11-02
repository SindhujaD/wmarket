"""
Calculate Local Digital Engagement Score (LDES) for WNBA teams.

Input:
    data/raw/trends/wnba_trends_local_monthly.csv

Output:
    data/processed/wnba_local_digital_engagement.csv

LDES methodology:

    Growth       = 40%
    Persistence  = 40%
    Momentum     = 20%

Periods:
    Historical baseline: 2021-2024
    Recent period:       2025 through latest available month
    Momentum baseline:   2023-2024

Important:
    Google Trends scores are interpreted within each team's local DMA.
    Raw 0-100 values are therefore NOT compared directly across teams.

    Instead, we calculate each team's change over time and then
    percentile-rank those changes across teams.

Established markets are used for the core benchmark:
    ATL, CHI, CON, DAL, IND, LVA, LAS, MIN, NYL, PHX, SEA, WAS

GSV and POR are retained in the raw data but excluded from the
core longitudinal LDES benchmark because they do not have a full
historical franchise record.

A sensitivity analysis also compares:
    - all available months
    - January-October only

This helps determine whether the incomplete 2026 calendar year
materially affects the results.
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "trends"
    / "wnba_trends_local_monthly.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "wnba_local_digital_engagement.csv"
)


# ============================================================
# CONFIGURATION
# ============================================================

# Established WNBA markets with enough history for the
# longitudinal benchmark.
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

# Period definitions
HISTORICAL_START = 2021
HISTORICAL_END = 2024

MOMENTUM_START = 2023
MOMENTUM_END = 2024

RECENT_START = 2025

# LDES weights
GROWTH_WEIGHT = 0.40
PERSISTENCE_WEIGHT = 0.40
MOMENTUM_WEIGHT = 0.20

# Number of months used in the rolling persistence calculation
ROLLING_WINDOW = 3


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def percentile_rank(series):
    """
    Convert a series into percentile ranks from 0-100.

    Higher values receive higher percentile scores.

    If every value is identical, all observations receive 50.
    """
    if series.nunique(dropna=True) <= 1:
        return pd.Series(
            50.0,
            index=series.index,
        )

    return series.rank(
        method="average",
        pct=True,
    ) * 100


def safe_mean(series):
    """
    Calculate a mean while ignoring missing values.
    """
    values = pd.to_numeric(series, errors="coerce")

    if values.dropna().empty:
        return np.nan

    return values.mean()


def calculate_growth(historical_mean, recent_mean):
    """
    Log growth:

        log(recent + 1) - log(historical + 1)

    The +1 prevents log(0).
    """
    if pd.isna(historical_mean) or pd.isna(recent_mean):
        return np.nan

    return (
        np.log(recent_mean + 1)
        - np.log(historical_mean + 1)
    )


def calculate_momentum(baseline_mean, recent_mean):
    """
    Relative momentum:

        (recent - baseline) / baseline

    If baseline is zero, return NaN rather than divide by zero.
    """
    if pd.isna(baseline_mean) or pd.isna(recent_mean):
        return np.nan

    if baseline_mean == 0:
        return np.nan

    return (
        (recent_mean - baseline_mean)
        / baseline_mean
    )


def calculate_persistence(team_df, historical_mean):
    """
    Calculate the proportion of recent 3-month rolling windows
    whose average exceeds the team's historical mean.

    Example:

        Historical mean = 10

        Recent rolling averages:
        8, 11, 13, 14, 9

        3 of 5 windows exceed 10

        Persistence = 3 / 5 = 0.60
    """

    if pd.isna(historical_mean):
        return np.nan

    recent = (
        team_df[
            team_df["year"] >= RECENT_START
        ]
        .sort_values("date")
        .copy()
    )

    if len(recent) < ROLLING_WINDOW:
        return np.nan

    rolling_average = (
        recent["trends_interest"]
        .rolling(
            window=ROLLING_WINDOW,
            min_periods=ROLLING_WINDOW,
        )
        .mean()
    )

    valid_windows = rolling_average.dropna()

    if valid_windows.empty:
        return np.nan

    return (
        (valid_windows > historical_mean)
        .mean()
    )


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("LOCAL DIGITAL ENGAGEMENT SCORE (LDES)")
print("=" * 70)

print("\nLoading data:")
print(INPUT_FILE)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found:\n{INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)


# ============================================================
# BASIC VALIDATION
# ============================================================

required_columns = [
    "date",
    "year",
    "month",
    "team_id",
    "team_name",
    "dma_name",
    "geo_code",
    "trends_interest",
]

missing_columns = [
    col
    for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        "Missing required columns:\n"
        + "\n".join(missing_columns)
    )


df["date"] = pd.to_datetime(df["date"])

df["year"] = pd.to_numeric(
    df["year"],
    errors="coerce",
)

df["month"] = pd.to_numeric(
    df["month"],
    errors="coerce",
)

df["trends_interest"] = pd.to_numeric(
    df["trends_interest"],
    errors="coerce",
)


# ============================================================
# DATA VALIDATION REPORT
# ============================================================

print("\n" + "=" * 70)
print("INPUT VALIDATION")
print("=" * 70)

print(f"\nRows: {len(df):,}")

print(
    f"Date range: "
    f"{df['date'].min().date()} "
    f"to "
    f"{df['date'].max().date()}"
)

print(
    f"Teams: {df['team_id'].nunique()}"
)

print(
    f"Unique months: {df['date'].nunique()}"
)

print("\nRows by team:")
print(
    df.groupby("team_id")
    .size()
    .sort_index()
)


# ============================================================
# CHECK EXPECTED MONTHLY COVERAGE
# ============================================================

print("\nChecking monthly coverage...")

coverage = (
    df.groupby("team_id")["date"]
    .nunique()
    .sort_index()
)

print(coverage)

incomplete = coverage[coverage < 70]

if not incomplete.empty:
    print(
        "\nWARNING: Some teams have fewer than 70 months:"
    )
    print(incomplete)
else:
    print(
        "\nAll teams have the expected 70 months."
    )


# ============================================================
# FILTER ESTABLISHED MARKETS
# ============================================================

analysis_df = df[
    df["team_id"].isin(ESTABLISHED_TEAMS)
].copy()

analysis_df = analysis_df.sort_values(
    ["team_id", "date"]
)


print("\n" + "=" * 70)
print("CORE LDES BENCHMARK")
print("=" * 70)

print(
    f"\nEstablished teams included: "
    f"{len(ESTABLISHED_TEAMS)}"
)

print(
    ESTABLISHED_TEAMS
)

excluded_teams = sorted(
    set(df["team_id"].unique())
    - set(ESTABLISHED_TEAMS)
)

print(
    "\nExcluded from core longitudinal benchmark:"
)

print(
    excluded_teams
)


# ============================================================
# CALCULATE TEAM-LEVEL COMPONENTS
# ============================================================

results = []


for team_id, team_df in analysis_df.groupby(
    "team_id",
    sort=True,
):

    team_df = team_df.sort_values("date").copy()

    team_name = team_df["team_name"].iloc[0]
    dma_name = team_df["dma_name"].iloc[0]
    geo_code = team_df["geo_code"].iloc[0]

    # --------------------------------------------------------
    # HISTORICAL PERIOD
    # --------------------------------------------------------

    historical = team_df[
        team_df["year"].between(
            HISTORICAL_START,
            HISTORICAL_END,
        )
    ]

    historical_mean = safe_mean(
        historical["trends_interest"]
    )

    # --------------------------------------------------------
    # MOMENTUM BASELINE
    # --------------------------------------------------------

    momentum_baseline = team_df[
        team_df["year"].between(
            MOMENTUM_START,
            MOMENTUM_END,
        )
    ]

    momentum_baseline_mean = safe_mean(
        momentum_baseline["trends_interest"]
    )

    # --------------------------------------------------------
    # RECENT PERIOD
    # --------------------------------------------------------

    recent = team_df[
        team_df["year"] >= RECENT_START
    ]

    recent_mean = safe_mean(
        recent["trends_interest"]
    )

    # --------------------------------------------------------
    # GROWTH
    # --------------------------------------------------------

    growth = calculate_growth(
        historical_mean,
        recent_mean,
    )

    # --------------------------------------------------------
    # PERSISTENCE
    # --------------------------------------------------------

    persistence = calculate_persistence(
        team_df,
        historical_mean,
    )

    # --------------------------------------------------------
    # MOMENTUM
    # --------------------------------------------------------

    momentum = calculate_momentum(
        momentum_baseline_mean,
        recent_mean,
    )

    # --------------------------------------------------------
    # PERIOD COUNTS
    # --------------------------------------------------------

    historical_months = len(historical)

    momentum_months = len(
        momentum_baseline
    )

    recent_months = len(recent)

    results.append(
        {
            "team_id": team_id,
            "team_name": team_name,
            "dma_name": dma_name,
            "geo_code": geo_code,

            "historical_mean": historical_mean,
            "recent_mean": recent_mean,
            "momentum_baseline_mean": momentum_baseline_mean,

            "growth": growth,
            "persistence": persistence,
            "momentum": momentum,

            "historical_months": historical_months,
            "momentum_months": momentum_months,
            "recent_months": recent_months,
        }
    )


results_df = pd.DataFrame(results)


# ============================================================
# COMPONENT PERCENTILE RANKS
# ============================================================

results_df[
    "growth_percentile"
] = percentile_rank(
    results_df["growth"]
)

results_df[
    "persistence_percentile"
] = percentile_rank(
    results_df["persistence"]
)

results_df[
    "momentum_percentile"
] = percentile_rank(
    results_df["momentum"]
)


# ============================================================
# FINAL LDES
# ============================================================

results_df["ldes"] = (
    GROWTH_WEIGHT
    * results_df["growth_percentile"]
    +
    PERSISTENCE_WEIGHT
    * results_df["persistence_percentile"]
    +
    MOMENTUM_WEIGHT
    * results_df["momentum_percentile"]
)


# ============================================================
# LDES RANK
# ============================================================

results_df["ldes_rank"] = (
    results_df["ldes"]
    .rank(
        ascending=False,
        method="min",
    )
    .astype(int)
)


# ============================================================
# SORT RESULTS
# ============================================================

results_df = results_df.sort_values(
    "ldes_rank"
).reset_index(drop=True)


# ============================================================
# SENSITIVITY ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("SENSITIVITY ANALYSIS")
print("=" * 70)

print(
    "\nTesting whether using all available months "
    "materially changes results compared with "
    "January-October-only comparisons."
)


def calculate_sensitivity_ldes(
    full_df,
    recent_end_month=10,
):
    """
    Recalculate the LDES using the same calendar months
    across all periods.

    Historical:
        Jan-recent_end_month, 2021-2024

    Momentum:
        Jan-recent_end_month, 2023-2024

    Recent:
        Jan-recent_end_month, 2025-2026
    """

    sensitivity_results = []

    for team_id, team_df in full_df.groupby(
        "team_id",
        sort=True,
    ):

        team_df = team_df.sort_values("date").copy()

        team_name = team_df["team_name"].iloc[0]

        historical = team_df[
            (
                team_df["year"].between(
                    HISTORICAL_START,
                    HISTORICAL_END,
                )
            )
            &
            (
                team_df["month"]
                <= recent_end_month
            )
        ]

        momentum_baseline = team_df[
            (
                team_df["year"].between(
                    MOMENTUM_START,
                    MOMENTUM_END,
                )
            )
            &
            (
                team_df["month"]
                <= recent_end_month
            )
        ]

        recent = team_df[
            (
                team_df["year"] >= RECENT_START
            )
            &
            (
                team_df["month"]
                <= recent_end_month
            )
        ]

        historical_mean = safe_mean(
            historical["trends_interest"]
        )

        momentum_baseline_mean = safe_mean(
            momentum_baseline["trends_interest"]
        )

        recent_mean = safe_mean(
            recent["trends_interest"]
        )

        growth = calculate_growth(
            historical_mean,
            recent_mean,
        )

        # For sensitivity persistence, calculate rolling
        # averages using only Jan-Oct observations.
        recent_for_persistence = recent.sort_values(
            "date"
        ).copy()

        rolling_average = (
            recent_for_persistence[
                "trends_interest"
            ]
            .rolling(
                window=ROLLING_WINDOW,
                min_periods=ROLLING_WINDOW,
            )
            .mean()
        )

        valid_windows = rolling_average.dropna()

        if valid_windows.empty:
            persistence = np.nan
        else:
            persistence = (
                valid_windows > historical_mean
            ).mean()

        momentum = calculate_momentum(
            momentum_baseline_mean,
            recent_mean,
        )

        sensitivity_results.append(
            {
                "team_id": team_id,
                "team_name": team_name,
                "growth_sensitivity": growth,
                "persistence_sensitivity": persistence,
                "momentum_sensitivity": momentum,
            }
        )

    sensitivity_df = pd.DataFrame(
        sensitivity_results
    )

    sensitivity_df[
        "growth_percentile_sensitivity"
    ] = percentile_rank(
        sensitivity_df["growth_sensitivity"]
    )

    sensitivity_df[
        "persistence_percentile_sensitivity"
    ] = percentile_rank(
        sensitivity_df["persistence_sensitivity"]
    )

    sensitivity_df[
        "momentum_percentile_sensitivity"
    ] = percentile_rank(
        sensitivity_df["momentum_sensitivity"]
    )

    sensitivity_df[
        "ldes_sensitivity"
    ] = (
        GROWTH_WEIGHT
        * sensitivity_df[
            "growth_percentile_sensitivity"
        ]
        +
        PERSISTENCE_WEIGHT
        * sensitivity_df[
            "persistence_percentile_sensitivity"
        ]
        +
        MOMENTUM_WEIGHT
        * sensitivity_df[
            "momentum_percentile_sensitivity"
        ]
    )

    sensitivity_df[
        "ldes_sensitivity_rank"
    ] = (
        sensitivity_df[
            "ldes_sensitivity"
        ]
        .rank(
            ascending=False,
            method="min",
        )
        .astype(int)
    )

    return sensitivity_df


sensitivity_df = calculate_sensitivity_ldes(
    analysis_df,
    recent_end_month=10,
)


# ============================================================
# MERGE SENSITIVITY RESULTS
# ============================================================

results_df = results_df.merge(
    sensitivity_df[
        [
            "team_id",
            "ldes_sensitivity",
            "ldes_sensitivity_rank",
        ]
    ],
    on="team_id",
    how="left",
)


# ============================================================
# RANK STABILITY
# ============================================================

results_df[
    "rank_difference"
] = (
    results_df["ldes_rank"]
    -
    results_df["ldes_sensitivity_rank"]
).abs()


results_df[
    "ldes_difference"
] = (
    results_df["ldes"]
    -
    results_df["ldes_sensitivity"]
).abs()


average_rank_difference = (
    results_df["rank_difference"].mean()
)

max_rank_difference = (
    results_df["rank_difference"].max()
)

average_ldes_difference = (
    results_df["ldes_difference"].mean()
)

max_ldes_difference = (
    results_df["ldes_difference"].max()
)


# ============================================================
# OUTPUT DISPLAY
# ============================================================

print("\n" + "=" * 70)
print("LDES RESULTS")
print("=" * 70)

display_columns = [
    "ldes_rank",
    "team_id",
    "team_name",
    "historical_mean",
    "recent_mean",
    "growth",
    "growth_percentile",
    "persistence",
    "persistence_percentile",
    "momentum",
    "momentum_percentile",
    "ldes",
]

print(
    results_df[
        display_columns
    ].to_string(
        index=False,
        float_format=lambda x: f"{x:.3f}",
    )
)


# ============================================================
# SENSITIVITY RESULTS
# ============================================================

print("\n" + "=" * 70)
print("SENSITIVITY RESULTS")
print("=" * 70)

print(
    "\nAll-month LDES vs January-October-only LDES:"
)

sensitivity_display = results_df[
    [
        "ldes_rank",
        "team_id",
        "ldes",
        "ldes_sensitivity_rank",
        "ldes_sensitivity",
        "rank_difference",
        "ldes_difference",
    ]
].sort_values("ldes_rank")

print(
    sensitivity_display.to_string(
        index=False,
        float_format=lambda x: f"{x:.3f}",
    )
)

print(
    "\nAverage rank difference: "
    f"{average_rank_difference:.2f}"
)

print(
    "Maximum rank difference: "
    f"{max_rank_difference:.0f}"
)

print(
    "Average LDES difference: "
    f"{average_ldes_difference:.2f} points"
)

print(
    "Maximum LDES difference: "
    f"{max_ldes_difference:.2f} points"
)


# ============================================================
# INTERPRET SENSITIVITY
# ============================================================

if (
    average_rank_difference <= 1.0
    and max_rank_difference <= 2
):
    sensitivity_conclusion = (
        "LOW SENSITIVITY: The LDES rankings are highly "
        "stable when restricting all periods to January-October."
    )

elif (
    average_rank_difference <= 2.0
    and max_rank_difference <= 3
):
    sensitivity_conclusion = (
        "MODERATE SENSITIVITY: The LDES rankings are "
        "generally stable, although some teams move modestly."
    )

else:
    sensitivity_conclusion = (
        "HIGHER SENSITIVITY: The incomplete 2026 calendar "
        "year has a meaningful effect on some rankings. "
        "This should be discussed prominently as a caveat."
    )


print(
    "\nSensitivity conclusion:"
)

print(
    sensitivity_conclusion
)


# ============================================================
# ADD METHODOLOGY METADATA
# ============================================================

results_df[
    "historical_period"
] = "2021-2024"

results_df[
    "recent_period"
] = "2025-2026 through latest available month"

results_df[
    "momentum_period"
] = "2023-2024"

results_df[
    "ldes_methodology"
] = (
    "40% growth + 40% persistence + 20% momentum; "
    "component measures percentile-ranked across established markets"
)

results_df[
    "trend_scale_note"
] = (
    "Google Trends 0-100 values are interpreted within each "
    "team's local DMA; raw levels are not directly compared across DMAs"
)

results_df[
    "sensitivity_note"
] = sensitivity_conclusion


# ============================================================
# FINAL COLUMN ORDER
# ============================================================

final_columns = [
    # Identification
    "team_id",
    "team_name",
    "dma_name",
    "geo_code",

    # Raw component inputs
    "historical_mean",
    "recent_mean",
    "momentum_baseline_mean",

    # Component metrics
    "growth",
    "persistence",
    "momentum",

    # Component percentiles
    "growth_percentile",
    "persistence_percentile",
    "momentum_percentile",

    # Final score
    "ldes",
    "ldes_rank",

    # Sensitivity
    "ldes_sensitivity",
    "ldes_sensitivity_rank",
    "rank_difference",
    "ldes_difference",

    # Observation counts
    "historical_months",
    "momentum_months",
    "recent_months",

    # Methodology metadata
    "historical_period",
    "recent_period",
    "momentum_period",
    "ldes_methodology",
    "trend_scale_note",
    "sensitivity_note",
]


results_df = results_df[
    final_columns
]


# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

results_df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# FINAL VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("FINAL VALIDATION")
print("=" * 70)

print(
    f"\nOutput file:\n{OUTPUT_FILE}"
)

print(
    f"\nRows saved: {len(results_df)}"
)

print(
    f"Teams saved: "
    f"{results_df['team_id'].nunique()}"
)

print(
    "\nLDES range:"
)

print(
    f"Minimum: {results_df['ldes'].min():.2f}"
)

print(
    f"Maximum: {results_df['ldes'].max():.2f}"
)

print(
    "\nRanked teams:"
)

print(
    results_df[
        [
            "ldes_rank",
            "team_id",
            "team_name",
            "ldes",
        ]
    ].to_string(
        index=False,
        float_format=lambda x: f"{x:.2f}",
    )
)

print(
    "\n" + "=" * 70
)

print(
    "LDES CALCULATION COMPLETE"
)

print(
    "=" * 70
)