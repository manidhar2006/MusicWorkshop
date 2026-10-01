"""Optional third opinion from music2emo; run it with music2emo's own interpreter (see README)."""
import csv
import os
import sys

from . import config


def main():
    melodies = sorted(config.EXAMPLES_DIR.glob("*/melody.wav"))
    if not melodies:
        sys.exit("No example audio found - run `python -m ecgmusic build` first.")
    sys.path.insert(0, str(config.MUSIC2EMO_DIR))
    os.chdir(config.MUSIC2EMO_DIR)  # music2emo reads its checkpoints and writes temp files relative to its folder
    from music2emo import Music2emo

    model = Music2emo()
    rows = []
    for wav in melodies:
        out = model.predict(str(wav))
        rows.append({"name": wav.parent.name, "valence": round(out["valence"], 4),
                     "arousal": round(out["arousal"], 4), "moods": "|".join(out["predicted_moods"])})
        print(f"{wav.parent.name:>11}: valence {out['valence']:.2f}  arousal {out['arousal']:.2f}")
    with open(config.OUTPUT_DIR / "music2emo_results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "valence", "arousal", "moods"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
