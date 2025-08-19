# scripts/api_clients.py
import io
import os
import time
import requests
import pandas as pd


ECB_BASE = "https://sdw-wsrest.ecb.europa.eu/service/data"  # SDMX REST

def fetch_ecb_fx_daily(symbols=("USD","JPY","CNY"),
                       start="2018-01-01",
                       end="2024-12-31",
                       sleep_sec=0.6) -> pd.DataFrame:
    """
    Pulls daily ECB FX rates: D.<CURRENCY>.EUR.SP00.A  (price of 1 EUR in target currency)
    Returns pandas DF with columns: date, currency, fx_rate
    """
    frames = []
    for cur in symbols:
        # EXR dataset: freq/currency/quote/type/seriesvariant
        # D = daily, .EUR = quote in EUR base, SP00 = spot, A = average/standard series
        url = (f"{ECB_BASE}/EXR/D.{cur}.EUR.SP00.A"
               f"?startPeriod={start}&endPeriod={end}&format=csvdata")
        r = requests.get(url, timeout=30)
        r.raise_for_status()

        # ECB CSV sometimes includes metadata lines; try robust parsing
        try:
            df = pd.read_csv(io.StringIO(r.text))
        except Exception:
            df = pd.read_csv(io.StringIO(r.text), comment='#')

        # Normalize columns if present
        # Typical columns: TIME_PERIOD, OBS_VALUE, CURRENCY, CURRENCY_DENOM, ...
        cols = {c.lower(): c for c in df.columns}
        if 'TIME_PERIOD' in df.columns:
            date_col, val_col = 'TIME_PERIOD', 'OBS_VALUE'
        elif 'time_period' in cols and 'obs_value' in cols:
            date_col, val_col = cols['time_period'], cols['obs_value']
        else:
            raise ValueError(f"Unexpected ECB columns: {df.columns.tolist()}")

        out = df[[date_col, val_col]].copy()
        out.columns = ['date', 'fx_rate']
        out['date'] = pd.to_datetime(out['date'])
        out['fx_rate'] = pd.to_numeric(out['fx_rate'], errors='coerce')
        out['currency'] = cur

        frames.append(out[['date', 'currency', 'fx_rate']])
        time.sleep(sleep_sec)  # be polite to API

    final = pd.concat(frames, ignore_index=True)
    return final

# scripts/api_clients.py  (new version for v1 API)
# --- Comtrade v1 client ---
CT_BASE = "https://comtradeapi.un.org/data/v1/get"  # v1 base

def _auth_headers():
    api_key = os.getenv("COMTRADE_API_KEY")
    if not api_key:
        raise RuntimeError("Set COMTRADE_API_KEY via env/secret.")
    return {"Ocp-Apim-Subscription-Key": api_key}

def fetch_comtrade_monthly_v1(
    year: int,
    hs_codes=("27","84","85","39","72"),
    reporter_code=276,
    partner_code=0,
    flow_code="M",
    classification="HS",
    retries=3,
    sleep_sec=0.7,
    api_key: str | None = None
):
    import time, requests, pandas as pd, os

    # Use YYYYMM to avoid 400s for monthly
    months = [f"{year}{m:02d}" for m in range(1, 13)]
    url = f"https://comtradeapi.un.org/data/v1/get/C/M/{classification}"

    params = {
        "cmdCode": ",".join(hs_codes),
        "reporterCode": reporter_code,
        "partnerCode": partner_code,
        "flowCode": flow_code,
        "period": ",".join(months),
        # v1 defaults that prevent validation errors:
        "motCode": 0,
        "partner2Code": 0,
        "customsCode": "C00",
        "includeDesc": "TRUE",
    }

    key = api_key or os.getenv("COMTRADE_API_KEY")
    if not key:
        raise RuntimeError("Missing COMTRADE_API_KEY")
    headers = {"Ocp-Apim-Subscription-Key": key}

    for attempt in range(retries):
        r = requests.get(url, params=params, headers=headers, timeout=120)
        if r.status_code == 200:
            break
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(sleep_sec * (attempt + 1))
            continue
        # Print body to see why it failed
        raise requests.HTTPError(f"{r.status_code} {r.reason}: {r.url}\n{r.text}")

    js = r.json()
    data = js.get("data", [])
    if not data:
        return pd.DataFrame()

    df = pd.json_normalize(data)
    # Normalize
    if "period" in df.columns:
        # period may be "202001" -> cast to month start
        per = df["period"].astype(str).str.replace("-", "", regex=False)
        df["period_date"] = pd.to_datetime(per + "01", format="%Y%m%d", errors="coerce")
    value_col = "primaryValue" if "primaryValue" in df.columns else "cifvalue"
    if value_col in df.columns:
        df["TradeValue"] = pd.to_numeric(df[value_col], errors="coerce")
    if "cmdCode" in df.columns:
        df["cmdCode"] = df["cmdCode"].astype(str)
    df["year"] = year
    return df

