"""Selection-bias null benchmark library (NULL_BENCHMARK_PLAN.md frozen)."""
from __future__ import annotations

import os, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
import batch1_lib as B
import batch2_lib as Z

TICK = 0.1
COMM = 0.05          # $5 RT in points
H_MAX = 120
MODELS = [(0.15, 0.15, 120), (0.15, 0.30, 120), (0.30, 0.15, 120),
          (None, None, 60), (0.10, 0.10, 120)]          # V1..V5; V1 = Benchmark A
RATES = [1.0, 2.0, 3.0, 5.0]
MIN_GAP = 15          # grid steps (=15*5=75 min? no: gap measured in eligible-list positions)


def eligible(D):
    n = len(D.ts)
    et_min = (D.df["et_shifted"].dt.hour * 60 + D.df["et_shifted"].dt.minute).to_numpy()
    ok = ((et_min % 5 == 0) & (D.sess < 4)
          & np.isfinite(D.adr[D.day])
          & (np.arange(n) + H_MAX <= D.seg_end)
          & (np.arange(n) - 5 >= D.seg_start))
    return np.flatnonzero(ok)


def outcome_table(D, elig):
    """pnl[e, dir(0=long,1=short), model] and exit day attribution (entry day)."""
    ne = len(elig)
    pnl = np.full((ne, 2, len(MODELS)), np.nan)
    h, l, c = D.h, D.l, D.c
    adr = D.adr[D.day]
    for k, i in enumerate(elig):
        a = adr[i]
        fh = np.maximum.accumulate(h[i + 1:i + 1 + H_MAX])
        fl = np.minimum.accumulate(l[i + 1:i + 1 + H_MAX])
        for di, sgn in ((0, 1.0), (1, -1.0)):
            pe = c[i] + sgn * TICK
            for mi, (s_, t_, hz) in enumerate(MODELS):
                if s_ is None:          # time-only exit
                    px = c[i + hz] - sgn * TICK
                    pnl[k, di, mi] = sgn * (px - pe) - COMM
                    continue
                stop = pe - sgn * s_ * a
                targ = pe + sgn * t_ * a
                if sgn > 0:
                    tt = int(np.searchsorted(fh[:hz], targ + TICK))
                    ts = int(np.searchsorted(-fl[:hz], -stop))
                else:
                    tt = int(np.searchsorted(-fl[:hz], -(targ - TICK)))
                    ts = int(np.searchsorted(fh[:hz], stop))
                hit_t = tt < hz
                hit_s = ts < hz
                if hit_s and (not hit_t or ts <= tt):          # both same bar -> stop
                    px = stop - sgn * TICK
                elif hit_t:
                    px = targ
                else:
                    px = c[i + hz] - sgn * TICK
                pnl[k, di, mi] = sgn * (px - pe) - COMM
    return pnl


def sample_strategy(rng, n_elig, n_pick):
    """Sorted entry positions with min gap in eligible-list index space."""
    picks = np.sort(rng.choice(n_elig, size=min(n_pick * 2, n_elig), replace=False))
    keep = [int(picks[0])]
    for p in picks[1:]:
        if p - keep[-1] >= MIN_GAP:
            keep.append(int(p))
        if len(keep) >= n_pick:
            break
    return np.array(keep, int)


def strat_metrics(pnl_vec, days_vec, all_days, years_vec):
    """Sharpe (daily, ann.), expectancy, PF, WR, total, maxDD, yearly totals."""
    dsum = np.bincount(days_vec - all_days[0], pnl_vec,
                       minlength=all_days[-1] - all_days[0] + 1)
    mu, sd = dsum.mean(), dsum.std()
    sharpe = mu / sd * np.sqrt(252) if sd > 0 else np.nan
    eq = np.cumsum(dsum)
    mdd = float(np.max(np.maximum.accumulate(eq) - eq)) if len(eq) else np.nan
    wins = pnl_vec[pnl_vec > 0].sum()
    losses = -pnl_vec[pnl_vec < 0].sum()
    yr_tot = {}
    for y in np.unique(years_vec):
        yr_tot[int(y)] = float(pnl_vec[years_vec == y].sum())
    return {"sharpe": float(sharpe), "exp": float(pnl_vec.mean()),
            "total": float(pnl_vec.sum()), "wr": float((pnl_vec > 0).mean()),
            "pf": float(wins / losses) if losses > 0 else np.inf,
            "mdd": mdd, "n": int(len(pnl_vec)),
            "pos_years": int(sum(v > 0 for v in yr_tot.values())),
            "yr": yr_tot}
