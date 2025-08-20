# 🥇 Gold Layer — Business-Ready Metrics & COVID Impact

**Goal:** ship BI-ready tables that quantify FX-adjusted import costs, trends, and COVID-period impacts.
**Inputs:** `fx_impact.silver_monthly_fact` (month × HS-2 with USD/EUR + FX pivots)

**Delivered notebooks**

* `04_fx_adjusted_cost_volatility.ipynb` – core Gold metrics (MoM/YoY, rolling vol, shares, totals)
* `05_pre_post_covid_analysis.ipynb` – Pre/During/Post COVID KPIs and “top movers”

Works on **Databricks CE** (managed Delta only; no `/FileStore`). Export CSV from the **grid Download** button.

---

## 📦 Output Tables (managed Delta)

### Core metrics

| Table                            | Grain        | What it’s for                                                                                                     |
| -------------------------------- | ------------ | ----------------------------------------------------------------------------------------------------------------- |
| `fx_impact.gold_monthly_metrics` | month × HS-2 | All-in feature table for visuals: EUR/USD, MoM/YoY, rolling vol (3M/6M), contribution share, FX MoM, COVID labels |
| `fx_impact.gold_monthly_totals`  | month        | Cards/lines of total EUR/USD per month; display USD/EUR level                                                     |

### COVID analysis

| Table                                     | Grain | What it’s for                                        |
| ----------------------------------------- | ----- | ---------------------------------------------------- |
| `fx_impact.gold_period_summary`           | 1 row | Δ During vs Pre, Δ Post vs Pre (overall)             |
| `fx_impact.gold_covid_period_kpis_total`  | 1 row | Period averages + month counts (sanity for cards)    |
| `fx_impact.gold_covid_period_kpis_by_cmd` | HS-2  | Per-commodity Pre/During/Post averages + Δ (abs & %) |
| `fx_impact.gold_covid_top_movers`         | HS-2  | Ranked movers up/down (abs and %) for Post vs Pre    |
| `fx_impact.dim_months`                    | month | Gap-free month dimension used to stabilize windows   |

---

## 🧮 Metric Definitions (truth set)

* **EUR conversion** (ECB quotes target per 1 EUR):
  `import_eur = import_usd / USD_per_EUR`
* **MoM % / YoY % (EUR)**:
  `eur_mom_pct = (EUR_t − EUR_{t−1}) / EUR_{t−1}` (NULL if denom ≤ 0)
  `eur_yoy_pct = (EUR_t − EUR_{t−12}) / EUR_{t−12}`
* **Rolling volatility (levels)** over last N rows:
  `eur_vol_3m`, `eur_vol_6m`, `fx_vol_3m`, `fx_vol_6m` = `STDDEV_POP(...)` with 3/6-month windows

  > Prefer return-vol? Swap to `ln(EUR_t/EUR_{t−1})` then std-dev on that.
* **Contribution share**:
  `share_of_total_eur = import_eur / SUM(import_eur) OVER (PARTITION BY month)`
* **COVID periods**:
  Pre (< 2020-01-01), During (≤ 2021-12-31), Post (≥ 2022-01-01).
  05-notebook supports toggles for including/excluding 2025 YTD or fixing Post to 2022–2024.

---

## 📚 Schemas

**`fx_impact.gold_monthly_metrics`** (month × HS-2)

* Keys: `month` DATE, `cmdCode` STRING
* Fields: `cmdDesc`, `covid_period`, `import_usd`, `import_eur`,
  `USD_per_EUR`, `JPY_per_EUR`, `CNY_per_EUR`,
  `usd_obs_days`, `usd_days_total`, `usd_null_share`,
  `total_eur_month`, `share_of_total_eur`,
  `eur_mom_pct`, `eur_yoy_pct`, `fx_mom_pct`,
  `eur_vol_3m`, `eur_vol_6m`, `fx_vol_3m`, `fx_vol_6m`.

**`fx_impact.gold_monthly_totals`** (month)

* `month`, `total_import_usd`, `total_import_eur`, `avg_usd_per_eur`.

**`fx_impact.gold_period_summary`** (1 row)

* `avg_eur_pre`, `avg_eur_during`, `avg_eur_post`,
  `delta_during_vs_pre_pct`, `delta_post_vs_pre_pct`.

**`fx_impact.gold_covid_period_kpis_total`** (1 row)

* `pre_eur`, `during_eur`, `post_eur`, `pre_m`, `during_m`, `post_m`, deltas vs Pre.

**`fx_impact.gold_covid_period_kpis_by_cmd`** (HS-2)

* `cmdCode`, `cmdDesc`, `pre_eur`, `during_eur`, `post_eur`,
  `abs_change_*`, `pct_change_*` (During vs Pre, Post vs Pre).

**`fx_impact.gold_covid_top_movers`** (HS-2)

* Above deltas + rank columns for Post vs Pre (abs\_up/down, pct\_up/down).

**`fx_impact.dim_months`**

* `month` DATE (gap-free sequence used to fill grids/warm windows).

---

## ✅ QA Checklist (run after builds)

```sql
-- Totals reconcile: sum(metrics.EUR) equals totals.EUR
WITH m AS (
  SELECT month, SUM(import_eur) sum_eur
  FROM fx_impact.gold_monthly_metrics GROUP BY month
)
SELECT t.month, t.total_import_eur, m.sum_eur,
       (t.total_import_eur - m.sum_eur) AS diff
FROM fx_impact.gold_monthly_totals t
JOIN m USING (month)
WHERE ABS(t.total_import_eur - m.sum_eur) > 1e-6;

-- Shares ~ 1 per month
SELECT month, SUM(share_of_total_eur) AS s
FROM fx_impact.gold_monthly_metrics
GROUP BY month
HAVING ABS(s - 1.0) > 1e-6;

-- Window warm-up NULLs are expected early on
SELECT month, cmdCode, eur_vol_3m, eur_vol_6m
FROM fx_impact.gold_monthly_metrics
ORDER BY month, cmdCode
LIMIT 20;

-- COVID period tables exist and look sane
SELECT * FROM fx_impact.gold_period_summary;
SELECT COUNT(*) FROM fx_impact.gold_covid_period_kpis_by_cmd;
```

---

## 🚢 Power BI Wiring (recommended)

* **Fact table:** `gold_monthly_metrics`
* **Date table:** your `Date` dimension (`Date[Date]` → `metrics[month]`)
* **Totals table (optional):** `gold_monthly_totals` for card/line speed
* **COVID tables (optional):** `gold_covid_*` for KPI bars/cards

**Starter DAX**

```DAX
Total EUR = SUM ( 'gold_monthly_metrics'[import_eur] )
Total USD = SUM ( 'gold_monthly_metrics'[import_usd] )

EUR MoM % =
VAR prev = CALCULATE ( [Total EUR], DATEADD ( 'Date'[Date], -1, MONTH ) )
RETURN DIVIDE ( [Total EUR] - prev, prev )

FX Avg (USD/EUR) = AVERAGE ( 'gold_monthly_metrics'[USD_per_EUR] )
EUR Vol 3M = AVERAGE ( 'gold_monthly_metrics'[eur_vol_3m] )
FX Vol 3M  = AVERAGE ( 'gold_monthly_metrics'[fx_vol_3m] )
```

**Visuals**

* **Overview:** line `total_import_eur` (from totals), cards for `FX Avg`, `EUR MoM %`, Δ Post vs Pre (from `gold_period_summary`)
* **FX vs Cost:** combo (column `avg_usd_per_eur`, line `total_import_eur`)
* **Commodity:** stacked area `import_eur` by `cmdDesc`; bars for `share_of_total_eur`
* **COVID Impact:** bars of `abs_change_post_vs_pre` / `pct_change_post_vs_pre` (Top N)

---

## 🔁 Re-run Policy

* Gold notebooks use **CREATE OR REPLACE TABLE**. Re-run anytime (after Bronze/Silver refresh) to extend to new months.
* If you toggle 2025 YTD inclusion or fix Post to 2022–2024, re-run `05_pre_post_covid_analysis.ipynb`.

---

## 🔧 Optional Enhancements

* **FX attribution (MoM):** split EUR change into FX vs “volume” effect

  ```
  fx_effect_mom      = import_usd_{t-1} * (1/USD_per_EUR_t - 1/USD_per_EUR_{t-1})
  volume_effect_mom  = import_eur_t - import_eur_{t-1} - fx_effect_mom
  ```

  Add as columns to `gold_monthly_metrics` for richer storytelling.
* Extend granularity (HS-4/HS-6) or add partner-country slices.
* Switch volatility to **return-based** if you want finance-grade narratives.

---

## 🧰 Troubleshooting

* **No rows in Post-COVID tables?** You filtered out 2025 or fixed Post to 2022–2024—verify flags in `05_pre_post_covid_analysis`.
* **Shares ≠ 1:** indicates missing commodities in a month; check Silver coverage.
* **MoM/YoY NULLs:** expected when prior month/year is zero or missing.

---

**Owner:** Gold layer notebooks (`04_…`, `05_…`)
**Last updated:** *20/08/2025*


