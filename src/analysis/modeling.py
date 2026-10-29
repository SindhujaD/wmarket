import statsmodels.formula.api as smf

model = smf.ols(
    """
    fan_penetration_index
    ~ market_opportunity_index
    + win_pct
    + playoff_appearance
    """,
    data=df
).fit()

print(model.summary())