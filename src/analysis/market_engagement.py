"""
WNBA Market Engagement Analysis

Combines physical and digital engagement measures to evaluate
how effectively WNBA markets are building and sustaining fan engagement.

Evaluation 1:
    How is Dallas performing as a market compared with other WNBA markets?

Physical engagement:
    - Average attendance
    - Average capacity utilization
    - Attendance growth
    - Capacity utilization growth

Digital engagement:
    - Local Digital Engagement Score (LDES)

The final combined market engagement score is:
    50% Physical Engagement Score
    50% LDES

Team performance is intentionally kept separate from the engagement score.
It will be analyzed later as an explanatory/contextual factor.
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PHYSICAL_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "tables"
    / "physical_engagement_summary.csv"
)

DIGITAL_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "wnba_local_digital_engagement.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "tables"


# ============================================================
# ESTABLISHED MARKETS
# ============================================================

# These are the markets with sufficient longitudinal history
# for the core engagement comparison.
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
# HELPERS
# ============================================================

def percentile_rank(series):
    """
    Convert a numeric series to a 0-100 percentile rank.

    Higher values = stronger market engagement.
    """
    return series.rank(pct=True, method="average") * 100


def classify_market(physical, digital, physical_median, digital_median):
    """
    Classify a market based on whether its physical and digital
    engagement are above or below the established-market medians.
    """

    physical_high = physical >= physical_median
    digital_high = digital >= digital_median

    if physical_high and digital_high:
        return "High Physical / High Digital"

    if physical_high and not digital_high:
        return "High Physical / Lower Digital"

    if not physical_high and digital_high:
        return "Lower Physical / High Digital"

    return "Lower Physical / Lower Digital"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not PHYSICAL_FILE.exists():
        raise FileNotFoundError(
            f"Physical engagement file not found:\n{PHYSICAL_FILE}"
        )

    if not DIGITAL_FILE.exists():
        raise FileNotFoundError(
            f"Digital engagement file not found:\n{DIGITAL_FILE}"
        )

    physical = pd.read_csv(PHYSICAL_FILE)
    digital = pd.read_csv(DIGITAL_FILE)

    print(f"Loaded physical engagement data: {len(physical)} rows")
    print(f"Loaded digital engagement data: {len(digital)} rows")

    return physical, digital


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(physical, digital):

    # --------------------------------------------------------
    # Physical engagement
    # --------------------------------------------------------

    physical_required = [
        "team_id",
        "team_name",
        "physical_engagement_score",
        "physical_engagement_rank",
        "avg_attendance",
        "avg_capacity_utilization",
        "attendance_growth",
        "capacity_utilization_growth",
    ]

    missing_physical = [
        col for col in physical_required
        if col not in physical.columns
    ]

    if missing_physical:
        raise ValueError(
            "Physical engagement file is missing required columns: "
            f"{missing_physical}"
        )

    physical = physical[
        physical["team_id"].isin(ESTABLISHED_TEAMS)
    ].copy()

    # --------------------------------------------------------
    # Digital engagement
    # --------------------------------------------------------

    digital_required = [
        "team_id",
        "ldes",
        "ldes_rank",
    ]

    missing_digital = [
        col for col in digital_required
        if col not in digital.columns
    ]

    if missing_digital:
        raise ValueError(
            "Digital engagement file is missing required columns: "
            f"{missing_digital}"
        )

    digital = digital[
        digital["team_id"].isin(ESTABLISHED_TEAMS)
    ].copy()

    # Keep only the digital columns needed for this analysis.
    digital_columns = [
        "team_id",
        "ldes",
        "ldes_rank",
        "growth",
        "growth_percentile",
        "persistence",
        "persistence_percentile",
        "momentum",
        "momentum_percentile",
        "benchmark_group",
    ]

    digital_columns = [
        col for col in digital_columns
        if col in digital.columns
    ]

    digital = digital[digital_columns].copy()

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    merged = physical.merge(
        digital,
        on="team_id",
        how="inner",
        suffixes=("_physical", "_digital"),
    )

    # Use the physical team name as the canonical display name.
    if "team_name_physical" in merged.columns:
        merged["team_name"] = merged["team_name_physical"]

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    numeric_columns = [
        "physical_engagement_score",
        "avg_attendance",
        "avg_capacity_utilization",
        "attendance_growth",
        "capacity_utilization_growth",
        "ldes",
        "growth",
        "persistence",
        "momentum",
    ]

    for column in numeric_columns:
        if column in merged.columns:
            merged[column] = pd.to_numeric(
                merged[column],
                errors="coerce",
            )

    return merged


# ============================================================
# CALCULATE MARKET ENGAGEMENT
# ============================================================

def calculate_market_engagement(df):

    df = df.copy()

    # --------------------------------------------------------
    # Combined score
    # --------------------------------------------------------

    df["physical_weighted"] = (
        df["physical_engagement_score"] * 0.50
    )

    df["digital_weighted"] = (
        df["ldes"] * 0.50
    )

    df["market_engagement_score"] = (
        df["physical_weighted"]
        + df["digital_weighted"]
    )

    # --------------------------------------------------------
    # Percentile ranks
    # --------------------------------------------------------

    df["physical_percentile"] = percentile_rank(
        df["physical_engagement_score"]
    )

    df["digital_percentile"] = percentile_rank(
        df["ldes"]
    )

    df["market_engagement_percentile"] = percentile_rank(
        df["market_engagement_score"]
    )

    # --------------------------------------------------------
    # Rank
    # --------------------------------------------------------

    df["market_engagement_rank"] = (
        df["market_engagement_score"]
        .rank(
            ascending=False,
            method="min",
        )
    )

    # --------------------------------------------------------
    # Market quadrant
    # --------------------------------------------------------

    physical_median = df["physical_engagement_score"].median()
    digital_median = df["ldes"].median()

    df["market_quadrant"] = df.apply(
        lambda row: classify_market(
            row["physical_engagement_score"],
            row["ldes"],
            physical_median,
            digital_median,
        ),
        axis=1,
    )

    # --------------------------------------------------------
    # Distance between physical and digital performance
    # --------------------------------------------------------

    df["digital_minus_physical"] = (
        df["ldes"]
        - df["physical_engagement_score"]
    )

    return df


# ============================================================
# DALLAS ANALYSIS
# ============================================================

def create_dallas_summary(df):

    dallas = df[df["team_id"] == "DAL"].copy()

    if dallas.empty:
        raise ValueError(
            "Dallas Wings (DAL) not found in the merged dataset."
        )

    dallas = dallas.iloc[0]

    established_mean = {
        "physical_engagement_score":
            df["physical_engagement_score"].mean(),

        "ldes":
            df["ldes"].mean(),

        "market_engagement_score":
            df["market_engagement_score"].mean(),

        "avg_attendance":
            df["avg_attendance"].mean(),

        "avg_capacity_utilization":
            df["avg_capacity_utilization"].mean(),

        "attendance_growth":
            df["attendance_growth"].mean(),

        "capacity_utilization_growth":
            df["capacity_utilization_growth"].mean(),
    }

    rows = []

    metrics = [
        (
            "Physical Engagement Score",
            dallas["physical_engagement_score"],
            established_mean["physical_engagement_score"],
        ),
        (
            "Local Digital Engagement Score",
            dallas["ldes"],
            established_mean["ldes"],
        ),
        (
            "Combined Market Engagement Score",
            dallas["market_engagement_score"],
            established_mean["market_engagement_score"],
        ),
        (
            "Average Attendance",
            dallas["avg_attendance"],
            established_mean["avg_attendance"],
        ),
        (
            "Capacity Utilization",
            dallas["avg_capacity_utilization"],
            established_mean["avg_capacity_utilization"],
        ),
        (
            "Attendance Growth",
            dallas["attendance_growth"],
            established_mean["attendance_growth"],
        ),
        (
            "Capacity Utilization Growth",
            dallas["capacity_utilization_growth"],
            established_mean["capacity_utilization_growth"],
        ),
    ]

    for metric, dallas_value, market_average in metrics:

        if pd.notna(market_average) and market_average != 0:
            difference_pct = (
                (dallas_value - market_average)
                / abs(market_average)
            ) * 100
        else:
            difference_pct = np.nan

        rows.append(
            {
                "metric": metric,
                "dallas_value": dallas_value,
                "established_market_average": market_average,
                "difference_from_average": (
                    dallas_value - market_average
                ),
                "difference_percent": difference_pct,
            }
        )

    summary = pd.DataFrame(rows)

    return summary


# ============================================================
# CREATE DISPLAY TABLE
# ============================================================

def create_market_summary(df):

    columns = [
        "team_id",
        "team_name",
        "market_engagement_rank",
        "market_engagement_score",
        "physical_engagement_score",
        "ldes",
        "physical_percentile",
        "digital_percentile",
        "market_engagement_percentile",
        "market_quadrant",
        "digital_minus_physical",
        "avg_attendance",
        "avg_capacity_utilization",
        "attendance_growth",
        "capacity_utilization_growth",
    ]

    columns = [
        col for col in columns
        if col in df.columns
    ]

    summary = df[columns].copy()

    summary = summary.sort_values(
        "market_engagement_rank"
    )

    return summary


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("WNBA MARKET ENGAGEMENT ANALYSIS")
    print("=" * 60)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    physical, digital = load_data()

    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    merged = prepare_data(
        physical,
        digital,
    )

    print(
        f"Established markets available for combined analysis: "
        f"{len(merged)}"
    )

    # --------------------------------------------------------
    # Calculate
    # --------------------------------------------------------

    engagement = calculate_market_engagement(
        merged
    )

    # --------------------------------------------------------
    # Tables
    # --------------------------------------------------------

    market_summary = create_market_summary(
        engagement
    )

    dallas_summary = create_dallas_summary(
        engagement
    )

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Save market summary
    # --------------------------------------------------------

    market_summary_file = (
        OUTPUT_DIR
        / "market_engagement_summary.csv"
    )

    market_summary.to_csv(
        market_summary_file,
        index=False,
    )

    # --------------------------------------------------------
    # Save Dallas comparison
    # --------------------------------------------------------

    dallas_file = (
        OUTPUT_DIR
        / "dallas_market_engagement.csv"
    )

    dallas_summary.to_csv(
        dallas_file,
        index=False,
    )

    # --------------------------------------------------------
    # Save full analysis
    # --------------------------------------------------------

    full_file = (
        OUTPUT_DIR
        / "market_engagement_full.csv"
    )

    engagement.to_csv(
        full_file,
        index=False,
    )

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print()
    print("MARKET ENGAGEMENT RANKING")
    print("-" * 60)

    display_columns = [
        "market_engagement_rank",
        "team_id",
        "market_engagement_score",
        "physical_engagement_score",
        "ldes",
        "market_quadrant",
    ]

    print(
        market_summary[
            display_columns
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.2f}",
        )
    )

    # --------------------------------------------------------
    # Dallas
    # --------------------------------------------------------

    dallas = engagement[
        engagement["team_id"] == "DAL"
    ].iloc[0]

    print()
    print("DALLAS WINGS")
    print("-" * 60)

    print(
        f"Market engagement rank: "
        f"{int(dallas['market_engagement_rank'])} "
        f"of {len(engagement)}"
    )

    print(
        f"Combined market engagement score: "
        f"{dallas['market_engagement_score']:.2f}"
    )

    print(
        f"Physical engagement score: "
        f"{dallas['physical_engagement_score']:.2f}"
    )

    print(
        f"Local Digital Engagement Score: "
        f"{dallas['ldes']:.2f}"
    )

    print(
        f"Market quadrant: "
        f"{dallas['market_quadrant']}"
    )

    print(
        f"Digital minus physical score: "
        f"{dallas['digital_minus_physical']:.2f}"
    )

    print()
    print("Files created:")
    print(f"  {market_summary_file}")
    print(f"  {dallas_file}")
    print(f"  {full_file}")

    print()
    print("=" * 60)
    print("MARKET ENGAGEMENT ANALYSIS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()