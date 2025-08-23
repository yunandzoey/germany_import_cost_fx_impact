# UN Comtrade – fields we ingest and how they land in our tables

**Goal:** monthly import values for Germany by HS-2 commodity, partner=World.

## API profile we call
- Product: `comtrade - v1`
- Endpoint: `GET /data/v1/get/{typeCode}/{freqCode}/{clCode}`
- Parameters we set:
  - `typeCode=C` (commodities)
  - `freqCode=M` (monthly)
  - `clCode=HS` (HS classification)
  - `reporterCode=276` (Germany)
  - `partnerCode=0` (World)
  - `flowCode=M` (Import)
  - `cmdCode=27,39,72,84,85` (HS-2 shortlist: fuels, plastics, iron&steel, machinery, electrical)
  - `period=YYYYMM` (loop 2018…latest)
  - `includeDesc=TRUE`

**Example (one month, HS 27):**
GET https://comtradeapi.un.org/data/v1/get/C/M/HS?cmdCode=27&reporterCode=276&partnerCode=0&flowCode=M&period=202001&includeDesc=TRUE


## Bronze table (`bronze_comtrade_imports`)
| Column | Type | Meaning |
|---|---|---|
| `period_date` | DATE (first day of month) | From `period` |
| `year` | INT | From `refYear` or derived |
| `cmdCode` | STRING | HS-2 code |
| `cmdDesc` | STRING | Commodity label (from API) |
| `TradeValue` | DOUBLE | Import value (USD) |
| `netWgt` | DOUBLE | Net weight (kg), optional / nullable |
| `source`, `ingest_ts` | STRING, TIMESTAMP | Lineage |

> DQ: `TradeValue > 0` and no duplicates on (`period_date`,`cmdCode`).

## Silver table (`silver_monthly_fact`)
Adds FX joins & clean labels:
| Column | Type | Notes |
|---|---|---|
| `month` | DATE | First of month |
| `cmdCode`, `cmdDesc` | STRING | HS-2 & label (short label where available) |
| `import_usd`, `import_eur` | DOUBLE | USD from Comtrade; EUR via monthly `USD_per_EUR` |
| `USD_per_EUR`, `JPY_per_EUR`, `CNY_per_EUR` | DOUBLE | From ECB monthly avg |
| `fx_mom_pct`, `fx_vol_3m`, `fx_vol_6m` | DOUBLE | FX change/vol metrics |
| `covid_period` | STRING | {Pre-COVID, During-COVID, Post-COVID} |

## Gold marts (for BI)
- `gold_monthly_metrics` – one row per `month × cmdCode` with: `import_eur`, `eur_mom_pct`, `eur_yoy_pct`, `fx_mom_pct`, `fx_vol_3m`, `fx_vol_6m`, `share_of_total_eur`, plus FX columns and labels.  
- `gold_monthly_totals` – monthly totals and MoM/YoY for all commodities.  
- `gold_covid_period_kpis_by_cmd` – pre/during/post averages & deltas.

