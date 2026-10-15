# BATCH 5 — FUNDAMENTALLY DIFFERENT FAMILIES (discovery 2016–2021, GC only)
Run 2026-08-16 · specs frozen pre-run (BATCH5_SPECS.md) · 24/24 parity/causality/roll checks PASS ·
C1v2 + standard C2 · strict lifecycle, first touch only, max touches 1 · seed 20260816 · no 2022+.

## Verdict table (Δ mean NetFav60/ADR14)

| Fam | N | Δ vs C1v2 [CI] | Δ vs C2 [CI] | Yrs +ve | Ev/day | Class |
|---|---|---|---|---|---|---|
| **ZON-028 trap** | **497** | **+0.053 [+0.027, +0.078]** | **+0.024 [+0.005, +0.044]** | **5/6** | 0.32 | **PROMISING (both CIs clear)** |
| ZON-026 QML | 4,110 | +0.101 [+0.065, +0.137]¹ | +0.009 [−0.002, +0.019] | 5/6 | 2.68 | PROMISING¹ (control-compromised) |
| ZON-027 breaker | 2,850 | −0.006 [−0.020, +0.010] | +0.005 [−0.005, +0.015] | 3/6 | 1.86 | NO EDGE |
| ZON-029 sweep+displ | 8,773 | +0.018 [+0.003, +0.036] | −0.001 [−0.008, +0.005] | 1/6 | 5.72 | NO EDGE (well-powered null vs C2) |
| ZON-030 HTF OB | 565 | +0.024 [−0.008, +0.055] | +0.004 [−0.021, +0.030] | 4/6 | 0.37 | NO EDGE |
| ZON-031 prev-week edge | 333 | −0.014 [−0.053, +0.018] | −0.027 [−0.060, +0.001] | 1/6 | 0.22 | NO EDGE |
| ZON-032 LVN | 470 | −0.005 [−0.026, +0.015] | −0.005 [−0.024, +0.013] | 3/6 | 0.31 | NO EDGE |
| ZON-033 quantile tail | 1,596 | −0.001 [−0.014, +0.012] | −0.010 [−0.022, +0.001] | 2/6 | 1.04 | NO EDGE |

¹ ZON-026's C1 is structurally compromised: QML zones self-overlap 86.7% (NN gap 0.022 ADR),
58% of zones found no eligible control strip (0.67 shadows/zone) — the surviving C1 sample is
selected, exactly the Batch-1 FVG failure mode. Its C2 (the trustworthy control here) straddles
zero at N=4,110. The preregistered classifier outputs PROMISING; the mandatory control-quality
caveat makes that label fragile.

## The finding: ZON-028 failed-breakout traps

First family in 33 hypotheses to clear **both control CIs simultaneously**:
- vs displaced strips **+5.3% ADR** (above the 5% materiality bar on C1);
- vs matched moments **+2.4% ADR** (CI positive; materiality bar unmet → PROMISING, not STRONG);
- positive 2016–2020 (+0.025…+0.049), negative 2021 (−0.032) — 5/6 years;
- the cleanest zone stream produced so far: 0.32 events/day, 69% of days none / 30% exactly one,
  NN spacing 0.61 ADR, self-overlap 2.2%, **ambiguity 1.6% (project minimum)**, rejection-rate
  19.9%→20.9% highest of any family, traversal 33% (lowest of typed families) and −3.2pp vs
  matched moments.
Mechanism reads coherently: a failed acceptance beyond a 3-session extreme leaves trapped
breakout participants; the overshoot pocket rejects price on first return. Everything is causal,
live-computable, roll-safe, first-touch-only.

## Continuation/traversal information

None usable: the high-traversal families (breaker 75%, sweep 73%) traverse *no more than matched
moments* (−1..−3pp). Weekly edges traverse +5pp *more* than matched moments with negative NetFav —
the familiar anti-barrier signature at weekly scale (echoes ZON-001/005). Descriptive only.

## Density / spacing / cross-family

Raw batch stream 12.5 events/day → 9.6 independent clusters/day (20.9% multi-family; top pairs:
sweep+breaker, sweep+QML — the ICT-style families largely tag the same structures). Sparse clean
families: trap 0.61-ADR spacing, OB 0.29, weekly 1.79, LVN/tails non-overlapping. Dense messy:
QML (87% overlap), sweep (80%).

## Control-quality diagnostics

Healthy (3.3–4.0 shadows/zone, ~0 uncontrolled): 028, 032, 033, 031, 030, 027. Compromised by
self-overlap: 026 (58% zones uncontrolled), 029 (27%). C2 shortfalls ≈ 0 everywhere. No control
was substituted after results anywhere.

## Failed families / branch decisions (one-follow-up rule, OBS-9)

- **CLOSE:** ZON-027 (breaker — flat, 22% ambiguity), ZON-029 (sweep — well-powered C2 null at
  N=8,773), ZON-030 (OB — straddling CIs, erratic years), ZON-031 (weekly edges — negative),
  ZON-032 (LVN — flat, honest null), ZON-033 (quantile tails — flat/negative).
- **ZON-026 QML:** eligible for its ONE follow-up strictly as a **control-repair** follow-up
  (generation-dedup to kill the 87% self-overlap so C1 becomes measurable); its C2 null at high N
  argues against; user decides whether the follow-up is spent.
- **ZON-028 trap:** did not fail — the first genuine validation-candidate-quality result.
  Options: (a) present for validation candidacy as-is; (b) spend its one follow-up on a
  preregistered robustness variant BEFORE any validation decision. Recommendation: (a) — the spec
  is clean, frozen, and untouched by iteration; saving the follow-up preserves optionality.

## Hypothesis count: 33. Strong-criterion frequency: 0/day; promising: 3.0/day (dominated by the
compromised ZON-026; trustworthy promising stream = ZON-028's 0.32/day).
