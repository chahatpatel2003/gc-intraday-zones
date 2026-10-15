# GC Intraday Zones: 44 Pre-Registered Tests of Supply/Demand-Style Zones in Gold Futures

Do the price "zones" that discretionary traders draw actually matter, beyond what random prices at the same distance would show? Examples are fair-value gaps, order blocks, quasimodo levels, value-area edges and failed-breakout traps.

This project tests that question for **COMEX gold futures (GC)** with a strict discovery protocol:

- zones are objects with boundaries, not lines;
- two independent controls;
- a sealed final holdout;
- a ledger entry for every hypothesis before it is run.

**44 zone hypotheses were registered and tested on the 2016–2021 discovery period.** 32 failed outright. A selection-bias null benchmark then showed that most small "edges" were indistinguishable from selection noise. Exactly one finding survived it.

| | |
|---|---|
| **Instrument** | GC futures, Databento `GC.v.0` 1-minute OHLCV (2016 → 2025); XAUUSD spot as a secondary check |
| **Stack** | Python 3.12, pandas, NumPy, PyArrow |
| **Scale** | 38 Python tools · 9 experiment batches · 44 ledgered hypotheses · a selection-bias null benchmark |
| **Tests** | loader self-tests (`tools/lib/test_gc_data.py`): the split and holdout-guard checks pass; data checks need the GC files |
| **Outcome** | 32 fail, 4 insufficient data, 1 context effect, 1 control failure. 1 finding (ZON-028) survives the null benchmark and remains frozen and unvalidated |

---

## Protocol

- **Splits fixed in advance**, enforced in `tools/lib/gc_data.py`:
  - discovery 2016–2021;
  - validation 2022–2023;
  - a gated 2024 stress period;
  - a **sealed final holdout for 2025**, with XAUUSD 2026-H1 also sealed.
- **Zones, not lines.** [`docs/protocol/ZONE_SPEC.md`](docs/protocol/ZONE_SPEC.md) defines the canonical zone object, interaction vocabulary, reaction metrics and density metrics. [`ZONE_LIFECYCLE.md`](docs/protocol/ZONE_LIFECYCLE.md) defines creation, activation, expiry and invalidation.
- **Two controls for every family**, in [`EVALUATION_FRAMEWORK.md`](docs/protocol/EVALUATION_FRAMEWORK.md):
  - **C1** asks whether the *location* beats shadow zones placed at matched distances;
  - **C2** asks whether the *timing* beats matched random moments.

  Results are reported as reaction differences in ADR units with confidence intervals and per-year signs.
- **Pre-registration.** Every batch has a frozen spec or plan in [`docs/batches/`](docs/batches/) written before outcomes, and every family has a row in [`HYPOTHESIS_LEDGER.csv`](HYPOTHESIS_LEDGER.csv). That row covers boundaries, width, activation and expiry rules, touch definition, controls, success criteria and multiplicity plan, then the result and verdict.
- **Rules of research conduct.** [`RESEARCH_PROTOCOL.md`](docs/protocol/RESEARCH_PROTOCOL.md) sets them out. Specs are never loosened after the fact: a rule that fires once a year is recorded as *insufficient data*, not redefined.

## Results

| Batch | Focus | Outcome |
|---|---|---|
| 1–2 | Classic families: prior-session extremes, round numbers, swing-pivot clusters, value-area edges, FVG, order blocks, sweeps, anchored-VWAP bands | Mostly **fail** against C1 or C2. ZON-012 (rolling 6-hour volume-concentration boundary) is the first to clear both controls, but below the materiality bar |
| 3–4 | Quality conditions and **attribution** (is it the zone, or the context?) | The isolated sub-family looked strongest (C1 +0.040 ADR), but the attribution test made the edge **vanish** against isolation-matched moments. It was a **context effect, not a zone effect** (ZON-022, ZON-025) |
| 5–6 | New structural families including quasimodo (QML) and its control repair | QML's C1 +0.101 was **structurally compromised**: 87 % self-overlap and 58 % uncontrolled zones. After repair, the branch was closed |
| 5 | **ZON-028, failed-breakout trap (30m)** | The only family to clear **both** controls with material size: C1 +0.053 [+0.027, +0.078], C2 +0.024 [+0.005, +0.044], positive in 5 of 6 years |
| null | Selection-bias benchmark ([report](aurum/nullbench/NULL_REPORT.md)) | Selection alone easily fakes relative edges of ≤ 0.01 ADR, so the ZON-012-class results are consistent with noise. **ZON-028's discovery signal is beyond selection noise.** The control method shows a 0 % false-family rate |
| 7–8 | Motif mining (mining window, then internal confirmation) and state vocabularies | **No survivor.** Mining-window edges shrank toward zero out of window, the signature of selection bias. No batch-8 finalist cleared +0.02 ADR against both controls |
| 9 | **Trade product**: zone + small 1-minute confirmation, 1R take-profit before stop-loss, 30 variants frozen in advance | **NO, and not close.** The best win rate was 49.4 % on 83 trades; every other variant scored 33–48 %, all with negative expectancy. Real setups did **worse than matched random entries**, because the confirmation consumes the bounce ([report](aurum/batch9/BATCH9_REPORT.md)) |

ZON-028 is deliberately **left frozen and unvalidated**. Its 2022+ validation and the sealed holdout have not been opened.

## Repository layout

```
├── TECHNICAL_README.md        original README (project status at framework lock)
├── HYPOTHESIS_LEDGER.csv      all 44 hypotheses: full spec, result summary, verdict
├── docs/
│   ├── protocol/              research protocol, evaluation framework, zone spec and lifecycle, split decision, holdout manifest, null plan
│   ├── data/                  Phase-0 data inventory and data-quality report
│   └── batches/               frozen batch specs and plans (2–9), ZON-034 spec, discovery observations
├── tools/
│   ├── lib/                   shared loader with phase guards, roll walls, session resampling, ADR14 (+ self-tests); news-calendar interface
│   ├── audit/                 Phase-0 audits, GC resolution check, holdout manifest builder
│   ├── batch1 … batch9/       zone generators and runners per batch
│   └── nullbench/             selection-bias null benchmark
└── aurum/                     results: audit outputs and seal hashes, per-batch reports and statistics, null-benchmark output
```

During migration the protocol, data and batch documents were moved from the repository root into `docs/` (contents unchanged). The tools mention these documents by name only, so no code was affected.

## Running it

```bash
git clone https://github.com/chahatpatel2003/gc-intraday-zones.git
cd gc-intraday-zones
python3.12 -m venv .venv && .venv/bin/pip install pandas numpy pyarrow
.venv/bin/python tools/lib/test_gc_data.py     # loader self-tests; the data-dependent checks need the GC files
```

**Data is not included.** The Databento GC bars and Dukascopy XAUUSD data are licensed, so they and all derived parquet files stay private. The runner scripts write their results into this repository's `aurum/` folder.

## Third-party material

- **Market data:** Databento GC 1-minute bars and Dukascopy XAUUSD (licensed; not included).
- **Published research cited** in the hypothesis ledger, e.g. Osler (2000), *Support for Resistance* (FRBNY Economic Policy Review).
- **Trading concepts:** zone families such as fair-value gaps, order blocks, quasimodo levels and value-area edges are publicly taught concepts, implemented here independently.
- **Open-source libraries** are installed as dependencies under their own licences; none are copied into this repository.

## Notes

- The original folder was named `long term bto`; results live in `aurum/`, the project's working name.
- Assembled on 2026-10-14. File contents are byte-identical to that snapshot (SHA-256 verified), except 21 files where a hardcoded local path was made portable without changing any logic: 2 documents, the generated holdout manifest, and 18 tool scripts.
- Research software only. Nothing here is investment advice.

© Chahat Patel. All rights reserved. This notice covers the original code, documentation and research results in this repository. It does not extend to the third-party material listed above, which belongs to its respective owners. No license to reuse this code is granted; it is published for review.
