"""Cross-section extension: reproduce the deployed stock engine and run the
rolling-origin study for the wider S&P universe (research/output/universe_tickers.json).

Each ticker is processed in a worker process:
  1. production-shaped OHLC from universe_yf_snapshot.csv (adjusted, with splits)
  2. run_simulation with the published s00 signals frozen from 2026-07-30
  3. event_study.analyse -> forecasts_/origins_/days_/events_/summary_ files
Keys are the lower-case ticker (e.g. "avgo"); BRK-B -> "brk_b".
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import OUTPUT_DIR, production_ohlc, reproduce_detailed_frame  # noqa: E402

STOCK_LIVE_START = "2026-07-30"


def key_for(ticker: str) -> str:
    return ticker.lower().replace("-", "_")


def spec_for(ticker: str) -> dict:
    return dict(pickle=f"detailed_s00_{key_for(ticker)}.pkl", dataset=f"s00_prediction_us_{ticker.lower()}", symbol=ticker,
                short_mode="cash", news=f"stock:{ticker}", asset_type="stock", label=f"{ticker} (deployed s00 dataset, live from 2026-07-30)")


def process(ticker: str) -> dict:
    import event_study  # noqa: WPS433  (worker import)

    t0 = time.time()
    key = key_for(ticker)
    spec = spec_for(ticker)
    snap = pd.read_csv(OUTPUT_DIR / "universe_yf_snapshot.csv", parse_dates=["date"])
    snap["v"] = 0.0
    ohlc = production_ohlc(snap, ticker)
    pickle = OUTPUT_DIR / spec["pickle"]
    if not pickle.exists():
        frame = reproduce_detailed_frame(spec["dataset"], ohlc, "cash", OUTPUT_DIR / "cache" / f"s00_{key}",
                                         live_signal_start=STOCK_LIVE_START, use_published_cache=True)
        frame.to_pickle(pickle)
    # register the spec so analyse() and downstream scripts can find it
    event_study.DATASETS[key] = spec
    # single-ticker news profile: extend COMPANY-name matching is not needed for counts
    counts = event_study.news_counts(spec["news"])
    summary = event_study.analyse(key, spec, counts)
    return {"ticker": ticker, "key": key, "origins": summary["origins"], "seconds": round(time.time() - t0, 1)}


def main() -> None:
    tickers = json.load(open(OUTPUT_DIR / "universe_tickers.json"))["tickers"]
    wanted = set(sys.argv[1:])
    if wanted:
        tickers = [t for t in tickers if t in wanted]
    results = []
    with ProcessPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(process, t): t for t in tickers}
        for fut in as_completed(futures):
            t = futures[fut]
            try:
                r = fut.result()
                results.append(r)
                print(f"[{r['ticker']}] origins={r['origins']} {r['seconds']}s")
            except Exception as exc:  # keep going; report at the end
                print(f"[{t}] FAILED: {exc!r}")
                results.append({"ticker": t, "error": repr(exc)})
    json.dump(results, open(OUTPUT_DIR / "universe_run_log.json", "w"), indent=1)
    print("done:", sum("error" not in r for r in results), "ok /", len(results))


if __name__ == "__main__":
    main()
