"""Batch-1 zone-location engine (discovery 2016-2021 GC only).

Implements ZONE_SPEC v1.1 + EVALUATION_FRAMEWORK v1.1 exactly:
- 6 preregistered families (ZON-001..006), one frozen spec each
- episode engine with T0-bar FE/AE conventions, dual rejection defs, fixed
  trading-minute horizons {5,15,30,60,120}, segment-bounded paths
- C1 displaced shadows (+/-2W, +/-4W) with availability rules
- C2 moment-matched pseudo-zones (K=5, 96 context cells, non-zone areas only)
- two-layer dedup (family events, cross-family interaction clusters)
- day-block bootstrap (seed 20260816), preregistered classification
"""
from __future__ import annotations

import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
import gc_data as G

HORIZONS = (5, 15, 30, 60, 120)
SEED = 20260816
TICK = 0.1
EP_CAP = 480          # episode end search cap (bars)
SEP_RUN = 5           # separation: consecutive bars fully 1W beyond P0
LOOKBACK = 30         # approach-side lookback bars
DEDUP_BARS = 30       # event dedup window (trading bars)

SESS_CODE = {"ASIA": 0, "LONDON": 1, "NY": 2, "LATE": 3, "HALT": 4}


# ---------------------------------------------------------------- data prep
class Data:
    pass


def load_discovery(start="2016-01-01", end="2022-01-01"):
    df = G.load_gc_1m("discovery", start=start, end=end)
    D = Data()
    D.df = df
    D.ts = df["ts"].astype("int64").to_numpy()
    for c in ("open", "high", "low", "close"):
        setattr(D, c[0], df[c].to_numpy(float))
    D.iid = df["instrument_id"].to_numpy()
    D.sess = df["session"].map(SESS_CODE).to_numpy(np.int8)

    days = pd.Index(sorted(df["trade_date"].unique()))
    D.day_index = {d: i for i, d in enumerate(days)}
    D.days = days
    D.day = df["trade_date"].map(D.day_index).to_numpy(np.int32)
    D.year = np.array([d.year for d in days])          # per day
    D.n_days = len(days)

    # segment run bounds
    rid = np.cumsum(df["seg_change"].to_numpy())
    D.seg_start = np.empty(len(df), np.int64)
    D.seg_end = np.empty(len(df), np.int64)
    starts = np.flatnonzero(np.r_[True, np.diff(rid) != 0])
    ends = np.r_[starts[1:] - 1, len(df) - 1]
    for s, e in zip(starts, ends):
        D.seg_start[s:e + 1] = s
        D.seg_end[s:e + 1] = e

    # day first/last bar
    D.day_first = np.zeros(D.n_days, np.int64)
    D.day_last = np.zeros(D.n_days, np.int64)
    db = np.flatnonzero(np.r_[True, np.diff(D.day) != 0])
    de = np.r_[db[1:] - 1, len(df) - 1]
    for s, e in zip(db, de):
        D.day_first[D.day[s]] = s
        D.day_last[D.day[s]] = e

    # ADR14 (roll-safe, known at open) + dominant segment hi/lo per day
    adr_t = G.session_adr(df)
    adr_map = dict(zip(adr_t["trade_date"], adr_t["adr"]))
    D.adr = np.array([adr_map.get(d, np.nan) for d in days])
    dom = (df.groupby(["trade_date", "instrument_id"])
             .agg(hi=("high", "max"), lo=("low", "min"), n=("ts", "size"),
                  last_close=("close", "last")).reset_index()
             .sort_values("n").groupby("trade_date").tail(1))
    D.dom_iid = np.zeros(D.n_days, np.int64)
    D.dom_hi = np.full(D.n_days, np.nan)
    D.dom_lo = np.full(D.n_days, np.nan)
    for _, r in dom.iterrows():
        i = D.day_index[r["trade_date"]]
        D.dom_iid[i] = r["instrument_id"]; D.dom_hi[i] = r["hi"]; D.dom_lo[i] = r["lo"]
    lc = df.groupby("trade_date")["close"].last()
    D.day_close = np.array([lc.get(d, np.nan) for d in days])

    # resamples for generation / break rules
    D.b15 = G.resample(df, "15min")
    D.b30 = G.resample(df, "30min")
    D.b60 = G.resample(df, "1h")
    for b in (D.b15, D.b30, D.b60):
        b["close_ns"] = b["ts_last"].astype("int64") + 60_000_000_000
    D.break_frames = {"15min": D.b15, "30min": D.b30, "1h": D.b60}
    return D


# ---------------------------------------------------------------- zone table
ZCOLS = ["fam", "zid", "L", "H", "act", "exp", "seg", "btype", "break_tf",
         "day_created", "meta"]

def ztable(rows):
    z = pd.DataFrame(rows, columns=ZCOLS)
    z["W"] = z["H"] - z["L"]
    return z


# ---------------------------------------------------------------- generators
def gen_zon001(D):
    rows, killed = [], 0
    for d in range(1, D.n_days):
        a = D.adr[d]
        if not np.isfinite(a) or not np.isfinite(D.dom_hi[d - 1]):
            continue
        half = 0.10 * a
        act = D.ts[D.day_first[d]]
        exp = D.ts[D.day_last[d]] + 60_000_000_000
        seg = D.dom_iid[d - 1]
        for ref, bt, tag in ((D.dom_hi[d - 1], +1, "PDH"), (D.dom_lo[d - 1], -1, "PDL")):
            rows.append(("ZON-001", f"Z1-{d}-{tag}", ref - half, ref + half,
                         act, exp, seg, bt, "30min", d, tag))
    return ztable(rows), killed


def gen_zon002(D):
    b = D.b15
    rows = []
    iid = b["instrument_id"].to_numpy()
    bins = b["bin"].to_numpy()
    hi, lo = b["high"].to_numpy(), b["low"].to_numpy()
    cns = b["close_ns"].to_numpy()
    dayix = np.array([D.day_index[d] for d in b["trade_date"]])
    step = np.timedelta64(15, "m")
    for i in range(2, len(b)):
        if not (iid[i] == iid[i - 1] == iid[i - 2]):
            continue
        if bins[i] - bins[i - 1] != step or bins[i - 1] - bins[i - 2] != step:
            continue
        d = dayix[i]; a = D.adr[d]
        if not np.isfinite(a):
            continue
        act = cns[i]
        expd = min(d + 5, D.n_days - 1)
        exp = D.ts[D.day_last[expd]] + 60_000_000_000
        if lo[i] > hi[i - 2]:          # bull FVG (support below)
            L, H, bt, tag = hi[i - 2], lo[i], -1, "bullFVG"
        elif hi[i] < lo[i - 2]:        # bear FVG (resistance above)
            L, H, bt, tag = hi[i], lo[i - 2], +1, "bearFVG"
        else:
            continue
        W = H - L
        if W < 0.3 or W > 1.0 * a:
            continue
        rows.append(("ZON-002", f"Z2-{i}", L, H, act, exp, iid[i], bt, "trav", d, tag))
    return ztable(rows), 0


def _profile(D, d):
    """Volume-at-price of day d's dominant segment; uniform spread across bar range."""
    i0, i1 = D.day_first[d], D.day_last[d]
    m = np.flatnonzero(D.iid[i0:i1 + 1] == D.dom_iid[d]) + i0
    lo = D.l[m]; hi = D.h[m]; vol = D.df["volume"].to_numpy()[m].astype(float)
    p0 = lo.min()
    i_lo = np.round((lo - p0) / TICK).astype(int)
    i_hi = np.round((hi - p0) / TICK).astype(int)
    hist = np.zeros(i_hi.max() + 1)
    for a_, b_, v in zip(i_lo, i_hi, vol):
        hist[a_:b_ + 1] += v / (b_ - a_ + 1)
    poc = int(np.argmax(hist))
    total = hist.sum()
    lo_i = hi_i = poc; cum = hist[poc]
    while cum < 0.70 * total:
        left = hist[lo_i - 1] if lo_i > 0 else -1.0
        right = hist[hi_i + 1] if hi_i < len(hist) - 1 else -1.0
        if right >= left:
            hi_i += 1; cum += hist[hi_i]
        else:
            lo_i -= 1; cum += hist[lo_i]
    return p0 + poc * TICK, p0 + hi_i * TICK, p0 + lo_i * TICK


def gen_zon003(D):
    rows = []
    for d in range(1, D.n_days):
        a = D.adr[d]
        if not np.isfinite(a) or not np.isfinite(D.dom_hi[d - 1]):
            continue
        poc, vah, val = _profile(D, d - 1)
        half = 0.05 * a
        act = D.ts[D.day_first[d]]
        exp = D.ts[D.day_last[d]] + 60_000_000_000
        seg = D.dom_iid[d - 1]
        for ref, tag in ((poc, "POC"), (vah, "VAH"), (val, "VAL")):
            rows.append(("ZON-003", f"Z3-{d}-{tag}", ref - half, ref + half,
                         act, exp, seg, 0, "30min", d, tag))
    return ztable(rows), 0


def gen_zon004(D):
    b = D.b30
    rows = []
    step = np.timedelta64(30, "m")
    for seg, g in b.groupby("instrument_id", sort=False):
        g = g.reset_index(drop=True)
        rng = (g["high"] - g["low"]).to_numpy()
        med20 = pd.Series(rng).rolling(20).median().shift(1).to_numpy()
        bins = g["bin"].to_numpy()
        contig = np.r_[False, np.diff(bins) == step]
        hi, lo, cl = g["high"].to_numpy(), g["low"].to_numpy(), g["close"].to_numpy()
        cns = g["close_ns"].to_numpy()
        dayix = np.array([D.day_index[d] for d in g["trade_date"]])
        i = 0
        n = len(g)
        while i < n:
            if not np.isfinite(med20[i]) or rng[i] > 0.5 * med20[i]:
                i += 1; continue
            j = i
            while j + 1 < n and contig[j + 1] and np.isfinite(med20[j + 1]) \
                    and rng[j + 1] <= 0.5 * med20[j + 1]:
                j += 1
            if j - i + 1 >= 3 and j + 1 < n and contig[j + 1] and np.isfinite(med20[j + 1]) \
                    and rng[j + 1] >= 2.0 * med20[j + 1]:
                k = j + 1
                bl, bh = lo[i:j + 1].min(), hi[i:j + 1].max()
                d = dayix[k]; a = D.adr[d]
                W = bh - bl
                if np.isfinite(a) and W <= 1.0 * a and W >= TICK:
                    expd = min(d + 10, D.n_days - 1)
                    exp = D.ts[D.day_last[expd]] + 60_000_000_000
                    if cl[k] > bh:
                        rows.append(("ZON-004", f"Z4-{seg}-{i}", bl, bh, cns[k], exp,
                                     seg, -1, "30min", d, "demand"))
                    elif cl[k] < bl:
                        rows.append(("ZON-004", f"Z4-{seg}-{i}", bl, bh, cns[k], exp,
                                     seg, +1, "30min", d, "supply"))
                i = k + 1
            else:
                i = j + 1
    return ztable(rows), 0


def gen_zon005(D):
    levels = np.arange(1000.0, 2200.0 + 1, 50.0)
    rows = []
    for d in range(1, D.n_days):
        a = D.adr[d]; ref = D.day_close[d - 1]
        if not np.isfinite(a) or not np.isfinite(ref):
            continue
        half = 0.05 * a
        act = D.ts[D.day_first[d]]
        exp = D.ts[D.day_last[d]] + 60_000_000_000
        for R in levels[np.abs(levels - ref) <= 1.5 * a]:
            tag = "major" if R % 100 == 0 else "minor"
            rows.append(("ZON-005", f"Z5-{d}-{int(R)}", R - half, R + half,
                         act, exp, -1, 0, None, d, tag))
    return ztable(rows), 0


def gen_zon006(D):
    b = D.b60
    step = np.timedelta64(60, "m")
    pivots = []          # (conf_ns, day, seg, side, price)
    for seg, g in b.groupby("instrument_id", sort=False):
        g = g.reset_index(drop=True)
        hi, lo = g["high"].to_numpy(), g["low"].to_numpy()
        bins = g["bin"].to_numpy()
        cns = g["close_ns"].to_numpy()
        dayix = np.array([D.day_index[d] for d in g["trade_date"]])
        for k in range(2, len(g) - 2):
            if (bins[k + 2] - bins[k - 2]) != 4 * step:
                continue
            if hi[k] > hi[k - 1] and hi[k] > hi[k - 2] and hi[k] > hi[k + 1] and hi[k] > hi[k + 2]:
                pivots.append((cns[k + 2], dayix[k + 2], seg, +1, hi[k]))
            if lo[k] < lo[k - 1] and lo[k] < lo[k - 2] and lo[k] < lo[k + 1] and lo[k] < lo[k + 2]:
                pivots.append((cns[k + 2], dayix[k + 2], seg, -1, lo[k]))
    pivots.sort()
    rows = []
    lineage_of = {}          # pivot idx -> lineage id
    active = {}              # lineage id -> row idx in rows
    nlin = 0
    plist = []               # kept pivots as dicts
    for conf, d, seg, side, price in pivots:
        a = D.adr[d]
        if not np.isfinite(a):
            plist.append(None); continue
        matches = [i for i, p in enumerate(plist)
                   if p and p["side"] == side and p["seg"] == seg
                   and d - p["day"] <= 15 and abs(price - p["price"]) <= 0.15 * a]
        pid = len(plist)
        plist.append({"day": d, "seg": seg, "side": side, "price": price})
        if not matches:
            lineage_of[pid] = None
            continue
        lins = {lineage_of[m] for m in matches if lineage_of.get(m) is not None}
        prices = [plist[m]["price"] for m in matches] + [price]
        lo_, hi_ = min(prices), max(prices)
        if hi_ - lo_ < 0.10 * a:
            mid = float(np.mean(prices))
            lo_, hi_ = mid - 0.05 * a, mid + 0.05 * a
        expd = min(d + 15, D.n_days - 1)
        exp = D.ts[D.day_last[expd]] + 60_000_000_000
        if lins:
            lin = min(lins)
            for l2 in lins:
                if l2 in active:
                    rows[active[l2]][5] = conf          # supersede old versions
                    del active[l2]
        else:
            lin = nlin; nlin += 1
        for m in matches:
            lineage_of[m] = lin
        lineage_of[pid] = lin
        rows.append(["ZON-006", f"Z6-{lin}-v{len(rows)}", lo_, hi_, conf, exp,
                     seg, side, "1h", d, f"lin{lin}"])
        active[lin] = len(rows) - 1
    return ztable([tuple(r) for r in rows]), 0


# ---------------------------------------------------------------- episode engine
EP_FIELDS = ["fam", "zid", "T0", "t0_ns", "day", "year", "sess", "side", "P0", "W",
             "adr", "touch_idx", "stratum", "age_min",
             "trav120", "depth120", "reclaim", "rejW", "rejA", "t_rejA",
             "ambig", "inside", "n_trunc", "t_end", "depth_end"] + \
            [f"FE{h}" for h in HORIZONS] + [f"AE{h}" for h in HORIZONS]


def _break_time(D, z, side_hint, from_ns):
    """First source-TF close beyond the distal edge (ns) or +inf.

    Typed zones (btype != 0): distal fixed by type, searched from activation.
    Relative zones (btype == 0): distal defined by the FIRST sided approach, so
    the search starts at that first touch — closes beyond the far side before
    any interaction are just price location, not acceptance-through.
    """
    bt = z.btype if z.btype != 0 else side_hint          # relative zones: distal vs 1st approach
    if z.break_tf in (None, "trav") or bt == 0:
        return np.inf
    start = z.act if z.btype != 0 else from_ns
    f = D.break_frames[z.break_tf]
    m = (f["instrument_id"].to_numpy() == z.seg) if z.seg >= 0 else np.ones(len(f), bool)
    cns = f["close_ns"].to_numpy()[m]
    cl = f["close"].to_numpy()[m]
    sel = (cns > start) & (cns < z.exp + 240 * 60_000_000_000)
    cns, cl = cns[sel], cl[sel]
    hit = np.flatnonzero(cl > z.H) if bt > 0 else np.flatnonzero(cl < z.L)
    return float(cns[hit[0]]) if len(hit) else np.inf


def run_episodes(D, zones, first_only=False):
    out = []
    roll_killed = 0
    n = len(D.ts)
    for z in zones.itertuples(index=False):
        i0 = np.searchsorted(D.ts, z.act, "left")
        i1 = np.searchsorted(D.ts, z.exp, "left") - 1
        if i0 >= n or i1 < i0:
            continue
        if z.seg >= 0:
            if D.iid[i0] != z.seg:
                roll_killed += 1
                continue
            i1 = min(i1, D.seg_end[i0])
        hh = D.h[i0:i1 + 1]; ll = D.l[i0:i1 + 1]
        contact = np.flatnonzero((hh >= z.L) & (ll <= z.H)) + i0
        if len(contact) == 0:
            continue
        touch_idx = 0
        brk = None
        pos = 0
        while pos < len(contact):
            T0 = int(contact[pos])
            lb = max(D.seg_start[T0], T0 - LOOKBACK)
            side = 0
            for j in range(T0 - 1, lb - 1, -1):
                if D.h[j] < z.L:
                    side = -1; break          # approach from below
                if D.l[j] > z.H:
                    side = +1; break          # approach from above
            if side == 0:
                # non-classifiable contact: touch_index 0, does not consume an index
                out.append((z.fam, z.zid, T0, D.ts[T0], D.day[T0], D.year[D.day[T0]],
                            D.sess[T0], 0, np.nan, z.H - z.L, D.adr[D.day[T0]],
                            0, "inside", np.nan,
                            *([np.nan] * 6), 0, 1, 0, np.nan, np.nan,
                            *([np.nan] * 10)))
                nxt = contact[contact > T0 + LOOKBACK]
                pos = len(contact) - len(nxt)
                continue          # first_only shadows keep looking for a sided episode
            touch_idx += 1
            P0 = z.L if side < 0 else z.H
            W = z.H - z.L
            # excursion paths may run past zone expiry but never past the roll boundary
            Emax = min(T0 + EP_CAP, D.seg_end[T0])
            m = Emax - T0
            hw = D.h[T0:Emax + 1]; lw = D.l[T0:Emax + 1]
            if side < 0:
                ae = np.maximum.accumulate(hw) - P0
                fe_src = P0 - np.minimum.accumulate(lw[1:]) if m >= 1 else np.array([])
                sep_ok = hw <= P0 - W
            else:
                ae = P0 - np.minimum.accumulate(lw)
                fe_src = np.maximum.accumulate(hw[1:]) - P0 if m >= 1 else np.array([])
                sep_ok = lw >= P0 + W
            np.clip(ae, 0, None, out=ae)
            fe = np.clip(fe_src, 0, None) if len(fe_src) else fe_src
            t_trav = int(np.searchsorted(ae, W)) if ae[-1] >= W else None
            def first_ge(arr, x):
                if len(arr) == 0 or arr[-1] < x:
                    return None
                return int(np.searchsorted(arr, x)) + 1          # offset from T0
            t_rejW = first_ge(fe, 1.0 * W)
            a_day = D.adr[D.day[T0]]
            t_rejA = first_ge(fe, 0.25 * a_day)
            def rejected(t_r):
                if t_r is None or t_r > 120:
                    return False, False
                if t_trav is not None and t_trav <= t_r:
                    return False, t_trav == t_r
                return True, False
            rejW, ambW = rejected(t_rejW)
            rejA, ambA = rejected(t_rejA)
            ambig = int(ambW or ambA or (t_trav == 0))
            trav120 = int(t_trav is not None and t_trav <= 120)
            depth120 = float(ae[min(120, m)] / W) if W > 0 else np.nan
            reclaim = np.nan
            if trav120:
                Tv = T0 + t_trav
                re_end = min(Tv + 120, D.seg_end[Tv])
                if re_end > Tv:
                    rh = D.h[Tv + 1:re_end + 1]; rl = D.l[Tv + 1:re_end + 1]
                    reclaim = float(np.any((rh >= z.L) & (rl <= z.H)))
            fes, aes, ntr = [], [], 0
            for hz in HORIZONS:
                if hz <= m:          # m is segment-bounded: truncation = roll cut
                    fes.append(float(fe[hz - 1]) if len(fe) >= hz else np.nan)
                    aes.append(float(ae[hz]))
                else:
                    fes.append(np.nan); aes.append(np.nan); ntr += 1
            # stratum
            if brk is None and z.break_tf == "trav":
                brk = np.inf
            if brk is None:
                brk = _break_time(D, z, side, float(D.ts[T0]))
            if z.break_tf == "trav" and trav120 and brk == np.inf:
                brk = float(D.ts[T0 + t_trav])
            stratum = "retest" if D.ts[T0] > brk else "pre"
            age_min = (D.ts[T0] - z.act) / 60e9
            # episode end (computed BEFORE the row so end-state fields are stored)
            ends = [t for t in (t_rejW, t_trav) if t is not None]
            run = 0; t_sep = None
            for t in range(1, m + 1):
                run = run + 1 if sep_ok[t] else 0
                if run >= SEP_RUN:
                    t_sep = t; break
            if t_sep is not None:
                ends.append(t_sep)
            t_end = min(ends) if ends else m
            depth_end = float(ae[min(t_end, m)] / W) if W > 0 else np.nan
            out.append((z.fam, z.zid, T0, D.ts[T0], D.day[T0], D.year[D.day[T0]],
                        D.sess[T0], side, P0, W, a_day, touch_idx, stratum, age_min,
                        trav120, depth120, reclaim, int(rejW), int(rejA),
                        (t_rejA if rejA else np.nan), ambig, 0, ntr,
                        t_end, depth_end, *fes, *aes))
            e_abs = T0 + t_end
            nxt = contact[contact > e_abs]
            pos = len(contact) - len(nxt)
            if first_only:
                break
    ep = pd.DataFrame(out, columns=EP_FIELDS)
    return ep, roll_killed


# ---------------------------------------------------------------- controls
def gen_shadows(zones):
    rows = []
    zv = zones
    L = zv["L"].to_numpy(); H = zv["H"].to_numpy()
    act = zv["act"].to_numpy(); exp = zv["exp"].to_numpy()
    for k, z in enumerate(zones.itertuples(index=False)):
        W = z.H - z.L; mid = 0.5 * (z.L + z.H)
        for off in (-4, -2, 2, 4):
            m2 = mid + off * W
            sl, sh = m2 - W / 2, m2 + W / 2
            ov = (L < sh) & (H > sl) & (act < z.exp) & (exp > z.act)
            ov[k] = False
            if ov.any():
                continue          # unavailable
            rows.append((z.fam, f"{z.zid}-S{off:+d}", sl, sh, z.act, z.exp,
                         z.seg, z.btype, None, z.day_created, f"shadow{off:+d}"))
    return ztable(rows)


def build_c2_pool(D):
    n = len(D.ts)
    ret5 = np.full(n, np.nan)
    ok = np.arange(5, n)
    same = D.seg_start[ok] <= ok - 5
    idx = ok[same]
    ret5[idx] = np.log(D.c[idx] / D.c[idx - 5])
    adr_day = D.adr[D.day]
    speed = np.abs(ret5) / adr_day
    valid = np.isfinite(ret5) & np.isfinite(adr_day) & (D.sess < 4)
    q = np.nanquantile(speed[valid], [0.25, 0.5, 0.75])
    ter = np.nanquantile(D.adr[np.isfinite(D.adr)], [1 / 3, 2 / 3])
    sq = np.digitize(speed, q)
    tc = np.digitize(adr_day, ter)
    dirn = (ret5 > 0).astype(int)
    cell = (((D.sess.astype(int) * 3 + tc) * 2 + dirn) * 4 + sq)
    cell[~valid] = -1
    pool = {}
    for cid in np.unique(cell):
        if cid >= 0:
            pool[int(cid)] = np.flatnonzero(cell == cid)
    return pool, cell, ter, q


def zones_by_day(zones, D):
    byday = {}
    for i, z in enumerate(zones.itertuples(index=False)):
        d0 = int(np.searchsorted(D.ts[D.day_first], z.act, "right") - 1)
        d1 = int(np.searchsorted(D.ts[D.day_first], z.exp, "right") - 1)
        for d in range(max(d0, 0), min(d1, D.n_days - 1) + 1):
            byday.setdefault(d, []).append(i)
    return byday


def run_c2(D, events, zones, pool, cell, rng, K=5):
    zL = zones["L"].to_numpy(); zH = zones["H"].to_numpy()
    zact = zones["act"].to_numpy(); zexp = zones["exp"].to_numpy()
    byday = zones_by_day(zones, D)
    rows = []
    shortfall = 0
    for e in events.itertuples(index=False):
        c0 = cell[e.T0]
        if c0 < 0 or c0 not in pool:
            shortfall += 1
            continue
        cand = pool[c0]
        got = 0; tries = 0
        while got < K and tries < 15 * K:
            i = int(cand[rng.integers(len(cand))]); tries += 1
            if D.day[i] == e.day:
                continue
            P0 = D.c[i]
            side = -1 if cell_dir(cell, i) else +1          # rising -> from below
            sl, sh = (P0, P0 + e.W) if side < 0 else (P0 - e.W, P0)
            zl = byday.get(D.day[i], [])
            bad = False
            for zi in zl:
                if zact[zi] <= D.ts[i] < zexp[zi] and zL[zi] < sh and zH[zi] > sl:
                    bad = True; break
            if bad:
                continue
            Hmax = min(i + 120, D.seg_end[i])
            m = Hmax - i
            if m < 5:
                continue
            hw = D.h[i:Hmax + 1]; lw = D.l[i:Hmax + 1]
            if side < 0:
                ae = np.clip(np.maximum.accumulate(hw) - P0, 0, None)
                fe = np.clip(P0 - np.minimum.accumulate(lw[1:]), 0, None)
            else:
                ae = np.clip(P0 - np.minimum.accumulate(lw), 0, None)
                fe = np.clip(np.maximum.accumulate(hw[1:]) - P0, 0, None)
            t_trav = int(np.searchsorted(ae, e.W)) if ae[-1] >= e.W else None
            def fge(arr, x):
                return (int(np.searchsorted(arr, x)) + 1) if (len(arr) and arr[-1] >= x) else None
            t_rw = fge(fe, e.W); t_ra = fge(fe, 0.25 * D.adr[D.day[i]])
            def rj(t_r):
                return int(t_r is not None and t_r <= 120 and (t_trav is None or t_trav > t_r))
            fes, aes = [], []
            for hz in HORIZONS:
                if hz <= m:
                    fes.append(float(fe[hz - 1]) if len(fe) >= hz else np.nan)
                    aes.append(float(ae[hz]))
                else:
                    fes.append(np.nan); aes.append(np.nan)
            rows.append((e.fam, e.zid, i, D.day[i], D.year[D.day[i]], e.W,
                         D.adr[D.day[i]], rj(t_rw), rj(t_ra),
                         int(t_trav is not None and t_trav <= 120), *fes, *aes))
            got += 1
        if got < K:
            shortfall += 1
    cols = ["fam", "event_zid", "T0", "day", "year", "W", "adr", "rejW", "rejA",
            "trav120"] + [f"FE{h}" for h in HORIZONS] + [f"AE{h}" for h in HORIZONS]
    return pd.DataFrame(rows, columns=cols), shortfall


def cell_dir(cell, i):
    return (cell[i] // 4) % 2 == 1          # dirn bit


# ---------------------------------------------------------------- dedup / clusters
def dedup(events, zones):
    """Within-family event dedup: T0 within DEDUP_BARS and interval overlap -> one event."""
    zmap = zones.set_index("zid")
    ev = events.sort_values("T0").reset_index(drop=True)
    L = zmap.loc[ev["zid"], "L"].to_numpy()
    H = zmap.loc[ev["zid"], "H"].to_numpy()
    act = zmap.loc[ev["zid"], "act"].to_numpy()
    T0 = ev["T0"].to_numpy()
    keep = np.ones(len(ev), bool)
    parent = np.arange(len(ev))
    for i in range(len(ev)):
        if not keep[i]:
            continue
        j = i + 1
        while j < len(ev) and T0[j] - T0[i] <= DEDUP_BARS:
            if keep[j] and L[j] < H[i] and H[j] > L[i]:
                if act[j] < act[i]:
                    keep[i] = False; parent[i] = j
                    break
                keep[j] = False; parent[j] = i
            j += 1
    ev["kept"] = keep
    return ev[keep].reset_index(drop=True), ev


def cross_clusters(all_events, zones_all):
    zmap = zones_all.set_index("zid")
    ev = all_events.sort_values("T0").reset_index(drop=True)
    L = zmap.loc[ev["zid"], "L"].to_numpy()
    H = zmap.loc[ev["zid"], "H"].to_numpy()
    T0 = ev["T0"].to_numpy()
    par = np.arange(len(ev))
    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]; x = par[x]
        return x
    for i in range(len(ev)):
        j = i + 1
        while j < len(ev) and T0[j] - T0[i] <= DEDUP_BARS:
            if L[j] < H[i] and H[j] > L[i]:
                par[find(j)] = find(i)
            j += 1
    ev["interaction_cluster_id"] = [find(i) for i in range(len(ev))]
    return ev


# ---------------------------------------------------------------- stats
def day_boot(rng, vals_by_day_real, vals_by_day_ctl=None, paired=None, reps=1000):
    """Difference-of-means CI. Unpaired: independent day resampling of each side.
    Paired: paired deltas resampled by day."""
    if paired is not None:
        days = list(paired.keys())
        s = np.array([paired[d].sum() for d in days])
        c = np.array([len(paired[d]) for d in days])
        est = s.sum() / c.sum()
        idx = rng.integers(0, len(days), (reps, len(days)))
        stats = (s[idx].sum(1)) / np.maximum(c[idx].sum(1), 1)
        return est, np.quantile(stats, [0.025, 0.975])
    dr = list(vals_by_day_real.keys()); dc = list(vals_by_day_ctl.keys())
    if not dr or not dc:
        return float("nan"), np.array([np.nan, np.nan])
    sr = np.array([vals_by_day_real[d].sum() for d in dr])
    nr = np.array([len(vals_by_day_real[d]) for d in dr])
    sc = np.array([vals_by_day_ctl[d].sum() for d in dc])
    nc = np.array([len(vals_by_day_ctl[d]) for d in dc])
    est = sr.sum() / nr.sum() - sc.sum() / nc.sum()
    ir = rng.integers(0, len(dr), (reps, len(dr)))
    ic = rng.integers(0, len(dc), (reps, len(dc)))
    stats = sr[ir].sum(1) / np.maximum(nr[ir].sum(1), 1) - \
        sc[ic].sum(1) / np.maximum(nc[ic].sum(1), 1)
    return est, np.quantile(stats, [0.025, 0.975])


def by_day(df, col):
    v = df[[col, "day"]].dropna()
    return {d: g[col].to_numpy() for d, g in v.groupby("day")}


def netfav(df, h=60):
    return (df[f"FE{h}"] - df[f"AE{h}"]) / df["adr"]
