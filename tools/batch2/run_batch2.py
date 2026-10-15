#!/usr/bin/env python3
"""Batch-2 runner — discovery 2016-2021 GC only. Writes aurum/batch2/."""
import json, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
import batch1_lib as B
import batch2_lib as Z
import run_batch1 as R1

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "batch2"))
os.makedirs(OUT, exist_ok=True)
SMOKE = "--smoke" in sys.argv
FAMS = list(Z.GENS)


def main():
    t0 = time.time()
    rng = np.random.default_rng(B.SEED)
    D = B.load_discovery(start="2019-01-01" if SMOKE else "2016-01-01",
                         end="2020-01-01" if SMOKE else "2022-01-01")
    Z.prep(D)
    print(f"bars={len(D.ts):,} days={D.n_days} [{time.time()-t0:.0f}s]", flush=True)
    pool, cell, _, _ = B.build_c2_pool(D)

    zones_all = {}
    for fam in FAMS:
        tg = time.time()
        zones_all[fam] = Z.GENS[fam](D)
        print(f"gen {fam}: {len(zones_all[fam])} zones [{time.time()-tg:.0f}s]", flush=True)
    occupied = pd.concat(zones_all.values(), ignore_index=True)

    stats, all_events, all_evall = {}, [], []
    for fam in FAMS:
        tf0 = time.time()
        zones = zones_all[fam]
        ep, roll_killed = B.run_episodes(D, zones)
        ep.to_parquet(f"{OUT}/episodes_{fam}.parquet")
        prim = R1.primary_filter(ep)
        events, _ = B.dedup(prim, zones)
        ev_all, _ = B.dedup(ep[ep["side"] != 0], zones)
        shadows, diag = Z.gen_shadows_v2(zones, D, zones)   # v1.3: same-family exclusion
        eps, _ = B.run_episodes(D, shadows, first_only=True)
        c1, _ = B.dedup(R1.primary_filter(eps), shadows)
        c1.to_parquet(f"{OUT}/episodes_{fam}_c1.parquet")
        c2, c2_short = B.run_c2(D, events, zones, pool, cell, rng, K=5)
        c2.to_parquet(f"{OUT}/episodes_{fam}_c2.parquet")
        events.to_parquet(f"{OUT}/events_{fam}.parquet")

        s = R1.family_stats(D, fam, zones, ep, events, ev_all, shadows, c1, c2,
                            c2_short, roll_killed, rng)
        s["C1"]["v2_diag"] = diag
        s["spacing"] = Z.spacing_stats(zones, D)
        if fam == "ZON-015":
            # continuation framing: NetAdv = -NetFav; deltas/CIs/yearly negate
            cont = {"delta": round(-s["C1"]["delta"], 4),
                    "ci": [round(-s["C1"]["ci"][1], 4), round(-s["C1"]["ci"][0], 4)]}
            cont2 = {"delta": round(-s["C2"]["delta"], 4),
                     "ci": [round(-s["C2"]["ci"][1], 4), round(-s["C2"]["ci"][0], 4)]}
            ycont = {y: round(-v, 4) for y, v in s["yearly_c2"].items()}
            sv = dict(s)
            sv["C1"] = {**s["C1"], **cont}
            sv["C2"] = {**s["C2"], **cont2}
            s["continuation_view"] = {"C1": cont, "C2": cont2, "yearly_c2": ycont,
                                      "classification": R1.classify(sv, ycont)
                                      + " (EXPLORATORY, Batch-1-inspired)"}
            s["classification"] = s["continuation_view"]["classification"]
        stats[fam] = s
        all_events.append(events.assign(fam=fam))
        all_evall.append(ev_all.assign(fam=fam))
        print(f"{fam}: zones={len(zones)} ep={len(ep)} prim={len(events)} "
              f"c1={len(c1)} (spz {diag['shadows_per_zone']}, noctl "
              f"{diag['zones_without_control']}) c2={len(c2)} "
              f"[{time.time()-tf0:.0f}s]", flush=True)

    evp = pd.concat(all_events, ignore_index=True)
    eva = pd.concat(all_evall, ignore_index=True)
    cl_p = B.cross_clusters(evp, occupied)
    cl_a = B.cross_clusters(eva, occupied)
    cl_a.to_parquet(f"{OUT}/interaction_clusters_all.parquet")
    stats["cross_family"] = R1.cluster_stats(D, cl_p, cl_a)

    strong = [f for f in FAMS if stats[f]["classification"].startswith("STRONG")]
    promising = [f for f in FAMS if stats[f]["classification"].startswith("PROMISING")]
    stats["strong_frequency"] = {
        "strong_families": strong,
        "promising_families": promising,
        "strong_interactions_per_day": round(sum(stats[f]["prim_events_per_day"]
                                                 for f in strong), 3),
        "strong_plus_promising_per_day": round(sum(stats[f]["prim_events_per_day"]
                                                   for f in strong + promising), 3),
        "raw_candidate_interactions_per_day": round(sum(stats[f]["prim_events_per_day"]
                                                        for f in FAMS), 2)}
    with open(f"{OUT}/batch2_stats.json", "w") as f:
        json.dump(stats, f, indent=1, default=float)
    print(f"TOTAL {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
