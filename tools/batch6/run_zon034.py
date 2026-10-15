#!/usr/bin/env python3
"""ZON-034 runner — QML control-repair follow-up, discovery 2016-2021."""
import json, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch3"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch5"))
import batch1_lib as B
import batch2_lib as Z
import batch5_lib as F
import zon034_lib as Q34
import run_batch1 as R1
import run_batch3 as R3

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "batch6"))
os.makedirs(OUT, exist_ok=True)

t0 = time.time()
rng = np.random.default_rng(B.SEED)
D = F.prep5(B.load_discovery())
pool, cell, _, _ = B.build_c2_pool(D)

zones, ddiag, _ = Q34.gen_zon034(D)
print(f"dedup: {ddiag}", flush=True)
ep, roll_killed = B.run_episodes(D, zones)
prim = R1.primary_filter(ep)
events, _ = B.dedup(prim, zones)
ev_all, _ = B.dedup(ep[ep["side"] != 0], zones)
shadows, cdiag = Z.gen_shadows_v2(zones, D, zones)
eps, _ = B.run_episodes(D, shadows, first_only=True)
c1, _ = B.dedup(R1.primary_filter(eps), shadows)
c2, c2_short = B.run_c2(D, events, zones, pool, cell, rng, K=5)
events.to_parquet(f"{OUT}/events_ZON-034.parquet")
c1.to_parquet(f"{OUT}/c1_ZON-034.parquet")
c2.to_parquet(f"{OUT}/c2_ZON-034.parquet")

s = R1.family_stats(D, "ZON-034", zones, ep, events, ev_all, shadows, c1, c2,
                    c2_short, roll_killed, rng)
s["C1"]["v2_diag"] = cdiag
s["dedup_diag"] = ddiag
s["spacing"] = Z.spacing_stats(zones, D)
s["stream"] = R3.stream_stats(events, zones, D)

# frozen availability gate (ZON-034_SPEC.md)
avail_ok = (cdiag["shadows_per_zone"] >= 2.0
            and cdiag["zones_without_control"] / max(len(zones), 1) <= 0.20)
s["availability_gate"] = {"healthy": bool(avail_ok),
                          "shadows_per_zone": cdiag["shadows_per_zone"],
                          "uncontrolled_share": round(cdiag["zones_without_control"]
                                                      / max(len(zones), 1), 3)}
if not avail_ok:
    s["classification"] = "UNRESOLVED/CONTROL FAILURE"
with open(f"{OUT}/zon034_stats.json", "w") as f:
    json.dump(s, f, indent=1, default=float)
print(f"zones={len(zones)} prim={len(events)} c1={len(c1)} "
      f"(spz {cdiag['shadows_per_zone']}, noctl {cdiag['zones_without_control']}) "
      f"c2={len(c2)} gate_healthy={avail_ok} class={s['classification']} "
      f"[{time.time()-t0:.0f}s]")
