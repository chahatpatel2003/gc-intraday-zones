#!/usr/bin/env python3
"""Batch-8 Stage C — frozen confirmation of ZON-039..043 on 2020-2021."""
import json, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
for p in ("batch1", "batch2", "batch7"):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", p))
import batch1_lib as B
import batch2_lib as Z
import motifs_lib as M7
import states_lib as SL
import run_batch1 as R1
from run_stage_a import universes, add_btype, paired_c2, run_c2_state

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "batch8"))
SP_Q25, SP_Q75 = 0.000006, 0.000026          # frozen from mining window
FINAL = [("ZON-039", "U5_vaedge", "S03"), ("ZON-040", "U5_vaedge", "S07"),
         ("ZON-041", "U2_compress", "S08"), ("ZON-042", "U5_vaedge", "S08"),
         ("ZON-043", "U2_compress", "S09")]

t0 = time.time()
rng = np.random.default_rng(B.SEED)
D = M7.prep7(B.load_discovery(start="2019-01-01", end="2022-01-01"))
S = SL.build(D)
S.sp_q25, S.sp_q75 = SP_Q25, SP_Q75
d2020 = next(i for i, d in enumerate(D.days) if d >= pd.Timestamp("2020-01-01").date())
pool, cell, _, _ = B.build_c2_pool(D)
for k in list(pool):
    pool[k] = pool[k][D.day[pool[k]] >= d2020]
    if not len(pool[k]):
        del pool[k]
ndc = int(np.isfinite(D.adr[d2020:]).sum())
print(f"confirm bars={len(D.ts):,} d2020={d2020} days={ndc} [{time.time()-t0:.0f}s]", flush=True)

U = universes(D)
n = len(D.ts)
allbars = np.arange(n)
need_states = sorted({s for _, _, s in FINAL})
donor_states = {s: (SL.flags(S, allbars, np.full(n, 1), np.full(n, 1))[s],
                    SL.flags(S, allbars, np.full(n, -1), np.full(n, -1))[s])
                for s in need_states}
znull = pd.read_csv(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "nullbench", "zone_null_log.csv")))
nd1 = znull["d1"].dropna().to_numpy(); nd2 = znull["d2"].dropna().to_numpy()

cacheU = {}
res = {}
for zid, u, s in FINAL:
    tp = time.time()
    if u not in cacheU:
        zones = U[u]
        zones = zones[zones["day_created"] >= d2020].reset_index(drop=True)
        ep, _ = B.run_episodes(D, zones)
        ev, _ = B.dedup(R1.primary_filter(ep), zones)
        ev = add_btype(ev.reset_index(drop=True), zones)
        ev["nf"] = B.netfav(ev)
        sh, diag = Z.gen_shadows_v2(zones, D, zones)
        eps, _ = B.run_episodes(D, sh, first_only=True)
        c1, _ = B.dedup(R1.primary_filter(eps), sh)
        c1 = add_btype(c1.reset_index(drop=True), sh)
        c1["nf"] = B.netfav(c1)
        fl_ev = SL.flags(S, ev["T0"].to_numpy(), ev["btype"].to_numpy(), ev["side"].to_numpy())
        fl_c1 = SL.flags(S, c1["T0"].to_numpy(), c1["btype"].to_numpy(), c1["side"].to_numpy())
        cacheU[u] = (zones, ev, c1, fl_ev, fl_c1, diag)
    zones, ev, c1, fl_ev, fl_c1, diag = cacheU[u]
    eon = ev[fl_ev[s]].reset_index(drop=True)
    con = c1[fl_c1[s]].reset_index(drop=True)
    evv = eon.dropna(subset=["nf"]); cvv = con.dropna(subset=["nf"])
    d1, ci1 = (B.day_boot(rng, B.by_day(evv, "nf"), B.by_day(cvv, "nf"))
               if len(cvv) >= 30 else (np.nan, [np.nan, np.nan]))
    on_sup, on_dem = donor_states[s]
    c2s, short = run_c2_state(D, eon, zones, pool, cell, rng, on_sup, on_dem)
    d2, ci2, yearly, npair = paired_c2(rng, evv, c2s)
    meanA = ev.dropna(subset=["nf"])["nf"].mean()
    cma = float(evv["nf"].mean() - meanA)
    counts = eon.groupby("day").size().reindex(range(d2020, D.n_days), fill_value=0)
    counts = counts[np.isfinite(D.adr[d2020:])]
    res[zid] = {"u": u, "s": s, "N": int(len(eon)), "ev_day": round(len(eon) / ndc, 3),
        "d1": round(float(d1), 4), "ci1": [round(float(x), 4) for x in ci1],
        "d2": round(float(d2), 4), "ci2": [round(float(x), 4) for x in ci2],
        "C_minus_A": round(cma, 4),
        "min_delta": round(float(min(d1, d2, cma)), 4),
        "yearly_c2": yearly, "c1_n": int(len(cvv)), "c2_pairs": int(npair),
        "c2_short": int(short), "spz": diag["shadows_per_zone"],
        "noctl": round(diag["zones_without_control"] / max(len(zones), 1), 3),
        "null_pct_d1": round(float(np.mean(nd1 < d1)) * 100, 1),
        "null_pct_d2": round(float(np.mean(nd2 < d2)) * 100, 1),
        "day_dist": {"0": round(float((counts == 0).mean()), 3),
                     "1": round(float((counts == 1).mean()), 3),
                     "2": round(float((counts == 2).mean()), 3),
                     "3": round(float((counts == 3).mean()), 3),
                     "4": round(float((counts == 4).mean()), 3),
                     "5+": round(float((counts >= 5).mean()), 3)},
        "ambig": round(float(eon["ambig"].mean()), 3)}
    hurdle = (d1 >= 0.02 and d2 >= 0.02 and cma > 0
              and all(v > 0 for v in yearly.values()) and len(yearly) >= 2)
    res[zid]["survives"] = bool(hurdle)
    print(f"{zid} {u}x{s}: {json.dumps(res[zid])[:450]} [{time.time()-tp:.0f}s]", flush=True)

with open(f"{OUT}/confirm_b8.json", "w") as f:
    json.dump(res, f, indent=1, default=float)
print(f"TOTAL {time.time()-t0:.0f}s")
