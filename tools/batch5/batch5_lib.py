"""Batch-5 zone generators (BATCH5_SPECS.md frozen 2026-08-16)."""
from __future__ import annotations

import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
import batch1_lib as B
import batch2_lib as Z
import gc_data as G

NS_MIN = 60_000_000_000


def prep5(D):
    Z.prep(D)
    if "1d" not in D.break_frames:
        b1d = G.resample(D.df, "1d")
        b1d["close_ns"] = b1d["ts_last"].astype("int64") + NS_MIN
        b1d["bin"] = pd.NaT
        D.b1d = b1d
        D.break_frames["1d"] = b1d
    return D


def _seg_frames(frame, step_min, D):
    """Yield per-segment reset frames with common arrays."""
    step = np.timedelta64(step_min, "m")
    for seg, g in frame.groupby("instrument_id", sort=False):
        g = g.reset_index(drop=True)
        yield seg, g, step


def _pivots(g, step, D):
    """Confirmed fractal pivots (k=2). Returns (highs, lows): lists of
    (bar_k, price, conf_ns, conf_day)."""
    hi, lo = g["high"].to_numpy(), g["low"].to_numpy()
    bins = g["bin"].to_numpy()
    cns = g["close_ns"].to_numpy()
    dayix = np.array([D.day_index[t] for t in g["trade_date"]])
    H, L = [], []
    for k in range(2, len(g) - 2):
        if (bins[k + 2] - bins[k - 2]) != 4 * step:
            continue
        if hi[k] > hi[k-1] and hi[k] > hi[k-2] and hi[k] > hi[k+1] and hi[k] > hi[k+2]:
            H.append((k, hi[k], cns[k + 2], dayix[k + 2]))
        if lo[k] < lo[k-1] and lo[k] < lo[k-2] and lo[k] < lo[k+1] and lo[k] < lo[k+2]:
            L.append((k, lo[k], cns[k + 2], dayix[k + 2]))
    return H, L


def _exp(D, d, sessions):
    return D.ts[D.day_last[min(d + sessions, D.n_days - 1)]] + NS_MIN


def _wfloor(L, H, floor):
    if H - L >= floor:
        return L, H
    mid = 0.5 * (L + H)
    return mid - floor / 2, mid + floor / 2


# ---------------------------------------------------------------- ZON-026 QML
def gen_zon026(D):
    rows = []
    for seg, g, step in _seg_frames(D.b30, 30, D):
        hi, lo, cl = g["high"].to_numpy(), g["low"].to_numpy(), g["close"].to_numpy()
        cns = g["close_ns"].to_numpy()
        dayix = np.array([D.day_index[t] for t in g["trade_date"]])
        H, L = _pivots(g, step, D)
        lows_k = np.array([p[0] for p in L]) if L else np.array([], int)
        highs_k = np.array([p[0] for p in H]) if H else np.array([], int)
        # bearish QM: H1 -> L1 -> sweep above h1 -> close below l1
        for (kh, h1, t1, d1) in H:
            nxt = lows_k[lows_k > kh]
            if not len(nxt):
                continue
            kl = int(nxt[0])
            l1 = lo[kl]
            lim = np.searchsorted(dayix, d1 + 16)
            js = np.flatnonzero(hi[kl + 1:lim] > h1) + kl + 1
            if not len(js):
                continue
            j = int(js[0])
            bs = np.flatnonzero(cl[j:lim] < l1) + j
            if not len(bs):
                continue
            b = int(bs[0])
            zl, zh = _wfloor(h1, float(hi[j:b + 1].max()), 0.05 * D.adr[dayix[b]]) \
                if np.isfinite(D.adr[dayix[b]]) else (None, None)
            if zl is None or zh - zl > 0.5 * D.adr[dayix[b]]:
                continue
            rows.append(("ZON-026", f"Z26-{seg}-{kh}H", zl, zh, cns[b],
                         _exp(D, dayix[b], 10), seg, +1, "30min", dayix[b], "bearQM"))
        # bullish mirrored: L1 -> H1 -> sweep below l1 -> close above h1
        for (kl, l1, t1, d1) in L:
            nxt = highs_k[highs_k > kl]
            if not len(nxt):
                continue
            kh = int(nxt[0])
            h1 = hi[kh]
            lim = np.searchsorted(dayix, d1 + 16)
            js = np.flatnonzero(lo[kh + 1:lim] < l1) + kh + 1
            if not len(js):
                continue
            j = int(js[0])
            bs = np.flatnonzero(cl[j:lim] > h1) + j
            if not len(bs):
                continue
            b = int(bs[0])
            a = D.adr[dayix[b]]
            if not np.isfinite(a):
                continue
            zl, zh = _wfloor(float(lo[j:b + 1].min()), l1, 0.05 * a)
            if zh - zl > 0.5 * a:
                continue
            rows.append(("ZON-026", f"Z26-{seg}-{kl}L", zl, zh, cns[b],
                         _exp(D, dayix[b], 10), seg, -1, "30min", dayix[b], "bullQM"))
    return B.ztable(rows)


# ------------------------------------------------------------- ZON-027 breaker
def _latest_pivot(gn, pivots, cns):
    """Per-bar (price, pivot_id) of the most recent pivot with conf_ns <= bar close."""
    price = np.full(gn, np.nan)
    pid = np.full(gn, -1)
    ps = sorted(pivots, key=lambda p: p[2])
    j = 0
    cur_p, cur_i = np.nan, -1
    for i in range(gn):
        while j < len(ps) and ps[j][2] <= cns[i]:
            cur_p, cur_i = ps[j][1], j
            j += 1
        price[i] = cur_p
        pid[i] = cur_i
    return price, pid


def gen_zon027(D):
    rows = []
    for seg, g, step in _seg_frames(D.b30, 30, D):
        o, h, l, c = (g[x].to_numpy() for x in ("open", "high", "low", "close"))
        rng = h - l
        med20 = pd.Series(rng).rolling(20).median().shift(1).to_numpy()
        cns = g["close_ns"].to_numpy()
        dayix = np.array([D.day_index[t] for t in g["trade_date"]])
        H, L = _pivots(g, step, D)
        hp, hid = _latest_pivot(len(g), H, cns)
        lp, lid = _latest_pivot(len(g), L, cns)
        broken_h, broken_l = set(), set()
        for i in range(1, len(g)):
            a = D.adr[dayix[i]]
            if not (np.isfinite(med20[i]) and np.isfinite(a)):
                continue
            if rng[i] < 1.5 * med20[i]:
                continue
            # bullish: close breaks last pivot high (first time)
            if np.isfinite(hp[i]) and c[i] > hp[i] and hid[i] not in broken_h \
                    and c[i - 1] <= hp[i]:
                broken_h.add(hid[i])
                for k in range(i - 1, max(i - 11, -1), -1):
                    if c[k] < o[k]:
                        zl, zh = min(o[k], c[k]), max(o[k], c[k])
                        if 0.2 <= zh - zl <= 0.5 * a:
                            rows.append(("ZON-027", f"Z27-{seg}-{i}B", zl, zh, cns[i],
                                         _exp(D, dayix[i], 10), seg, -1, "30min",
                                         dayix[i], "bullBreaker"))
                        break
            # bearish mirrored
            if np.isfinite(lp[i]) and c[i] < lp[i] and lid[i] not in broken_l \
                    and c[i - 1] >= lp[i]:
                broken_l.add(lid[i])
                for k in range(i - 1, max(i - 11, -1), -1):
                    if c[k] > o[k]:
                        zl, zh = min(o[k], c[k]), max(o[k], c[k])
                        if 0.2 <= zh - zl <= 0.5 * a:
                            rows.append(("ZON-027", f"Z27-{seg}-{i}S", zl, zh, cns[i],
                                         _exp(D, dayix[i], 10), seg, +1, "30min",
                                         dayix[i], "bearBreaker"))
                        break
    return B.ztable(rows)


# ---------------------------------------------------------------- ZON-028 trap
def gen_zon028(D):
    rows = []
    b = D.b30
    iid = b["instrument_id"].to_numpy()
    h, l, c = b["high"].to_numpy(), b["low"].to_numpy(), b["close"].to_numpy()
    cns = b["close_ns"].to_numpy()
    dayix = np.array([D.day_index[t] for t in b["trade_date"]])
    for d in range(4, D.n_days):
        a = D.adr[d]
        if not np.isfinite(a):
            continue
        seg0 = D.iid[D.day_first[d]]
        i0, i1 = D.day_first[d - 3], D.day_last[d - 1]
        m = np.flatnonzero(D.iid[i0:i1 + 1] == seg0) + i0
        if len(m) < 1000:
            continue
        H3, L3 = float(D.h[m].max()), float(D.l[m].min())
        bars = np.flatnonzero((dayix == d) & (iid == seg0))
        done_bull = done_bear = False
        for x, i in enumerate(bars):
            if not done_bull and c[i] > H3:
                for j in bars[x + 1:x + 5]:
                    if c[j] < H3:
                        exc = float(h[i:j + 1].max())
                        zl, zh = _wfloor(H3, exc, 0.05 * a)
                        if zh - zl <= 0.5 * a:
                            rows.append(("ZON-028", f"Z28-{d}-B", zl, zh, cns[j],
                                         _exp(D, d, 5), seg0, +1, "30min", d, "bullTrap"))
                        done_bull = True
                        break
            if not done_bear and c[i] < L3:
                for j in bars[x + 1:x + 5]:
                    if c[j] > L3:
                        exc = float(l[i:j + 1].min())
                        zl, zh = _wfloor(exc, L3, 0.05 * a)
                        if zh - zl <= 0.5 * a:
                            rows.append(("ZON-028", f"Z28-{d}-S", zl, zh, cns[j],
                                         _exp(D, d, 5), seg0, -1, "30min", d, "bearTrap"))
                        done_bear = True
                        break
            if done_bull and done_bear:
                break
    return B.ztable(rows)


# --------------------------------------------------------------- ZON-029 sweep
def gen_zon029(D):
    rows = []
    for seg, g, step in _seg_frames(D.b15, 15, D):
        o, h, l, c = (g[x].to_numpy() for x in ("open", "high", "low", "close"))
        rng = h - l
        med20 = pd.Series(rng).rolling(20).median().shift(1).to_numpy()
        cns = g["close_ns"].to_numpy()
        dayix = np.array([D.day_index[t] for t in g["trade_date"]])
        H, L = _pivots(g, step, D)
        for j in range(2, len(g) - 2):
            a = D.adr[dayix[j]]
            if not np.isfinite(a):
                continue
            # sweep of a pivot high
            cand = [p for p in H if p[0] + 2 < j and j - p[0] >= 8
                    and h[j] > p[1] and c[j] < p[1]]
            if cand:
                for m_ in (j + 1, j + 2):
                    if m_ >= len(g) or not np.isfinite(med20[m_]):
                        continue
                    if rng[m_] >= 2.0 * med20[m_] and c[m_] < l[j]:
                        zl, zh = _wfloor(max(o[j], c[j]), h[j], 0.05 * a)
                        if zh - zl <= 0.5 * a:
                            rows.append(("ZON-029", f"Z29-{seg}-{j}H", zl, zh, cns[m_],
                                         _exp(D, dayix[m_], 5), seg, +1, "15min",
                                         dayix[m_], "sweepHigh"))
                        break
            cand = [p for p in L if p[0] + 2 < j and j - p[0] >= 8
                    and l[j] < p[1] and c[j] > p[1]]
            if cand:
                for m_ in (j + 1, j + 2):
                    if m_ >= len(g) or not np.isfinite(med20[m_]):
                        continue
                    if rng[m_] >= 2.0 * med20[m_] and c[m_] > h[j]:
                        zl, zh = _wfloor(l[j], min(o[j], c[j]), 0.05 * a)
                        if zh - zl <= 0.5 * a:
                            rows.append(("ZON-029", f"Z29-{seg}-{j}L", zl, zh, cns[m_],
                                         _exp(D, dayix[m_], 5), seg, -1, "15min",
                                         dayix[m_], "sweepLow"))
                        break
    return B.ztable(rows)


# ------------------------------------------------------------------ ZON-030 OB
def gen_zon030(D):
    rows = []
    for seg, g, step in _seg_frames(D.b60, 60, D):
        o, h, l, c = (g[x].to_numpy() for x in ("open", "high", "low", "close"))
        rng = h - l
        body = np.abs(c - o)
        med20 = pd.Series(rng).rolling(20).median().shift(1).to_numpy()
        cns = g["close_ns"].to_numpy()
        dayix = np.array([D.day_index[t] for t in g["trade_date"]])
        H, L = _pivots(g, step, D)
        hp, _ = _latest_pivot(len(g), H, cns)
        lp, _ = _latest_pivot(len(g), L, cns)
        for i in range(1, len(g)):
            a = D.adr[dayix[i]]
            if not (np.isfinite(med20[i]) and np.isfinite(a)):
                continue
            if rng[i] < 2.0 * med20[i] or body[i] < 0.7 * rng[i]:
                continue
            if c[i] > o[i] and np.isfinite(hp[i]) and c[i] > hp[i]:
                dr, tag = -1, "bullOB"          # demand below
                opp = lambda k: c[k] < o[k]
            elif c[i] < o[i] and np.isfinite(lp[i]) and c[i] < lp[i]:
                dr, tag = +1, "bearOB"
                opp = lambda k: c[k] > o[k]
            else:
                continue
            for k in range(i - 1, max(i - 4, -1), -1):
                if opp(k):
                    zl, zh = float(l[k]), float(h[k])
                    if 0.2 <= zh - zl <= 0.5 * a:
                        rows.append(("ZON-030", f"Z30-{seg}-{i}", zl, zh, cns[i],
                                     _exp(D, dayix[i], 10), seg, dr, "1h",
                                     dayix[i], tag))
                    break
    return B.ztable(rows)


# ------------------------------------------------------------- ZON-031 weekly
def gen_zon031(D):
    rows = []
    wk = {}
    for d, date in enumerate(D.days):
        iso = pd.Timestamp(date).isocalendar()
        wk.setdefault((iso[0], iso[1]), []).append(d)
    weeks = [v for _, v in sorted(wk.items())]
    for w in range(1, len(weeks)):
        cur, prev = weeks[w], weeks[w - 1]
        d0 = cur[0]
        a = D.adr[d0]
        if not np.isfinite(a):
            continue
        seg0 = D.iid[D.day_first[d0]]
        i0, i1 = D.day_first[prev[0]], D.day_last[prev[-1]]
        m = np.flatnonzero(D.iid[i0:i1 + 1] == seg0) + i0
        if len(m) < 2000:
            continue
        wh, wl = float(D.h[m].max()), float(D.l[m].min())
        R = wh - wl
        if R <= 0:
            continue
        wu = min(0.15 * R, 1.0 * a)
        act = D.ts[D.day_first[d0]]
        exp = D.ts[D.day_last[cur[-1]]] + NS_MIN
        rows.append(("ZON-031", f"Z31-{w}U", wh - wu, wh, act, exp, seg0, +1,
                     "1d", d0, "wkUpper"))
        rows.append(("ZON-031", f"Z31-{w}L", wl, wl + wu, act, exp, seg0, -1,
                     "1d", d0, "wkLower"))
    return B.ztable(rows)


# ---------------------------------------------------------------- ZON-032 LVN
def _smooth(x, k=5):
    ker = np.ones(k) / k
    return np.convolve(x, ker, mode="same")


def gen_zon032(D):
    rows = []
    for d in range(3, D.n_days):
        a = D.adr[d]
        if not np.isfinite(a):
            continue
        seg0 = D.iid[D.day_first[d]]
        i0, i1 = D.day_first[d - 2], D.day_last[d - 1]
        m = np.flatnonzero(D.iid[i0:i1 + 1] == seg0) + i0
        if len(m) < 800:
            continue
        lo, hi, vol = D.l[m], D.h[m], D.v[m]
        p0 = lo.min()
        il = np.round((lo - p0) / B.TICK).astype(int)
        ih = np.round((hi - p0) / B.TICK).astype(int)
        hist = np.zeros(ih.max() + 1)
        for aa, bb, vv in zip(il, ih, vol):
            hist[aa:bb + 1] += vv / (bb - aa + 1)
        s = _smooth(hist)
        pk = [i for i in range(2, len(s) - 2)
              if s[i] >= s[i-1] and s[i] >= s[i-2] and s[i] >= s[i+1] and s[i] >= s[i+2]
              and s[i] > 0]
        pk.sort(key=lambda i: -s[i])
        sep = int(round(0.3 * a / B.TICK))
        pair = None
        for x in range(len(pk)):
            for y in range(x + 1, len(pk)):
                if abs(pk[x] - pk[y]) >= sep:
                    pair = (min(pk[x], pk[y]), max(pk[x], pk[y]))
                    break
            if pair:
                break
        if not pair:
            continue
        p1, p2 = pair
        seg_v = s[p1:p2 + 1]
        lvn = p1 + int(np.argmin(seg_v))
        pmin = min(s[p1], s[p2])
        if s[lvn] > 0.4 * pmin:
            continue
        thr = 0.5 * pmin
        lo_i = lvn
        while lo_i - 1 > p1 and s[lo_i - 1] <= thr:
            lo_i -= 1
        hi_i = lvn
        while hi_i + 1 < p2 and s[hi_i + 1] <= thr:
            hi_i += 1
        zl, zh = p0 + lo_i * B.TICK, p0 + hi_i * B.TICK
        if zh - zl < 0.3 or zh - zl > 0.5 * a:
            continue
        act = D.ts[D.day_first[d]]
        exp = D.ts[D.day_last[d]] + NS_MIN
        rows.append(("ZON-032", f"Z32-{d}", zl, zh, act, exp, seg0, 0, "30min",
                     d, "lvn"))
    return B.ztable(rows)


# ----------------------------------------------------------- ZON-033 quantile
def gen_zon033(D):
    rows = []
    for d in range(3, D.n_days):
        a = D.adr[d]
        if not np.isfinite(a):
            continue
        seg0 = D.iid[D.day_first[d]]
        i0, i1 = D.day_first[d - 2], D.day_last[d - 1]
        m = np.flatnonzero(D.iid[i0:i1 + 1] == seg0) + i0
        if len(m) < 800:
            continue
        cl = D.c[m]
        q025, q10, q90, q975 = np.quantile(cl, [0.025, 0.10, 0.90, 0.975])
        act = D.ts[D.day_first[d]]
        exp = D.ts[D.day_last[d]] + NS_MIN
        for zl, zh, bt, tag in ((q025, q10, -1, "lowTail"), (q90, q975, +1, "highTail")):
            if 0.2 <= zh - zl <= 0.5 * a:
                rows.append(("ZON-033", f"Z33-{d}-{tag}", float(zl), float(zh),
                             act, exp, seg0, bt, "30min", d, tag))
    return B.ztable(rows)


GENS5 = {"ZON-026": gen_zon026, "ZON-027": gen_zon027, "ZON-028": gen_zon028,
         "ZON-029": gen_zon029, "ZON-030": gen_zon030, "ZON-031": gen_zon031,
         "ZON-032": gen_zon032, "ZON-033": gen_zon033}
