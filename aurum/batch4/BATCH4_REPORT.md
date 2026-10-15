# BATCH 4 — ATTRIBUTION RESULTS (discovery 2016–2021, GC only)
Run 2026-08-16 · specs frozen pre-run (BATCH4_SPECS.md) · parity/causality tests 3/3 PASS ·
C2v2 isolation-matched control frozen pre-outcome · seed 20260816 · no 2022+ touched.

## The central question and its answer

> Is there a genuinely special price zone after controlling for isolation/context, or are we
> mainly detecting good market moments?

**Answer: we were detecting good market moments.**

**ZON-022 (the decisive test).** Isolated ZON-012 boundary first-touches (N=574, the deterministic
ZON-017 event set) vs **isolated non-ZON-012 areas at matched moments** (C2v2):
**Δ = −0.001 [−0.027, +0.026]** — the edge vanishes exactly when the control is forced to share
the isolation state. Meanwhile the same events still beat displaced strips (C1 +0.040 [+0.014,
+0.064], replicating ZON-017). Synthesis: at isolated moments price behaves better around its
current location than around nearby displaced strips **wherever it is** — with or without a
volume boundary there. ZON-017's +4% ADR was an isolation/moment context effect, not boundary
information. Yearly vs C2v2: 3/6 positive, all small. Control caveat: isolation-matched donors are
scarce (418/574 events got <5 donors; 494 events paired, mean 2.8 donors) → CI ±0.026; a residual
effect up to ~+0.025 cannot be excluded, but the point estimate is zero and the +0.05 materiality
bar is excluded.

**ZON-025 (generality).** Across the preregistered pool (frozen isolation rule, first touch,
strict lifecycle): isolated vs non-isolated raw outcomes are **flat in every family** —
ZON-001 +0.000 [−0.030, +0.030] · ZON-008 −0.022 [−0.056, +0.012] · ZON-009 +0.001 (n_iso=48) ·
ZON-011 −0.002 [−0.014, +0.009] · ZON-013 +0.001 [−0.037, +0.035] · ZON-015 unmeasurable
(isolated FVGs < 30 — family too dense). And the iso-vs-C1 pattern REPLICATES elsewhere:
ZON-011's isolated events beat their displaced strips +0.025 [+0.010, +0.040] — the same
neighborhood-vs-moment signature as ZON-017, in a family with NO edge vs matched moments.
Conclusion: **isolation is a general context feature** (isolated moments mean-revert to the
current location vs its neighborhood); it is not specific to volume boundaries and creates no
family-level location edge anywhere.

## Results table

| Hyp | N | Δ vs C1v2 [CI] | Δ vs C2v2 [CI] | Yrs +ve | Ev/day | Class |
|---|---|---|---|---|---|---|
| ZON-022 iso boundary vs iso context | 574 | +0.040 [+0.014, +0.064] | **−0.001 [−0.027, +0.026]** | 3/6 | 0.37 | **NO LOCATION EDGE** |
| ZON-023 strong departure | 7,031 | +0.005 [−0.003, +0.014] | **+0.011 [+0.005, +0.016]** | **6/6** | 4.58 | PROMISING |
| ZON-024 iso ∧ strong dep | 265 | +0.032 [−0.003, +0.066] | −0.030 [−0.068, +0.009] | 3/6 | 0.17 | INSUFFICIENT (N<300) |
| ZON-025 isolation generality | pool | see above | — | — | — | attribution: context-general, no family edge |

## Departure strength — formal result (ZON-023, discovery-inspired)

The Batch-3 descriptive flag survives formalization *partially*: strong-departure events
(dep ≥ 0.15·ADR pre-touch; 46% of parent events) beat isolation-matched moments **+1.1% ADR,
positive all six years** — the most stable C2-side result in the project — but do NOT beat their
own neighborhood (C1 +0.005, straddling), and the magnitude remains an order of magnitude below
the +5%-ADR materiality bar. It carries the same signature as its parent: a small, consistent,
context-flavored effect. Its threshold provenance (descriptive terciles) further discounts it.

## Combination (ZON-024)

Starved as predicted: 265 events (< 300 floor), C2v2 point NEGATIVE (−0.030) with violent yearly
swings — the two conditions do not stack; honestly INSUFFICIENT.

## Frequency of any survivor

Strong: **0/day** (nothing met the standard). The only PROMISING stream (ZON-023) runs 4.6/day at
+0.011 ADR/event — economically, ≈0.2 pt at ADR≈20, i.e. **at or below one round-trip of
GC spread+slippage**; it cannot be material even if it validates.

## Recommendation: **END THIS BRANCH**

1. The decisive attribution test is null: the project's best "location edge" is a context effect.
2. 25 hypotheses across 4 batches; nothing ever cleared both controls at material size; the
   largest surviving effects (+1% ADR) are smaller than GC round-trip friction — they cannot
   carry execution costs even if perfectly real and validated.
3. The protocol's stop rule (§F.22: several fundamentally different attempts failing ⇒ stop
   rather than endlessly tweak) is met several times over at the location stage alone.
4. Spending 2022–2023 validation on immaterial candidates would burn the last clean research data
   for no decision-relevant outcome. Recommended disposition: close the GC bounce/location-zone
   branch with an honest negative; 2022–2023 remains untouched for any future, genuinely
   different research direction (which per protocol would need new preregistration).

Alternative if the user still wants a validation shot: ZON-023 (and parent ZON-012) are the only
defensible candidates — with the explicit prior that even full replication leaves them below
economic materiality.

## Files
`aurum/batch4/`: batch4_stats.json, events/c1/c2v2 parquets for ZON-022/023/024, this report.
`tools/batch4/`: batch4_lib.py, run_batch4.py, test_parity_b4.py.
