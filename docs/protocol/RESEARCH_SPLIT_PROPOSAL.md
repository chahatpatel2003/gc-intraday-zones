# RESEARCH-DATA SPLIT — **DECIDED** (user, 2026-08-16)
History: audit proposed variants A/B; the user chose a modified B. This is now binding
(RESEARCH_PROTOCOL §A0) and enforced by `tools/lib/gc_data.py` phase guards (self-tested,
guards raise before any file I/O). **No new data purchases/downloads.**

| Window | Role | GC | XAUUSD | Loader phase / gate |
|---|---|---|---|---|
| 2016-01 → 2021-12 | **Discovery** (current) | ✓ | from 2021-06-29 | `discovery` — open |
| 2022-01 → 2023-12 | **Validation** | ✓ | ✓ | `validation` — frozen preregistered specs only |
| 2024-01 → 2024-12 | **Development / stress testing (later)** | ✓ | ✓ | `development_2024` — requires `allow_development=True` |
| 2025-01 → 2025-12 | **FINAL PROJECT HOLDOUT** | ✓ | ✓ | `final_holdout_2025` — requires flag + env `AURUM_FINAL_TEST=1`; opens once |
| 2026-01 → 2026-06 | **Sealed holdout** | (no GC data exists) | ✓ | no phase reaches it |

Usage rules:
- Discovery iterates freely inside 2016–2021; regime stability checks use sub-splits
  (2016–2018 vs 2019–2021) before promoting any family.
- Validation runs only frozen specs from the ledger; a spec changed after seeing validation
  results returns to discovery under a new ID.
- 2024's exact role (stress protocols, degradation tests) is specified later by the user —
  until then nobody reads it.
- 2025 opens once for the preregistered final test; XAUUSD 2026 H1 stays sealed beyond that
  (available as an optional post-project honesty check on the XAUUSD side only, if the user
  ever chooses).
- Contamination disclosure carried forward from the audit: prior Phase 57 (different project)
  backtested strategy families on GC through 2025; AURUM studied spot gold through 2024.
  Recorded in HOLDOUT_MANIFEST §6; final-test claims must repeat this caveat.
