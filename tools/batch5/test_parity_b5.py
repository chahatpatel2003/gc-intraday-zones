#!/usr/bin/env python3
"""Batch-5 leakage/streaming-parity + roll-safety tests. Must pass BEFORE outcomes."""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
import batch1_lib as B
import batch5_lib as F

fails = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name, flush=True)
    if not cond:
        fails.append(name)

Df = F.prep5(B.load_discovery(start="2016-01-01", end="2018-01-01"))
Dt = F.prep5(B.load_discovery(start="2016-01-01", end="2017-07-01"))
margin = Dt.n_days - 25

def key(zf, nd):
    m = zf["day_created"] < nd
    return set(zip(zf.loc[m, "fam"], zf.loc[m, "L"].round(6), zf.loc[m, "H"].round(6),
                   zf.loc[m, "act"], zf.loc[m, "btype"]))

for fam, gen in F.GENS5.items():
    zf, zt = gen(Df), gen(Dt)
    check(f"{fam} truncation parity ({len(key(zf, margin))} zones)",
          key(zf, margin) == key(zt, margin))
    ok_act = all(z.act >= Df.ts[Df.day_first[z.day_created]]
                 for z in zf.itertuples(index=False))
    check(f"{fam} activation causality", ok_act)
    # roll safety: the bar at activation belongs to the zone's declared segment
    ok_seg = True
    for z in zf.itertuples(index=False):
        i0 = int(np.searchsorted(Df.ts, z.act, "left"))
        if i0 < len(Df.ts) and Df.iid[i0] != z.seg and Df.ts[i0] < z.exp:
            # engine drops these as roll-killed; just ensure declared seg existed at creation
            j = int(np.searchsorted(Df.ts, z.act, "left")) - 1
            if j >= 0 and Df.iid[j] != z.seg:
                ok_seg = False
                break
    check(f"{fam} roll safety (segment declared correctly)", ok_seg)

print("\n" + ("ALL PASS" if not fails else f"FAILURES: {fails}"))
sys.exit(1 if fails else 0)
