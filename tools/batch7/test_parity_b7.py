#!/usr/bin/env python3
"""Batch-7 Stage B — parity/leakage/roll gates on the four frozen candidates."""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
import batch1_lib as B
import motifs_lib as M

fails = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name, flush=True)
    if not cond:
        fails.append(name)

Df = M.prep7(B.load_discovery(start="2016-01-01", end="2018-01-01"))
Dt = M.prep7(B.load_discovery(start="2016-01-01", end="2017-07-01"))
margin = Dt.n_days - 25
SEL = {"ZON-035": "M07", "ZON-036": "M01", "ZON-037": "M09", "ZON-038": "M02"}

def key(z, nd):
    m = z["day_created"] < nd
    return set(zip(z.loc[m, "L"].round(6), z.loc[m, "H"].round(6),
                   z.loc[m, "act"], z.loc[m, "btype"]))

for zid, mid in SEL.items():
    zf, zt = M.MOTIFS[mid](Df), M.MOTIFS[mid](Dt)
    check(f"{zid}/{mid} truncation parity ({len(key(zf, margin))})",
          key(zf, margin) == key(zt, margin))
    check(f"{zid}/{mid} activation causality",
          all(z.act >= Df.ts[Df.day_first[z.day_created]]
              for z in zf.itertuples(index=False)))
    ok_seg = True
    for z in zf.itertuples(index=False):
        j = int(np.searchsorted(Df.ts, z.act, "left")) - 1
        if j >= 0 and Df.iid[j] != z.seg:
            ok_seg = False
            break
    check(f"{zid}/{mid} roll safety", ok_seg)

print("\n" + ("ALL PASS" if not fails else f"FAILURES: {fails}"))
sys.exit(1 if fails else 0)
