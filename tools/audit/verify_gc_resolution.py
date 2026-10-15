#!/usr/bin/env python3
"""Direct re-verification of GC data resolution. NON-HOLDOUT files only (2016-2023).

Prints structure/timing facts ONLY — no price or volume values are displayed.
"""
import collections
import numpy as np
import pandas as pd

GC = "/Volumes/T9/Gc:Xauusd/gc"
YEARS = range(2016, 2024)                     # research years only; 2024/2025 never opened

frames = []
for y in YEARS:
    df = pd.read_parquet(f"{GC}/gc_{y}.parquet").reset_index()
    frames.append(df)
df = pd.concat(frames, ignore_index=True)

print("== columns / dtypes ==")
for c, t in df.dtypes.items():
    print(f"  {c}: {t}")

ts = pd.to_datetime(df["ts_event"], utc=True).dt.as_unit("ns")
ns = ts.astype("int64").to_numpy()
srt = np.sort(ns)

print("\n== schema identifiers ==")
print("  rtype unique:", sorted(df["rtype"].unique().tolist()))
print("  publisher_id unique:", sorted(df["publisher_id"].unique().tolist()))
print("  symbol unique:", df["symbol"].unique().tolist())
print("  instrument_id nunique:", int(df["instrument_id"].nunique()))

print("\n== timestamp resolution ==")
print("  stored dtype:", df["ts_event"].dtype if "ts_event" in df else "index")
for unit, div in [("1s", 1_000_000_000), ("60s", 60_000_000_000)]:
    frac = float(((ns % div) == 0).mean())
    print(f"  fraction of timestamps exactly aligned to {unit}: {frac:.6f}")
dts = np.diff(srt)
pos = dts[dts > 0]
print("  min positive spacing:", pos.min() / 1e9, "s")
print("  duplicate timestamps:", int((dts == 0).sum()))

print("\n== timestamp spacing histogram (seconds, top 10) ==")
cnt = collections.Counter((pos / 1e9).round(0))
tot = len(pos)
for v, c in cnt.most_common(10):
    print(f"  {int(v):>7}s : {c:>9,}  ({100*c/tot:.3f}%)")
sub60 = int((pos < 60_000_000_000).sum())
print("  spacings < 60s:", sub60)

print("\n== rows per trade day ==")
et = ts.dt.tz_convert("America/New_York").dt.tz_localize(None)
tdate = (et + pd.Timedelta(hours=6)).dt.date
per = pd.Series(1, index=tdate).groupby(level=0).sum()
print(f"  days={len(per)}  median={per.median():.0f}  p10={per.quantile(.1):.0f}  "
      f"p90={per.quantile(.9):.0f}  max={per.max()}")
print(f"  total rows={len(df):,}  ~rows/day={len(df)/len(per):.0f}")

print("\n== record-type verdict ==")
has_ohlc = all(c in df.columns for c in ("open", "high", "low", "close"))
print("  has open/high/low/close aggregate columns:", has_ohlc)
print("  has per-trade fields (price,size,side,sequence)?:",
      any(c in df.columns for c in ("price", "size", "side", "sequence", "action")))
mx = int(per.max())
print(f"  max rows/day {mx} vs minutes in a 23h session (1380): "
      f"{'<= bar grid — inconsistent with trades/ticks' if mx <= 1380 else 'EXCEEDS minute grid'}")
