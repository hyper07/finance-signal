"""Write DATA_DEPOSIT.md: the file manifest (size, SHA-256) a data repository
deposit needs so that the study can be verified byte-for-byte."""
from __future__ import annotations

import hashlib
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ALPACA_DIR, OUTPUT_DIR, REPO  # noqa: E402

INPUTS = [
    ALPACA_DIR / "underlying_daily.csv",
    ALPACA_DIR / "crypto_daily.csv",
    ALPACA_DIR / "news.jsonl",
    OUTPUT_DIR / "stocks_yf_snapshot.csv",
    OUTPUT_DIR / "spy_yf_snapshot.csv",
    OUTPUT_DIR / "qqq_yf_snapshot.csv",
    OUTPUT_DIR / "earnings_dates.csv",
    Path(__file__).resolve().parent / "manual_attributions.json",
    *sorted(OUTPUT_DIR.glob("public_*.json")),
]
DERIVED = sorted(
    p for p in OUTPUT_DIR.glob("*")
    if p.is_file() and p.suffix in {".csv", ".json"} and not p.name.startswith("public_")
    and p.name not in {"stocks_yf_snapshot.csv", "spy_yf_snapshot.csv", "qqq_yf_snapshot.csv", "earnings_dates.csv"}
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def table(paths: list[Path]) -> str:
    lines = ["| file | size (MB) | SHA-256 |", "|---|---|---|"]
    for p in paths:
        lines.append(f"| `{p.relative_to(REPO)}` | {p.stat().st_size / 1e6:.2f} | `{sha256(p)}` |")
    return "\n".join(lines)


def main() -> None:
    text = f"""# Data deposit manifest

Generated {date.today().isoformat()} by `research/deposit_manifest.py`.

The **inputs** table records local provenance and hashes. Do **not** upload raw
market bars or licensed news text without written redistribution permission.
Upload only rights-cleared derived outputs and figures. The derived files let a
reader verify reported calculations without rerunning the proprietary engine.

## Inputs (required to reproduce)

{table(INPUTS)}

Provenance: Alpaca Market Data historical API (SIP feed for equities; crypto
bars; Benzinga news via Alpaca News API), pulled 2026-08-24/30 with
`tools/alpaca_history.py`; Yahoo Finance adjusted daily history with split
events for AAPL/MSFT/TSLA/NVDA pulled 2026-09-03; public prediction datasets
from `https://signal.dotori.ai/api/public/datasets/<name>` snapshotted 2026-09-03.
Redistribution terms: raw bars and news text are excluded unless the provider
grants written permission. A hash manifest supports identity checks but does not
make the unavailable forecast engine or absent retrieval utility reproducible.

## Derived outputs

{table(DERIVED)}

## Figures

{", ".join(f"`{p.name}`" for p in sorted([*(OUTPUT_DIR / "figures").glob("*.png"), *(OUTPUT_DIR / "figures").glob("*.pdf")]))}
"""
    (Path(__file__).resolve().parent / "DATA_DEPOSIT.md").write_text(text)
    print("DATA_DEPOSIT.md written:", len(INPUTS), "inputs,", len(DERIVED), "derived files")


if __name__ == "__main__":
    main()
