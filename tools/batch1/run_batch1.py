#!/usr/bin/env python3
"""Batch-1 runner — discovery 2016-2021 GC only. Writes aurum/batch1/."""
import json, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import batch1_lib as B

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "batch1"))
os.makedirs(OUT, exist_ok=True)
SMOKE = "--smoke" in sys.argv

FAMS = ["ZON-001", "ZON-002", "ZON-003", "ZON-004", "ZON-005", "ZON-006"]
GENS = {"ZON-001": B.gen_zon001, "ZON-002": B.gen_zon002, "ZON-003": B.gen_zon003,
        "ZON-004": B.gen_zon004, "ZON-005": B.gen_zon005, "ZON-006": B.gen_zon006}


def primary_filter(ep):
    return ep[(ep["touch_idx"] == 1) & (ep["side"] != 0) & (ep["stratum"] == "pre")]


def main():
    t0 = time.time()
    rng = np.random.default_rng(B.SEED)
    D = B.load_discovery(start="2019-01-01" if SMOKE else "2016-01-01",
                         end="2020-01-01" if SMOKE else "2022-01-01")
    print(f"bars={len(D.ts):,} days={D.n_days} [{time.time()-t0:.0f}s]", flush=True)
    pool, cell, ter, spq = B.build_c2_pool(D)

    stats = {}
    all_events = []
    all_zone_frames = []
    all_ep_dedup_all = []
    for fam in FAMS:
        tf0 = time.time()
        zones, _ = GENS[fam](D)
        ep, roll_killed = B.run_episodes(D, zones, first_only=False)
        ep.to_parquet(f"{OUT}/episodes_{fam}.parquet")
        prim = primary_filter(ep)
        events, _ = B.dedup(prim, zones)
        # all-episode dedup (any touch index) for density
        sided = ep[ep["side"] != 0]
        ev_all, _ = B.dedup(sided, zones)

        shadows = B.gen_shadows(zones)
        eps, _ = B.run_episodes(D, shadows, first_only=True)
        eps_p = primary_filter(eps)
        c1, _ = B.dedup(eps_p, shadows)
        c1.to_parquet(f"{OUT}/episodes_{fam}_c1.parquet")

        c2, c2_short = B.run_c2(D, events, zones, pool, cell, rng, K=5)
        c2.to_parquet(f"{OUT}/episodes_{fam}_c2.parquet")
        events.to_parquet(f"{OUT}/events_{fam}.parquet")

        s = family_stats(D, fam, zones, ep, events, ev_all, shadows, c1, c2,
                         c2_short, roll_killed, rng)
        stats[fam] = s
        all_events.append(events.assign(fam=fam))
        all_ep_dedup_all.append(ev_all.assign(fam=fam))
        all_zone_frames.append(zones)
        print(f"{fam}: zones={len(zones)} ep={len(ep)} prim={len(events)} "
              f"c1={len(c1)} c2={len(c2)} [{time.time()-tf0:.0f}s]", flush=True)

    # cross-family clusters
    zall = pd.concat(all_zone_frames, ignore_index=True)
    evp = pd.concat(all_events, ignore_index=True)
    eva = pd.concat(all_ep_dedup_all, ignore_index=True)
    cl_p = B.cross_clusters(evp, zall)
    cl_a = B.cross_clusters(eva, zall)
    cl_a.to_parquet(f"{OUT}/interaction_clusters_all.parquet")
    xstats = cluster_stats(D, cl_p, cl_a)
    stats["cross_family"] = xstats

    with open(f"{OUT}/batch1_stats.json", "w") as f:
        json.dump(stats, f, indent=1, default=float)
    print(f"TOTAL {time.time()-t0:.0f}s")
    return stats


def family_stats(D, fam, zones, ep, events, ev_all, shadows, c1, c2,
                 c2_short, roll_killed, rng):
    s = {"zones": int(len(zones)), "roll_killed": int(roll_killed)}
    nd = int(np.isfinite(D.adr).sum())
    s["days"] = nd
    s["zones_per_day"] = round(len(zones) / nd, 2)
    # active zones/day
    alive = np.zeros(D.n_days + 1)
    d0 = np.searchsorted(D.ts[D.day_first], zones["act"].to_numpy(), "right") - 1
    d1 = np.searchsorted(D.ts[D.day_first], zones["exp"].to_numpy(), "right") - 1
    for a, b in zip(d0, np.minimum(d1, D.n_days - 1)):
        if a >= 0:
            alive[a] += 1; alive[b + 1] -= 1
    s["active_per_day_mean"] = round(float(np.cumsum(alive)[:D.n_days][np.isfinite(D.adr)].mean()), 2)
    s["touched_per_day"] = round(len(ev_all) / nd, 2)
    s["prim_events_per_day"] = round(len(events) / nd, 3)

    W = events["W"] / events["adr"]
    s["width_pts"] = [round(float(events["W"].quantile(q)), 2) for q in (0.25, 0.5, 0.75)]
    s["width_adr"] = [round(float(W.quantile(q)), 3) for q in (0.25, 0.5, 0.75)]
    s["age_min_median"] = round(float(events["age_min"].median()), 1)
    s["N_primary"] = int(len(events))
    s["N_raw_first"] = int((ep["touch_idx"] == 1).sum())
    s["inside_at_activation"] = int((ep["side"] == 0).sum())
    s["ambig_rate"] = round(float(events["ambig"].mean()), 4) if len(events) else None
    s["trunc_FE60"] = int(events["FE60"].isna().sum())

    # touch strata
    tb = ep[ep["side"] != 0].copy()
    tb["bucket"] = np.where(tb["stratum"] == "retest", "retest",
                            np.where(tb["touch_idx"] == 1, "t1",
                                     np.where(tb["touch_idx"] == 2, "t2", "t3+")))
    s["touch_buckets"] = {k: [int(len(g)), round(float(B.netfav(g).mean()), 4)]
                          for k, g in tb.groupby("bucket")}

    # metric profile (primary events)
    prof = {}
    for h in B.HORIZONS:
        fe = events[f"FE{h}"] / events["adr"]; ae = events[f"AE{h}"] / events["adr"]
        prof[h] = {"FE_adr": round(float(fe.mean()), 4), "AE_adr": round(float(ae.mean()), 4),
                   "FE_pts": round(float(events[f"FE{h}"].mean()), 3),
                   "AE_pts": round(float(events[f"AE{h}"].mean()), 3),
                   "FE_W": round(float((events[f"FE{h}"] / events["W"]).mean()), 3),
                   "AE_W": round(float((events[f"AE{h}"] / events["W"]).mean()), 3)}
    s["profile"] = prof
    s["rejW_rate"] = round(float(events["rejW"].mean()), 4)
    s["rejA_rate"] = round(float(events["rejA"].mean()), 4)
    s["trav_rate"] = round(float(events["trav120"].mean()), 4)
    s["depth_med"] = round(float(events["depth120"].median()), 3)
    s["reclaim_rate"] = (round(float(events["reclaim"].dropna().mean()), 4)
                         if events["reclaim"].notna().any() else None)
    sp = events["t_rejA"].dropna()
    s["speed_med_min"] = round(float(sp.median()), 1) if len(sp) else None
    s["sessions"] = {int(k): [int(len(g)), round(float(B.netfav(g).mean()), 4)]
                     for k, g in events.groupby("sess")}

    # ---- controls
    ev_v = events.assign(nf=B.netfav(events)).dropna(subset=["nf"])
    c1_v = c1.assign(nf=B.netfav(c1)).dropna(subset=["nf"])
    d_c1, ci_c1 = B.day_boot(rng, B.by_day(ev_v, "nf"), B.by_day(c1_v, "nf"))
    s["C1"] = {"n": int(len(c1_v)), "delta": round(float(d_c1), 4),
               "ci": [round(float(x), 4) for x in ci_c1],
               "shadow_unavailable_rate": round(1 - len(shadows) / (4 * len(zones)), 3)}
    # paired C2
    c2 = c2.assign(nf=(c2["FE60"] - c2["AE60"]) / c2["adr"])
    don = c2.dropna(subset=["nf"]).groupby("event_zid")["nf"].mean()
    ev_k = ev_v.set_index("zid")
    common = ev_k.index.intersection(don.index)
    paired = ev_k.loc[common, "nf"] - don.loc[common]
    pday = ev_k.loc[common, "day"]
    pd_map = {d: paired[pday == d].to_numpy() for d in pday.unique()}
    d_c2, ci_c2 = B.day_boot(rng, None, None, paired=pd_map)
    s["C2"] = {"n_events_paired": int(len(common)), "n_donor_rows": int(len(c2)),
               "delta": round(float(d_c2), 4), "ci": [round(float(x), 4) for x in ci_c2],
               "shortfall_events": int(c2_short)}
    # secondary deltas (point)
    s["secondary"] = {
        "dFE60_adr_c2": round(float((ev_k.loc[common, "FE60"] / ev_k.loc[common, "adr"]).mean()
                                    - (c2.dropna(subset=["FE60"]).groupby("event_zid")["FE60"].mean()
                                       / ev_k.loc[common, "adr"]).loc[common].mean()), 4)
        if len(common) else None,
        "rejA_c1": round(float(events["rejA"].mean() - c1["rejA"].mean()), 4),
        "rejA_c2": round(float(events["rejA"].mean() - c2["rejA"].mean()), 4),
        "trav_c1": round(float(events["trav120"].mean() - c1["trav120"].mean()), 4),
        "trav_c2": round(float(events["trav120"].mean() - c2["trav120"].mean()), 4),
    }
    # yearly stability vs C2 (paired point estimates)
    yearly = {}
    yr = ev_k.loc[common, "year"]
    for y, g in paired.groupby(yr):
        if len(g) >= 30:
            yearly[int(y)] = round(float(g.mean()), 4)
    s["yearly_c2"] = yearly
    s["classification"] = classify(s, yearly)
    return s


def classify(s, yearly):
    N = s["N_primary"]
    if N < 300:
        return "INSUFFICIENT DATA"
    d1, ci1 = s["C1"]["delta"], s["C1"]["ci"]
    d2, ci2 = s["C2"]["delta"], s["C2"]["ci"]
    pos_share = (np.mean([v > 0 for v in yearly.values()]) if yearly else 0.0)
    both_ci = ci1[0] > 0 and ci2[0] > 0
    both_mat = d1 >= 0.05 and d2 >= 0.05
    if both_ci and both_mat and len(yearly) >= 4 and pos_share >= 0.8:
        return "STRONG LOCATION EVIDENCE"
    one_ci = (ci1[0] > 0) != (ci2[0] > 0)
    other_pos = (d2 > 0) if ci1[0] > 0 else (d1 > 0)
    if pos_share >= 0.6 and ((both_ci and not both_mat) or (one_ci and other_pos)):
        return "PROMISING"
    return "NO LOCATION EDGE"


def cluster_stats(D, cl_p, cl_a):
    nd = int(np.isfinite(D.adr).sum())
    x = {}
    for name, cl in (("primary", cl_p), ("all_touches", cl_a)):
        g = cl.groupby("interaction_cluster_id")
        nfam = g["fam"].nunique()
        x[name] = {
            "episodes": int(len(cl)),
            "clusters": int(g.ngroups),
            "clusters_per_day": round(g.ngroups / nd, 2),
            "multi_family_share": round(float((nfam >= 2).mean()), 3),
            "mean_members": round(float(g.size().mean()), 2),
        }
        pairs = {}
        for _, grp in g:
            fams = sorted(grp["fam"].unique())
            if len(fams) >= 2:
                for i in range(len(fams)):
                    for j in range(i + 1, len(fams)):
                        k = f"{fams[i]}+{fams[j]}"
                        pairs[k] = pairs.get(k, 0) + 1
        x[name]["top_pairs"] = dict(sorted(pairs.items(), key=lambda kv: -kv[1])[:8])
    per_day = cl_a.groupby("interaction_cluster_id")["day"].first().value_counts()
    counts = per_day.reindex(range(D.n_days), fill_value=0)
    counts = counts[np.isfinite(D.adr)]
    x["day_distribution"] = {"0": round(float((counts == 0).mean()), 3),
                             "1": round(float((counts == 1).mean()), 3),
                             "2-5": round(float(((counts >= 2) & (counts <= 5)).mean()), 3),
                             ">5": round(float((counts > 5).mean()), 3),
                             "median_per_day": float(counts.median())}
    return x


if __name__ == "__main__":
    main()
