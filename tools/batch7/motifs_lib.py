"""Batch-7 motif generators + indicator machinery (BATCH7_MINING_PLAN.md frozen)."""
from __future__ import annotations

import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch5"))
import batch1_lib as B
import batch2_lib as Z
import batch5_lib as F

NS_MIN = 60_000_000_000
FLOOR = 0.05
CAP = 0.5


def prep7(D):
    F.prep5(D)
    if not hasattr(D, "vwap1m"):
        n = len(D.ts)
        D.vwap1m = np.full(n, np.nan)
        D.sig1m = np.full(n, np.nan)
        for d in range(D.n_days):
            i0, i1 = D.day_first[d], min(D.day_last[d], D.seg_end[D.day_first[d]])
            if i1 - i0 < 30:
                continue
            sl = slice(i0, i1 + 1)
            tp = (D.h[sl] + D.l[sl] + D.c[sl]) / 3.0
            v = np.maximum(D.v[sl], 1e-9)
            cw = np.cumsum(v)
            vw = np.cumsum(v * tp) / cw
            var = np.clip(np.cumsum(v * tp * tp) / cw - vw ** 2, 0, None)
            D.vwap1m[sl] = vw
            D.sig1m[sl] = np.sqrt(var)
    return D


def ctx(D, frame):
    g = {}
    g["iid"] = frame["instrument_id"].to_numpy()
    for c in ("open", "high", "low", "close"):
        g[c[0]] = frame[c].to_numpy()
    g["v"] = frame["volume"].to_numpy(float)
    g["rng"] = g["h"] - g["l"]
    g["cns"] = frame["close_ns"].to_numpy()
    g["day"] = np.array([D.day_index[t] for t in frame["trade_date"]])
    g["bins"] = frame["bin"].to_numpy()
    li = np.searchsorted(D.ts, frame["ts_last"].astype("int64").to_numpy(), "left")
    li = np.clip(li, 0, len(D.ts) - 1)
    g["vwap"] = D.vwap1m[li]
    g["sig"] = D.sig1m[li]
    sm = frame["ts_last"].dt.tz_convert("America/New_York")
    g["et_min"] = (sm.dt.hour * 60 + sm.dt.minute).to_numpy()
    return g


def segs(D, frame):
    for seg, gg in frame.groupby("instrument_id", sort=False):
        idx = gg.index.to_numpy()
        yield seg, idx


def med20(x):
    return pd.Series(x).rolling(20).median().shift(1).to_numpy()


def rsi14(close):
    d = np.diff(close, prepend=close[0])
    up = np.clip(d, 0, None)
    dn = np.clip(-d, 0, None)
    au = pd.Series(up).ewm(alpha=1 / 14, adjust=False).mean().to_numpy()
    ad = pd.Series(dn).ewm(alpha=1 / 14, adjust=False).mean().to_numpy()
    rs = au / np.maximum(ad, 1e-12)
    return 100 - 100 / (1 + rs)


def ema(x, span):
    return pd.Series(x).ewm(span=span, adjust=False).mean().to_numpy()


def adx14(h, l, c):
    up = np.diff(h, prepend=h[0])
    dn = -np.diff(l, prepend=l[0])
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.roll(c, 1)),
                                      np.abs(l - np.roll(c, 1))))
    tr[0] = h[0] - l[0]
    atr = pd.Series(tr).ewm(alpha=1 / 14, adjust=False).mean().to_numpy()
    pdi = 100 * pd.Series(pdm).ewm(alpha=1 / 14, adjust=False).mean().to_numpy() / np.maximum(atr, 1e-12)
    ndi = 100 * pd.Series(ndm).ewm(alpha=1 / 14, adjust=False).mean().to_numpy() / np.maximum(atr, 1e-12)
    dx = 100 * np.abs(pdi - ndi) / np.maximum(pdi + ndi, 1e-12)
    return pd.Series(dx).ewm(alpha=1 / 14, adjust=False).mean().to_numpy()


def volz20(v):
    m = pd.Series(v).rolling(20).mean().shift(1).to_numpy()
    s = pd.Series(v).rolling(20).std().shift(1).to_numpy()
    return (v - m) / np.maximum(s, 1e-9)


def _z(D, fam, zid, L, H, act, day, seg, bt, btf, tag, sess_end=False, life=5):
    a = D.adr[day]
    if not np.isfinite(a) or H <= L:
        return None
    if H - L < FLOOR * a:
        mid = 0.5 * (L + H)
        L, H = mid - FLOOR * a / 2, mid + FLOOR * a / 2
    if H - L > CAP * a:
        return None
    exp = (D.ts[D.day_last[day]] + NS_MIN) if sess_end else \
        (D.ts[D.day_last[min(day + life, D.n_days - 1)]] + NS_MIN)
    if act >= exp:
        return None
    return (fam, zid, float(L), float(H), int(act), int(exp), seg, bt, btf, int(day), tag)


class GD:
    def __init__(self):
        self.a = []
    def ok(self, L, H, now, exp):
        self.a = [x for x in self.a if x[2] > now]
        for l2, h2, _ in self.a:
            i = max(0.0, min(H, h2) - max(L, l2))
            u = max(H, h2) - min(L, l2)
            if u > 0 and i / u >= 0.5:
                return False
        self.a.append((L, H, exp))
        return True


# ------------------------------------------------------------------ motifs
def m01(D):          # OR trap
    g = ctx(D, D.b15)
    rows = []
    for seg, ix in segs(D, D.b15):
        days = g["day"][ix]
        for d in np.unique(days):
            bars = ix[days == d]
            if len(bars) < 8:
                continue
            orh = g["h"][bars[:4]].max(); orl = g["l"][bars[:4]].min()
            for side in (1, -1):
                done = False
                for x in range(4, len(bars)):
                    i = bars[x]
                    if done:
                        break
                    br = (g["c"][i] > orh) if side > 0 else (g["c"][i] < orl)
                    if not br:
                        continue
                    for y in range(x + 1, min(x + 4, len(bars))):
                        j = bars[y]
                        if (side > 0 and g["c"][j] < orh) or (side < 0 and g["c"][j] > orl):
                            ext = g["h"][bars[x]:j + 1].max() if side > 0 else g["l"][bars[x]:j + 1].min()
                            z = _z(D, "M01", f"M01-{d}{'U' if side>0 else 'D'}",
                                   orh if side > 0 else ext, ext if side > 0 else orl,
                                   g["cns"][j], d, seg, side, "15min", "ORtrap", sess_end=True)
                            if z:
                                rows.append(z)
                            done = True
                            break
                    else:
                        continue
                    break
    return B.ztable(rows)


def m02(D):          # session-extreme trap
    g = ctx(D, D.b15)
    rows = []
    for seg, ix in segs(D, D.b15):
        days = g["day"][ix]
        for d in np.unique(days):
            bars = ix[days == d]
            if len(bars) < 12:
                continue
            hh = np.maximum.accumulate(g["h"][bars])
            ll = np.minimum.accumulate(g["l"][bars])
            hset = np.zeros(len(bars), int); lset = np.zeros(len(bars), int)
            for x in range(1, len(bars)):
                hset[x] = x if hh[x] > hh[x - 1] else hset[x - 1]
                lset[x] = x if ll[x] < ll[x - 1] else lset[x - 1]
            dd = GD()
            for x in range(8, len(bars)):
                i = bars[x]
                if x - hset[x - 1] >= 8 and g["c"][i] > hh[x - 1]:
                    for y in range(x + 1, min(x + 4, len(bars))):
                        j = bars[y]
                        if g["c"][j] < hh[x - 1]:
                            ext = g["h"][i:j + 1].max()
                            z = _z(D, "M02", f"M02-{d}-{x}U", hh[x - 1], ext,
                                   g["cns"][j], d, seg, +1, "15min", "sesHiTrap", sess_end=True)
                            if z and dd.ok(z[2], z[3], z[4], z[5]):
                                rows.append(z)
                            break
                if x - lset[x - 1] >= 8 and g["c"][i] < ll[x - 1]:
                    for y in range(x + 1, min(x + 4, len(bars))):
                        j = bars[y]
                        if g["c"][j] > ll[x - 1]:
                            ext = g["l"][i:j + 1].min()
                            z = _z(D, "M02", f"M02-{d}-{x}D", ext, ll[x - 1],
                                   g["cns"][j], d, seg, -1, "15min", "sesLoTrap", sess_end=True)
                            if z and dd.ok(z[2], z[3], z[4], z[5]):
                                rows.append(z)
                            break
    return B.ztable(rows)


def m03(D):          # 1-session trap (SCREEN-ONLY)
    g = ctx(D, D.b30)
    rows = []
    for d in range(2, D.n_days):
        seg0 = D.iid[D.day_first[d]]
        i0, i1 = D.day_first[d - 1], D.day_last[d - 1]
        m = np.flatnonzero(D.iid[i0:i1 + 1] == seg0) + i0
        if len(m) < 400:
            continue
        H1, L1 = D.h[m].max(), D.l[m].min()
        bars = np.flatnonzero((g["day"] == d) & (g["iid"] == seg0))
        for side, ref in ((1, H1), (-1, L1)):
            done = False
            for x, i in enumerate(bars):
                if done:
                    break
                if (side > 0 and g["c"][i] > ref) or (side < 0 and g["c"][i] < ref):
                    for j in bars[x + 1:x + 5]:
                        if (side > 0 and g["c"][j] < ref) or (side < 0 and g["c"][j] > ref):
                            ext = g["h"][i:j + 1].max() if side > 0 else g["l"][i:j + 1].min()
                            z = _z(D, "M03", f"M03-{d}{side}", ref if side > 0 else ext,
                                   ext if side > 0 else ref, g["cns"][j], d, seg0,
                                   side, "30min", "1sesTrap")
                            if z:
                                rows.append(z)
                            done = True
                            break
    return B.ztable(rows)


def m04(D):          # VWAP band trap
    g = ctx(D, D.b15)
    rows = []
    for seg, ix in segs(D, D.b15):
        days = g["day"][ix]
        for d in np.unique(days):
            bars = ix[days == d]
            dd = GD()
            for x in range(4, len(bars)):
                i = bars[x]
                if not np.isfinite(g["sig"][i]) or g["sig"][i] <= 0:
                    continue
                up = g["vwap"][i] + 2 * g["sig"][i]
                dn = g["vwap"][i] - 2 * g["sig"][i]
                for side, band in ((1, up), (-1, dn)):
                    if (side > 0 and g["c"][i] > band) or (side < 0 and g["c"][i] < band):
                        for y in range(x + 1, min(x + 4, len(bars))):
                            j = bars[y]
                            b2 = g["vwap"][j] + 2 * side * g["sig"][j]
                            if (side > 0 and g["c"][j] < b2) or (side < 0 and g["c"][j] > b2):
                                ext = g["h"][i:j + 1].max() if side > 0 else g["l"][i:j + 1].min()
                                z = _z(D, "M04", f"M04-{d}-{x}{side}",
                                       band if side > 0 else ext,
                                       ext if side > 0 else band,
                                       g["cns"][j], d, seg, side, "15min", "vwapTrap",
                                       sess_end=True)
                                if z and dd.ok(z[2], z[3], z[4], z[5]):
                                    rows.append(z)
                                break
                        break
    return B.ztable(rows)


def m05(D):          # double attack
    g = ctx(D, D.b15)
    rows = []
    for seg, ix in segs(D, D.b15):
        h = g["h"][ix]; l = g["l"][ix]; c = g["c"][ix]; o = g["o"][ix]
        rng = h - l
        uw = h - np.maximum(o, c)
        lw = np.minimum(o, c) - l
        cns = g["cns"][ix]; day = g["day"][ix]
        dd = GD()
        pu = np.flatnonzero(uw >= 0.3 * np.maximum(rng, 1e-9))
        pl = np.flatnonzero(lw >= 0.3 * np.maximum(rng, 1e-9))
        for arr, side in ((pu, +1), (pl, -1)):
            for j in arr:
                a = D.adr[day[j]]
                if not np.isfinite(a):
                    continue
                prior = arr[(arr >= j - 32) & (arr <= j - 4)]
                for i in prior:
                    ref_i = h[i] if side > 0 else l[i]
                    ref_j = h[j] if side > 0 else l[j]
                    if abs(ref_i - ref_j) > 0.05 * a:
                        continue
                    top = max(ref_i, ref_j); bot = min(ref_i, ref_j)
                    inter = c[i + 1:j + 1]
                    if side > 0 and np.any(inter > top):
                        continue
                    if side < 0 and np.any(inter < bot):
                        continue
                    z = _z(D, "M05", f"M05-{seg}-{j}{side}", bot, top, cns[j],
                           day[j], seg, side, "15min", "dblAttack")
                    if z and dd.ok(z[2], z[3], z[4], z[5]):
                        rows.append(z)
                    break
    return B.ztable(rows)


def m06(D):          # exhaustion reversal
    g = ctx(D, D.b15)
    rows = []
    for seg, ix in segs(D, D.b15):
        o = g["o"][ix]; c = g["c"][ix]; h = g["h"][ix]; l = g["l"][ix]
        rng = h - l
        m20 = med20(rng)
        cns = g["cns"][ix]; day = g["day"][ix]
        up = (c > o).astype(int)
        run = np.zeros(len(ix), int)
        for x in range(1, len(ix)):
            run[x] = run[x - 1] + 1 if up[x] == up[x - 1] else 1
        for x in range(1, len(ix) - 1):
            if run[x] < 4 or not np.isfinite(m20[x]) or rng[x] < 2 * m20[x]:
                continue
            y = x + 1
            body = abs(c[y] - o[y])
            if up[x] == 1 and c[y] < o[y] and body >= 0.7 * max(rng[y], 1e-9) and rng[y] >= m20[y]:
                z = _z(D, "M06", f"M06-{seg}-{x}U", (h[x] + l[x]) / 2, h[x],
                       cns[y], day[y], seg, +1, "15min", "exhUp")
                if z:
                    rows.append(z)
            if up[x] == 0 and c[y] > o[y] and body >= 0.7 * max(rng[y], 1e-9) and rng[y] >= m20[y]:
                z = _z(D, "M06", f"M06-{seg}-{x}D", l[x], (h[x] + l[x]) / 2,
                       cns[y], day[y], seg, -1, "15min", "exhDn")
                if z:
                    rows.append(z)
    return B.ztable(rows)


def m07(D):          # volume climax
    g = ctx(D, D.b30)
    rows = []
    for seg, ix in segs(D, D.b30):
        h = g["h"][ix]; l = g["l"][ix]; c = g["c"][ix]; v = g["v"][ix]
        rng = np.maximum(h - l, 1e-9)
        vm = med20(v)
        cns = g["cns"][ix]; day = g["day"][ix]
        for x in range(20, len(ix)):
            if not np.isfinite(vm[x]) or v[x] < 3 * vm[x]:
                continue
            if h[x] > h[x - 20:x].max() and (c[x] - l[x]) / rng[x] <= 0.5:
                z = _z(D, "M07", f"M07-{seg}-{x}U", (h[x] + l[x]) / 2, h[x],
                       cns[x], day[x], seg, +1, "30min", "volClimaxUp")
                if z:
                    rows.append(z)
            if l[x] < l[x - 20:x].min() and (h[x] - c[x]) / rng[x] <= 0.5:
                z = _z(D, "M07", f"M07-{seg}-{x}D", l[x], (h[x] + l[x]) / 2,
                       cns[x], day[x], seg, -1, "30min", "volClimaxDn")
                if z:
                    rows.append(z)
    return B.ztable(rows)


def m08(D):          # impulse -> pullback base
    g = ctx(D, D.b15)
    rows = []
    for seg, ix in segs(D, D.b15):
        o = g["o"][ix]; c = g["c"][ix]; h = g["h"][ix]; l = g["l"][ix]
        rng = h - l
        m20 = med20(rng)
        cns = g["cns"][ix]; day = g["day"][ix]
        for x in range(1, len(ix) - 6):
            if not np.isfinite(m20[x]) or rng[x] < 2.5 * m20[x] or \
                    abs(c[x] - o[x]) < 0.7 * max(rng[x], 1e-9):
                continue
            side = +1 if c[x] > o[x] else -1
            e = x + 1
            while e < min(x + 5, len(ix)) and np.isfinite(m20[e]) and rng[e] <= m20[e]:
                e += 1
            nb = e - (x + 1)
            if nb < 2:
                continue
            bl, bh = l[x + 1:e].min(), h[x + 1:e].max()
            if side > 0 and bl <= o[x]:
                continue
            if side < 0 and bh >= o[x]:
                continue
            if e >= len(ix):
                continue
            if side > 0 and c[e] > bh:
                z = _z(D, "M08", f"M08-{seg}-{x}", bl, bh, cns[e], day[e], seg,
                       -1, "15min", "impBaseUp")
                if z:
                    rows.append(z)
            if side < 0 and c[e] < bl:
                z = _z(D, "M08", f"M08-{seg}-{x}", bl, bh, cns[e], day[e], seg,
                       +1, "15min", "impBaseDn")
                if z:
                    rows.append(z)
    return B.ztable(rows)


def m09(D):          # NR7 release
    g = ctx(D, D.b30)
    rows = []
    for seg, ix in segs(D, D.b30):
        h = g["h"][ix]; l = g["l"][ix]; c = g["c"][ix]
        rng = h - l
        m20 = med20(rng)
        cns = g["cns"][ix]; day = g["day"][ix]
        for x in range(7, len(ix) - 1):
            if rng[x] > rng[x - 6:x].min():
                continue
            y = x + 1
            if not np.isfinite(m20[y]) or rng[y] < 1.5 * m20[y]:
                continue
            if c[y] > h[x]:
                z = _z(D, "M09", f"M09-{seg}-{x}", l[x], h[x], cns[y], day[y],
                       seg, -1, "30min", "nr7Up")
            elif c[y] < l[x]:
                z = _z(D, "M09", f"M09-{seg}-{x}", l[x], h[x], cns[y], day[y],
                       seg, +1, "30min", "nr7Dn")
            else:
                continue
            if z:
                rows.append(z)
    return B.ztable(rows)


def m10(D):          # balance break -> return (CONTINUATION)
    g = ctx(D, D.b30)
    rows = []
    for seg, ix in segs(D, D.b30):
        h = g["h"][ix]; l = g["l"][ix]; c = g["c"][ix]
        rng = h - l
        m20 = med20(rng)
        cns = g["cns"][ix]; day = g["day"][ix]
        dd = GD()
        for x in range(6, len(ix)):
            a = D.adr[day[x]]
            if not (np.isfinite(a) and np.isfinite(m20[x])):
                continue
            bh = h[x - 6:x].max(); bl = l[x - 6:x].min()
            if bh - bl > 0.35 * a or rng[x] < 1.5 * m20[x]:
                continue
            if c[x] > bh:
                bt = +1          # entered later from above; continuation = traverse down
            elif c[x] < bl:
                bt = -1
            else:
                continue
            z = _z(D, "M10", f"M10-{seg}-{x}", bl, bh, cns[x], day[x], seg,
                   bt, None, "balanceCont")
            if z and dd.ok(z[2], z[3], z[4], z[5]):
                rows.append(z)
    return B.ztable(rows)


def m11(D):          # three declining probes
    g = ctx(D, D.b15)
    rows = []
    for seg, ix in segs(D, D.b15):
        h = g["h"][ix]; l = g["l"][ix]; c = g["c"][ix]
        rng = h - l
        cns = g["cns"][ix]; day = g["day"][ix]
        nh = [x for x in range(20, len(ix)) if h[x] > h[x - 20:x].max()]
        nl = [x for x in range(20, len(ix)) if l[x] < l[x - 20:x].min()]
        for arr, side in ((nh, +1), (nl, -1)):
            for t in range(2, len(arr)):
                p1, p2, p3 = arr[t - 2], arr[t - 1], arr[t]
                if p3 - p1 > 40 or p3 + 1 >= len(ix):
                    continue
                a = D.adr[day[p3]]
                if not np.isfinite(a):
                    continue
                if side > 0:
                    if not (h[p2] - h[p1] <= 0.15 * a and h[p3] - h[p2] <= 0.15 * a):
                        continue
                    if not (rng[p1] > rng[p2] > rng[p3]):
                        continue
                    if c[p3 + 1] >= l[p3]:
                        continue
                    z = _z(D, "M11", f"M11-{seg}-{p3}U", h[p2], h[p3],
                           cns[p3 + 1], day[p3 + 1], seg, +1, "15min", "probes3U")
                else:
                    if not (l[p1] - l[p2] <= 0.15 * a and l[p2] - l[p3] <= 0.15 * a):
                        continue
                    if not (rng[p1] > rng[p2] > rng[p3]):
                        continue
                    if c[p3 + 1] <= h[p3]:
                        continue
                    z = _z(D, "M11", f"M11-{seg}-{p3}D", l[p3], l[p2],
                           cns[p3 + 1], day[p3 + 1], seg, -1, "15min", "probes3D")
                if z:
                    rows.append(z)
    return B.ztable(rows)


def m12(D):          # NY-open fade
    g = ctx(D, D.b15)
    rows = []
    for seg, ix in segs(D, D.b15):
        o = g["o"][ix]; c = g["c"][ix]; h = g["h"][ix]; l = g["l"][ix]
        rng = h - l
        m20 = med20(rng)
        cns = g["cns"][ix]; day = g["day"][ix]; em = g["et_min"][ix]
        for d in np.unique(day):
            bars = np.flatnonzero(day == d)
            ny = bars[(em[bars] >= 500) & (em[bars] < 560)]
            ny = [x for x in ny if em[x] >= 500 and (x == bars[0] or em[x - 1] < 500)]
            if not ny:
                continue
            x = ny[0]
            if x + 2 >= len(ix) or not np.isfinite(m20[x]) or rng[x] < 2 * m20[x]:
                continue
            if c[x] > o[x]:
                if h[x] - l[x + 1:x + 3].min() >= 0.6 * rng[x]:
                    z = _z(D, "M12", f"M12-{d}", (h[x] + l[x]) / 2, h[x],
                           cns[x + 2], d, seg, +1, "15min", "nyFadeU", sess_end=True)
                    if z:
                        rows.append(z)
            else:
                if h[x + 1:x + 3].max() - l[x] >= 0.6 * rng[x]:
                    z = _z(D, "M12", f"M12-{d}", l[x], (h[x] + l[x]) / 2,
                           cns[x + 2], d, seg, -1, "15min", "nyFadeD", sess_end=True)
                    if z:
                        rows.append(z)
    return B.ztable(rows)


def m13(D):          # VWAP whipsaw
    g = ctx(D, D.b30)
    rows = []
    for seg, ix in segs(D, D.b30):
        c = g["c"][ix]; h = g["h"][ix]; l = g["l"][ix]
        vw = g["vwap"][ix]
        cns = g["cns"][ix]; day = g["day"][ix]
        for d in np.unique(day):
            bars = np.flatnonzero(day == d)
            done = False
            for t in range(3, len(bars) - 1):
                if done:
                    break
                i = bars[t]
                if not np.isfinite(vw[i]):
                    continue
                above = c[bars[t - 3:t]] > vw[bars[t - 3:t]]
                if above.all() and c[i] < vw[i]:
                    for y in range(t + 1, min(t + 3, len(bars))):
                        j = bars[y]
                        if c[j] > vw[j]:
                            ext = l[i:j + 1].min()
                            z = _z(D, "M13", f"M13-{d}", ext, float(vw[j]),
                                   cns[j], d, seg, -1, "30min", "whipDn", sess_end=True)
                            if z:
                                rows.append(z)
                            done = True
                            break
                if (~above).all() and c[i] > vw[i]:
                    for y in range(t + 1, min(t + 3, len(bars))):
                        j = bars[y]
                        if c[j] < vw[j]:
                            ext = h[i:j + 1].max()
                            z = _z(D, "M13", f"M13-{d}", float(vw[j]), ext,
                                   cns[j], d, seg, +1, "30min", "whipUp", sess_end=True)
                            if z:
                                rows.append(z)
                            done = True
                            break
    return B.ztable(rows)


def m14(D):          # high-volume base
    g = ctx(D, D.b30)
    rows = []
    for seg, ix in segs(D, D.b30):
        c = g["c"][ix]; h = g["h"][ix]; l = g["l"][ix]; v = g["v"][ix]
        rng = h - l
        m20 = med20(rng)
        vm = med20(v)
        cns = g["cns"][ix]; day = g["day"][ix]
        for x in range(20, len(ix) - 4):
            if not (np.isfinite(m20[x]) and np.isfinite(vm[x])):
                continue
            for nb in (2, 3):
                base = slice(x, x + nb)
                if np.any(rng[base] > m20[x]) or v[base].sum() < 2 * nb * vm[x]:
                    continue
                y = x + nb
                if y >= len(ix) or rng[y] < 2 * m20[y]:
                    continue
                bl, bh = l[base].min(), h[base].max()
                if c[y] > bh:
                    z = _z(D, "M14", f"M14-{seg}-{x}", bl, bh, cns[y], day[y],
                           seg, -1, "30min", "hvBaseUp")
                elif c[y] < bl:
                    z = _z(D, "M14", f"M14-{seg}-{x}", bl, bh, cns[y], day[y],
                           seg, +1, "30min", "hvBaseDn")
                else:
                    continue
                if z:
                    rows.append(z)
                break
    return B.ztable(rows)


def m15(D):          # RSI divergence probe
    g = ctx(D, D.b15)
    rows = []
    for seg, ix in segs(D, D.b15):
        h = g["h"][ix]; l = g["l"][ix]; c = g["c"][ix]
        r = rsi14(c)
        cns = g["cns"][ix]; day = g["day"][ix]
        lastH = None
        lastL = None
        for x in range(20, len(ix)):
            if h[x] > h[x - 20:x].max():
                if lastH and x - lastH[0] <= 60 and r[x] < lastH[2] and h[x] > lastH[1]:
                    for j in range(x + 1, min(x + 4, len(ix))):
                        if c[j] < lastH[1]:
                            z = _z(D, "M15", f"M15-{seg}-{x}U", lastH[1], h[x],
                                   cns[j], day[j], seg, +1, "15min", "rsiDivU")
                            if z:
                                rows.append(z)
                            break
                lastH = (x, h[x], r[x])
            if l[x] < l[x - 20:x].min():
                if lastL and x - lastL[0] <= 60 and r[x] > lastL[2] and l[x] < lastL[1]:
                    for j in range(x + 1, min(x + 4, len(ix))):
                        if c[j] > lastL[1]:
                            z = _z(D, "M15", f"M15-{seg}-{x}D", l[x], lastL[1],
                                   cns[j], day[j], seg, -1, "15min", "rsiDivD")
                            if z:
                                rows.append(z)
                            break
                lastL = (x, l[x], r[x])
    return B.ztable(rows)


def m16(D):          # trend pullback to EMA20 snapshot
    g = ctx(D, D.b30)
    rows = []
    for seg, ix in segs(D, D.b30):
        c = g["c"][ix]
        e20 = ema(c, 20); e50 = ema(c, 50)
        cns = g["cns"][ix]; day = g["day"][ix]
        dd = GD()
        above = c > e20
        for x in range(55, len(ix)):
            a = D.adr[day[x]]
            if not np.isfinite(a):
                continue
            if e20[x] > e50[x] and e20[x] > e20[x - 1] and e50[x] > e50[x - 1] \
                    and above[x - 5:x].all() and c[x] - e20[x] <= 0.20 * a \
                    and c[x] - (e20[x] + FLOOR * a) >= 0.10 * a:
                z = _z(D, "M16", f"M16-{seg}-{x}U", e20[x] - FLOOR * a,
                       e20[x] + FLOOR * a, cns[x], day[x], seg, -1, "30min", "emaPbU")
                if z and dd.ok(z[2], z[3], z[4], z[5]):
                    rows.append(z)
            if e20[x] < e50[x] and e20[x] < e20[x - 1] and e50[x] < e50[x - 1] \
                    and (~above[x - 5:x]).all() and e20[x] - c[x] <= 0.20 * a \
                    and (e20[x] - FLOOR * a) - c[x] >= 0.10 * a:
                z = _z(D, "M16", f"M16-{seg}-{x}D", e20[x] - FLOOR * a,
                       e20[x] + FLOOR * a, cns[x], day[x], seg, +1, "30min", "emaPbD")
                if z and dd.ok(z[2], z[3], z[4], z[5]):
                    rows.append(z)
    return B.ztable(rows)


MOTIFS = {"M01": m01, "M02": m02, "M03": m03, "M04": m04, "M05": m05, "M06": m06,
          "M07": m07, "M08": m08, "M09": m09, "M10": m10, "M11": m11, "M12": m12,
          "M13": m13, "M14": m14, "M15": m15, "M16": m16}
CONTINUATION = {"M10"}
SCREEN_ONLY = {"M03"}
