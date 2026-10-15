# SELECTION-BIAS NULL BENCHMARK — RESULTS
Run 2026-08-16 · plan frozen pre-outcome (NULL_BENCHMARK_PLAN.md) · master seed 20260816, all
tournament seeds = master+1000+t, OOS streams master+900000+t·1000+winner (logged in
tournaments.json) · leakage spot-test PASS · 2016–2021 only; 2022+ untouched.

## Benchmark A — fixed-rule null (100 tournaments × 1,000 zero-edge strategies)
Eligible universe: 5-min grid, active sessions, ADR defined, ≥120 same-segment forward bars.
Buckets 250×{1,2,3,5}/day. Execution: entry close+1 tick, stop −1 tick slippage, target only if
traded through, $5 RT commission, both-in-bar → stop. Exit V1 = 0.15/0.15·ADR, 120-bar time stop.

**Best-of-1,000 distribution across tournaments (2016–2019):**

| max of | median | p90 | p95 | p99 |
|---|---|---|---|---|
| Sharpe | −0.61 | −0.34 | −0.23 | −0.18 |
| expectancy (pt) | −0.076 | −0.043 | −0.029 | −0.023 |
| profit factor | 0.914 | 0.951 | 0.966 | 0.973 |
| win rate | 48.7% | 49.4% | 49.8% | 50.0% |
| total P&L (pt) | −79 | −44 | −30 | −24 |
| positive years (of 4) | 1 | 2 | 2 | 2 |

Under honest GC frictions (≈0.25 pt RT), **even the best of 1,000 random strategies is
unprofitable in-sample, in every one of 100 tournaments**. Apparent *profitability* cannot be
manufactured by strategy selection alone at this scale — cost drag dominates.

## Benchmark B — researcher-freedom null (+5 exit variants per strategy = 5,000 effective)
Best-of-5,000: Sharpe median −0.23, **p90 +0.02, p95 +0.13, p99 +0.30**; expectancy p95 +0.017,
p99 +0.041 pt. **One extra selection layer (5 exits) adds ≈ +0.4 Sharpe of pure illusion** and
produces an apparently profitable zero-edge system in ~10–15% of tournaments. Researcher freedom,
not market signal, is where fake edges come from.

## Winner's curse (frozen ranking = Benchmark-A Sharpe; winner carried unchanged to 2020–2021)
Winner IS Sharpe median −0.61 → OOS median **−0.81**; IS expectancy −0.078 → OOS −0.212 pt.
**11% of selected winners were profitable OOS** (pure luck). Selection uplift evaporates exactly
as theory predicts.

## Random-zone null (200 information-free zone families, exact real pipeline, 2016–2019)
Realistic width (U 0.05–0.25·ADR), distance (U 0.05–0.30·ADR), rate {0.5–3}/day, real lifecycle,
C1v2 + C2, first touch, dedup — placement random by construction.

| ΔNetFav60/ADR | median | p90 | p95 | p99 | **max of 200** |
|---|---|---|---|---|---|
| vs C1 | −0.007 | +0.007 | +0.008 | +0.013 | **+0.020** |
| vs C2 | −0.011 | −0.002 | +0.001 | +0.007 | **+0.011** |
| min(both) | −0.012 | −0.003 | −0.001 | +0.007 | **+0.011** |

**False-family rate (both CIs > 0): 0 / 200.** The double-control architecture produced zero
false positives on random zones — the project's methodology is sound.

## Our historical findings vs the zone null (diagnostic; nothing rerun)

| Finding | Δs | Percentile vs null | Verdict |
|---|---|---|---|
| ZON-028 trap (2016–21) | +0.053 / +0.024 | **100.0 / 100.0** — beyond the max of 200 randoms on BOTH controls (2.6× best random C1, 2.2× best random C2) | NOT explainable by selection at our search scale |
| ZON-017 isolated C1 | +0.040 | 100.0 | beyond null max (but Batch-4 showed it was context, a different failure) |
| ZON-035 mined | +0.030 / +0.016 | 100.0 / 100.0 | beyond null max in-window (C2 later failed confirmation) |
| M03 trap echo | min +0.023 | 100.0 | beyond null max |
| ZON-012 | +0.010 / +0.007 | 98.0 / 98.5 | **inside selection noise**: our real search ≈ 38 hypotheses + 21 mining DoF ≈ 60 effective families; the expected best-of-60 min-delta ≈ the null's p98.3 ≈ +0.007 — exactly ZON-012's value |

Caveats: window mismatch (several findings measured on 2016–2021 vs null on 2016–2019) and the
null's 200 families exceed our ~60 effective searches, making the hurdle conservative.

## Frozen selection-bias hurdles for any future work
Zone-level: a family must exceed **≈ +0.02 ADR on BOTH controls** (null max +0.011 min-delta;
p99 +0.007) to sit beyond best-of-search noise at our scale. Trade-level: any backtested system
must beat Benchmark-B p95/p99 Sharpe **+0.13 / +0.30** before being taken seriously.

## Researcher degrees of freedom (this experiment)
100,000 independent null strategies (A); ×5 exits = 500,000 effective candidates (B); 200 random
zone families × 2 controls; 4 buckets; 1 frozen ranking metric + 6 descriptive maxima;
100 tournaments = Monte-Carlo repetitions (not candidates). All seeds and logs in
tournaments.json / zone_null_log.csv.

## Conclusions
1. Selection alone cannot fake PROFITABILITY on GC under honest costs — but it easily fakes
   RELATIVE edges of ≤ ~+0.01 ADR and, with modest parameter freedom, positive Sharpe.
2. The project's control methodology is validated (0% false-family rate).
3. **ZON-012-class results (+0.7–1% ADR) are fully consistent with selection bias** — coherent
   with their later reattribution to context.
4. **ZON-028's discovery signal is genuinely beyond selection noise** on the discovery data —
   the one prior finding the null cannot explain. (This says nothing about 2022+; it was never
   validated and remains frozen.)
5. The trap-mechanism echoes (M03) also exceed the null — the mechanism class, not just the one
   spec, appears non-random in-sample.
