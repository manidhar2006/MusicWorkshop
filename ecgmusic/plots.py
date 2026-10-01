"""Figures: the ECG, the generated score, and the emotion estimates on the valence-arousal plane."""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from . import config

TIER_COLORS = {"consonant": "tab:green", "tense": "tab:orange", "chaotic": "tab:purple"}


def _finish(fig, path):
    """Save and close when a path is given (batch use); otherwise leave it for the notebook."""
    fig.tight_layout()
    if path is not None:
        fig.savefig(path, dpi=130)
        plt.close(fig)
    return fig


def plot_clip(clip, title="", path=None):
    fig, ax = plt.subplots(figsize=(12, 2.8))
    ax.plot(np.arange(len(clip.signal)) / clip.fs, clip.signal, linewidth=0.6)
    ax.plot(clip.peaks / clip.fs, clip.signal[clip.peaks], "rx", markersize=4, label="heartbeat (R-peak)")
    ax.set(title=title or f"{clip.label} clip: RMSSD {clip.rmssd_ms:.1f} ms, mean R-R {clip.mean_rr_ms:.0f} ms",
           xlabel="Time (s)", ylabel="ECG (mV)")
    ax.legend(loc="upper right", fontsize=8)
    return _finish(fig, path)


def plot_score(clip, notes, chords, title="", path=None):
    """ECG, beat-to-beat R-R deviation and the generated score on one shared time axis."""
    fig, (ecg, dev, score) = plt.subplots(3, 1, figsize=(12, 8), sharex=True,
                                          gridspec_kw={"height_ratios": [1, 1, 2]})
    ecg.plot(np.arange(len(clip.signal)) / clip.fs, clip.signal, linewidth=0.6)
    ecg.plot(clip.peaks / clip.fs, clip.signal[clip.peaks], "rx", markersize=4)
    ecg.set(title=title, ylabel="ECG (mV)")

    dev.stem([n.start for n in notes], [n.deviation * 100 for n in notes], basefmt=" ")
    for sign in (1, -1):
        dev.axhline(sign * config.CHROMATIC_THRESHOLD * 100, color="red", linewidth=0.6, linestyle="--")
    dev.set_ylabel("R-R deviation (%)")

    for c in chords:
        score.hlines(c.pitches, c.start, c.end, colors=TIER_COLORS[c.tier], linewidth=7, alpha=0.35)
    for n in notes:
        score.hlines(n.pitch, n.start, n.start + n.duration, linewidth=3.5,
                     colors="tab:red" if n.chromatic else "tab:blue")
    pitches = [n.pitch for n in notes] + [p for c in chords for p in c.pitches]
    low, high = min(pitches) - 2, max(pitches) + 2
    c_notes = [p for p in range(24, 109, 12) if low <= p <= high]
    score.set_ylim(low, high)
    score.set_yticks(c_notes, [f"C{p // 12 - 1}" for p in c_notes])
    score.set(ylabel="Pitch", xlabel="Time (s)")
    score.legend(handles=[
        Line2D([], [], color="tab:blue", linewidth=3.5, label="melody, in scale"),
        Line2D([], [], color="tab:red", linewidth=3.5, label="melody, chromatic"),
        *[Line2D([], [], color=color, linewidth=7, alpha=0.35, label=f"chord, {tier}")
          for tier, color in TIER_COLORS.items()],
    ], loc="upper center", bbox_to_anchor=(0.5, -0.22), fontsize=8, ncol=5, frameon=False)
    return _finish(fig, path)


def plot_circumplex(rows, path=None):
    """Emotion estimates on Russell's plane; `rows` are dicts with record, label, valence, arousal."""
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.add_patch(plt.Circle((0, 0), 1, fill=False, color="lightgray"))
    ax.axhline(0, color="gray", linewidth=0.6)
    ax.axvline(0, color="gray", linewidth=0.6)
    for x, y, text in ((0.6, 1.05, "happy / excited"), (-0.6, 1.05, "tense / anxious"),
                       (-0.6, -1.1, "sad / depressed"), (0.6, -1.1, "calm / relaxed")):
        ax.text(x, y, text, ha="center", color="dimgray", fontsize=10)

    by_record = {}
    for row in rows:
        by_record.setdefault(str(row["record"]), {})[row["label"]] = (float(row["valence"]), float(row["arousal"]))
    for record, points in by_record.items():
        if {"N", "AFIB"} <= points.keys():
            ax.annotate("", xy=points["AFIB"], xytext=points["N"],
                        arrowprops={"arrowstyle": "->", "color": "lightgray"})
        for label, (valence, arousal) in points.items():
            normal = label == "N"
            ax.scatter(valence, arousal, marker="o" if normal else "^", s=60,
                       color="tab:blue" if normal else "tab:red", zorder=3)
            ax.annotate(record, (valence, arousal), textcoords="offset points", xytext=(5, 4), fontsize=8)

    ax.set(xlim=(-1.25, 1.25), ylim=(-1.25, 1.25), aspect="equal", xlabel="valence (unpleasant → pleasant)",
           ylabel="arousal (calm → energetic)", title="Emotion estimate of every example (arrow: normal → AFib)")
    ax.legend(handles=[Line2D([], [], marker="o", color="tab:blue", linestyle="", label="normal rhythm"),
                       Line2D([], [], marker="^", color="tab:red", linestyle="", label="atrial fibrillation")],
              loc="lower left", fontsize=8)
    return _finish(fig, path)
