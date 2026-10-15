# GC Intraday Zones — research project
Status: **Phase 1 framework locked (zones, controls, ledger batch 1) — STOPPED before zone
backtests, awaiting user approval of the first batch.** No zone backtest has been run.

Primary instrument: GC futures (Databento GC.v.0, 1-min OHLCV bars — verified, nothing finer).
Secondary: XAUUSD Dukascopy (must prove incremental value for GC; not ground truth).
Canonical data: `/Volumes/T9/Gc:Xauusd/` (read-only by rule). No new data purchases.

Split (decided): discovery 2016–2021 · validation 2022–2023 · development/stress 2024 (gated) ·
**final holdout 2025** (sealed) · XAUUSD 2026 H1 sealed. Enforced in `tools/lib/gc_data.py`.

| File | Purpose |
|---|---|
| `RESEARCH_PROTOCOL.md` | Non-negotiable rules v1.1 (split §A0, zones-not-lines §A1, phase gate) |
| `ZONE_SPEC.md` | Canonical zone object, interaction vocabulary, reaction metrics, density metrics |
| `EVALUATION_FRAMEWORK.md` | Location-vs-timing design, C1/C2 controls, decision rule, dedup/clustering |
| `HYPOTHESIS_LEDGER.csv` | 6 batch-1 families preregistered (`planned`, awaiting approval) |
| `RESEARCH_SPLIT_PROPOSAL.md` | Decided split (binding) |
| `HOLDOUT_MANIFEST.md` | Seal at 2025-01-01 (amended); 2024 quarantined; hashes unchanged |
| `DATA_INVENTORY.md`, `DATA_QUALITY_REPORT.md` | Phase-0 audit results |
| `tools/lib/gc_data.py` (+`test_gc_data.py`) | Shared loader: phase guards, roll walls, session resampling, ADR14 — 27/27 self-tests pass |
| `tools/lib/news_calendar.py` | Point-in-time news-tagging interface (no data; acquisition needs approval) |
| `tools/audit/` | Phase-0 audit + `verify_gc_resolution.py` (GC = 1m bars, definitively) |
| `aurum/audit/` | Machine-readable audit outputs + seal hashes |

Pending user decisions: approve/modify batch-1 families (ZON-001…006) · confirm XAUUSD-2025
grouping with the final holdout · news-calendar acquisition (later) · role/protocol for 2024 (later).
