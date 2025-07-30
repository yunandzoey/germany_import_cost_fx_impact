# 💶 Currency Impact on Germany’s Import Costs (2018–2024)

This project explores how foreign exchange (FX) rate fluctuations impacted Germany’s monthly import costs from 2018 to 2024 — before, during, and after the COVID-19 pandemic.

## 🧩 Goal
Analyze how EUR/USD, EUR/CNY, and EUR/JPY exchange rates influenced Germany’s commodity import costs, and uncover macroeconomic patterns over time.

## 🔗 Data Sources
- **ECB FX Rates API**: Daily exchange rates → Monthly average
- **UN Comtrade API**: Monthly import values by country and commodity
- **World Bank API (optional)**: Fuel prices, inflation rates

## 🛠 Tools & Stack
- **Databricks (Community Edition)**: Python, PySpark, Delta Lake
- **Power BI**: Data storytelling & visual analytics
- **GitHub**: Version control & documentation

## 🔁 ETL Architecture (Bronze–Silver–Gold)
- **Bronze**: Raw ingestions from ECB and Comtrade
- **Silver**: Cleaned, aggregated monthly data
- **Gold**: FX-adjusted import costs, volatility metrics, COVID period tags

## 📦 Deliverables
- ✅ Structured Databricks notebooks (bronze/silver/gold)
- ✅ GitHub repo with clean code & documentation
- ⏳ Power BI dashboard (in progress)
- ⏳ Pre/Post COVID analysis & insights (in progress)

## 📁 Repo layout (Planned)
```

GERMANY_IMPORT_COST_FX_IMPACT/
│
├── README.md                  # Project overview, setup, and deliverables
├── LICENSE                    # License file (e.g., MIT)
├── requirements.txt           # Python dependencies
├── .gitignore                 # Ignore logs, temp files, credentials, etc.
│
├── conf/
│   └── job_fx_pipeline.json   # Optional: config for Databricks job automation
│
├── notebooks/
│   ├── 0_bronze/
│   │   ├── 01_ingest_ecb_fx_rates.ipynb         # Raw FX rate ingestion
│   │   └── 02_ingest_comtrade_data.ipynb        # Raw import data ingestion
│   │   └── README_bronze.md                     # Description of bronze tasks
│   │
│   ├── 1_silver/
│   │   ├── 03_clean_join_monthly_data.ipynb     # Data cleaning + join
│   │   └── README_silver.md                     # Description of silver tasks
│   │
│   ├── 2_gold/
│       ├── 04_fx_adjusted_cost_volatility.ipynb # Final business metrics
│       ├── 05_pre_post_covid_analysis.ipynb     # COVID impact analysis
│       └── README_gold.md                       # Description of gold layer
│
├── scripts/
│   ├── api_clients.py         # API wrappers for ECB and Comtrade
│   └── utils.py               # Reusable functions: date, logging, validation
│
├── data/                      # (Optional) local cached API data
│   ├── raw_sample/            # Optional sample data for testing
│   └── reference_tables/      # Optional: HS codes, country codes
│
├── dashboard/
│   ├── final_dashboard.pbix   # Power BI file
│   ├── screenshots/           # Optional: for GitHub preview
│   └── dax_measures.txt       # Optional: store DAX expressions outside PBIX
│
├── docs/                      # (Optional) project documentation
│   ├── api_reference_ecb.md
│   ├── comtrade_schema.md
│   └── covid_period_definition.md
│
└── sandbox/                   # (Optional) temp or experimental notebooks
    └── fx_rate_exploration.ipynb

```

## 📅 Milestone Status
| Milestone | Status |
|----------|--------|
| Project setup & bronze ingestion | ⏳ In Progress |
| Silver table development | ⏳ Not started |
| Gold layer & metrics | ⏳ Not started |
| Power BI dashboard | ⏳ Not started |
| Final packaging | ⏳ Not started |


## 🧭 Forward Outlook (2025+)

While this project focuses on data from 2018–2024, it's worth noting that the 2025 global economic outlook may be shaped by recent political developments — including renewed U.S. leadership under Donald Trump.

Potential implications:
- Renewed trade friction with China or EU
- FX market volatility driven by policy shocks
- Changes to commodity flows due to tariff reinstatements

Future work could extend this analysis to include 2025+ data as the effects unfold.

