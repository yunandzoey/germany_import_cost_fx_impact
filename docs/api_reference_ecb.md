# ECB FX Rates – what we call and how we use it

**Goal:** pull daily EUR cross rates and roll them to monthly averages for USD, JPY, CNY.

## Endpoints we use
ECB SDW (Statistical Data Warehouse) REST:
- Base: `https://sdw-wsrest.ecb.europa.eu/service/data`
- Dataset: `EXR` (exchange rates)

Series keys (spot, daily, EUR as denominator):
- USD/EUR: `EXR/D.USD.EUR.SP00.A`
- JPY/EUR: `EXR/D.JPY.EUR.SP00.A`
- CNY/EUR: `EXR/D.CNY.EUR.SP00.A`

Example (USD, 2018→today, JSON):
