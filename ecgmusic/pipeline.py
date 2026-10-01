"""End to end: ECG clip -> melody -> emotion estimate -> arrangement -> MIDI, audio and score."""
import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import config
from .arrangement import Track, arrange
from .audio import render
from .data import clip_from_signal, load_signal, record_clips
from .emotion import Emotion, estimate_emotion
from .melody import melody
from .plots import plot_score

SUMMARY_FIELDS = ["db", "record", "label", "rmssd_ms", "mean_rr_ms", "n_notes", "pitch_min", "pitch_max",
                  "pitch_std", "pct_chromatic", "valence", "arousal", "quadrant", "instrument",
                  "consonant_chords", "tense_chords", "chaotic_chords"]
ESSENTIA_FIELDS = ["name", "render", *config.MOODS, "valence", "arousal"]


@dataclass
class Piece:
    notes: list
    emotion: Emotion
    tracks: list
    chords: list

    def summary(self):
        pitches = [n.pitch for n in self.notes]
        tiers = [c.tier for c in self.chords]
        return {
            "n_notes": len(self.notes),
            "pitch_min": min(pitches),
            "pitch_max": max(pitches),
            "pitch_std": float(np.std(pitches)),
            "pct_chromatic": 100 * float(np.mean([n.chromatic for n in self.notes])),
            "valence": self.emotion.valence,
            "arousal": self.emotion.arousal,
            "quadrant": self.emotion.quadrant,
            "instrument": self.emotion.instrument,
            **{f"{tier}_chords": tiers.count(tier) for tier in ("consonant", "tense", "chaotic")},
        }


def compose(clip):
    """Melody, emotion estimate and three-part arrangement for one clip (nothing is written)."""
    notes = melody(clip)
    if not notes:
        raise ValueError("the clip is too short to make any notes")
    emotion = estimate_emotion(notes)
    tracks, chords = arrange(notes, emotion.program)
    return Piece(notes, emotion, tracks, chords)


def save(piece, clip, out_dir, title="", audio=True):
    """Write melody.mid, arrangement.mid, score.png and (if `audio`) the matching WAV files."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    plain = Track("melody", config.PIANO_PROGRAM, piece.notes)
    files = {}
    files["melody_mid"], files["melody_wav"] = render([plain], out_dir / "melody", audio)
    files["arrangement_mid"], files["arrangement_wav"] = render(piece.tracks, out_dir / "arrangement", audio)
    files["score_png"] = out_dir / "score.png"
    plot_score(clip, piece.notes, piece.chords,
               f"{title}: {piece.emotion.quadrant}, melody on {piece.emotion.instrument}", files["score_png"])
    return files


def _write_csv(path, rows, fields):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_examples(records=config.EXAMPLE_RECORDS, audio=True, essentia=True):
    """Compose every example record, write output/examples/ and the result tables."""
    if essentia and not audio:
        raise ValueError("the Essentia analysis listens to the rendered audio, so it needs audio=True")
    if essentia:
        from .essentia_models import analyze_wav

    summary, essentia_rows = [], []
    for db, record in records:
        try:
            clips = record_clips(record, db)
        except (OSError, ValueError) as error:
            print(f"skipping {db}/{record}: {error}")
            continue
        for label, clip in clips.items():
            name = f"{record}_{label}"
            piece = compose(clip)
            files = save(piece, clip, config.EXAMPLES_DIR / name, f"{db} {record} {label}", audio)
            row = {"db": db, "record": record, "label": label,
                   "rmssd_ms": round(clip.rmssd_ms, 1), "mean_rr_ms": round(clip.mean_rr_ms)}
            row.update({key: round(value, 2) if isinstance(value, float) else value
                        for key, value in piece.summary().items()})
            summary.append(row)
            print(f"{name:>11}: {row['quadrant']:<13} valence {row['valence']:+.2f}  arousal {row['arousal']:+.2f}  "
                  f"chords {row['consonant_chords']}/{row['tense_chords']}/{row['chaotic_chords']}")
            if essentia:
                for render_name in ("melody", "arrangement"):
                    scores = analyze_wav(files[f"{render_name}_wav"])
                    essentia_rows.append({"name": name, "render": render_name,
                                          **{key: round(value, 3) for key, value in scores.items()}})

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_csv(config.OUTPUT_DIR / "examples_summary.csv", summary, SUMMARY_FIELDS)
    if essentia_rows:
        _write_csv(config.OUTPUT_DIR / "essentia_results.csv", essentia_rows, ESSENTIA_FIELDS)
    return summary, essentia_rows


def analyze_signal(signal, fs, name="input", start=0.0, duration=60.0, out_dir=None, audio=True, essentia=False):
    """Detect beats in a raw ECG signal, compose it and write the results to out_dir."""
    clip = clip_from_signal(signal, fs, start, duration)
    piece = compose(clip)
    out_dir = Path(out_dir) if out_dir else config.ANALYSIS_DIR / name
    files = save(piece, clip, out_dir, name, audio)
    second_opinion = None
    if essentia:
        if not audio:
            raise ValueError("the Essentia analysis listens to the rendered audio, so it needs audio=True")
        from .essentia_models import analyze_wav
        second_opinion = analyze_wav(files["melody_wav"])
    return {"clip": clip, "piece": piece, "files": files, "essentia": second_opinion}


def analyze_file(path, fs=None, channel=0, **options):
    """analyze_signal for a WFDB record (path without extension) or a one-column sample file."""
    signal, fs = load_signal(path, fs, channel)
    return analyze_signal(signal, fs, name=Path(str(path).rstrip("/")).stem, **options)
