"""
Phase 3 end-to-end: load the normal / AFib clips extracted in Phase 2, run the
sonification mapping, render MIDI + audio, and produce a sanity-check plot
that lines up R-R interval variability against the resulting pitch sequence
(before trusting the output by ear alone).
"""
import os

import matplotlib.pyplot as plt
import numpy as np

from mapping import sonify_clip
from render import notes_to_midi, midi_to_wav

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
MIDI_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "midi")
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "audio")
PLOT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")


def load_clip(record, label):
    path = os.path.join(PROCESSED_DIR, f"{record}_{label}_clip.npz")
    with np.load(path) as data:
        return {k: data[k] for k in data.files}


def sanity_plot(record, clip, notes, label, out_path):
    fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True)

    t = np.arange(len(clip["signal"])) / clip["fs"]
    axes[0].plot(t, clip["signal"], linewidth=0.7)
    axes[0].set_ylabel("ECG (mV)")
    axes[0].set_title(f"{record} - {label}: ECG, R-R deviation, and generated pitch")

    starts = [n["start"] for n in notes]
    deviations = [n["deviation"] * 100 for n in notes]
    axes[1].stem(starts, deviations, basefmt=" ")
    axes[1].axhline(0, color="gray", linewidth=0.5)
    axes[1].axhline(12, color="red", linewidth=0.5, linestyle="--", label="chromatic threshold")
    axes[1].axhline(-12, color="red", linewidth=0.5, linestyle="--")
    axes[1].set_ylabel("R-R deviation (%)")
    axes[1].legend(loc="upper right", fontsize=8)

    pitches = [n["pitch"] for n in notes]
    colors = ["tab:red" if n["used_chromatic"] else "tab:blue" for n in notes]
    axes[2].scatter(starts, pitches, c=colors, s=20)
    axes[2].axhline(60, color="gray", linewidth=0.5, label="root note (C4)")
    axes[2].set_ylabel("MIDI pitch")
    axes[2].set_xlabel("Time (s)")
    axes[2].legend(loc="upper right", fontsize=8)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved sanity plot to {out_path}")


def process(record, label):
    os.makedirs(MIDI_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)

    clip = load_clip(record, label)
    notes = sonify_clip(clip)
    if not notes:
        print(f"{record} {label}: 0 notes generated (clip too short), skipping render.")
        return None, None, None

    midi_path = os.path.join(MIDI_DIR, f"{record}_{label}.mid")
    notes_to_midi(notes, midi_path)

    wav_path = os.path.join(AUDIO_DIR, f"{record}_{label}.wav")
    midi_to_wav(midi_path, wav_path)

    plot_path = os.path.join(PLOT_DIR, f"{record}_{label}_sonification.png")
    sanity_plot(record, clip, notes, label, plot_path)

    pitches = [n["pitch"] for n in notes]
    n_chromatic = sum(n["used_chromatic"] for n in notes)
    stats = {
        "record": record, "label": label, "n_notes": len(notes),
        "pitch_min": min(pitches), "pitch_max": max(pitches),
        "pct_chromatic": 100 * n_chromatic / len(notes),
        "pitch_std": float(np.std(pitches)),
    }
    print(f"{record} {label}: {len(notes)} notes, pitch range {min(pitches)}-{max(pitches)} "
          f"(root=60), {n_chromatic}/{len(notes)} chromatic, "
          f"pitch std={np.std(pitches):.1f} semitones")
    return midi_path, wav_path, stats


if __name__ == "__main__":
    print("--- Normal rhythm ---")
    process("04043", "N")
    print("\n--- AFib rhythm ---")
    process("04043", "AFIB")
