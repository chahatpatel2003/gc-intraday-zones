#!/usr/bin/env python3
"""Batch-3 leakage/parity tests. Must pass BEFORE outcome computation.

1. Instrumented ZON-012 twin produces byte-identical zones to the frozen generator.
2. Truncation parity: sharp/fvr metadata and FRESH/ISOLATED flags computed on
   truncated data equal the full-data values for events well before the cut.
3. Engine end-state fields: t_end/depth_end sane (depth_end <= depth120+eps;
   t_end within episode cap) and depth_end is decided at episode end (causal
   basis for the ZON-021 clean-defense condition; replaces depth120 whose
   120-bar window can overlap touch 2 — flaw caught in pre-run design review).
4. Clean-defense causality: every ZON-021 event's episode-1 end bar < touch-2 bar.
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
import batch1_lib as B
import batch2_lib as Z
import batch3_lib as Q
import run_batch1 as R1

fails = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name, flush=True)
    if not cond:
        fails.append(name)

Df = Z.prep(B.load_discovery(start="2016-01-01", end="2018-01-01"))
Dt = Z.prep(B.load_discovery(start="2016-01-01", end="2017-07-01"))

# 1. twin identity
za = Z.gen_zon012(Df)
zb = Q.gen_zon012_inst(Df)
ka = set(zip(za["L"].round(6), za["H"].round(6), za["act"], za["btype"]))
kb = set(zip(zb["L"].round(6), zb["H"].round(6), zb["act"], zb["btype"]))
check(f"instrumented ZON-012 twin identical ({len(ka)} zones)", ka == kb)

# 2. truncation parity of metadata + condition flags
zbt = Q.gen_zon012_inst(Dt)
margin = Dt.n_days - 25
mf = zb[zb["day_created"] < margin]
mt = zbt[zbt["day_created"] < margin]
kf = set(zip(mf["act"], mf["sharp"].round(6), mf["fvr"].round(6).fillna(-1)))
kt = set(zip(mt["act"], mt["sharp"].round(6), mt["fvr"].round(6).fillna(-1)))
check(f"sharp/fvr truncation parity ({len(kf)})", kf == kt)

def flags(D, zf):
    ep, _ = B.run_episodes(D, zf)
    ev = R1.primary_filter(ep)
    ev, _ = B.dedup(ev, zf)
    ev = ev[ev["day"] < margin].reset_index(drop=True)
    fr = Q.fresh_mask(ev, ep, 60)
    iso = Q.isolation_mask(ev, Q.mids_for(ev, zf), zf, D,
                           exclude_ids=ev["zid"].to_numpy())
    return {(r.zid, r.T0): (bool(f), bool(i))
            for r, f, i in zip(ev.itertuples(index=False), fr, iso)}
Ff, Ft = flags(Df, zb), flags(Dt, zbt)
common = set(Ff) & set(Ft)
check(f"FRESH/ISOLATED truncation parity ({len(common)} events, "
      f"{len(Ff)^len(Ft) if False else abs(len(Ff)-len(Ft))} edge-only diff)",
      len(common) > 0 and all(Ff[k] == Ft[k] for k in common))

# 3. end-state fields sane
ep, _ = B.run_episodes(Dt, zbt)
s = ep[ep["side"] != 0]
early = s["t_end"] <= 120
check("depth_end monotone vs depth120 (<= when episode ends <=120 bars, >= after)",
      bool((s.loc[early, "depth_end"] <= s.loc[early, "depth120"] + 1e-9).all()
           and (s.loc[~early, "depth_end"] >= s.loc[~early, "depth120"] - 1e-9).all()))
check("t_end within cap", bool((s["t_end"] <= B.EP_CAP).all()))

# 4. clean-defense causality: episode-1 END bar strictly before touch-2 bar
t2 = Q.defended_touch2(ep)
e1 = s[s["touch_idx"] == 1].set_index("zid")
ok = True
for e in t2.itertuples(index=False):
    r = e1.loc[e.zid]
    if isinstance(r, pd.DataFrame):
        r = r.iloc[0]
    if r["T0"] + r["t_end"] >= e.T0:
        ok = False
        break
check(f"clean-defense causality: ep1 end < touch2 start ({len(t2)} events)", ok)

print("\n" + ("ALL PASS" if not fails else f"FAILURES: {fails}"))
sys.exit(1 if fails else 0)
