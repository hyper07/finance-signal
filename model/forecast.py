"""Interface stub for the proprietary seven-session forecaster (not published).

``research/event_study.py`` calls ``build_forecast`` at every origin. The
required payload schema and the no-look-ahead rule are specified in
``model/INTERFACE.md``; any forecaster that returns that payload can be audited
by this repository unchanged.
"""
from __future__ import annotations

_MESSAGE = (
    "model.forecast.build_forecast is not published in this repository.\n"
    "See model/INTERFACE.md for the required payload schema; any point-in-time\n"
    "forecaster returning it can be scored by research/event_study.py.\n"
    "To reproduce the paper's results without an engine, unzip derived_outputs.zip\n"
    "from https://doi.org/10.5281/zenodo.22308637 into research/output/."
)

FORECAST_VERSION = "not_published"


def build_forecast(*args, **kwargs):
    raise NotImplementedError(_MESSAGE)
