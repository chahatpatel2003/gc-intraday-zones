# BATCH 2 — FROZEN SPECIFICATIONS (ZON-007…015)
Frozen 2026-08-16 BEFORE any outcome computation. One spec per family, no parameter sweeps.
Common rules: discovery 2016–2021 GC only · zones not lines · source TF ≥ 5m · roll-segment
walls (no structure spans an `instrument_id` change; artificial roll gaps never create zones) ·
ADR14 = roll-safe average session range known at open · point→zone conversion ±0.05·ADR14
(ZONE_SPEC §3b) · activation = creation bar close +1s · episode engine, horizons, dual unit
systems per ZONE_SPEC v1.1 · controls C1v2 + C2 per EVALUATION_FRAMEWORK v1.2 · primary metric
NetFav60/ADR14 (ZON-015: continuation NetAdv60/ADR14) · classification thresholds unchanged.
Generation-time dedup for rolling snapshot families (ZON-011/012): a new zone is skipped if it
overlaps a still-active same-family zone with IoU ≥ 0.5 (prevents snapshot explosion; frozen).

**ZON-007 Displacement-origin (15m).** Displacement bar j: range ≥ 3.0×med20 (median 15m range of
prior 20 bars, shifted) AND |close−open| ≥ 0.7×range. Base = maximal run (1–4 bars) ending at j−1,
each with range ≤ 1.0×med20, contiguous, same segment. Zone = [min low, max high] of base bars;
demand if displacement up, supply if down. Guards: 2 ticks ≤ W ≤ 0.5·ADR14(day j). Expiry 5
sessions; invalidation 15m close beyond distal.

**ZON-008 Rejection-tail (30m).** Bar j with range ≥ 1.5×med20 and dominant tail ≥ 0.6×range
(upper tail = high−max(o,c); lower = min(o,c)−low). Zone = OUTER HALF of the tail:
upper [high−0.5·tail, high] (supply), lower [low, low+0.5·tail] (demand). Guards: 2 ticks ≤ W ≤
0.5·ADR14. Expiry 5 sessions; invalidation 30m close beyond distal.

**ZON-009 Breakout role-reversal (1h).** Confirmed 1h fractal pivot (strictly above/below 2 bars
each side, confirmed 2 bars later — causal). First subsequent 1h close (same segment, ≤15 sessions
after pivot confirmation) beyond the pivot price by ≥ 0.15·ADR14(day of close) = breakout. Zone =
pivot ± 0.05·ADR14; broke above swing high → support (demand); broke below swing low →
resistance. One zone per pivot. No retest requirement. Expiry 10 sessions; invalidation 1h close
back beyond the zone on the original side (= acceptance beyond distal under btype).

**ZON-010 Multi-touch acceptance boundaries (30m rule TF; 3-session structure).** At each session
open: time-at-price histogram (0.1 bins; each prior 1m bar adds 1 to every tick in its range) over
the prior 3 full sessions, bars of the segment active at today's open only (skip day if < 1000
such bars). 70% time-value-area around the time-POC (greedy single-bin expansion). Zones = the two
acceptance EDGES: upper/lower VA boundary ± 0.05·ADR14(today). Skip day if VA width < 0.3·ADR14
(degenerate). Active today only; untyped (btype 0); invalidation 30m close beyond distal
(approach-relative).

**ZON-011 Anchored VWAP deviation (session-open anchor).** Per session, volume-weighted VWAP and
weighted σ of typical price (h+l+c)/3, cumulative from session open, single opening segment (band
dies at a roll). At each completed shifted-clock hour (≥60 bars elapsed): snapshot levels
vwap±2.0σ; create a zone (level ± 0.05·ADR14) per side IF the level is ≥ 0.10·ADR14 away from
current close (band ahead of price, no instant-touch artifact). Upper band = resistance-type,
lower = support-type. Expiry 240 trading minutes (bar-indexed); invalidation 30m close beyond
distal. Only the session-open anchor (no swing/impulse anchors in this batch — one spec).

**ZON-012 Volume-concentration boundaries (rolling 6h).** At each completed shifted-clock hour:
volume-at-price histogram (0.1 bins, volume spread uniformly over each 1m bar's range) of the
prior 360 1m bars (same segment; skip if fewer). 70% volume-VA around the rolling POC. Zones =
VA outer boundaries ± 0.05·ADR14 IF the boundary is ≥ 0.05·ADR14 from current close. Untyped;
expiry 240 trading minutes; invalidation 1h close beyond distal. Distinct from ZON-003
(prior-session, daily) and ZON-010 (time-based, 3-session).

**ZON-013 Compression→expansion origin (5m).** Box = trailing 12 five-minute bars (contiguous,
same segment) with total span (max high − min low) ≤ 0.25·ADR14. Expansion bar x (the next bar):
range ≥ 2.5 × median range of the 12 box bars AND close outside the box. Zone = the box
[min low, max high]; demand if expansion up, supply if down. Guards: W ≥ 3 ticks (box cap implies
W ≤ 0.25·ADR14). Skip if overlapping an active ZON-013 zone with IoU ≥ 0.5. Expiry 5 sessions;
invalidation 15m close beyond distal. (Distinct from failed ZON-004: 5m TF, box-span definition
normalized by ADR, expansion measured vs box's own ranges.)

**ZON-014 HTF imbalance confluence (1h + 4h).** FVGs built with the ZON-002 3-bar rule on 1h and
on 4h (contiguous bins, same segment; guards 2 ticks ≤ W ≤ 1.0·ADR14). When a NEW 1h FVG overlaps
an ACTIVE same-direction 4h FVG (4h FVG age ≤ 10 sessions) by ≥ 50% of the smaller width: zone =
the INTERSECTION interval, created at the 1h FVG creation. One definition, no other combinations.
Expiry 10 sessions; invalidation full traversal (like ZON-002).

**ZON-015 FVG traversal/continuation — BATCH-1-INSPIRED EXPLORATORY (label mandatory).**
Universe = the exact ZON-002 15m FVG spec (unchanged). Hypothesis: ENTERING an FVG predicts
continuation through it (toward/beyond the opposite edge) versus comparable areas. Primary metric
= Δ mean NetAdv60/ADR14 = (AE₆₀−FE₆₀)/ADR14 real − control, vs C1v2 AND C2; secondary Δ traversal
rate. NOT a bounce hypothesis; the Batch-1 bounce criterion is not reused. Because it was
motivated by Batch-1 discovery results, a pass can NEVER be treated as independent confirmation —
it would still require validation, and its exploratory status is carried in every report.
