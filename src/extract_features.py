"""
Phase 2: extract R-peaks and rhythm labels from downloaded PhysioNet data,
compute R-R interval series and RMSSD, and isolate one normal-rhythm clip
and one AFib clip to carry into Phase 3 (the sonification mapping).

Two database layouts are supported (confirmed by direct inspection):

  afdb (MIT-BIH Atrial Fibrillation Database):
    <record>.qrs - beat annotations: one entry per detected R-peak. This is
                   an UNAUDITED automatic detector, not manually verified.
    <record>.atr - rhythm annotations: one entry per rhythm *change*, with
                   aux_note like '(N' (normal sinus rhythm), '(AFIB'
                   (atrial fibrillation), '(AFL' (atrial flutter). Each
                   label applies from its sample until the next one.
                   This file IS cardiologist-verified.

  mitdb (MIT-BIH Arrhythmia Database):
    <record>.atr - a single file carrying both: beat-by-beat annotations
                   (symbol = beat type, e.g. 'N' normal, 'V' PVC - these
                   ARE manually verified, unlike afdb's .qrs) and rhythm
                   change markers (symbol == '+', aux_note like '(AFIB',
                   same convention as afdb's rhythm labels).
"""
import os

import numpy as np
import matplotlib.pyplot as plt
import wfdb

DATA_ROOT = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
PLOT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")

CLIP_DURATION_SEC = 30

# Standard MIT-BIH beat annotation codes (actual QRS/beat events) - excludes
# rhythm-change markers ('+'), signal-quality markers ('~'), and other
# non-beat annotations.
BEAT_SYMBOLS = set("NLRBAJSVrFejnE/fQ")


def rhythm_intervals(samples, aux_notes, total_samples):
    """Turn point-in-time rhythm change labels into [start, end, label) intervals."""
    intervals = []
    for i, (start, label) in enumerate(zip(samples, aux_notes)):
        end = samples[i + 1] if i + 1 < len(samples) else total_samples
        intervals.append((int(start), int(end), label.strip("(").strip("\x00").strip()))
    return intervals


def load_beats_and_rhythms(record_path, db):
    """Returns (beat_samples, intervals, fs, total_samples) using the
    annotation layout appropriate to `db` ("afdb" or "mitdb")."""
    header = wfdb.rdheader(record_path)
    fs = header.fs
    total_samples = header.sig_len

    if db == "afdb":
        qrs = wfdb.rdann(record_path, "qrs")
        atr = wfdb.rdann(record_path, "atr")
        beat_samples = qrs.sample
        intervals = rhythm_intervals(atr.sample, atr.aux_note, total_samples)
    elif db == "mitdb":
        atr = wfdb.rdann(record_path, "atr")
        beat_mask = np.array([s in BEAT_SYMBOLS for s in atr.symbol])
        beat_samples = atr.sample[beat_mask]
        rhythm_mask = np.array([s == "+" for s in atr.symbol])
        rhythm_idx = np.where(rhythm_mask)[0]
        intervals = rhythm_intervals(
            atr.sample[rhythm_mask], [atr.aux_note[i] for i in rhythm_idx], total_samples)
    else:
        raise ValueError(f"unknown database: {db!r} (expected 'afdb' or 'mitdb')")

    return beat_samples, intervals, fs, total_samples


def rr_intervals(peak_samples, fs):
    """R-R intervals in seconds from a sorted array of R-peak sample indices."""
    return np.diff(peak_samples) / fs


def rmssd(rr):
    """Root mean square of successive differences between R-R intervals."""
    diffs = np.diff(rr)
    return float(np.sqrt(np.mean(diffs ** 2))) if len(diffs) > 0 else float("nan")


def find_clip(intervals, label, duration_sec, fs, qrs_sample=None, prefer=None, n_windows=5):
    """Pick a `duration_sec`-long window labeled `label`.

    The afdb rhythm labels (.atr) are cardiologist-verified, but the R-peak
    beat annotations (.qrs) are an unaudited automatic detector - it can
    jitter/misfire even inside a correctly-labeled segment, which inflates
    RMSSD with detector noise rather than real physiology. If `qrs_sample`
    and `prefer` are given, several candidate windows across all qualifying
    intervals are scored and the best one is picked instead of just the
    first: prefer="min_rmssd" picks the lowest-RMSSD window (appropriate for
    "N" - true normal sinus rhythm should be low-variability, so a high
    RMSSD there is almost certainly a detection artifact), prefer="most_beats"
    picks the window with the most detected beats (appropriate for "AFIB" -
    favors reliable detection density without cherry-picking for the most
    dramatic irregularity).
    """
    needed = int(duration_sec * fs)

    if qrs_sample is None or prefer is None:
        for start, end, lbl in intervals:
            if lbl == label and (end - start) >= needed:
                return start, start + needed
        return None

    candidates = []
    for start, end, lbl in intervals:
        if lbl != label or (end - start) < needed:
            continue
        span = end - start - needed
        n = min(n_windows, span // needed + 1) if span > 0 else 1
        offsets = np.linspace(0, span, n).astype(int) if span > 0 else [0]
        for off in offsets:
            clip_start, clip_end = start + int(off), start + int(off) + needed
            peaks = qrs_sample[(qrs_sample >= clip_start) & (qrs_sample < clip_end)]
            rr = rr_intervals(peaks, fs)
            if len(rr) < 5:
                continue
            candidates.append((rmssd(rr), len(peaks), clip_start, clip_end))

    if not candidates:
        return None
    key = (lambda c: c[0]) if prefer == "min_rmssd" else (lambda c: -c[1])
    candidates.sort(key=key)
    _, _, clip_start, clip_end = candidates[0]
    return clip_start, clip_end


def build_clip(record_path, pn_dir_unused, clip_start, clip_end, qrs_sample, fs, label):
    signal_record = wfdb.rdrecord(record_path, sampfrom=clip_start, sampto=clip_end)
    peaks_in_clip = qrs_sample[(qrs_sample >= clip_start) & (qrs_sample < clip_end)]
    peaks_relative = peaks_in_clip - clip_start
    rr = rr_intervals(peaks_in_clip, fs)

    return {
        "label": label,
        "fs": fs,
        "signal": signal_record.p_signal[:, 0],
        "sig_name": signal_record.sig_name[0],
        "peaks_relative": peaks_relative,
        "rr_intervals_sec": rr,
        "rmssd_sec": rmssd(rr),
        "mean_rr_sec": float(np.mean(rr)) if len(rr) else float("nan"),
        "n_beats": len(peaks_in_clip),
    }


def plot_clip(record, clip, out_path):
    fig, ax = plt.subplots(figsize=(10, 3))
    t = np.arange(len(clip["signal"])) / clip["fs"]
    ax.plot(t, clip["signal"], linewidth=0.8)
    ax.plot(clip["peaks_relative"] / clip["fs"], clip["signal"][clip["peaks_relative"]],
            "rx", markersize=5, label="R-peak")
    ax.set_title(f"{record} - {clip['label']} clip - RMSSD={clip['rmssd_sec']*1000:.1f}ms, "
                 f"mean RR={clip['mean_rr_sec']*1000:.0f}ms")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude (mV)")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved plot to {out_path}")


def process_record(record, db="afdb"):
    """Extract normal + AFib clips for one record. Returns {label: clip_dict}
    for whichever of the two labels had a long-enough interval (may be empty
    or missing one label if the record doesn't contain it).

    Assumes record IDs are unique across databases used in this project
    (true for afdb's 5-digit IDs vs mitdb's 3-digit IDs) - saved clip/plot
    filenames are keyed by record only, not db."""
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PLOT_DIR, exist_ok=True)

    record_path = os.path.join(DATA_ROOT, db, record)
    beat_samples, intervals, fs, total_samples = load_beats_and_rhythms(record_path, db)

    print(f"Record {db}/{record}: {len(beat_samples)} beats, {len(intervals)} rhythm "
          f"segments, fs={fs} Hz, duration={total_samples/fs/3600:.2f}h")

    labels_present = sorted(set(lbl for _, _, lbl in intervals))
    print("Rhythm labels present:", labels_present)

    clips = {}
    select_by = {"N": "min_rmssd", "AFIB": "most_beats"}
    for label in ("N", "AFIB"):
        found = find_clip(intervals, label, CLIP_DURATION_SEC, fs,
                           qrs_sample=beat_samples, prefer=select_by[label])
        if found is None:
            print(f"No {label} interval >= {CLIP_DURATION_SEC}s found, skipping.")
            continue
        clip_start, clip_end = found
        clip = build_clip(record_path, None, clip_start, clip_end, beat_samples, fs, label)
        clips[label] = clip
        np.savez(os.path.join(OUT_DIR, f"{record}_{label}_clip.npz"), **clip)
        plot_clip(record, clip, os.path.join(PLOT_DIR, f"{record}_{label}_clip.png"))

    print("--- Summary ---")
    for label, clip in clips.items():
        print(f"{label}: {clip['n_beats']} beats, mean RR={clip['mean_rr_sec']*1000:.0f}ms, "
              f"RMSSD={clip['rmssd_sec']*1000:.1f}ms")
    return clips


if __name__ == "__main__":
    process_record("04043", db="afdb")
