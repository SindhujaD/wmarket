from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ATTENDANCE_FILE = (
    PROJECT_ROOT / "data" / "processed" / "attendance_analysis.csv"
)

LDES_FILE = (
    PROJECT_ROOT / "data" / "processed" / "wnba_local_digital_engagement.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"


# ============================================================
# SETTINGS
# ============================================================

# 2021 attendance was heavily affected by COVID restrictions,
# so it is NOT used as the baseline for physical engagement growth.
#
# We compare:
#   Early period: 2023-2024
#   Recent period: 2025-2026
#
# 2026 is currently partial, but the LDES sensitivity analysis
# showed that this does not materially change the rankings.

EARLY_SEASONS = [2023, 2024]
RECENT_SEASONS = [2025, 2026]

# Established teams used for longitudinal digital analysis.
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

def find_column(df, candidates, description):
    """
    Find the first matching column from a list of candidates.
    Raises a useful error if none are present.
    """
    for column in candidates:
        if column in df.columns:
            return column

    raise ValueError(
        f"Could not find {description}.\n"
        f"Tried: {candidates}\n"
        f"Available columns: {list(df.columns)}"
    )


def safe_pct_change(recent, early):
    """
    Percentage change from early period to recent period.
    """
    if pd.isna(early) or early == 0:
        return np.nan

    return ((recent - early) / early) * 100


# ============================================================
# LOAD ATTENDANCE / PERFORMANCE DATA
# ============================================================

print("\nLoading attendance data...")

attendance = pd.read_csv(ATTENDANCE_FILE)

print(f"Attendance rows: {len(attendance):,}")
print(f"Attendance columns: {list(attendance.columns)}")


# ------------------------------------------------------------
# Identify important columns
# ------------------------------------------------------------

team_col = find_column(
    attendance,
    ["team_id", "team", "team_abbr", "team_code"],
    "team identifier",
)

season_col = find_column(
    attendance,
    ["season", "year"],
    "season",
)

attendance_col = find_column(
    attendance,
    ["average_attendance", "avg_attendance"],
    "average attendance",
)

capacity_col = find_column(
    attendance,
    ["average_capacity", "avg_capacity"],
    "average capacity",
)

win_col = find_column(
    attendance,
    ["win_pct", "win_percentage", "winning_pct"],
    "win percentage",
)

playoff_col = find_column(
    attendance,
    ["playoff", "playoffs", "made_playoffs"],
    "playoff indicator",
)


# ============================================================
# STANDARDIZE ATTENDANCE DATA
# ============================================================

attendance = attendance.rename(
    columns={
        team_col: "team",
        season_col: "season",
        attendance_col: "average_attendance",
        capacity_col: "average_capacity",
        win_col: "win_pct",
        playoff_col: "playoff",
    }
).copy()


attendance["season"] = pd.to_numeric(
    attendance["season"],
    errors="coerce",
)

attendance["average_attendance"] = pd.to_numeric(
    attendance["average_attendance"],
    errors="coerce",
)

attendance["average_capacity"] = pd.to_numeric(
    attendance["average_capacity"],
    errors="coerce",
)

attendance["win_pct"] = pd.to_numeric(
    attendance["win_pct"],
    errors="coerce",
)

attendance["playoff"] = pd.to_numeric(
    attendance["playoff"],
    errors="coerce",
)


# ============================================================
# CAPACITY UTILIZATION
# ============================================================

# Important:
# 2021 Indiana has 0 attendance and 0 capacity because fans
# were not allowed. That should be treated as missing utilization,
# NOT as 0% utilization.

attendance["capacity_utilization"] = np.where(
    attendance["average_capacity"] > 0,
    attendance["average_attendance"]
    / attendance["average_capacity"],
    np.nan,
)

attendance["capacity_utilization_pct"] = (
    attendance["capacity_utilization"] * 100
)


# ============================================================
# YEAR-OVER-YEAR PHYSICAL ENGAGEMENT
# ============================================================

attendance = attendance.sort_values(
    ["team", "season"]
).reset_index(drop=True)


attendance["attendance_yoy_pct"] = (
    attendance
    .groupby("team")["average_attendance"]
    .pct_change(fill_method=None)
    * 100
)


attendance["utilization_yoy_pct"] = (
    attendance
    .groupby("team")["capacity_utilization"]
    .pct_change(fill_method=None)
    * 100
)


# ============================================================
# TEAM-SEASON ENGAGEMENT/PERFORMANCE DATASET
# ============================================================

team_season = attendance[
    [
        "team",
        "season",
        "average_attendance",
        "average_capacity",
        "capacity_utilization",
        "capacity_utilization_pct",
        "attendance_yoy_pct",
        "utilization_yoy_pct",
        "win_pct",
        "playoff",
    ]
].copy()


team_season = team_season.sort_values(
    ["team", "season"]
).reset_index(drop=True)


team_season_output = (
    OUTPUT_DIR / "wnba_engagement_performance.csv"
)

team_season.to_csv(
    team_season_output,
    index=False,
)

print(
    f"\nSaved team-season dataset:\n"
    f"{team_season_output}"
)


# ============================================================
# PHYSICAL MARKET ENGAGEMENT SUMMARY
# ============================================================

print("\nCalculating physical engagement metrics...")


def calculate_period_metrics(group):
    """
    Calculate early-period and recent-period physical engagement
    metrics for one team.
    """

    early = group[
        group["season"].isin(EARLY_SEASONS)
    ]

    recent = group[
        group["season"].isin(RECENT_SEASONS)
    ]

    early_attendance = early[
        "average_attendance"
    ].mean()

    recent_attendance = recent[
        "average_attendance"
    ].mean()

    early_utilization = early[
        "capacity_utilization"
    ].mean()

    recent_utilization = recent[
        "capacity_utilization"
    ].mean()

    return pd.Series(
        {
            "early_attendance_mean": early_attendance,
            "recent_attendance_mean": recent_attendance,

            "attendance_growth_pct": safe_pct_change(
                recent_attendance,
                early_attendance,
            ),

            "early_capacity_utilization": early_utilization,
            "recent_capacity_utilization": recent_utilization,

            "capacity_utilization_growth_pct": safe_pct_change(
                recent_utilization,
                early_utilization,
            ),

            "avg_attendance": group[
                "average_attendance"
            ].mean(),

            "avg_capacity_utilization": group[
                "capacity_utilization"
            ].mean(),

            "avg_win_pct": group[
                "win_pct"
            ].mean(),

            "playoff_rate": group[
                "playoff"
            ].mean(),

            "seasons": group[
                "season"
            ].nunique(),
        }
    )


physical_summary = (
    attendance
    .groupby("team")
    .apply(
        calculate_period_metrics,
        include_groups=False,
    )
    .reset_index()
)


# Convert playoff rate to percentage.
physical_summary["playoff_rate_pct"] = (
    physical_summary["playoff_rate"] * 100
)


# ============================================================
# LOAD LDES
# ============================================================

print("\nLoading LDES data...")

ldes = pd.read_csv(LDES_FILE)

print(f"LDES rows: {len(ldes):,}")
print(f"LDES columns: {list(ldes.columns)}")


# ------------------------------------------------------------
# Standardize LDES team column
# ------------------------------------------------------------

ldes_team_col = find_column(
    ldes,
    ["team", "team_id", "team_abbr"],
    "LDES team identifier",
)

ldes = ldes.rename(
    columns={
        ldes_team_col: "team"
    }
).copy()


# ============================================================
# KEEP CORE LDES METRICS
# ============================================================

ldes_columns = [
    "team",
    "historical_mean",
    "recent_mean",
    "momentum_baseline_mean",
    "growth",
    "persistence",
    "momentum",
    "growth_percentile",
    "persistence_percentile",
    "momentum_percentile",
    "ldes",
    "ldes_rank",
    "ldes_sensitivity",
    "ldes_sensitivity_rank",
    "rank_difference",
    "ldes_difference",
    "historical_months",
    "momentum_months",
    "recent_months",
]

missing_ldes = [
    column
    for column in ldes_columns
    if column not in ldes.columns
]

if missing_ldes:
    raise ValueError(
        "The LDES file is missing expected columns:\n"
        + "\n".join(missing_ldes)
    )


ldes = ldes[ldes_columns].copy()


# Only established teams belong in the core longitudinal
# digital benchmark.

ldes_core = ldes[
    ldes["team"].isin(ESTABLISHED_TEAMS)
].copy()


# ============================================================
# COMBINE PHYSICAL + DIGITAL ENGAGEMENT
# ============================================================

print("\nCombining physical and digital engagement...")


market_engagement = physical_summary.merge(
    ldes_core,
    on="team",
    how="inner",
)


# ============================================================
# RANK MARKET ENGAGEMENT COMPONENTS
# ============================================================

# These rankings are descriptive market benchmarks.
# Higher = stronger engagement.

ranking_columns = {
    "avg_attendance": "attendance_rank",
    "avg_capacity_utilization": "capacity_utilization_rank",
    "attendance_growth_pct": "attendance_growth_rank",
    "capacity_utilization_growth_pct": "utilization_growth_rank",
    "ldes": "ldes_rank_market",
    "growth": "digital_growth_rank",
    "persistence": "digital_persistence_rank",
    "momentum": "digital_momentum_rank",
}


for metric, rank_column in ranking_columns.items():
    market_engagement[rank_column] = (
        market_engagement[metric]
        .rank(
            ascending=False,
            method="min",
        )
    )


# ============================================================
# PHYSICAL ENGAGEMENT SCORE
# ============================================================

# Equal weighting across the four physical indicators:
#
# 25% average attendance
# 25% capacity utilization
# 25% attendance growth
# 25% utilization growth

market_engagement["physical_engagement_score"] = (
    market_engagement["attendance_rank"]
    .rank(ascending=True, pct=True)
    * 25
    +
    market_engagement["capacity_utilization_rank"]
    .rank(ascending=True, pct=True)
    * 25
    +
    market_engagement["attendance_growth_rank"]
    .rank(ascending=True, pct=True)
    * 25
    +
    market_engagement["utilization_growth_rank"]
    .rank(ascending=True, pct=True)
    * 25
)


# ============================================================
# DIGITAL ENGAGEMENT COMPONENTS
# ============================================================

# LDES is already the combined digital score.
# We keep the underlying components visible for the dashboard.

market_engagement["digital_engagement_score"] = (
    market_engagement["ldes"]
)


# ============================================================
# OVERALL MARKET ENGAGEMENT
# ============================================================

# We deliberately do NOT include:
# - win percentage
# - playoff participation
#
# Those are performance variables, not engagement measures.

market_engagement["market_engagement_score"] = (
    (
        market_engagement["physical_engagement_score"]
        + market_engagement["digital_engagement_score"]
    )
    / 2
)


market_engagement["market_engagement_rank"] = (
    market_engagement["market_engagement_score"]
    .rank(
        ascending=False,
        method="min",
    )
)


# ============================================================
# DALLAS FLAG
# ============================================================

market_engagement["is_dallas"] = (
    market_engagement["team"] == "DAL"
)


# ============================================================
# SORT + SAVE
# ============================================================

market_engagement = market_engagement.sort_values(
    "market_engagement_score",
    ascending=False,
).reset_index(drop=True)


market_summary_output = (
    OUTPUT_DIR / "wnba_market_engagement_summary.csv"
)

market_engagement.to_csv(
    market_summary_output,
    index=False,
)


print(
    f"\nSaved market engagement summary:\n"
    f"{market_summary_output}"
)


# ============================================================
# TEAM-LEVEL PERFORMANCE SUMMARY
# ============================================================

# This is the correct level for comparing LDES to team
# performance because LDES is a longitudinal team-level metric.
#
# We do NOT repeat the same LDES score across six seasons.

performance_summary = (
    attendance[
        attendance["team"].isin(ESTABLISHED_TEAMS)
    ]
    .groupby("team")
    .agg(
        avg_attendance=(
            "average_attendance",
            "mean",
        ),
        avg_capacity_utilization=(
            "capacity_utilization",
            "mean",
        ),
        attendance_growth_pct=(
            "average_attendance",
            lambda x: np.nan,
        ),
        utilization_growth_pct=(
            "capacity_utilization",
            lambda x: np.nan,
        ),
        avg_win_pct=(
            "win_pct",
            "mean",
        ),
        playoff_rate=(
            "playoff",
            "mean",
        ),
        seasons=(
            "season",
            "nunique",
        ),
    )
    .reset_index()
)


# Merge in the physical growth metrics already calculated.
performance_summary = performance_summary.drop(
    columns=[
        "attendance_growth_pct",
        "utilization_growth_pct",
    ]
).merge(
    physical_summary[
        [
            "team",
            "attendance_growth_pct",
            "capacity_utilization_growth_pct",
        ]
    ],
    on="team",
    how="left",
)


# Merge digital engagement.
performance_summary = performance_summary.merge(
    ldes_core[
        [
            "team",
            "ldes",
            "growth",
            "persistence",
            "momentum",
        ]
    ],
    on="team",
    how="left",
)


performance_summary["playoff_rate_pct"] = (
    performance_summary["playoff_rate"] * 100
)


performance_summary = performance_summary.sort_values(
    "ldes",
    ascending=False,
).reset_index(drop=True)


performance_output = (
    OUTPUT_DIR
    / "wnba_engagement_performance_summary.csv"
)

performance_summary.to_csv(
    performance_output,
    index=False,
)


print(
    f"\nSaved team-level engagement/performance summary:\n"
    f"{performance_output}"
)


# ============================================================
# CORRELATIONS
# ============================================================

print("\nCalculating correlations...")


correlation_metrics = {
    "avg_capacity_utilization": (
        "Average capacity utilization"
    ),
    "capacity_utilization_growth_pct": (
        "Capacity utilization growth"
    ),
    "avg_attendance": (
        "Average attendance"
    ),
    "attendance_growth_pct": (
        "Attendance growth"
    ),
    "ldes": (
        "LDES"
    ),
    "growth": (
        "Digital growth"
    ),
    "persistence": (
        "Digital persistence"
    ),
    "momentum": (
        "Digital momentum"
    ),
}


performance_variables = {
    "avg_win_pct": "Average win %",
    "playoff_rate": "Playoff rate",
}


correlation_rows = []


for engagement_column, engagement_label in correlation_metrics.items():

    for performance_column, performance_label in performance_variables.items():

        subset = performance_summary[
            [
                engagement_column,
                performance_column,
            ]
        ].dropna()

        if len(subset) < 3:
            continue

        pearson = subset[
            engagement_column
        ].corr(
            subset[performance_column],
            method="pearson",
        )

        spearman = subset[
            engagement_column
        ].corr(
            subset[performance_column],
            method="spearman",
        )

        correlation_rows.append(
            {
                "engagement_metric": engagement_column,
                "engagement_label": engagement_label,
                "performance_metric": performance_column,
                "performance_label": performance_label,
                "n": len(subset),
                "pearson_r": pearson,
                "spearman_rho": spearman,
            }
        )


correlations = pd.DataFrame(
    correlation_rows
)


correlation_output = (
    OUTPUT_DIR
    / "wnba_engagement_performance_correlations.csv"
)

correlations.to_csv(
    correlation_output,
    index=False,
)


print(
    f"\nSaved correlation table:\n"
    f"{correlation_output}"
)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

print(
    f"\nCore LDES teams: "
    f"{len(ldes_core)}"
)

print(
    "\nMarket engagement summary:"
)

print(
    market_engagement[
        [
            "team",
            "physical_engagement_score",
            "digital_engagement_score",
            "market_engagement_score",
            "market_engagement_rank",
        ]
    ].to_string(index=False)
)


print(
    "\nDallas:"
)

print(
    market_engagement[
        market_engagement["team"] == "DAL"
    ][
        [
            "team",
            "avg_attendance",
            "avg_capacity_utilization",
            "attendance_growth_pct",
            "capacity_utilization_growth_pct",
            "ldes",
            "growth",
            "persistence",
            "momentum",
            "physical_engagement_score",
            "market_engagement_score",
            "market_engagement_rank",
        ]
    ].to_string(index=False)
)


print(
    "\nCorrelation results:"
)

print(
    correlations[
        [
            "engagement_metric",
            "performance_metric",
            "n",
            "pearson_r",
            "spearman_rho",
        ]
    ].to_string(index=False)
)


print("\n" + "=" * 70)
print("DONE")
print("=" * 70)