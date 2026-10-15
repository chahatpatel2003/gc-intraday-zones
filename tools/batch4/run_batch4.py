#!/usr/bin/env python3
"""Batch-4 runner — attribution hypotheses ZON-022..025 on discovery 2016-2021."""
import json, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch3"))
import batch1_lib as B
import batch2_lib as Z
import batch3_lib as Q
import batch4_lib as A
import run_batch1 as R1
import run_batch3 as R3

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "batch4"))
os.makedirs(OUT, exist_ok=True)
POOL = ["ZON-001", "ZON-008", "ZON-009", "ZON-011", "ZON-013", "ZON-015"]


def main():
    t0 = time.time()
    rng = np.random.default_rng(B.SEED)
    D = Z.prep(B.load_discovery())
    pool, cell, _, _ = B.build_c2_pool(D)
    print(f"bars={len(D.ts):,} days={D.n_days} [{time.time()-t0:.0f}s]", flush=True)

    z12 = Q.gen_zon012_inst(D)
    ep12, _ = B.run_episodes(D, z12)
    prim12 = R1.primary_filter(ep12).reset_index(drop=True)
    sh12, diag12 = Z.gen_shadows_v2(z12, D, z12)
    eps12, _ = B.run_episodes(D, sh12, first_only=True)
    prim12s = R1.primary_filter(eps12).reset_index(drop=True)

    prim12["iso"] = Q.isolation_mask(prim12, Q.mids_for(prim12, z12), z12, D,
                                     exclude_ids=prim12["zid"].to_numpy())
    prim12s["iso"] = Q.isolation_mask(prim12s, Q.mids_for(prim12s, sh12), z12, D,
                                      exclude_ids=np.array(Q.shadow_parent(prim12s["zid"])))
    prim12["dep"] = A.dep_strength(prim12, z12, D)
    prim12s["dep"] = A.dep_strength(prim12s, sh12, D)
    prim12["strong"] = A.strong_mask(prim12["dep"].to_numpy())
    prim12s["strong"] = A.strong_mask(prim12s["dep"].to_numpy())
    print(f"parent ready: prim={len(prim12)} iso%={prim12['iso'].mean():.3f} "
          f"strong%={prim12['strong'].mean():.3f} [{time.time()-t0:.0f}s]", flush=True)

    HYPS = {
        "ZON-022": (prim12[prim12["iso"]], prim12s[prim12s["iso"]]),
        "ZON-023": (prim12[prim12["strong"]], prim12s[prim12s["strong"]]),
        "ZON-024": (prim12[prim12["iso"] & prim12["strong"]],
                    prim12s[prim12s["iso"] & prim12s["strong"]]),
    }
    stats = {"parent": {"zones": int(len(z12)), "prim": int(len(prim12)),
                        "iso_share": round(float(prim12["iso"].mean()), 4),
                        "strong_share": round(float(prim12["strong"].mean()), 4)}}
    for hyp, (rev, sev) in HYPS.items():
        th = time.time()
        events, _ = B.dedup(rev.reset_index(drop=True), z12)
        c1ev, _ = B.dedup(sev.reset_index(drop=True), sh12)
        events = events.assign(fam=hyp)
        c1ev = c1ev.assign(fam=hyp)
        c2, short = A.run_c2v2(D, events, z12, pool, cell, rng,
                               events["iso"].to_numpy(), K=5)
        s = R1.family_stats(D, hyp, z12, ep12, events, events, sh12, c1ev, c2,
                            short, 0, rng)
        s["C2"]["type"] = "C2v2 isolation-matched"
        s["stream"] = R3.stream_stats(events, z12, D)
        stats[hyp] = s
        events.to_parquet(f"{OUT}/events_{hyp}.parquet")
        c1ev.to_parquet(f"{OUT}/c1_{hyp}.parquet")
        c2.to_parquet(f"{OUT}/c2v2_{hyp}.parquet")
        print(f"{hyp}: N={len(events)} c1={len(c1ev)} c2v2={len(c2)} "
              f"(short {short}) class={s['classification']} [{time.time()-th:.0f}s]",
              flush=True)

    # ---- ZON-025 pooled isolation attribution
    z25 = {}
    for fam in POOL:
        th = time.time()
        if fam == "ZON-001":
            zf, _ = B.gen_zon001(D)
        else:
            zf = Z.GENS[fam](D)
        ep, _ = B.run_episodes(D, zf)
        ev = R1.primary_filter(ep)
        ev, _ = B.dedup(ev, zf)
        ev = ev.reset_index(drop=True)
        iso = Q.isolation_mask(ev, Q.mids_for(ev, zf), zf, D,
                               exclude_ids=ev["zid"].to_numpy())
        res = A.iso_vs_noniso(ev, iso, rng) or {}
        shf, _ = Z.gen_shadows_v2(zf, D, zf)
        epsf, _ = B.run_episodes(D, shf, first_only=True)
        c1 = R1.primary_filter(epsf)
        c1, _ = B.dedup(c1, shf)
        c1 = c1.reset_index(drop=True)
        iso_s = Q.isolation_mask(c1, Q.mids_for(c1, shf), zf, D,
                                 exclude_ids=np.array(Q.shadow_parent(c1["zid"])))
        ei = ev[iso].assign(nf=B.netfav(ev[iso])).dropna(subset=["nf"])
        ci_ = c1[iso_s].assign(nf=B.netfav(c1[iso_s])).dropna(subset=["nf"])
        if len(ei) >= 30 and len(ci_) >= 30:
            d, ci = B.day_boot(rng, B.by_day(ei, "nf"), B.by_day(ci_, "nf"))
            res["iso_vs_c1"] = {"delta": round(float(d), 4),
                                "ci": [round(float(x), 4) for x in ci],
                                "n_iso": int(len(ei)), "n_c1iso": int(len(ci_))}
        z25[fam] = res
        print(f"025/{fam}: {json.dumps(res)[:150]} [{time.time()-th:.0f}s]", flush=True)
    stats["ZON-025"] = z25

    with open(f"{OUT}/batch4_stats.json", "w") as f:
        json.dump(stats, f, indent=1, default=float)
    print(f"TOTAL {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
