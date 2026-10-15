# ZONE SPECIFICATION — canonical definitions v1.1
Locked 2026-08-16 (v1.1 corrections applied BEFORE any Batch-1 run; changelog at end).
Every experiment uses THESE definitions. Changing any constant or definition creates a new spec
version and new ledger IDs; nothing here may be re-chosen after seeing results.

## 1. What a zone is

A zone is a **price interval, not a line**: `[zone_low, zone_high]` with `zone_low < zone_high`,
attached to one instrument and one contract segment. Point-based concepts (a prior high, a round
number, a POC) become zones only through their family's preregistered width rule.

**Canonical zone record (all fields mandatory):**

| Field | Meaning |
|---|---|
| `zone_id` | deterministic id (family + creation ts + segment) |
| `family`, `spec_version` | ledger family and the frozen spec that built it |
| `instrument`, `roll_segment` | GC + `instrument_id`; zones never span segments |
| `source_tf` | timeframe of the completed bars that built it (≥ 5m) |
| `ztype` | family-specific type (e.g. supply/demand, PDH/PDL, VAH/VAL/POC, round) |
| `side_rule` | how expected-reaction side is determined (fixed by type, or by approach side) |
| `zone_high, zone_low` | boundaries fixed at creation from completed bars only |
| `zone_mid` | (high+low)/2 |
| `width_W` | high − low; also stored in ADR14 units (`W_adr`) |
| `width_rule` | the family's preregistered width definition (see ledger) |
| `created_ts` | close time of the bar that completes the defining pattern |
| `activation_ts` | created_ts + 1s processing latency (or family rule, e.g. "next session open") — zone is observable/testable only from here |
| `expiry_ts / expiry_rule` | preregistered lifetime; expired zones stop generating events |
| `invalidation_rule` | the live-observable event that kills the zone (e.g. acceptance beyond distal edge) |
| `mutation_policy` | `immutable` (default) or the family's causal mutation rule; any mutation creates a new `zone_version` at its own observable timestamp — old episodes keep the geometry that existed when they happened |
| `provenance` | ids/timestamps of source bars (audit trail) |
| `status` | pending → active → (touched…) → broken / reclaimed / expired — transitions only at observable times |

**Causality invariants (protocol §B):** boundaries and status may never be backdated or adjusted
using information after the fact; a historical zone must be byte-identical to what a live process
running on streaming data would have produced (parity harness required before results are trusted).
Zones may not be created from bars that span a roll, from the artificial roll gap itself, or from
bars flagged `after_gap` where the family's pattern depends on continuity.

## 2. Geometry conventions

For an interaction, the **approach side** is where price came from (last trade strictly outside the
zone before contact). The **proximal edge** is the boundary on the approach side; the **distal
edge** is the other one. `depth(t)` = max penetration beyond the proximal edge so far, as % of W
(0% = touched edge only, 100% = reached distal edge). All path logic runs on GC 1-minute bars
(finest owned); within one 1m bar the order of extremes is unknowable → every event carries an
`ambiguous` flag when its defining crossings could have occurred in either order inside one bar,
and ambiguous shares are reported in all outputs.

## 3. Canonical interaction definitions (fixed vocabulary)

Let the zone be active, W its width, T₀ the first contact bar.

| Term | Definition |
|---|---|
| **Edge touch** | a 1m bar trades at or beyond the proximal edge (bar range includes it) |
| **First touch** | first edge touch after `activation_ts` (touch_index = 1) |
| **Entry into zone** | a trade strictly inside (zone_low, zone_high) |
| **Midpoint penetration** | depth ≥ 50% (trades at/beyond zone_mid) |
| **Full traversal** | depth = 100% (trades at/beyond the distal edge) |
| **Partial mitigation** | episode max depth in [50%, 100%) |
| **Full mitigation** | episode reached depth 100% at least once |
| **Rejection** | within `T_r` of T₀, price moves ≥ `r·W` away from the proximal edge on the approach side, **before** any full traversal. Constants: r = 1.0; T_r reported at both 30m and 120m (both preregistered, both always reported) |
| **Acceptance (through zone)** | first source-TF bar **close** beyond the distal edge |
| **Break** | = acceptance; zone status → broken (wick-through without close = traversal, not break) |
| **Reclaim** | after a break and before expiry: a source-TF close back on the original side |
| **Retest** | first edge touch after a break, approaching from the opposite side (polarity-flip test; its own stratum, never pooled with pre-break touches) |
| **Repeated touch** | touch_index ≥ 2, using episode separation below |
| **Time inside** | minutes with any trade inside the zone during the episode |

**Episode separation (dedup of consecutive bars):** an episode starts at an edge touch and ends at
the earliest of: rejection achieved · full traversal · price staying ≥ 1.0·W beyond… i.e. remaining
at least 1.0·W away from the proximal edge (on the approach side) for ≥ 5 consecutive minutes ·
zone expiry/invalidation. The next contact after an episode ends is a new touch_index. One episode
= one row; bars inside an episode are never counted as separate interactions.

## 3b. Point→zone conversion rule (width fairness; user correction #3)

Naturally **interval-based** concepts use their **structural boundaries** (FVG span, supply/demand
base span, profile-derived intervals). Naturally **point-based** references (PDH/PDL, POC, VAH/VAL,
round numbers, pivot prices) are converted to zones by a **documented symmetric volatility-scaled
half-width — an explicit modelling ASSUMPTION, not a claim of correctness**:
±0.10·ADR14 for session extremes (wick extremes are noisy), ±0.05·ADR14 for sharp references
(POC/VAH/VAL/round numbers) and as the minimum-width floor for pivot clusters. One width rule per
family in Batch 1; no width variations are tested; any different width rule is a NEW hypothesis ID
later. ADR14 is the loader's roll-safe average session range, known at session open. ZON-005
special case: the grid is re-instantiated per trade_date (daily causal re-width; touch_index counts
within the day; "active" for density = levels within 1.0·ADR14 of the prior session close).

## 4. Preregistered reaction measurements (per episode) — v1.1 (width-bias corrected)

**Every excursion is measured in BOTH unit systems** so zone width never defines success on its own:
absolute/volatility-normalized (GC **points**, **ticks** = pts/0.1, **/ADR14**) AND zone-relative
(**/W**). Fixed horizons h ∈ {**5, 15, 30, 60, 120**} **trading minutes** (bars of the same contract
segment after T₀; horizons truncated by a roll are NaN and counted, never extrapolated). No
unlimited horizon anywhere; horizons are never re-optimized.

Measurement conventions (identical for real zones and all controls): P₀ = proximal edge
(pseudo-zones: the donor price). **FE_h** = max favorable excursion beyond P₀ away from the zone,
over bars T₀+1…T₀+h (the touch bar's own extremes never credit the reaction).
**AE_h** = max adverse penetration beyond P₀ toward/through the zone over bars T₀…T₀+h (the touch
bar's penetration is real). Depth = AE/W.

- **M1a** rejection **R_W**: FE ≥ 1.0·W within 120m before traversal (zone-relative)
- **M1b** rejection **R_ADR**: FE ≥ 0.25·ADR14 within 120m before traversal (width-independent)
- **M2** FE_h and AE_h at all five horizons, each in points / ticks / ADR14 / W units;
  and **NetFav_h = FE_h − AE_h** (points and /ADR14) — the primary comparison quantity at h=60
- **M3** max penetration depth (%W) within 120m
- **M4** time-to-resolution (first of R_W / traversal / episode end)
- **M5** P(full traversal, depth ≥ 100%, within 120m)
- **M6** reclaim: P(price re-enters [L,H] within 120 trading min after a full traversal)
- **M7** time inside zone (minutes); reaction speed = trading minutes to reach R_ADR (achievers)

If rejection and traversal complete in the same 1m bar, the episode counts as NOT rejected
(worst case) and sets the `ambiguous` flag. **No single binary win-rate defines success**; the
family question is whether the real zone's excursion PROFILE beats matched controls
(EVALUATION_FRAMEWORK §4).

Strata recorded on every row (analysis slices, never selection filters): touch_index (1, 2, 3+),
retest-after-break flag, session bucket (ASIA/LONDON/NY/LATE), ADR14 tercile (within phase),
zone age at touch (in source-TF bars), prior-touch count, approach speed (5m return into T₀,
quartile), `ambiguous` flag, `roll_session` / `after_gap` coverage flags, news bucket (once a
calendar exists; "unknown" until then). **No unlimited-horizon "eventual reaction" anywhere.**

## 5. Density & opportunity accounting (reported for every family, always)

- zones created/day; active zones at session open and per session bucket
- zones touched/day; **independent episodes/day** (after §EVAL dedup)
- distance of active zones from price (in ADR14 units), spacing between adjacent active zones
- overcrowding: fraction of the ±0.5·ADR14 band around price covered by active zones (median/p90)
- share of sessions with 0, 1, 2–5, >5 independent interactions (the 2–5/day question is answered
  by this table, not forced)

*Changelog:* v1.0 initial. v1.1 (2026-08-16, pre-run): §3b point→zone conversion rule made explicit;
§4 rewritten — dual unit systems (absolute/ADR + zone-relative), horizons fixed at 5/15/30/60/120
trading min, R_W + R_ADR dual rejection definitions, T₀-bar FE/AE conventions, reclaim = re-entry
after traversal, primary = excursion profile vs controls (no single binary); ZON-005 daily
re-instantiation defined.
