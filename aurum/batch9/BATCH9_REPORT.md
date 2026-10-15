# BATCH 9 — TRADE-PRODUCT PHASE RESULTS (1R TP-BEFORE-SL)
Run 2026-08-16 · plan frozen pre-outcome (BATCH9_PLAN.md) · 30 predefined variants (6 families ×
C0–C4), no additions · discovery 2016–2019 · **zero finalists → confirmation stage empty;
2020–2021 was NOT opened in this phase** · 2022+ untouched · ZON-028 untouched.

## Question and answer

> Can any mechanically generated GC zone + small 1m confirmation produce a 60–70% realistic 1R
> TP-before-SL reaction with a small stop and useful frequency?

**NO — and it is not close.** Across all 30 variants (73,703 raw interactions simulated):
- Best win rate: **49.4%** (F3 compression × C3 micro-break — 83 trades, 0.08/day, below every
  frequency floor). Every other variant: **33.3–48.0%**.
- **All 30 variants have negative net expectancy** except that same 83-trade outlier (+0.04R).
- The matched best-of-30 random null (50 tournaments, same frequency/stops/costs/rules): best
  random WR median **50.0%**, p95 **53.6%**, p99 54.7%; best random expectancy p95 −0.01R.
  **The real zone+confirmation setups performed BELOW random entries.** Fading a zone touch after
  a confirmation is adversely selected: the confirmation consumes the bounce, then mean reversion
  works against the displaced entry.

## Discovery table (headline rows; full table discovery_table.csv / discovery_stats.json)

| Variant | n | trades/day | WR(1R) | net exp (R) | timeout | ambig | stop med (pt / ADR) | notes |
|---|---|---|---|---|---|---|---|---|
| F3×C3 | 83 | 0.08 | .494 | +0.04 | 13% | 0% | 1.4 / 0.086 | only positive; 90% of its attempts STOP_TOO_LARGE; unusable frequency |
| F6×C0 | 371 | 0.36 | .480 | −0.11 | 4% | 1% | 1.2 / 0.081 | 2018 WR .288 |
| F2×C0 | 1,615 | 1.59 | .467 | −0.13 | 5% | 2% | 1.2 / 0.090 | 84% attempts gated out |
| F4×C0 | 819 | 0.80 | .454 | −0.19 | 2% | 1% | 1.0 / 0.073 | |
| F1×C1 | 4,228 | 4.15 | .435 | −0.21 | 3% | 0% | 1.0 / 0.066 | 1,153 missed + 751 cancelled |
| F1×C0 | 5,981 | 5.88 | .429 | −0.28 | 2% | 2% | 0.8 / 0.058 | max losing streak 12 |
| F5 (all confs) | 120–477 | ≤0.47 | .33–.40 | −0.25…−0.37 | | | | worst family |

Confirmation-cost findings (the §7 measurements): confirmations DID raise WR slightly over C0
within families (e.g. F1: C0 .429 → C1 .435 → C2 .443) but never by more than ~1.5 points, while
adding delay (0–2 bars median), consuming pre-entry movement (median 0.8–2.0% of ADR already
gone), inflating stops (C-entries push R up ≈ 0.2 pt), and discarding 20–50% of setups
(missed+cancelled). No confirmation converts a ~45% zone into anything near 60%.

Structural mechanics behaved as designed: three-concept separation enforced (structural validity
vs eligibility vs trade stop; max 1 attempt per zone); ambiguity was a non-issue (0–2.4% — stops
of ~1 pt dwarf 1m bar ranges); timeouts 2–16%; STOP_TOO_LARGE gate excluded 24–90% of attempts
per variant (wide zones + confirmation displacement frequently exceed 0.10·ADR — reported, not
tuned); yearly WRs were stable at their LOW levels (no year of any major variant exceeded 50%).

## Why (mechanism, consistent with 44 prior hypotheses)

The location research already established that GC zones carry at most +0.01–0.02 ADR of
context-adjusted information. A 1R bracket with R ≈ 0.06–0.09 ADR requires the zone to shift the
first-passage probability by ~10–20 percentage points to reach 60%; the measured information
content supports ~1–3 points at best — and the confirmation's adverse selection plus the
conservative both-in-bar rule and costs consume more than that. The 60–70% product target is not
a tuning distance away from these zones; it is a category distance.

## Frozen-process outcome

Finalist rule (WR ≥ 60%, net > 0, ≥ 0.5/day, ambig ≤ 15%, > null p95): **zero qualifiers.**
No finalists → nothing frozen → 2020–2021 confirmation not run → no combined stream. No rescue,
no parameter changes, no month deletion. ZON-044 (the phase registration) closes as FAIL.

## Files
`BATCH9_PLAN.md` · `tools/batch9/{trade_lib.py, run_discovery.py}` ·
`aurum/batch9/{trades_discovery.parquet, discovery_stats.json, discovery_table.csv, null30.json,
BATCH9_REPORT.md}` · ledger ZON-044 closed. Hypothesis count: **44**.
