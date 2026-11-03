"""
WNBA Performance Relationships Analysis

Evaluation 2:
    Are physical and digital fan engagement associated with
    team performance?

Physical relationships:
    Uses the existing team-season correlation analysis.

Digital relationships:
    Compares team-level longitudinal digital engagement metrics
    with team-level aggregated performance.

Cross-engagement relationships:
    Compares team-level physical engagement with team-level
    digital engagement.

Important:
    Performance is NOT included in any engagement score.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PHYSICAL_PERFORMANCE_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "tables"
    / "physical_engagement_performance.csv"
)

PHYSICAL_SUMMARY_FILE = (
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

STANDINGS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "wnba_team_season.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "tables"


# ============================================================
# ESTABLISHED MARKETS
# ============================================================

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

def correlation(x, y):

    data = pd.DataFrame({
        "x": x,
        "y": y,
    }).dropna()

    n = len(data)

    if n < 3:
        return {
            "n": n,
            "pearson_r": np.nan,
            "pearson_p": np.nan,
            "spearman_r": np.nan,
            "spearman_p": np.nan,
        }

    pearson_r, pearson_p = pearsonr(
        data["x"],
        data["y"],
    )

    spearman_r, spearman_p = spearmanr(
        data["x"],
        data["y"],
    )

    return {
        "n": n,
        "pearson_r": pearson_r,
        "pearson_p": pearson_p,
        "spearman_r": spearman_r,
        "spearman_p": spearman_p,
    }


def relationship_strength(r):

    if pd.isna(r):
        return "Insufficient data"

    r_abs = abs(r)

    if r_abs < 0.20:
        strength = "Very weak"
    elif r_abs < 0.40:
        strength = "Weak"
    elif r_abs < 0.60:
        strength = "Moderate"
    elif r_abs < 0.80:
        strength = "Strong"
    else:
        strength = "Very strong"

    if r > 0:
        direction = "positive"
    elif r < 0:
        direction = "negative"
    else:
        direction = "none"

    return f"{strength} {direction}"


def add_relationship(
    results,
    category,
    measure,
    performance,
    x,
    y,
):

    result = correlation(x, y)

    results.append({
        "category": category,
        "engagement_measure": measure,
        "performance_measure": performance,
        "n": result["n"],
        "pearson_r": result["pearson_r"],
        "pearson_p": result["pearson_p"],
        "pearson_interpretation":
            relationship_strength(
                result["pearson_r"]
            ),
        "spearman_r": result["spearman_r"],
        "spearman_p": result["spearman_p"],
        "spearman_interpretation":
            relationship_strength(
                result["spearman_r"]
            ),
    })


# ============================================================
# LOAD
# ============================================================

def load_data():

    required_files = {
        "physical_performance":
            PHYSICAL_PERFORMANCE_FILE,
        "physical_summary":
            PHYSICAL_SUMMARY_FILE,
        "digital":
            DIGITAL_FILE,
        "standings":
            STANDINGS_FILE,
    }

    for name, path in required_files.items():

        if not path.exists():
            raise FileNotFoundError(
                f"{name} file not found:\n{path}"
            )

    physical_performance = pd.read_csv(
        PHYSICAL_PERFORMANCE_FILE
    )

    physical_summary = pd.read_csv(
        PHYSICAL_SUMMARY_FILE
    )

    digital = pd.read_csv(
        DIGITAL_FILE
    )

    standings = pd.read_csv(
        STANDINGS_FILE
    )

    print(
        f"Loaded physical relationship results: "
        f"{len(physical_performance)} rows"
    )

    print(
        f"Loaded physical summary: "
        f"{len(physical_summary)} rows"
    )

    print(
        f"Loaded digital engagement data: "
        f"{len(digital)} rows"
    )

    print(
        f"Loaded standings data: "
        f"{len(standings)} rows"
    )

    return (
        physical_performance,
        physical_summary,
        digital,
        standings,
    )


# ============================================================
# PHYSICAL RELATIONSHIPS
# ============================================================

def prepare_physical_relationships(
    physical_performance
):

    required = [
        "analysis_level",
        "engagement_metric",
        "engagement_metric_label",
        "performance_metric",
        "n",
        "pearson_correlation",
        "spearman_correlation",
    ]

    missing = [
        column
        for column in required
        if column not in physical_performance.columns
    ]

    if missing:
        raise ValueError(
            "Physical relationship file is missing "
            f"columns: {missing}"
        )

    data = physical_performance.copy()

    data["category"] = "Physical"

    data["engagement_measure"] = (
        data["engagement_metric_label"]
    )

    data["performance_measure"] = (
        data["performance_metric_label"]
        .fillna(data["performance_metric"])
    )

    data["pearson_r"] = pd.to_numeric(
        data["pearson_correlation"],
        errors="coerce",
    )

    data["spearman_r"] = pd.to_numeric(
        data["spearman_correlation"],
        errors="coerce",
    )

    data["n"] = pd.to_numeric(
        data["n"],
        errors="coerce",
    )

    # This file already contains correlations, so p-values
    # are not reconstructed here.
    data["pearson_p"] = np.nan
    data["spearman_p"] = np.nan

    data["pearson_interpretation"] = (
        data["pearson_r"]
        .apply(relationship_strength)
    )

    data["spearman_interpretation"] = (
        data["spearman_r"]
        .apply(relationship_strength)
    )

    return data[
        [
            "analysis_level",
            "category",
            "engagement_measure",
            "performance_measure",
            "n",
            "pearson_r",
            "pearson_p",
            "pearson_interpretation",
            "spearman_r",
            "spearman_p",
            "spearman_interpretation",
        ]
    ]


# ============================================================
# DIGITAL PERFORMANCE
# ============================================================

def prepare_digital_performance(
    digital,
    standings,
):

    digital = digital[
        digital["team_id"].isin(
            ESTABLISHED_TEAMS
        )
    ].copy()

    standings = standings[
        standings["team_id"].isin(
            ESTABLISHED_TEAMS
        )
    ].copy()

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    digital_columns = [
        "ldes",
        "growth",
        "persistence",
        "momentum",
    ]

    for column in digital_columns:

        digital[column] = pd.to_numeric(
            digital[column],
            errors="coerce",
        )

    standings["win_pct"] = pd.to_numeric(
        standings["win_pct"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Playoff normalization
    # --------------------------------------------------------

    playoff_candidates = [
        "playoff",
        "playoff_appearance",
        "playoffs",
        "made_playoffs",
    ]

    playoff_col = next(
        (
            col
            for col in playoff_candidates
            if col in standings.columns
        ),
        None
    )

    if playoff_col is None:
        raise ValueError(
            "Could not find a playoff indicator column. "
            f"Available columns: {list(standings.columns)}"
        )

    # Rename whichever playoff column exists
    # to a single standardized name.
    if playoff_col != "playoff":
        standings = standings.rename(
            columns={
                playoff_col: "playoff"
            }
        )

    # Convert playoff indicator to numeric 0/1.
    if standings["playoff"].dtype == object:

        standings["playoff"] = (
            standings["playoff"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({
                "true": 1,
                "false": 0,
                "yes": 1,
                "no": 0,
                "1": 1,
                "0": 0,
            })
        )

    else:

        standings["playoff"] = pd.to_numeric(
            standings["playoff"],
            errors="coerce",
        )

    # --------------------------------------------------------
    # Aggregate performance to team level
    # --------------------------------------------------------

    performance = (
        standings
        .groupby("team_id")
        .agg(
            avg_win_pct=("win_pct", "mean"),
            playoff_rate=("playoff", "mean"),
            seasons_available=("season", "count"),
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    data = digital.merge(
        performance,
        on="team_id",
        how="inner",
    )

    return data

# ============================================================
# DIGITAL RELATIONSHIPS
# ============================================================

def calculate_digital_relationships(
    digital
):

    results = []

    measures = [
        ("LDES", "ldes"),
        ("Digital Growth", "growth"),
        ("Digital Persistence", "persistence"),
        ("Digital Momentum", "momentum"),
    ]

    for label, column in measures:

        add_relationship(
            results,
            category="Digital",
            measure=label,
            performance="Average Win Percentage",
            x=digital[column],
            y=digital["avg_win_pct"],
        )

        add_relationship(
            results,
            category="Digital",
            measure=label,
            performance="Playoff Rate",
            x=digital[column],
            y=digital["playoff_rate"],
        )

    result = pd.DataFrame(results)

    result.insert(
        0,
        "analysis_level",
        "team",
    )

    return result


# ============================================================
# PHYSICAL VS DIGITAL
# ============================================================

def calculate_cross_engagement(
    physical_summary,
    digital,
):

    physical = physical_summary[
        physical_summary["team_id"].isin(
            ESTABLISHED_TEAMS
        )
    ].copy()

    digital = digital[
        digital["team_id"].isin(
            ESTABLISHED_TEAMS
        )
    ].copy()

    data = physical.merge(
        digital[
            [
                "team_id",
                "ldes",
                "growth",
                "persistence",
                "momentum",
            ]
        ],
        on="team_id",
        how="inner",
    )

    results = []

    # --------------------------------------------------------
    # Physical score vs LDES
    # --------------------------------------------------------

    add_relationship(
        results,
        category="Physical vs Digital",
        measure="Physical Engagement Score",
        performance="LDES",
        x=data["physical_engagement_score"],
        y=data["ldes"],
    )

    # --------------------------------------------------------
    # Attendance growth vs digital growth
    # --------------------------------------------------------

    if "attendance_growth" in data.columns:

        add_relationship(
            results,
            category="Physical vs Digital",
            measure="Attendance Growth",
            performance="Digital Growth",
            x=data["attendance_growth"],
            y=data["growth"],
        )

    result = pd.DataFrame(results)

    result.insert(
        0,
        "analysis_level",
        "team",
    )

    return result


# ============================================================
# DALLAS SUMMARY
# ============================================================
def create_dallas_summary(
    digital,
    standings,
):

    dallas_digital = digital[
        digital["team_id"] == "DAL"
    ].copy()

    dallas_standings = standings[
        standings["team_id"] == "DAL"
    ].copy()

    if dallas_digital.empty:
        raise ValueError(
            "Dallas digital engagement data not found."
        )

    dallas_digital = dallas_digital.iloc[0]

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    dallas_standings["win_pct"] = pd.to_numeric(
        dallas_standings["win_pct"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Identify playoff column
    # --------------------------------------------------------

    playoff_candidates = [
        "playoff",
        "playoff_appearance",
        "playoffs",
        "made_playoffs",
    ]

    playoff_col = next(
        (
            col
            for col in playoff_candidates
            if col in dallas_standings.columns
        ),
        None
    )

    if playoff_col is None:
        raise ValueError(
            "Could not find a playoff indicator column. "
            f"Available columns: {list(dallas_standings.columns)}"
        )

    # --------------------------------------------------------
    # Convert playoff indicator to 0/1
    # --------------------------------------------------------

    if dallas_standings[playoff_col].dtype == object:

        dallas_standings["playoff_binary"] = (
            dallas_standings[playoff_col]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({
                "true": 1,
                "false": 0,
                "yes": 1,
                "no": 0,
                "1": 1,
                "0": 0,
            })
        )

    else:

        dallas_standings["playoff_binary"] = pd.to_numeric(
            dallas_standings[playoff_col],
            errors="coerce",
        )

    # --------------------------------------------------------
    # Build summary
    # --------------------------------------------------------

    return pd.DataFrame([
        {
            "metric": "LDES",
            "value": dallas_digital["ldes"],
        },
        {
            "metric": "Digital Growth",
            "value": dallas_digital["growth"],
        },
        {
            "metric": "Digital Persistence",
            "value": dallas_digital["persistence"],
        },
        {
            "metric": "Digital Momentum",
            "value": dallas_digital["momentum"],
        },
        {
            "metric": "Average Win Percentage",
            "value": dallas_standings[
                "win_pct"
            ].mean(),
        },
        {
            "metric": "Playoff Rate",
            "value": dallas_standings[
                "playoff_binary"
            ].mean(),
        },
    ])


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("WNBA PERFORMANCE RELATIONSHIPS ANALYSIS")
    print("=" * 60)

    (
        physical_performance,
        physical_summary,
        digital,
        standings,
    ) = load_data()

    # --------------------------------------------------------
    # Physical
    # --------------------------------------------------------

    physical_results = (
        prepare_physical_relationships(
            physical_performance
        )
    )

    # --------------------------------------------------------
    # Digital
    # --------------------------------------------------------

    digital_performance = (
        prepare_digital_performance(
            digital,
            standings,
        )
    )

    digital_results = (
        calculate_digital_relationships(
            digital_performance
        )
    )

    # --------------------------------------------------------
    # Physical vs digital
    # --------------------------------------------------------

    cross_results = (
        calculate_cross_engagement(
            physical_summary,
            digital_performance,
        )
    )

    # --------------------------------------------------------
    # Combined
    # --------------------------------------------------------

    all_results = pd.concat(
        [
            physical_results,
            digital_results,
            cross_results,
        ],
        ignore_index=True,
    )

    # --------------------------------------------------------
    # Dallas
    # --------------------------------------------------------

    dallas_summary = create_dallas_summary(
        digital_performance,
        standings,
    )

    # --------------------------------------------------------
    # Output directory
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Output files
    # --------------------------------------------------------

    physical_file = (
        OUTPUT_DIR
        / "performance_relationships_physical.csv"
    )

    digital_file = (
        OUTPUT_DIR
        / "performance_relationships_digital.csv"
    )

    cross_file = (
        OUTPUT_DIR
        / "performance_relationships_cross_engagement.csv"
    )

    all_file = (
        OUTPUT_DIR
        / "performance_relationships_all.csv"
    )

    dallas_file = (
        OUTPUT_DIR
        / "dallas_performance_summary.csv"
    )

    physical_results.to_csv(
        physical_file,
        index=False,
    )

    digital_results.to_csv(
        digital_file,
        index=False,
    )

    cross_results.to_csv(
        cross_file,
        index=False,
    )

    all_results.to_csv(
        all_file,
        index=False,
    )

    dallas_summary.to_csv(
        dallas_file,
        index=False,
    )

    # --------------------------------------------------------
    # Print physical relationships
    # --------------------------------------------------------

    print()
    print("PHYSICAL ENGAGEMENT VS PERFORMANCE")
    print("-" * 60)

    print(
        physical_results[
            [
                "analysis_level",
                "engagement_measure",
                "performance_measure",
                "n",
                "pearson_r",
                "spearman_r",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}",
        )
    )

    # --------------------------------------------------------
    # Print digital relationships
    # --------------------------------------------------------

    print()
    print("DIGITAL ENGAGEMENT VS PERFORMANCE")
    print("-" * 60)

    print(
        digital_results[
            [
                "engagement_measure",
                "performance_measure",
                "n",
                "pearson_r",
                "pearson_p",
                "spearman_r",
                "spearman_p",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}",
        )
    )

    # --------------------------------------------------------
    # Print cross relationships
    # --------------------------------------------------------

    print()
    print("PHYSICAL VS DIGITAL ENGAGEMENT")
    print("-" * 60)

    print(
        cross_results[
            [
                "engagement_measure",
                "performance_measure",
                "n",
                "pearson_r",
                "pearson_p",
                "spearman_r",
                "spearman_p",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}",
        )
    )

    # --------------------------------------------------------
    # Dallas
    # --------------------------------------------------------

    print()
    print("DALLAS PERFORMANCE CONTEXT")
    print("-" * 60)

    print(
        dallas_summary.to_string(
            index=False,
            float_format=lambda x: f"{x:.3f}",
        )
    )

    # --------------------------------------------------------
    # Files
    # --------------------------------------------------------

    print()
    print("Files created:")
    print(f"  {physical_file}")
    print(f"  {digital_file}")
    print(f"  {cross_file}")
    print(f"  {all_file}")
    print(f"  {dallas_file}")

    print()
    print("=" * 60)
    print("PERFORMANCE RELATIONSHIPS ANALYSIS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()