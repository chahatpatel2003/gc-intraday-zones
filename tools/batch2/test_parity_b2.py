#!/usr/bin/env python3
"""Batch-2 leakage / streaming-parity tests. Must pass BEFORE outcome computation.

1. Truncation parity: every generator run on [2016, 2018-01) vs truncated
   [2016, 2017-07) must produce IDENTICAL zones (boundaries, activation, type)
   for zones created > 25 sessions before the truncation edge. Catches any use
   of future data in zone construction (incl. ADR, dedup state, profiles).
2. Activation causality: no zone activates before its creation day began.
3. Engine brute-force recheck: FE60/AE60 recomputed independently for sampled
   episodes must match the engine.
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
import batch1_lib as B
import batch2_lib as Z

fails = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name, flush=True)
    if not cond:
        fails.append(name)

Df = Z.prep(B.load_discovery(start="2016-01-01", end="2018-01-01"))
Dt = Z.prep(B.load_discovery(start="2016-01-01", end="2017-07-01"))
margin = Dt.n_days - 25

def key(zf, nd):
    m = zf["day_created"] < nd
    return set(zip(zf.loc[m, "fam"],
                   zf.loc[m, "L"].round(6), zf.loc[m, "H"].round(6),
                   zf.loc[m, "act"], zf.loc[m, "btype"]))

for fam, gen in Z.GENS.items():
    zf, zt = gen(Df), gen(Dt)
    kf, kt = key(zf, margin), key(zt, margin)
    check(f"{fam} truncation parity ({len(kf)} zones)", kf == kt)
    ok_act = True
    for z in zf.itertuples(index=False):
        if z.act < Df.ts[Df.day_first[z.day_created]]:
            ok_act = False
            break
    check(f"{fam} activation causality", ok_act)

# brute-force excursion recheck on ZON-008 (trunc window)
z8 = Z.gen_zon008(Dt)
ep, _ = B.run_episodes(Dt, z8)
s = ep[(ep["side"] != 0) & ep["FE60"].notna()].sample(25, random_state=7)
ok = True
for e in s.itertuples(index=False):
    T0 = int(e.T0)
    end = min(T0 + 60, Dt.seg_end[T0])
    if end - T0 < 60:
        continue
    if e.side < 0:
        fe = max(e.P0 - Dt.l[T0 + 1:end + 1].min(), 0.0)
        ae = max(Dt.h[T0:end + 1].max() - e.P0, 0.0)
    else:
        fe = max(Dt.h[T0 + 1:end + 1].max() - e.P0, 0.0)
        ae = max(e.P0 - Dt.l[T0:end + 1].min(), 0.0)
    if not (np.isclose(fe, e.FE60, atol=1e-9) and np.isclose(ae, e.AE60, atol=1e-9)):
        ok = False
        break
check("engine FE60/AE60 brute-force match (25 sampled)", ok)

print("\n" + ("ALL PASS" if not fails else f"FAILURES: {fails}"))
sys.exit(1 if fails else 0)
