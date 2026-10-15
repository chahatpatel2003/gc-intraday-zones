# BATCH 9 — TRADE-PRODUCT PHASE: 1R TP-BEFORE-SL (frozen BEFORE any outcome)
Frozen 2026-08-16. 2016–2019 discovery · 2020–2021 frozen internal confirmation · 2022+ untouched.
ZON-028 not reopened; closed branches not restarted. No ML, no overlays, no threshold sweeps.
Question: can a valid GC zone + a SMALL causal 1m confirmation produce ≥60–70% TP-before-SL at 1R
with a small stop, positive net expectancy, and useful frequency?

## Three separated concepts (enforced in code)
**A. Structural zone validity** — family lifecycle unchanged (source-TF close beyond distal /
traversal / expiry / roll). A stopped trade does NOT delete the zone.
**B. Trade eligibility** — max 1 trade attempt per zone (first eligible interaction; after it,
trade_eligible=false regardless of outcome). A pending confirmation is CANCELLED if any 1m close
beyond the distal edge occurs before entry (trade-level cancel; zone's structural life continues
per its own rules).
**C. Trade stop** — SL = 1 tick beyond the distal boundary; a wick to SL loses the trade without
structurally invalidating the zone.

## Zone families (6) — selection rule: highest-frequency representative of each structural class
from existing frozen geometries (frequency + mechanical clarity + diversity; NOT historical
performance): F1 15m FVG (imbalance) · F2 rolling-6h VA boundary (volume distribution) ·
F3 5m compression box (volatility) · F4 30m rejection tail (wick rejection) · F5 NR7 box
(compression-release) · F6 30m volume climax (volume extreme). Exact existing geometry/lifecycle;
strict first-touch primary events, within-family dedup. Trade direction = AWAY from the zone
(fade the touch): approach from above → long; from below → short.

## Confirmations (frozen; identical for all families; entry always next 1m open + 1 tick adverse)
C0 none: enter at open(T0+1). C1 reclaim: first bar in [T0 … T0+4] CLOSING beyond the proximal
edge in trade direction → enter next open. C2 touch-bar rejection: T0 itself closes out of the
zone in trade direction → enter open(T0+1). C3 micro break: first bar in [T0+1 … T0+5] closing
beyond the touch bar's extreme (trade direction) → next open. C4 displacement: first bar in
[T0+1 … T0+5] with body ≥ 1.5× median body of its prior 20 completed 1m bars, directional, closing
beyond the proximal edge → next open. Cancel any pending confirmation on the eligibility rule
above or window end (missed setup, counted).

## Stop / target / label / costs (frozen)
SL = distal edge ∓ 1 tick. R = |entry − SL|; primary gate **R ≤ 0.10·ADR14** else STOP_TOO_LARGE
(excluded from the primary product, occurrence reported). TP = 1R (primary; 1.5R/2R descriptive
only). First passage from the entry bar (its post-open extremes included): TP touched first → WIN;
SL touched first → LOSS; **both inside one 1m bar → LOSS (+ambiguous)**; neither in 120 bars →
TIMEOUT (exit at close −1 tick). Net P&L: win +R − 0.05 comm; loss −R − 0.1 slip − 0.05; timeout
marked-to-market −0.1 − 0.05. WR = wins/(wins+losses+timeouts). Entry slippage lives in the entry
price. No perfect fills; no intrabar inference; no XAUUSD tick inference.

## Budget: exactly 6×5 = **30 predefined variants**. No additions without stopping.

## Matched best-of-30 null (this experiment's selection hurdle; previous null untouched)
50 tournaments × 30 zero-information variants: random eligible 1m entries (nullbench universe,
2016–2019), frequency matched per-variant to the real variants' trade counts, coin-flip direction,
stop distance ~ U(0.03, 0.10)·ADR beyond entry, TP = 1R, identical passage/cost/timeout rules.
Report distribution of the best-of-30 WR / net expectancy / PF (median, p95, p99). Real finalists
must materially exceed the p95 hurdle.

## Frozen selection & confirmation standards
Discovery finalist rule: eligible iff WR ≥ 60%, net expectancy (R units) > 0, trades/day ≥ 0.5
(≥1 preferred), ambiguity ≤ 15%, WR > matched-null p95; rank eligible by net expectancy in R;
top ≤ 3 → frozen finalists. Confirmation (2020–2021, unchanged): prefer WR ≥ 60% combined, both
years supportive, positive net expectancy, frequency, small stops intact. No rescue, no filters,
no month deletion. If several survive: cross-family deduplicated combined stream (30-trading-min
+ price-overlap rule) targeting 2–5 setups/day. If nothing survives: reported cleanly.
