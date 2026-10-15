#!/usr/bin/env python3
"""Random-zone null: 200 information-free zone families through the exact real pipeline."""
import json, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
import batch1_lib as B
import batch2_lib as Z
import null_lib as N
import run_batch1 as R1

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "nullbench"))
MASTER = 20260816
NFAM = 200
NS_MIN = 60_000_000_000

t0 = time.time()
D = Z.prep(B.load_discovery(start="2016-01-01", end="2020-01-01"))
pool, cell, _, _ = B.build_c2_pool(D)
elig = N.eligible(D)
nd = int(np.isfinite(D.adr).sum())
print(f"zone-null window: {len(elig):,} eligible bars, {nd} days [{time.time()-t0:.0f}s]", flush=True)

rows = []
for f in range(NFAM):
    rng = np.random.default_rng(MASTER + 50000 + f)
    rate = [0.5, 1.0, 2.0, 3.0][f % 4]
    sess_life = bool(f % 2)
    n_z = int(rate * nd)
    bars = np.sort(rng.choice(elig, size=n_z, replace=False))
    dd = Z._GenDedup()
    zr = []
    for k, i in enumerate(bars):
        d = D.day[i]
        a = D.adr[d]
        side = 1 if rng.random() < 0.5 else -1
        dist = rng.uniform(0.05, 0.30) * a
        w = rng.uniform(0.05, 0.25) * a
        mid = D.c[i] + side * dist
        L, H = mid - w / 2, mid + w / 2
        act = D.ts[i] + NS_MIN
        exp = (D.ts[D.day_last[d]] + NS_MIN) if sess_life else \
            (D.ts[D.day_last[min(d + 5, D.n_days - 1)]] + NS_MIN)
        if act >= exp or not dd.ok(L, H, act, exp):
            continue
        zr.append((f"RZ{f}", f"RZ{f}-{k}", L, H, act, exp, D.iid[i], side,
                   "30min", d, "rand"))
    zones = B.ztable(zr)
    if len(zones) < 50:
        continue
    ep, _ = B.run_episodes(D, zones)
    events, _ = B.dedup(R1.primary_filter(ep), zones)
    if len(events) < 100:
        continue
    shadows, diag = Z.gen_shadows_v2(zones, D, zones)
    eps, _ = B.run_episodes(D, shadows, first_only=True)
    c1, _ = B.dedup(R1.primary_filter(eps), shadows)
    c2, _ = B.run_c2(D, events, zones, pool, cell, rng, K=5)
    ev = events.assign(nf=B.netfav(events)).dropna(subset=["nf"])
    cv = c1.assign(nf=B.netfav(c1)).dropna(subset=["nf"])
    d1, ci1 = (B.day_boot(rng, B.by_day(ev, "nf"), B.by_day(cv, "nf"))
               if len(cv) >= 30 else (np.nan, [np.nan, np.nan]))
    c2 = c2.assign(nf=(c2["FE60"] - c2["AE60"]) / c2["adr"])
    don = c2.dropna(subset=["nf"]).groupby("event_zid")["nf"].mean()
    evk = ev.set_index("zid")
    common = evk.index.intersection(don.index)
    if len(common) >= 30:
        paired = evk.loc[common, "nf"] - don.loc[common]
        pday = evk.loc[common, "day"]
        pmap = {dd_: paired[pday == dd_].to_numpy() for dd_ in pday.unique()}
        d2, ci2 = B.day_boot(rng, None, None, paired=pmap)
    else:
        d2, ci2 = np.nan, [np.nan, np.nan]
    rows.append({"fam": f, "rate": rate, "sess_life": sess_life,
                 "zones": int(len(zones)), "N": int(len(events)),
                 "d1": round(float(d1), 4), "c1lo": round(float(ci1[0]), 4),
                 "c1hi": round(float(ci1[1]), 4),
                 "d2": round(float(d2), 4), "c2lo": round(float(ci2[0]), 4),
                 "c2hi": round(float(ci2[1]), 4),
                 "both_ci_pos": bool(ci1[0] > 0 and ci2[0] > 0)})
    if (f + 1) % 25 == 0:
        print(f"family {f+1}/{NFAM} [{time.time()-t0:.0f}s]", flush=True)

df = pd.DataFrame(rows)
df.to_csv(f"{OUT}/zone_null_log.csv", index=False)
d1 = df["d1"].dropna().to_numpy(); d2 = df["d2"].dropna().to_numpy()
mn = np.minimum(df["d1"].to_numpy(), df["d2"].to_numpy())
mn = mn[np.isfinite(mn)]

def q(v):
    return {"median": round(float(np.median(v)), 4), "p90": round(float(np.quantile(v, .9)), 4),
            "p95": round(float(np.quantile(v, .95)), 4), "p99": round(float(np.quantile(v, .99)), 4),
            "max": round(float(v.max()), 4)}

def pct(v, x):
    return round(float(np.mean(v < x)) * 100, 1)

summary = {"families_evaluated": int(len(df)), "d1": q(d1), "d2": q(d2), "min_delta": q(mn),
           "false_family_rate_bothCIs": round(float(df["both_ci_pos"].mean()), 4),
           "percentile_ranks": {
               "ZON-028_d1_+0.053": pct(d1, 0.053), "ZON-028_d2_+0.024": pct(d2, 0.024),
               "ZON-028_min_+0.024": pct(mn, 0.024),
               "ZON-017_d1_+0.040": pct(d1, 0.040),
               "ZON-035mined_d1_+0.030": pct(d1, 0.030), "ZON-035mined_d2_+0.016": pct(d2, 0.016),
               "M03_min_+0.023": pct(mn, 0.023),
               "ZON-012_d1_+0.010": pct(d1, 0.010), "ZON-012_d2_+0.007": pct(d2, 0.007),
               "ZON-012_min_+0.007": pct(mn, 0.007)}}
with open(f"{OUT}/zone_null_summary.json", "w") as fjs:
    json.dump(summary, fjs, indent=1)
print(json.dumps(summary, indent=1))
print(f"TOTAL {time.time()-t0:.0f}s")
