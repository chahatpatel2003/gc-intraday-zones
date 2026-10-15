# BATCH 7 — PATTERN MINING → FROZEN CONFIRMATION (GC, discovery branch)
Run 2026-08-16 · plan frozen pre-mining (BATCH7_MINING_PLAN.md) · candidates frozen pre-confirmation
(BATCH7_SPECS.md) · Stage-B gates 12/12 PASS · 2016–2019 mined, 2020–2021 opened once, frozen ·
2022+ never touched.

## Search accounting (researcher degrees of freedom)
16 motif templates screened (one frozen parameterization each; no threshold sweeps) + 4 matched
indicator overlays + 2 indicator-bearing bases (M15 RSI-divergence, M16 EMA-pullback) within the
16 + 1 frozen mechanical selection rule = **21 DoF**, all logged (`mining_log.csv`,
`overlay_log.csv`, `jaccard.json`). M03 (ZON-028 near-clone) screened for information only and
barred from selection — it ranked FIRST (ΔC1 +0.042, ΔC2 +0.023, both CIs clear), an out-of-family
echo of the trap mechanism on 2016–2019.

## Mining outcomes (2016–2019)
Eligible positive-min bases: M07 volume climax (+0.030/+0.016, both CIs clear), M01 OR-trap,
M09 NR7, M02 session-extreme trap. Failures: VWAP-band trap NEGATIVE both sides (−0.028/−0.038);
double-attack, exhaustion, 3-probes, NY-fade, whipsaw, RSI-divergence flat-to-negative;
impulse-base and HV-base starved (21/16 zones); balance-continuation failed control health + C2.
**Indicators: every overlay reduced both deltas** (e.g. M07+RSI: +0.030→+0.012, +0.016→+0.009,
N 1066→269) — zone+indicator NEVER beat zone-alone; incremental rule (+0.02) rejected all four.
Event-overlap Jaccard ≤ 0.101 → no dedup removals. Frozen: ZON-035 (M07), ZON-036 (M01),
ZON-037 (M09), ZON-038 (M02) — four candidates, slots 039/040 left honestly unfilled.

## Confirmation (2020–2021, one-shot, frozen)

| ID | N | Δ vs C1v2 [CI] | Δ vs C2 [CI] | 2020 / 2021 | Ev/day | Verdict |
|---|---|---|---|---|---|---|
| ZON-035 volume climax | 594 | **+0.048 [+0.019, +0.077]** | +0.006 [−0.016, +0.027] | 0.000 / +0.012 | 1.15 | NO LOCATION EDGE |
| ZON-036 OR trap | 726 | +0.006 [−0.012, +0.023] | −0.001 [−0.014, +0.012] | −0.004 / +0.002 | 1.41 | NO LOCATION EDGE |
| ZON-037 NR7 release | 369 | +0.023 [−0.002, +0.052] | +0.020 [−0.003, +0.042] | +0.034 / +0.007 | 0.72 | NO LOCATION EDGE |
| ZON-038 session trap | 349 | +0.023 [−0.004, +0.046] | +0.000 [−0.022, +0.025] | −0.016 / +0.016 | 0.68 | NO LOCATION EDGE |

Control health in confirmation: fine everywhere (spz 2.7–3.9; noctl ≤ 21/647 zones); ambiguity
2–5%; C2 shortfalls ≈ 0.

## Reading
- **No survivor.** The mining-window C2 edges shrank toward zero out-of-window — the expected
  signature of selection bias, which the internal split existed to catch. The frozen standard
  (both CIs > 0, both years positive) was met by nothing.
- **ZON-035's C1 effect genuinely replicated** (+0.030 mined → +0.048 confirmed, CI clear) — the
  strongest cross-window C1 replication in the project — but its matched-moment test failed again
  (+0.006). Sixth independent appearance of the project's core phenomenon: candidate zones beat
  their NEIGHBORHOOD, not the MOMENT.
- ZON-037 is the only candidate positive on all four cells (both controls, both years) but is
  CI-limited at N=369 and cannot gain N without loosening (forbidden).
- Continuation framing (M10) failed in mining (C2 −0.009, control starvation). No continuation
  candidate reached confirmation.
- XAUUSD: preregistered infeasible (spot data begins 2021-06-29; zero mining-window overlap).

## Branch decisions
CLOSE ZON-035, ZON-036, ZON-037, ZON-038 (base tests failed; no follow-up can honestly address
the failure mode — 035/037's limitation is context-dependence and sample size, not a repairable
spec defect). Nothing in this batch is strong enough for execution-confirmation research.
Per plan §19: a failed batch does not conclude "zones don't work"; the next batch, if any, must be
fundamentally different. Hypothesis count: **38**.
