# BATCH 8 — STATE×ZONE INTERACTION MINING (GC, 2016–2019 mine / 2020–2021 confirm)
Run 2026-08-16 · plan/states/triage/ranking frozen pre-outcome (BATCH8_PLAN.md) · state truncation
parity PASS (3,007 events × 20 states) · null hurdle (OBS-11) applied as hard gate ·
2022+ untouched · ZON-028 remains skipped.

## Search accounting (158 DoF, all logged)
6 zone universes (existing parity-tested geometries) + 20 frozen state definitions + 120 cheap
triage contrasts (`triage_grid.csv`) + 10 full state×zone evaluations + frozen triage rule +
frozen ranking formula. No threshold sweeps; speed-quartile thresholds frozen from the mining
window and carried unchanged into confirmation.

## Universe baselines (zone alone, 2016–2019)
U1 FVG 7.9/day (C1 unhealthy: 45% uncontrolled) · U2 compression 2.4/day · U3 tail 1.3/day ·
U4 session-trap 0.57/day · U5 VA-boundary 10.0/day (d1 +0.008/d2 +0.008) · U6 NR7 0.8/day.
No baseline near the hurdle — consistent with all prior batches.

## Mining highlights (full evaluations; frozen score = min(ΔC1s, ΔC2s, C−A) + frequency + stability)
Selected pairs concentrated on: VWAP-side, slow-approach, high/low-vol regime, counter-trend,
failed-acceptance states. Strongest C2-side effects: FVG×slow-approach +0.041 (4/4 yrs),
FVG×counter-trend +0.031 (4/4), VA×slow +0.022 (4/4), compress×high-vol +0.022. But **no pair's
min-delta exceeded +0.011 in mining** — exactly the random-zone null maximum. Finalists (top-5 by
frozen formula): ZON-039 VA×VWAP-side · ZON-040 VA×slow-approach · ZON-041 compress×high-vol ·
ZON-042 VA×high-vol · ZON-043 compress×low-vol.

## Confirmation (2020–2021, frozen, one-shot)

| ID | pair | N | ΔC1-state [CI] | ΔC2-state [CI] | C−A | yrs | ev/day | survives |
|---|---|---|---|---|---|---|---|---|
| 039 | VA×vwapSide | 2,253 | **+0.055 [+0.018,+0.091]** | +0.006 [−0.004,+0.016] | +0.007 | +/− | 4.37 | **NO** |
| 040 | VA×slowApproach | 550 | +0.004 [−0.089,+0.085] | +0.016 [+0.001,+0.030] | +0.012 | +/+ | 1.07 | **NO** |
| 041 | compress×highVol | 368 | −0.026 | +0.024 [+0.005,+0.044] | +0.001 | (2020 only) | 0.71 | **NO** |
| 042 | VA×highVol | 1,638 | +0.007 | +0.009 [+0.000,+0.016] | +0.008 | +/− | 3.17 | **NO** |
| 043 | compress×lowVol | 379 | +0.045 (wide) | +0.013 [−0.012,+0.035] | −0.006 | (2021 only) | 0.73 | **NO** |

**No finalist clears ≥ +0.02 ADR against BOTH controls.** Verdict: batch fails; all five closed;
no rescue variants.

## What the batch established
1. **The interaction hypothesis is answered, negatively but precisely:** market states DO
   modulate zone-touch outcomes vs matched moments — ZON-040's slow-approach effect is the most
   consistent C2-side signal the project has produced (positive in ALL SIX periods 2016→2021,
   +0.013…+0.049) — but no state makes a SPECIFIC zone worth ≥ +0.02 beyond both the state itself
   and same-state nearby areas simultaneously.
2. **The C1↔C2 dissociation persists under conditioning** (7th independent appearance): ZON-039's
   C1 replicated and grew (+0.028 → +0.055, null pct 100) while its C2 stayed flat. Whatever
   makes touches "work" travels with the moment/context, not the drawn rectangle.
3. Frequency goals were reachable (1–4.4 qualified touches/day); magnitude was not.
4. Control quality was healthy for the finalists (spz 1.8–3.9; VA/compress noctl ≤ 16%; FVG's
   chronic C1 starvation kept its pairs out of the finals).

## Files
`BATCH8_PLAN.md` · `tools/batch8/{states_lib.py, run_stage_a.py, confirm_b8.py}` ·
`aurum/batch8/{triage_grid.csv, stage_a.json, confirm_b8.json, BATCH8_REPORT.md}` ·
ledger +5 rows (ZON-039…043, all fail). Hypothesis count: **43**.
