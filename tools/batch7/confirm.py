#!/usr/bin/env python3
"""Batch-7 Stage C — frozen confirmation on 2020-2021 (warmup from 2019-11-01)."""
import json, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch3"))
import batch1_lib as B
import batch2_lib as Z
import motifs_lib as M
import run_batch1 as R1
import run_batch3 as R3

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "batch7"))
SEL = {"ZON-035": "M07", "ZON-036": "M01", "ZON-037": "M09", "ZON-038": "M02"}

t0 = time.time()
rng = np.random.default_rng(B.SEED)
D = M.prep7(B.load_discovery(start="2019-11-01", end="2022-01-01"))
d2020 = next(i for i, d in enumerate(D.days) if d >= pd.Timestamp("2020-01-01").date())
pool, cell, _, _ = B.build_c2_pool(D)
for k in list(pool):          # donor pool restricted to confirmation days
    pool[k] = pool[k][D.day[pool[k]] >= d2020]
    if not len(pool[k]):
        del pool[k]
print(f"CONFIRMATION bars={len(D.ts):,} days={D.n_days} (2020 starts day {d2020}) "
      f"[{time.time()-t0:.0f}s]", flush=True)

stats = {}
for zid, mid in SEL.items():
    th = time.time()
    zones = M.MOTIFS[mid](D)
    zones = zones[zones["day_created"] >= d2020].reset_index(drop=True)
    ep, roll_killed = B.run_episodes(D, zones)
    prim = R1.primary_filter(ep)
    events, _ = B.dedup(prim, zones)
    ev_all, _ = B.dedup(ep[ep["side"] != 0], zones)
    shadows, diag = Z.gen_shadows_v2(zones, D, zones)
    eps, _ = B.run_episodes(D, shadows, first_only=True)
    c1, _ = B.dedup(R1.primary_filter(eps), shadows)
    c2, c2_short = B.run_c2(D, events, zones, pool, cell, rng, K=5)
    events.to_parquet(f"{OUT}/confirm_events_{zid}.parquet")
    s = R1.family_stats(D, zid, zones, ep, events, ev_all, shadows, c1, c2,
                        c2_short, roll_killed, rng)
    s["C1"]["v2_diag"] = diag
    s["stream"] = R3.stream_stats(events, zones, D)
    # events/day over confirmation days only
    ndc = int(np.isfinite(D.adr[d2020:]).sum())
    s["stream"]["events_per_day_2020_21"] = round(len(events) / ndc, 3)
    stats[zid] = s
    print(f"{zid}/{mid}: zones={len(zones)} N={len(events)} c1={len(c1)} c2={len(c2)} "
          f"class={s['classification']} [{time.time()-th:.0f}s]", flush=True)

with open(f"{OUT}/confirm_stats.json", "w") as f:
    json.dump(stats, f, indent=1, default=float)
print(f"TOTAL {time.time()-t0:.0f}s")
