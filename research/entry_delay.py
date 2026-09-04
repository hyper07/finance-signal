"""In-sample entry-delay table (Table 19): sign-adjusted return from the close of
session k after a shock to the close of session 7, by event set and cause."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUTPUT_DIR

def table(ev: pd.DataFrame, label: str) -> pd.DataFrame:
    ev = ev.dropna(subset=["post_ret_7d_pct"]).copy()
    sgn = np.where(ev["direction"] == "up", 1, -1)
    rows = []
    for k, col in ((0, None), (1, "post_ret_1d_pct"), (2, "post_ret_2d_pct"), (3, "post_ret_3d_pct"), (5, "post_ret_5d_pct")):
        r7 = ev["post_ret_7d_pct"] / 100; rk = 0.0 if col is None else ev[col] / 100
        rem = sgn * ((1 + r7) / (1 + rk) - 1) * 100
        t, p = stats.ttest_1samp(rem, 0) if len(rem) > 4 else (np.nan, np.nan)
        rows.append(dict(set=label, entry_day=k, n=len(rem), mean_pct=rem.mean(), median_pct=rem.median(), share_pos=(rem > 0).mean(), sd_pct=rem.std(ddof=1), t=t, p=p))
    return pd.DataFrame(rows)

def main() -> None:
    out = []
    for key, label in (("btc", "BTC shocks (all)"), ("bito", "BITO shocks (all)"), ("spy", "SPY shocks (all)"), ("spxl", "SPXL shocks (all)")):
        out.append(table(pd.read_csv(OUTPUT_DIR / f"events_{key}.csv"), label))
    btc = pd.read_csv(OUTPUT_DIR / "events_btc.csv"); out.append(table(btc[btc.direction == "up"], "BTC up-shocks"))
    cat = pd.read_csv(OUTPUT_DIR / "stock_events_catalogue.csv")
    frames = []
    for key, sym in (("aapl", "AAPL"), ("msft", "MSFT"), ("tsla", "TSLA"), ("nvda", "NVDA")):
        e = pd.read_csv(OUTPUT_DIR / f"events_{key}.csv"); e["symbol"] = sym; e["date"] = e["event_date"]; frames.append(e)
    ev4 = pd.concat(frames).merge(cat[["symbol", "date", "category"]], on=["symbol", "date"])
    for c in ("earnings", "idiosyncratic", "market-wide"):
        sub = ev4[(ev4.category == c) & (ev4.direction == "up")]; out.append(table(sub, f"stock up-shocks: {c}"))
    res = pd.concat(out); res.to_csv(OUTPUT_DIR / "entry_delay.csv", index=False)
    with pd.option_context("display.width", 200, "display.float_format", "{:.2f}".format):
        print(res.to_string(index=False))

if __name__ == "__main__":
    main()
