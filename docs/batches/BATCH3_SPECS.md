# BATCH 3 — ZONE QUALITY / LIFECYCLE SPECS (ZON-016…021)
Frozen 2026-08-16 BEFORE any Batch-3 outcome computation. Max 6 hypotheses (budget respected).
Parents are NOT modified or rerun as hypotheses; parent universes are regenerated deterministically
(parity-tested identical) and conditioned. All conditions use ONLY pre-touch information.
Machinery: strict lifecycle v1 (ZONE_LIFECYCLE.md) · standard episode engine · C1v2 shadows
(same-parent-family exclusion; event-level conditions applied SYMMETRICALLY to shadow episodes) ·
C2 moment-matched (unchanged) · primary Δ mean NetFav60/ADR14 · classification thresholds
unchanged (EVALUATION_FRAMEWORK v1.3) · seed 20260816 · discovery 2016–2021 only.

Frozen quality conditions (used by the hypotheses below; one rule each, no sweeps):
- **FRESH**: zone age at touch ≤ 60 wall-minutes since activation AND the zone had no
  inside-at-activation contact before the touch. (ZON-020 uses ≤ 120 min for the slower 5m-box
  family — fixed a priori.)
- **ISOLATED**: at touch time, no other ACTIVE same-parent-family zone has |midpoint − midpoint|
  < 0.5·ADR14(day). Applied identically to C1 shadows (shadow midpoint vs real active zones).
- **SHARP (ZON-012 boundary prominence)**: at formation, mean volume/tick in the 0.10·ADR band
  just INSIDE the VA edge ≥ 2.0 × mean volume/tick in the 0.10·ADR band just OUTSIDE it
  (computed on the formation histogram only — a steep acceptance cliff).
- **CLEAN PRIOR DEFENSE (touch-2 condition)**: the zone's first episode achieved rejection R_W
  AND its max penetration depth stayed < 50% of W. Episode-1 resolution precedes touch 2 by
  construction (episode separation), so the condition is fully causal at touch 2.

| ID | Parent | Event set (all: pre-break, LIVE zones, within-family deduped) | Mechanism |
|---|---|---|---|
| **ZON-016** | ZON-012 | first touches, FRESH | freshness: young, untested boundaries |
| **ZON-017** | ZON-012 | first touches, ISOLATED | isolation: boundary not inside a cluster |
| **ZON-018** | ZON-012 (zones filtered to SHARP) | first touches of SHARP zones | formation quality: steep volume cliff = well-defined acceptance edge |
| **ZON-019** | ZON-012 | first touches, FRESH ∧ ISOLATED ∧ SHARP | preregistered combination — the "materially stronger ZON-012" candidate; flagged as a combination (its multiplicity is declared, not post-hoc) |
| **ZON-020** | ZON-013 | first touches, FRESH(≤120m) ∧ ISOLATED | does lifecycle quality rescue the compression-origin family that beat C2 6/6 but not C1 |
| **ZON-021** | ZON-012 | SECOND touches after CLEAN PRIOR DEFENSE | explicit freshness/degradation hypothesis: does a cleanly-defended boundary retain value at touch 2, or is degradation universal |

Controls detail: C1v2 shadows are generated from the parent universe once and reused; for ZON-018/
019 shadows attach to SHARP zones only; FRESH/ISOLATED filters are applied to shadow first-touch
episodes with the identical rules (shadow age; shadow midpoint vs active REAL zones); for ZON-021
shadow second-touch episodes require the shadow's own episode-1 CLEAN PRIOR DEFENSE. C2 donors are
drawn per conditioned event with the standard context cells (freshness/isolation are not in the
cell — C2 remains the pure matched-moment null; documented limitation).

Also produced (NOT hypotheses — descriptive, post-hoc-labeled): a preregistered CAUSAL FEATURE
TABLE per ZON-012/ZON-013 primary event — age, width/ADR, prior touches, prior max depth,
departure strength & cleanliness after creation, distance travelled before touch, formation volume
ratio, SHARP prominence value, approach speed/direction, isolation distance, cross-family
confluence count (Batch-2 universes), session, ADR tercile — with binned outcome means reported
for future hypothesis design. No Batch-3 hypothesis was constructed from this table's outcomes
(the six above were frozen first, motivated only by already-published Batch-1/2 observations).

Success emphasis (user §9): report Δ vs both controls AND materiality vs the +0.05·ADR STRONG bar,
events/day, spacing/isolation of the conditioned stream, yearly stability. Frequency target 2–5/day
is reported, never forced.
