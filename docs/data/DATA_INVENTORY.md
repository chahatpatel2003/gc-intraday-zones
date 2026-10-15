# DATA INVENTORY — GC / XAUUSD level-research project
Audit date: 2026-08-16 · Auditor: Claude (Phase 0 data audit) · Status: **frozen, pre-approval**

Canonical data root: `/Volumes/T9/Gc:Xauusd/` (note the literal `:` in the folder name — always quote paths).
Rule inherited from prior projects: **T9 data is treated read-only**; nothing on T9 or in Desktop data
folders was modified by this audit.

---

## 1. GC futures (PRIMARY)

**Location:** `/Volumes/T9/Gc:Xauusd/gc/` (research) and `/Volumes/T9/Gc:Xauusd/gc/Holdout/` (sealed).

| Property | Value |
|---|---|
| Source | Databento, CME Globex (`publisher_id=1`), symbol **`GC.v.0`** |
| Series type | **Continuous front-month, volume-rolled, NOT back-adjusted** (verified: 41 `instrument_id`s, 40 roll events 2016–2023, un-adjusted price jumps at rolls) |
| Data type | **1-minute OHLCV bars only** (`rtype=33`). No ticks, no trades, no MBP/quotes anywhere on disk |
| Format | Parquet, one file per year. Index `ts_event` = **bar-OPEN time, datetime64[ns, UTC]** |
| Columns | `rtype u8, publisher_id u16, instrument_id u32, open/high/low/close f64, volume u64, symbol str` |
| Tick size | 0.1 (all 2.78M research prices verified on-grid) |
| Session | Globex: 18:00 ET open → 17:00 ET close, daily 17:00–18:00 ET halt; ~258 sessions/yr; median 1378 bars/session |
| Volume | Contracts per minute; research median 73/min, max 21,135/min |

**Files** (bytes; row counts from data for research, from parquet footers for holdout):

| File | Rows | Actual coverage (UTC) | Size |
|---|---|---|---|
| gc_2016.parquet | 347,990 | 2016-01-03 23:00 → 2016-12-30 21:59 | 5.35 MB |
| gc_2017.parquet | 346,699 | 2017-01-02 23:00 → 2017-12-29 21:59 | 5.00 MB |
| gc_2018.parquet | 347,107 | 2018-01-01 23:00 → 2018-12-31 21:59 | 5.17 MB |
| gc_2019.parquet | 348,036 | 2019-01-01 23:00 → 2019-12-31 21:59 | 5.11 MB |
| gc_2020.parquet | 349,567 | 2020-01-01 23:00 → 2020-12-31 21:59 | 5.64 MB |
| gc_2021.parquet | 348,357 | 2021-01-03 23:00 → 2021-12-31 21:59 | 5.38 MB |
| gc_2022.parquet | 349,732 | 2022-01-02 23:00 → 2022-12-30 21:59 | 5.62 MB |
| gc_2023.parquet | 346,674 | 2023-01-02 23:00 → 2023-12-29 21:59 | 5.35 MB |
| **Holdout/gc_2024.parquet** | 351,320 | 2024-01-01 23:00 → 2024-12-31 21:59 (footer metadata only) | 5.68 MB |
| **Holdout/gc_2024_jan.parquet** | 28,098 | 2024-01-01 → 2024-01-30 — **duplicate subset of gc_2024** | 0.45 MB |
| **Holdout/gc_2025.parquet** | 350,874 | 2025-01-01 23:00 → 2025-12-31 21:59 (footer metadata only) | 6.14 MB |

Research total: **2,784,162 rows, 2016-01-03 → 2023-12-29.** Files partition cleanly (no cross-file
duplicates/overlaps). Holdout file schemas are footer-identical to research files.
**GC data ends 2025-12-31 — there is NO 2026 GC data on disk.**

**Contract identification:** only the continuous alias `GC.v.0` + numeric `instrument_id`; individual
contract symbols (GCJ4 etc.) are NOT recoverable from these files. Rolls are detectable only via
`instrument_id` changes (~5/yr, month-end, at session boundaries).

**Shadow copy (unsorted, contains holdout-period files):** `~/Desktop/gc DATA/` — all 11
files, byte-identical (sha256-verified). Sealed by rule; do not read from research code.

---

## 2. XAUUSD spot (SECONDARY) — Dukascopy

**Location:** `/Volumes/T9/Gc:Xauusd/XAUUSD Data/`

| Property | Value |
|---|---|
| Source | Dukascopy Bank historical feed (bank/broker feed, not exchange); downloaded 2026-06-29 by `xauusd_dukascopy.py` (script preserved, hash frozen) |
| Coverage | **2021-06-29 00:00 → 2026-06-28 23:59 UTC**, 1,772,172 1-min bars total; research slice (<2024) = 889,954 bars |
| Combined files | `XAUUSD_1min.csv` (143.3 MB) + `XAUUSD_1min.parquet` (40.1 MB) — **single files spanning research AND holdout periods** |
| Schema | `timestamp_utc` (bar-OPEN, stored **datetime64[us, UTC]** — µs, not ns!), `open/high/low/close` f64, `volume` f64, `source` str |
| Price basis | **BID-price OHLC**, 3 decimals (0.001 grid verified). Ask exists only in raw ticks |
| Volume units | Dukascopy native (millions of units), ask_vol+bid_vol summed; research median 0.041/min. Broker volume, not exchange volume |
| Session | 24h with daily halt 17:00 NY (21:00 UTC EDT / 22:00 UTC EST — DST-verified), weekend Fri 17:00 → Sun 18:00 ET, no Saturday bars |
| Raw ticks | `raw/XAUUSD/{YYYY}/{MM0}/{DD}/{HH}h_ticks.bi5` — **LZMA, big-endian `>3i2f`** = ms_into_hour, ask×1000, bid×1000, ask_vol f32, bid_vol f32. **Month folders are 0-indexed** (Jan=00). `*.nodata` marks empty hours |
| Raw research | 2021: 3,840 files/95.8 MB · 2022: 7,488/222.4 MB · 2023: 7,512/145.2 MB (nodata: 798/1,573/1,622) |
| Raw holdout | `raw/XAUUSD/Hold out/{2024,2025,2026}`: 18,720 files, 730 MB, 4,002 nodata — SEALED |
| Vendor audit artifacts | `README.txt`, `gaps_report.csv` (every gap>1min, classified), `daily_counts.csv`, `download.log` — all hash-frozen |

**Tick fidelity verified:** two research-period hours decoded from .bi5 reproduce the combined 1m file
**bar-for-bar exactly** (OHLC + volume), ms timestamps monotonic. Median observed spread ≈ **$0.32–0.35**.

**Shadow copy:** `/Volumes/T9/DATA/XAUUSD Data/` — full duplicate (combined files sha256-identical,
same research/`Hold out` raw arrangement, 18,720 files/730 MB holdout). Sealed by rule.

---

## 3. Cross-market overlap

- Common (both markets have a bar): 2021-06-29 → 2023-12-29 research: **874,856 common minutes**;
  GC-only 629; XAUUSD-only 15,098 (GC zero-trade minutes, GC holidays).
- Clock alignment: 1-min return correlation peaks at **lag 0** (0.960; ±1 min ≈ 0.01) — UTC clocks agree at minute precision. 5-min corr 0.982.
- Basis (GC − spot, 20:00 UTC): median +$0.94 (2021) → +$2.67 (2022) → +$10.29 (2023); p5–p95 −0.95…+22.6. Economically consistent carry.
- Full-range overlap after holdout decisions: GC ends 2025-12-31, XAUUSD ends 2026-06-28.

---

## 4. Other data on T9 (out of scope, for awareness)

`DATA/Gold Data/` (MT5 EA artifacts only, no data), `nq data/` (NQ Databento mbp1+trades),
`nq_levels/`, `NQ_HOLDOUT/`, `DATA/NAS 100 Data/` — NQ projects, not used here.

## 5. Prior-use disclosure (contamination map)

- **Phase 57 "GC viability" (Topstep project, ~June 2026)** backtested 15 intraday strategy families
  (incl. PDH/PDL sweeps, VWAP, POC/value-area — level-adjacent) on **GC.v.0 over FULL 2016–2025**,
  with published IS/OOS stats. ⇒ **No GC period on disk is virgin**, including the Holdout files.
- **AURUM (gold spot project, June 2026)** researched a *different* gold dataset through 2024 with 2025
  sealed. ⇒ gold-2024 market behavior was studied; XAUUSD-2025 untouched by discipline.
- **This Dukascopy XAUUSD download (2026-06-29) has no found consumers** in any prior project
  (searched all Desktop projects). ⇒ XAUUSD **2026 H1 is fully virgin**; 2025 near-virgin.
- Audit scripts here read GC 2016–2023 and XAUUSD <2024-01-01 only; holdout untouched except
  file bytes (hashing) and parquet footer/timestamp metadata.

Machine-readable detail: `aurum/audit/gc_audit.json`, `xauusd_audit.json`, `alignment_audit.json`,
`holdout_manifest.json`. Scripts: `tools/audit/*.py`.
