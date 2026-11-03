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
        color: #666;
        margin-bottom: 2rem;
    }

    .section-title {
        font-size: 1.7rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 0.5rem;
    }

    .section-description {
        color: #666;
        margin-bottom: 1rem;
    }

    .insight-box {
        padding: 1.2rem;
        border-radius: 10px;
        background-color: #f5f5f5;
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
    'How effectively are WNBA teams building and sustaining '
    'fan engagement in their markets?'
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
        "Physical vs Digital",
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

else:

    dallas_rank = np.nan
    dallas_market_score = np.nan
    dallas_physical_score = np.nan
    dallas_ldes = np.nan


# ============================================================
# PAGE 1 — MARKET OVERVIEW
# ============================================================

if page == "Market Overview":

    st.markdown(
        '<div class="section-title">'
        'Dallas at a glance'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'Dallas compared with the 12 established WNBA markets '
        'in the market engagement benchmark.'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Overall market rank",
            (
                f"#{int(dallas_rank)} of 12"
                if not pd.isna(dallas_rank)
                else "—"
            ),
        )

    with col2:
        st.metric(
            "Market engagement",
            format_score(dallas_market_score),
        )

    with col3:
        st.metric(
            "Physical engagement",
            format_score(dallas_physical_score),
        )

    with col4:
        st.metric(
            "Digital engagement",
            format_score(dallas_ldes),
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

    st.markdown(
        '<div class="insight-box">'
        '<div class="insight-title">'
        'Dallas takeaway'
        '</div>'
        'Dallas ranks 4th among the 12 established markets. '
        'Its overall position is driven by a particularly strong '
        'digital engagement profile, while physical engagement '
        'remains comparatively lower.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">'
        'Dallas compared with the benchmark'
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


# ============================================================
# PAGE 2 — PHYSICAL VS DIGITAL
# ============================================================

elif page == "Physical vs Digital":

    st.markdown(
        '<div class="section-title">'
        'Physical vs digital engagement'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'The central market-penetration question: are markets '
        'building engagement primarily through physical attendance, '
        'digital interest, or both?'
        '</div>',
        unsafe_allow_html=True,
    )

    plot_data = market.copy()

    plot_data["Team"] = plot_data["team_id"].map(
        TEAM_NAMES
    )

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

    st.markdown(
        '<div class="section-title">'
        'Dallas market profile'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    dallas_row = market[
        market["team_id"] == "DAL"
    ]

    if not dallas_row.empty:

        dallas_row = dallas_row.iloc[0]

        physical = dallas_row[
            "physical_engagement_score"
        ]

        digital_score = dallas_row["ldes"]

        gap = dallas_row.get(
            "digital_minus_physical",
            digital_score - physical,
        )

        quadrant = dallas_row.get(
            "market_quadrant",
            "—",
        )

    else:

        physical = np.nan
        digital_score = np.nan
        gap = np.nan
        quadrant = "—"

    with col1:
        st.metric(
            "Physical score",
            format_score(physical),
        )

    with col2:
        st.metric(
            "Digital score",
            format_score(digital_score),
        )

    with col3:
        st.metric(
            "Digital − physical gap",
            format_score(gap),
        )

    st.info(
        f"Dallas falls into the **{quadrant}** quadrant. "
        "This means its digital engagement is substantially "
        "stronger than its physical engagement relative to "
        "the established-market benchmark."
    )

    st.markdown(
        '<div class="section-title">'
        'What does the gap mean?'
        '</div>',
        unsafe_allow_html=True,
    )

    st.write(
        "Dallas's engagement profile is unusual because its "
        "digital footprint is considerably stronger than its "
        "physical attendance profile. This suggests that the "
        "market has an audience that is engaging with the Wings "
        "digitally even though that engagement has not translated "
        "into equally strong physical attendance."
    )


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
        'The Local Digital Engagement Score combines longitudinal '
        'growth, persistence, and recent momentum.'
        '</div>',
        unsafe_allow_html=True,
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

    st.markdown(
        '<div class="section-title">'
        'What drives Dallas digital engagement?'
        '</div>',
        unsafe_allow_html=True,
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
        'Are stronger fan-engagement markets also the markets '
        'with stronger on-court performance?'
        '</div>',
        unsafe_allow_html=True,
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
                "strong positive association across the 12 "
                "established markets."
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

        col1, col2, col3, col4 = st.columns(4)

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


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "WNBA Market Penetration | Public-data portfolio analysis | "
    "Established-market benchmark"
)