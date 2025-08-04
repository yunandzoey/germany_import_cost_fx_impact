# scripts/api_clients.py
import io
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
