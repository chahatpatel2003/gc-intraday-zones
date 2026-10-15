"""Batch-2 zone generators + C1v2 control (BATCH2_SPECS.md frozen 2026-08-16).

Reuses the Batch-1 episode engine (tools/batch1/batch1_lib.py) unchanged.
"""
from __future__ import annotations

import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
import batch1_lib as B
import gc_data as G

NS_MIN = 60_000_000_000
LADDER = (2, 3, 4, 5, 6, 8, 10, 12)


def prep(D):
    """Augment the Batch-1 data container with Batch-2 needs."""
    if not hasattr(D, "b5"):
        D.b5 = G.resample(D.df, "5min")
        D.b240 = G.resample(D.df, "4h")
        for b in (D.b5, D.b240):
            b["close_ns"] = b["ts_last"].astype("int64") + NS_MIN
        D.v = D.df["volume"].to_numpy(float)
        et = D.df["et_shifted"]
        D.sm = (et.dt.hour * 60 + et.dt.minute).to_numpy(np.int32)
    return D


def _day_exp(D, d, sessions):
    return D.ts[D.day_last[min(d + sessions, D.n_days - 1)]] + NS_MIN


def _adr_at(D, dayix_arr):
    return D.adr[dayix_arr]


def _iou(l1, h1, l2, h2):
    inter = max(0.0, min(h1, h2) - max(l1, l2))
    union = max(h1, h2) - min(l1, l2)
    return inter / union if union > 0 else 0.0


class _GenDedup:
    """Generation-time dedup for rolling snapshot families (IoU>=0.5 vs active)."""
    def __init__(self):
        self.act = []          # (L, H, exp_ns)
    def ok(self, L, H, now_ns, exp_ns):
        self.act = [a for a in self.act if a[2] > now_ns]
        for l2, h2, _ in self.act:
            if _iou(L, H, l2, h2) >= 0.5:
                return False
        self.act.append((L, H, exp_ns))
        return True


# ------------------------------------------------------------------ ZON-007
def gen_zon007(D):
    rows = []
    step = np.timedelta64(15, "m")
    for seg, g in D.b15.groupby("instrument_id", sort=False):
        g = g.reset_index(drop=True)
        rng = (g["high"] - g["low"]).to_numpy()
        body = (g["close"] - g["open"]).abs().to_numpy()
        med20 = pd.Series(rng).rolling(20).median().shift(1).to_numpy()
        bins = g["bin"].to_numpy()
        contig = np.r_[False, np.diff(bins) == step]
        hi, lo = g["high"].to_numpy(), g["low"].to_numpy()
        up = (g["close"] > g["open"]).to_numpy()
        cns = g["close_ns"].to_numpy()
        dayix = np.array([D.day_index[t] for t in g["trade_date"]])
        ev = np.flatnonzero(np.isfinite(med20) & (rng >= 3.0 * med20)
                            & (body >= 0.7 * rng))
        for j in ev:
            a = D.adr[dayix[j]]
            if not np.isfinite(a):
                continue
            i = j - 1
            base = []
            while i >= 0 and len(base) < 4 and contig[i + 1] \
                    and np.isfinite(med20[i]) and rng[i] <= 1.0 * med20[i]:
                base.append(i); i -= 1
            if not base:
                continue
            bl = lo[base].min(); bh = hi[base].max()
            W = bh - bl
            if W < 0.2 or W > 0.5 * a:
                continue
            bt = -1 if up[j] else +1          # up displacement -> demand below
            rows.append(("ZON-007", f"Z7-{seg}-{j}", bl, bh, cns[j],
                         _day_exp(D, dayix[j], 5), seg, bt, "15min",
                         dayix[j], "up" if up[j] else "dn"))
    return B.ztable(rows)


# ------------------------------------------------------------------ ZON-008
def gen_zon008(D):
    rows = []
    for seg, g in D.b30.groupby("instrument_id", sort=False):
        g = g.reset_index(drop=True)
        o, h, l, c = (g[x].to_numpy() for x in ("open", "high", "low", "close"))
        rng = h - l
        med20 = pd.Series(rng).rolling(20).median().shift(1).to_numpy()
        ut = h - np.maximum(o, c)
        lt = np.minimum(o, c) - l
        cns = g["close_ns"].to_numpy()
        dayix = np.array([D.day_index[t] for t in g["trade_date"]])
        big = np.isfinite(med20) & (rng >= 1.5 * med20) & (rng > 0)
        for j in np.flatnonzero(big):
            a = D.adr[dayix[j]]
            if not np.isfinite(a):
                continue
            if ut[j] >= 0.6 * rng[j]:
                L, H, bt, tag = h[j] - 0.5 * ut[j], h[j], +1, "upper"
            elif lt[j] >= 0.6 * rng[j]:
                L, H, bt, tag = l[j], l[j] + 0.5 * lt[j], -1, "lower"
            else:
                continue
            W = H - L
            if W < 0.2 or W > 0.5 * a:
                continue
            rows.append(("ZON-008", f"Z8-{seg}-{j}", L, H, cns[j],
                         _day_exp(D, dayix[j], 5), seg, bt, "30min", dayix[j], tag))
    return B.ztable(rows)


# ------------------------------------------------------------------ ZON-009
def _pivots_1h(D):
    step = np.timedelta64(60, "m")
    out = []          # (conf_ns, conf_day, seg, side, price, gidx)
    for seg, g in D.b60.groupby("instrument_id", sort=False):
        g = g.reset_index(drop=True)
        hi, lo = g["high"].to_numpy(), g["low"].to_numpy()
        bins = g["bin"].to_numpy()
        cns = g["close_ns"].to_numpy()
        dayix = np.array([D.day_index[t] for t in g["trade_date"]])
        for k in range(2, len(g) - 2):
            if (bins[k + 2] - bins[k - 2]) != 4 * step:
                continue
            if hi[k] > hi[k-1] and hi[k] > hi[k-2] and hi[k] > hi[k+1] and hi[k] > hi[k+2]:
                out.append((cns[k+2], dayix[k+2], seg, +1, hi[k], g, k))
            if lo[k] < lo[k-1] and lo[k] < lo[k-2] and lo[k] < lo[k+1] and lo[k] < lo[k+2]:
                out.append((cns[k+2], dayix[k+2], seg, -1, lo[k], g, k))
    return out


def gen_zon009(D):
    rows = []
    n = 0
    for conf_ns, cd, seg, side, price, g, k in _pivots_1h(D):
        cl = g["close"].to_numpy()
        cns = g["close_ns"].to_numpy()
        dayix = np.array([D.day_index[t] for t in g["trade_date"]])
        sub = np.arange(k + 3, len(g))
        sub = sub[(dayix[sub] - cd <= 15) & (cns[sub] > conf_ns)]
        if not len(sub):
            continue
        a = D.adr[dayix[sub]]
        okd = np.isfinite(a)
        if side > 0:
            hit = sub[okd & (cl[sub] > price + 0.15 * a)]
        else:
            hit = sub[okd & (cl[sub] < price - 0.15 * a)]
        if not len(hit):
            continue
        j = int(hit[0])
        ab = D.adr[dayix[j]]
        half = 0.05 * ab
        bt = -1 if side > 0 else +1          # broke above high -> support
        n += 1
        rows.append(("ZON-009", f"Z9-{seg}-{n}", price - half, price + half,
                     cns[j], _day_exp(D, dayix[j], 10), seg, bt, "1h",
                     dayix[j], "RtoS" if side > 0 else "StoR"))
    return B.ztable(rows)


# ------------------------------------------------------------------ profiles
def _hist_edges(vals_lo, vals_hi, weights):
    p0 = vals_lo.min()
    i_lo = np.round((vals_lo - p0) / B.TICK).astype(int)
    i_hi = np.round((vals_hi - p0) / B.TICK).astype(int)
    hist = np.zeros(i_hi.max() + 1)
    for a, b, w in zip(i_lo, i_hi, weights):
        hist[a:b + 1] += w / (b - a + 1)
    poc = int(np.argmax(hist))
    tot = hist.sum()
    lo_i = hi_i = poc; cum = hist[poc]
    while cum < 0.70 * tot:
        left = hist[lo_i - 1] if lo_i > 0 else -1.0
        right = hist[hi_i + 1] if hi_i < len(hist) - 1 else -1.0
        if right >= left:
            hi_i += 1; cum += hist[hi_i]
        else:
            lo_i -= 1; cum += hist[lo_i]
    return p0 + lo_i * B.TICK, p0 + hi_i * B.TICK


# ------------------------------------------------------------------ ZON-010
def gen_zon010(D):
    rows = []
    for d in range(4, D.n_days):
        a = D.adr[d]
        if not np.isfinite(a):
            continue
        seg0 = D.iid[D.day_first[d]]
        i0, i1 = D.day_first[d - 3], D.day_last[d - 1]
        m = np.flatnonzero(D.iid[i0:i1 + 1] == seg0) + i0
        if len(m) < 1000:
            continue
        val, vah = _hist_edges(D.l[m], D.h[m], np.ones(len(m)))
        if vah - val < 0.3 * a:
            continue
        act = D.ts[D.day_first[d]]
        exp = D.ts[D.day_last[d]] + NS_MIN
        half = 0.05 * a
        for ref, tag in ((vah, "upperEdge"), (val, "lowerEdge")):
            rows.append(("ZON-010", f"Z10-{d}-{tag}", ref - half, ref + half,
                         act, exp, seg0, 0, "30min", d, tag))
    return B.ztable(rows)


# ------------------------------------------------------------------ ZON-011
def gen_zon011(D):
    rows = []
    dd = _GenDedup()
    n = len(D.ts)
    for d in range(D.n_days):
        a = D.adr[d]
        if not np.isfinite(a):
            continue
        i0, i1 = D.day_first[d], D.day_last[d]
        i1 = min(i1, D.seg_end[i0])          # opening segment only
        if i1 - i0 < 60:
            continue
        sl = slice(i0, i1 + 1)
        tp = (D.h[sl] + D.l[sl] + D.c[sl]) / 3.0
        v = np.maximum(D.v[sl], 1e-9)
        cw = np.cumsum(v)
        vwap = np.cumsum(v * tp) / cw
        var = np.clip(np.cumsum(v * tp * tp) / cw - vwap ** 2, 0, None)
        sig = np.sqrt(var)
        snaps = np.flatnonzero(D.sm[sl] % 60 == 59)
        snaps = snaps[snaps >= 59]
        seg = D.iid[i0]
        for t in snaps:
            i = i0 + int(t)
            for lvl, bt, tag in ((vwap[t] + 2.0 * sig[t], +1, "up2s"),
                                 (vwap[t] - 2.0 * sig[t], -1, "dn2s")):
                if abs(lvl - D.c[i]) < 0.10 * a:
                    continue
                L, H = lvl - 0.05 * a, lvl + 0.05 * a
                act = D.ts[i] + NS_MIN
                exp = D.ts[min(i + 240, n - 1)] + NS_MIN
                if dd.ok(L, H, act, exp):
                    rows.append(("ZON-011", f"Z11-{d}-{t}-{tag}", L, H, act, exp,
                                 seg, bt, "30min", d, tag))
    return B.ztable(rows)


# ------------------------------------------------------------------ ZON-012
def gen_zon012(D):
    rows = []
    dd = _GenDedup()
    n = len(D.ts)
    snaps = np.flatnonzero(D.sm % 60 == 59)
    for i in snaps:
        d = D.day[i]
        a = D.adr[d]
        if not np.isfinite(a) or i - 359 < D.seg_start[i]:
            continue
        m = slice(i - 359, i + 1)
        val, vah = _hist_edges(D.l[m], D.h[m], D.v[m])
        act = D.ts[i] + NS_MIN
        exp = D.ts[min(i + 240, n - 1)] + NS_MIN
        half = 0.05 * a
        seg = D.iid[i]
        for ref, tag in ((vah, "upperVA"), (val, "lowerVA")):
            if abs(ref - D.c[i]) < 0.05 * a:
                continue
            L, H = ref - half, ref + half
            if dd.ok(L, H, act, exp):
                rows.append(("ZON-012", f"Z12-{i}-{tag}", L, H, act, exp,
                             seg, 0, "1h", d, tag))
    return B.ztable(rows)


# ------------------------------------------------------------------ ZON-013
def gen_zon013(D):
    rows = []
    dd = _GenDedup()
    step = np.timedelta64(5, "m")
    for seg, g in D.b5.groupby("instrument_id", sort=False):
        g = g.reset_index(drop=True)
        h, l, c = g["high"].to_numpy(), g["low"].to_numpy(), g["close"].to_numpy()
        rng = h - l
        bh = pd.Series(h).rolling(12).max().shift(1).to_numpy()
        bl = pd.Series(l).rolling(12).min().shift(1).to_numpy()
        med12 = pd.Series(rng).rolling(12).median().shift(1).to_numpy()
        bins = g["bin"].to_numpy()
        cns = g["close_ns"].to_numpy()
        dayix = np.array([D.day_index[t] for t in g["trade_date"]])
        contig12 = np.zeros(len(g), bool)
        contig12[12:] = (bins[12:] - bins[:-12]) == 12 * step
        a = D.adr[dayix]
        with np.errstate(invalid="ignore"):
            cand = (contig12 & np.isfinite(bh) & np.isfinite(a)
                    & ((bh - bl) <= 0.25 * a) & (rng >= 2.5 * med12)
                    & ((c > bh) | (c < bl)))
        for x in np.flatnonzero(cand):
            L, H = bl[x], bh[x]
            if H - L < 0.3:
                continue
            act = cns[x]
            exp = _day_exp(D, dayix[x], 5)
            if not dd.ok(L, H, act, exp):
                continue
            bt = -1 if c[x] > bh[x] else +1
            rows.append(("ZON-013", f"Z13-{seg}-{x}", L, H, act, exp, seg, bt,
                         "15min", dayix[x], "up" if bt < 0 else "dn"))
    return B.ztable(rows)


# ------------------------------------------------------------------ ZON-014
def _fvgs(frame, minutes, D):
    step = np.timedelta64(minutes, "m")
    out = []
    for seg, g in frame.groupby("instrument_id", sort=False):
        g = g.reset_index(drop=True)
        hi, lo = g["high"].to_numpy(), g["low"].to_numpy()
        bins = g["bin"].to_numpy()
        cns = g["close_ns"].to_numpy()
        dayix = np.array([D.day_index[t] for t in g["trade_date"]])
        for i in range(2, len(g)):
            if bins[i] - bins[i-1] != step or bins[i-1] - bins[i-2] != step:
                continue
            a = D.adr[dayix[i]]
            if not np.isfinite(a):
                continue
            if lo[i] > hi[i - 2]:
                L, H, dr = hi[i - 2], lo[i], -1
            elif hi[i] < lo[i - 2]:
                L, H, dr = hi[i], lo[i - 2], +1
            else:
                continue
            if H - L < 0.2 or H - L > 1.0 * a:
                continue
            out.append((L, H, dr, cns[i], dayix[i], seg))
    out.sort(key=lambda r: r[3])
    return out


def gen_zon014(D):
    f1 = _fvgs(D.b60, 60, D)
    f4 = _fvgs(D.b240, 240, D)
    rows = []
    n = 0
    for L1, H1, dr, act, d, seg in f1:
        for L4, H4, dr4, act4, d4, seg4 in f4:
            if act4 >= act or seg4 != seg or dr4 != dr or d - d4 > 10:
                continue
            inter = min(H1, H4) - max(L1, L4)
            if inter < 0.5 * min(H1 - L1, H4 - L4) or inter <= 0:
                continue
            n += 1
            rows.append(("ZON-014", f"Z14-{n}", max(L1, L4), min(H1, H4), act,
                         _day_exp(D, d, 10), seg, dr, "trav", d, "nested"))
            break
    return B.ztable(rows)


# ------------------------------------------------------------------ ZON-015
def gen_zon015(D):
    z, _ = B.gen_zon002(D)
    z = z.copy()
    z["fam"] = "ZON-015"
    z["zid"] = z["zid"].str.replace("Z2-", "Z15-", regex=False)
    return z


# ------------------------------------------------------------------ C1v2
def gen_shadows_v2(zones, D, occupied):
    """Nearest-eligible non-zone strips per EVALUATION_FRAMEWORK v1.2.

    occupied: concatenated frame of ALL Batch-2 family zones (union blob).
    Returns (shadow_frame, diagnostics dict).
    """
    oL = occupied["L"].to_numpy(); oH = occupied["H"].to_numpy()
    oa = occupied["act"].to_numpy(); oe = occupied["exp"].to_numpy()
    byday = B.zones_by_day(occupied, D)
    rows, kdist, no_ctl = [], {}, 0
    for z in zones.itertuples(index=False):
        W = z.H - z.L
        mid = 0.5 * (z.L + z.H)
        a = D.adr[z.day_created]
        if not np.isfinite(a) or W <= 0:
            no_ctl += 1
            continue
        d0 = int(np.searchsorted(D.ts[D.day_first], z.act, "right") - 1)
        d1 = int(np.searchsorted(D.ts[D.day_first], z.exp, "right") - 1)
        cand = set()
        for d in range(max(d0, 0), min(d1, D.n_days - 1) + 1):
            cand.update(byday.get(d, []))
        cand = np.fromiter(cand, int) if cand else np.array([], int)
        if len(cand):
            tmask = (oa[cand] < z.exp) & (oe[cand] > z.act)
            cand = cand[tmask]
        cL, cH = oL[cand], oH[cand]
        got_any = False
        for side in (+1, -1):
            got = 0
            for k in LADDER:
                off = side * k * W
                if abs(off) > 1.0 * a:
                    break
                sl, sh = mid + off - W / 2, mid + off + W / 2
                if len(cand) and np.any((cL < sh) & (cH > sl)):
                    continue
                rows.append((z.fam, f"{z.zid}-S{side*k:+d}", sl, sh, z.act, z.exp,
                             z.seg, z.btype, None, z.day_created, f"k{side*k:+d}"))
                kdist[k] = kdist.get(k, 0) + 1
                got += 1; got_any = True
                if got == 2:
                    break
        if not got_any:
            no_ctl += 1
    diag = {"k_distribution": kdist, "zones_without_control": int(no_ctl),
            "zones_total": int(len(zones)),
            "shadows": int(len(rows)),
            "shadows_per_zone": round(len(rows) / max(len(zones), 1), 2)}
    return B.ztable(rows), diag


# ------------------------------------------------------------------ spacing
def spacing_stats(zones, D):
    byday = B.zones_by_day(zones, D)
    L = zones["L"].to_numpy(); H = zones["H"].to_numpy()
    gaps, overl = [], 0
    tot = 0
    for d, idxs in byday.items():
        a = D.adr[d]
        if not np.isfinite(a) or len(idxs) < 2:
            continue
        mids = np.sort((L[np.array(idxs)] + H[np.array(idxs)]) / 2)
        gg = np.diff(mids) / a
        gaps.extend(gg.tolist())
        lo = L[np.array(idxs)]; hi = H[np.array(idxs)]
        order = np.argsort(lo)
        ov = np.sum(lo[order][1:] < hi[order][:-1])
        overl += int(ov); tot += len(idxs)
    return {"nn_gap_adr_median": round(float(np.median(gaps)), 3) if gaps else None,
            "nn_gap_adr_p25": round(float(np.quantile(gaps, .25)), 3) if gaps else None,
            "overlap_pair_share": round(overl / max(tot, 1), 3)}


GENS = {"ZON-007": gen_zon007, "ZON-008": gen_zon008, "ZON-009": gen_zon009,
        "ZON-010": gen_zon010, "ZON-011": gen_zon011, "ZON-012": gen_zon012,
        "ZON-013": gen_zon013, "ZON-014": gen_zon014, "ZON-015": gen_zon015}
