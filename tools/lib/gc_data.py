"""Shared data loader for the GC zone-location project.

Enforces, in one place, the non-negotiables that every research script inherits:

* PHASE GUARDS (RESEARCH_PROTOCOL v1.1 split):
    discovery          2016-01-01 -> 2022-01-01
    validation         2022-01-01 -> 2024-01-01
    development_2024   2024-01-01 -> 2025-01-01   (locked: allow_development=True required)
    final_holdout_2025 2025-01-01 -> 2026-01-01   (locked: allow_final_holdout=True AND
                                                   env AURUM_FINAL_TEST=1)
  XAUUSD 2026 H1 is sealed and reachable by no phase.
  Guards raise BEFORE any file I/O on locked periods.

* ROLL SAFETY: GC.v.0 is volume-rolled, not back-adjusted. `instrument_id` is the
  contract-segment key (ids never repeat in-range). No resampled bar, rolling window,
  or downstream zone may span two instrument_ids: resampling groups by instrument_id,
  and mid-session rolls therefore split a bin into two rows (`seg_change` marks the
  first bar of a new segment).

* UNITS: GC timestamps ns-UTC bar-open; XAUUSD parquet stores us-UTC (normalized to
  ns here); XAUUSD prices are BID-based; volumes are contracts (GC) vs notional
  millions (XAUUSD).

* SESSION CLOCK: CME ET clock. trade_date = ET bar-open + 6h (Sun 18:00 ET opens
  Monday's session). Session buckets: ASIA 18:00-02:59, LONDON 03:00-08:19,
  NY 08:20-13:29, LATE 13:30-16:59 ET.

* ADR14: per-session range of the session's dominant contract segment (roll-safe),
  14-session mean, shifted one session (known at open). The width unit for
  volatility-scaled zone rules.
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd

GC_DIR = "/Volumes/T9/Gc:Xauusd/gc"
XA_PARQ = "/Volumes/T9/Gc:Xauusd/XAUUSD Data/XAUUSD_1min.parquet"
ET = "America/New_York"

PHASES = {
    "discovery": ("2016-01-01", "2022-01-01"),
    "validation": ("2022-01-01", "2024-01-01"),
    "development_2024": ("2024-01-01", "2025-01-01"),
    "final_holdout_2025": ("2025-01-01", "2026-01-01"),
}

_GC_FILES = {y: f"{GC_DIR}/gc_{y}.parquet" for y in range(2016, 2024)}
_GC_FILES[2024] = f"{GC_DIR}/Holdout/gc_2024.parquet"      # dev-gated
_GC_FILES[2025] = f"{GC_DIR}/Holdout/gc_2025.parquet"      # final-holdout-gated
# gc_2024_jan.parquet is a duplicate subset and is never loaded.

class PhaseAccessError(RuntimeError):
    pass


def _resolve_phase(phase: str, allow_development: bool, allow_final_holdout: bool):
    if phase not in PHASES:
        raise ValueError(f"unknown phase {phase!r}; choose from {list(PHASES)}")
    if phase == "development_2024" and not allow_development:
        raise PhaseAccessError(
            "2024 is reserved for later development/stress testing. "
            "Pass allow_development=True only for approved development work.")
    if phase == "final_holdout_2025":
        if not (allow_final_holdout and os.environ.get("AURUM_FINAL_TEST") == "1"):
            raise PhaseAccessError(
                "2025 is the FINAL SEALED HOLDOUT. It opens once, for the "
                "preregistered final test only (allow_final_holdout=True AND "
                "env AURUM_FINAL_TEST=1).")
    lo, hi = (pd.Timestamp(t, tz="UTC") for t in PHASES[phase])
    return lo, hi


def _clip_window(lo, hi, start, end):
    if start is not None:
        s = pd.Timestamp(start, tz="UTC")
        if s < lo:
            raise PhaseAccessError(f"start {s} precedes phase window {lo}")
        lo = s
    if end is not None:
        e = pd.Timestamp(end, tz="UTC")
        if e > hi:
            raise PhaseAccessError(f"end {e} exceeds phase window {hi}")
        hi = e
    return lo, hi


def _add_clock_columns(df: pd.DataFrame) -> pd.DataFrame:
    et = df["ts"].dt.tz_convert(ET).dt.tz_localize(None)
    df["trade_date"] = (et + pd.Timedelta(hours=6)).dt.date
    mins = et.dt.hour * 60 + et.dt.minute
    sess = np.select(
        [(mins >= 18 * 60) | (mins < 3 * 60),
         (mins >= 3 * 60) & (mins < 8 * 60 + 20),
         (mins >= 8 * 60 + 20) & (mins < 13 * 60 + 30),
         (mins >= 13 * 60 + 30) & (mins < 17 * 60)],
        ["ASIA", "LONDON", "NY", "LATE"], default="HALT")
    df["session"] = sess
    df["et_shifted"] = et + pd.Timedelta(hours=6)      # session-anchored clock
    return df


def load_gc_1m(phase: str, start=None, end=None, *,
               allow_development: bool = False,
               allow_final_holdout: bool = False) -> pd.DataFrame:
    """GC.v.0 1-minute bars for one phase, roll- and session-annotated."""
    lo, hi = _resolve_phase(phase, allow_development, allow_final_holdout)
    lo, hi = _clip_window(lo, hi, start, end)
    # last year actually inside [lo, hi) — never touch a later year's file
    # (an exact Jan-1 upper bound must NOT open the next year, which may be gated)
    last_year = (hi - pd.Timedelta(nanoseconds=1)).year
    years = range(lo.year, min(last_year, 2025) + 1)
    frames = []
    for y in years:
        p = _GC_FILES.get(y)
        if p is None:
            continue
        d = pd.read_parquet(p).reset_index()
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df["ts"] = pd.to_datetime(df["ts_event"], utc=True).dt.as_unit("ns")
    df = (df.drop(columns=["ts_event", "rtype", "publisher_id", "symbol"])
            .sort_values("ts", kind="stable").reset_index(drop=True))
    df = df[(df["ts"] >= lo) & (df["ts"] < hi)].reset_index(drop=True)
    if df.empty:
        raise ValueError("empty window")
    df["seg_change"] = df["instrument_id"].ne(df["instrument_id"].shift()).fillna(False)
    df.loc[0, "seg_change"] = False
    gap_s = df["ts"].diff().dt.total_seconds()
    df["after_gap"] = (gap_s > 60).fillna(False)
    df = _add_clock_columns(df)
    roll_dates = set(df.loc[df["seg_change"], "trade_date"])
    df["roll_session"] = df["trade_date"].isin(roll_dates)
    return df


def load_xauusd_1m(phase: str, start=None, end=None, *,
                   allow_development: bool = False,
                   allow_final_holdout: bool = False) -> pd.DataFrame:
    """XAUUSD Dukascopy 1-minute BID bars for one phase (mixed file, predicate-filtered)."""
    import pyarrow.parquet as pq
    lo, hi = _resolve_phase(phase, allow_development, allow_final_holdout)
    lo, hi = _clip_window(lo, hi, start, end)
    t = pq.read_table(XA_PARQ, filters=[("timestamp_utc", ">=", lo.to_pydatetime()),
                                        ("timestamp_utc", "<", hi.to_pydatetime())])
    df = t.to_pandas()
    if "timestamp_utc" not in df.columns:
        df = df.reset_index()
    df["ts"] = pd.to_datetime(df["timestamp_utc"], utc=True).dt.as_unit("ns")
    df = (df.drop(columns=["timestamp_utc", "source"], errors="ignore")
            .sort_values("ts", kind="stable").reset_index(drop=True))
    df["instrument_id"] = 0            # spot: single continuous segment
    df["seg_change"] = False
    df["after_gap"] = (df["ts"].diff().dt.total_seconds() > 60).fillna(False)
    return _add_clock_columns(df)


_TF_MIN = {"5min": 5, "15min": 15, "30min": 30, "1h": 60, "4h": 240}


def resample(df: pd.DataFrame, tf: str) -> pd.DataFrame:
    """Session-anchored, roll-safe resample of 1m bars to 5min/15min/30min/1h/4h/1d.

    Bins are anchored to the 18:00 ET session open (via the +6h shifted clock) and
    grouped by instrument_id, so no output bar ever spans a roll; a mid-session roll
    yields two partial bars for the same bin timestamp (distinct instrument_id).
    Output ts = UTC open time of the first 1m bar in the bin. n1m = coverage count.
    """
    if tf == "1d":
        keys = ["instrument_id", "trade_date"]
        binned = df.assign(_bin=df["trade_date"])
    elif tf in _TF_MIN:
        m = _TF_MIN[tf]
        b = df["et_shifted"].dt.floor(f"{m}min")
        binned = df.assign(_bin=b)
        keys = ["instrument_id", "_bin"]
    else:
        raise ValueError(f"unsupported tf {tf!r} (no sub-5m bars may be produced)")
    spec = dict(ts=("ts", "first"), ts_last=("ts", "last"), open=("open", "first"),
                high=("high", "max"), low=("low", "min"), close=("close", "last"),
                volume=("volume", "sum"), n1m=("ts", "size"), session=("session", "first"))
    if tf != "1d":
        spec["trade_date"] = ("trade_date", "first")
        spec["bin"] = ("_bin", "first")
    agg = binned.groupby(keys, sort=False).agg(**spec)
    agg = agg.reset_index().sort_values("ts", kind="stable").reset_index(drop=True)
    agg["seg_change"] = agg["instrument_id"].ne(agg["instrument_id"].shift()).fillna(False)
    if len(agg):
        agg.loc[0, "seg_change"] = False
    return agg.drop(columns=["_bin"], errors="ignore")


def session_adr(df1m: pd.DataFrame, n: int = 14) -> pd.DataFrame:
    """ADR14 per trade_date, roll-safe, shifted so it is known at session open.

    Range is taken from the session's DOMINANT contract segment only (on the ~5
    roll sessions/yr the minority segment is ignored rather than polluting the
    range with the roll jump).
    """
    g = (df1m.groupby(["trade_date", "instrument_id"])
              .agg(hi=("high", "max"), lo=("low", "min"), n=("ts", "size"))
              .reset_index())
    g = g.sort_values("n").groupby("trade_date").tail(1).sort_values("trade_date")
    g["range"] = g["hi"] - g["lo"]
    g["adr"] = g["range"].rolling(n, min_periods=n).mean().shift(1)
    return g[["trade_date", "range", "adr"]].reset_index(drop=True)
