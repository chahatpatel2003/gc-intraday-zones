# BATCH 2 — ZONE-LOCATION RESULTS (discovery 2016–2021, GC only)
Run 2026-08-16 · specs frozen pre-run (BATCH2_SPECS.md) · controls per EVALUATION_FRAMEWORK v1.3
(C1v2 nearest-eligible strips, same-family exclusion — amended from availability diagnostics only,
union-variant smoke outputs deleted unread; C2 moment-matched unchanged) · 19/19 leakage/parity
checks passed pre-run · seed 20260816 · 1,548 sessions · no 2022+ data touched.
Primary: Δ mean NetFav60/ADR14 (ZON-015: continuation NetAdv60/ADR14) vs C1v2 AND C2.

## Verdict table

| Family | N | Δ vs C1v2 [95% CI] | Δ vs C2 [95% CI] | Years +ve vs C2 | Classification |
|---|---|---|---|---|---|
| ZON-007 displacement origin 15m | 305 | +0.033 [0.000, +0.065] | +0.021 [−0.010, +0.047] | 4/6 | NO LOCATION EDGE (borderline, thin N) |
| ZON-008 rejection tail 30m | 2,012 | +0.007 [−0.008, +0.023] | −0.008 [−0.020, +0.004] | 3/6 | NO LOCATION EDGE |
| ZON-009 breakout role-reversal 1h | 3,606 | +0.013 [−0.012, +0.037] | +0.007 [−0.003, +0.016] | 4/6 | NO LOCATION EDGE |
| ZON-010 acceptance boundary 3-day | 1,391 | −0.008 [−0.023, +0.006] | **−0.014 [−0.026, −0.001]** | 1/6 | NO LOCATION EDGE |
| ZON-011 VWAP ±2σ | 7,052 | +0.007 [−0.001, +0.014] | **−0.018 [−0.024, −0.012]** | 0/6 | NO LOCATION EDGE |
| **ZON-012 volume-concentration boundary 6h** | **15,414** | **+0.010 [+0.003, +0.018]** | **+0.007 [+0.004, +0.011]** | **6/6** | **PROMISING** |
| ZON-013 compression→expansion 5m | 3,611 | −0.007 [−0.029, +0.015] | **+0.013 [+0.006, +0.020]** | 6/6 | NO LOCATION EDGE |
| ZON-014 HTF imbalance confluence | 1,149 | +0.002 [−0.018, +0.020] | +0.002 [−0.013, +0.017] | 2/6 | NO LOCATION EDGE |
| ZON-015 FVG continuation (EXPLORATORY) | 13,791 | **+0.058 [+0.045, +0.070]** (continuation) | **−0.017 [−0.021, −0.013]** (continuation) | 0/6 | NO LOCATION EDGE (exploratory) |

## The one survivor — ZON-012 (PROMISING, not STRONG)

Rolling 6-hour volume-profile VA boundaries beat BOTH controls with CIs clear of zero and are
positive vs C2 in all six years (range +0.002…+0.014). It fails STRONG on **materiality**: the
uplift is +0.7–1.0% of ADR (≈0.15–0.2 pt at ADR≈20) against a +5% floor. It is a real but SMALL
location signal, delivered at very high frequency (10.0 primary events/day, median width 0.10 ADR,
median zone age at touch 28 min). Per the preregistered rules: provisional, requires user-gated
validation; no promotion, no filtering, no optimization performed.

## Continuation findings (ZON-015, exploratory)

The two controls answer differently and both cleanly: entering a 15m FVG produces MORE traversal/
continuation than nearby non-FVG strips (+0.058 ADR, CI [+0.045, +0.070] — FVGs are locally
porous), but LESS continuation than matched momentum-moments elsewhere (−0.017 ADR — consistent
with Batch-1's small bounce-lean vs C2). Under the both-controls rule: no edge. The C1/C2 split is
itself informative: FVG location information exists but its sign depends on the null — relative to
its neighborhood an FVG is a conduit; relative to matched moments it slightly brakes. Recorded as
observation only (exploratory family; no new hypothesis registered).

## Other notable descriptive facts (no hypotheses drawn)

- ZON-007 (displacement origins) is the only other family with both point estimates positive
  (+0.033/+0.021) and was held back by CI width at N=305 and 2020–21 sign flips.
- ZON-013 (compression boxes) beats matched moments consistently (+0.013, 6/6 years) but not its
  own neighborhood (C1 −0.007) — the box area is no better than strips ±2–12W away.
- ZON-010/ZON-011 are actively worse than matched moments (VWAP ±2σ bands get run through;
  0/6 and 1/6 years positive).
- Reclaim after traversal remains 94–98% everywhere; median penetration 0.9–2.2×W — Batch-2 zones
  are as porous as Batch-1's.

## Density / spacing / confluence

- Raw candidate interactions: **31.5 primary events/day** summed over families; Layer-2 dedup:
  **22.4 independent primary clusters/day** (27.6% multi-family), 32.0/day counting all touches
  (55.7% multi-family — Batch-2 families tag heavily overlapping structures, esp. 012+015, 011+012,
  013+015). 99.3% of sessions have >5 interactions.
- **Strong-criterion frequency: 0/day** (no STRONG family). Strong+PROMISING = 10.0/day, all from
  ZON-012 (tiny per-event effect). The 2–5 strong/day product target is NOT met by Batch 2.
- Spacing (median nearest-neighbor gap, ADR units): sparse families ZON-010 0.71, ZON-007 0.38;
  dense families 0.02–0.08 with 60–85% same-family overlap pairs (ZON-009 0.031/82.5%,
  ZON-011 0.039/68.5%, ZON-012 0.035/85.1%, ZON-015 0.018/70.7%) — dense families are heavily
  self-overlapping; dedup handled counting, but as products they would crowd the chart.

## Control-quality diagnostics (C1v2)

Shadows/zone: 3.3–4.0 for ZON-007/008/010/011/012/014 (zones-without-control ≈ 0); residual
starvation where same-family zones blanket space: ZON-015 49% zones uncontrolled (0.91 shadows/zone
— still far better than Batch-1's 94%), ZON-009 35%, ZON-013 17%. Ladder distances: k=2–3 dominant
for most families; ZON-015's controls sit farther out (mode k=10–12), so its C1 compares against
strips up to ~0.5 ADR away — documented, not repaired post-hoc. C2 donor shortfalls negligible
(≤172 events). The v1.3 amendment trail (union-blob variant starved: 0.12–1.33 shadows/zone, one
family zero controls; outputs deleted unread) is in EVALUATION_FRAMEWORK §3.

## Failure modes / data issues

- ZON-014 ambiguity 17.2% (intersection zones are tiny vs 1m bars); ZON-015 11.0%; others ≤8%.
- ZON-007 delivered only 305 events (0.23 zones/day) — at the sample floor; its borderline result
  is fragile by construction.
- ZON-009 zones are highly duplicative (one pivot family, 82.5% overlap pairs) — dedup contained
  it (3,606 events from 6,209 zones).
- Rolling families (011/012) rest on generation-time IoU dedup; without it the snapshot count
  would be ~5×. Frozen pre-run; sensitivity NOT explored (would be post-hoc).
- All families remain bounded by the 1m-resolution ceiling and roll-window data holes (flags
  carried on every episode; truncated horizons ≤0.5% everywhere).

## Bottom line

Batch 2 produced the project's first family to clear both preregistered controls — ZON-012
volume-concentration boundaries — but at ~1% of ADR it is an order of magnitude below the
materiality bar for STRONG, and no family met the strong-location criterion. Frequency of strong
zones remains **zero per day**; the raw candidate stream (22–32 independent interactions/day) is
abundant and mediocre. Two structural facts recur across 15 hypotheses: GC zones are porous
(reclaim ≈95%), and location effects, where present, are small relative to normal excursion noise.
