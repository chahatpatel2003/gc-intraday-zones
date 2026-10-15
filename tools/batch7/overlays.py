#!/usr/bin/env python3
"""Batch-7 Stage A2 — matched indicator overlays on eligible bases + Jaccard dedup.

Frozen assignments (category mapping from BATCH7_MINING_PLAN; M07's category resolved
to RSI because its built-in vol>=3x median makes the volz overlay degenerate —
resolved before any overlay outcome was computed):
  M01 + volz20>=2 at creation bar · M02 + volz20>=2 · M07 + RSI14 extreme
  (>=70 supply / <=30 demand) · M09 + EMA20>EMA50 trend alignment (30m).
"""
import json, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
import batch1_lib as B
import motifs_lib as M
import mine as MI

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "batch7"))


def bar_indicator_maps(D):
    """(seg, close_ns) -> dict of indicator values, per frame."""
    maps = {}
    for tfname, frame in (("15min", D.b15), ("30min", D.b30)):
        g = M.ctx(D, frame)
        out = {}
        for seg, ix in M.segs(D, frame):
            c = g["c"][ix]; v = g["v"][ix]
            r = M.rsi14(c)
            vz = M.volz20(v)
            e20 = M.ema(c, 20); e50 = M.ema(c, 50)
            cns = g["cns"][ix]
            for k in range(len(ix)):
                out[(seg, int(cns[k]))] = (r[k], vz[k], e20[k], e50[k])
        maps[tfname] = out
    return maps


def overlay_filter(zones, name, maps):
    tf = "15min" if name in ("M01", "M02") else "30min"
    mp = maps[tf]
    keep = []
    for z in zones.itertuples(index=False):
        key = (z.seg, int(z.act))
        if key not in mp:
            keep.append(False)
            continue
        r, vz, e20, e50 = mp[key]
        if name in ("M01", "M02"):
            keep.append(bool(np.isfinite(vz) and vz >= 2.0))
        elif name == "M07":
            keep.append(bool((z.btype > 0 and r >= 70) or (z.btype < 0 and r <= 30)))
        elif name == "M09":
            keep.append(bool((z.btype < 0 and e20 > e50) or (z.btype > 0 and e20 < e50)))
        else:
            keep.append(False)
    return zones[np.array(keep, bool)].reset_index(drop=True)


def main():
    t0 = time.time()
    rng = np.random.default_rng(B.SEED)
    D = M.prep7(B.load_discovery(start="2016-01-01", end="2020-01-01"))
    pool, cell, _, _ = B.build_c2_pool(D)
    maps = bar_indicator_maps(D)
    log = pd.read_csv(f"{OUT}/mining_log.csv")

    # Jaccard dedup among positive-min eligibles
    elig = ["M07", "M01", "M09", "M02"]
    keys = {}
    for m in elig:
        row = log[log["motif"] == m].iloc[0]
        keys[m] = set(map(tuple, json.loads(row["events_key"])))
    jac = {}
    for i in range(len(elig)):
        for j in range(i + 1, len(elig)):
            a, b = keys[elig[i]], keys[elig[j]]
            jac[f"{elig[i]}&{elig[j]}"] = round(len(a & b) / max(len(a | b), 1), 3)
    print("jaccard:", jac, flush=True)

    rows = []
    for m in elig:
        zones = M.MOTIFS[m](D)
        ov = overlay_filter(zones, m, maps)
        r = MI.screen(D, f"{m}+ind", ov, pool, cell, rng, m in M.CONTINUATION)
        r.pop("events_key", None)
        r["base_zones"] = int(len(zones))
        rows.append(r)
        print(r, flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/overlay_log.csv", index=False)
    with open(f"{OUT}/jaccard.json", "w") as f:
        json.dump(jac, f)
    print(f"done [{time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
