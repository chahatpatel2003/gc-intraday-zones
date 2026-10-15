"""Batch-8 state vocabulary (BATCH8_PLAN.md frozen). All lookups causal:
1m-level info through T0-1; frame-level info from bars fully CLOSED at/before T0 open."""
from __future__ import annotations

import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch7"))
import batch1_lib as B
import motifs_lib as M

STATES = [f"S{i:02d}" for i in range(1, 21)]


def _scatter(frame, D, colfn):
    """Compute per-segment series on a resampled frame; return in frame row order."""
    out = np.full(len(frame), np.nan)
    for seg, gg in frame.groupby("instrument_id", sort=False):
        idx = gg.index.to_numpy()
        out[idx] = colfn(gg.reset_index(drop=True))
    return out


def build(D):
    """Precompute all per-bar state ingredients. Returns a lookup object."""
    S = type("S", (), {})()
    n = len(D.ts)
    b15, b30 = D.b15, D.b30
    S.c15 = M.ctx(D, b15)
    S.c30 = M.ctx(D, b30)
    # map 1m bar -> last frame row with close_ns <= ts (completed before bar open)
    S.i15 = np.searchsorted(b15["close_ns"].to_numpy(), D.ts, "right") - 1
    S.i30 = np.searchsorted(b30["close_ns"].to_numpy(), D.ts, "right") - 1

    # ---- 15m ingredients
    adr15 = D.adr[S.c15["day"]]
    S.rsi15 = _scatter(b15, D, lambda g: M.rsi14(g["close"].to_numpy()))
    S.volz15 = _scatter(b15, D, lambda g: M.volz20(g["volume"].to_numpy(float)))
    h, l, o, c = (S.c15[k] for k in ("h", "l", "o", "c"))
    rng = h - l
    med = _scatter(b15, D, lambda g: M.med20((g["high"] - g["low"]).to_numpy()))

    def roll_any(x, w):
        return pd.Series(x.astype(float)).rolling(w, min_periods=1).max().to_numpy() > 0.5

    def roll_mean(x, w):
        return pd.Series(x).rolling(w, min_periods=w).mean().to_numpy()

    roc5 = np.full(len(b15), np.nan)
    for seg, gg in b15.groupby("instrument_id", sort=False):
        ii = gg.index.to_numpy()
        cc = c[ii]
        r = np.full(len(ii), np.nan)
        r[5:] = (cc[5:] - cc[:-5]) / adr15[ii[5:]]
        roc5[ii] = r
    S.decel = np.zeros(len(b15), bool)
    m = np.isfinite(roc5)
    r5p = np.full(len(b15), np.nan)
    r5p[5:] = roc5[:-5]
    S.decel = m & np.isfinite(r5p) & (np.abs(roc5) <= 0.75 * np.abs(r5p)) & (np.abs(r5p) >= 0.05)

    up_disp = (rng >= 2.5 * med) & (c > o)
    dn_disp = (rng >= 2.5 * med) & (c < o)
    S.dispUp6 = roll_any(up_disp, 6)
    S.dispDn6 = roll_any(dn_disp, 6)
    S.volz3max = pd.Series(S.volz15).rolling(3, min_periods=1).max().to_numpy()
    S.volz3mean = pd.Series(S.volz15).rolling(3, min_periods=3).mean().to_numpy()

    p20h = pd.Series(h).rolling(20).max().shift(1).to_numpy()
    p20l = pd.Series(l).rolling(20).min().shift(1).to_numpy()
    upsw = np.isfinite(p20h) & (h > p20h) & (c < p20h)
    dnsw = np.isfinite(p20l) & (l < p20l) & (c > p20l)
    S.upSweep12 = roll_any(upsw, 12)
    S.dnSweep12 = roll_any(dnsw, 12)

    inter = np.minimum(h, np.roll(h, 1)) - np.maximum(l, np.roll(l, 1))
    union = np.maximum(h, np.roll(h, 1)) - np.minimum(l, np.roll(l, 1))
    iou = np.clip(inter, 0, None) / np.maximum(union, 1e-9)
    iou[0] = np.nan
    S.chop6 = roll_mean(iou, 6) >= 0.6

    # ---- 30m ingredients
    e20 = _scatter(b30, D, lambda g: M.ema(g["close"].to_numpy(), 20))
    e50 = _scatter(b30, D, lambda g: M.ema(g["close"].to_numpy(), 50))
    S.trendUp = e20 > e50
    S.trendDn = e20 < e50
    h3, l3, c3 = S.c30["h"], S.c30["l"], S.c30["c"]
    adr30 = D.adr[S.c30["day"]]
    span_h = pd.Series(h3).rolling(6).max().shift(7).to_numpy()
    span_l = pd.Series(l3).rolling(6).min().shift(7).to_numpy()
    S.balTrans = (np.isfinite(span_h) & ((span_h - span_l) <= 0.35 * adr30)
                  & ((c3 > span_h) | (c3 < span_l)))
    fa_up = np.zeros(len(b30), bool)
    fa_dn = np.zeros(len(b30), bool)
    day30 = S.c30["day"]
    for d in np.unique(day30):
        bars = np.flatnonzero(day30 == d)
        if len(bars) < 4:
            continue
        rh = np.maximum.accumulate(h3[bars])
        rl = np.minimum.accumulate(l3[bars])
        for x in range(1, len(bars)):
            if c3[bars[x]] > rh[x - 1]:
                for y in range(x + 1, min(x + 4, len(bars))):
                    if c3[bars[y]] < rh[x - 1]:
                        fa_up[bars[y]] = True
                        break
            if c3[bars[x]] < rl[x - 1]:
                for y in range(x + 1, min(x + 4, len(bars))):
                    if c3[bars[y]] > rl[x - 1]:
                        fa_dn[bars[y]] = True
                        break
    S.faUp12 = roll_any(fa_up, 12)
    S.faDn12 = roll_any(fa_dn, 12)

    # ---- 1m ingredients
    S.pos = np.full(n, np.nan)
    S.expday = np.zeros(n, bool)
    for d in range(D.n_days):
        i0, i1 = D.day_first[d], D.day_last[d]
        cm = np.maximum.accumulate(D.h[i0:i1 + 1])
        cn = np.minimum.accumulate(D.l[i0:i1 + 1])
        rngd = np.maximum(cm - cn, 1e-9)
        S.pos[i0:i1 + 1] = (D.c[i0:i1 + 1] - cn) / rngd
        if np.isfinite(D.adr[d]):
            S.expday[i0:i1 + 1] = (cm - cn) >= 1.0 * D.adr[d]
    S.barno = np.arange(n) - D.day_first[D.day]
    sp = np.full(n, np.nan)
    ok = np.arange(5, n)
    ok = ok[D.seg_start[ok] <= ok - 5]
    sp[ok] = np.abs(np.log(D.c[ok] / D.c[ok - 5])) / D.adr[D.day[ok]]
    S.speed = sp
    v = sp[np.isfinite(sp)]
    S.sp_q25, S.sp_q75 = float(np.quantile(v, .25)), float(np.quantile(v, .75))
    # trailing-250 ADR percentile per day
    S.adr_pct = np.full(D.n_days, np.nan)
    for d in range(250, D.n_days):
        w = D.adr[d - 250:d]
        w = w[np.isfinite(w)]
        if len(w) > 100 and np.isfinite(D.adr[d]):
            S.adr_pct[d] = float(np.mean(w <= D.adr[d]))
    S.D = D
    return S


def flags(S, T0, btype, side):
    """Bool dict S01..S20 for arrays of touch bars. btype 0 -> effective side from approach."""
    D = S.D
    T0 = np.asarray(T0, int)
    eff = np.where(np.asarray(btype) != 0, btype,
                   np.where(np.asarray(side) < 0, 1, -1))
    sup = eff > 0
    dem = eff < 0
    i15 = S.i15[T0]
    i30 = S.i30[T0]
    ok15 = i15 >= 0
    ok30 = i30 >= 0
    i15c = np.clip(i15, 0, None)
    i30c = np.clip(i30, 0, None)
    p = np.clip(T0 - 1, 0, None)
    day = D.day[T0]
    out = {}
    out["S01"] = ok30 & ((S.trendUp[i30c] & dem) | (S.trendDn[i30c] & sup))
    out["S02"] = ok30 & ((S.trendUp[i30c] & sup) | (S.trendDn[i30c] & dem))
    vw = D.vwap1m[p]
    out["S03"] = np.isfinite(vw) & (((D.c[p] > vw) & dem) | ((D.c[p] < vw) & sup))
    out["S04"] = ok15 & (((S.rsi15[i15c] >= 70) & sup) | ((S.rsi15[i15c] <= 30) & dem))
    out["S05"] = ok15 & S.decel[i15c]
    out["S06"] = np.isfinite(S.speed[T0]) & (S.speed[T0] >= S.sp_q75)
    out["S07"] = np.isfinite(S.speed[T0]) & (S.speed[T0] <= S.sp_q25)
    ap = S.adr_pct[day]
    out["S08"] = np.isfinite(ap) & (ap >= 0.67)
    out["S09"] = np.isfinite(ap) & (ap <= 0.33)
    out["S10"] = S.expday[p]
    out["S11"] = ok15 & (S.volz3max[i15c] >= 3.0)
    out["S12"] = ok15 & np.isfinite(S.volz3mean[i15c]) & (S.volz3mean[i15c] <= -0.5)
    out["S13"] = ok15 & ((S.upSweep12[i15c] & sup) | (S.dnSweep12[i15c] & dem))
    out["S14"] = ok30 & ((S.faUp12[i30c] & sup) | (S.faDn12[i30c] & dem))
    out["S15"] = ok15 & ((S.dispUp6[i15c] & sup) | (S.dispDn6[i15c] & dem))
    out["S16"] = ok15 & S.chop6[i15c]
    out["S17"] = ok30 & S.balTrans[i30c]
    ps = S.pos[p]
    out["S18"] = np.isfinite(ps) & (((ps >= 0.8) & sup) | ((ps <= 0.2) & dem))
    out["S19"] = D.sess[T0] == 2
    out["S20"] = S.barno[T0] <= 90
    return out
