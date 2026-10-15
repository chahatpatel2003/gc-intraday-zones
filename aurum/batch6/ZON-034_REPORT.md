# ZON-034 — QML CONTROL-REPAIR FOLLOW-UP RESULT (discovery 2016–2021)
Run 2026-08-16 · spec frozen pre-outcome (ZON-034_SPEC.md) · 4/4 parity checks PASS ·
QML geometry/lifecycle byte-identical to ZON-026 · the one allowed follow-up, now spent.

## Dedup effect
7,800 raw QML zones → **2,114 cluster representatives** (3.69 members/cluster, max 29).
Self-overlap 86.7% → 35.5%; NN spacing 0.022 → 0.14 ADR; independent stream 2.68 → **1.17
events/day** (30% of days none, 38% exactly one).

## Frozen availability gate: **FAILED**
C1 availability improved 0.67 → 1.43 shadows/zone and 58.4% → 30.8% uncontrolled — still below
the pre-committed standard (≥ 2.0 and ≤ 20%). QML areas remain intrinsically clustered even
one-per-structure (opposite-direction QMLs and adjacent clusters keep blocking the ladder).
Per the frozen rule: **UNRESOLVED/CONTROL FAILURE — no further control redesign permitted.**

## Outcome data (reported for completeness; the gate alone already closes the branch)
- vs C2 (trustworthy control): **−0.0196 [−0.0361, −0.0037]** — deduplicated QML areas perform
  WORSE than matched moments, **negative all six years** (2016 −0.056 … 2021 −0.005).
- vs C1 (still-selected 69%-covered sample): +0.043 [+0.017, +0.069] — the familiar
  neighborhood-vs-moment context signature, not location evidence.
- rejA 14.9%, traversal 58.7%, ambiguity 12.8%.

Batch-5's ZON-026 "PROMISING" label is hereby superseded: it was an artifact of the compromised
control plus the 3.7× duplicated universe. With one zone per physical area and its own honest
context control, QML carries **no location edge on GC — if anything the opposite sign**.

## Verdict: **CLOSE QML** (control failure by the frozen gate AND negative vs the matched-moment
control). No ZON-035, no alternative QML definitions, no timeframe changes.

## ZON-028 confirmation
Untouched throughout: frozen spec in BATCH5_SPECS.md (sha256 a642a9dc1d1eac90…), cached events
(sha256 9c7c11c32ccbaf8c…), ledger row `promising_pending_validation` unchanged. It remains the
sole validation candidate.
