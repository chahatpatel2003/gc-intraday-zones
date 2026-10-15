# BATCH 4 — ATTRIBUTION SPECS (ZON-022…025)
Frozen 2026-08-16 BEFORE any Batch-4 outcome. Max 4 hypotheses. Discovery 2016–2021 only.
Question: **is there a genuinely special price zone after controlling for isolation/context, or
are we mainly detecting good market moments?**

## Frozen lifecycle (all four; user §1/§4 — never loosened for frequency)

| Property | Rule (ZON-012 parent; ZON-025 pool families use their parent equivalents) |
|---|---|
| Creation | rolling-6h volume-VA edge at completed hourly snapshot (parent rule, unchanged geometry) |
| Activation | creation close +1s; valid because formation window is fully closed and level is ≥0.05·ADR from price |
| Stays valid | ACTIVE ∧ not mitigated ∧ not invalidated ∧ not expired ∧ same contract (LIVE, strict lifecycle v1) |
| First touch | first sided edge touch after activation (ZONE_SPEC §3); inside-at-activation contacts consume no index |
| Mitigation | full traversal (depth ≥100%) → dead |
| Invalidation | 1h close beyond distal (approach-relative) → dead; contract roll → dead |
| Expiration | 240 trading minutes (parent) |
| Max tradable touch count | **1** (all Batch-4 hypotheses) |
| Reclaim | **not allowed** (would require a new zone/version ID + new hypothesis) |
| Boundaries | immutable; no future reaction affects validity; no backdating |

Frozen condition definitions:
- **ISOLATED** (unchanged from Batch 3): at touch, no other ACTIVE same-parent-family zone midpoint
  within 0.5·ADR14(day); self/parent excluded; applied symmetrically to C1 shadows.
- **STRONG DEPARTURE** (new, leak-free): dep = max |1m close − zone midpoint| over bars
  [activation … min(activation+60 bars, T0 − 1)], same segment, normalized by ADR14 of the zone's
  creation day; STRONG iff dep ≥ **0.15·ADR14**. Window NEVER includes the touch bar (the Batch-3
  descriptive feature used act…act+60 regardless of T0; the hypothesis version is strictly
  pre-touch). Threshold provenance disclosed: chosen after seeing Batch-3 descriptive terciles
  (split ≈0.14) → ZON-023/024 are **discovery-inspired**; single threshold, no sweep.

## C2v2 — strengthened matched-moment control (frozen; used by ZON-022/023/024)

C2 upgraded so donors match the isolation variables themselves. A donor moment must satisfy ALL of:
session bucket, ADR14 tercile, approach direction, approach-speed quartile (the existing 96 cells);
pseudo-zone width = real W; side ahead of travel; proximal edge = donor close (distance from price
= 0, as at the real touch; first-touch-like: the pseudo-area is by construction untouched);
pseudo-zone overlaps no active parent-family zone (existing); **NEW: the donor's pseudo-zone
isolation state (no active parent-family zone midpoint within 0.5·ADR of the pseudo midpoint)
must EQUAL the real event's isolation state**; donor trade_date ≠ event trade_date. K=5, up to 125
tries, shortfalls counted. Seed 20260816.

## The four hypotheses

**ZON-022 — Isolated ZON-012 boundary vs isolated non-ZON-012 area (THE attribution test).**
Event set = isolated first-touch ZON-012 events (deterministic regeneration of the ZON-017 set;
ZON-017 itself untouched). Primary: Δ mean NetFav60/ADR14 vs **C2v2** (paired) — the isolated
matched-moment null. Secondary: vs C1v2 (isolated shadows, replicates the +0.040 reference).
Reading: if Δ vs C2v2 ≈ 0, ZON-017 was mainly isolation/context; if it stays materially positive,
the boundary itself carries information.

**ZON-023 — Strong-departure ZON-012 (discovery-inspired; formalizes the descriptive flag).**
Event set = first-touch ZON-012 events with STRONG DEPARTURE. Controls: C1v2 shadows with the
identical departure condition applied to the shadow's own geometry/first touch; C2v2 with
isolation-state matching (each event's own state). Primary: Δ NetFav60/ADR vs both.

**ZON-024 — ISOLATED ∧ STRONG DEPARTURE ZON-012.** The single preregistered combination.
Expected sparse; reported honestly (no other filters).

**ZON-025 — Isolation as a general context feature (attribution across families; NOT a tradable
family claim).** Preregistered pool = previously defined families with parent primary N ≥ 1,500,
geometry unchanged: ZON-001 (prior extremes), ZON-008 (rejection tails), ZON-009 (role reversal),
ZON-011 (VWAP bands), ZON-013 (compression origins), ZON-015-universe (15m FVG). Strict lifecycle,
first touch only, frozen isolation definition per family. Deliverable per family (tags retained):
N_iso / N_non-iso; Δ(iso − non-iso) NetFav60/ADR with day-block bootstrap CI; iso-subset vs its own
C1v2 (isolated shadows). Attribution reading: isolation helping ~everything ⇒ context feature;
isolation helping specifically volume boundaries ⇒ family-specific location structure.

Success standard (user §6): CI>0 vs BOTH controls AND useful magnitude AND stable yearly sign AND
low ambiguity AND no dead-zone dependence — statistical significance alone insufficient. No
execution research. Frequency is never manufactured.
