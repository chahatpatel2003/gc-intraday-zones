# HOLDOUT MANIFEST — STATUS: **SEALED** (amended per user split decision)
Sealed: 2026-08-16 · **Sealed boundary: 2025-01-01 00:00 UTC.**
2025 (GC + XAUUSD) = **PROJECT HOLDOUT — PRIOR-RESEARCH CONTAMINATED** (user terminology decision):
completely inaccessible during discovery/validation, usable later as a final project **stress
test**, but **never to be described as virgin/unseen** — prior unrelated GC research (Phase 57)
touched 2025, and any conclusion drawn on it must state that it is not genuinely unseen to the
researcher. XAUUSD 2026 H1 remains sealed with no opening phase. **2024 is UNSEALED but
QUARANTINED** — reserved for later development/stress testing, locked in the loader behind
`allow_development=True`, and must not be opened during discovery/validation.
Machine-readable: `aurum/audit/holdout_manifest.json` · Hash lists: `aurum/audit/hashes_*.txt`

**Seal rule.** No research code, notebook, or analysis may read sealed data (≥ 2025-01-01, plus all
XAUUSD 2026), nor quarantined 2024 data outside an approved development phase, until the
pre-registered final stress test (2025; opens once via `allow_final_holdout=True` +
env `AURUM_FINAL_TEST=1`).
Boundaries were established from **filenames, folder structure, and parquet footer/timestamp
metadata only**; no holdout market values (prices/volumes) were read, computed on, or summarized.
Holdout results are never used to invent, select, or modify hypotheses.

## 1. GC sealed files — `/Volumes/T9/Gc:Xauusd/gc/Holdout/`

| File | Rows (footer) | Coverage (footer ts only) | sha256 (first 16) |
|---|---|---|---|
| gc_2024.parquet | 351,320 | 2024-01-01 23:00 → 2024-12-31 21:59 UTC | see hashes_gc_holdout.txt |
| gc_2024_jan.parquet | 28,098 | duplicate Jan-2024 subset of gc_2024 | see hashes_gc_holdout.txt |
| gc_2025.parquet | 350,874 | 2025-01-01 23:00 → 2025-12-31 21:59 UTC | see hashes_gc_holdout.txt |

## 2. XAUUSD mixed files (research + holdout in one file) — sealed **by loader filter**

`XAUUSD_1min.parquet` and `XAUUSD_1min.csv` span 2021-06-29 → 2026-06-28. Every load goes through
`tools/lib/gc_data.py::load_xauusd_1m`, which applies the current phase's window as a pyarrow
predicate at read time (discovery < 2022-01-01; validation < 2024-01-01; development 2024 gated;
2025 final-holdout gated; 2026 unreachable). Rows beyond the allowed window are mechanically
discarded, never inspected. Both files sha256-frozen (`hashes_xauusd_combined.txt`).

## 3. XAUUSD raw tick holdout — `.../XAUUSD Data/raw/XAUUSD/Hold out/{2024,2025,2026}`

18,720 files · 730,187,101 bytes · 4,002 `.nodata` markers · per-file sha256 in
`hashes_xauusd_raw_holdout.txt` · aggregate sha256-of-hashlist `bf6edd498b610368…` (full value in JSON).

## 4. Shadow copies (byte-identical, sealed by the same rule)

- `~/Desktop/gc DATA/` — all 11 GC parquets incl. the three holdout files (sha256 match verified).
- `/Volumes/T9/DATA/XAUUSD Data/` — full duplicate of the XAUUSD dataset incl. `Hold out` raw tree
  (combined-file sha256 match verified; raw tree same file count/bytes).
Recommendation: leave untouched; research loaders whitelist only the canonical paths in
`/Volumes/T9/Gc:Xauusd/` and never these.

## 5. Research-side provenance freeze

sha256 of the 8 GC research parquets + `xauusd_dukascopy.py`, `gaps_report.csv`, `daily_counts.csv`,
`README.txt` recorded in `hashes_research_freeze.txt` (detects any silent modification of research
inputs mid-project).

## 6. Honesty disclosure — how "untouched" this holdout really is

- **GC 2024–2025:** used by the prior Topstep **Phase 57** study (15 strategy families backtested over
  full 2016–2025, incl. PDH/PDL/VWAP/POC families; summary stats were published in that repo and have
  been read by the researcher/agent). ⇒ *Not virgin.* Sealing still has value (no level-research
  fitting has touched it), but final-test claims must carry this caveat.
- **XAUUSD 2024:** gold-2024 (different dataset, same market) was researched in AURUM. Same caveat class.
- **XAUUSD 2025:** sealed discipline in AURUM; this download itself post-dates AURUM. Near-virgin.
- **XAUUSD 2026-H1:** post-dates every prior project; no consumers found. **Virgin.**
- **GC 2026:** does not exist on disk — acquiring it (decision D2) would create the only truly virgin GC period.

## 7. Amendment rule

The manifest may be amended only BEFORE any zone research begins and only by explicit user decision.
Once discovery starts, the seal may only tighten, never loosen. Any amendment appends a dated
changelog entry here.

*Changelog:*
- 2026-08-16 — initial seal at 2024-01-01 boundary matching the user's physical file arrangement.
- 2026-08-16 (before any research) — **user decision:** 2024 (GC `Holdout/gc_2024.parquet` +
  `gc_2024_jan.parquet`, XAUUSD 2024 rows/raw) reclassified from sealed → **development/stress
  reserve**, loader-gated; sealed boundary moves to **2025-01-01**; GC+XAUUSD 2025 = final project
  holdout; XAUUSD 2026 H1 = sealed with no opening phase; **no new data may be bought/downloaded**.
  Physical files stay exactly where they are on T9 (T9 is treated read-only — no moves); all
  hashes from the initial seal remain valid and binding. Access control is enforced purely by
  `tools/lib/gc_data.py` phase guards (self-tested).
