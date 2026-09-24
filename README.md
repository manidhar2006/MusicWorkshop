# Sonifying the Heart: Turning ECG Data into Music

Music Workshop project — converting real ECG recordings into audible music, so a healthy
heart rhythm and a diseased one (atrial fibrillation) sound noticeably different.

**Team:** Chervith Reddy (2024101076) · Manidhar Sukasi (2023101067) · Sathwik Reddy (2024121002)

Full proposal: [`music_workshop.pdf`](music_workshop.pdf)

This README exists because the repo currently has nothing but the proposal PDF. It turns
that proposal into an ordered, checkable to-do list so it's obvious what to build first.

---

## 1. The core idea, in one paragraph

Every heartbeat has an R-peak. The gap between consecutive R-peaks (the **R–R interval**)
becomes a musical note's timing. How much that gap varies from beat to beat controls how
consonant/dissonant the notes are. The signal's amplitude controls how loud (velocity) each
note is. A normal heart → steady, consonant pattern. Atrial fibrillation → irregular,
unstable-sounding pattern. That's the whole pipeline: **ECG signal → R-peaks → musical
mapping → MIDI → audio.**

---

## 2. Goal & use case

**One-liner:** We turn real ECG recordings into music, so a healthy heartbeat and an
irregular one (atrial fibrillation) sound different — not just look different on a monitor.

**Why it matters:** An ECG strip is normally something only a trained eye can read. We map
the heart's own rhythm — timing between beats, how irregular that timing is, and the
signal's strength — onto musical parameters: note timing, pitch/dissonance, and loudness. A
steady, healthy rhythm comes out sounding calm and consonant; atrial fibrillation comes out
sounding unstable and dissonant. The goal is a working demo, built on real clinical data
from PhysioNet, that makes arrhythmia audible.

This targets three concrete uses, not just novelty:
- **Teaching** — trainees can learn to recognize arrhythmias by ear, not just by eye.
- **Accessibility** — gives visually impaired clinicians/technicians a way to interpret ECG
  data at all.
- **Eyes-free monitoring** — like a pulse-ox beep, but carrying more information than a flat
  tone.

**Honest scope:** this is not a clinical tool. The actual deliverable is a reproducible
pipeline (ECG → R-R intervals → musical mapping → MIDI/audio) demonstrated on a handful of
paired clips (normal vs. AFib) from MIT-BIH data, with plots showing the ECG aligned to the
generated score — a proof-of-concept and reference implementation, which is itself a
recognized gap in this research area (see Section 5 of the proposal PDF).

Note on where the "music" actually comes from: rhythm (note timing) genuinely comes from the
ECG, since R-R intervals are already periodic like a beat. Pitch, harmony, and scale choice
are *not* inherent to the signal — those are a mapping we design (this is called
**sonification**, the same idea behind a Geiger counter's clicks or astronomers turning
telescope data into sound), not something "found" in the body.

---

## 3. Actual project structure

This is what exists now (updated as of the `mitdb` extension) — see
[PROGRESS.md](PROGRESS.md) for the build history and [PRESENTATION.md](PRESENTATION.md) for
results.

```
Project/
├── music_workshop.pdf         # proposal
├── README.md                  # this file (the plan)
├── PROGRESS.md                # dated build log, checklist status
├── PRESENTATION.md            # Phase 5 write-up: rationale + results
├── requirements.txt
├── .gitignore
├── data/
│   ├── afdb/                  # full MIT-BIH Atrial Fibrillation Database (downloaded)
│   ├── mitdb/                 # full MIT-BIH Arrhythmia Database (downloaded)
│   └── processed/             # extracted 30s clips as .npz (signal, R-peaks, R-R, RMSSD)
├── src/
│   ├── download_db.py         # fast parallel PhysioNet downloader (any database)
│   ├── extract_features.py    # Phase 2: R-peaks, rhythm labels, R-R intervals, RMSSD
│   ├── explore_data.py        # Phase 1: quick record streaming/plotting
│   ├── mapping.py             # Phase 3: R-R/amplitude -> pitch/duration/velocity
│   ├── render.py              # Phase 4: notes -> MIDI -> WAV (FluidSynth)
│   ├── sonify.py              # ties mapping+render together, sanity plots
│   └── build_examples.py      # batch driver: runs the whole pipeline across records
└── output/
    ├── midi/, audio/          # rendered MIDI + WAV per record/label
    ├── *_clip.png              # Phase 2 ECG+R-peak plots
    ├── *_sonification.png      # Phase 3 ECG/deviation/pitch sanity plots
    └── examples_summary.csv   # results table across all processed records
```

Add a `.gitignore` early (raw PhysioNet data files and rendered audio are large/binary —
don't commit them):

```
data/
output/
*.wav
*.mp3
__pycache__/
*.pyc
.ipynb_checkpoints/
```

---

## 4. Step-by-step plan

### Phase 0 — Environment setup
- [ ] Install Python 3.10+ and create a virtual environment (`python -m venv venv`).
- [ ] Install core packages: `pip install wfdb numpy scipy pretty_midi mido matplotlib`
- [ ] Install **FluidSynth** for audio rendering (`sudo apt install fluidsynth` on Ubuntu),
      or plan to render MIDI manually in a DAW instead.
- [ ] Download a General MIDI soundfont (e.g. `FluidR3_GM.sf2`) — needed for FluidSynth to
      turn MIDI into actual sound.
- [ ] Freeze the above into `requirements.txt`.

### Phase 1 — Get and explore the data
- [ ] Read up on [PhysioNet](https://physionet.org/) and the two databases you'll use:
  - **MIT-BIH Arrhythmia Database (`mitdb`)**
  - **MIT-BIH Atrial Fibrillation Database (`afdb`)** — has pre-computed R-peaks and
    cardiologist-verified rhythm labels, so you don't need to build beat detection yourself.
- [ ] Use `wfdb.dl_database('afdb', dl_dir='data/afdb')` (and same for `mitdb`) to download
      a handful of records — don't grab the whole database at first, just 2–3 records to
      experiment with.
- [ ] Load one record with `wfdb.rdrecord()` / `wfdb.rdann()` and plot the raw ECG signal
      with matplotlib. Goal: confirm you can read a record and see a waveform.

### Phase 2 — Extract rhythm features
- [ ] From annotations, pull out R-peak positions and rhythm labels (normal sinus rhythm vs.
      atrial fibrillation) for a record.
- [ ] Compute the R–R interval series (time between consecutive R-peaks).
- [ ] Compute a beat-to-beat variability measure (RMSSD).
- [ ] Select and isolate one "normal" segment and one "AFib" segment from the same or
      different records, to use as your first before/after comparison.

### Phase 3 — Design the sonification mapping
- [ ] Decide the mapping rules (start simple, then refine):
  - R–R interval → note onset time and duration
  - Deviation from a running mean of R–R interval → pitch selection
  - ECG amplitude at/near the R-peak → note velocity (loudness)
  - Stable rhythm → stay within a pentatonic scale; increasing irregularity → introduce
    chromatic movement
- [ ] Implement this as a function: `segment (ECG + R-peaks) -> list of (pitch, start_time,
      duration, velocity)` notes.
- [ ] Sanity-check by printing/plotting the generated note sequence next to the R–R interval
      plot before generating audio.

### Phase 4 — Render to MIDI and audio
- [ ] Use `pretty_midi` or `mido` to turn your note list into a `.mid` file.
- [ ] Render the MIDI file to audio using FluidSynth (`fluidsynth -ni soundfont.sf2 in.mid
      -F out.wav`) or by opening it in a DAW.
- [ ] Generate a **paired clip**: same length, one from a normal-rhythm segment, one from an
      AFib segment, so the contrast is audible back-to-back.

### Phase 5 — Present
- [ ] Produce a small set (3–5) of paired audio examples (normal vs. AFib).
- [ ] For each, make a plot aligning the raw ECG waveform with the generated musical score
      (piano-roll style is fine).
- [ ] Write a short explanation of the mapping rationale (this can mostly reuse Section 3 of
      the proposal PDF).
- [ ] (Optional, not central) Explore whether an LLM can suggest alternative mappings worth
      trying.

---

## 5. Where to start right now

If you genuinely don't know where to begin: do **Phase 0 and Phase 1 only** this session.
Get one ECG record downloaded and plotted on screen. Everything else builds on that working
first step.

## 6. Notes

- This README will get stale as the project evolves — update the checkboxes as you go
  rather than treating it as fixed spec.
- Nothing in this repo has been committed beyond the initial commit; nothing new will be
  committed until you say so.
