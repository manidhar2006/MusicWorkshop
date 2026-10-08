"""Analyse the listening study: do people hear what the model says they should?

Takes the blinded ratings collected from listeners, joins them to the key written by the study
build, and answers four questions:

  1. Does listener valence/arousal track the model's?        (Spearman across clips)
  2. Is the AFib piece rated lower in valence and higher in
     arousal than the same person's normal piece?            (Wilcoxon, paired per record)
  3. Does the forced-choice word match the model's quadrant?  (hit rate against 25% chance)
  4. Record 219, whose "normal" label the pipeline disputes.  (the hidden control)

Responses come either as a directory of JSON documents (one per listener, as exported from the
study page's store) or as a single CSV of clip ratings with a `listener` column.

    python -m ecgmusic.listening_study responses/ --key output/listening_study/KEY.csv
"""
import argparse
import csv
import json
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy import stats

WORD_TO_QUADRANT = {"calm": "calm_relaxed", "tense": "tense_anxious",
                    "happy": "happy_excited", "sad": "sad_depressed"}
RATING_FIELDS = ("pleasant", "energy", "steady")


@dataclass
class Clip:
    """One clip's key entry plus every rating listeners gave it."""
    clip: str
    record: str
    rhythm: str
    excluded: bool
    rmssd_ms: float
    model_valence: float
    model_arousal: float
    model_quadrant: str
    pleasant: list = field(default_factory=list)
    energy: list = field(default_factory=list)
    steady: list = field(default_factory=list)
    words: list = field(default_factory=list)

    @property
    def n(self):
        return len(self.pleasant)

    def mean(self, name):
        values = getattr(self, name)
        return float(statistics.fmean(values)) if values else float("nan")

    def sem(self, name):
        values = getattr(self, name)
        return float(stats.sem(values)) if len(values) > 1 else float("nan")

    @property
    def listener_valence(self):
        """Mean pleasantness rescaled from 1-9 to the model's -1..+1."""
        return (self.mean("pleasant") - 5) / 4

    @property
    def listener_arousal(self):
        return (self.mean("energy") - 5) / 4

    @property
    def hit_rate(self):
        """Share of listeners whose chosen word matches the model's quadrant."""
        if not self.words:
            return float("nan")
        hits = sum(WORD_TO_QUADRANT.get(w) == self.model_quadrant for w in self.words)
        return hits / len(self.words)


# --- loading ---------------------------------------------------------------------------------

def load_key(path):
    """The clip -> condition map written when the study set was built."""
    clips = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            clips[row["clip"]] = Clip(
                clip=row["clip"], record=row["record"], rhythm=row["rhythm"],
                excluded=row["excluded_record"].strip().lower() in ("true", "1", "yes"),
                rmssd_ms=float(row["rmssd_ms"]),
                model_valence=float(row["model_valence"]),
                model_arousal=float(row["model_arousal"]),
                model_quadrant=row["model_quadrant"])
    return clips


def _add(clips, clip_id, rating):
    clip = clips.get(clip_id)
    if clip is None:
        return False
    try:
        clip.pleasant.append(int(rating["pleasant"]))
        clip.energy.append(int(rating["energy"]))
        clip.steady.append(int(rating["steady"]))
    except (KeyError, TypeError, ValueError):
        return False
    word = str(rating.get("word", "")).strip().lower()
    if word in WORD_TO_QUADRANT:
        clip.words.append(word)
    return True


def _forms_columns(header):
    """Map a Google Forms export header to (clip id, field), for the columns that are ratings.

    Forms names each column after the question title, so the titles in the circulated form embed
    the clip id ("clip_07 - How pleasant does it sound?"). Anything else (timestamp, training) is
    ignored.
    """
    keywords = {"pleasant": "pleasant", "energetic": "energy", "energy": "energy",
                "word": "word", "steady": "steady", "regular": "steady"}
    columns = {}
    for name in header:
        low = name.lower()
        match = re.search(r"clip[_\s-]*(\d{1,2})", low)
        if not match:
            continue
        field_name = next((v for k, v in keywords.items() if k in low), None)
        if field_name:
            columns[name] = (f"clip_{int(match.group(1)):02d}", field_name)
    return columns


def _load_forms_csv(path, clips):
    """One row per listener, one column per question - Google Forms' own export shape."""
    listeners = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        columns = _forms_columns(reader.fieldnames or [])
        if not columns:
            return None
        training_col = next((c for c in reader.fieldnames if "training" in c.lower()), None)
        context_col = next((c for c in reader.fieldnames if "listening" in c.lower()
                            or "headphone" in c.lower()), None)
        for i, row in enumerate(reader, 1):
            by_clip = {}
            for column, (clip_id, field_name) in columns.items():
                value = (row.get(column) or "").strip()
                if value:
                    by_clip.setdefault(clip_id, {})[field_name] = value
            kept = sum(_add(clips, clip_id, rating) for clip_id, rating in by_clip.items())
            if kept:
                listeners.append({"listener": f"forms_{i:03d}", "clips": kept,
                                  "training_years": row.get(training_col) if training_col else None,
                                  "listening": row.get(context_col) if context_col else None})
    return listeners


def load_responses(path, clips):
    """Fill `clips` from per-listener JSON, a long CSV, or a Google Forms export. Returns listeners."""
    path = Path(path)
    listeners = []
    if path.is_file() and path.suffix.lower() == ".csv":
        from_forms = _load_forms_csv(path, clips)
        if from_forms is not None:
            return from_forms
    if path.is_dir():
        for doc_path in sorted(path.rglob("*.json")):
            doc = json.loads(doc_path.read_text())
            ratings = doc.get("ratings") or {}
            kept = sum(_add(clips, clip_id, r) for clip_id, r in ratings.items())
            if kept:
                listeners.append({"listener": doc_path.stem, "clips": kept,
                                  "training_years": doc.get("trainingYears"),
                                  "listening": doc.get("listening")})
    else:
        rows = {}
        with open(path) as f:
            for row in csv.DictReader(f):
                rows.setdefault(row.get("listener", "anon"), []).append(row)
        for listener, entries in rows.items():
            kept = sum(_add(clips, e["clip"], e) for e in entries)
            if kept:
                listeners.append({"listener": listener, "clips": kept,
                                  "training_years": entries[0].get("training_years"),
                                  "listening": entries[0].get("listening")})
    return listeners


# --- the four questions ----------------------------------------------------------------------

def correlation(clips):
    """Spearman between the model's valence/arousal and the listeners' means, across clips."""
    rated = [c for c in clips if c.n]
    out = {}
    for axis, listener_attr, model_attr in (("valence", "listener_valence", "model_valence"),
                                            ("arousal", "listener_arousal", "model_arousal")):
        if len(rated) < 3:
            out[axis] = (float("nan"), float("nan"))
            continue
        rho, p = stats.spearmanr([getattr(c, model_attr) for c in rated],
                                 [getattr(c, listener_attr) for c in rated])
        out[axis] = (float(rho), float(p))
    return out


def paired_by_record(clips):
    """Per record, the AFib-minus-normal difference in listener valence, arousal and steadiness."""
    by_record = {}
    for c in clips:
        if c.n:
            by_record.setdefault(c.record, {})[c.rhythm] = c
    rows = []
    for record, pair in sorted(by_record.items()):
        if {"normal", "afib"} - pair.keys():
            continue
        normal, afib = pair["normal"], pair["afib"]
        rows.append({
            "record": record,
            "excluded": normal.excluded,
            "d_valence": afib.listener_valence - normal.listener_valence,
            "d_arousal": afib.listener_arousal - normal.listener_arousal,
            "d_steady": afib.mean("steady") - normal.mean("steady"),
        })
    return rows


def signed_rank(rows, key):
    """Wilcoxon signed-rank over the per-record differences, excluding record 219."""
    values = [r[key] for r in rows if not r["excluded"]]
    if len(values) < 5:
        return None
    statistic, p = stats.wilcoxon(values)
    return {"n": len(values), "statistic": float(statistic), "p": float(p),
            "median": float(np.median(values)),
            "negative": sum(v < 0 for v in values), "positive": sum(v > 0 for v in values)}


def quadrant_agreement(clips):
    """Overall forced-choice hit rate against the 25% chance level, with a binomial test."""
    hits = total = 0
    for c in clips:
        for w in c.words:
            total += 1
            hits += WORD_TO_QUADRANT.get(w) == c.model_quadrant
    if not total:
        return None
    result = stats.binomtest(hits, total, 0.25, alternative="greater")
    return {"hits": hits, "total": total, "rate": hits / total, "p": float(result.pvalue)}


# --- reporting -------------------------------------------------------------------------------

def report(clips, listeners):
    ordered = sorted(clips.values(), key=lambda c: (c.record, c.rhythm))
    rated = [c for c in ordered if c.n]
    print(f"\n{len(listeners)} listeners · {sum(c.n for c in ordered)} ratings · "
          f"{len(rated)}/{len(ordered)} clips rated\n")

    print("Per clip (listener means, 1-9; model on its own -1..+1 scale)")
    print(f"{'clip':<9}{'record':>8}{'rhythm':>8}{'n':>4}{'pleasant':>10}{'energy':>9}"
          f"{'steady':>8}{'hit%':>7}{'model v':>9}{'model a':>9}  quadrant")
    for c in ordered:
        if not c.n:
            continue
        mark = " *" if c.excluded else "  "
        print(f"{c.clip:<9}{c.record:>8}{c.rhythm:>8}{c.n:>4}"
              f"{c.mean('pleasant'):>10.2f}{c.mean('energy'):>9.2f}{c.mean('steady'):>8.2f}"
              f"{100 * c.hit_rate:>7.0f}{c.model_valence:>9.2f}{c.model_arousal:>9.2f}  "
              f"{c.model_quadrant}{mark}")
    if any(c.excluded for c in rated):
        print("  * record 219: the excluded record, included here unlabelled as a control")

    print("\n1. Does listener rating track the model? (Spearman across clips)")
    for axis, (rho, p) in correlation(ordered).items():
        verdict = "" if np.isnan(p) else ("  significant" if p < 0.05 else "  not significant")
        print(f"   {axis:<8} rho = {rho:+.3f}   p = {p:.4f}{verdict}")

    rows = paired_by_record(ordered)
    print("\n2. AFib minus normal, per record (listener means; negative valence = less pleasant)")
    print(f"   {'record':>8}{'d valence':>12}{'d arousal':>12}{'d steady':>11}")
    for r in rows:
        mark = "  <- excluded record" if r["excluded"] else ""
        print(f"   {r['record']:>8}{r['d_valence']:>+12.3f}{r['d_arousal']:>+12.3f}"
              f"{r['d_steady']:>+11.2f}{mark}")
    for key, label, expect in (("d_valence", "valence", "lower for AFib"),
                               ("d_arousal", "arousal", "higher for AFib"),
                               ("d_steady", "steadiness", "lower for AFib")):
        test = signed_rank(rows, key)
        if test is None:
            print(f"   {label:<11} too few records for a signed-rank test")
            continue
        print(f"   {label:<11} median {test['median']:+.3f}  "
              f"({test['negative']} down / {test['positive']} up of {test['n']})  "
              f"p = {test['p']:.4f}   expected: {expect}")

    print("\n3. Forced-choice word vs the model's quadrant")
    agreement = quadrant_agreement(ordered)
    if agreement:
        print(f"   {agreement['hits']}/{agreement['total']} = {100 * agreement['rate']:.1f}% "
              f"(chance 25%)   p = {agreement['p']:.4g}")
    else:
        print("   no word choices recorded")

    print("\n4. Record 219 — the control the pipeline disputes")
    control = {c.rhythm: c for c in ordered if c.excluded and c.n}
    if {"normal", "afib"} <= control.keys():
        normal, afib = control["normal"], control["afib"]
        print(f"   labelled normal : steady {normal.mean('steady'):.2f}  "
              f"pleasant {normal.mean('pleasant'):.2f}  energy {normal.mean('energy'):.2f}")
        print(f"   labelled AFib   : steady {afib.mean('steady'):.2f}  "
              f"pleasant {afib.mean('pleasant'):.2f}  energy {afib.mean('energy'):.2f}")
        if normal.mean("steady") < afib.mean("steady"):
            print("   Listeners heard the *normal*-labelled clip as the less steady one —")
            print("   the same inversion the pipeline found, confirmed independently by ear.")
        else:
            print("   Listeners did not reproduce the inversion the pipeline found here.")
    else:
        print("   not rated")
    print()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m ecgmusic.listening_study",
                                     description="Analyse the listening-study ratings.")
    parser.add_argument("responses", help="directory of per-listener JSON, or one CSV of ratings")
    parser.add_argument("--key", default="output/listening_study/KEY.csv",
                        help="the clip key written when the study set was built")
    args = parser.parse_args(argv)

    clips = load_key(args.key)
    listeners = load_responses(args.responses, clips)
    if not listeners:
        raise SystemExit(f"no usable responses found in {args.responses}")
    report(clips, listeners)


if __name__ == "__main__":
    main()
