"""Batch-4 attribution machinery (BATCH4_SPECS.md frozen 2026-08-16)."""
from __future__ import annotations

import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch3"))
import batch1_lib as B
import batch2_lib as Z
import batch3_lib as Q

DEP_CAP = 60
DEP_THRESH = 0.15
ISO_ADR = 0.5


def dep_strength(events, zones, D):
    """Leak-free pre-touch departure strength, /ADR14 of the zone's creation day.

    Window = [activation bar .. min(activation+60, T0-1)], same segment.
    NEVER includes the touch bar. Empty window -> NaN (not strong).
    """
    zm = zones.set_index("zid")
    out = np.full(len(events), np.nan)
    for k, e in enumerate(events.itertuples(index=False)):
        z = zm.loc[e.zid]
        if isinstance(z, pd.DataFrame):
            z = z.iloc[0]
        a = D.adr[int(z["day_created"])]
        if not np.isfinite(a):
            continue
        mid = 0.5 * (z["L"] + z["H"])
        ia = int(np.searchsorted(D.ts, z["act"], "left"))
        if ia >= len(D.ts):
            continue
        iw = min(ia + DEP_CAP, int(e.T0) - 1, D.seg_end[ia])
        if iw < ia:
            continue
        out[k] = float(np.max(np.abs(D.c[ia:iw + 1] - mid)) / a)
    return out


def strong_mask(dep):
    return np.isfinite(dep) & (dep >= DEP_THRESH)


class IsoIndex:
    """Fast isolation test for arbitrary midpoints vs a family's active zones."""
    def __init__(self, zones, D):
        self.mid = ((zones["L"] + zones["H"]) / 2).to_numpy()
        self.act = zones["act"].to_numpy()
        self.exp = zones["exp"].to_numpy()
        self.zid = zones["zid"].to_numpy()
        self.byday = B.zones_by_day(zones, D)
        self.D = D

    def isolated(self, day, ts_ns, mid, exclude_zid=None):
        a = self.D.adr[int(day)]
        for ci in self.byday.get(int(day), []):
            if exclude_zid is not None and self.zid[ci] == exclude_zid:
                continue
            if self.act[ci] <= ts_ns < self.exp[ci] and abs(self.mid[ci] - mid) < ISO_ADR * a:
                return False
        return True


def run_c2v2(D, events, zones, pool, cell, rng, iso_flags, K=5):
    """C2 with isolation-state matching (BATCH4_SPECS.md)."""
    idx = IsoIndex(zones, D)
    zL = zones["L"].to_numpy(); zH = zones["H"].to_numpy()
    zact = zones["act"].to_numpy(); zexp = zones["exp"].to_numpy()
    byday = idx.byday
    rows, shortfall = [], 0
    H = B.HORIZONS
    for e, want_iso in zip(events.itertuples(index=False), iso_flags):
        c0 = cell[e.T0]
        if c0 < 0 or c0 not in pool:
            shortfall += 1
            continue
        cand = pool[c0]
        got = 0; tries = 0
        while got < K and tries < 25 * K:
            i = int(cand[rng.integers(len(cand))]); tries += 1
            if D.day[i] == e.day:
                continue
            P0 = D.c[i]
            side = -1 if B.cell_dir(cell, i) else +1
            sl, sh = (P0, P0 + e.W) if side < 0 else (P0 - e.W, P0)
            pmid = 0.5 * (sl + sh)
            bad = False
            for zi in byday.get(int(D.day[i]), []):
                if zact[zi] <= D.ts[i] < zexp[zi] and zL[zi] < sh and zH[zi] > sl:
                    bad = True; break
            if bad:
                continue
            if idx.isolated(D.day[i], D.ts[i], pmid) != bool(want_iso):
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
            for hz in H:
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
            "trav120"] + [f"FE{h}" for h in H] + [f"AE{h}" for h in H]
    return pd.DataFrame(rows, columns=cols), shortfall


def iso_vs_noniso(events, iso, rng):
    """Day-block bootstrap of mean NetFav60/ADR difference (iso - noniso)."""
    ev = events.assign(nf=B.netfav(events)).dropna(subset=["nf"])
    m = pd.Series(iso[:len(events)], index=events.index).reindex(ev.index)
    a, b = ev[m.astype(bool)], ev[~m.astype(bool)]
    if len(a) < 30 or len(b) < 30:
        return None
    d, ci = B.day_boot(rng, B.by_day(a, "nf"), B.by_day(b, "nf"))
    return {"n_iso": int(len(a)), "n_non": int(len(b)),
            "delta": round(float(d), 4), "ci": [round(float(x), 4) for x in ci],
            "iso_mean": round(float(a["nf"].mean()), 4),
            "non_mean": round(float(b["nf"].mean()), 4)}
