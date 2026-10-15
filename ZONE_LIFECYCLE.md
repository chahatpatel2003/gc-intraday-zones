# ZONE LIFECYCLE — canonical state machine v1.0 + audit of ZON-001…015
Frozen 2026-08-16 BEFORE any Batch-3 outcome. Old results are NOT retroactively changed.

## 1. Canonical state machine (all future zone work)

`CREATED → ACTIVE → TOUCHED → MITIGATED → INVALIDATED / EXPIRED`

| State | Entry rule (causal, observable live) |
|---|---|
| CREATED | geometry first exists: all defining bars/windows CLOSED (source candle closes, displacement bar closes, structure break confirms, profile window finishes, pivots causally confirmed). A future reaction can NEVER create or validate a zone. |
| ACTIVE | creation + activation latency (+1s) or family rule (e.g. next session open). Only ACTIVE zones generate tradable interactions. |
| TOUCHED | first edge touch after activation (ZONE_SPEC §3 vocabulary: edge touch / penetration / midpoint / full traversal). Touch does NOT invalidate unless the family says so. |
| MITIGATED | full traversal (depth ≥ 100%). Under strict lifecycle v1 a MITIGATED zone is dead for new interactions. Partial mitigation (≥50% depth) is recorded state, not death, unless the family rule says otherwise. |
| INVALIDATED | family acceptance rule (source-TF close beyond distal), opposite structural break, penetration tolerance, max-touch cap, or **contract roll (always)**. |
| EXPIRED | family age/session limit, or structural-regime end where defined. |
| RECLAIMED | never a reactivation. A broken zone that becomes interesting again must be a NEW zone/version ID with a new causal activation timestamp; requires its own hypothesis. Not used in Batch 3. |

**Strict lifecycle v1 (applies to ZON-016+):** a zone is LIVE only while ACTIVE ∧ not MITIGATED ∧
not INVALIDATED ∧ not EXPIRED. Every conditioned event set in Batch 3 draws only from LIVE zones
(primary events were already touch-1 pre-break; strictness adds death-on-mitigation and the
conditions preregistered per hypothesis). Reporting of density/touched-per-day for Batch 3 uses
LIVE zones only.

## 2. Audit of ZON-001…015 lifecycle (as implemented; results untouched)

**What was correct:** activation fully causal everywhere (creation-close +1s or next-session open;
truncation-parity tested twice). Invalidation existed (source-TF acceptance / full mitigation) and
retests were stratified out of primary stats. Reclaim never reactivated anything (measurement
only, no state change → no backdating). Primary results (touch-1, pre-break, deduped) are
therefore CLEAN and stand.

**What was permissive (measured from cached episode tables):**

| Fam | episodes | % post-break (retest) | % touch ≥3 | age p90 at touch (min) | max touch # |
|---|---|---|---|---|---|
| 001 | 10,273 | 27% | 60% | 1,145 | 43 |
| 002/015 | 969,483 | **95%** | 97% | 9,160 | **503** |
| 003 | 37,037 | 66% | 81% | 1,122 | 58 |
| 006 | 34,468 | 42% | 73% | 10,820 | 174 |
| 007 | 13,157 | 80% | 95% | 9,367 | 219 |
| 008 | 89,561 | 77% | 95% | 9,361 | 318 |
| 009 | 209,843 | 71% | 94% | 17,458 | 214 |
| 013 | 121,686 | 71% | 93% | 9,421 | 243 |
| 014 | 98,968 | **95%** | 98% | 16,506 | **589** |
| 011 | 33,408 | 19% | 60% | **219** | 39 |
| 012 | 72,437 | 25% | 58% | **220** | 42 |

Findings:
1. **Zombie zones**: zones stayed countable until fixed expiry (5–15 sessions) even after break/
   mitigation → 71–95% of raw episodes in long-lived families hit already-dead structure. This
   inflated active-zone density, touched/day and self-overlap (60–85% overlapping pairs), and
   produced hundreds of repeated weak interactions per zone (max touch 43–589).
2. **Reclaim 94–98% is mechanically near-vacuous**: re-entering a 0.03–0.2·ADR strip within 120
   trading minutes of traversing it is close to certain for narrow zones in mean-reverting 1m
   noise. It measured noise, not zone magnetism.
3. **Expiry did the killing that invalidation should have done**; only ZON-011/012 (240-trading-
   minute expiry) had tight lifecycles — retest 19–25%, age p90 ≈ 3.7h, max touch ≈ 40 — and
   ZON-012 is also the only PROMISING family (correlation noted descriptively, not claimed causal).
4. No material causality/leakage bug found → Batch 3 may proceed. The permissiveness affected
   DENSITY/liveness accounting and raw episode counts, not the preregistered primary comparisons.

## 3. Family lifecycle table (as-implemented, for the record)

001/003/010: active one session; acceptance = 30m close beyond distal; expiry = session end.
002/015: mitigation = full traversal kills tradability (stratum-wise), expiry 5 sessions.
005: no invalidation (grid), daily re-instantiation. 006: 1h acceptance, 15 sessions, causal
widen-only mutation. 007/013: 15m acceptance, 5 sessions. 008: 30m acceptance, 5 sessions.
009: 1h close back through zone, 10 sessions. 011: 30m acceptance, 240 trading min.
012: 1h acceptance, 240 trading min. 014: traversal, 10 sessions. Rolls: all structural zones die
at `instrument_id` change (loader walls); grid zones flagged.
