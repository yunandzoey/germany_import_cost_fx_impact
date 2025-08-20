# 🥈 Silver Layer – Monthly Modeling & Joins

**Goal:** turn raw Bronze data into **clean, analysis-ready monthly tables** with FX pivots and EUR-converted import costs.

**Scope:**

* ECB FX → monthly averages, pivoted to `USD_per_EUR`, `JPY_per_EUR`, `CNY_per_EUR`
* Comtrade → monthly import totals (USD) by HS-2 (`27, 39, 72, 84, 85`)
* Join on month and compute **EUR**: `import_eur = import_usd / USD_per_EUR`
* Add **quality fields** (obs days, null share) and **COVID period** labels

Works on **Databricks CE** (managed Delta; no `/FileStore`).

---

## 📦 Outputs (managed Delta tables)

| Table                  | Name                               | Grain            | Key Columns                                                                                              |
| ---------------------- | ---------------------------------- | ---------------- | -------------------------------------------------------------------------------------------------------- |
| FX monthly (long)      | `fx_impact.silver_fx_monthly_long` | month × currency | `month`, `currency`, `fx_avg`, `obs_days`, `days_total`, `null_share`                                    |
| FX monthly (pivot)     | `fx_impact.silver_fx_monthly`      | month            | `month`, `USD_per_EUR`, `JPY_per_EUR`, `CNY_per_EUR`, `usd_obs_days`, `usd_days_total`, `usd_null_share` |
| Imports monthly (USD)  | `fx_impact.silver_imports_monthly` | month × HS-2     | `month`, `cmdCode`, `cmdDesc`, `import_usd`                                                              |
| **Monthly fact (EUR)** | `fx_impact.silver_monthly_fact`    | month × HS-2     | `month`, `cmdCode`, `cmdDesc`, `import_usd`, `import_eur`, FX pivots, quality fields, `covid_period`     |

**Timelines:**

* FX: **2018-01-01 → today** (monthly rollups)
* Comtrade: **2018–2025 (YTD)**; partial months for 2025 are expected

---

## 🔧 Build order (one-time + re-runs)

Create these in a notebook (we ship `03_clean_join_monthly_data.ipynb`):

1. `silver_fx_monthly_long` – monthly averages + quality fields
2. `silver_fx_monthly` – pivoted FX + USD quality columns
3. `silver_imports_monthly` – monthly import totals (USD) by HS-2
4. `silver_monthly_fact` – join + EUR conversion + period label

> All tables use **CREATE OR REPLACE TABLE** (idempotent). Re-running replaces the table atomically.

---

## 🧮 Core logic (truth you’ll reference later)

* **ECB series** is *target per 1 EUR*. For USD this is **USD\_per\_EUR**.
  → **EUR conversion:** `import_eur = import_usd / USD_per_EUR`
* **Monthly FX** via `AVG(fx_rate)` grouped by `date_trunc('month', date)`.
* **Quality**:

  * `obs_days` = number of days with an observation in that month
  * `days_total` = days in month
  * `null_share` = `1 - obs_days/days_total`
* **COVID labels** (adjust as needed):

  * `Pre-COVID` < 2020-01-01
  * `During COVID` ≤ 2021-12-31
  * `Post-COVID` otherwise

---

## ✅ Data Quality (Silver)

**FX monthly (long/pivot)**

* `obs_days` ≤ `days_total`
* `null_share` ∈ \[0, 1]; monitor spikes
* No missing `USD_per_EUR` for months used in Comtrade (join should cover all months where both exist)

**Imports monthly**

* `import_usd > 0`
* No duplicates on `(month, cmdCode)`

**Joined fact**

* No duplicates on `(month, cmdCode)`
* `fx_missing_flag` should be **0** for almost all rows; investigate if not

---

## 🧪 Smoke tests

```sql
-- Ranges & row counts
SELECT MIN(month) min_m, MAX(month) max_m, COUNT(*) rows FROM fx_impact.silver_fx_monthly;
SELECT MIN(month) min_m, MAX(month) max_m, COUNT(*) rows FROM fx_impact.silver_imports_monthly;
SELECT MIN(month) min_m, MAX(month) max_m, COUNT(*) rows FROM fx_impact.silver_monthly_fact;

-- Dupes check
SELECT month, cmdCode, COUNT(*) c
FROM fx_impact.silver_monthly_fact
GROUP BY month, cmdCode
HAVING COUNT(*) > 1;

-- FX availability in joined fact
SELECT SUM(CASE WHEN fx_missing_flag=1 THEN 1 ELSE 0 END) AS rows_fx_missing
FROM fx_impact.silver_monthly_fact;
```

---

## 🧱 Schemas

**`fx_impact.silver_fx_monthly_long`**

* `month` DATE
* `currency` STRING (`USD`,`JPY`,`CNY`)
* `fx_avg` DOUBLE
* `obs_days` INT, `days_total` INT, `null_share` DOUBLE

**`fx_impact.silver_fx_monthly`**

* `month` DATE
* `USD_per_EUR` DOUBLE, `JPY_per_EUR` DOUBLE, `CNY_per_EUR` DOUBLE
* `usd_obs_days` INT, `usd_days_total` INT, `usd_null_share` DOUBLE

**`fx_impact.silver_imports_monthly`**

* `month` DATE
* `cmdCode` STRING (HS-2), `cmdDesc` STRING
* `import_usd` DOUBLE

**`fx_impact.silver_monthly_fact`**

* `month` DATE, `covid_period` STRING
* `cmdCode` STRING, `cmdDesc` STRING
* `import_usd` DOUBLE, `import_eur` DOUBLE
* `USD_per_EUR` DOUBLE, `JPY_per_EUR` DOUBLE, `CNY_per_EUR` DOUBLE
* `usd_obs_days` INT, `usd_days_total` INT, `usd_null_share` DOUBLE
* `fx_missing_flag` INT (0/1)

---

## 🔁 Re-run & incrementals

* **Full refresh:** re-run the notebook; `CREATE OR REPLACE TABLE` overwrites atomically.
* **New months (e.g., 2025 updates):** just re-run; monthly logic is date-driven.
* If you only updated Comtrade for 2025 in Bronze, the Silver build will fold it in—no special handling needed.

---

## ⚡ Performance tips (optional)

* FX and HS-2 volumes are modest; default is fine.
* If you extend HS granularity (HS-4/HS-6) or add partners, consider **ZORDER** on `month`, `cmdCode` (if available in your workspace).
* Keep Bronze → Silver transformations column-pruned.

---

## 🚢 Power BI handoff (CE-friendly)

If you’re staying on CE, export a CSV from the grid:

```python
df = spark.sql("""
  SELECT month, cmdCode, cmdDesc, import_usd, import_eur,
         USD_per_EUR, JPY_per_EUR, CNY_per_EUR,
         usd_obs_days, usd_null_share, covid_period
  FROM fx_impact.silver_monthly_fact
  ORDER BY month, cmdCode
""")
display(df)  # Download → CSV
```

In a paid workspace, expose `silver_monthly_fact` via a **SQL Warehouse** and connect **Power BI** with the Databricks connector (DirectQuery or Import).

---

## 🔜 Next (Gold)

* Rolling **3M/6M volatility** for `import_eur` and `USD_per_EUR`
* **MoM% / YoY%** measures
* **Contribution** of each HS-2 to total EUR imports by month
* Publish `fx_impact.gold_monthly_metrics` as the BI-facing table

---

## Known gotchas

* If you changed Bronze FX `date` to TIMESTAMP by accident, re-run Bronze with `DATE` or cast in Silver before aggregating.
* If FX missing spikes for any month, check ECB holidays and consider ffill/backfill rules **before** averaging (not needed so far).
* Comtrade returns partial 2025 — visuals should respect partial-year logic (use YTD measures in Power BI if needed).

---

**Owner:** `03_clean_join_monthly_data.ipynb` (this layer)
**Last updated:** *20/08/2025*
