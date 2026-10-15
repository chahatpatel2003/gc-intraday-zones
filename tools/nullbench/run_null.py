#!/usr/bin/env python3
"""Run 100 tournaments x 1000 zero-edge strategies (Benchmarks A and B) + replication."""
import json, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
import batch1_lib as B
import batch2_lib as Z
import null_lib as N

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "nullbench"))
os.makedirs(OUT, exist_ok=True)
MASTER = 20260816
N_TOUR = 100
N_STRAT = 1000

t0 = time.time()
D = Z.prep(B.load_discovery())
d2020 = next(i for i, d in enumerate(D.days) if d >= __import__("pandas").Timestamp("2020-01-01").date())
elig = N.eligible(D)
day_e = D.day[elig]
yr_e = D.year[day_e]
is_sel = day_e < d2020
E_IS = np.flatnonzero(is_sel)          # positions within elig
E_OOS = np.flatnonzero(~is_sel)
nd_is = int(np.isfinite(D.adr[:d2020]).sum())
nd_oos = int(np.isfinite(D.adr[d2020:]).sum())
print(f"eligible bars: {len(elig):,} (IS {len(E_IS):,} / OOS {len(E_OOS):,}) "
      f"days {nd_is}/{nd_oos} [{time.time()-t0:.0f}s]", flush=True)

tblpath = f"{OUT}/outcome_table.npy"
if os.path.exists(tblpath):
    pnl = np.load(tblpath)
else:
    pnl = N.outcome_table(D, elig)
    np.save(tblpath, pnl)
print(f"outcome table {pnl.shape} [{time.time()-t0:.0f}s]", flush=True)

days_is = day_e[E_IS]; yrs_is = yr_e[E_IS]
all_days_is = (int(days_is.min()), int(days_is.max()))
days_oos = day_e[E_OOS]; yrs_oos = yr_e[E_OOS]
all_days_oos = (int(days_oos.min()), int(days_oos.max()))

tours = []
for t in range(N_TOUR):
    rng = np.random.default_rng(MASTER + 1000 + t)
    best = None
    maxima = {k: -1e18 for k in ("sharpe", "exp", "pf", "wr", "total", "pos_years")}
    maxima_B = {k: -1e18 for k in ("sharpe", "exp", "pf", "total")}
    for s in range(N_STRAT):
        rate = N.RATES[s % 4]
        n_pick = int(rate * nd_is)
        pos = N.sample_strategy(rng, len(E_IS), n_pick)
        eidx = E_IS[pos]
        dirs = rng.integers(0, 2, len(eidx))
        pv = pnl[eidx, dirs, 0]
        m = N.strat_metrics(pv, days_is[pos], all_days_is, yrs_is[pos])
        for k in maxima:
            if np.isfinite(m.get(k, np.nan)) and m[k] > maxima[k]:
                maxima[k] = m[k]
        if best is None or (np.isfinite(m["sharpe"]) and m["sharpe"] > best[0]):
            best = (m["sharpe"], s, rate, eidx, dirs, m)
        # Benchmark B: best of 5 exits by Sharpe for this strategy
        bs = -1e18; bm = None
        for mi in range(5):
            mm = N.strat_metrics(pnl[eidx, dirs, mi], days_is[pos], all_days_is, yrs_is[pos])
            if np.isfinite(mm["sharpe"]) and mm["sharpe"] > bs:
                bs, bm = mm["sharpe"], mm
        for k in maxima_B:
            if bm and np.isfinite(bm.get(k, np.nan)) and bm[k] > maxima_B[k]:
                maxima_B[k] = bm[k]
    # replication: winner rule applied to 2020-21, fresh seeded stream
    _, sid, rate, _, _, m_is = best
    rng2 = np.random.default_rng(MASTER + 900000 + t * 1000 + sid)
    pos2 = N.sample_strategy(rng2, len(E_OOS), int(rate * nd_oos))
    eidx2 = E_OOS[pos2]
    dirs2 = rng2.integers(0, 2, len(eidx2))
    m_oos = N.strat_metrics(pnl[eidx2, dirs2, 0], days_oos[pos2], all_days_oos, yrs_oos[pos2])
    tours.append({"t": t, "seed": MASTER + 1000 + t, "winner_bucket": rate,
                  "max_A": {k: round(v, 4) for k, v in maxima.items()},
                  "max_B": {k: round(v, 4) for k, v in maxima_B.items()},
                  "winner_is": {k: (round(v, 4) if isinstance(v, float) else v)
                                for k, v in m_is.items() if k != "yr"},
                  "winner_oos": {k: (round(v, 4) if isinstance(v, float) else v)
                                 for k, v in m_oos.items() if k != "yr"}})
    if (t + 1) % 10 == 0:
        print(f"tournament {t+1}/{N_TOUR} [{time.time()-t0:.0f}s]", flush=True)

with open(f"{OUT}/tournaments.json", "w") as f:
    json.dump(tours, f, indent=0)

def dist(key, sub):
    v = np.array([x[sub][key] for x in tours if np.isfinite(x[sub].get(key, np.nan))])
    return {"median": round(float(np.median(v)), 3), "p90": round(float(np.quantile(v, .9)), 3),
            "p95": round(float(np.quantile(v, .95)), 3), "p99": round(float(np.quantile(v, .99)), 3)}

summary = {
    "n_tournaments": N_TOUR, "n_strats": N_STRAT,
    "best_of_1000_A": {k: dist(k, "max_A") for k in ("sharpe", "exp", "pf", "wr", "total", "pos_years")},
    "best_of_5000_B": {k: dist(k, "max_B") for k in ("sharpe", "exp", "pf", "total")},
    "winner_is_sharpe": dist("sharpe", "winner_is"),
    "winner_oos_sharpe": dist("sharpe", "winner_oos"),
    "winner_is_exp": dist("exp", "winner_is"),
    "winner_oos_exp": dist("exp", "winner_oos"),
    "pct_winners_profitable_oos": round(float(np.mean(
        [x["winner_oos"]["total"] > 0 for x in tours])), 3),
}
with open(f"{OUT}/null_summary.json", "w") as f:
    json.dump(summary, f, indent=1)
print(json.dumps(summary, indent=1))
print(f"TOTAL {time.time()-t0:.0f}s")
