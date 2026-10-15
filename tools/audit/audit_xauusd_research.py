#!/usr/bin/env python3
"""XAUUSD (Dukascopy) research-window integrity audit.

RESEARCH WINDOW ONLY: rows with timestamp_utc < 2024-01-01 are loaded via a
mechanical pyarrow filter; holdout-period rows (2024+) are never materialized,
inspected, or summarized. Also decodes two research-period raw .bi5 tick hours
and reconciles them bar-for-bar against the combined 1m dataset.

Writes aurum/audit/xauusd_audit.json; prints a compact summary.
"""
import json, lzma, os, struct, sys
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pyarrow.compute as pc

BASE = "/Volumes/T9/Gc:Xauusd/XAUUSD Data"
PARQ = f"{BASE}/XAUUSD_1min.parquet"
OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "audit", "xauusd_audit.json"))
SEAL = pd.Timestamp("2024-01-01", tz="UTC")
SCALE = 1000.0

def load_research():
    t = pq.read_table(PARQ, filters=[("timestamp_utc", "<", SEAL.to_pydatetime())])
    df = t.to_pandas()
    if "timestamp_utc" not in df.columns:
        df = df.reset_index()
    return df

def decode_bi5(path):
    raw = lzma.decompress(open(path, "rb").read())
    n = len(raw) // 20
    rec = struct.unpack(">" + "3i2f" * n, raw[:n * 20])
    a = np.array(rec, dtype=object).reshape(n, 5)
    ms = a[:, 0].astype(np.int64)
    ask = a[:, 1].astype(np.int64) / SCALE
    bid = a[:, 2].astype(np.int64) / SCALE
    av = a[:, 3].astype(float); bv = a[:, 4].astype(float)
    return ms, ask, bid, av, bv

def ticks_to_1m(hour_utc, ms, bid, av, bv):
    t = pd.to_datetime(hour_utc, utc=True) + pd.to_timedelta(ms, unit="ms")
    df = pd.DataFrame({"bid": bid, "vol": av + bv}, index=t)
    o = df["bid"].resample("1min").ohlc()
    v = df["vol"].resample("1min").sum()
    o["volume"] = v
    return o.dropna(subset=["open"])

def audit():
    res = {}
    df = load_research()
    ts = pd.to_datetime(df["timestamp_utc"], utc=True).dt.as_unit("ns")
    df = df.assign(_ts=ts).sort_values("_ts", kind="stable").reset_index(drop=True)
    r = res
    r["columns"] = {c: str(t) for c, t in df.dtypes.items()}
    r["rows_research"] = int(len(df))
    r["first_ts"] = str(df["_ts"].iloc[0]); r["last_ts"] = str(df["_ts"].iloc[-1])
    ns = df["_ts"].astype("int64")
    r["was_sorted_on_disk"] = bool(ts.is_monotonic_increasing)
    r["minute_aligned_all"] = bool(((ns % 60_000_000_000) == 0).all())
    r["dup_timestamps"] = int(df["_ts"].duplicated().sum())
    r["source_unique"] = [str(x) for x in df["source"].unique()] if "source" in df else None

    for c in ("open", "high", "low", "close"):
        r[f"bad_{c}_nonpos"] = int((df[c] <= 0).sum())
        r[f"nan_{c}"] = int(df[c].isna().sum())
    r["ohlc_violations"] = int(((df["high"] < df[["open", "close"]].max(axis=1)) |
                                (df["low"] > df[["open", "close"]].min(axis=1)) |
                                (df["high"] < df["low"])).sum())
    scaled = df[["open", "high", "low", "close"]].to_numpy() * SCALE
    r["off_scale_values"] = int((np.abs(scaled - np.round(scaled)) > 1e-6).sum())
    r["price_min"] = float(df["low"].min()); r["price_max"] = float(df["high"].max())

    dt = np.diff(ns.to_numpy()) / 1e9
    lr = np.log(df["close"].to_numpy()[1:] / df["close"].to_numpy()[:-1])
    intra = dt <= 120
    r["ret1m_abs_p9999_bps"] = float(np.quantile(np.abs(lr[intra]), 0.9999) * 1e4)
    big = np.flatnonzero((np.abs(lr) > 0.005) & intra) + 1
    r["ret1m_gt_50bps"] = int(len(big))
    r["ret1m_worst"] = [{"ts": str(df["_ts"].iloc[i]),
                         "ret_bps": round(float(lr[i - 1]) * 1e4, 1)}
                        for i in big[np.argsort(-np.abs(lr[big - 1]))][:8]]

    r["vol_dtype"] = str(df["volume"].dtype)
    r["vol_negative"] = int((df["volume"] < 0).sum())
    r["vol_zero"] = int((df["volume"] == 0).sum())
    r["vol_p50"] = float(df["volume"].median()); r["vol_max"] = float(df["volume"].max())

    # gaps: daily break is 17:00 New York (21:00 or 22:00 UTC by DST)
    et = df["_ts"].dt.tz_convert("America/New_York").dt.tz_localize(None)
    gaps_ix = np.flatnonzero(dt > 60)
    daily, weekend, intraday = 0, 0, []
    break_start_utc_hours = {}
    for i in gaps_ix:
        t0, t1 = et.iloc[i], et.iloc[i + 1]
        mins = int(dt[i] / 60 - 1)
        d0 = t0.normalize()
        halts = pd.date_range(d0, t1.normalize(), freq="D") + pd.Timedelta(hours=17)
        spans_halt = any((t0 < h <= t1) for h in halts)
        if spans_halt and (t1.weekday() in (5, 6) or (t0.weekday() == 4 and t1.weekday() == 6)):
            weekend += 1
        elif spans_halt:
            daily += 1
            h = df["_ts"].iloc[i + 1].hour
            break_start_utc_hours[h] = break_start_utc_hours.get(h, 0) + 1
        else:
            intraday.append({"from": str(df['_ts'].iloc[i]),
                             "to": str(df['_ts'].iloc[i + 1]), "missing_min": mins})
    r["gaps_daily_break"] = daily
    r["gaps_weekend"] = weekend
    r["reopen_utc_hour_counts"] = break_start_utc_hours
    r["gaps_intraday_count"] = len(intraday)
    r["gaps_intraday_total_min"] = int(sum(x["missing_min"] for x in intraday))
    r["gaps_intraday_top"] = sorted(intraday, key=lambda x: -x["missing_min"])[:20]

    # per-day bar counts (UTC calendar day, like daily_counts.csv)
    day = df["_ts"].dt.floor("D")
    per = day.value_counts().sort_index()
    r["days_total"] = int(len(per))
    r["bars_per_day_median"] = float(per.median())
    r["days_lt_1000"] = {str(k.date()): int(v) for k, v in per[per < 1000].items()}
    all_days = pd.date_range(per.index.min(), per.index.max(), freq="D")
    missing = [d for d in all_days if d not in set(per.index)]
    r["zero_bar_days_excl_sat"] = [str(d.date()) for d in missing if d.weekday() != 5]
    r["saturday_bars_total"] = int((df["_ts"].dt.weekday == 5).sum())

    # cross-check against the dataset's own gaps_report (research window)
    gr = pd.read_csv(f"{BASE}/gaps_report.csv", parse_dates=["gap_start_utc", "gap_end_utc"])
    grr = gr[gr["gap_end_utc"] < SEAL]
    r["gaps_report_research_rows"] = int(len(grr))
    r["gaps_report_research_by_class"] = {str(k): int(v) for k, v in
                                          grr["classification"].value_counts().items()}
    my_total = daily + weekend + len(intraday)
    r["my_gap_total_vs_report"] = [int(my_total), int(len(grr))]

    # ---- raw .bi5 tick reconciliation (research hours only) ----
    checks = []
    for (y, m0, d, h) in [(2022, "02", "01", "10"), (2023, "08", "15", "13")]:
        p = f"{BASE}/raw/XAUUSD/{y}/{m0}/{d}/{h}h_ticks.bi5"
        month = int(m0) + 1
        hour_utc = f"{y}-{month:02d}-{d} {h}:00:00"
        try:
            ms, ask, bid, av, bv = decode_bi5(p)
            bars = ticks_to_1m(hour_utc, ms, bid, av, bv)
            win = df[(df["_ts"] >= pd.Timestamp(hour_utc, tz="UTC")) &
                     (df["_ts"] < pd.Timestamp(hour_utc, tz="UTC") + pd.Timedelta(hours=1))]
            merged = bars.join(win.set_index("_ts")[["open", "high", "low", "close", "volume"]],
                               how="inner", rsuffix="_ds")
            price_ok = bool(np.allclose(merged[["open", "high", "low", "close"]].to_numpy(),
                                        merged[["open_ds", "high_ds", "low_ds", "close_ds"]].to_numpy(),
                                        atol=1e-9))
            vol_ok = bool(np.allclose(merged["volume"].to_numpy(),
                                      merged["volume_ds"].to_numpy(), rtol=1e-5))
            spread = ask - bid
            checks.append({"hour": hour_utc, "ticks": int(len(ms)),
                           "bars_raw": int(len(bars)), "bars_ds": int(len(win)),
                           "bars_matched": int(len(merged)),
                           "price_exact_match": price_ok, "volume_match": vol_ok,
                           "spread_usd_median": round(float(np.median(spread)), 3),
                           "spread_usd_p90": round(float(np.quantile(spread, 0.9)), 3),
                           "ms_monotonic": bool((np.diff(ms) >= 0).all())})
        except Exception as e:
            checks.append({"hour": hour_utc, "error": repr(e)})
    r["bi5_reconciliation"] = checks

    with open(OUT, "w") as f:
        json.dump(res, f, indent=1, default=str)

    print(f"rows={r['rows_research']:,}  {r['first_ts']} -> {r['last_ts']}")
    print(f"dups={r['dup_timestamps']} aligned={r['minute_aligned_all']} sorted={r['was_sorted_on_disk']} "
          f"ohlc_viol={r['ohlc_violations']} off_scale={r['off_scale_values']} "
          f"nonpos={r['bad_close_nonpos']} vol0={r['vol_zero']}")
    print(f"gaps: daily={r['gaps_daily_break']} wknd={r['gaps_weekend']} "
          f"intraday={r['gaps_intraday_count']} ({r['gaps_intraday_total_min']}min) "
          f"reopen_hours={r['reopen_utc_hour_counts']}")
    print(f"days={r['days_total']} bars/day_med={r['bars_per_day_median']} "
          f"short_days={len(r['days_lt_1000'])} zero_days={r['zero_bar_days_excl_sat']} "
          f"sat_bars={r['saturday_bars_total']}")
    print(f"gap totals mine-vs-report: {r['my_gap_total_vs_report']} "
          f"report_by_class={r['gaps_report_research_by_class']}")
    for c in checks:
        print("bi5:", c)

if __name__ == "__main__":
    sys.exit(audit())
