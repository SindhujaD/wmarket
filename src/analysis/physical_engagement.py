"""
Physical Engagement Analysis

Analyzes WNBA physical fan engagement using:
- Average attendance
- Average capacity utilization
- Attendance growth
- Capacity utilization growth
- Win percentage
- Playoff participation

Outputs:
    outputs/tables/physical_engagement_summary.csv
    outputs/tables/physical_engagement_season.csv
    outputs/tables/physical_engagement_performance.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ATTENDANCE_PATH = (
    PROJECT_ROOT / "data" / "processed" / "wnba_attendance.csv"
)

TEAM_SEASON_PATH = (
    PROJECT_ROOT / "data" / "processed" / "wnba_team_season.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "tables"

SUMMARY_OUTPUT = OUTPUT_DIR / "physical_engagement_summary.csv"
SEASON_OUTPUT = OUTPUT_DIR / "physical_engagement_season.csv"
PERFORMANCE_OUTPUT = OUTPUT_DIR / "physical_engagement_performance.csv"


# ============================================================
# ANALYSIS PERIODS
# ============================================================

# We exclude 2021–2022 from the growth calculation because
# these seasons were unusually affected by the pandemic and
# attendance restrictions.
BASELINE_SEASONS = [2023, 2024]
RECENT_SEASONS = [2025, 2026]


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    """Load processed attendance and team-season datasets."""

    attendance = pd.read_csv(ATTENDANCE_PATH)
    team_season = pd.read_csv(TEAM_SEASON_PATH)

    return attendance, team_season


# ============================================================
# PREPARE DATA
# ============================================================

def prepare_data(attendance, team_season):
    """
    Clean and combine attendance with team performance.

    Returns:
        DataFrame containing one row per team-season.
    """

    attendance = attendance.copy()
    team_season = team_season.copy()

    # --------------------------------------------------------
    # Standardize column names
    # --------------------------------------------------------

    attendance.columns = attendance.columns.str.strip()
    team_season.columns = team_season.columns.str.strip()

    # --------------------------------------------------------
    # Convert numeric fields
    # --------------------------------------------------------

    numeric_attendance = [
        "season",
        "average_attendance",
        "average_capacity",
        "capacity_utilization",
    ]

    for column in numeric_attendance:
        if column in attendance.columns:
            attendance[column] = pd.to_numeric(
                attendance[column],
                errors="coerce",
            )

    numeric_performance = [
        "season",
        "win_pct",
        "playoff_appearance",
    ]

    for column in numeric_performance:
        if column in team_season.columns:
            team_season[column] = pd.to_numeric(
                team_season[column],
                errors="coerce",
            )

    # --------------------------------------------------------
    # Normalize team IDs
    # --------------------------------------------------------

    attendance["team_id"] = (
        attendance["team_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    team_season["team_id"] = (
        team_season["team_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------------
    # Normalize seasons
    # --------------------------------------------------------

    attendance["season"] = attendance["season"].astype("Int64")
    team_season["season"] = team_season["season"].astype("Int64")

    # --------------------------------------------------------
    # Check for duplicate team-season rows
    # --------------------------------------------------------

    attendance_duplicates = attendance.duplicated(
        subset=["team_id", "season"]
    )

    if attendance_duplicates.any():
        duplicate_rows = attendance.loc[
            attendance_duplicates,
            ["team_id", "season"],
        ]

        raise ValueError(
            "Duplicate attendance team-season rows found:\n"
            f"{duplicate_rows}"
        )

    team_duplicates = team_season.duplicated(
        subset=["team_id", "season"]
    )

    if team_duplicates.any():
        duplicate_rows = team_season.loc[
            team_duplicates,
            ["team_id", "season"],
        ]

        raise ValueError(
            "Duplicate team-season performance rows found:\n"
            f"{duplicate_rows}"
        )

    # --------------------------------------------------------
    # Select relevant performance columns
    # --------------------------------------------------------

    performance_columns = [
        "team_id",
        "season",
        "win_pct",
        "playoff_appearance",
    ]

    missing_performance = [
        column
        for column in performance_columns
        if column not in team_season.columns
    ]

    if missing_performance:
        raise ValueError(
            "Missing required performance columns: "
            f"{missing_performance}"
        )

    performance = team_season[performance_columns].copy()

    # --------------------------------------------------------
    # Merge attendance and performance
    # --------------------------------------------------------

    data = attendance.merge(
        performance,
        on=["team_id", "season"],
        how="left",
        validate="one_to_one",
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    data = data.sort_values(
        ["team_id", "season"]
    ).reset_index(drop=True)

    return data


# ============================================================
# SEASON-LEVEL PHYSICAL ENGAGEMENT
# ============================================================

def calculate_season_metrics(data):
    """
    Create season-level physical engagement metrics.

    Returns:
        One row per team-season.
    """

    season = data.copy()

    # Attendance relative to previous season
    season["attendance_yoy_growth"] = (
        season.groupby("team_id")["average_attendance"]
        .pct_change()
    )

    # Capacity utilization relative to previous season
    season["utilization_yoy_growth"] = (
        season.groupby("team_id")["capacity_utilization"]
        .pct_change()
    )

    return season


# ============================================================
# PERIOD SUMMARY
# ============================================================

def calculate_period_summary(data):
    """
    Calculate baseline and recent physical engagement.

    Baseline:
        2023–2024

    Recent:
        2025–2026

    Growth is calculated from the average of each period.
    """

    rows = []

    for team_id, team_data in data.groupby("team_id"):

        team_data = team_data.copy()

        baseline = team_data[
            team_data["season"].isin(BASELINE_SEASONS)
        ]

        recent = team_data[
            team_data["season"].isin(RECENT_SEASONS)
        ]

        # ----------------------------------------------------
        # Basic averages across all available seasons
        # ----------------------------------------------------

        avg_attendance = team_data[
            "average_attendance"
        ].mean()

        avg_utilization = team_data[
            "capacity_utilization"
        ].mean()

        avg_win_pct = team_data[
            "win_pct"
        ].mean()

        playoff_rate = team_data[
            "playoff_appearance"
        ].mean()

        # ----------------------------------------------------
        # Baseline period
        # ----------------------------------------------------

        baseline_attendance = baseline[
            "average_attendance"
        ].mean()

        baseline_utilization = baseline[
            "capacity_utilization"
        ].mean()

        # ----------------------------------------------------
        # Recent period
        # ----------------------------------------------------

        recent_attendance = recent[
            "average_attendance"
        ].mean()

        recent_utilization = recent[
            "capacity_utilization"
        ].mean()

        # ----------------------------------------------------
        # Growth calculations
        # ----------------------------------------------------

        if (
            pd.notna(baseline_attendance)
            and baseline_attendance != 0
            and pd.notna(recent_attendance)
        ):
            attendance_growth = (
                recent_attendance / baseline_attendance
            ) - 1
        else:
            attendance_growth = np.nan

        if (
            pd.notna(baseline_utilization)
            and baseline_utilization != 0
            and pd.notna(recent_utilization)
        ):
            utilization_growth = (
                recent_utilization / baseline_utilization
            ) - 1
        else:
            utilization_growth = np.nan

        # ----------------------------------------------------
        # Number of seasons
        # ----------------------------------------------------

        seasons_available = team_data["season"].nunique()

        baseline_seasons_available = baseline[
            "season"
        ].nunique()

        recent_seasons_available = recent[
            "season"
        ].nunique()

        # ----------------------------------------------------
        # Team name
        # ----------------------------------------------------

        if "team_name" in team_data.columns:
            team_name = team_data["team_name"].iloc[0]
        else:
            team_name = team_id

        rows.append(
            {
                "team_id": team_id,
                "team_name": team_name,

                "seasons_available": seasons_available,

                "avg_attendance": avg_attendance,
                "avg_capacity_utilization": avg_utilization,

                "baseline_attendance": baseline_attendance,
                "recent_attendance": recent_attendance,
                "attendance_growth": attendance_growth,

                "baseline_capacity_utilization":
                    baseline_utilization,
                "recent_capacity_utilization":
                    recent_utilization,
                "capacity_utilization_growth":
                    utilization_growth,

                "avg_win_pct": avg_win_pct,
                "playoff_rate": playoff_rate,

                "baseline_seasons_available":
                    baseline_seasons_available,
                "recent_seasons_available":
                    recent_seasons_available,
            }
        )

    summary = pd.DataFrame(rows)

    # --------------------------------------------------------
    # Rankings
    # --------------------------------------------------------

    summary["attendance_rank"] = (
        summary["avg_attendance"]
        .rank(
            ascending=False,
            method="min",
        )
    )

    summary["capacity_utilization_rank"] = (
        summary["avg_capacity_utilization"]
        .rank(
            ascending=False,
            method="min",
        )
    )

    summary["attendance_growth_rank"] = (
        summary["attendance_growth"]
        .rank(
            ascending=False,
            method="min",
        )
    )

    summary["capacity_utilization_growth_rank"] = (
        summary["capacity_utilization_growth"]
        .rank(
            ascending=False,
            method="min",
        )
    )

    # --------------------------------------------------------
    # Physical engagement composite
    # --------------------------------------------------------
    #
    # This is NOT the final market engagement score.
    #
    # It simply summarizes physical engagement using four
    # equally weighted percentile components:
    #
    #   25% average attendance
    #   25% capacity utilization
    #   25% attendance growth
    #   25% utilization growth
    #
    # The final market engagement analysis can decide how
    # physical and digital engagement should be combined.
    # --------------------------------------------------------

    components = [
        "avg_attendance",
        "avg_capacity_utilization",
        "attendance_growth",
        "capacity_utilization_growth",
    ]

    for column in components:
        percentile_column = f"{column}_percentile"

        summary[percentile_column] = (
            summary[column]
            .rank(
                pct=True,
                method="average",
            )
            * 100
        )

    percentile_columns = [
        "avg_attendance_percentile",
        "avg_capacity_utilization_percentile",
        "attendance_growth_percentile",
        "capacity_utilization_growth_percentile",
    ]

    summary["physical_engagement_score"] = (
        summary[percentile_columns]
        .mean(axis=1)
    )

    summary["physical_engagement_rank"] = (
        summary["physical_engagement_score"]
        .rank(
            ascending=False,
            method="min",
        )
    )

    summary = summary.sort_values(
        "physical_engagement_rank"
    ).reset_index(drop=True)

    return summary


# ============================================================
# PERFORMANCE RELATIONSHIPS
# ============================================================

def calculate_performance_relationships(data, summary):
    """
    Calculate relationships between physical engagement
    and team performance.

    Two types of analysis are produced:

    1. Team-season relationships
       - capacity utilization vs win %
       - attendance vs win %
       - attendance growth vs win %
       - utilization growth vs win %

    2. Team-level relationships
       - average physical engagement vs average win %
       - average physical engagement vs playoff rate

    Pearson and Spearman correlations are both reported.
    """

    # --------------------------------------------------------
    # Team-season relationships
    # --------------------------------------------------------

    season_correlations = []

    season_metrics = {
        "average_attendance": "Average Attendance",
        "capacity_utilization": "Capacity Utilization",
        "attendance_yoy_growth": "Attendance YoY Growth",
        "utilization_yoy_growth":
            "Capacity Utilization YoY Growth",
    }

    for metric, label in season_metrics.items():

        subset = data[
            [metric, "win_pct"]
        ].dropna()

        if len(subset) >= 3:

            pearson = subset[metric].corr(
                subset["win_pct"],
                method="pearson",
            )

            spearman = subset[metric].corr(
                subset["win_pct"],
                method="spearman",
            )

        else:
            pearson = np.nan
            spearman = np.nan

        season_correlations.append(
            {
                "analysis_level": "team-season",
                "engagement_metric": metric,
                "engagement_metric_label": label,
                "performance_metric": "win_pct",
                "n": len(subset),
                "pearson_correlation": pearson,
                "spearman_correlation": spearman,
            }
        )

    # --------------------------------------------------------
    # Team-level relationships
    # --------------------------------------------------------

    team_correlations = []

    team_metrics = {
        "avg_attendance":
            "Average Attendance",
        "avg_capacity_utilization":
            "Average Capacity Utilization",
        "attendance_growth":
            "Attendance Growth",
        "capacity_utilization_growth":
            "Capacity Utilization Growth",
        "physical_engagement_score":
            "Physical Engagement Score",
    }

    performance_metrics = {
        "avg_win_pct":
            "Average Win Percentage",
        "playoff_rate":
            "Playoff Rate",
    }

    for engagement_metric, engagement_label in team_metrics.items():

        for performance_metric, performance_label in (
            performance_metrics.items()
        ):

            subset = summary[
                [engagement_metric, performance_metric]
            ].dropna()

            if len(subset) >= 3:

                pearson = subset[
                    engagement_metric
                ].corr(
                    subset[performance_metric],
                    method="pearson",
                )

                spearman = subset[
                    engagement_metric
                ].corr(
                    subset[performance_metric],
                    method="spearman",
                )

            else:
                pearson = np.nan
                spearman = np.nan

            team_correlations.append(
                {
                    "analysis_level": "team",
                    "engagement_metric":
                        engagement_metric,
                    "engagement_metric_label":
                        engagement_label,
                    "performance_metric":
                        performance_metric,
                    "performance_metric_label":
                        performance_label,
                    "n": len(subset),
                    "pearson_correlation":
                        pearson,
                    "spearman_correlation":
                        spearman,
                }
            )

    correlations = pd.DataFrame(
        season_correlations + team_correlations
    )

    return correlations


# ============================================================
# DALLAS ANALYSIS
# ============================================================

def get_dallas_analysis(summary):
    """
    Extract Dallas-specific results for easy dashboard use.
    """

    dallas = summary[
        summary["team_id"] == "DAL"
    ].copy()

    if dallas.empty:
        return dallas

    return dallas


# ============================================================
# VALIDATION
# ============================================================

def validate_data(data, summary):
    """Run basic validation checks."""

    print("\n" + "=" * 60)
    print("PHYSICAL ENGAGEMENT VALIDATION")
    print("=" * 60)

    print(
        f"\nTeam-season rows: {len(data):,}"
    )

    print(
        f"Teams: {data['team_id'].nunique()}"
    )

    print(
        f"Seasons: "
        f"{data['season'].min()}–{data['season'].max()}"
    )

    print(
        "\nMissing values:"
    )

    validation_columns = [
        "average_attendance",
        "average_capacity",
        "capacity_utilization",
        "win_pct",
        "playoff_appearance",
    ]

    print(
        data[validation_columns]
        .isna()
        .sum()
        .to_string()
    )

    # --------------------------------------------------------
    # Check duplicate rows
    # --------------------------------------------------------

    duplicates = data.duplicated(
        subset=["team_id", "season"]
    ).sum()

    print(
        f"\nDuplicate team-season rows: {duplicates}"
    )

    if duplicates > 0:
        raise ValueError(
            "Duplicate team-season rows detected."
        )

    # --------------------------------------------------------
    # Check utilization range
    # --------------------------------------------------------

    valid_utilization = data[
        "capacity_utilization"
    ].dropna()

    invalid_utilization = (
        (valid_utilization < 0)
        | (valid_utilization > 2)
    ).sum()

    print(
        "Suspicious capacity utilization values: "
        f"{invalid_utilization}"
    )

    # We allow values above 100% because the project already
    # identified legitimate cases where average attendance
    # exceeded average capacity due to multiple venues.
    #
    # Values above 200%, however, are flagged as suspicious.

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print(
        f"\nSummary rows: {len(summary)}"
    )

    print(
        "\nDallas summary:"
    )

    dallas = get_dallas_analysis(summary)

    if not dallas.empty:

        display_columns = [
            "team_id",
            "avg_attendance",
            "avg_capacity_utilization",
            "attendance_growth",
            "capacity_utilization_growth",
            "physical_engagement_score",
            "physical_engagement_rank",
            "avg_win_pct",
            "playoff_rate",
        ]

        print(
            dallas[display_columns]
            .to_string(index=False)
        )

    print("\nValidation complete.")


# ============================================================
# SAVE OUTPUTS
# ============================================================

def save_outputs(data, summary, correlations):
    """Save analysis outputs."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Season-level output
    # --------------------------------------------------------

    season_columns = [
        "team_id",
        "team_name",
        "season",
        "average_attendance",
        "average_capacity",
        "capacity_utilization",
        "attendance_yoy_growth",
        "utilization_yoy_growth",
        "win_pct",
        "playoff_appearance",
    ]

    season_output = data[
        [
            column
            for column in season_columns
            if column in data.columns
        ]
    ].copy()

    season_output.to_csv(
        SEASON_OUTPUT,
        index=False,
    )

    # --------------------------------------------------------
    # Summary output
    # --------------------------------------------------------

    summary.to_csv(
        SUMMARY_OUTPUT,
        index=False,
    )

    # --------------------------------------------------------
    # Performance relationships
    # --------------------------------------------------------

    correlations.to_csv(
        PERFORMANCE_OUTPUT,
        index=False,
    )

    print("\nSaved outputs:")
    print(f"  {SEASON_OUTPUT}")
    print(f"  {SUMMARY_OUTPUT}")
    print(f"  {PERFORMANCE_OUTPUT}")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("WNBA PHYSICAL ENGAGEMENT ANALYSIS")
    print("=" * 60)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    attendance, team_season = load_data()

    print(
        f"\nLoaded attendance data: "
        f"{len(attendance):,} rows"
    )

    print(
        f"Loaded team-season data: "
        f"{len(team_season):,} rows"
    )

    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    data = prepare_data(
        attendance,
        team_season,
    )

    print(
        f"Merged dataset: "
        f"{len(data):,} rows"
    )

    # --------------------------------------------------------
    # Season metrics
    # --------------------------------------------------------

    data = calculate_season_metrics(data)

    # --------------------------------------------------------
    # Team summary
    # --------------------------------------------------------

    summary = calculate_period_summary(data)

    # --------------------------------------------------------
    # Performance relationships
    # --------------------------------------------------------

    correlations = calculate_performance_relationships(
        data,
        summary,
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    validate_data(
        data,
        summary,
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    save_outputs(
        data,
        summary,
        correlations,
    )

    print(
        "\nPhysical engagement analysis complete."
    )


if __name__ == "__main__":
    main()