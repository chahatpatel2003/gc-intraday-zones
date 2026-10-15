"""Point-in-time scheduled-news tagging — INFRASTRUCTURE ONLY (no data bundled).

Protocol rules (RESEARCH_PROTOCOL v1.1): news effects are analyzed later, never
optimized yet; only information available at its true release timestamp may be
used; actual/revised figures must never leak before `released_utc`.

No calendar data ships with this module. Acquiring a historical scheduled-release
calendar is decision D-NEWS (user approval; no downloads without it). A calendar
CSV must provide, per release:

    event_id,event_type,scheduled_utc,released_utc,source
    # scheduled_utc  = the time the release was scheduled for, as known IN ADVANCE
    # released_utc   = when values actually became public (>= scheduled_utc)
    # values/revisions, if ever added, need their own point-in-time columns

Deliberately NOT implemented: deriving schedules from rules of thumb ("NFP is the
first Friday, 08:30 ET") — exceptions exist and silently wrong point-in-time
schedules are worse than none.
"""
from __future__ import annotations

import pandas as pd

REQUIRED = ["event_id", "event_type", "scheduled_utc", "released_utc", "source"]

# Preregistered condition buckets (ZONE_SPEC/EVALUATION_FRAMEWORK): relative to
# scheduled_utc T: pre_news [T-60m, T), release [T, T+5m), post_news [T+5m, T+60m),
# else normal. Buckets are fixed; do not tune them per result.
WINDOWS_MIN = {"pre_news": (-60, 0), "release": (0, 5), "post_news": (5, 60)}


def load_calendar(csv_path: str) -> pd.DataFrame:
    cal = pd.read_csv(csv_path)
    missing = [c for c in REQUIRED if c not in cal.columns]
    if missing:
        raise ValueError(f"calendar missing point-in-time columns: {missing}")
    for c in ("scheduled_utc", "released_utc"):
        cal[c] = pd.to_datetime(cal[c], utc=True)
    if (cal["released_utc"] < cal["scheduled_utc"]).any():
        raise ValueError("released_utc before scheduled_utc — not point-in-time safe")
    return cal.sort_values("scheduled_utc").reset_index(drop=True)


def tag_timestamps(ts: pd.Series, cal: pd.DataFrame,
                   event_types: list[str] | None = None) -> pd.Series:
    """Categorical news bucket per timestamp (normal/pre_news/release/post_news).

    Uses scheduled_utc only — i.e. exactly what was knowable in advance.
    Overlapping windows resolve to the most acute bucket (release > pre > post).
    """
    if event_types is not None:
        cal = cal[cal["event_type"].isin(event_types)]
    out = pd.Series("normal", index=ts.index, dtype="object")
    order = ["post_news", "pre_news", "release"]          # increasing precedence
    for name in order:
        lo_m, hi_m = WINDOWS_MIN[name]
        for t in cal["scheduled_utc"]:
            m = (ts >= t + pd.Timedelta(minutes=lo_m)) & \
                (ts < t + pd.Timedelta(minutes=hi_m))
            out[m] = name
    return out
