# BATCH 7 — PATTERN-MINING PLAN (frozen BEFORE mining)
Frozen 2026-08-16. Internal split: **2016–2019 mining · 2020–2021 untouched-within-branch
confirmation** (loader-enforced; 2020–2021 opened only after ZON-035…040 are frozen; 2022+ never).
ZON-028 is skipped entirely (frozen, not validated, not screened, near-clones barred from
selection). Closed families receive no new hypotheses; mechanism CLASSES from the user's motif
list may be searched with genuinely different constructions.

## Search space (every screened motif counts toward researcher degrees of freedom)

16 motif templates, ONE frozen parameterization each (constants below are final — no sweeps).
Common: both directions mirrored; zone floor 0.05·ADR / cap 0.5·ADR; activation = confirm close
+1s; invalidation = source-TF close beyond distal; expiry 5 sessions (session-scoped motifs:
session end); strict lifecycle; max touches 1; roll death; med20 = trailing 20-bar median range
(shifted); volmed20 likewise for volume.

| ID | TF | Sequence (causal) | Zone | Frame |
|---|---|---|---|---|
| M01 OR-trap | 15m | opening range = first 4 bars of session; later close beyond OR edge, close back inside within 3 bars | [OR edge, excursion extreme] | rejection, session life |
| M02 session-high trap | 15m | running session extreme set ≥8 bars ago; close beyond, back inside within 3 bars | overshoot pocket | rejection, session life |
| M03 1-session trap | 30m | prior-session extreme trap (SCREEN-ONLY: ZON-028 near-clone, barred from selection) | overshoot pocket | rejection |
| M04 VWAP-band trap | 15m | session VWAP±2σ (causal); close beyond band, close back within 3 bars | [band level at breach, excursion extreme] | rejection, session life |
| M05 double-attack | 15m | two probe bars (upper wick ≥0.3·range), 4–32 bars apart, highs within 0.05·ADR, no intervening close above | [min, max] of probe highs | rejection |
| M06 exhaustion reversal | 15m | ≥4 consecutive same-direction closes; final bar range ≥2×med20; next bar opposite body ≥0.7·range and range ≥1×med20 | outer half of exhaustion bar | rejection |
| M07 volume climax | 30m | new 20-bar high AND vol ≥3×volmed20 AND close location ≤0.5 | upper half of climax bar | rejection |
| M08 impulse→pullback base | 15m | displacement (≥2.5×med20, body ≥0.7); 2–4 bar base (each ≤1×med20) above displacement open; base-break close confirms | base [min low, max high] | rejection (with-trend) |
| M09 NR7 release | 30m | narrowest range of last 7; next bar closes beyond NR range with range ≥1.5×med20 | NR bar range | rejection (with release) |
| M10 balance-break return | 30m | 6-bar balance span ≤0.35·ADR; breakout close beyond with range ≥1.5×med20 | full balance range | **CONTINUATION** (re-entry traverses); invalidation = 30m close ≥0.25·ADR outside proximal side |
| M11 three declining probes | 15m | 3 successive higher highs, each ≤0.15·ADR above prior, ranges r1>r2>r3; confirm = next close < probe-3 high | [probe-2 high, probe-3 high] | rejection |
| M12 NY-open fade | 15m | first bar ≥08:20 ET with range ≥2×med20; next 2 bars retrace ≥60% | outer half of displacement bar | rejection, session life |
| M13 VWAP whipsaw | 30m | ≥3 closes one side of session VWAP, close across, close back within 2 bars | whipsaw extreme pocket [VWAP-cross extreme, band...] = [far extreme, re-cross close] | rejection, session life |
| M14 high-volume base | 30m | 2–3 bar base (each ≤1×med20) with total vol ≥2×(volmed20×n); displacement away ≥2×med20 | base range | rejection |
| M15 RSI-divergence probe | 15m | new 20-bar high with RSI-14 < RSI at prior 20-bar high; close back below prior high | [prior high, new high] | rejection (indicator-bearing base; RSI-14 Wilder, frozen) |
| M16 trend-pullback | 30m | EMA20>EMA50 (both rising, 30m closes, conventional spans); ≥5 bars above EMA20; first close within 0.10·ADR of EMA20 while still ≥0.10·ADR above zone top | snapshot [EMA20−0.05·ADR, EMA20+0.05·ADR] | rejection (indicator-defined location) |

## Indicator overlays (Stage A2)
After base screening, the top 5 bases (by the frozen rank) each get exactly ONE mechanically
matched overlay — conventional settings frozen now: trend filter EMA20>EMA50(30m) for trap/
reversal bases; RSI-14 >70/<30 at completion for exhaustion/probe bases; volume z-score(20) ≥2 for
volume/trap bases; ADX-14 <20 for the continuation base. Overlay survives into a frozen candidate
only if its incremental Δ (both controls, mining window) ≥ **+0.02 ADR** vs the same base without
it; otherwise the base ships alone. Zone-alone vs zone+indicator is always reported.

## Screening measurement (2016–2019 only)
Full standard machinery per motif: strict lifecycle, first touch, within-family dedup, C1v2
(nearest-eligible strips) and C2 (96-cell matched moments), Δ mean NetFav60/ADR (continuation
motifs: Δ mean NetAdv60/ADR), day-block bootstrap seed 20260816.

## Frozen selection rule (applied mechanically to the mining log)
Eligible: support ≥ 0.5 events/day OR min(ΔC1, ΔC2) ≥ +0.05 (exceptional-rarity clause); M03
excluded; control health required (shadows/zone ≥ 2.0, uncontrolled ≤ 20%). Rank by
min(ΔC1, ΔC2) on the motif's own frame metric. Deduplicate: if two eligible motifs' event sets
overlap (Jaccard on (day, cluster) keys > 0.4), keep the better-ranked. Select top ≤ 6 →
ZON-035…040. Freeze specs + ledger BEFORE any 2020–2021 access. Stage B tests (truncation/
streaming parity, leakage, roll, indicator timing, control health) must pass before Stage C.

## XAUUSD constraint (recorded now)
Dukascopy XAUUSD begins 2021-06-29 — the mining window (2016–2019) contains ZERO overlap, so no
cross-market candidate can be mined in this branch; at most it could be evaluated on ~6 months of
2021, which fails every support requirement. **No XAUUSD candidate in Batch 7** (item preregistered
as infeasible, not skipped silently).

## Degrees-of-freedom accounting
DoF = 16 motif templates + ≤5 overlay combos + 1 frozen selection rule + 0 threshold variants
(all constants single-valued). Mining log records every screened item with its results.
