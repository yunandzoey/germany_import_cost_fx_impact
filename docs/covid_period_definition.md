# COVID period definitions used in this analysis

We split the timeline into three buckets aligned to common EU timelines and supply-chain impact:

- **Pre-COVID:** `2018-01-01` → `2020-02-29`
- **During COVID:** `2020-03-01` → `2021-12-31`  
  (first EU lockdowns in Mar-2020; we keep 2021 as part of the disrupted period)
- **Post-COVID:** `2022-01-01` → *latest complete month in data*

Implementation details:
- The pipeline computes `last_complete_month = last_day(add_months(current_date(), -1))`.
- Any data after that date is not used for “latest” KPIs to avoid partial months.
- Each row in `silver_monthly_fact` gets a `covid_period` label via these ranges, which flows to Gold tables and Power BI.

**Why these cut-offs?**
They line up with observable jumps in FX volatility and Germany’s import patterns, and keep each bucket long enough for stable monthly averages.
