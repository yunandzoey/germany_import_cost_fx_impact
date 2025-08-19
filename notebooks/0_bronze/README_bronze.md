# 🟫 Bronze Layer – Raw Data Ingestion

Project: **Currency Impact on Germany’s Import Costs (2018–2024/25 YTD)**  
Layer owners: `notebooks/0_bronze` + `scripts/api_clients.py`, `scripts/utils.py`

This layer ingests **daily ECB FX rates** and **monthly UN Comtrade import values** into **managed Delta tables** (no FileStore paths). It’s designed to be **re-runnable** (full refresh or partition overwrite) and safe for Databricks Community Edition.

---

## 📦 Outputs (managed Delta tables)

| Table | Name | Partitions | Notes |
|---|---|---|---|
| ECB FX (daily) | `fx_impact.bronze_ecb_fx_rates` | `currency` | EUR quoted **in target currency**: `D.<CUR>.EUR.SP00.A` (e.g., USD_per_EUR). |
| Comtrade (monthly) | `fx_impact.bronze_comtrade_imports` | `year`, `cmdCode` | Imports for Germany (reporter 276), **World** partner, HS-2 shortlist: `27,84,85,39,72` (extensible). |

Common metadata columns: `ingest_ts` (timestamp), `source` (string).

---

## 🔌 Data Sources

### 1) ECB FX Rates (SDMX REST)
- Dataset: `EXR` (Exchange rates)  
- Series pattern (daily spot): **`EXR/D.<CURRENCY>.EUR.SP00.A`**  
- Example URL (CSV):  
  `https://sdw-wsrest.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?startPeriod=2018-01-01&endPeriod=2025-12-31&format=csvdata`  
- Notes:
  - `fx_rate` = **TARGET per 1 EUR** (e.g., `USD_per_EUR` ≈ 1.10).
  - Expect occasional missing days (holidays) → acceptable in Bronze.

### 2) UN Comtrade v1 (Azure API Mgmt)
- Base: `https://comtradeapi.un.org/data/v1/get/{type}/{freq}/{classification}`  
- We use: **`/C/M/HS`** (Commodity/Monthly/HS)  
- Required header: `Ocp-Apim-Subscription-Key: <your key>`  
- Core params we send:
  - `cmdCode` = HS-2 list (e.g., `27,84,85,39,72`)
  - `reporterCode` = `276` (Germany)
  - `partnerCode`  = `0` (World)
  - `flowCode`     = `M` (Import)
  - `period`       = comma-separated **YYYYMM** months per year (e.g., `201801,201802,...`)
  - Defaults to avoid 400s: `motCode=0`, `partner2Code=0`, `customsCode=C00`, `includeDesc=TRUE`

> 🔐 **Secrets:** Provide `COMTRADE_API_KEY` via **Databricks widget** (not hardcoded; not committed).

---

## 🧱 Notebooks & Scripts

```
notebooks/
  0_bronze/
    01_ingest_ecb_fx_rates.ipynb
    02_ingest_comtrade_data.ipynb
scripts/
  api_clients.py   # fetch_ecb_fx_daily(), fetch_comtrade_monthly_v1()
  utils.py         # with_ingest_meta(), write helpers
```

**ECB ingestion summary**
- Pulls daily `USD`, `JPY`, `CNY` series.
- Converts to Spark DF, adds metadata, **writes managed Delta** (partitioned by `currency`).

**Comtrade ingestion summary**
- Pulls monthly HS-2 shortlist for **2018–2025 (YTD)**, `World` partner.
- Normalizes fields: `period` → `period_date (YYYY-MM-01)`, `TradeValue` (USD).  
- Adds metadata, **writes managed Delta** (partitioned by `year`, `cmdCode`).

---

## ✅ Data Quality Rules (Bronze)

**ECB**
- Duplicates: none on `(date, currency)`.
- Values: `fx_rate > 0`; currency-aware sanity ranges (approx):  
  - USD: 0.5–2.0, CNY: 5–12, JPY: 80–300.
- Nulls: allowed (holidays); handled later in Silver monthly averages.

**Comtrade**
- Duplicates: none on `(period_date, cmdCode)` for the chosen scope.
- Values: `TradeValue > 0`.
- Coverage: ≤12 months per `year` × `cmdCode` (partial 2025 is expected).

---

## 🧪 Smoke Tests

```sql
-- ECB coverage
SELECT currency, MIN(date) AS min_d, MAX(date) AS max_d, COUNT(*) AS rows
FROM fx_impact.bronze_ecb_fx_rates
GROUP BY currency;

-- Comtrade coverage
SELECT year, COUNT(*) AS rows
FROM fx_impact.bronze_comtrade_imports
GROUP BY year ORDER BY year;
```

---

## 🔁 Re-run Policy (refresh vs incremental)

**Full refresh (safe if schema unchanged):**
```python
(sdf.write
  .format("delta")
  .mode("overwrite")
  .option("overwriteSchema","true")
  .partitionBy("currency")  # ECB
  .saveAsTable("fx_impact.bronze_ecb_fx_rates"))
```

```python
(sdf.write
  .format("delta")
  .mode("overwrite")
  .option("overwriteSchema","true")
  .partitionBy("year","cmdCode")  # Comtrade
  .saveAsTable("fx_impact.bronze_comtrade_imports"))
```

**Incremental (Comtrade 2025 only):**
```python
from pyspark.sql import functions as F

sdf_2025 = sdf.filter(F.col("year")==2025)

(sdf_2025.write
  .format("delta")
  .mode("overwrite")
  .option("replaceWhere","year = 2025")  # overwrite only this partition
  .partitionBy("year","cmdCode")
  .saveAsTable("fx_impact.bronze_comtrade_imports"))
```

---

## 🧷 Secrets & .gitignore

- **Never** hardcode or print `COMTRADE_API_KEY`.
- Use widget-only pattern (Databricks CE-friendly):
  ```python
  dbutils.widgets.removeAll()
  dbutils.widgets.text("COMTRADE_API_KEY","")
  import os
  os.environ["COMTRADE_API_KEY"] = dbutils.widgets.get("COMTRADE_API_KEY")
  ```
- `.gitignore` should exclude: `.env`, `secrets/**`, `data/**` (except reference tables), `.ipynb_checkpoints/`, etc.

---

## 🧭 Known Gotchas

- **Public DBFS root disabled** → don’t write to `/FileStore`. Use **managed tables** (`saveAsTable`) and download CSVs from the **notebook grid** (`display(df)` → Download).
- **Comtrade 400** → ensure `period` uses **YYYYMM** and you pass `motCode=0`, `partner2Code=0`, `customsCode=C00`, `includeDesc=TRUE`.
- **401/403** → missing/invalid key; set the widget; header name must be exactly `Ocp-Apim-Subscription-Key`.
- **429 (rate limit)** → increase sleep to `1.0–1.5s`, split years or HS lists.

---

## 🔜 Silver (next layer preview)

- Build monthly FX averages: `date_trunc('month', date)` → `USD_per_EUR`, `JPY_per_EUR`, `CNY_per_EUR` (pivot).  
- Aggregate Comtrade by month × HS.  
- Join on `month`, compute **EUR**: `import_eur = import_usd / USD_per_EUR`.  
- Persist as `fx_impact.silver_monthly_fact` (or keep TEMP views for export).

**Quick export (TEMP)**
```sql
-- Create TEMP views in a Silver notebook, then:
-- Python
df = spark.sql("""
  SELECT month, cmdCode, cmdDesc, import_usd, import_eur,
         USD_per_EUR, JPY_per_EUR, CNY_per_EUR
  FROM monthly_fact
  ORDER BY month, cmdCode
""")
display(df)  # Download → CSV for Power BI
```

---

## 📚 Schema (Bronze)

**`fx_impact.bronze_ecb_fx_rates`**
- `date` DATE
- `currency` STRING  (`USD`,`JPY`,`CNY`)
- `fx_rate` DOUBLE   (TARGET per 1 EUR)
- `ingest_ts` TIMESTAMP
- `source` STRING (`ECB_SDMX_EXR_D_SP00_A`)

**`fx_impact.bronze_comtrade_imports`**
- `period` STRING (e.g., `202501`)
- `period_date` DATE (month start)
- `cmdCode` STRING (HS-2)
- `cmdDesc` STRING
- `reporterCode` INT, `reporterDesc` STRING
- `partnerCode` INT, `partnerDesc` STRING
- `flowCode` STRING (`M`), `flowDesc` STRING
- `TradeValue` DOUBLE (USD)
- `netWgt` DOUBLE (if available)
- `year` INT
- `ingest_ts` TIMESTAMP
- `source` STRING (`COMTRADE_API_V1_HS2_WORLD_IMPORTS`)

---

## 🧱 Run Order

1. `01_ingest_ecb_fx_rates.ipynb` → writes `fx_impact.bronze_ecb_fx_rates`  
2. `02_ingest_comtrade_data.ipynb` → writes `fx_impact.bronze_comtrade_imports`

Commit message suggestion:
```
docs(bronze): add README_bronze with sources, DQ, re-run policy, schema
```

