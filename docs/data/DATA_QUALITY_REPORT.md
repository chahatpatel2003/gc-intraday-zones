# DATA QUALITY REPORT — GC / XAUUSD
Audit date: 2026-08-16 · Non-holdout data only (GC 2016–2023; XAUUSD 2021-06→2023-12).
Detail JSONs in `aurum/audit/`; reproducible via `tools/audit/`.

## 1. GC (Databento GC.v.0 1-min) — verdict: **GOOD, with three structural caveats**

**Clean:** 0 duplicate timestamps (incl. across file boundaries) · chronologically sorted ·
all timestamps exactly minute-aligned ns-UTC · 0 OHLC-consistency violations · 0 non-positive/NaN
prices · all prices on the 0.1 tick grid · 0 zero/negative-volume bars · yearly files partition
cleanly · consistent schema across all files (holdout footers included).

**Calendar:** 2,063 trade sessions; 23 zero-bar weekdays = CME full holidays (all verified plausible);
39 short sessions = exchange early closes; 1 stray bar on Sunday 2018-08-05 (single pre-open print;
negligible, excluded by session filters).

**Extreme prints are real, not errors** — worst 1-min moves land exactly on known events (2016 NFPs,
Brexit, 2020-01-05 Soleimani gap, 2021-08-08 gold flash crash, 2022 CPI prints). p99.99 |1-min ret|
= 38 bps; max 1-min range 42.8 pts.

**Caveat A — un-adjusted volume rolls (~5/yr).** 40 roll events in 2016–2023, median artificial
close→open jump **5.9 pts**, max **38.2 pts** (vs p99.9 of non-roll close→open = 0.7 pt). A level
computed across a roll boundary is contaminated by an artificial gap ≈8× larger than any normal
minute step. Consequences (locked into protocol): level state must be roll-aware; multi-day levels
must either be recomputed per contract segment, use a project-built back-adjustment, or be
invalidated at rolls; roll timestamps derived from `instrument_id` changes.

**Caveat B — zero-trade minutes are absent.** 17,584 intraday missing-minute gaps totaling 48,518
min (~1.7% of session minutes), overwhelmingly 1–3 min in quiet Asia hours; 472 gaps >15 min
cluster at **roll-window liquidity deserts** (outgoing contract dying). Notable holes:
2020-02-27/28 (session of Fri 2020-02-28 **entirely missing** — COVID-week roll; a real, violent
market day), 2019-02-27 (181 min), 2021-11-30 (93 min). Consequences: "no bar" ≠ "market closed";
a level touch can only be observed at a traded price; time-based features must tolerate missing
minutes; month-end roll days need a data-coverage flag.

**Caveat C — resolution ceiling.** 1-minute trade bars are the finest GC data owned. Intrabar
ordering of high vs low is unknowable → exact tick-level first passage is not reconstructible
(see §4).

## 2. XAUUSD (Dukascopy 1-min + raw ticks) — verdict: **VERY GOOD, minor caveats**

**Clean:** 0 duplicates · sorted · minute-aligned (µs storage unit — handled) · 0 OHLC violations ·
0 non-positive prices · all prices on 0.001 grid · 0 zero-volume bars · no Saturday bars ·
daily halt follows NY 17:00 exactly (21:00 UTC EDT / 22:00 UTC EST; reopen-hour counts 345 vs 175
match the DST calendar) · 6 zero-bar days in window = known holidays · my independent gap scan
reconciles with the vendor's own `gaps_report.csv` **exactly (936 = 936 events)**.

**Density:** 778 UTC days, median 1,379 bars/day; intraday missing minutes total just **416 min
over 2.5 years** (289 gaps; worst single outage 54 min on 2023-09-25). Far denser than GC bars
(quote-driven vs trade-driven).

**Tick layer verified:** two sampled hours decoded from raw `.bi5` reproduce the 1m dataset
bar-for-bar (OHLC + volume exact), ms timestamps monotonic; spread median ≈ $0.32–0.35, p90 ≈ $0.39.
Extremes real (same 2021-08-08 flash crash, −269 bps minute; 2022 CPI +128 bps).

**Caveats:** (a) bid-price OHLC — bar "touches" are bid touches; ask path only via raw ticks;
(b) single-bank feed — spreads/volumes are broker-specific, volume units are notional millions,
not exchange volume; (c) µs-vs-ns storage trap (documented; one audit bug already caused by it);
(d) weekend/holiday behavior differs slightly from CME (spot trades some CME holidays).

## 3. Cross-market sanity — verdict: **ALIGNED**

874,856 common research minutes; 1-min return correlation peaks precisely at lag 0 (0.960, ±1 min
≈ 0.01) → no clock skew at minute resolution; 5-min corr 0.982; futures−spot basis positive and
rate-consistent (median $0.94 → $10.29 across 2021→2023; only 5 days < −$2). XAUUSD is a valid
alignment/sanity companion and a cautious tick-resolution *proxy* for GC intrabar paths — never a
substitute for GC first-passage labels (basis drifts intraday; microstructures differ).

## 4. Exact first-passage verdict

- **GC: exact tick-level first passage NOT possible** (1-min bars only). Possible and locked into
  protocol: bar-path first passage at 1-min granularity with a **conservative ambiguity rule** —
  if TP and SL levels are both inside one bar's range, the trade labels as SL-first (worst case)
  and is also counted in a mandatory **ambiguity-rate metric** reported per label configuration;
  configurations with material ambiguity rates are invalid for tight-stop conclusions.
- **XAUUSD: exact first passage IS possible** (ms bid+ask ticks) across research and holdout.
- Upgrade path if a GC candidate survives to needing exact paths: purchase Databento GC trades
  (tick) data — also repairs roll-window visibility. Deferred; not needed for location-edge phase.
