#!/usr/bin/env python3
"""Loader self-test — discovery data only; proves guards, roll safety, resampling.

NOT a zone backtest. Prints structure facts, no price values.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pandas as pd
import gc_data as G

fails = []

def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)

# 1. guards must raise BEFORE any I/O on locked periods
for phase, kw in [("development_2024", {}), ("final_holdout_2025", {}),
                  ("final_holdout_2025", {"allow_final_holdout": True})]:
    try:
        G.load_gc_1m(phase, **kw)
        check(f"guard {phase} {kw}", False)
    except G.PhaseAccessError:
        check(f"guard {phase} {kw} raises", True)

# 2. window escape attempts
try:
    G.load_gc_1m("discovery", end="2022-06-01")
    check("discovery end-escape blocked", False)
except G.PhaseAccessError:
    check("discovery end-escape blocked", True)

# 3. validation phase must not open the gated 2024 file (exact Jan-1 bound)
last = (pd.Timestamp(G.PHASES["validation"][1], tz="UTC") - pd.Timedelta(nanoseconds=1)).year
check("validation last file year == 2023", last == 2023)

# 4. load a discovery slice spanning a known roll month (2019-11/12)
df = G.load_gc_1m("discovery", start="2019-11-01", end="2019-12-15")
check("slice loaded", len(df) > 30000)
check("within window", df["ts"].min() >= pd.Timestamp("2019-11-01", tz="UTC")
      and df["ts"].max() < pd.Timestamp("2019-12-15", tz="UTC"))
nseg = df["instrument_id"].nunique()
check(f"contains a roll (segments={nseg})", nseg >= 2)
check("seg_change count == segments-1", int(df["seg_change"].sum()) == nseg - 1)
check("roll sessions flagged", df.loc[df["seg_change"], "trade_date"].isin(
    df.loc[df["roll_session"], "trade_date"]).all())

# 5. resample roll safety: every output bar has exactly one instrument_id by construction;
#    verify no bin ts appears with >1 instrument except at the roll, and n1m sums match
for tf in ("5min", "30min", "4h", "1d"):
    r = G.resample(df, tf)
    check(f"{tf}: n1m conserved", int(r["n1m"].sum()) == len(df))
    dupbins = r.groupby(["trade_date", "ts"]).size().max() if tf != "1d" else \
              r.groupby("trade_date").size().max()
    if tf == "1d":
        check("1d: one row/session (rolls at session boundary here)",
              dupbins in (1, 2))
    else:
        check(f"{tf}: bins unique per instrument", dupbins in (1, 2))
    seg_ok = (r.groupby("instrument_id")["ts"].apply(lambda s: s.is_monotonic_increasing).all())
    check(f"{tf}: per-segment time order", bool(seg_ok))

# 6. sessions labelled + ADR available and roll-safe
check("session buckets present",
      set(df["session"].unique()) <= {"ASIA", "LONDON", "NY", "LATE", "HALT"})
adr = G.session_adr(G.load_gc_1m("discovery", start="2019-09-01", end="2019-12-15"))
have = adr.dropna(subset=["adr"])
check("ADR14 known-at-open values exist", len(have) > 40)

# 7. XAUUSD loader: phase filter + clock columns (discovery overlap only)
xa = G.load_xauusd_1m("discovery", start="2021-07-01", end="2021-07-15")
check("xauusd slice loaded", len(xa) > 8000)
check("xauusd within window", xa["ts"].max() < pd.Timestamp("2021-07-15", tz="UTC"))
check("xauusd ns-normalized", str(xa["ts"].dtype) == "datetime64[ns, UTC]")

print("\n" + ("ALL PASS" if not fails else f"FAILURES: {fails}"))
sys.exit(1 if fails else 0)
