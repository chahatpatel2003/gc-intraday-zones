# ZONE-LOCATION EVALUATION FRAMEWORK v1.2
Locked 2026-08-16, corrections applied BEFORE any Batch-1 run; §3-C1v2 added and frozen BEFORE any
Batch-2 outcome was calculated (changelog at end).
Phase question: **is the zone's LOCATION special, beyond market timing/context?**
No entries, confirmations, TP/SL, RR, sizing, strategies, or ML in this phase.

## 1. The estimand

Per family: the difference in the preregistered excursion PROFILE (ZONE_SPEC §4) between real-zone
episodes and matched control episodes sharing the moment's context but not the location. Timing/
context cancels in the comparison; what survives is location information. **Never reduced to one
binary win-rate.**

## 2. Unit of analysis, strata, independence

- Unit = **episode** (ZONE_SPEC §3). **Primary stratum** = first touches (touch_index = 1,
  defined approach side, pre-break/pre-mitigation), after within-family dedup (§5).
- Touch 2 / 3+ and post-break retests: separate strata (degradation), never pooled.
- Inference: **day-block bootstrap** (resample trade_dates with replacement, 1,000 reps, 95% CI,
  rng seed 20260816). Episodes within a session are never treated as independent.

## 3. Controls (both mandatory)

**C1 — Displaced shadow zones.** Per real zone: four shadows with **identical width**, identical
creation/activation/expiry timestamps, same contract segment, and carried type/side, at midpoint
offsets **+2W, +4W, −2W, −4W**. Validity requirements (violations ⇒ that shadow is marked
`unavailable`, never forced): no overlap with the parent zone (guaranteed by construction, gap ≥ W);
no overlap with ANY other same-family real zone whose lifetime overlaps; comparable
distance-from-price regime (offsets are ≤ 0.4·ADR-scale by construction; a shadow landing outside
the day's plausible range simply never gets touched and drops out). Shadows run through the
identical episode engine; comparison uses their first-touch episodes, deduped like real ones.

**C1v2 — Nearest-eligible non-zone strips (Batch 2+; frozen 2026-08-16 before any Batch-2
outcome).** Batch 1 showed fixed ±2W/±4W shadows starve for dense families (94% unavailable for
FVG) and the survivors are a selected sample. Replacement, used for ALL Batch-2 families:
per real zone, candidate strips share its width, creation/activation/expiry, segment, and carried
type; candidate midpoints follow the outward ladder k ∈ {2,3,4,5,6,8,10,12} (order +2,−2,+3,−3,…,
i.e. nearest first, alternating sides). A candidate is ELIGIBLE iff it overlaps no active real zone
of the SAME family, and its midpoint offset satisfies |k·W| ≤ 1.0·ADR14 (creation day) to stay in
the same distance-from-price regime. *(v1.3 amendment, made from availability DIAGNOSTICS only,
before any Batch-2 outcome was viewed: the originally frozen union-blob exclusion — no overlap
with ANY Batch-2 family's zones — left 0.12–1.33 shadows/zone and gave most zones zero control
(one family: zero C1 episodes), because the rolling ZON-011/012 universes blanket nearby price
space. A control that cannot exist is not a control. Same-family exclusion restores the intended
question — "this exact area vs comparable nearby areas not tagged by THIS hypothesis" — and does
not treat other UNVALIDATED families' zones as established structure. The union-variant smoke
outputs were deleted unread.)* Up to the nearest TWO eligible strips per side
(max 4) are taken; if none exists within the ladder the zone contributes no C1 control (counted —
never forced). Diagnostics reported: ladder-distance distribution, zones-without-control rate.
The method was designed from Batch-1 control DIAGNOSTICS only (availability rates), not from any
Batch-2 outcome, and is frozen before Batch-2 outcome computation. Batch-1 C1 results are not
restated under this method; no cross-batch C1 comparability is claimed.

**C2 — Moment-matched pseudo-zones.** For each real primary episode, K=5 donor moments are sampled
(different trade_date) from the same preregistered context cell:
**session bucket (4) × ADR14 tercile (3) × approach direction (2) × approach-speed quartile (4)**,
where approach direction/speed use the signed 5-bar (5-trading-minute) log return into the moment.
The pseudo-zone is fully specified: **width = the real zone's W; proximal edge P₀ = the donor bar's
close (distance from current price = 0, exactly as at a real touch); side = ahead of the donor's
direction of travel** (rising ⇒ area above, falling ⇒ area below), i.e. a genuinely comparable
alternative price area being reached at a comparable moment — not merely a similar timestamp.
Donor moments whose pseudo-zone overlaps any same-family real zone alive at that time are rejected
and resampled (the control must be a non-zone area). Outcomes measured with the identical FE/AE
conventions.

## 4. Decision rule & classification (preregistered)

Primary quantity: **Δ mean NetFav60/ADR14 = mean[(FE₆₀ − AE₆₀)/ADR14]**, real minus control:
vs C1 (unpaired difference, independent day-block bootstrap of each side) and vs C2 (paired per
event: real − mean of its donors; day-block bootstrap over real days). Materiality floor
**+0.05 ADR14**. Secondary (reported, non-gating): ΔFE₆₀/ADR, ΔAE₆₀/ADR, ΔR_ADR, ΔR_W,
Δtraversal, depth, reclaim, full horizon curves 5→120m in both unit systems.

Yearly stability: sign of the primary Δ vs C2 per calendar year (years with ≥30 primary episodes).

| Classification | Rule (N = primary episodes) |
|---|---|
| **STRONG LOCATION EVIDENCE** | N ≥ 300 AND primary Δ 95% CI > 0 vs **both** C1 and C2 AND Δ ≥ +0.05 ADR vs both AND ≥80% of usable years positive vs C2 |
| **PROMISING** | N ≥ 300 AND ≥60% usable years positive AND [CI > 0 vs both but materiality unmet] OR [CI > 0 vs one control AND point Δ > 0 vs the other] |
| **NO LOCATION EDGE** | N ≥ 300 and neither of the above (frequent raw reactions do NOT rescue a family that fails its controls) |
| **INSUFFICIENT DATA** | N < 300 (never "extend until significant") |

Multiplicity: 6 preregistered family primaries; α=5% ⇒ ~0.3 false passes expected; every discovery
PASS is provisional until the same frozen spec repeats on validation (2022–2023, user-gated).
Session/year/vol subgroups are descriptive only — selecting on them = new post-hoc hypothesis ID.

## 5. Two-layer dedup & the interaction-cluster architecture (user correction #4)

**Layer 1 — family evaluation (attribution).** Every family keeps its own zones and episodes so
families can be compared; a physical price area may legitimately carry several family tags.
Within one family: co-occurring episodes (first-touch bars ≤ 30 trading minutes apart AND zone
intervals overlapping ≥ 1 tick) collapse to ONE independent family event (representative = earliest-
activated zone; members logged). All family statistics and control comparisons use these deduped
events.

**Layer 2 — independent opportunity count (`interaction_cluster_id`).** Across ALL families:
deduped episodes whose touch bars are ≤ 30 trading minutes apart AND whose zone intervals overlap
are union-found into one **physical market interaction** with a single `interaction_cluster_id`;
contributing families/timeframes/zone ids stored as metadata. **Mandatory basis for:**
opportunities/day, density, independent reaction counts, and all later trading analysis. Overlapping
zones never inflate sample sizes; confluence (≥2 families in a cluster) is recorded information,
analyzed later as its own hypothesis, never double-counted.

## 6. Outputs per family (fixed report card)

Density table (ZONE_SPEC §5 on Layer-2 clusters + per-family) · episode tables (parquet, seeded,
reproducible) · full metric profile vs C1/C2 with CIs · ambiguity/truncation/coverage counts ·
yearly stability table · classification per §4 · ledger row updated (result_summary, verdict).

## 7. Out of scope this phase

Entry triggers, confirmations, sub-5m execution, TP/SL, RR, costs, sizing, ML, news optimization.

## 8. Operational addendum (fixed before Batch-1 run)

Approach side = last strictly-outside bar within 30 bars before T₀ (same segment; possibly
pre-activation history); no such bar ⇒ `inside_at_activation`, excluded from metrics, counted, and
recorded with touch_index 0 — a non-classifiable contact does NOT consume a touch index, so the
first genuine sided approach is always touch_index 1. (Operational clarification recorded
2026-08-16 after a smoke run exposed only event COUNTS — no outcome deltas, comparisons, or
classifications were viewed before this clarification.)
Episode end = first of R_W · traversal · ≥5 consecutive bars fully ≥1.0·W beyond P₀ on the approach
side · zone expiry/segment end · 480-bar cap. Excursion paths extend past zone expiry (price
behavior is the measurand) but never past a segment (roll) boundary. Zones whose creation pattern
would span a roll are not created; zones whose activation lands on a different contract than their
geometry are dropped as roll-killed (counted). Sessions without a defined ADR14 (first 14 sessions
of the sample) generate no zones/donors. Break/retest uses each family's registered acceptance rule
(30m/1h source-TF close beyond distal; FVG: full mitigation; round grid: none — untyped zones
break relative to the first episode's approach side).

*Changelog:* v1.3 (2026-08-16, before any Batch-2 outcome was viewed): C1v2 eligibility amended
from union-blob exclusion to SAME-FAMILY exclusion after the union variant starved (diagnostics
in §3; smoke outputs deleted unread). v1.2 (2026-08-16, before any Batch-2 outcome): C1v2 nearest-eligible-strip control
added for Batch 2+; C2 unchanged; Batch-2 primary metric = NetFav60/ADR for ZON-007…014
(location-of-reaction framing) and CONTINUATION NetAdv60/ADR = (AE₆₀−FE₆₀)/ADR for ZON-015 only
(Batch-1-inspired exploratory; same CI/materiality/stability/N thresholds applied to that metric).
v1.0 initial. v1.1 (2026-08-16, pre-run, user corrections): primary metric changed
from binary M1 uplift to the NetFav60/ADR excursion profile with dual unit systems; C1 validity/
unavailability rules made explicit; C2 pseudo-zone fully specified (center/width/side/distance/
direction/session/vol/speed); two-layer dedup with mandatory cross-family `interaction_cluster_id`;
classification table preregistered; operational addendum locked.
