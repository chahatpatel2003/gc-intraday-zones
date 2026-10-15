# BATCH 8 — STATE×ZONE INTERACTION MINING (frozen BEFORE any outcome)
Frozen 2026-08-16. Split: 2016–2019 mining · 2020–2021 frozen branch confirmation (NOT globally
virgin — used in earlier project batches; within-branch discipline: freeze before looking, no
rescue variants). 2022+ untouched. ZON-028 stays skipped. Null hurdle (OBS-11) is HARD:
promotion requires ≥ +0.02 ADR vs BOTH controls; null percentile recorded for every finalist.

## Zone universe (6 existing deterministic, parity-tested geometries — unconditional hypotheses
stay closed; the NEW hypotheses are state×zone interactions)
U1 15m FVG (gen_zon002) · U2 5m compression box (gen_zon013) · U3 30m rejection tail (gen_zon008)
· U4 session-extreme trap pocket (motif M02) · U5 rolling-6h volume-VA boundary (gen_zon012) ·
U6 NR7 box (motif M09). Strict lifecycle, LIVE first touch only, within-family dedup, roll death.

## State vocabulary — 20 motifs, ONE frozen definition each (evaluated from COMPLETED bars only,
strictly before the touch bar T0; side-matched states use the zone's btype; identical lookup
applied to C1 shadows (their btype) and C2 donors (pseudo-side)):
S01 withTrend: last completed 30m EMA20>EMA50 & demand zone, or EMA20<EMA50 & supply.
S02 counterTrend: the opposite alignment. S03 vwapSide: 1m close(T0−1) above session VWAP &
demand, or below & supply. S04 rsiStretch: last completed 15m RSI14 ≥70 & supply, or ≤30 & demand.
S05 decelApproach: |roc5|(t) ≤ 0.75×|roc5|(t−5) with |roc5|(t−5) ≥ 0.05 ADR (15m closes/ADR).
S06 fastApproach: 1m 5-bar |log-ret|/ADR in mining-window top quartile (threshold frozen at
build, logged). S07 slowApproach: bottom quartile. S08 highVolRegime: ADR14 ≥ 67th pct of
trailing 250 sessions. S09 lowVolRegime: ≤ 33rd pct. S10 expansionDay: session range-so-far ≥
1.0×ADR14. S11 volClimax3: max 15m volz20 of last 3 completed bars ≥ 3. S12 quietApproach: mean
15m volz20 of last 3 ≤ −0.5. S13 sweepReclaim: within last 12 completed 15m bars, a bar exceeded
its prior-20-bar extreme and closed back inside, on the ZONE's side. S14 failedAccept: within
last 12 completed 30m bars, close beyond running session extreme then close back within 3 bars,
zone side. S15 displacementApproach: within last 6 completed 15m bars, range ≥ 2.5×med20 toward
the zone. S16 chopApproach: mean consecutive-bar range IoU of last 6 completed 15m bars ≥ 0.6.
S17 balanceTransition: 30m bars t−12..t−7 span ≤ 0.35×ADR AND last completed close outside it.
S18 rangeEdge: close(T0−1) in outer 20% of session range-so-far, zone side. S19 nySession: T0 in
NY bucket. S20 opening90: T0 within first 90 trading bars of session.

## Search path & budget (hard caps)
1. Universe baselines A: 6 zone-alone evaluations (full C1v2+C2) on 2016–2019.
2. Triage grid: 6×20 = 120 CHEAP conditional contrasts (state-on vs universe mean NetFav60/ADR;
   no controls). Frozen triage rule: eligible if N_on ≥ 300 AND state-on events/day ≥ 0.5; rank
   by uplift; take top 10 pairs, max 3 per universe.
3. Full interaction evaluation of ≤10 pairs: C1-state (ladder strips whose shadow touches satisfy
   the state) · C2-state (matched moments where the state holds without the zone) · interaction
   deltas C−A (vs zone-alone universe mean) and C−B (≡ ΔC2-state).
4. **Frozen ranking formula:** Score = min(ΔC1state, ΔC2state, C−A) + 0.01×min(events/day, 3)
   + 0.01×(positive discovery years − 2). Eligibility: N ≥ 300, events/day ≥ 0.5 (unless
   min-delta ≥ +0.05), healthy controls (spz ≥ 2, uncontrolled ≤ 20%). Top ≤5 → finalists
   ZON-039…043, frozen (state, geometry, direction=rejection unless declared, lifecycle,
   thresholds) before ANY 2020–2021 access.
5. Confirmation standard: ΔC1state & ΔC2state ≥ +0.02 ADR preferred, C−A > 0, both years
   supportive, health, ≥1/day preferred; small significant effects below the hurdle FAIL.

Rejection vs continuation: universes U1–U6 are evaluated in REJECTION framing by default; a
continuation-framed finalist requires the declaration at freeze (Score computed on its declared
metric). DoF accounting: 6 baselines + 20 states + 120 triage contrasts + ≤10 full evaluations +
1 triage rule + 1 ranking formula ≈ **158**, all logged. No XAUUSD (dedicated later branch). News
descriptive only (no calendar on disk → not recorded). No execution research.
