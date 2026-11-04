from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="WNBA Market Penetration",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MARKET_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "tables"
    / "market_engagement_full.csv"
)

DALLAS_MARKET_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "tables"
    / "dallas_market_engagement.csv"
)

DIGITAL_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "wnba_local_digital_engagement.csv"
)

PHYSICAL_SUMMARY_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "tables"
    / "physical_engagement_summary.csv"
)

PERFORMANCE_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "tables"
    / "performance_relationships_all.csv"
)

DALLAS_PERFORMANCE_FILE = (
    PROJECT_ROOT
    / "outputs"
    / "tables"
    / "dallas_performance_summary.csv"
)


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


TEAM_NAMES = {
    "ATL": "Atlanta Dream",
    "CHI": "Chicago Sky",
    "CON": "Connecticut Sun",
    "DAL": "Dallas Wings",
    "IND": "Indiana Fever",
    "LVA": "Las Vegas Aces",
    "LAS": "Los Angeles Sparks",
    "MIN": "Minnesota Lynx",
    "NYL": "New York Liberty",
    "PHX": "Phoenix Mercury",
    "SEA": "Seattle Storm",
    "WAS": "Washington Mystics",
}


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        padding-top: 1rem;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .dashboard-title {
        font-size: 2.7rem;
        font-weight: 750;
        margin-bottom: 0.2rem;
    }

    .dashboard-subtitle {
        font-size: 1.15rem;
        color: #ffffff;
        margin-bottom: 2rem;
    }

    .section-title {
        font-size: 1.7rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 0.5rem;
    }

    .section-description {
        color: #ffffff;
        margin-bottom: 1rem;
    }

    .insight-box {
        padding: 1.2rem;
        border-radius: 10px;
        background-color: white;
        color: black;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    .insight-title {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    market = pd.read_csv(MARKET_FILE)
    digital = pd.read_csv(DIGITAL_FILE)
    physical = pd.read_csv(PHYSICAL_SUMMARY_FILE)
    performance = pd.read_csv(PERFORMANCE_FILE)

    if DALLAS_MARKET_FILE.exists():
        dallas_market = pd.read_csv(DALLAS_MARKET_FILE)
    else:
        dallas_market = pd.DataFrame()

    if DALLAS_PERFORMANCE_FILE.exists():
        dallas_performance = pd.read_csv(
            DALLAS_PERFORMANCE_FILE
        )
    else:
        dallas_performance = pd.DataFrame()

    return (
        market,
        digital,
        physical,
        performance,
        dallas_market,
        dallas_performance,
    )


(
    market,
    digital,
    physical,
    performance,
    dallas_market,
    dallas_performance,
) = load_data()


# ============================================================
# STANDARDIZE DATA
# ============================================================

for df in [
    market,
    digital,
    physical,
]:
    if "team_id" in df.columns:
        df["team_name_display"] = (
            df["team_id"]
            .map(TEAM_NAMES)
            .fillna(df["team_id"])
        )


# Keep only established markets for the primary comparison.
market = market[
    market["team_id"].isin(ESTABLISHED_TEAMS)
].copy()

digital_established = digital[
    digital["team_id"].isin(ESTABLISHED_TEAMS)
].copy()

physical_established = physical[
    physical["team_id"].isin(ESTABLISHED_TEAMS)
].copy()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_value(df, column, team_id="DAL"):

    row = df[df["team_id"] == team_id]

    if row.empty or column not in row.columns:
        return np.nan

    return row.iloc[0][column]


def format_percent(value):

    if pd.isna(value):
        return "—"

    return f"{value * 100:.1f}%"


def format_score(value):

    if pd.isna(value):
        return "—"

    return f"{value:.1f}"


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="dashboard-title">'
    'WNBA Market Penetration'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="dashboard-subtitle">'
    'This project is an analysis of how effectively WNBA teams are building and sustaining '
    'fan engagement in their markets. I wanted to see how the Dallas Wings compare with other established WNBA markets, '
    'and what the data can tell us about the relationship between digital engagement, physical attendance, and on-court performance. ' \
    'You can peruse through all sections of this analysis with in the sidebar. The data and code are publicly available on the GitHub repository, ' \
    'which can be found by pressing the Github logo in the top right corner.'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("Explore the analysis")

page = st.sidebar.radio(
    "Dashboard section",
    [
        "Market Overview",
        "Physical Engagement",
        "Digital Engagement",
        "Engagement & Performance",
    ],
)

st.sidebar.markdown("---")

st.sidebar.caption(
    "Primary benchmark: 12 established WNBA markets."
)

st.sidebar.caption(
    "Golden State and Portland are excluded from "
    "longitudinal digital benchmarking because of "
    "insufficient franchise history."
)


# ============================================================
# DALLAS METRICS
# ============================================================

dallas_market_row = market[
    market["team_id"] == "DAL"
]

if not dallas_market_row.empty:

    dallas_market_row = dallas_market_row.iloc[0]

    dallas_rank = dallas_market_row.get(
        "market_engagement_rank",
        np.nan,
    )

    dallas_market_score = dallas_market_row.get(
        "market_engagement_score",
        np.nan,
    )

    dallas_physical_score = dallas_market_row.get(
        "physical_engagement_score",
        np.nan,
    )

    dallas_ldes = dallas_market_row.get(
        "ldes",
        np.nan,
    )
    gap = dallas_market_row.get(
        "digital_minus_physical",
        dallas_ldes - dallas_physical_score,
    )

else:

    dallas_rank = np.nan
    dallas_market_score = np.nan
    dallas_physical_score = np.nan
    dallas_ldes = np.nan
    gap = np.nan



# ============================================================
# PAGE 1 — MARKET OVERVIEW
# ============================================================

if page == "Market Overview":

    st.markdown(
        '<div class="section-title">'
        'The Dallas Wings at a Glance'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'This page explores how the Dallas Wings compare against other WNBA teams in regards to their digital and physical engagement.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.expander(" **How to read this page and its numbers** "):
        st.markdown(
            '''
            **Overall market rank** ranks each team's market performance as a rank between the 12 WNBA teams in the 12 established markets; 1 is the highest rank.

            **Market Engagement Score** is a 0–100 composite score that gives
            50% weight to the Physical Engagement Score and 50% to the Local Digital Engagement Score.

            **Physical Engagement Score** combines four equally weighted
            percentile components calculated upstream: average attendance,
            average capacity utilization, attendance growth, and utilization
            growth. These components are calculated for the 2021-2026 period.

            **Local Digital Engagement Score (LDES)**  is a 0–100 relative index combining local digital
            search-interest growth, persistence, and recent momentum, based on Google Trends data. It is calculated for the 2021-2026 period.

            These are comparative index scores, not percentages of fans,
            market share, or probabilities. A score of 80 does not mean
            that 80% of residents are fans.
            '''
        )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Overall Market Rank",
            (
                f"#{int(dallas_rank)} of 12"
                if not pd.isna(dallas_rank)
                else "—"
            ),
        )

    with col2:
        st.metric(
            "Overall Market Engagement Score",
            format_score(dallas_market_score),
        )

    with col3:
        st.metric(
            "Physical Engagement Percentile",
            format_score(dallas_physical_score),
        )

    with col4:
        st.metric(
            "Digital Engagement Percentiles",
            format_score(dallas_ldes),
        )

    with col5:
        st.metric(
            "Digital − physical gap",
            format_score(gap),
        )

    st.markdown(
        '<div class="section-title">'
        'Market engagement ranking'
        '</div>',
        unsafe_allow_html=True,
    )

    ranking = market.sort_values(
        "market_engagement_rank"
    ).copy()

    ranking["Team"] = ranking["team_id"].map(
        TEAM_NAMES
    )

    fig = px.bar(
        ranking,
        x="market_engagement_score",
        y="Team",
        orientation="h",
        text="market_engagement_score",
        labels={
            "market_engagement_score":
                "Market Engagement Score",
            "Team": "",
        },
        title="Established-market engagement benchmark",
    )

    fig.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside",
    )

    fig.update_layout(
        height=600,
        yaxis={"categoryorder": "array",
               "categoryarray": ranking["Team"][::-1]},
        showlegend=False,
        margin=dict(l=20, r=60, t=60, b=20),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.success(
        ' **Dallas takeaway:** '
        'Dallas ranks 4th among the 12 established markets. '
        'Its overall position is driven by a particularly strong '
        'digital engagement profile, while physical engagement '
        'remains comparatively lower.',
    )

    st.markdown(
        '<div class="section-description" style="font-weight: bold;">'
        'Are teams building engagement primarily through physical attendance, '
        'digital interest, or both?'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.expander(" **How to interpret the four-quadrant chart** "):
        st.markdown(
            '''
            Each dot is one established WNBA market. The x-axis is its
            **Physical Engagement Score** and the y-axis is its **LDES**.
            The two central reference lines are the medians of the 12
            markets shown.

            - **Upper right:** above-median physical and digital engagement.
            - **Upper left:** below-median physical, above-median digital.
            - **Lower right:** above-median physical, below-median digital.
            - **Lower left:** below-median physical and digital engagement.

            “High” and “lower” are relative to this comparison group, not
            absolute industry standards. The median intersection is a
            benchmark, not a zero point. The digital-minus-physical gap is
            a difference between index scores, measured in score points.
            '''
        )

    plot_data = market.copy()

    plot_data["Team"] = plot_data["team_id"].map(TEAM_NAMES)

    fig = px.scatter(
        plot_data,
        x="physical_engagement_score",
        y="ldes",
        text="team_id",
        hover_name="Team",
        hover_data={
            "physical_engagement_score": ":.1f",
            "ldes": ":.1f",
            "market_engagement_score": ":.1f",
        },
        labels={
            "physical_engagement_score":
                "Physical Engagement Score",
            "ldes":
                "Local Digital Engagement Score",
        },
        title="Physical vs digital engagement",
    )

    fig.update_traces(
        marker=dict(size=14),
        textposition="top center",
    )

    physical_median = plot_data[
        "physical_engagement_score"
    ].median()

    digital_median = plot_data[
        "ldes"
    ].median()

    # --------------------------------------------------------
    # Center axes at the established-market medians
    # --------------------------------------------------------

    fig.add_vline(
        x=physical_median,
        line_color="#333333",
        line_width=2,
        line_dash="solid",
    )

    fig.add_hline(
        y=digital_median,
        line_color="#333333",
        line_width=2,
        line_dash="solid",
    )

    # --------------------------------------------------------
    # Quadrant labels
    # --------------------------------------------------------

    x_min = plot_data["physical_engagement_score"].min()
    x_max = plot_data["physical_engagement_score"].max()
    y_min = plot_data["ldes"].min()
    y_max = plot_data["ldes"].max()

    x_padding = (x_max - x_min) * 0.08
    y_padding = (y_max - y_min) * 0.08

    fig.add_annotation(
        x=(physical_median + x_max) / 2,
        y=(digital_median + y_max) / 2,
        text="<b>HIGH PHYSICAL<br>HIGH DIGITAL</b>",
        showarrow=False,
        font=dict(size=12, color="#777777"),
    )

    fig.add_annotation(
        x=(x_min + physical_median) / 2,
        y=(digital_median + y_max) / 2,
        text="<b>LOWER PHYSICAL<br>HIGH DIGITAL</b>",
        showarrow=False,
        font=dict(size=12, color="#777777"),
    )

    fig.add_annotation(
        x=(physical_median + x_max) / 2,
        y=(y_min + digital_median) / 2,
        text="<b>HIGH PHYSICAL<br>LOWER DIGITAL</b>",
        showarrow=False,
        font=dict(size=12, color="#777777"),
    )

    fig.add_annotation(
        x=(x_min + physical_median) / 2,
        y=(y_min + digital_median) / 2,
        text="<b>LOWER PHYSICAL<br>LOWER DIGITAL</b>",
        showarrow=False,
        font=dict(size=12, color="#777777"),
    )

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    fig.update_layout(
        height=700,
        margin=dict(l=40, r=40, t=80, b=40),
        xaxis=dict(
            range=[
                x_min - x_padding,
                x_max + x_padding,
            ],
            showline=False,
            zeroline=False,
            showgrid=True,
            gridcolor="rgba(150,150,150,0.15)",
        ),
        yaxis=dict(
            range=[
                y_min - y_padding,
                y_max + y_padding,
            ],
            showline=False,
            zeroline=False,
            showgrid=True,
            gridcolor="rgba(150,150,150,0.15)",
        ),
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    dallas_row = market[
        market["team_id"] == "DAL"
    ]

    if not dallas_row.empty:
        quadrant = dallas_row.get(
            "market_quadrant",
            "—",
        )

    else:
        quadrant = "—"

    st.success(
        "Dallas falls into the **Lower Physical - Higher Digital** quadrant. "
        "This means its digital engagement is substantially "
        "stronger than its physical engagement relative to "
        "the established-market benchmark."
        "This suggests that the market has an audience that "
        "is engaging with the Wings digitally even though that " 
        "engagement has not translated into equally strong physical attendance."
    )

    st.markdown(
        '<div class="section-title">'
        'Team-level market engagement metrics'
        '</div>',
        unsafe_allow_html=True,
    )

    display_cols = [
        "team_id",
        "market_engagement_rank",
        "market_engagement_score",
        "physical_engagement_score",
        "ldes",
        "market_quadrant",
    ]

    available_cols = [
        c for c in display_cols
        if c in market.columns
    ]

    table = market.sort_values(
        "market_engagement_rank"
    )[available_cols].copy()

    table["team_id"] = table["team_id"].map(
        TEAM_NAMES
    )

    table = table.rename(
        columns={
            "team_id": "Team",
            "market_engagement_rank": "Rank",
            "market_engagement_score":
                "Market Score",
            "physical_engagement_score":
                "Physical Score",
            "ldes": "LDES",
            "market_quadrant": "Quadrant",
        }
    )

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
    )

        
    with st.expander("Assumptions & Limitations"):
        st.markdown("""
        - Market population is used as a proxy for the potential audience, not a measure of actual fan interest.
        - Team markets are represented using the geographic definitions and population data selected for the project.
        - Market size alone does not account for differences in income, competing sports, local interest, or fan demographics.
        - Historical comparisons may be affected by franchise relocations, expansion, and changes in market boundaries.
        """)

# ============================================================
# PAGE 2 — PHYSICAL ENGAGEMENT
# ============================================================

elif page == "Physical Engagement":

    st.markdown(
        '<div class="section-title">'
        'Physical engagement'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'This page explores how effectively WNBA teams convert '
        'their local fan interest into in-person attendance. '
        'The Physical Engagement Score combines attendance, '
        'arena capacity utilization, and growth in both measures.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.expander("**What the Physical Engagement Score measures and how to read its components**"):
        st.markdown(
            '''
            The Physical Engagement Score is a **relative 0–100 index**
            designed to compare how successfully WNBA teams attract
            fans to their games.

            It combines four equally weighted components:

            - **Average attendance (25%):** Average number of attendees
              per game across the available seasons.
            - **Average capacity utilization (25%):** Average share of
              available arena capacity filled during games.
            - **Attendance growth (25%):** Change in average attendance
              between the 2023–2024 baseline and the 2025–2026 recent period.
            - **Capacity utilization growth (25%):** Change in average
              capacity utilization between those same periods.

            Each component is converted to a percentile rank among the
            established markets before weighting. The final score is
            the average of those four percentile rankings.

            The growth measures compare the average of the recent period
            with the average of the baseline period. Positive growth
            indicates improvement; negative growth indicates a decline.

            The component table shows both the underlying measurements
            and their percentile rankings. Percentile rankings are
            relative positions among the comparison markets, not
            percentages of fans or percentage growth.
            '''
        )

    # --------------------------------------------------------
    # PREPARE PHYSICAL ENGAGEMENT DATA
    # --------------------------------------------------------

    physical_display = physical_established.copy()

    physical_display["Team"] = (
        physical_display["team_id"]
        .map(TEAM_NAMES)
        .fillna(physical_display["team_id"])
    )

    physical_display = physical_display.sort_values(
        "physical_engagement_score",
        ascending=False,
    )

    # --------------------------------------------------------
    # OVERALL PHYSICAL ENGAGEMENT RANKING
    # --------------------------------------------------------

    fig = px.bar(
        physical_display,
        x="physical_engagement_score",
        y="Team",
        orientation="h",
        text="physical_engagement_score",
        labels={
            "physical_engagement_score":
                "Physical Engagement Score",
            "Team": "",
        },
        title="Physical Engagement Score",
    )

    fig.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside",
    )

    fig.update_layout(
        height=550,
        yaxis={
            "categoryorder": "array",
            "categoryarray":
                physical_display["Team"][::-1],
        },
        showlegend=False,
        margin=dict(l=20, r=60, t=60, b=20),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    # --------------------------------------------------------
    # TEAM-LEVEL PHYSICAL ENGAGEMENT COMPONENT COMPARISON
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Team-level physical engagement components'
        '</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Raw measurements show the underlying attendance and "
        "growth values. Percentile columns show each team's "
        "relative standing among the 12 established markets."
    )

    physical_table = physical_display[
        [
            "Team",
            "avg_attendance",
            "avg_capacity_utilization",
            "attendance_growth",
            "capacity_utilization_growth",
            "avg_attendance_percentile",
            "avg_capacity_utilization_percentile",
            "attendance_growth_percentile",
            "capacity_utilization_growth_percentile",
            "physical_engagement_score",
        ]
    ].copy()

    physical_table = physical_table.rename(
        columns={
            "avg_attendance": "Average attendance",
            "avg_capacity_utilization":
                "Average capacity utilization",
            "attendance_growth": "Attendance growth",
            "capacity_utilization_growth":
                "Capacity utilization growth",
            "avg_attendance_percentile":
                "Attendance percentile",
            "avg_capacity_utilization_percentile":
                "Utilization percentile",
            "attendance_growth_percentile":
                "Attendance growth percentile",
            "capacity_utilization_growth_percentile":
                "Utilization growth percentile",
            "physical_engagement_score":
                "Final Physical Score",
        }
    )

    # Format raw values for readability.
    physical_table["Average attendance"] = (
        physical_table["Average attendance"].round(0)
    )

    percentage_columns = [
        "Average capacity utilization",
        "Attendance growth",
        "Capacity utilization growth",
    ]

    for column in percentage_columns:
        physical_table[column] = (
            physical_table[column] * 100
        ).round(1).astype(str) + "%"

    percentile_columns = [
        "Attendance percentile",
        "Utilization percentile",
        "Attendance growth percentile",
        "Utilization growth percentile",
        "Final Physical Score",
    ]

    physical_table[percentile_columns] = (
        physical_table[percentile_columns].round(1)
    )

    st.dataframe(
        physical_table,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # DALLAS PHYSICAL ENGAGEMENT COMPONENTS
    # --------------------------------------------------------


    dallas_physical = physical_established[
        physical_established["team_id"] == "DAL"
    ]

    if not dallas_physical.empty:

        row = dallas_physical.iloc[0]

        component_data = pd.DataFrame({
            "Component": [
                "Average attendance",
                "Capacity utilization",
                "Attendance growth",
                "Utilization growth",
            ],
            "Percentile": [
                row["avg_attendance_percentile"],
                row["avg_capacity_utilization_percentile"],
                row["attendance_growth_percentile"],
                row["capacity_utilization_growth_percentile"],
            ],
        })

        fig = px.bar(
            component_data,
            x="Component",
            y="Percentile",
            text="Percentile",
            labels={
                "Percentile":
                    "Percentile among established markets",
            },
            title="Dallas physical engagement components",
        )

        fig.update_traces(
            texttemplate="%{text:.1f}",
            textposition="outside",
        )

        fig.update_yaxes(
            range=[0, 100],
            ticksuffix="%",
        )

        fig.update_layout(
            height=450,
            showlegend=False,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        dallas_rank = (
            physical_display["physical_engagement_score"]
            .rank(method="min", ascending=False)
        )

        dallas_rank_value = dallas_rank[
            physical_display["team_id"] == "DAL"
        ].iloc[0]

        st.success(
            f"Dallas ranks #{int(dallas_rank_value)} out of "
            f"{len(physical_display)} established markets in "
            "physical engagement. The component chart shows "
            "which areas contribute most and least to its score."
        )

    with st.expander("Assumptions & Limitations"):
        st.markdown("""
        - Attendance and capacity utilization are used as proxies for in-person fan engagement.
        - Average attendance and utilization are calculated from the available season-level data.
        - Growth compares the 2025–2026 recent period with the 2023–2024 baseline period.
        - The score gives equal weight to four percentile-ranked components: average attendance, average capacity utilization, attendance growth, and capacity utilization growth.
        - Percentile scores reflect relative performance among the teams included, not an absolute measure of engagement.
        - Differences in arena size, scheduling, team performance, and reporting practices may affect comparisons.
        """)

# ============================================================
# PAGE 3 — DIGITAL ENGAGEMENT
# ============================================================

elif page == "Digital Engagement":
    

    st.markdown(
        '<div class="section-title">'
        'Local digital engagement'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'This page explores the Local Digital Engagement Score, which evaluates the local interest each team generates on Google Trends. The metric combines longitudinal '
        'growth, persistence, and recent momentum.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.expander(" **What LDES measures and how to read its components** "):
        st.markdown(
            '''
            LDES is a **relative 0–100 index** built from local Google Trends
            search-interest patterns. It is intended to capture whether
            interest in a franchise is growing, recurring over time, and
            strengthening recently.

            - **Growth (40%):** recent-period average versus the historical
              baseline, calculated on a log scale.
            - **Persistence (40%):** share of valid recent three-month
              rolling windows whose average is above the historical mean.
            - **Recent momentum (20%):** recent average compared with the
              2023–2024 momentum baseline.

            Each component is converted to a percentile rank among the
            established markets before weighting. The historical baseline
            is 2021–2024; the recent period begins in 2025 and runs through
            the latest available month. An incomplete year is year-to-date,
            not a full-year observation.

            The component chart shows **percentile ranks**, not raw search
            volume or percentage growth. A 90th-percentile value means the
            component ranks above roughly 90% of the comparison group; it
            does not mean search interest rose by 90%.
            '''
        )

    digital_display = digital_established.copy()

    digital_display["Team"] = digital_display[
        "team_id"
    ].map(TEAM_NAMES)

    digital_display = digital_display.sort_values(
        "ldes",
        ascending=False,
    )

    fig = px.bar(
        digital_display,
        x="ldes",
        y="Team",
        orientation="h",
        text="ldes",
        labels={
            "ldes": "Local Digital Engagement Score",
            "Team": "",
        },
        title="Local Digital Engagement Score",
    )

    fig.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside",
    )

    fig.update_layout(
        height=550,
        yaxis={
            "categoryorder": "array",
            "categoryarray":
                digital_display["Team"][::-1],
        },
        showlegend=False,
        margin=dict(l=20, r=60, t=60, b=20),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    dallas_digital = digital_established[
        digital_established["team_id"] == "DAL"
    ]

    if not dallas_digital.empty:

        row = dallas_digital.iloc[0]

        component_data = pd.DataFrame({
            "Component": [
                "Growth",
                "Persistence",
                "Momentum",
            ],
            "Percentile": [
                row["growth_percentile"],
                row["persistence_percentile"],
                row["momentum_percentile"],
            ],
        })

        fig = px.bar(
            component_data,
            x="Component",
            y="Percentile",
            text="Percentile",
            labels={
                "Percentile":
                    "Percentile among established markets",
            },
            title="Dallas digital engagement components",
        )

        fig.update_traces(
            texttemplate="%{text:.1f}",
            textposition="outside",
        )

        fig.update_yaxes(
            range=[0, 100],
            ticksuffix="%",
        )

        fig.update_layout(
            height=450,
            showlegend=False,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        st.success(
            "Dallas ranks highly across all three digital "
            "dimensions: growth, persistence, and recent momentum. "
            "Its #2 LDES is therefore not driven by a single "
            "temporary spike."
        )

    # --------------------------------------------------------
    # TEAM-LEVEL LDES COMPONENT COMPARISON
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Team-level digital engagement components'
        '</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Each component is shown as a percentile rank among the "
        "12 established markets. LDES is the final weighted score."
    )

    component_table = digital_display[
        [
            "Team",
            "growth_percentile",
            "persistence_percentile",
            "momentum_percentile",
            "ldes",
        ]
    ].copy()

    component_table = component_table.rename(
        columns={
            "Team": "Team",
            "growth_percentile": "Growth percentile",
            "persistence_percentile": "Persistence percentile",
            "momentum_percentile": "Momentum percentile",
            "ldes": "Final LDES",
        }
    )

    component_table = component_table.round(1)

    st.dataframe(
        component_table,
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Assumptions & Limitations"):
        st.markdown("""
        - Search interest is normalized within each team's local media market, so scores should not be interpreted as directly comparable search volumes across DMAs.
        - Search terms are selected to represent franchise-specific interest, but may not capture every way fans engage with a team.
        - Recent-year data may cover only part of the year.
        - Search activity does not necessarily translate into attendance, merchandise purchases, or viewership.
        """)
# ============================================================
# PAGE 4 — ENGAGEMENT & PERFORMANCE
# ============================================================

elif page == "Engagement & Performance":

    st.markdown(
        '<div class="section-title">'
        'Engagement and team performance'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'This page explores if there is a relationship between fan engagement and team performance. '
        'You can select various engagement & team performance metric pairings and see how they correlate with each other.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.expander("How to interpret the correlation statistics"):
        st.markdown(
            '''
            **Pearson r** measures the direction and strength of a linear
            relationship. It ranges from -1 to +1.
            
            In plain English: Pearson asks, "When one variable increases, 
            does the other tend to increase or decrease by a relatively consistent amount?"

            **Spearman r** measures the direction and strength of a
            rank-based monotonic relationship. It also ranges from -1 to +1.

            In plain English: Spearman asks, "Do teams that rank higher in one 
            category generally rank higher in the other?"

            **Sample size (n)** is the number of team-level observations.
            **p-value** measures how surprising a result at least this
            extreme would be under a null hypothesis of no association,
            given the test assumptions. It is not proof of causation.

            These are market-level correlations, not individual-fan
            behavior. With only 12 established markets, results are
            exploratory and can be sensitive to individual teams.
            '''
        )

    # --------------------------------------------------------
    # Relationship selector
    # --------------------------------------------------------

    if "category" in performance.columns:

        digital_results = performance[
            performance["category"] == "Digital"
        ].copy()

    else:

        digital_results = pd.DataFrame()

    if not digital_results.empty:

        digital_results["Relationship"] = (
            digital_results["engagement_measure"]
            + " → "
            + digital_results["performance_measure"]
        )

        selected_relationship = st.selectbox(
            "Select a relationship",
            digital_results["Relationship"].tolist(),
        )

        selected = digital_results[
            digital_results["Relationship"]
            == selected_relationship
        ].iloc[0]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Pearson correlation",
                f"{selected['pearson_r']:.3f}",
            )

        with col2:
            st.metric(
                "Spearman correlation",
                f"{selected['spearman_r']:.3f}",
            )

        with col3:
            st.metric(
                "Sample size",
                int(selected["n"]),
            )

        st.info(
            "These correlations describe association, not "
            "causation. Digital engagement is measured at the "
            "team level, while performance is aggregated across "
            "the same longitudinal period."
        )

        st.caption(
            "Read the correlation alongside its sample size and p-value. "
            "A larger absolute correlation does not by itself establish "
            "a reliable or causal effect."
        )

    # --------------------------------------------------------
    # Attendance growth vs digital growth
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Attendance growth and digital growth'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'The strongest relationship identified in the analysis.'
        '</div>',
        unsafe_allow_html=True,
    )

    cross_file = PROJECT_ROOT / "outputs" / "tables" / (
        "performance_relationships_cross_engagement.csv"
    )

    if cross_file.exists():

        cross = pd.read_csv(cross_file)

        growth_row = cross[
            (
                cross["engagement_measure"]
                == "Attendance Growth"
            )
            &
            (
                cross["performance_measure"]
                == "Digital Growth"
            )
        ]

        if not growth_row.empty:

            growth_row = growth_row.iloc[0]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Pearson r",
                    f"{growth_row['pearson_r']:.3f}",
                )

            with col2:
                st.metric(
                    "Spearman r",
                    f"{growth_row['spearman_r']:.3f}",
                )

            with col3:
                st.metric(
                    "p-value",
                    f"{growth_row['pearson_p']:.3f}",
                )

            st.success(
                "Attendance growth and digital growth show a "
                "positive association in this 12-market sample. "
                "This observational relationship does not establish "
                "that growth in one measure causes growth in the other."
            )

            st.caption(
                "Pearson r summarizes the linear association; Spearman r "
                "summarizes the rank-based association. The displayed "
                "p-value is for the Pearson correlation."
            )

    # --------------------------------------------------------
    # Dallas performance
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Dallas performance context'
        '</div>',
        unsafe_allow_html=True,
    )

    if not dallas_performance.empty:

        perf = dallas_performance.copy()

        metrics = {}

        for _, row in perf.iterrows():
            metrics[row["metric"]] = row["value"]

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "LDES",
                f"{metrics.get('LDES', np.nan):.1f}",
            )

        with col2:
            st.metric(
                "Average win %",
                format_percent(
                    metrics.get(
                        "Average Win Percentage",
                        np.nan,
                    )
                ),
            )

        with col3:
            st.metric(
                "Playoff rate",
                format_percent(
                    metrics.get(
                        "Playoff Rate",
                        np.nan,
                    )
                ),
            )

        with col4:
            st.metric(
                "Digital growth",
                f"{metrics.get('Digital Growth', np.nan):.2f}",
            )

    st.markdown(
        '<div class="insight-box">'
        '<div class="insight-title">'
        'Key interpretation'
        '</div>'
        'The analysis does not show a strong relationship between '
        'digital engagement and winning. Instead, the strongest '
        'relationship appears between growth in physical attendance '
        'and growth in digital engagement. Dallas therefore provides '
        'an interesting case of strong digital engagement despite '
        'relatively modest on-court performance.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.expander("Assumptions & Limitations"):
        st.markdown("""
        - Correlations describe associations, not causal relationships.
        - The analysis includes a relatively small number of established WNBA markets, limiting statistical power.
        - Team performance is represented by the selected win percentage and playoff measures, which do not capture every factor affecting fan engagement.
        - Attendance and digital engagement may respond to external factors such as marketing, star players, local media coverage, and schedule changes.
        - Results should be interpreted as exploratory rather than proof that one type of engagement causes another.
        """)

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "WNBA Market Penetration | Public-data portfolio analysis | "
    "Established-market benchmark"
)