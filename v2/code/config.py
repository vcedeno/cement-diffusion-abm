"""Paths, time axis and constants shared by all modules.

Time is monthly. Month index 0 is January 2010. The observed record runs to December 2025
(USGS Mineral Industry Surveys). Scenario runs can extend the horizon with the environment
variable PLC_END (for example PLC_END=2035-12); demand after the record repeats the last
12 observed months.

Periods used throughout:
  calibration (training)  2010-01 .. 2022-12
  validation (forecast)   2023-01 .. 2025-12   (never used in calibration)
"""
from __future__ import annotations
import os
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]          # the Majid/ folder
ORIG = ROOT / "original_data"                       # inputs received from the cement-diffusion-abm repository
NEW = ROOT / "new_data"                             # inputs compiled for this model (evidence and derived files)
DERIVED = NEW / "derived"                           # model-ready tables built by build_inputs.py
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

OBS_END = "2025-12"                                  # last month of the observed record
CAL_END = "2022-12"                                  # last month of the calibration window
MONTHS = pd.period_range("2010-01", max(os.environ.get("PLC_END", OBS_END), OBS_END), freq="M")
T = len(MONTHS)                                      # simulated months
T_OBS = len(pd.period_range("2010-01", OBS_END, freq="M"))   # observed months (192)
T_DEM = len(pd.period_range("2010-01", "2024-12", freq="M"))  # months covered by the ready-mix demand file (180)
T_CAL = len(pd.period_range("2010-01", CAL_END, freq="M"))   # calibration months (156)

# Dated industry signals (leaders' start hazard). Evidence: ledger items S1, S2.
GCCA_DATE = "2020-09"        # GCCA 2050 Climate Ambition statement (members commit to net-zero concrete)
ROADMAP_DATE = "2021-10"     # PCA Roadmap to Carbon Neutrality (October 2021)
STANDARD_DATE = "2012-01"    # ASTM C595 Type IL: earliest month any firm can start (ledger S0)
# Procurement shift: start month drawn uniformly per run in this window (ledger P1-P3)
PROC_LO, PROC_HI = "2021-12", "2022-09"


def midx(ym) -> int:
    """Month index of 'YYYY-MM' (or 'YYYY-MM-DD'); before 2010 is negative; missing maps to 10**6 (never)."""
    if ym is None or (isinstance(ym, float) and np.isnan(ym)) or str(ym) in ("nan", "None", ""):
        return 10**6
    return (pd.Period(str(ym)[:7], freq="M") - MONTHS[0]).n

# Calibration setup (calibrate.py, validate.py): fixed values and structural rules of the reported model
CAL_FIXED = dict(lC=1.0, H=18.0)
CAL_STRUCTURE = dict(firm_form="observed", sigma=1.0, firm_ramp=True, iiv_keep=True, follower_keep_opc=True)
