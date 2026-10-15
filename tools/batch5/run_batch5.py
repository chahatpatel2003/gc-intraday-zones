#!/usr/bin/env python3
"""Batch-5 runner — discovery 2016-2021 GC only. Writes aurum/batch5/."""
import json, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch3"))
import batch1_lib as B
import batch2_lib as Z
import batch5_lib as F
import run_batch1 as R1
import run_batch3 as R3

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "batch5"))
os.makedirs(OUT, exist_ok=True)
FAMS = list(F.GENS5)


def main():
    t0 = time.time()
    rng = np.random.default_rng(B.SEED)
    D = F.prep5(B.load_discovery())
    pool, cell, _, _ = B.build_c2_pool(D)
    print(f"bars={len(D.ts):,} days={D.n_days} [{time.time()-t0:.0f}s]", flush=True)

    zones_all = {}
    for fam in FAMS:
        tg = time.time()
        zones_all[fam] = F.GENS5[fam](D)
        print(f"gen {fam}: {len(zones_all[fam])} zones [{time.time()-tg:.0f}s]", flush=True)

    stats, all_events, all_evall = {}, [], []
    for fam in FAMS:
        tf0 = time.time()
        zones = zones_all[fam]
        if not len(zones):
            stats[fam] = {"classification": "INVALID (no zones)", "N_primary": 0}
            continue
        ep, roll_killed = B.run_episodes(D, zones)
        ep.to_parquet(f"{OUT}/episodes_{fam}.parquet")
        prim = R1.primary_filter(ep)
        events, _ = B.dedup(prim, zones)
        ev_all, _ = B.dedup(ep[ep["side"] != 0], zones)
        shadows, diag = Z.gen_shadows_v2(zones, D, zones)
        eps, _ = B.run_episodes(D, shadows, first_only=True)
        c1, _ = B.dedup(R1.primary_filter(eps), shadows)
        c2, c2_short = B.run_c2(D, events, zones, pool, cell, rng, K=5)
        events.to_parquet(f"{OUT}/events_{fam}.parquet")
        c1.to_parquet(f"{OUT}/c1_{fam}.parquet")
        c2.to_parquet(f"{OUT}/c2_{fam}.parquet")
        s = R1.family_stats(D, fam, zones, ep, events, ev_all, shadows, c1, c2,
                            c2_short, roll_killed, rng)
        s["C1"]["v2_diag"] = diag
        s["spacing"] = Z.spacing_stats(zones, D)
        s["stream"] = R3.stream_stats(events, zones, D)
        stats[fam] = s
        all_events.append(events.assign(fam=fam))
        all_evall.append(ev_all.assign(fam=fam))
        print(f"{fam}: zones={len(zones)} ep={len(ep)} prim={len(events)} "
              f"c1={len(c1)} (spz {diag['shadows_per_zone']}, noctl "
              f"{diag['zones_without_control']}) c2={len(c2)} "
              f"class={s['classification']} [{time.time()-tf0:.0f}s]", flush=True)

    occupied = pd.concat([z for z in zones_all.values() if len(z)], ignore_index=True)
    evp = pd.concat(all_events, ignore_index=True)
    eva = pd.concat(all_evall, ignore_index=True)
    cl_p = B.cross_clusters(evp, occupied)
    cl_a = B.cross_clusters(eva, occupied)
    cl_a.to_parquet(f"{OUT}/interaction_clusters_all.parquet")
    stats["cross_family"] = R1.cluster_stats(D, cl_p, cl_a)

    strong = [f for f in FAMS if stats[f].get("classification", "").startswith("STRONG")]
    promising = [f for f in FAMS if stats[f].get("classification", "").startswith("PROMISING")]
    stats["strong_frequency"] = {
        "strong": strong, "promising": promising,
        "strong_per_day": round(sum(stats[f]["stream"]["events_per_day"] for f in strong), 3),
        "strong_plus_promising_per_day": round(sum(stats[f]["stream"]["events_per_day"]
                                                   for f in strong + promising), 3),
        "raw_per_day": round(sum(stats[f]["stream"]["events_per_day"]
                                 for f in FAMS if "stream" in stats[f]), 2)}
    with open(f"{OUT}/batch5_stats.json", "w") as f:
        json.dump(stats, f, indent=1, default=float)
    print(f"TOTAL {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
