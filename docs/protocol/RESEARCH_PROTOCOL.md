# RESEARCH PROTOCOL — GC intraday zones
Version 1.1 · Locked 2026-08-16 · Changes require explicit user approval + dated changelog entry.
These rules are **non-negotiable** for every script, notebook, and analysis in this project.

## A0. Decided data split (user decision, 2026-08-16) — enforced in `tools/lib/gc_data.py`

| Window | Role | Access |
|---|---|---|
| 2016–2021 | **Discovery** | open (current phase) |
| 2022–2023 | **Validation** | preregistered confirmation runs only |
| 2024 | **Development / stress testing (later)** | locked behind `allow_development=True`; do not open during discovery/validation |
| 2025 (GC + XAUUSD) | **PROJECT HOLDOUT — PRIOR-RESEARCH CONTAMINATED** (final stress test; NOT virgin — prior unrelated GC research touched it; conclusions must say so) | sealed; opens once via `allow_final_holdout=True` + env `AURUM_FINAL_TEST=1` |
| 2026 H1 (XAUUSD) | **Sealed holdout** | no phase reaches it |

No new market data may be bought or downloaded; the project runs on the existing GC and XAUUSD
datasets only. XAUUSD phase windows mirror GC on the overlap (XAUUSD starts 2021-06-29).

## A1. Zones, not lines — and location before execution

Every candidate is a **price area with an explicit upper and lower boundary** per ZONE_SPEC.md:
reproducible rules for zone high/low/mid, width, creation timestamp, source timeframe (≥ 5m),
type/direction, activation, expiration/invalidation, and mutation policy. Historical zone
behavior must equal live behavior exactly (no future-adjusted or backdated boundaries).
**Current phase = zone-location research only** (EVALUATION_FRAMEWORK.md). Until the user
promotes the phase, it is forbidden to test: confirmations, entry triggers, sub-5m execution,
TP/SL combinations, RR, position sizing, complete strategies, or ML. Width is part of each
hypothesis: defined before testing, never silently optimized; each materially different width
rule is a separate ledger row; no clouds of tiny width variants.

## A. Labels & outcomes

1. **Exact TP-before-SL first passage, never "eventual reaction".** An interaction outcome is decided
   by which bracket side is crossed first on the finest available price path from the entry-decision
   timestamp forward. "It bounced eventually" is not an outcome.
2. **Highest available resolution for labels.** GC: 1-min bar paths (finest owned). XAUUSD: raw ticks
   when the label needs them. If TP and SL both lie within one GC 1-min bar's range, the label is
   **SL-first (worst case)** AND the event increments the config's **ambiguity counter**. Every result
   table must report its ambiguity rate; conclusions about stops tighter than the typical 1-min range
   are invalid by construction.
3. **Stop tolerance is built into the label.** Labels are defined on a preregistered bracket grid
   (stop distance × target distance × max horizon), not inferred post-hoc. Win rate alone is never a
   result; **expectancy/RR (after costs) with uncertainty is the unit of evidence**.
4. **Reaction ≠ capturable trade.** Any claimed edge must survive the full chain:
   location → observable trigger → realistic fill → bracket outcome after costs.

## B. Leakage & timing

5. **No future leakage of any kind.** A feature/level value may only use data with timestamps
   ≤ its stated availability time. Bar data availability = bar close (bar-open ts + TF) + a modeled
   processing latency (default 1 s, sensitivity-checked).
6. **Level lifecycle is causal.** A level exists only from the moment its defining pattern is complete
   and observable live; broken/invalid state changes only at the first live-observable crossing
   (lesson imported from the NQ-levels project, where backdated broken-state was a real bug class).
7. **No immature prior-outcome features.** Any feature summarizing a level's past interactions may
   only include interactions whose own outcomes were decided before the current timestamp.
8. **Research = streaming.** Every level/feature computation must produce identical output when run
   on truncated data ending at time T and on full data sliced at T. A parity harness test is required
   before any statistic from that computation is trusted.
9. **Point-in-time discipline extends to everything** — session templates, rolling stats, calendars.
   News/economic-calendar work (later) must use point-in-time availability, never revised history.

## C. Market/data structure (from the audit)

10. **GC rolls are structural events.** Continuous GC.v.0 is volume-rolled, NOT back-adjusted
    (median 5.9 pt artificial jump, max 38.2 pt, ~5 rolls/yr; `instrument_id` change = roll).
    Levels/features must be roll-aware: recompute per contract segment, apply a documented
    project-built adjustment, or invalidate at the roll — chosen per level family and preregistered.
    Roll windows also carry thin-liquidity data holes (worst: session 2020-02-28 missing entirely);
    every event row carries a data-coverage flag.
11. **"No bar" ≠ "no market".** GC 1-min bars are trade-driven; ~1.7% of session minutes are absent
    (zero trades). A touch is observable only at traded prices. Time-window logic must tolerate
    missing minutes.
12. **Unit traps are documented and tested:** XAUUSD parquet timestamps are datetime64[**us**];
    GC datetime64[ns]; both bar-OPEN stamped; XAUUSD prices are BID-based; XAUUSD volume is broker
    notional (millions), GC volume is contracts.

## D. Execution realism

13. **Costs from day one, on every result ever shown:** GC/MGC defaults — spread+aggression ≥ 1 tick
    (0.1 pt) per side, slippage 1 tick per side on stop/market exits (2 ticks on news-minute fills),
    commission $1.48 RT (MGC) / $5.00 RT (GC) — sensitivity at 2× costs mandatory. XAUUSD defaults —
    observed spread (median ≈ $0.33) + $0.10 slippage per side. Free-of-cost numbers may appear only
    next to the after-cost numbers, never alone.
14. **No perfect-limit-fill assumption.** Baseline fill model: stop/market through the level with
    adverse slippage; a limit fill may be assumed only when the path traded THROUGH the limit price
    (price beyond limit), never on a touch.
15. **Four edges are measured separately and never conflated:**
    (1) location edge — does price behave non-randomly at the level at all;
    (2) confirmation/entry edge — what a live trigger captures;
    (3) exit edge; (4) execution edge (fills/slippage).
    **Favorable movement consumed before confirmation is always measured** — a location edge that
    evaporates by trigger time is reported as exactly that.

## E. Statistics & independence

16. **Deduplicate overlapping levels and correlated opportunities.** Overlapping/nested levels from
    multiple TFs that produce the same touch cluster into ONE independent event (clustering rule
    preregistered per family). Counts reported = independent events, never raw signal rows.
17. **Level density and spacing are first-class metrics** (levels/day, spacing distribution vs
    typical bar range and bracket size). A level type that plasters the chart is unfalsifiable and fails.
18. **Statistical significance ≠ profitability.** Both are required, separately: after-cost
    expectancy CIs (block bootstrap by session) AND economic materiality vs costs.
19. **Multiplicity is tracked, not hand-waved.** Every hypothesis/variant/filter/threshold run is a
    ledger row BEFORE results are viewed; families of related tests carry a stated selection plan;
    no post-hoc rule selection. If it isn't in the ledger, its result does not exist.
20. **Development periods stay separated** per the decided split (§A0): discovery (2016–2021) may
    iterate freely; validation (2022–2023) only confirms frozen, preregistered specs — a spec
    altered after seeing validation results returns to discovery under a new ID; 2024 is reserved
    for later development/stress testing; the sealed holdout (2025; XAUUSD 2026 H1) is used ONCE
    for the preregistered final test.

## F. Modeling discipline

21. **Mechanical baseline first.** A fixed-rule, parameter-light baseline must clear costs before any
    ML is permitted. **ML cannot rescue a weak baseline** — it may only refine an already-positive
    mechanical edge, under the same leakage/ledger rules.
22. **Stop condition.** If **4 fundamentally different monetization families** (not parameter
    variants) fail honest validation, the project stops with a negative result rather than
    endlessly tweaking. (Precedent honored: prior NQ/gold projects closed on honest negatives.)

## G. Scope & instruments

23. GC is the primary instrument. XAUUSD may be researched later only as confirmation/divergence/
    relative displacement/lead-lag/cross-market structure/context for GC, must prove **incremental
    value for GC**, and is never treated as ground truth for GC (broker-based spot feed). The
    project does not migrate to XAUUSD merely because its data is higher resolution.
24. Zone-generation timeframes: **5m minimum** (then 15m/30m/1h/4h/daily+). **No zone may originate
    below 5m.** Sub-5m data may be used only later for confirmation/execution studies and for
    label paths.
25. Deliverable target: zone definitions strong enough to be marked by an indicator; usefulness
    target ~2–5+ strong GC zone opportunities/day **if the data supports it** — density is
    measured (ZONE_SPEC §5), never forced.
26. **Roll boundaries are hard walls** (loader-enforced): no zone, swing structure, FVG, QML,
    statistical window, VWAP-derived structure, or rolling calculation may unknowingly cross an
    `instrument_id` change; artificial roll gaps must never generate zones.
27. **External research** (SSRN/arXiv/journals/microstructure/quant/institutional) may seed
    hypotheses; every external idea gets a ledger row with its source BEFORE testing; no
    literature-driven mass parameter searches.
28. **News:** infrastructure only for now (`tools/lib/news_calendar.py`, point-in-time schema).
    Zones will later be analyzed under normal / pre-news / release / post-news buckets; nothing is
    optimized on news yet; actual/revised figures never leak before their release timestamps.
    Acquiring a historical calendar requires user approval (no downloads).

## H. Ledger mechanics (HYPOTHESIS_LEDGER.csv)

One row per experiment, written BEFORE the experiment runs. **No undocumented experiments; no
post-hoc parameter changes without a new ID.** Fields:
`id` (ZON-###), `registered_utc`, `phase`, `status` (planned/running/done/abandoned),
`instrument`, `zone_family`, `source` (origin of the idea, incl. citation if external),
`source_timeframes`, `boundary_construction` (exact zone-high/low rule),
`width_rule`, `creation_rule`, `activation_rule`, `expiration_invalidation_rule`,
`touch_definition`, `reaction_definitions`, `controls`, `filters`,
`dedup_rule`, `test_period`, `expected_n_events`, `primary_metric`,
`success_criteria` (declared in advance), `multiplicity_plan`,
`parent_id` (lineage of every tweak), `reason` (why this experiment now),
`result_summary` (filled after), `verdict` (pass/fail/insufficient_data/inconclusive), `notes`.

*Changelog:*
1.0 (2026-08-16) initial lock.
1.1 (2026-08-16) user decisions applied: split decided (§A0, no new data purchases); zones-not-lines
+ phase gate (§A1); XAUUSD role tightened (§23); roll walls (§26); external research (§27);
news infrastructure (§28); ledger fields restructured for zone research (§H).
1.2 (2026-08-16, pre-run) Batch-1 approval corrections: 2025 renamed PROJECT HOLDOUT —
PRIOR-RESEARCH CONTAMINATED (§A0; never called virgin); reaction metrics de-width-biased
(ZONE_SPEC v1.1 §4: dual unit systems, fixed 5/15/30/60/120 trading-min horizons); point→zone
conversion made an explicit documented assumption (ZONE_SPEC §3b); two-layer dedup with mandatory
cross-family interaction_cluster_id (EVALUATION_FRAMEWORK v1.1 §5); C1/C2 control validity rules
tightened (EVALUATION_FRAMEWORK §3). Batch 1 (ZON-001…006) approved to run on discovery
2016–2021 GC only.
