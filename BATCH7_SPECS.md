# BATCH 7 — FROZEN CONFIRMATION CANDIDATES (ZON-035…038)
Frozen 2026-08-16 AFTER Stage-A mining (2016–2019), BEFORE any 2020–2021 access.
Selection applied mechanically per BATCH7_MINING_PLAN (log: aurum/batch7/mining_log.csv,
overlay_log.csv, jaccard.json). Degrees of freedom spent: 16 motifs + 4 overlays + 1 frozen
selection rule = **21**, all logged. M03 (ZON-028 near-clone) was barred from selection despite
ranking first — its result stands only as an out-of-family echo of the trap mechanism.
**No indicator survived** (every overlay reduced both deltas; incremental rule +0.02 failed
everywhere) → all candidates are PURE pattern→zone. **No XAUUSD candidate** (spot data begins
2021-06-29; zero overlap with the mining window — preregistered as infeasible).

| ID | = Motif | TF | Sequence & zone (constants frozen in BATCH7_MINING_PLAN) | Mining ΔC1 / ΔC2 | Ev/day |
|---|---|---|---|---|---|
| **ZON-035** | M07 volume climax | 30m | new 20-bar extreme + vol ≥3×volmed20 + close in far half → zone = outer half of climax bar; rejection | +0.030 [+0.011,+0.050] / +0.016 [+0.000,+0.033] | 1.05 |
| **ZON-036** | M01 opening-range trap | 15m | OR = first 4 bars; close beyond OR edge then close back inside ≤3 bars → overshoot pocket; rejection; session life | +0.010 / +0.004 | 1.29 |
| **ZON-037** | M09 NR7 release | 30m | narrowest-of-7 bar; next bar closes beyond it with range ≥1.5×med20 → zone = NR bar range; rejection | +0.009 / +0.002 | 0.81 |
| **ZON-038** | M02 session-extreme trap | 15m | running session extreme (set ≥8 bars prior) broken by close, close back inside ≤3 bars → overshoot pocket; rejection; session life | +0.013 / +0.001 | 0.58 |

Lifecycle (all): activation = confirm close (+1s equiv.), invalidation = source-TF close beyond
distal, session-scoped motifs expire at session end, others 5 sessions, mitigation = full
traversal, max touches 1, reclaim = new ID, roll death, strict lifecycle, no future info.

## Confirmation protocol (Stage C, frozen)
Window: **2020-01-01 → 2021-12-31**, loaded with warmup from 2019-11-01 (indicator/ADR/med20
history only); ONLY zones created on/after the first 2020 trade date count; C2 donor pool
restricted to 2020–2021 days; C1v2/C2 machinery identical to mining; day-block bootstrap seed
20260816. NO changes of any kind to the four specs. Survivor standard: ΔC1 CI > 0 AND ΔC2 CI > 0
on 2020–2021, both years' point estimates positive, healthy controls, magnitude reported against
the +0.05·ADR economic bar. Stage-B gates first: truncation/streaming parity, activation
causality, roll safety on all four generators (windows inside the mining period).
