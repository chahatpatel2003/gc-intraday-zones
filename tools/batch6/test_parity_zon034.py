#!/usr/bin/env python3
"""ZON-034 parity tests: truncation parity of the cluster rule; representative
geometry identical to ZON-026 zones; rule uses creation-time info only."""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch5"))
import batch1_lib as B
import batch5_lib as F
import zon034_lib as Q34

fails = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name, flush=True)
    if not cond:
        fails.append(name)

Df = F.prep5(B.load_discovery(start="2016-01-01", end="2018-01-01"))
Dt = F.prep5(B.load_discovery(start="2016-01-01", end="2017-07-01"))
margin = Dt.n_days - 25

zf, df_, z26f = Q34.gen_zon034(Df)
zt, dt_, z26t = Q34.gen_zon034(Dt)

def key(z, nd):
    m = z["day_created"] < nd
    return set(zip(z.loc[m, "L"].round(6), z.loc[m, "H"].round(6),
                   z.loc[m, "act"], z.loc[m, "btype"]))
check(f"cluster-rule truncation parity ({len(key(zf, margin))} reps)",
      key(zf, margin) == key(zt, margin))

k26 = set(zip(z26f["L"].round(6), z26f["H"].round(6), z26f["act"], z26f["btype"]))
k34 = set(zip(zf["L"].round(6), zf["H"].round(6), zf["act"], zf["btype"]))
check("every representative is a byte-identical ZON-026 zone", k34 <= k26)
check("representatives are a strict subset (dedup active)", len(k34) < len(k26))
check("suppressed + reps == raw", df_["representatives"] + df_["suppressed"] == df_["raw_zones"])
print("diag (2016-2018 window):", df_)

print("\n" + ("ALL PASS" if not fails else f"FAILURES: {fails}"))
sys.exit(1 if fails else 0)
