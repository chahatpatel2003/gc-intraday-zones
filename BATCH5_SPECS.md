# BATCH 5 — FUNDAMENTALLY DIFFERENT FAMILIES (ZON-026…033)
Frozen 2026-08-16 BEFORE any Batch-5 outcome. One construction per family, no sweeps, no
replacement exercised (external-research option reviewed; sources logged per family in the ledger;
no fundamentally superior alternative found that warranted replacing a family).

**Common locked rules (every family):** discovery 2016–2021 GC only · source TF ≥ 5m (frames used:
15m/30m/1h/1d/weekly structure from 1m aggregation) · strict lifecycle
`CREATED → ACTIVE → TOUCHED → MITIGATED/INVALIDATED/EXPIRED`, only LIVE zones interact ·
**max valid touches = 1** · no broken-zone reuse · reclaim = new version only (not used) · no
backdating/future info · **zone dies at contract roll**; no structure spans a roll · activation =
creation close +1s · med20 = trailing 20-bar median range (shifted) on the family's frame ·
pivots = fractal k=2, confirmed 2 bars later (causal) · width guards preregistered per family ·
mitigation = full traversal (dead) unless stated · episode engine, horizons 5/15/30/60/120
trading-min, dual unit systems, ambiguity flags — all unchanged (ZONE_SPEC v1.1).
**Controls:** C1v2 nearest-eligible strips (same-family exclusion, ladder 2–12W, ≤1.0·ADR) and
standard C2 moment-matched (96 context cells, width/side/distance-0 matched; these families are
not density-conditioned so the isolation-state extension is not applicable — frozen). Primary =
Δ mean NetFav60/ADR14 vs both, day-block bootstrap seed 20260816, classification thresholds
unchanged. If a control is structurally unusable for a family it is reported, never substituted.

| ID | TF | Construction (creation) | Zone [low, high] | Type | Invalidation / Expiry |
|---|---|---|---|---|---|
| **ZON-026 QML** | 30m | Bearish: confirmed pivot high H1 → next confirmed pivot low L1 → sweep bar trades above h1 → a later 30m bar CLOSES below l1 (structural break) — all within 15 sessions of H1, one segment; created at the break close. Bullish mirrored. One zone per H1 (first completed sequence). | [h1, sweep-phase max high]; symmetric-expand to 0.05·ADR floor; skip if W > 0.5·ADR | supply (+1) / demand (−1) | 30m close beyond distal / 10 sessions |
| **ZON-027 Breaker** | 30m | Confirmed pivot low, then a 30m bar with range ≥ 1.5·med20 CLOSES above the most recent prior confirmed pivot high (displacement structure-break up). Zone = BODY [min(o,c), max(o,c)] of the last bearish candle within 10 bars before the break bar (none → no zone). Bearish mirrored. Created at break close; no retest required. | opposing-candle body | demand (−1) / supply (+1) | 30m close beyond distal / 10 sessions |
| **ZON-028 Trap** | 30m + 3-session range | H3/L3 = prior-3-session extremes fixed at session open (current-open segment, ≥1000 bars). Bull-trap: a 30m bar CLOSES above H3, then within the next four 30m bars a bar CLOSES back below H3 — created at the failure close. Bear mirrored. | [H3, excursion max high] (overshoot pocket); floor 0.05·ADR, cap 0.5·ADR | supply (+1) / demand (−1) | 30m close beyond distal / 5 sessions |
| **ZON-029 Sweep+displacement** | 15m | Confirmed 15m pivot high ≥ 8 bars old; sweep bar: high > pivot high but CLOSES below it; within 2 bars a displacement bar: range ≥ 2.0·med20 closing below the sweep bar's low. Created at displacement close. Mirrored for lows. | [sweep-bar body top, sweep-bar high] (swept pocket); floor 0.05·ADR, cap 0.5·ADR | supply (+1) / demand (−1) | 15m close beyond distal / 5 sessions |
| **ZON-030 HTF order block** | 1h | Displacement bar: range ≥ 2.0·med20 AND body ≥ 0.7·range, whose close breaks the most recent prior confirmed 1h pivot (high for bullish). Zone = FULL RANGE of the last opposing-color candle ≤ 3 bars before the displacement bar (none → no zone). Created at the displacement/break close. | opposing candle [low, high]; guards 2 ticks–0.5·ADR | demand (−1) / supply (+1) | 1h close beyond distal / 10 sessions |
| **ZON-031 Prev-week edge structure** | weekly (from 1m) | At each week's first session open: prior-week high/low/range from the week's dominant segment (skip if < 2000 bars). Upper zone = outer 15% of prior-week range at the high; lower mirrored; width clipped to ≤ 1.0·ADR anchored at the extreme. Created/active at week open; NOT the failed PDH/PDL line method — structural width from the week's own range. | [wkLow+0.85·R, wkHigh] / [wkLow, wkLow+0.15·R] | supply (+1) / demand (−1) | **1d close beyond distal** / week end; roll mid-week kills |
| **ZON-032 LVN transition** | session (vol profile from 1m) | At session open: volume-at-price of prior 2 sessions (current-open segment, ≥ 800 bars), 5-tick smoothed; find two highest local peaks ≥ 0.3·ADR apart; LVN = minimum bin between them; require vol(LVN) ≤ 0.4·min(peak vols). Zone = maximal contiguous run of bins around LVN with vol ≤ 0.5·min(peak vols). Floor 3 ticks, cap 0.5·ADR. | LVN valley interval | untyped (0, approach-relative) | 30m close beyond distal / session end |
| **ZON-033 Statistical tail** | session (quantiles from 1m closes) | At session open: empirical quantiles of prior 2 sessions' 1m closes (current-open segment): lower zone = [q2.5, q10], upper = [q90, q97.5]. Non-discretionary distribution-tail band (short-horizon reversal literature). Guards 2 ticks–0.5·ADR. | quantile band | demand (−1) / supply (+1) | 30m close beyond distal / session end |

Per-family validation summary (user requirement): what makes each valid = all defining closes/
confirmations complete at creation (pivot confirmations, break closes, failure closes, finished
profile/quantile windows, finished prior week); what keeps it valid = LIVE state (no acceptance
beyond distal on the stated frame, no full traversal, not expired, same contract); first touch =
ZONE_SPEC canonical (inside-at-activation contacts consume no index); max touches 1; reclaim not
allowed. A future reaction can never create, validate, or resurrect a zone.
