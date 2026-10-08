"""Build the blinded clip set for the listening study.

Produces `output/listening_study/`: sixteen mp3s named clip_01..clip_16, plus the key that maps
them back to the recordings. Deterministic - the same SEED always gives the same order - so the
set and its key can be regenerated instead of committed. That matters because this repository is
public and the key would unblind the study.

Two choices here carry the study's validity:

* **The plain melody, not the arrangement.** `melody.wav` renders on PIANO_PROGRAM, so the
  instrument is NOT the one our own emotion model chose for the piece. Were we to use the
  arrangement, a listener calling an AFib clip "tense" might only be reacting to a distortion
  guitar, and the test would be circular.
* **Record 219 is included, unlabelled.** It is excluded from the published results because its
  "normal" window is more irregular than its AFib one (133 non-conducted P-waves). That makes it
  the one clip pair where the database's label and our pipeline disagree, so listeners decide
  between them without knowing they are doing so.

    python -m ecgmusic.build_study
"""
import argparse
import csv
import json
import random
import subprocess
from pathlib import Path

from . import config
from .data import record_clips
from .pipeline import compose, save

SEED = 20261008
CONTROL_RECORD = ("mitdb", "219")
STUDY_DIR = config.OUTPUT_DIR / "listening_study"
MP3_BITRATE = "96k"
KEY_FIELDS = ["clip", "position", "record", "label", "rhythm", "excluded_record", "rmssd_ms",
              "pct_chromatic", "model_valence", "model_arousal", "model_quadrant",
              "consonant", "tense", "chaotic"]


def build_control(audio=True):
    """Compose the excluded record's two clips, which the headline build leaves out."""
    db, record = CONTROL_RECORD
    rows = []
    for label, clip in record_clips(record, db).items():
        piece = compose(clip)
        save(piece, clip, config.EXAMPLES_DIR / f"{record}_{label}", f"{db} {record} {label}", audio)
        summary = piece.summary()
        rows.append({"db": db, "record": record, "label": label,
                     "rmssd_ms": round(clip.rmssd_ms, 1), "mean_rr_ms": round(clip.mean_rr_ms),
                     **{k: (round(v, 2) if isinstance(v, float) else v)
                        for k, v in summary.items()}})
        print(f"{record}_{label:<4}: {summary['quadrant']:<13} rmssd {clip.rmssd_ms:>6.1f} ms  "
              f"chords {summary['consonant_chords']}/{summary['tense_chords']}/{summary['chaotic_chords']}")
    if rows:
        path = config.OUTPUT_DIR / "record219_excluded.csv"
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return rows


def presentation_order(sources, seed=SEED):
    """Shuffle so no two clips of one record are adjacent and no rhythm runs four deep."""
    rng = random.Random(seed)
    for _ in range(10000):
        trial = sources[:]
        rng.shuffle(trial)
        if any(trial[i][0] == trial[i - 1][0] for i in range(1, len(trial))):
            continue
        if any(len({trial[j][1] for j in range(i - 3, i + 1)}) == 1 for i in range(3, len(trial))):
            continue
        return trial
    raise RuntimeError("no ordering satisfied the spacing constraints")


def _model_rows():
    """Every composed clip's summary, from the headline table plus the excluded record."""
    rows = {}
    for path in (config.OUTPUT_DIR / "examples_summary.csv",
                 config.OUTPUT_DIR / "record219_excluded.csv"):
        if path.exists():
            with open(path) as f:
                for row in csv.DictReader(f):
                    rows[(row["record"], row["label"])] = row
    return rows


def build(out_dir=STUDY_DIR, seed=SEED):
    """Convert each plain melody to a blinded mp3 and write the key beside it."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model = _model_rows()
    if not model:
        raise SystemExit("no summaries found - run `python -m ecgmusic build` first")

    # Record order, then normal before AFib. The shuffle is seeded, so this input order is part of
    # what fixes the presentation order: changing it changes every clip number.
    ordered = sorted(model, key=lambda pair: (pair[0], 0 if pair[1] == "N" else 1))
    sources = [(record, label) for (record, label) in ordered
               if (config.EXAMPLES_DIR / f"{record}_{label}" / "melody.wav").exists()]
    missing = [f"{r}_{l}" for (r, l) in ordered if (r, l) not in sources]
    if missing:
        print(f"skipping (no rendered melody): {', '.join(missing)}")

    key = []
    for position, (record, label) in enumerate(presentation_order(sources, seed), 1):
        clip = f"clip_{position:02d}"
        destination = out_dir / f"{clip}.mp3"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
                        "-i", str(config.EXAMPLES_DIR / f"{record}_{label}" / "melody.wav"),
                        "-ac", "1", "-codec:a", "libmp3lame", "-b:a", MP3_BITRATE,
                        str(destination)], check=True)
        row = model[(record, label)]
        key.append({"clip": clip, "position": position, "record": record, "label": label,
                    "rhythm": "normal" if label == "N" else "afib",
                    "excluded_record": record == CONTROL_RECORD[1],
                    "rmssd_ms": row["rmssd_ms"], "pct_chromatic": row["pct_chromatic"],
                    "model_valence": row["valence"], "model_arousal": row["arousal"],
                    "model_quadrant": row["quadrant"], "consonant": row["consonant_chords"],
                    "tense": row["tense_chords"], "chaotic": row["chaotic_chords"]})
        print(f"{clip} <- {record}_{label:<4} {row['quadrant']}")

    with open(out_dir / "KEY.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=KEY_FIELDS)
        writer.writeheader()
        writer.writerows(key)
    (out_dir / "key.json").write_text(json.dumps(key, indent=2))
    print(f"\n{len(key)} clips in {out_dir}")
    print("KEY.csv maps them back - it is gitignored, and participants must never see it.")
    return key


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m ecgmusic.build_study",
                                     description="Build the blinded listening-study clip set.")
    parser.add_argument("--skip-control", action="store_true",
                        help="don't compose record 219 (assume it is already in output/examples/)")
    parser.add_argument("--seed", type=int, default=SEED, help=f"ordering seed (default {SEED})")
    args = parser.parse_args(argv)

    if not args.skip_control:
        build_control()
    build(seed=args.seed)


if __name__ == "__main__":
    main()
