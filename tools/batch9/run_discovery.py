#!/usr/bin/env python3
"""Batch-9 discovery: 30 frozen variants on 2016-2019 + matched best-of-30 null."""
import json, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
for p in ("batch1", "batch2", "batch7", "nullbench"):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", p))
import batch1_lib as B
import motifs_lib as M7
import trade_lib as T
import null_lib as NL

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "batch9"))
os.makedirs(OUT, exist_ok=True)

t0 = time.time()
D = M7.prep7(B.load_discovery(start="2016-01-01", end="2020-01-01"))
nd = int(np.isfinite(D.adr).sum())
print(f"discovery bars={len(D.ts):,} days={nd} [{time.time()-t0:.0f}s]", flush=True)

tr, misses = T.run_variants(D)
tr.to_parquet(f"{OUT}/trades_discovery.parquet")
print(f"raw trade rows={len(tr):,} misses={len(misses):,} [{time.time()-t0:.0f}s]", flush=True)

stats = {}
gate_info = {}
for (fam, conf), g in tr.groupby(["fam", "conf"]):
    gated = g[g["gate"]]
    gate_info[f"{fam}x{conf}"] = {"attempts": int(len(g)),
                                  "stop_too_large_pct": round(float(1 - g["gate"].mean()), 3)}
    s = T.variant_stats(gated.reset_index(drop=True), nd)
    if s:
        s["stop_too_large_pct"] = gate_info[f"{fam}x{conf}"]["stop_too_large_pct"]
        mc = misses[(misses["fam"] == fam) & (misses["conf"] == conf)]
        s["missed"] = int((mc["reason"] == "missed").sum())
        s["cancelled"] = int((mc["reason"] == "cancel_invalid").sum())
        stats[f"{fam}x{conf}"] = s

with open(f"{OUT}/discovery_stats.json", "w") as f:
    json.dump(stats, f, indent=1, default=float)
rows = [{"variant": k, **{kk: vv for kk, vv in v.items()
                          if not isinstance(vv, dict)}} for k, v in stats.items()]
pd.DataFrame(rows).to_csv(f"{OUT}/discovery_table.csv", index=False)
for k, v in sorted(stats.items(), key=lambda kv: -kv[1]["wr"]):
    print(f"{k}: wr={v['wr']:.3f} expR={v['exp_R']:+.3f} n={v['n']} tpd={v['tpd']} "
          f"ambig={v['ambig']:.3f} stop_med={v['stop_med']} to={v['to_pct']:.2f}", flush=True)

# ---- matched best-of-30 null: 50 tournaments
real_counts = [v["n"] for v in stats.values()]
elig = NL.eligible(D)
rng0 = np.random.default_rng(B.SEED)
best = []
for tno in range(50):
    rng = np.random.default_rng(B.SEED + 7000 + tno)
    best_wr, best_exp, best_pf = -1, -9, -9
    for vi in range(30):
        n_tr = real_counts[vi % len(real_counts)]
        bars = rng.choice(elig, size=min(n_tr, len(elig)), replace=False)
        wr_n = exp_sum = wins = losses = 0
        for i in bars:
            d = 1 if rng.random() < 0.5 else -1
            a = D.adr[D.day[i]]
            R = rng.uniform(0.03, 0.10) * a
            entry = D.o[i] + d * T.TICK
            sl = entry - d * R
            tp = entry + d * R
            end = min(i + T.HOLD - 1, D.seg_end[i])
            hh = D.h[i:end + 1]; ll = D.l[i:end + 1]
            fh = np.maximum.accumulate(hh); fl = np.minimum.accumulate(ll)
            if d > 0:
                t_tp = int(np.searchsorted(fh, tp)) if fh[-1] >= tp else None
                t_sl = int(np.searchsorted(-fl, -sl)) if fl[-1] <= sl else None
            else:
                t_tp = int(np.searchsorted(-fl, -tp)) if fl[-1] <= tp else None
                t_sl = int(np.searchsorted(fh, sl)) if fh[-1] >= sl else None
            if t_sl is not None and (t_tp is None or t_sl <= t_tp):
                pnl = -(R + T.SLIP) - T.COMM
            elif t_tp is not None:
                pnl = R - T.COMM; wr_n += 1
            else:
                pnl = d * (D.c[end] - d * T.TICK - entry) - T.COMM
            exp_sum += pnl / R
            if pnl > 0:
                wins += pnl
            else:
                losses -= pnl
        wr = wr_n / len(bars)
        expR = exp_sum / len(bars)
        pf = wins / losses if losses > 0 else np.inf
        best_wr = max(best_wr, wr); best_exp = max(best_exp, expR); best_pf = max(best_pf, pf)
    best.append({"wr": best_wr, "expR": best_exp, "pf": best_pf})
    if (tno + 1) % 10 == 0:
        print(f"null tournament {tno+1}/50 [{time.time()-t0:.0f}s]", flush=True)

bb = pd.DataFrame(best)
null30 = {k: {"median": round(float(bb[k].median()), 4),
              "p95": round(float(bb[k].quantile(.95)), 4),
              "p99": round(float(bb[k].quantile(.99)), 4)} for k in ("wr", "expR", "pf")}
with open(f"{OUT}/null30.json", "w") as f:
    json.dump(null30, f, indent=1)
print("matched null best-of-30:", json.dumps(null30))
print(f"TOTAL {time.time()-t0:.0f}s")
