# SELECTION-BIAS NULL BENCHMARK — PLAN (frozen before any outcome)
Frozen 2026-08-16. 2016–2021 only; 2022+ untouched. This is a META experiment (no ZON id, no real
strategy search). Master seed **20260816**; tournament t uses seed master+t; every stream is
seeded/reproducible and logged.

## Eligible entry universe (defined before outcomes)
GC 1m bars, 2016–2021, on a 5-minute grid (bar minute % 5 == 0), session ∈ {ASIA, LONDON, NY,
LATE}, ADR14 defined, ≥120 forward bars remaining in the same contract segment (no roll-transition
entries), ≥5 bars into the segment. Selection window 2016–2019; frozen replication window
2020–2021.

## Random strategies (information-free by construction)
Entry bars sampled uniformly without replacement from the eligible set (per window), minimum gap
15 bars within a strategy; direction = fair coin per entry. No price/indicator/volume/session-
predictive content anywhere. Frequency buckets (preregistered): 250 strategies each at ~1, ~2, ~3,
~5 entries/day (N = rate × eligible days). Signal-level evaluation (overlaps allowed — identical
convention for every strategy; Sharpe uses daily aggregated P&L so overlap penalizes itself).

## Execution (identical for all)
GC tick 0.1 ($10/tick). Entry at signal-bar close + 1 tick adverse. Stop fill = stop − 1 tick
slippage. Target = limit filled only when traded THROUGH by ≥1 tick. Time exit at close − 1 tick.
Commission $5.00 RT = 0.05 pt. Intrabar rule: target and stop both inside one 1m bar → STOP
(project's conservative ambiguity convention). First passage on the 1m path, never intrabar
sequencing.

## Exit models (frozen)
**Benchmark A (fixed-rule null):** every strategy uses V1 = stop 0.15·ADR14 / target 0.15·ADR14
(1:1), time-stop 120 bars.
**Benchmark B (researcher-freedom null):** per strategy, best of 5 variants by the frozen ranking
metric: V1 1:1 (0.15/0.15) · V2 1:2 (0.15/0.30) · V3 2:1 (0.30/0.15) · V4 time-only 60 bars ·
V5 tight 1:1 (0.10/0.10). Exit-variant count explicitly logged.

## Frozen primary ranking metric
**Annualized daily-P&L Sharpe (√252) on 2016–2019, Benchmark-A model.** One metric, chosen now.
All other statistics (expectancy, PF, win rate, max drawdown, total P&L, yearly consistency) are
descriptive; their per-tournament maxima are reported as per-metric nulls, never used to select.

## Tournaments
**100 tournaments × 1,000 strategies** (Benchmark A and B evaluated for all). Per tournament: rank
by the frozen metric, carry the single winner's generative RULE (bucket rate + seeded stream)
unchanged into 2020–2021 (fresh eligible bars, fresh coins — a zero-edge rule stays zero-edge),
Benchmark-A exits; measure collapse. No reselection on 2020–2021. Estimated cost ~10–30 min
(precomputed outcome tables make strategies cheap); the full 100 is run — no silent reduction.

## Random-zone null (separate)
**200 random zone families** on 2016–2019 through the EXACT real-zone pipeline (strict lifecycle,
first touch, within-family dedup, C1v2 nearest-eligible strips, C2 matched moments, seed 20260816).
Per family (seeded): rate ∈ {0.5,1,2,3}/day; life 50% session-end / 50% 5-sessions; per zone:
random eligible creation bar, offset distance U(0.05,0.30)·ADR to a random side, width
U(0.05,0.25)·ADR, btype = side, invalidation 30m close beyond distal, gen-dedup IoU ≥ 0.5.
Placement independent of future outcomes by construction. Deliverable: distribution and maxima of
ΔC1/ΔC2 point estimates and the both-CIs-clear false-family rate; percentile ranks of our
strongest historical findings against it (diagnostic only; historical results untouched).

## Researcher-freedom accounting
Independent null candidates: 100,000 strategies (A); ×5 exits = 500,000 effective (B); + 200
random zone families ×2 controls. Monte-Carlo repetitions (tournaments): 100 — counted separately
from candidates. Ranking choices: 1 frozen + 6 descriptive maxima. Buckets: 4.
