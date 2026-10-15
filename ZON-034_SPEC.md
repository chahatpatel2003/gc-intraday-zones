# ZON-034 — QML CONTROL-REPAIR FOLLOW-UP (the ONE allowed follow-up for ZON-026)
Frozen 2026-08-16 BEFORE any ZON-034 outcome. Not a new QML definition.

## What is unchanged (identical to ZON-026, byte-for-byte)
QML structure (pivot-H1 → pivot-L1 → sweep beyond h1 → 30m close beyond l1, mirrored), 30m source
TF, zone boundaries ([h1, sweep-phase extreme] with 0.05·ADR floor / 0.5·ADR cap), creation at the
structural-break close, activation +1s, invalidation (30m close beyond distal), expiration
(10 sessions), first-touch-only, max touches = 1, reclaim = new zone ID only, roll death,
reaction metrics (ZONE_SPEC v1.1), episode engine, horizons, seed.

## The ONLY change — frozen generation-time dedup/clustering rule
Zones are processed chronologically by activation (ties by zid; deterministic). A list of ACTIVE
cluster representatives is maintained (representatives whose [act, exp) still overlaps the new
zone's activation, same contract segment). A new zone is SUPPRESSED as a member of an existing
cluster iff an active representative exists with: **same segment AND same direction (btype) AND
[price-interval IoU ≥ 0.5 OR |midpoint difference| ≤ 0.5·max(W_new, W_rep)]**. Otherwise it
becomes a new cluster representative. The representative keeps its own boundaries and lifecycle
(earliest structure = the physical QML area; no mutation, no extension by members, no reactions
consulted). Member metadata preserved (cluster id, member count, member zids). A cluster whose
representative dies does not resurrect — a later similar sequence forms a NEW representative
(new zone ID), consistent with reclaim-as-new-ID. Inputs to the rule are creation-time only:
price overlap, boundary similarity, direction/segment (source-structure relationship), timing.

## Lifecycle record (user requirement)
CREATED: structural-break 30m close completes the sequence (all pivots causally confirmed, sweep
and break observable). VALID/ACTIVE: creation close +1s (for representatives; suppressed members
never activate). Stays valid: LIVE (no 30m close beyond distal, no full traversal, not expired,
same contract). First touch: ZONE_SPEC canonical (inside-at-activation contacts consume no index).
Mitigation: full traversal → dead. Invalidation: 30m close beyond distal → dead. Expiration:
10 sessions. Roll: death. Max touches: 1. Reclaim: new zone ID only. No future information, no
backdating; a future reaction can never validate a zone or select a cluster representative.

## Controls
C1v2 rebuilt on the DEDUPLICATED universe (nearest-eligible strips: same width/timestamps/segment,
ladder 2–12W within 1.0·ADR, no overlap with any active real QML cluster representative — the
same-family exclusion now references clusters). C2 unchanged except cluster identity replaces
raw-zone identity in its exclusion. **Frozen availability standard (decided pre-outcome): C1 is
healthy iff shadows/zone ≥ 2.0 AND zones-without-control ≤ 20%. If availability remains below
this after dedup, the QML branch is classified UNRESOLVED/CONTROL FAILURE and CLOSED — the control
will not be redesigned again.**

## Success standard
KEEP FOR VALIDATION only if: positive vs BOTH controls with CIs supporting a genuine effect,
meaningful magnitude, reasonable yearly stability, useful independent frequency, healthy control
availability. No filters, no geometry changes, no further follow-ups. ZON-028 remains frozen and
untouched throughout.
