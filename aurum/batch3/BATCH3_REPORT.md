# BATCH 3 — LIFECYCLE & ZONE-QUALITY RESULTS (discovery 2016–2021, GC only)
Run 2026-08-16 · specs frozen pre-run (BATCH3_SPECS.md, ZONE_LIFECYCLE.md) · parity/causality
tests 6/6 PASS (incl. a causality flaw caught in design review: ZON-021's condition now uses
`depth_end` — depth at episode end — because `depth120`'s window can overlap touch 2; engine field
added additively, no cached results changed) · seed 20260816 · no 2022+ data touched.

Parent universes regenerated deterministically: ZON-012 28,242 zones (instrumented twin verified
byte-identical), 17,108 primary rows; ZON-013 3,844 zones, 3,704 primary rows.

## Verdict table (Δ mean NetFav60/ADR14)

| Hyp | Condition | N | Δ vs C1v2 [CI] | Δ vs C2 [CI] | Yrs +ve | Events/day | Class |
|---|---|---|---|---|---|---|---|
| ZON-016 | 012 FRESH (≤60m, no prior inside) | 11,133 | +0.026 [+0.014, +0.038] | −0.000 [−0.004, +0.003] | 4/6 | 7.26 | NO EDGE |
| **ZON-017** | **012 ISOLATED (0.5·ADR)** | **574** | **+0.040 [+0.014, +0.066]** | +0.005 [−0.014, +0.024] | 4/6 | **0.37** | **PROMISING** |
| ZON-018 | 012 SHARP (≥2.0 cliff) | 10,346 | +0.001 [−0.007, +0.010] | +0.002 [−0.001, +0.006] | 4/6 | 6.74 | NO EDGE |
| ZON-019 | 012 FRESH∧ISO∧SHARP | 287 | +0.024 [−0.020, +0.068] | −0.000 [−0.027, +0.032] | 2/6 | 0.19 | INSUFFICIENT (N<300) |
| ZON-020 | 013 FRESH∧ISO | 120 | +0.003 [−0.096, +0.106] | +0.008 [−0.036, +0.047] | — | 0.08 | INSUFFICIENT |
| ZON-021 | 012 defended touch-2 | 887 | +0.002 [−0.019, +0.021] | **−0.017 [−0.035, −0.000]** | 1/6 | 0.58 | NO EDGE |

## What Batch 3 established

1. **Isolation materially matters — the strongest location evidence in 21 hypotheses.**
   Isolated ZON-012 boundaries (no other active boundary within 0.5·ADR) beat their own
   neighborhood by **+4.0% of ADR** with a CI comfortably clear of zero — the largest, cleanest
   C1 result of the project (parent ZON-012: +1.0%). Only 3.4% of parent events qualify → a
   naturally sparse stream (0.37/day; 26% of days have exactly one, 5.5% have 2–5, never >5;
   NN spacing 0.18 ADR). Vs matched moments (C2) the uplift is +0.005 and does not clear —
   part of the isolated-boundary effect is context. PROMISING, not STRONG.
2. **Freshness-in-minutes does NOT matter** (ZON-016): 65% of parent events are already ≤60 min
   old; conditioning on it changes nothing vs C2 (−0.000). The parent family is intrinsically
   young (4h lifecycle); age adds no information within it.
3. **Touch-count freshness DOES matter, negatively — degradation is now a tested result, not a
   description** (ZON-021): even after a textbook clean first defense (rejection, <50%
   penetration), second touches run **−1.7% ADR below matched moments** (CI < 0, 5/6 years
   negative, traversal 67%). "Defended zones hold better" is rejected on GC; first touch is the
   only touch with any value.
4. **Formation sharpness does not matter** (ZON-018: flat; threshold kept 62% of zones —
   selectivity was weak by construction, recorded as such). Descriptively (feature table), the
   only formation variable with visible spread is **post-creation departure strength**: weakest-
   departure tercile −0.031 vs +0.006/+0.003 — flagged for future preregistration, NOT tested.
5. **Combinations starve**: FRESH∧ISO∧SHARP = 287 events (just under the floor) — honest
   INSUFFICIENT, point estimates directionally like ZON-017 but unusable. ZON-020 (rescuing
   ZON-013 with quality conditions) also starved (120 events).

## Pre-touch predictor summary (descriptive, post-hoc-labeled; from features_z012.parquet)

Meaningful spread: departure strength after creation (−0.031 → +0.006 across terciles), prior
inside contact (−0.028 vs −0.007, N=204), isolation (tested: +0.04 vs C1), high confluence
(4–5 co-active families: −0.001 vs −0.009 — mild, counterintuitive sign vs crowding).
Flat: age, width, sharpness, formation volume ratio, approach speed/direction, distance travelled
before touch, session. No hypothesis was created from these bins in this batch.

## Lifecycle audit outcome (details in ZONE_LIFECYCLE.md)

No causality bug — primary results of ZON-001…015 stand. But the lifecycle was permissive:
71–95% of raw episodes in long-lived families struck already-broken/mitigated zones (max touch
counts 43–589; age p90 6–12 days); the 94–98% "reclaim" is mechanically near-vacuous for narrow
zones; only ZON-011/012's 4-hour expiry produced sane histories. Strict lifecycle v1 (LIVE zones
only) is now canonical for all future work.

## Frequency accounting

Strong-criterion stream: **0/day**. Strong+promising: **0.37/day** (ZON-017 alone) — below the
2–5/day goal; not forced. Event-set overlaps among 012-hypotheses recorded (016∩018 = 6,917 of
their events; 021 disjoint from all first-touch sets, as required).

## Bottom line

Zone quality on GC is not about formation aesthetics (sharpness, volume, freshness-in-minutes) —
it is about **standing alone** (isolation) and **being untested** (touch 1 only; even defended
zones die by touch 2). The best specification so far: ZON-012 volume-concentration boundary +
isolation + first touch — +4% ADR vs its neighborhood, ~0.4 events/day, but still context-heavy
vs matched moments and below STRONG materiality. Whether this is worth validation, a redesigned
isolation-first hypothesis, or a stop-decision is the user's call.
