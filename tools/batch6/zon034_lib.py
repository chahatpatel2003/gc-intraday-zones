"""ZON-034: ZON-026 QML universe + the ONE frozen clustering rule (ZON-034_SPEC.md)."""
from __future__ import annotations

import os, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "batch5"))
import batch1_lib as B
import batch5_lib as F


def _iou(l1, h1, l2, h2):
    inter = max(0.0, min(h1, h2) - max(l1, l2))
    union = max(h1, h2) - min(l1, l2)
    return inter / union if union > 0 else 0.0


def gen_zon034(D):
    """Deterministic clustering of the unchanged ZON-026 universe.

    Returns (representatives_frame, diagnostics). Representative geometry and
    lifecycle are byte-identical ZON-026 zones; suppressed members are logged.
    """
    z26 = F.gen_zon026(D)
    z = z26.sort_values(["act", "zid"], kind="stable").reset_index(drop=True)
    reps = []          # indexes into z of active representatives
    keep = np.zeros(len(z), bool)
    cluster_of = np.full(len(z), -1)
    members = {}
    for i, r in enumerate(z.itertuples(index=False)):
        reps = [j for j in reps if z.at[j, "exp"] > r.act]
        hit = None
        for j in reps:
            if z.at[j, "seg"] != r.seg or z.at[j, "btype"] != r.btype:
                continue
            L2, H2 = z.at[j, "L"], z.at[j, "H"]
            w1, w2 = r.H - r.L, H2 - L2
            if _iou(r.L, r.H, L2, H2) >= 0.5 or \
                    abs((r.L + r.H) / 2 - (L2 + H2) / 2) <= 0.5 * max(w1, w2):
                hit = j
                break
        if hit is None:
            keep[i] = True
            cluster_of[i] = i
            members[i] = [r.zid]
            reps.append(i)
        else:
            cluster_of[i] = hit
            members[hit].append(r.zid)
    out = z[keep].reset_index(drop=True)
    out["fam"] = "ZON-034"
    out["zid"] = out["zid"].str.replace("Z26-", "Z34-", regex=False)
    out["n_members"] = [len(members[i]) for i in np.flatnonzero(keep)]
    diag = {"raw_zones": int(len(z)), "representatives": int(len(out)),
            "suppressed": int(len(z) - len(out)),
            "members_mean": round(float(out["n_members"].mean()), 2),
            "members_max": int(out["n_members"].max())}
    return out, diag, z26
