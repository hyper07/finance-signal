"""Interface stub for the proprietary signal engine (not published).

The audit in ``research/`` needs one function from this module. Its contract —
inputs, the columns of the returned frame, and the frozen-signal rule — is
specified in ``model/INTERFACE.md``. Supply your own implementation here to run
the study on your own forecaster, or unzip the deposited outputs
(https://doi.org/10.5281/zenodo.22308637) to reproduce the published results
without any engine.
"""
from __future__ import annotations

_MESSAGE = (
    "model.strategy.run_simulation is not published in this repository.\n"
    "See model/INTERFACE.md for the required signature and output columns.\n"
    "To reproduce the paper's results without an engine, unzip derived_outputs.zip\n"
    "from https://doi.org/10.5281/zenodo.22308637 into research/output/ and run the\n"
    "analysis steps in research/README.md (steps 3 onward)."
)


def run_simulation(*args, **kwargs):
    raise NotImplementedError(_MESSAGE)
