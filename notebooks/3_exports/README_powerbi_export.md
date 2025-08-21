# 📤 Power BI Export (Databricks CE)

**Goal:** get clean CSVs from your **Gold** tables for use in **Power BI**, without touching DBFS/FileStore or hardcoding paths.

Works on **Databricks Community Edition**. You’ll export via the **grid Download** button after `display(df)`.

---

## 🧱 Prereqs

* Gold notebooks have been run:

  * `fx_impact.gold_monthly_metrics`
  * `fx_impact.gold_monthly_totals`
  * `fx_impact.gold_period_summary`
  * `fx_impact.gold_covid_period_kpis_by_cmd` (from the COVID notebook)
* Cluster is **running** and the notebook is **attached**.

Recommended repo spots:

```
notebooks/
  3_exports/
    99_export_powerbi.ipynb
dashboard/
  exports/           # <- store downloaded CSVs here (local Git ignored)
  screenshots/       # <- place Power BI screenshots here
```

> 🔒 **Do not commit CSVs**. Add `dashboard/exports/` to `.gitignore`.

---

## 🚀 How to export

Open `notebooks/3_exports/99_export_powerbi.ipynb` and run the cells top-to-bottom.

### 1) (Optional) Only export **complete months**

In **Cell 1**, choose:

```python
FILTER_TO_COMPLETE_MONTHS = True  # recommended for clean MoM/YoY
```

This filters data to **last complete month** (e.g., excludes current partial month).

### 2) Sanity check Gold tables

**Cell 2** describes tables so you know they exist & are readable.

### 3) Export the main fact

**Cell 3**:

```python
df_metrics = spark.sql("""
  SELECT month, cmdCode,
       cmdDesc,            -- short (visuals)
       cmdDesc_long,       -- full (tooltips)
       covid_period,
       import_usd, import_eur,
       USD_per_EUR, JPY_per_EUR, CNY_per_EUR,
       share_of_total_eur, eur_mom_pct, eur_yoy_pct,
       eur_vol_3m, eur_vol_6m, fx_mom_pct, fx_vol_3m, fx_vol_6m
  FROM fx_impact.gold_monthly_metrics
  ORDER BY month, cmdCode
""")
display(df_metrics)  # ← Click Download → CSV
```

Save as **`gold_monthly_metrics.csv`**.

### 4) Export totals (nice for fast cards/lines)

**Cell 4**:

```python
display(
  spark.sql("""
    SELECT month, total_import_usd, total_import_eur, avg_usd_per_eur
    FROM fx_impact.gold_monthly_totals
    ORDER BY month
  """)
)
```

Save as **`gold_monthly_totals.csv`**.

### 5) Export COVID summary tables

**Cell 5**:

```python
display(spark.sql("SELECT * FROM fx_impact.gold_period_summary"))
```

Save as **`gold_period_summary.csv`**.

**Cell 6**:

```python
display(spark.sql("""
  SELECT cmdCode, 
         cmdDesc,            -- short (visuals)
         cmdDesc_long,       -- full (tooltips)
         pre_eur, during_eur, post_eur,
         abs_change_during_vs_pre, pct_change_during_vs_pre,
         abs_change_post_vs_pre,   pct_change_post_vs_pre
  FROM fx_impact.gold_covid_period_kpis_by_cmd
  ORDER BY abs_change_post_vs_pre DESC NULLS LAST
"""))
```

Save as **`gold_covid_period_kpis_by_cmd.csv`**.

> Want pre-ranked tables (Top movers up/down)? Add an extra export from `fx_impact.gold_covid_top_movers`.

### If your tenant blocks OneDrive/Lakehouse
Use **Create → Paste or manually enter data** in the Service:
1) Paste `gold_monthly_metrics.csv` (all rows) as table **metrics**.
2) In Model view, add a calculated **Date** column if `month` pasted as text:
   ```DAX
   month_date =
   VAR s = SELECTEDVALUE ( metrics[month] )
   RETURN DATE ( VALUE(LEFT(s,4)), VALUE(MID(s,6,2)), VALUE(RIGHT(s,2)) )

---

## 🧭 Naming & versioning

Use a date-stamped naming convention locally:

```
dashboard/exports/
  2025-08-20_gold_monthly_metrics.csv
  2025-08-20_gold_monthly_totals.csv
  2025-08-20_gold_period_summary.csv
  2025-08-20_gold_covid_period_kpis_by_cmd.csv
```

Keep a short `README` or `manifest.txt` in `dashboard/exports/` stating:

* Bronze/Silver/Gold notebooks commit SHA (optional)
* Export date
* Filter setting (`FILTER_TO_COMPLETE_MONTHS=True/False`)

---

## 🟡 Why we export via `display(df)` (not DBFS)

Your workspace has **Public DBFS root disabled**, so browsing/downloading by path (e.g., `/FileStore`) is blocked.
The **grid Download** button avoids that policy and keeps secrets out of your repo.

---

## 🖥️ Load into Power BI (Desktop)

1. **Get Data → Text/CSV**: load all exported CSVs.
2. **Power Query**:

   * Ensure `month` column type is **Date**.
   * Rename tables to: `metrics`, `totals`, `period_summary`, `covid_by_cmd`.
   * Close & Apply.
3. **Date table** (Modeling → New Table):

```DAX
Date = CALENDAR ( DATE(2018,1,1), DATE(2025,12,31) )
Date[Year] = YEAR ( 'Date'[Date] )
Date[MonthNum] = MONTH ( 'Date'[Date] )
Date[Month] = FORMAT ( 'Date'[Date], "YYYY-MM" )
```

* **Mark as Date table** → `Date[Date]`.
* Sort `Date[Month]` by `Date[MonthNum]`.

4. **Relationships**:

   * `Date[Date]` → `metrics[month]` (single direction)
   * Optional: `Date[Date]` → `totals[month]`

---

## 📊 Starter DAX (measures table)

Create a “Measures” table (Modeling → New Table → `Measures = { (blank) }`), then:

```DAX
Total EUR = SUM ( metrics[import_eur] )
Total USD = SUM ( metrics[import_usd] )

EUR MoM % =
VAR prev = CALCULATE ( [Total EUR], DATEADD ( 'Date'[Date], -1, MONTH ) )
RETURN DIVIDE ( [Total EUR] - prev, prev )

EUR YoY % =
VAR prev = CALCULATE ( [Total EUR], DATEADD ( 'Date'[Date], -12, MONTH ) )
RETURN DIVIDE ( [Total EUR] - prev, prev )

FX Avg (USD/EUR) = AVERAGE ( metrics[USD_per_EUR] )
EUR Vol 3M       = AVERAGE ( metrics[eur_vol_3m] )
FX Vol 3M        = AVERAGE ( metrics[fx_vol_3m] )

Share of Total EUR = AVERAGE ( metrics[share_of_total_eur] )

Total EUR YTD = TOTALYTD ( [Total EUR], 'Date'[Date] )  -- for 2025 partial year
```

---

## 🧩 Suggested pages

* **Overview**: line (totals `total_import_eur`), cards (FX Avg, EUR MoM %, YTD).
* **FX vs Costs**: combo (column = avg USD/EUR; line = total EUR).
* **Commodity**: stacked area `import_eur` by `cmdDesc`; bar Top N by `Share of Total EUR`.
* **COVID Impact**: bars from `covid_by_cmd` (abs/% Δ Post vs Pre); cards from `period_summary`.

---

## 🛠️ Troubleshooting

* **No Download button?** You’re not using `display(df)`. Make sure the last line of the cell is `display(df)` (or `display(spark.sql(...))`).
* **CSV shows month+time**: Power BI read it as DateTime—set type to **Date**.
* **MoM/YoY blank at edges**: expected where previous month/year is missing or zero.
* **Numbers look off for the current month**: you exported **partial month**. Re-export with `FILTER_TO_COMPLETE_MONTHS = True`.
* **Files too large?** You expanded to HS-4/HS-6. Use `TopN` exports or filter by commodity in the export query.

---

## 🔄 Upgrading later (paid workspace)

When you move off CE:

* Create a **SQL Warehouse**.
* Connect Power BI via **Databricks** connector (token auth).
* Keep the same visuals/measures; just repoint the data source to the Warehouse.

---
## Changelog

### 2025-08-21
- Adopted short HS labels in Gold: `cmdDesc` (short), `cmdDesc_long` (full).
- Power BI export now includes `cmdDesc_long` for tooltips.
- Added Service-only paste workflow (for tenants without OneDrive/Lakehouse).

---
**Owner:** `notebooks/3_exports/99_export_powerbi.ipynb`
**Last updated:** *20/08/2025*


