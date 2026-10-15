"""Batch-9 trade-product engine (BATCH9_PLAN.md frozen)."""
from __future__ import annotations

import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch2"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch7"))
import batch1_lib as B
import batch2_lib as Z
import motifs_lib as M7
import run_batch1 as R1

TICK = 0.1
COMM = 0.05
SLIP = 0.1
HOLD = 120
GATE = 0.10
CONFS = ["C0", "C1", "C2", "C3", "C4"]

FAMS = {"F1_fvg": lambda D: B.gen_zon002(D)[0],
        "F2_vaedge": Z.gen_zon012,
        "F3_compress": Z.gen_zon013,
        "F4_tail": Z.gen_zon008,
        "F5_nr7": M7.m09,
        "F6_climax": M7.m07}


def family_events(D, fam):
    zones = FAMS[fam](D).assign(fam=fam)
    ep, _ = B.run_episodes(D, zones)
    ev, _ = B.dedup(R1.primary_filter(ep), zones)
    ev = ev.reset_index(drop=True)
    zm = zones.set_index("zid")
    ev["L"] = zm.loc[ev["zid"], "L"].to_numpy()
    ev["H"] = zm.loc[ev["zid"], "H"].to_numpy()
    return zones, ev


def median_body20(D):
    body = np.abs(D.c - D.o)
    return pd.Series(body).rolling(20).median().shift(1).to_numpy()


def confirm_entry(D, e, conf, mb20):
    """Return (entry_bar, delay_bars) or (None, reason). dir = e.side (fade touch)."""
    T0 = int(e.T0)
    d = 1 if e.side > 0 else -1
    prox = e.H if d > 0 else e.L          # long: entered from above through H
    dist = e.L if d > 0 else e.H
    if conf == "C0":
        j = T0
    else:
        if conf == "C2":
            win = [T0]
        elif conf == "C1":
            win = range(T0, T0 + 5)
        else:
            win = range(T0 + 1, T0 + 6)
        j = None
        for k in win:
            if k > D.seg_end[T0]:
                break
            # eligibility cancel: 1m close beyond distal before trigger
            if (d > 0 and D.c[k] < dist) or (d < 0 and D.c[k] > dist):
                return None, "cancel_invalid"
            if conf in ("C1", "C2"):
                hit = (D.c[k] > prox) if d > 0 else (D.c[k] < prox)
            elif conf == "C3":
                hit = (D.c[k] > D.h[T0]) if d > 0 else (D.c[k] < D.l[T0])
            else:          # C4
                body = abs(D.c[k] - D.o[k])
                m = mb20[k]
                hit = (np.isfinite(m) and body >= 1.5 * m
                       and ((d > 0 and D.c[k] > D.o[k] and D.c[k] > prox)
                            or (d < 0 and D.c[k] < D.o[k] and D.c[k] < prox)))
            if hit:
                j = k
                break
        if j is None:
            return None, "missed"
    if j + 1 > D.seg_end[T0]:
        return None, "segment_end"
    return j + 1, j - T0


def simulate(D, e, entry_bar, conf):
    d = 1 if e.side > 0 else -1
    dist = e.L if d > 0 else e.H
    prox = e.H if d > 0 else e.L
    entry = D.o[entry_bar] + d * TICK
    sl = dist - d * TICK
    R = d * (entry - sl)
    a = D.adr[D.day[entry_bar]]
    if R <= 0 or not np.isfinite(a):
        return None
    row = {"fam": e.fam, "conf": conf, "zid": e.zid, "day": int(D.day[entry_bar]),
           "year": int(D.year[D.day[entry_bar]]), "sess": int(D.sess[entry_bar]),
           "dir": d, "R": float(R), "R_adr": float(R / a),
           "delay": int(entry_bar - e.T0 - 1),
           "gone": float(d * (entry - prox)),
           "gone_adr": float(d * (entry - prox) / a),
           "gate": bool(R <= GATE * a)}
    tp = entry + d * R
    end = min(entry_bar + HOLD - 1, D.seg_end[entry_bar])
    hh = D.h[entry_bar:end + 1]
    ll = D.l[entry_bar:end + 1]
    if d > 0:
        fh = np.maximum.accumulate(hh)
        fl = np.minimum.accumulate(ll)
        t_tp = int(np.searchsorted(fh, tp)) if fh[-1] >= tp else None
        t_sl = int(np.searchsorted(-fl, -sl)) if fl[-1] <= sl else None
    else:
        fl = np.minimum.accumulate(ll)
        fh = np.maximum.accumulate(hh)
        t_tp = int(np.searchsorted(-fl, -tp)) if fl[-1] <= tp else None
        t_sl = int(np.searchsorted(fh, sl)) if fh[-1] >= sl else None
    ambig = t_tp is not None and t_sl is not None and t_tp == t_sl
    if t_sl is not None and (t_tp is None or t_sl <= t_tp):
        row.update(label="LOSS", pnl=-(R + SLIP) - COMM, ambig=bool(ambig), t_res=t_sl)
    elif t_tp is not None:
        row.update(label="WIN", pnl=R - COMM, ambig=False, t_res=t_tp)
    else:
        px = D.c[end] - d * TICK
        row.update(label="TIMEOUT", pnl=float(d * (px - entry)) - COMM,
                   ambig=False, t_res=end - entry_bar)
    # descriptive secondary targets
    for mult, tag in ((1.5, "w15"), (2.0, "w20")):
        tpx = entry + d * mult * R
        if d > 0:
            tt = int(np.searchsorted(fh, tpx)) if fh[-1] >= tpx else None
        else:
            tt = int(np.searchsorted(-fl, -tpx)) if fl[-1] <= tpx else None
        row[tag] = bool(tt is not None and (t_sl is None or tt < t_sl))
    row["pnl_R"] = row["pnl"] / R
    return row


def run_variants(D, fams=None, confs=None):
    mb20 = median_body20(D)
    out = []
    misses = []
    for fam in (fams or FAMS):
        zones, ev = family_events(D, fam)
        for conf in (confs or CONFS):
            for e in ev.itertuples(index=False):
                r = confirm_entry(D, e, conf, mb20)
                if r[0] is None:
                    misses.append({"fam": fam, "conf": conf, "reason": r[1]})
                    continue
                entry_bar, delay = r
                row = simulate(D, e, entry_bar, conf)
                if row is not None:
                    out.append(row)
    return pd.DataFrame(out), pd.DataFrame(misses)


def variant_stats(tr, nd):
    """tr: trades of one fam x conf AFTER gate filter."""
    if len(tr) < 30:
        return None
    wr = float((tr["label"] == "WIN").mean())
    wins = tr.loc[tr["pnl"] > 0, "pnl"].sum()
    losses = -tr.loc[tr["pnl"] < 0, "pnl"].sum()
    per = tr.groupby("day").size()
    lab = (tr.sort_values(["day"]).reset_index()["label"] == "WIN").to_numpy()
    streak = mx = 0
    for w in lab:
        streak = 0 if w else streak + 1
        mx = max(mx, streak)
    return {"n": int(len(tr)), "tpd": round(len(tr) / nd, 2),
            "wr": round(wr, 4),
            "loss_pct": round(float((tr["label"] == "LOSS").mean()), 4),
            "to_pct": round(float((tr["label"] == "TIMEOUT").mean()), 4),
            "ambig": round(float(tr["ambig"].mean()), 4),
            "exp_R": round(float(tr["pnl_R"].mean()), 4),
            "exp_pts": round(float(tr["pnl"].mean()), 4),
            "pf": round(float(wins / losses), 3) if losses > 0 else np.inf,
            "stop_med": round(float(tr["R"].median()), 3),
            "stop_adr_med": round(float(tr["R_adr"].median()), 4),
            "delay_med": round(float(tr["delay"].median()), 1),
            "gone_adr_med": round(float(tr["gone_adr"].median()), 4),
            "max_lstreak": int(mx),
            "wr15": round(float(tr["w15"].mean()), 3),
            "wr20": round(float(tr["w20"].mean()), 3),
            "yearly_expR": {int(y): round(float(g["pnl_R"].mean()), 3)
                            for y, g in tr.groupby("year")},
            "yearly_wr": {int(y): round(float((g["label"] == "WIN").mean()), 3)
                          for y, g in tr.groupby("year")}}
