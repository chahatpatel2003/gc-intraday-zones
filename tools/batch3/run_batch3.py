#!/usr/bin/env python3
"""Batch-3 runner — conditioned lifecycle/quality hypotheses on discovery 2016-2021."""
import json, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
import batch1_lib as B
import batch2_lib as Z
import batch3_lib as Q
import run_batch1 as R1

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "batch3"))
os.makedirs(OUT, exist_ok=True)


def cond_key(df):
    return set(zip(df["zid"], df["T0"]))


def stream_stats(events, zones, D):
    per = events.groupby("day").size()
    counts = per.reindex(range(D.n_days), fill_value=0)
    counts = counts[np.isfinite(D.adr)]
    zm = zones.set_index("zid")
    gaps = []
    for d, g in events.groupby("day"):
        a = D.adr[int(d)]
        if len(g) < 2 or not np.isfinite(a):
            continue
        mids = np.sort((zm.loc[g["zid"], "L"].to_numpy()
                        + zm.loc[g["zid"], "H"].to_numpy()) / 2)
        gaps.extend((np.diff(mids) / a).tolist())
    return {"events_per_day": round(float(counts.mean()), 3),
            "day_dist": {"0": round(float((counts == 0).mean()), 3),
                         "1": round(float((counts == 1).mean()), 3),
                         "2-5": round(float(((counts >= 2) & (counts <= 5)).mean()), 3),
                         ">5": round(float((counts > 5).mean()), 3)},
            "nn_gap_adr_median": round(float(np.median(gaps)), 3) if gaps else None}


def main():
    t0 = time.time()
    rng = np.random.default_rng(B.SEED)
    D = Z.prep(B.load_discovery())
    pool, cell, _, _ = B.build_c2_pool(D)
    print(f"bars={len(D.ts):,} days={D.n_days} [{time.time()-t0:.0f}s]", flush=True)

    z12 = Q.gen_zon012_inst(D)
    ep12, _ = B.run_episodes(D, z12)
    sh12, diag12 = Z.gen_shadows_v2(z12, D, z12)
    eps12, _ = B.run_episodes(D, sh12, first_only=False)
    z13 = Z.gen_zon013(D)
    ep13, _ = B.run_episodes(D, z13)
    sh13, diag13 = Z.gen_shadows_v2(z13, D, z13)
    eps13, _ = B.run_episodes(D, sh13, first_only=True)
    print(f"parents: z12={len(z12)} ep12={len(ep12)} sh12={len(sh12)} eps12={len(eps12)} "
          f"| z13={len(z13)} ep13={len(ep13)} [{time.time()-t0:.0f}s]", flush=True)

    prim12 = R1.primary_filter(ep12).reset_index(drop=True)
    prim12s = R1.primary_filter(eps12).reset_index(drop=True)
    prim13 = R1.primary_filter(ep13).reset_index(drop=True)
    prim13s = R1.primary_filter(eps13).reset_index(drop=True)

    # frozen condition masks
    fr12 = Q.fresh_mask(prim12, ep12, 60)
    fr12s = Q.fresh_mask(prim12s, eps12, 60)
    iso12 = Q.isolation_mask(prim12, Q.mids_for(prim12, z12), z12, D,
                             exclude_ids=prim12["zid"].to_numpy())
    iso12s = Q.isolation_mask(prim12s, Q.mids_for(prim12s, sh12), z12, D,
                              exclude_ids=np.array(Q.shadow_parent(prim12s["zid"])))
    sharp_ids = set(z12.loc[z12["sharp"] >= 2.0, "zid"])
    shp12 = prim12["zid"].isin(sharp_ids).to_numpy()
    shp12s = pd.Series(Q.shadow_parent(prim12s["zid"])).isin(sharp_ids).to_numpy()
    fr13 = Q.fresh_mask(prim13, ep13, 120)
    fr13s = Q.fresh_mask(prim13s, eps13, 120)
    iso13 = Q.isolation_mask(prim13, Q.mids_for(prim13, z13), z13, D,
                             exclude_ids=prim13["zid"].to_numpy())
    iso13s = Q.isolation_mask(prim13s, Q.mids_for(prim13s, sh13), z13, D,
                              exclude_ids=np.array(Q.shadow_parent(prim13s["zid"])))
    t2_12 = Q.defended_touch2(ep12)
    t2_12s = Q.defended_touch2(eps12)

    HYPS = {
        "ZON-016": (prim12[fr12], prim12s[fr12s], z12, ep12, sh12, z12),
        "ZON-017": (prim12[iso12], prim12s[iso12s], z12, ep12, sh12, z12),
        "ZON-018": (prim12[shp12], prim12s[shp12s],
                    z12[z12["sharp"] >= 2.0], ep12, sh12, z12),
        "ZON-019": (prim12[fr12 & iso12 & shp12], prim12s[fr12s & iso12s & shp12s],
                    z12[z12["sharp"] >= 2.0], ep12, sh12, z12),
        "ZON-020": (prim13[fr13 & iso13], prim13s[fr13s & iso13s], z13, ep13, sh13, z13),
        "ZON-021": (t2_12, t2_12s, z12, ep12, sh12, z12),
    }

    stats = {"parents": {"z12_zones": int(len(z12)), "z12_prim": int(len(prim12)),
                         "z12_sharp_zones": int((z12["sharp"] >= 2.0).sum()),
                         "z13_zones": int(len(z13)), "z13_prim": int(len(prim13)),
                         "c1v2_diag_012": diag12, "c1v2_diag_013": diag13}}
    keys = {}
    for hyp, (rev, sev, zstat, ep_par, shf, zpar) in HYPS.items():
        th = time.time()
        events, _ = B.dedup(rev.reset_index(drop=True), zpar if hyp != "ZON-021" else zpar)
        c1ev, _ = B.dedup(sev.reset_index(drop=True), shf)
        events = events.assign(fam=hyp)
        c1ev = c1ev.assign(fam=hyp)
        c2, c2_short = B.run_c2(D, events, zpar, pool, cell, rng, K=5)
        s = R1.family_stats(D, hyp, zstat, ep_par, events, events, shf, c1ev, c2,
                            c2_short, 0, rng)
        s["stream"] = stream_stats(events, zpar, D)
        s["share_of_parent"] = round(len(events) /
                                     max(len(prim13 if hyp == "ZON-020" else prim12), 1), 3)
        stats[hyp] = s
        keys[hyp] = cond_key(events)
        events.to_parquet(f"{OUT}/events_{hyp}.parquet")
        c1ev.to_parquet(f"{OUT}/c1_{hyp}.parquet")
        c2.to_parquet(f"{OUT}/c2_{hyp}.parquet")
        print(f"{hyp}: N={len(events)} c1={len(c1ev)} c2={len(c2)} "
              f"class={s['classification']} [{time.time()-th:.0f}s]", flush=True)

    # conditioned-set overlaps (within z12 hypotheses)
    ov = {}
    ids = ["ZON-016", "ZON-017", "ZON-018", "ZON-019", "ZON-021"]
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = keys[ids[i]], keys[ids[j]]
            ov[f"{ids[i]}&{ids[j]}"] = int(len(a & b))
    stats["event_set_overlaps"] = ov

    # descriptive feature tables (post-hoc labeled; no hypothesis built from them)
    all_b2 = {f: Z.GENS[f](D) for f in ("ZON-008", "ZON-009", "ZON-011", "ZON-013",
                                        "ZON-015")}
    ft12 = Q.feature_table(D, z12, ep12, prim12.assign(fam="ZON-012"), all_b2)
    ft12.to_parquet(f"{OUT}/features_z012.parquet")
    feats = ["age_min", "w_adr", "prior_inside", "dep60_adr", "clean_dep",
             "dist_before_touch_adr", "approach_speed_adr", "sharp", "fvr",
             "confluence_n", "sess"]
    stats["feature_bins_z012_descriptive"] = Q.binned_report(ft12, feats)

    strong = [h for h in HYPS if stats[h]["classification"].startswith("STRONG")]
    promising = [h for h in HYPS if stats[h]["classification"].startswith("PROMISING")]
    stats["strong_frequency"] = {
        "strong": strong, "promising": promising,
        "strong_events_per_day": round(sum(stats[h]["stream"]["events_per_day"]
                                           for h in strong), 3),
        "strong_plus_promising_per_day": round(sum(stats[h]["stream"]["events_per_day"]
                                                   for h in strong + promising), 3)}
    with open(f"{OUT}/batch3_stats.json", "w") as f:
        json.dump(stats, f, indent=1, default=float)
    print(f"TOTAL {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
