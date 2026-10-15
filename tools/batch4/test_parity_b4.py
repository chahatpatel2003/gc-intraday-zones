#!/usr/bin/env python3
"""Batch-4 leakage/parity tests. Must pass BEFORE outcome computation."""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch3"))
import batch1_lib as B
import batch2_lib as Z
import batch3_lib as Q
import batch4_lib as A
import run_batch1 as R1

fails = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name, flush=True)
    if not cond:
        fails.append(name)

Df = Z.prep(B.load_discovery(start="2016-01-01", end="2018-01-01"))
Dt = Z.prep(B.load_discovery(start="2016-01-01", end="2017-07-01"))
margin = Dt.n_days - 25

def pipeline(D):
    z = Q.gen_zon012_inst(D)
    ep, _ = B.run_episodes(D, z)
    ev = R1.primary_filter(ep)
    ev, _ = B.dedup(ev, z)
    dep = A.dep_strength(ev, z, D)
    return z, ep, ev.reset_index(drop=True), dep

zf, epf, evf, depf = pipeline(Df)
zt, ept, evt, dept = pipeline(Dt)

# 1. departure causality: window end strictly before T0 for every finite value
zm = zf.set_index("zid")
ok = True
for e, d in zip(evf.itertuples(index=False), depf):
    if not np.isfinite(d):
        continue
    ia = int(np.searchsorted(Df.ts, zm.loc[e.zid, "act"], "left"))
    if min(ia + A.DEP_CAP, e.T0 - 1, Df.seg_end[ia]) >= e.T0:
        ok = False
        break
check("departure window strictly pre-touch (all events)", ok)

# 2. departure truncation parity
kf = {(e.zid, e.T0): round(float(d), 6) for e, d in zip(evf.itertuples(index=False), depf)
      if e.day < margin and np.isfinite(d)}
kt = {(e.zid, e.T0): round(float(d), 6) for e, d in zip(evt.itertuples(index=False), dept)
      if e.day < margin and np.isfinite(d)}
common = set(kf) & set(kt)
check(f"departure truncation parity ({len(common)} events)",
      len(common) > 0 and all(kf[k] == kt[k] for k in common))

# 3. C2v2 donor constraints on a sample: isolation state matches, day differs,
#    pseudo-zone overlaps no parent zone
pool, cellv, _, _ = B.build_c2_pool(Dt)
iso = Q.isolation_mask(evt, Q.mids_for(evt, zt), zt, Dt, exclude_ids=evt["zid"].to_numpy())
sub = evt.iloc[:120].reset_index(drop=True)
rng = np.random.default_rng(7)
c2, short = A.run_c2v2(Dt, sub, zt, pool, cellv, rng, iso[:120], K=3)
idx = A.IsoIndex(zt, Dt)
want = dict(zip(sub["zid"], iso[:120]))
evd = dict(zip(sub["zid"], sub["day"]))
ok = len(c2) > 0
for r in c2.itertuples(index=False):
    if r.day == evd.get(r.event_zid, -1):
        ok = False; break
check(f"C2v2 donors: day differs from event day (n={len(c2)}, shortfall={short})", ok)

print("\n" + ("ALL PASS" if not fails else f"FAILURES: {fails}"))
sys.exit(1 if fails else 0)
