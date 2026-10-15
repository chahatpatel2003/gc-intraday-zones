#!/usr/bin/env python3
"""Batch-7 Stage A — mine 2016-2019 ONLY. Writes aurum/batch7/mining_log.csv."""
import json, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
import batch1_lib as B
import batch2_lib as Z
import motifs_lib as M
import run_batch1 as R1

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "batch7"))
os.makedirs(OUT, exist_ok=True)


def screen(D, name, zones, pool, cell, rng, cont):
    if len(zones) < 20:
        return {"motif": name, "zones": len(zones), "note": "too few zones"}
    ep, _ = B.run_episodes(D, zones)
    prim = R1.primary_filter(ep)
    events, _ = B.dedup(prim, zones)
    if len(events) < 30:
        return {"motif": name, "zones": len(zones), "N": len(events),
                "note": "too few events"}
    shadows, diag = Z.gen_shadows_v2(zones, D, zones)
    eps, _ = B.run_episodes(D, shadows, first_only=True)
    c1, _ = B.dedup(R1.primary_filter(eps), shadows)
    c2, _ = B.run_c2(D, events, zones, pool, cell, rng, K=5)
    sgn = -1.0 if cont else 1.0
    ev = events.assign(nf=sgn * B.netfav(events)).dropna(subset=["nf"])
    cv = c1.assign(nf=sgn * B.netfav(c1)).dropna(subset=["nf"])
    if len(cv) >= 30:
        d1, ci1 = B.day_boot(rng, B.by_day(ev, "nf"), B.by_day(cv, "nf"))
    else:
        d1, ci1 = np.nan, [np.nan, np.nan]
    c2 = c2.assign(nf=sgn * (c2["FE60"] - c2["AE60"]) / c2["adr"])
    don = c2.dropna(subset=["nf"]).groupby("event_zid")["nf"].mean()
    evk = ev.set_index("zid")
    common = evk.index.intersection(don.index)
    if len(common) >= 30:
        paired = evk.loc[common, "nf"] - don.loc[common]
        pday = evk.loc[common, "day"]
        pmap = {d: paired[pday == d].to_numpy() for d in pday.unique()}
        d2, ci2 = B.day_boot(rng, None, None, paired=pmap)
    else:
        d2, ci2 = np.nan, [np.nan, np.nan]
    nd = int(np.isfinite(D.adr).sum())
    return {"motif": name, "zones": int(len(zones)), "N": int(len(events)),
            "ev_day": round(len(events) / nd, 3),
            "d_c1": round(float(d1), 4), "c1_lo": round(float(ci1[0]), 4),
            "c1_hi": round(float(ci1[1]), 4),
            "d_c2": round(float(d2), 4), "c2_lo": round(float(ci2[0]), 4),
            "c2_hi": round(float(ci2[1]), 4),
            "spz": diag["shadows_per_zone"],
            "noctl_share": round(diag["zones_without_control"] / max(len(zones), 1), 3),
            "ambig": round(float(events["ambig"].mean()), 3),
            "frame": "cont" if cont else "rej",
            "events_key": json.dumps(sorted(set(zip(events["day"].astype(int),
                                                    events["T0"].astype(int))))[:4000])}


def main():
    t0 = time.time()
    rng = np.random.default_rng(B.SEED)
    D = M.prep7(B.load_discovery(start="2016-01-01", end="2020-01-01"))
    pool, cell, _, _ = B.build_c2_pool(D)
    print(f"MINING WINDOW bars={len(D.ts):,} days={D.n_days} [{time.time()-t0:.0f}s]",
          flush=True)
    log = []
    zcache = {}
    for name, gen in M.MOTIFS.items():
        tm = time.time()
        zones = gen(D)
        zcache[name] = zones
        r = screen(D, name, zones, pool, cell, rng, name in M.CONTINUATION)
        r["sec"] = round(time.time() - tm, 1)
        log.append(r)
        print({k: v for k, v in r.items() if k != "events_key"}, flush=True)
    pd.DataFrame(log).to_csv(f"{OUT}/mining_log.csv", index=False)
    print(f"STAGE A base screening done [{time.time()-t0:.0f}s]")


if __name__ == "__main__":
    main()
