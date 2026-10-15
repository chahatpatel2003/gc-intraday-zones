#!/usr/bin/env python3
"""GC vs XAUUSD alignment sanity check — RESEARCH WINDOW ONLY (<= 2023-12-31).

Data-sanity/alignment only (clock offset, coverage overlap, return coherence,
futures-spot basis magnitude). No predictive testing.
Writes aurum/audit/alignment_audit.json.
"""
import json
import os
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

GC_DIR = "/Volumes/T9/Gc:Xauusd/gc"
XA = "/Volumes/T9/Gc:Xauusd/XAUUSD Data/XAUUSD_1min.parquet"
OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "audit", "alignment_audit.json"))
SEAL = pd.Timestamp("2024-01-01", tz="UTC")

gc = pd.concat([pd.read_parquet(f"{GC_DIR}/gc_{y}.parquet")[["close"]]
                for y in (2021, 2022, 2023)])
gc.index = pd.DatetimeIndex(gc.index).tz_convert("UTC").as_unit("ns")
gc = gc[~gc.index.duplicated()].sort_index()
gc = gc[gc.index >= "2021-06-29"]

xt = pq.read_table(XA, filters=[("timestamp_utc", "<", SEAL.to_pydatetime())]).to_pandas()
if "timestamp_utc" not in xt.columns:
    xt = xt.reset_index()
xa = xt.set_index(pd.DatetimeIndex(pd.to_datetime(xt["timestamp_utc"], utc=True)).as_unit("ns"))[["close"]]
xa = xa[~xa.index.duplicated()].sort_index()

res = {"window": [str(max(gc.index[0], xa.index[0])), str(min(gc.index[-1], xa.index[-1]))]}
common = gc.index.intersection(xa.index)
res["gc_minutes"] = int(len(gc)); res["xa_minutes"] = int(len(xa))
res["common_minutes"] = int(len(common))
res["gc_only"] = int(len(gc.index.difference(xa.index)))
res["xa_only"] = int(len(xa.index.difference(gc.index)))

# where does each-only fall (UTC hour histogram, top entries)?
def hour_hist(ix):
    h = pd.Series(ix.hour)
    return {int(k): int(v) for k, v in h.value_counts().head(6).items()}
res["gc_only_by_hour"] = hour_hist(gc.index.difference(xa.index))
res["xa_only_by_hour"] = hour_hist(xa.index.difference(gc.index))

# 5m log-return correlation on common grid, and clock-offset scan at 1m shifts
j = pd.DataFrame({"gc": gc["close"], "xa": xa["close"]}).dropna()
r5 = np.log(j).groupby(pd.Grouper(freq="5min")).last().dropna().diff().dropna()
res["corr_5m"] = round(float(r5["gc"].corr(r5["xa"])), 4)
r1 = np.log(j).diff().dropna()
lags = {}
for k in (-3, -2, -1, 0, 1, 2, 3):
    lags[k] = round(float(r1["gc"].corr(r1["xa"].shift(k))), 4)
res["corr_1m_by_lag"] = lags
res["lag_peak_at_zero"] = bool(max(lags, key=lambda k: lags[k]) == 0)

# futures - spot basis at 20:00 UTC daily
snap = j[(j.index.hour == 20) & (j.index.minute == 0)]
basis = (snap["gc"] - snap["xa"])
by_y = basis.groupby(snap.index.year)
res["basis_usd_median_by_year"] = {int(k): round(float(v), 2) for k, v in by_y.median().items()}
res["basis_usd_p5_p95"] = [round(float(basis.quantile(q)), 2) for q in (0.05, 0.95)]
res["basis_negative_days"] = int((basis < -2).sum())

with open(OUT, "w") as f:
    json.dump(res, f, indent=1)
print(json.dumps(res, indent=1))
