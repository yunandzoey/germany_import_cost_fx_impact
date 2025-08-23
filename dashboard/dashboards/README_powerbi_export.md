# Power BI Report — Germany Imports & FX Impact

**Pages**
1. **Overview** – Trend of monthly imports; cards for latest month, FX avg, and MoM%.
2. **FX vs Costs** – Stacked imports vs USD/EUR rate (secondary axis) + 3-mo FX volatility.
3. **Commodity Mix** – Monthly HS-2 split + latest-month top commodities & share of total.
4. **COVID Impact** – Pre/During/Post averages & Post vs Pre (%) by commodity.
5. **Details** – Tabular view with MoM%, YoY%, FX rate & volatility; conditional colors.

**Slicers (synced across pages)**  
- Month (From/To) • Commodity (HS-2)

**How to open**
- Open `dashboard/Germany_Imports_FX_Impact_v1.pbix` in Power BI Desktop, or view `dashboard/exports/Germany_Imports_FX_Impact_v1.pdf`.

**Data refresh**
- Report reads the Gold tables/views in Databricks (`fx_impact`). Refresh by re-running the Databricks jobs (Bronze→Silver→Gold). If using CSV exports, re-run `99_export_powerbi.ipynb` to overwrite the `dashboard/exports/*.csv` files, then Refresh in Power BI.
