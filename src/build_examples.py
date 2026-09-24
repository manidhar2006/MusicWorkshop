"""
Phase 5 prep: run the full pipeline (Phase 2 extraction -> Phase 3/4
sonification+rendering) across several records to build the paired
normal-vs-AFib example set for presentation.
"""
import csv
import os

from extract_features import process_record
from sonify import process as sonify_process

RECORDS = ([("afdb", r) for r in ["04043", "04015", "04126", "06995", "08455"]]
           + [("mitdb", r) for r in ["201", "202"]])
# mitdb record 219 was tried and excluded: its "N"-labeled segments have 133
# non-conducted P-wave events (genuine blocked atrial beats, not a detection
# artifact), making its ventricular rhythm genuinely irregular even though
# it isn't rhythm-labeled as one of the tracked arrhythmias. RMSSD stayed
# high (270ms) across every candidate window, so it wouldn't demonstrate
# "normal = calm" - a real patient-specific finding, not a bug. See
# PROGRESS.md's mitdb log entry.

SUMMARY_PATH = os.path.join(os.path.dirname(__file__), "..", "output", "examples_summary.csv")


def main():
    rows = []
    for db, record in RECORDS:
        print(f"\n=== {db}/{record} ===")
        try:
            clips = process_record(record, db=db)
        except Exception as e:
            print(f"  FAILED extracting {record}: {e} -- skipping this record entirely")
            continue

        for label in ("N", "AFIB"):
            if label not in clips:
                print(f"  skipping {record}/{label}: no qualifying segment")
                continue
            clip = clips[label]
            try:
                _, _, stats = sonify_process(record, label)
            except Exception as e:
                print(f"  FAILED sonifying {record}/{label}: {e} -- skipping")
                continue
            if stats is None:
                continue
            rows.append({
                "db": db,
                "record": record,
                "label": label,
                "rmssd_ms": round(clip["rmssd_sec"] * 1000, 1),
                "mean_rr_ms": round(clip["mean_rr_sec"] * 1000, 0),
                "n_notes": stats["n_notes"],
                "pitch_min": stats["pitch_min"],
                "pitch_max": stats["pitch_max"],
                "pct_chromatic": round(stats["pct_chromatic"], 0),
                "pitch_std": round(stats["pitch_std"], 1),
            })

    if not rows:
        print("\nNo examples were produced -- every record failed or had no qualifying "
              "segment. Nothing written.")
        return

    os.makedirs(os.path.dirname(SUMMARY_PATH), exist_ok=True)
    with open(SUMMARY_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote summary to {SUMMARY_PATH}")

    print("\n--- All examples ---")
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
