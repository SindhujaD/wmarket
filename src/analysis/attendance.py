import sys
from pathlib import Path

import pandas as pd
import numpy as np


# ---------------------------------------------------------
# PROJECT PATH
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from src.config import PROCESSED_DIR


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

def load_data():

    attendance_path = (
        PROCESSED_DIR /
        "wnba_attendance.csv"
    )

    performance_path = (
        PROCESSED_DIR /
        "wnba_team_season.csv"
    )

    attendance = pd.read_csv(
        attendance_path
    )

    performance = pd.read_csv(
        performance_path
    )

    return attendance, performance


# ---------------------------------------------------------
# PREPARE DATA
# ---------------------------------------------------------

def prepare_data(attendance, performance):

    performance = performance[
        [
            "season",
            "team_id",
            "win_pct",
            "playoff_appearance",
        ]
    ].copy()

    df = attendance.merge(
        performance,
        on=[
            "season",
            "team_id",
        ],
        how="left",
        validate="one_to_one"
    )

    return df


# ---------------------------------------------------------
# TEAM SUMMARY
# ---------------------------------------------------------

def team_summary(df):

    summary = (
        df
        .groupby(
            [
                "team_id",
                "team_name",
            ]
        )
        .agg(
            seasons=(
                "season",
                "count"
            ),
            avg_attendance=(
                "average_attendance",
                "mean"
            ),
            avg_capacity_utilization=(
                "capacity_utilization",
                "mean"
            ),
            median_capacity_utilization=(
                "capacity_utilization",
                "median"
            ),
            avg_win_pct=(
                "win_pct",
                "mean"
            ),
            playoff_rate=(
                "playoff_appearance",
                "mean"
            ),
        )
        .reset_index()
    )

    summary["playoff_rate"] *= 100

    return summary.sort_values(
        "avg_capacity_utilization",
        ascending=False
    )


# ---------------------------------------------------------
# SEASON SUMMARY
# ---------------------------------------------------------

def season_summary(df):

    summary = (
        df
        .groupby("season")
        .agg(
            teams=(
                "team_id",
                "nunique"
            ),
            avg_attendance=(
                "average_attendance",
                "mean"
            ),
            avg_capacity_utilization=(
                "capacity_utilization",
                "mean"
            ),
            median_capacity_utilization=(
                "capacity_utilization",
                "median"
            ),
            avg_win_pct=(
                "win_pct",
                "mean"
            ),
        )
        .reset_index()
    )

    return summary


# ---------------------------------------------------------
# DALLAS ANALYSIS
# ---------------------------------------------------------

def dallas_analysis(df):

    dallas = (
        df[
            df["team_id"] == "DAL"
        ]
        [
            [
                "season",
                "team_name",
                "average_attendance",
                "average_capacity",
                "capacity_utilization",
                "win_pct",
                "playoff_appearance",
            ]
        ]
        .sort_values("season")
        .copy()
    )

    return dallas


# ---------------------------------------------------------
# PERFORMANCE RELATIONSHIP
# ---------------------------------------------------------

def performance_relationship(df):

    analysis = df[
        [
            "capacity_utilization",
            "average_attendance",
            "win_pct",
            "playoff_appearance",
        ]
    ].dropna()

    correlations = (
        analysis.corr()
    )

    return correlations


# ---------------------------------------------------------
# YEAR-OVER-YEAR CHANGE
# ---------------------------------------------------------

def calculate_changes(df):

    df = df.sort_values(
        [
            "team_id",
            "season",
        ]
    ).copy()

    df["attendance_change_pct"] = (
        df
        .groupby("team_id")["average_attendance"]
        .pct_change()
        * 100
    )

    df["capacity_utilization_change_pct_points"] = (
        df
        .groupby("team_id")["capacity_utilization"]
        .diff()
        * 100
    )

    return df


# ---------------------------------------------------------
# SAVE OUTPUTS
# ---------------------------------------------------------

def save_outputs(
    df,
    team_summary_df,
    season_summary_df,
    dallas_df,
):

    team_summary_path = (
        PROCESSED_DIR /
        "attendance_team_summary.csv"
    )

    season_summary_path = (
        PROCESSED_DIR /
        "attendance_season_summary.csv"
    )

    dallas_path = (
        PROCESSED_DIR /
        "attendance_dallas.csv"
    )

    analysis_path = (
        PROCESSED_DIR /
        "attendance_analysis.csv"
    )

    team_summary_df.to_csv(
        team_summary_path,
        index=False
    )

    season_summary_df.to_csv(
        season_summary_path,
        index=False
    )

    dallas_df.to_csv(
        dallas_path,
        index=False
    )

    df.to_csv(
        analysis_path,
        index=False
    )

    print(
        "\nSaved:"
        f"\n{team_summary_path}"
        f"\n{season_summary_path}"
        f"\n{dallas_path}"
        f"\n{analysis_path}"
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print(
        "\n" + "=" * 70
    )

    print(
        "WNBA ATTENDANCE ANALYSIS"
    )

    print(
        "=" * 70
    )

    attendance, performance = (
        load_data()
    )

    df = prepare_data(
        attendance,
        performance
    )

    df = calculate_changes(df)

    # -----------------------------------------------------
    # TEAM SUMMARY
    # -----------------------------------------------------

    team = team_summary(df)

    print(
        "\n\nTEAM ATTENDANCE SUMMARY"
    )

    print(
        team.to_string(index=False)
    )

    # -----------------------------------------------------
    # SEASON SUMMARY
    # -----------------------------------------------------

    season = season_summary(df)

    print(
        "\n\nLEAGUE ATTENDANCE SUMMARY"
    )

    print(
        season.to_string(index=False)
    )

    # -----------------------------------------------------
    # DALLAS
    # -----------------------------------------------------

    dallas = dallas_analysis(df)

    print(
        "\n\nDALLAS WINGS"
    )

    print(
        dallas.to_string(index=False)
    )

    # -----------------------------------------------------
    # CORRELATIONS
    # -----------------------------------------------------

    correlations = performance_relationship(
        df
    )

    print(
        "\n\nCORRELATION MATRIX"
    )

    print(
        correlations.to_string()
    )

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    save_outputs(
        df,
        team,
        season,
        dallas
    )

    print(
        "\nAttendance analysis complete."
    )


if __name__ == "__main__":
    main()