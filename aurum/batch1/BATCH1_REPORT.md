# BATCH 1 — ZONE-LOCATION RESULTS (discovery 2016–2021, GC only)
Run 2026-08-16 · engine `tools/batch1/` · seed 20260816 · specs frozen pre-run (ZONE_SPEC v1.1,
EVALUATION_FRAMEWORK v1.1) · 1,548 sessions, 2,087,756 1-min bars · no 2022+ data touched.

Primary metric: Δ mean NetFav60/ADR14 = (max favorable − max adverse excursion at 60 trading min,
in ADR units), real first-touch events vs C1 displaced shadows (unpaired) and C2 moment-matched
pseudo-zones (paired, K=5). Positive Δ = the real zone's location produced better subsequent
behavior than a comparable non-zone area.

## Verdict table

| Family | N primary | Δ vs C1 [95% CI] | Δ vs C2 [95% CI] | Years +ve vs C2 | Classification |
|---|---|---|---|---|---|
| ZON-001 prior-session extremes | 1,683 | −0.014 [−0.029, +0.001] | **−0.029 [−0.042, −0.016]** | 0/6 | **NO LOCATION EDGE** |
| ZON-002 FVG 15m | 13,791 | **−0.063 [−0.077, −0.049]**¹ | **+0.016 [+0.012, +0.020]** | 6/6 | **NO LOCATION EDGE** (by rule¹) |
| ZON-003 value-area edges | 3,106 | +0.004 [−0.007, +0.014] | +0.002 [−0.005, +0.010] | 2/6 | **NO LOCATION EDGE** |
| ZON-004 supply/demand base | 5 | — | — | — | **INSUFFICIENT DATA** |
| ZON-005 round numbers | 601 | −0.027 [−0.055, +0.002] | **−0.041 [−0.065, −0.016]** | 1/6 | **NO LOCATION EDGE** |
| ZON-006 pivot clusters 1h | 4,514 | +0.005 [−0.009, +0.021] | **−0.016 [−0.023, −0.009]** | 0/6 | **NO LOCATION EDGE** |

¹ ZON-002's C1 must be read with a flagged defect: 94.2% of its shadows were unavailable (FVGs
cluster so densely that displaced shadows almost always overlap another real FVG). The surviving
6% sit in atypically quiet areas — a selected, likely unfavorable control. Its paired C2 result
(+0.016 ADR, positive all 6 years) is the cleaner comparison but fails the preregistered rule
(CI > 0 vs BOTH controls) and is small in absolute terms (~+1.6% of ADR ≈ 0.3 pt at ADR≈20).
The classification stands; the caveat is recorded for the user's review.

## What the data actually shows (descriptive, no new hypotheses drawn)

1. **No family produced bounce-type location edge.** At every structurally visible zone except
   FVG, price does the same or WORSE (more adverse penetration, deeper traversal) than at matched
   arbitrary areas reached in comparable conditions.
2. **Prior extremes and round numbers behave like conduits, not barriers**: traversal within 120m
   is +5–8 pp (ZON-001) and +15 pp (ZON-005 vs C2) HIGHER than controls; NetFav is negative vs
   controls in nearly every year (ZON-001: 6/6 negative; ZON-005: 5/6). Rejection ≥0.25·ADR before
   traversal is LESS likely at real zones than at shadows for every family (−2 to −10 pp).
3. **Value-area edges (ZON-003) mildly impede traversal** (−4.7 to −7.6 pp vs controls) but produce
   zero net excursion advantage — price stalls there without reacting directionally.
4. **Touch degradation is universal and steep**: mean NetFav60/ADR by stratum, e.g. ZON-001:
   t1 −0.028 → t2 −0.121 → t3+ −0.198 → retest −0.143; ZON-006: −0.018 → −0.101 → −0.160.
   Later touches at any zone were strongly adverse for the bounce framing. First touches are the
   least bad everywhere.
5. **Zones are porous**: median max penetration 0.6–2.2 × zone width; reclaim (re-entry after full
   traversal within 120m) 94–98% everywhere — traversals routinely retrace into the zone.
6. **Session/vol slices don't rescue anything** (descriptive): signs are stable across ASIA/LONDON/
   NY/LATE within each family; no subgroup selection performed.

## Density & opportunity accounting (Layer-2 clusters, EVALUATION_FRAMEWORK §5)

| Level | independent interactions/day | multi-family share |
|---|---|---|
| Primary (first touches) | **13.7** clusters/day (20,947 total) | 10.5% |
| All touches | **47.6** clusters/day (72,997 from 123,219 episodes) | 25.3% |

99.8% of sessions have >5 independent interactions (median 47/day): with these six specs active
the chart is heavily overcrowded relative to the eventual 2–5 strong-opportunities/day target —
frequency is abundant; SELECTIVITY is what's missing. Family densities: ZON-002 dominates
(9.0 primary events/day, median width only 0.042 ADR); ZON-001 1.10/day; ZON-003 2.03/day;
ZON-006 2.94/day; ZON-005 0.39/day; ZON-004 0.003/day.
Top confluence pairs (all-touch): FVG+value-edges (10,321), FVG+pivot-clusters (9,359).

## Per-family metric profile (primary events, means)

| Family | FE60/ADR | AE60/ADR | rejA | rejW | trav120 | depth med | reclaim | speed (med min to 0.25·ADR) | width med (ADR) | age med (min) |
|---|---|---|---|---|---|---|---|---|---|---|
| ZON-001 | 0.115 | 0.143 | 13.1% | 20.3% | 32.2% | 0.60 W | 93.7% | 52 | 0.20 | 221 |
| ZON-002 | 0.118 | 0.112 | 10.3% | 48.0% | 73.8% | 2.22 W | 97.6% | 45 | 0.042 | 18 |
| ZON-003 | 0.101 | 0.106 | 9.9% | 41.0% | 46.8% | 0.93 W | 96.3% | 57 | 0.10 | 141 |
| ZON-005 | 0.132 | 0.176 | 12.2% | 41.4% | 63.4% | 1.48 W | 94.8% | 40 | 0.10 | 524 |
| ZON-006 | 0.113 | 0.131 | 14.3% | 28.1% | 38.2% | 0.68 W | 95.7% | 59 | 0.16 | 91 |

Full horizon curves (5/15/30/60/120m, points + ticks + /ADR + /W), sessions, yearly tables:
`batch1_stats.json`; raw episode tables: `episodes_*.parquet`, `events_*.parquet`,
`interaction_clusters_all.parquet`.

## Failure modes / data issues recorded

- **C1 starvation for ZON-002** (94.2% shadows unavailable; ZON-006 60.7%; ZON-003 31.4%) — dense
  families structurally weaken the displaced-shadow control; noted for any future control design.
- **1m resolution vs narrow zones**: ZON-002 ambiguity rate 11.0% (both edges inside one 1m bar);
  ZON-005 8.7%; others 3–4%. Conclusions about zones ≲0.05 ADR wide carry material intrabar
  uncertainty (protocol §A caveat honored).
- **ZON-004's registered spec fires ~1×/year** (6 zones in 6 years) — honestly INSUFFICIENT DATA;
  per protocol it was NOT loosened post-hoc; any different base definition is a new hypothesis.
- Inside-at-activation contacts (excluded, counted): ZON-002 21,766; ZON-006 6,557; ZON-003 4,242;
  ZON-001 2,567; ZON-005 475. Roll-truncated 60m horizons: ≤69 per family (negligible).
- Pre-run engine fixes are logged in EVALUATION_FRAMEWORK §8 (touch-index clarification; approach-
  relative break start for untyped zones) — both made before any outcome delta was viewed.

## Bottom line

Under preregistered controls, **none of the six families demonstrates exploitable bounce-type
location edge on GC at first touch in 2016–2021**. The two genuine, consistent location signals in
the batch have the OPPOSITE character: structurally visible reference prices (prior extremes, round
numbers) get traversed MORE than comparable areas, and the only positive-vs-context result
(FVG vs C2, +1.6% ADR, 6/6 years) is too small to clear both controls. Whether any of these
observations becomes a new hypothesis (e.g. continuation-through-zones framing) is the user's
decision — none has been registered or tested.
