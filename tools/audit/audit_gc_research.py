#!/usr/bin/env python3
"""GC research-data integrity audit — NON-HOLDOUT files only (gc_2016..gc_2023).

Never opens anything in /Volumes/T9/Gc:Xauusd/gc/Holdout/.
Writes detailed JSON to aurum/audit/gc_audit.json; prints a compact summary.
"""
import json, os, sys
import numpy as np
import pandas as pd

GC_DIR = "/Volumes/T9/Gc:Xauusd/gc"
YEARS = list(range(2016, 2024))          # research years ONLY
OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "audit", "gc_audit.json"))

ET = "America/New_York"
TICK = 0.1

def audit():
    res = {"files": {}, "global": {}}
    frames = []
    for y in YEARS:
        p = f"{GC_DIR}/gc_{y}.parquet"
        df = pd.read_parquet(p)
        idx_name = df.index.name or "index"
        df = df.reset_index()          # ts_event lives in the index
        res["files"][y] = {"path": p, "rows": int(len(df)), "index_name": idx_name,
                           "index_dtype": str(df[idx_name].dtype) if idx_name in df else "?",
                           "columns": {c: str(t) for c, t in df.dtypes.items()}}
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)

    # --- timestamp handling ---
    ts_col = "ts_event" if "ts_event" in df.columns else df.columns[0]
    ts = pd.to_datetime(df[ts_col], utc=True)
    df = df.assign(_ts=ts).sort_values("_ts", kind="stable").reset_index(drop=True)
    g = res["global"]
    g["ts_col"] = ts_col
    g["first_ts"] = str(df["_ts"].iloc[0]); g["last_ts"] = str(df["_ts"].iloc[-1])
    g["rows_total"] = int(len(df))
    g["was_sorted_on_disk"] = bool(ts.is_monotonic_increasing)
    ns = ts.astype("int64")
    g["minute_aligned_all"] = bool(((ns % 60_000_000_000) == 0).all())
    g["dup_timestamps"] = int(df["_ts"].duplicated().sum())
    if g["dup_timestamps"]:
        d = df[df["_ts"].duplicated(keep=False)]
        g["dup_examples"] = [str(x) for x in d["_ts"].head(10)]

    # --- id / symbol columns ---
    for c in ("symbol", "rtype", "publisher_id"):
        if c in df.columns:
            g[f"unique_{c}"] = [str(v) for v in df[c].unique()[:10]]
    if "instrument_id" in df.columns:
        iid = df["instrument_id"].to_numpy()
        chg = np.flatnonzero(iid[1:] != iid[:-1]) + 1
        g["instrument_id_unique"] = int(df["instrument_id"].nunique())
        rolls = []
        for i in chg:
            prev_c = float(df["close"].iloc[i-1]); new_o = float(df["open"].iloc[i])
            rolls.append({"ts": str(df["_ts"].iloc[i]),
                          "from": int(iid[i-1]), "to": int(iid[i]),
                          "gap_pts": round(new_o - prev_c, 2)})
        g["roll_events"] = len(rolls)
        gaps = np.array([abs(r["gap_pts"]) for r in rolls]) if rolls else np.array([0.0])
        g["roll_gap_abs_median"] = float(np.median(gaps))
        g["roll_gap_abs_max"] = float(gaps.max())
        g["roll_events_detail"] = rolls
        # non-roll adjacent |close->open| for comparison
        co = np.abs(df["open"].to_numpy()[1:] - df["close"].to_numpy()[:-1])
        mask = np.ones(len(co), bool); mask[chg - 1] = False
        # restrict to gaps < 30 min (exclude session breaks)
        dt = np.diff(ns) / 1e9
        mask &= dt <= 1800
        g["nonroll_close_open_abs_p999"] = float(np.quantile(co[mask], 0.999))

    # --- price sanity ---
    for c in ("open", "high", "low", "close"):
        g[f"bad_{c}_nonpos"] = int((df[c] <= 0).sum())
        g[f"nan_{c}"] = int(df[c].isna().sum())
    g["ohlc_violations"] = int(((df["high"] < df[["open", "close"]].max(axis=1)) |
                                (df["low"] > df[["open", "close"]].min(axis=1)) |
                                (df["high"] < df["low"])).sum())
    scaled = df[["open", "high", "low", "close"]].to_numpy() / TICK
    g["off_tick_values"] = int((np.abs(scaled - np.round(scaled)) > 1e-6).sum())
    g["price_min"] = float(df["low"].min()); g["price_max"] = float(df["high"].max())

    # spikes: 1-minute log return
    lr = np.log(df["close"].to_numpy()[1:] / df["close"].to_numpy()[:-1])
    dt = np.diff(ns) / 1e9
    intra = dt <= 120
    g["ret1m_abs_p9999_bps"] = float(np.quantile(np.abs(lr[intra]), 0.9999) * 1e4)
    big = np.flatnonzero((np.abs(lr) > 0.005) & intra) + 1
    g["ret1m_gt_50bps"] = int(len(big))
    g["ret1m_worst"] = [{"ts": str(df["_ts"].iloc[i]),
                         "ret_bps": round(float(lr[i-1]) * 1e4, 1)}
                        for i in big[np.argsort(-np.abs(lr[big - 1]))][:8]]
    rng = (df["high"] - df["low"]).to_numpy()
    g["range_p9999_pts"] = float(np.quantile(rng, 0.9999))
    g["range_max_pts"] = float(rng.max())

    # --- volume ---
    g["vol_dtype"] = str(df["volume"].dtype)
    g["vol_negative"] = int((df["volume"] < 0).sum())
    g["vol_zero"] = int((df["volume"] == 0).sum())
    g["vol_p50"] = float(df["volume"].median()); g["vol_max"] = float(df["volume"].max())

    # --- gaps / calendar (ET session clock; bar ts = bar OPEN) ---
    et = df["_ts"].dt.tz_convert(ET)
    et_naive = et.dt.tz_localize(None)
    gaps_ix = np.flatnonzero(dt > 60)
    halt = {"eod_break": 0, "weekend": 0}
    intraday = []          # gaps fully inside a session
    for i in gaps_ix:
        t0, t1 = et_naive.iloc[i], et_naive.iloc[i + 1]
        mins = int(dt[i] / 60 - 1)          # fully missing minutes
        # does [t0, t1] span a 17:00 ET boundary (maintenance/EOD halt)?
        d0 = t0.normalize()
        halts = pd.date_range(d0, t1.normalize(), freq="D") + pd.Timedelta(hours=17)
        spans_halt = any((t0 < h <= t1) for h in halts)
        if spans_halt and t1.weekday() in (5, 6) or spans_halt and t0.weekday() == 4 and t1.weekday() == 6:
            halt["weekend"] += 1
        elif spans_halt:
            halt["eod_break"] += 1
        else:
            intraday.append({"from": str(df['_ts'].iloc[i]),
                             "to": str(df['_ts'].iloc[i + 1]), "missing_min": mins})
    g["gaps_eod_or_holiday"] = halt["eod_break"]
    g["gaps_weekend"] = halt["weekend"]
    g["gaps_intraday_count"] = len(intraday)
    g["gaps_intraday_total_min"] = int(sum(x["missing_min"] for x in intraday))
    g["gaps_intraday_gt15min"] = [x for x in intraday if x["missing_min"] > 15]
    oth = sorted(intraday, key=lambda x: -x["missing_min"])
    g["gaps_intraday_top"] = oth[:25]

    # trade-date convention: bar_open ET + 6h -> date (Sun 18:00 -> Monday)
    tdate = (et_naive + pd.Timedelta(hours=6)).dt.date
    per = pd.Series(1, index=tdate).groupby(level=0).sum()
    g["sessions_total"] = int(len(per))
    g["bars_per_session_median"] = float(per.median())
    g["bars_per_session_min"] = int(per.min())
    g["sessions_lt_1000_bars"] = int((per < 1000).sum())
    g["short_sessions"] = {str(k): int(v) for k, v in per[per < 1000].items()}
    wknd_sessions = [str(d) for d in per.index if pd.Timestamp(d).weekday() >= 5]
    g["weekend_trade_dates"] = wknd_sessions          # should be empty
    all_days = pd.date_range(per.index.min(), per.index.max(), freq="D")
    wk = [d.date() for d in all_days if d.weekday() < 5]
    missing = [str(d) for d in wk if d not in set(per.index)]
    g["missing_trade_days_count"] = len(missing)
    g["missing_trade_days"] = missing

    # per-year summary rows (calendar years present in data, not filenames)
    g["rows_by_calendar_year"] = {int(k): int(v)
                                  for k, v in df["_ts"].dt.year.value_counts().sort_index().items()}
    for y in YEARS:
        sub = df[df["_ts"].dt.year == y]
        if len(sub):
            res["files"][y].update({
                "first_ts": str(sub["_ts"].iloc[0]), "last_ts": str(sub["_ts"].iloc[-1]),
                "price_min": float(sub["low"].min()), "price_max": float(sub["high"].max()),
            })
    # per-FILE actual coverage (independent of calendar year)
    for y in YEARS:
        p = f"{GC_DIR}/gc_{y}.parquet"
        t = pd.to_datetime(pd.read_parquet(p).reset_index()[ts_col], utc=True)
        res["files"][y]["file_first_ts"] = str(t.min())
        res["files"][y]["file_last_ts"] = str(t.max())

    with open(OUT, "w") as f:
        json.dump(res, f, indent=1, default=str)

    print(f"rows={g['rows_total']:,}  {g['first_ts']} -> {g['last_ts']}")
    print(f"dups={g['dup_timestamps']} minute_aligned={g['minute_aligned_all']} "
          f"sorted={g['was_sorted_on_disk']} ohlc_viol={g['ohlc_violations']} "
          f"off_tick={g['off_tick_values']} nonpos={g['bad_close_nonpos']}")
    print(f"symbols={g.get('unique_symbol')} rtype={g.get('unique_rtype')} "
          f"instr_ids={g.get('instrument_id_unique')} rolls={g.get('roll_events')} "
          f"roll_gap_med={g.get('roll_gap_abs_median')} max={g.get('roll_gap_abs_max')}")
    print(f"gaps: eod/holiday={g['gaps_eod_or_holiday']} wknd={g['gaps_weekend']} "
          f"intraday={g['gaps_intraday_count']} ({g['gaps_intraday_total_min']} min total, "
          f">15min: {len(g['gaps_intraday_gt15min'])})  vol0={g['vol_zero']}")
    print(f"sessions={g['sessions_total']} bars/sess_med={g['bars_per_session_median']} "
          f"short(<1000)={g['sessions_lt_1000_bars']} missing_trade_days={g['missing_trade_days_count']} "
          f"weekend_dates={len(g['weekend_trade_dates'])}")
    print(f"spikes>50bps={g['ret1m_gt_50bps']}  range_max={g['range_max_pts']}pts")

if __name__ == "__main__":
    sys.exit(audit())
