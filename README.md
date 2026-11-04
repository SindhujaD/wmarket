# WNBA Market Penetration Analysis

## Project Overview

This project examines how effectively WNBA teams build and sustain fan engagement within their markets, with a particular focus on the Dallas Wings.
Rather than evaluating market success through attendance alone, the analysis considers both **physical engagement** (in-person attendance and arena utilization) and **digital engagement** (local Google search interest).
The goal is to compare how teams perform across these dimensions, identify differences between physical and digital engagement, and explore how engagement relates to on-court performance.
The analysis focuses on 12 established WNBA markets. Expansion franchises are excluded from the core longitudinal comparisons because they do not have the same historical data availability.

## Definitions

**Physical engagement:** A measure of in-person fan activity based on average attendance, arena capacity utilization, and growth in both metrics.

**Digital engagement:** A measure of local online interest based on Google Trends search activity within each team's designated local media market.

**Local Digital Engagement Score (LDES):** A composite score combining digital search growth, persistence, and recent momentum. The score is percentile-based and ranges from 0 to 100.

**Physical Engagement Score:** A composite score combining average attendance, average capacity utilization, attendance growth, and capacity utilization growth. Each component contributes equally to the final score.

**Capacity utilization:** Attendance relative to arena capacity. This helps account for differences in venue size when comparing teams.

**Established markets:** The 12 teams included in the core longitudinal analysis: Atlanta Dream, Chicago Sky, Connecticut Sun, Dallas Wings, Indiana Fever, Las Vegas Aces, Los Angeles Sparks, Minnesota Lynx, New York Liberty, Phoenix Mercury, Seattle Storm, and Washington Mystics.

## How the Local Digital Engagement Score Was Calculated

The LDES combines three components to evaluate different dimensions of local search interest.

| Component | Weight | What it measures |
|---|---:|---|
| Search growth | 40% | The change in average search interest between the historical and recent periods. |
| Persistence | 40% | The proportion of valid recent three-month rolling windows in which search interest exceeds the historical average. |
| Recent momentum | 20% | The change in search interest compared with a more recent baseline period. |

The resulting LDES is a relative score from 0 to 100. A higher score indicates stronger digital engagement compared with the other markets in the analysis.

## How the Physical Engagement Score Was Calculated

The Physical Engagement Score combines four measures of in-person fan engagement.

| Component | Weight | What it measures |
|---|---:|---|
| Average attendance | 25% | Average number of attendees per game. |
| Average capacity utilization | 25% | Average attendance relative to arena capacity. |
| Attendance growth | 25% | Change in attendance between the baseline and recent periods. |
| Capacity utilization growth | 25% | Change in arena utilization between the baseline and recent periods. |

Each component is converted into a percentile relative to the other established markets. The four percentile scores are averaged with equal weighting to produce the final Physical Engagement Score.
The score ranges from 0 to 100, with higher values indicating stronger relative physical engagement.

## Engagement & Performance Analysis

The project also explores the relationship between fan engagement and on-court performance.

The analysis considers:

- Physical engagement relative to win percentage and playoff performance.
- Digital engagement relative to win percentage and playoff performance.
- The relationship between growth in physical engagement and growth in digital engagement.
- Differences between teams with relatively high physical engagement and teams with relatively high digital engagement.

Pearson and Spearman correlation coefficients are used to evaluate relationships between selected metrics.

**Pearson correlation** measures the strength and direction of a linear relationship between two variables.

**Spearman correlation** measures the strength and direction of a relationship based on the relative rankings of the observations.

These analyses are exploratory and are not intended to establish causal relationships.

## Assumptions

- The 12 established markets are used as the primary comparison group to provide a more consistent historical benchmark.
- Google Trends search interest is treated as a proxy for digital fan engagement.
- Local media market (DMA) search interest is used to approximate regional interest in each franchise.
- Attendance and capacity utilization are treated as proxies for physical fan engagement.
- The Physical Engagement Score gives equal weight to its four components.
- The LDES uses weights of 40% for search growth, 40% for persistence, and 20% for recent momentum.
- Component percentiles are calculated relative to the established markets included in the analysis.
- The recent digital period uses all available data through the latest collection date.
- The recent physical period uses the available 2025–2026 season data.

## Limitations

- Google Trends provides normalized search interest rather than absolute search volume. Values should not be interpreted as the number of people searching for a team.
- Google Trends data is normalized within each local DMA. As a result, local scores are useful for evaluating changes over time within a market but are not direct comparisons of absolute search volume across markets.
- Search activity does not necessarily translate into ticket purchases, merchandise sales, television viewership, or actual fandom.
- Search terms may not capture every way fans refer to or search for a franchise.
- DMA boundaries may not perfectly represent a team's actual fanbase or geographic reach.
- Partial-year data can affect comparisons between recent and historical periods.
- Arena capacity and attendance reporting may differ across teams, seasons, and venues.
- Capacity utilization helps account for differences in arena size but does not account for ticket prices, sellouts, seat availability, or differences in the number of home games.
- Growth rates can be sensitive to unusually high or low baseline values.
- Percentile-based scores are relative to the comparison group. A team's score can change if the comparison group changes, even if its underlying metrics remain constant.
- The weighting systems are methodological assumptions rather than empirically validated measures of fan engagement.
- The analysis includes a relatively small number of established markets, limiting the statistical power of correlation analyses.
- Correlation does not imply causation. Team performance, marketing, star players, media exposure, scheduling, and other factors may influence engagement.

## Data Sources

**Google Trends:**  
https://trends.google.com/trends/

**WNBA Official Website:**  
https://www.wnba.com/

**Basketball Reference – WNBA:**  
https://www.basketball-reference.com/wnba/

**WNBA Stats:**  
https://stats.wnba.com/

*Note: The specific attendance, arena-capacity, and performance datasets were assembled for this project. The sources above are starting points for the underlying league and team information. Consult the project's raw data files for the exact records and source documentation used in each dataset.*