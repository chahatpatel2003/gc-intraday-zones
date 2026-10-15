#!/usr/bin/env python3
"""Build the SEALED holdout manifest.

Holdout market values are NEVER read. For GC holdout parquets, only the file
FOOTER metadata is touched, and only num_rows plus the ts_event column's
min/max statistics are extracted (date boundaries = metadata). Price/volume
statistics are never accessed. Raw .bi5 holdout files are content-hashed
(bytes -> sha256), which reveals nothing to the researcher.

Outputs:
  aurum/audit/holdout_manifest.json
  aurum/audit/hashes_gc_holdout.txt
  aurum/audit/hashes_xauusd_combined.txt
  aurum/audit/hashes_xauusd_raw_holdout.txt      (per-file, ~20k lines)
  aurum/audit/hashes_research_freeze.txt         (research-side provenance)
"""
import hashlib, json, os, sys
import pyarrow.parquet as pq

AUD = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "aurum", "audit"))
GC_HOLD = "/Volumes/T9/Gc:Xauusd/gc/Holdout"
GC_RES = "/Volumes/T9/Gc:Xauusd/gc"
XA_BASE = "/Volumes/T9/Gc:Xauusd/XAUUSD Data"
XA_RAW_HOLD = f"{XA_BASE}/raw/XAUUSD/Hold out"
SHADOWS = {
    "gc_desktop": os.path.expanduser("~/Desktop/gc DATA"),
    "xauusd_t9_data_dir": "/Volumes/T9/DATA/XAUUSD Data",
}

def sha256(path, bufsize=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(bufsize)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def gc_footer_bounds(path):
    """num_rows + ts_event min/max from footer statistics ONLY."""
    md = pq.ParquetFile(path).metadata
    idx = None
    for i in range(md.num_columns):
        if md.row_group(0).column(i).path_in_schema == "ts_event":
            idx = i
            break
    lo = hi = None
    if idx is not None:
        for rg in range(md.num_row_groups):
            st = md.row_group(rg).column(idx).statistics
            if st is None:
                continue
            lo = st.min if lo is None or st.min < lo else lo
            hi = st.max if hi is None or st.max > hi else hi
    return md.num_rows, str(lo), str(hi)

def main():
    man = {"sealed_utc_boundary": "2024-01-01T00:00:00Z",
           "rule": ("Everything at or after the boundary is SEALED for both "
                    "instruments. Research code must never read these paths, "
                    "and must filter mixed files to ts < boundary."),
           "gc_holdout_files": [], "xauusd_raw_holdout": {},
           "xauusd_mixed_files": [], "shadow_copies": {}, "notes": []}

    lines = []
    for fn in sorted(os.listdir(GC_HOLD)):
        p = os.path.join(GC_HOLD, fn)
        if not fn.endswith(".parquet"):
            continue
        rows, lo, hi = gc_footer_bounds(p)
        h = sha256(p)
        man["gc_holdout_files"].append(
            {"path": p, "bytes": os.path.getsize(p), "sha256": h,
             "rows_footer": rows, "ts_min_footer": lo, "ts_max_footer": hi})
        lines.append(f"{h}  {p}")
    open(f"{AUD}/hashes_gc_holdout.txt", "w").write("\n".join(lines) + "\n")

    # raw .bi5 holdout tree
    lines, nbytes, nfiles, nodata = [], 0, 0, 0
    for root, _, files in os.walk(XA_RAW_HOLD):
        for fn in sorted(files):
            p = os.path.join(root, fn)
            if fn.endswith(".nodata"):
                nodata += 1
            nfiles += 1
            nbytes += os.path.getsize(p)
            lines.append(f"{sha256(p)}  {p}")
    lines.sort(key=lambda s: s.split("  ", 1)[1])
    open(f"{AUD}/hashes_xauusd_raw_holdout.txt", "w").write("\n".join(lines) + "\n")
    agg = hashlib.sha256("\n".join(lines).encode()).hexdigest()
    man["xauusd_raw_holdout"] = {"root": XA_RAW_HOLD, "files": nfiles,
                                 "nodata_markers": nodata, "bytes": nbytes,
                                 "aggregate_sha256_of_hashlist": agg}

    # mixed (research+holdout) combined files — hashed, sealed-by-filter
    lines = []
    for fn in ("XAUUSD_1min.parquet", "XAUUSD_1min.csv"):
        p = f"{XA_BASE}/{fn}"
        h = sha256(p)
        man["xauusd_mixed_files"].append(
            {"path": p, "bytes": os.path.getsize(p), "sha256": h,
             "contains": "2021-06-29 .. 2026-06-28 (rows >= 2024-01-01 are SEALED)"})
        lines.append(f"{h}  {p}")
    open(f"{AUD}/hashes_xauusd_combined.txt", "w").write("\n".join(lines) + "\n")

    # shadow copies
    sh = {}
    d = SHADOWS["gc_desktop"]
    sh["gc_desktop"] = [{"path": os.path.join(d, fn),
                         "bytes": os.path.getsize(os.path.join(d, fn)),
                         "sha256": sha256(os.path.join(d, fn))}
                        for fn in sorted(os.listdir(d)) if fn.endswith(".parquet")]
    x = SHADOWS["xauusd_t9_data_dir"]
    sh["xauusd_t9_data_dir"] = [{"path": os.path.join(x, fn),
                                 "bytes": os.path.getsize(os.path.join(x, fn)),
                                 "sha256": sha256(os.path.join(x, fn))}
                                for fn in ("XAUUSD_1min.parquet", "XAUUSD_1min.csv")]
    xr = os.path.join(x, "raw", "XAUUSD", "Hold out")
    n, b = 0, 0
    for root, _, files in os.walk(xr):
        for fn in files:
            n += 1; b += os.path.getsize(os.path.join(root, fn))
    sh["xauusd_t9_data_dir_raw_holdout"] = {"root": xr, "files": n, "bytes": b}
    man["shadow_copies"] = sh

    # research-side provenance freeze
    lines = []
    for y in range(2016, 2024):
        p = f"{GC_RES}/gc_{y}.parquet"
        lines.append(f"{sha256(p)}  {p}")
    for fn in ("xauusd_dukascopy.py", "gaps_report.csv", "daily_counts.csv", "README.txt"):
        p = f"{XA_BASE}/{fn}"
        lines.append(f"{sha256(p)}  {p}")
    open(f"{AUD}/hashes_research_freeze.txt", "w").write("\n".join(lines) + "\n")

    # research raw structural fingerprint (counts only, no hashing of 40k files)
    for y in (2021, 2022, 2023):
        root = f"{XA_BASE}/raw/XAUUSD/{y}"
        n, b = 0, 0
        for r, _, fs in os.walk(root):
            for fn in fs:
                n += 1; b += os.path.getsize(os.path.join(r, fn))
        man["notes"].append(f"research raw {y}: {n} files, {b} bytes (not content-hashed)")

    with open(f"{AUD}/holdout_manifest.json", "w") as f:
        json.dump(man, f, indent=1)

    print("GC holdout files:")
    for e in man["gc_holdout_files"]:
        print(f"  {os.path.basename(e['path'])}: rows={e['rows_footer']:,} "
              f"{e['ts_min_footer']} -> {e['ts_max_footer']}")
    print(f"XAUUSD raw holdout: {nfiles} files, {nbytes/1e9:.2f} GB, "
          f"{nodata} nodata, agg={agg[:16]}…")
    same = (sh['gc_desktop'] and
            {e['sha256'] for e in sh['gc_desktop']} >=
            {e['sha256'] for e in man['gc_holdout_files']})
    print(f"desktop gc shadow contains identical holdout bytes: {same}")
    print("shadow xauusd combined matches:",
          {e['sha256'] for e in sh['xauusd_t9_data_dir']} ==
          {e['sha256'] for e in man['xauusd_mixed_files']})
    for n_ in man["notes"]:
        print(" ", n_)

if __name__ == "__main__":
    sys.exit(main())
