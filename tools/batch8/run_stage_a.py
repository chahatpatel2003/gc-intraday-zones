#!/usr/bin/env python3
"""Batch-8 Stage A — mine 2016-2019: baselines, 120-triage grid, <=10 full pairs, rank."""
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

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "batch8"))
os.makedirs(OUT, exist_ok=True)
H = B.HORIZONS


def universes(D):
    z1, _ = B.gen_zon002(D)
    return {"U1_fvg": z1.assign(fam="U1_fvg"),
            "U2_compress": Z.gen_zon013(D).assign(fam="U2_compress"),
            "U3_tail": Z.gen_zon008(D).assign(fam="U3_tail"),
            "U4_sestrap": M7.m02(D).assign(fam="U4_sestrap"),
            "U5_vaedge": Z.gen_zon012(D).assign(fam="U5_vaedge"),
            "U6_nr7": M7.m09(D).assign(fam="U6_nr7")}


def add_btype(ev, zones):
    zm = zones.set_index("zid")["btype"]
    return ev.assign(btype=zm.reindex(ev["zid"]).to_numpy())


def paired_c2(rng, ev, c2):
    c2 = c2.assign(nf=(c2["FE60"] - c2["AE60"]) / c2["adr"])
    don = c2.dropna(subset=["nf"]).groupby("event_zid")["nf"].mean()
    evk = ev.set_index("zid")
    common = evk.index.intersection(don.index)
    if len(common) < 30:
        return np.nan, [np.nan, np.nan], {}, 0
    paired = evk.loc[common, "nf"] - don.loc[common]
    pday = evk.loc[common, "day"]
    pmap = {d: paired[pday == d].to_numpy() for d in pday.unique()}
    d2, ci2 = B.day_boot(rng, None, None, paired=pmap)
    yearly = {}
    yr = evk.loc[common, "year"]
    for y, g in paired.groupby(yr):
        if len(g) >= 30:
            yearly[int(y)] = round(float(g.mean()), 4)
    return d2, ci2, yearly, len(common)


def run_c2_state(D, events, zones, pool, cell, rng, on_sup, on_dem, K=5):
    zL = zones["L"].to_numpy(); zH = zones["H"].to_numpy()
    zact = zones["act"].to_numpy(); zexp = zones["exp"].to_numpy()
    byday = B.zones_by_day(zones, D)
    rows, short = [], 0
    for e in events.itertuples(index=False):
        c0 = cell[e.T0]
        if c0 < 0 or c0 not in pool:
            short += 1
            continue
        cand = pool[c0]
        got = 0; tries = 0
        while got < K and tries < 25 * K:
            i = int(cand[rng.integers(len(cand))]); tries += 1
            if D.day[i] == e.day:
                continue
            side = -1 if B.cell_dir(cell, i) else +1          # -1 rising: pseudo above
            if not (on_sup[i] if side < 0 else on_dem[i]):
                continue
            P0 = D.c[i]
            sl, sh = (P0, P0 + e.W) if side < 0 else (P0 - e.W, P0)
            bad = False
            for zi in byday.get(int(D.day[i]), []):
                if zact[zi] <= D.ts[i] < zexp[zi] and zL[zi] < sh and zH[zi] > sl:
                    bad = True; break
            if bad:
                continue
            Hm = min(i + 120, D.seg_end[i])
            m = Hm - i
            if m < 5:
                continue
            hw = D.h[i:Hm + 1]; lw = D.l[i:Hm + 1]
            if side < 0:
                ae = np.clip(np.maximum.accumulate(hw) - P0, 0, None)
                fe = np.clip(P0 - np.minimum.accumulate(lw[1:]), 0, None)
            else:
                ae = np.clip(P0 - np.minimum.accumulate(lw), 0, None)
                fe = np.clip(np.maximum.accumulate(hw[1:]) - P0, 0, None)
            fes, aes = [], []
            for hz in H:
                if hz <= m:
                    fes.append(float(fe[hz - 1]) if len(fe) >= hz else np.nan)
                    aes.append(float(ae[hz]))
                else:
                    fes.append(np.nan); aes.append(np.nan)
            rows.append((e.fam, e.zid, i, D.day[i], D.year[D.day[i]], e.W,
                         D.adr[D.day[i]], 0, 0, 0, *fes, *aes))
            got += 1
        if got < K:
            short += 1
    cols = ["fam", "event_zid", "T0", "day", "year", "W", "adr", "rejW", "rejA",
            "trav120"] + [f"FE{h}" for h in H] + [f"AE{h}" for h in H]
    return pd.DataFrame(rows, columns=cols), short


def main():
    t0 = time.time()
    rng = np.random.default_rng(B.SEED)
    D = M7.prep7(B.load_discovery(start="2016-01-01", end="2020-01-01"))
    S = SL.build(D)
    pool, cell, _, _ = B.build_c2_pool(D)
    nd = int(np.isfinite(D.adr).sum())
    print(f"mining bars={len(D.ts):,} days={nd} sp_q=({S.sp_q25:.6f},{S.sp_q75:.6f}) "
          f"[{time.time()-t0:.0f}s]", flush=True)

    cache = {}
    base = {}
    for u, zones in universes(D).items():
        tu = time.time()
        ep, _ = B.run_episodes(D, zones)
        ev, _ = B.dedup(R1.primary_filter(ep), zones)
        ev = add_btype(ev.reset_index(drop=True), zones)
        ev["nf"] = B.netfav(ev)
        sh, diag = Z.gen_shadows_v2(zones, D, zones)
        eps, _ = B.run_episodes(D, sh, first_only=True)
        c1, _ = B.dedup(R1.primary_filter(eps), sh)
        c1 = add_btype(c1.reset_index(drop=True), sh)
        c1["nf"] = B.netfav(c1)
        c2, _ = B.run_c2(D, ev, zones, pool, cell, rng, K=5)
        evv = ev.dropna(subset=["nf"]); cvv = c1.dropna(subset=["nf"])
        d1, ci1 = B.day_boot(rng, B.by_day(evv, "nf"), B.by_day(cvv, "nf"))
        d2, ci2, _, _ = paired_c2(rng, evv, c2)
        base[u] = {"zones": int(len(zones)), "N": int(len(ev)),
                   "ev_day": round(len(ev) / nd, 2),
                   "meanA": round(float(evv["nf"].mean()), 4),
                   "d1": round(float(d1), 4), "d2": round(float(d2), 4),
                   "spz": diag["shadows_per_zone"],
                   "noctl": round(diag["zones_without_control"] / max(len(zones), 1), 3)}
        fl_ev = SL.flags(S, ev["T0"].to_numpy(), ev["btype"].to_numpy(),
                         ev["side"].to_numpy())
        fl_c1 = SL.flags(S, c1["T0"].to_numpy(), c1["btype"].to_numpy(),
                         c1["side"].to_numpy())
        cache[u] = (zones, ev, c1, fl_ev, fl_c1, diag)
        print(f"{u}: {base[u]} [{time.time()-tu:.0f}s]", flush=True)

    # 120-cell triage grid
    grid = []
    for u, (zones, ev, c1, fl_ev, _, _) in cache.items():
        evv = ev.dropna(subset=["nf"])
        meanA = evv["nf"].mean()
        for s in SL.STATES:
            on = fl_ev[s][ev["nf"].notna().to_numpy()]
            sub = evv[on]
            grid.append({"u": u, "s": s, "n_on": int(len(sub)),
                         "ev_day_on": round(len(sub) / nd, 3),
                         "uplift": round(float(sub["nf"].mean() - meanA), 4)
                         if len(sub) >= 30 else np.nan})
    gdf = pd.DataFrame(grid)
    gdf.to_csv(f"{OUT}/triage_grid.csv", index=False)
    elig = gdf[(gdf["n_on"] >= 300) & (gdf["ev_day_on"] >= 0.5)
               & np.isfinite(gdf["uplift"])].sort_values("uplift", ascending=False)
    pairs = []
    per_u = {}
    for _, r in elig.iterrows():
        if per_u.get(r["u"], 0) >= 3:
            continue
        pairs.append((r["u"], r["s"]))
        per_u[r["u"]] = per_u.get(r["u"], 0) + 1
        if len(pairs) >= 10:
            break
    print("selected pairs:", pairs, flush=True)

    # precompute per-bar state arrays for donor checks (both hypothetical sides)
    n = len(D.ts)
    allbars = np.arange(n)
    donor_states = {}
    for s in {s for _, s in pairs}:
        fs = SL.flags(S, allbars, np.full(n, +1), np.full(n, +1))[s]
        fd = SL.flags(S, allbars, np.full(n, -1), np.full(n, -1))[s]
        donor_states[s] = (fs, fd)
    print(f"donor state arrays ready [{time.time()-t0:.0f}s]", flush=True)

    znull = pd.read_csv(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "nullbench", "zone_null_log.csv")))
    nd1 = znull["d1"].dropna().to_numpy(); nd2 = znull["d2"].dropna().to_numpy()
    results = []
    for u, s in pairs:
        tp = time.time()
        zones, ev, c1, fl_ev, fl_c1, diag = cache[u]
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
        mind = min(d1, d2, cma)
        posyears = sum(v > 0 for v in yearly.values())
        score = (mind + 0.01 * min(len(evv) / nd, 3) + 0.01 * (posyears - 2)) \
            if np.isfinite(mind) else np.nan
        res = {"u": u, "s": s, "N": int(len(eon)), "ev_day": round(len(eon) / nd, 3),
               "d1": round(float(d1), 4), "ci1": [round(float(x), 4) for x in ci1],
               "d2": round(float(d2), 4), "ci2": [round(float(x), 4) for x in ci2],
               "C_minus_A": round(cma, 4), "min_delta": round(float(mind), 4),
               "yearly_c2": yearly, "pos_years": int(posyears),
               "c1_n": int(len(cvv)), "c2_pairs": int(npair), "c2_short": int(short),
               "null_pct_d1": round(float(np.mean(nd1 < d1)) * 100, 1),
               "null_pct_d2": round(float(np.mean(nd2 < d2)) * 100, 1),
               "score": round(float(score), 4) if np.isfinite(score) else None}
        results.append(res)
        print(f"{u}x{s}: {res} [{time.time()-tp:.0f}s]", flush=True)

    results.sort(key=lambda r: -(r["score"] if r["score"] is not None else -9))
    with open(f"{OUT}/stage_a.json", "w") as f:
        json.dump({"baselines": base, "pairs": results}, f, indent=1, default=float)
    print(f"TOTAL {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
