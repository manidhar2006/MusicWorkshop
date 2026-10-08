# Progress: Sonifying the Heart

**Inner emotion detection from ECG through music**: ECG data → Heartbeats → Music → Emotion

**Last updated:** 2026-10-09 · Full description: [project_description.md](project_description.md) ·
Overview and setup: [README.md](README.md)

This log is updated after every work session. Newest entry first. Each entry says what changed,
why, and what is next.

---

## Current status

| Part | Status | Notes |
|---|---|---|
| Stage 1: ECG data | ✅ Done | `afdb` and `mitdb` from PhysioNet. Records are streamed by default, and a parallel downloader is optional. Any WFDB or CSV file works. |
| Stage 2: Heartbeats | ✅ Done | Database annotations or XQRS detection; R-R intervals and RMSSD; clip selection that survives `afdb`'s jittery beat marks. |
| Stage 3: Music | ✅ Done | Melody (one note per heartbeat), strings with tension tiers, lub-dub pulse; MIDI, audio and a score plot. |
| Stage 4: Emotion | ✅ Built · 🟨 not validated | Our model, Essentia and music2emo. Essentia's mood columns were fixed today. Not yet compared with people's own emotion reports. |
| Code | ✅ Run and verified | Ran end to end on 2026-10-08. All 14 examples reproduce [§11.1](project_description.md#111-heartbeats-music-and-our-model) exactly. Now a single notebook. |
| Results | ✅ Reproduced | 14 clips from 7 recordings of 6 people, in [project_description.md §11](project_description.md#11-results). Regenerated 2026-10-08; every figure matches. |
| Documentation | ✅ Done | [Plan.md](Plan.md) (start here), [README.md](README.md), [project_description.md](project_description.md), this file. |
| [sonifying_the_heart.ipynb](sonifying_the_heart.ipynb) | ✅ The project, executed | Every stage in one self-contained notebook, 60 cells, saved with outputs. Switches off, so it opens fast and re-runs in under a minute. Replaced the `ecgmusic/` package and `main.ipynb`. |
| Listening study | ✅ Ready to circulate | 16 blinded clips in `output/listening_study/`, the Google Form spec in [listening_study_questions.md](listening_study_questions.md), and `ecgmusic/listening_study.py` for the analysis. No listeners yet. |
| Sprint 3 submission | ✅ Written | `sprint3/`: team report `Sprint3.pdf` (3 pages) and one 1-page individual report per member (`<roll number>_Sprint3.pdf`), with their LaTeX sources. Not committed. |
| Git | ✅ Committed, not pushed | All work was committed on 2026-10-01 at the user's request, on the branch `claude/inner-emotion-rewrite`. Nothing has been pushed to GitHub yet. |

Legend: ✅ done · 🟨 partly done or in progress · ⬜ not started

---

## Next steps

- [x] **Run the rewritten code once** (done 2026-10-08; 14/14 examples match §11.1 exactly).
- [ ] **Run the Essentia and music2emo stages** on the regenerated audio, to check §11.2 and
      §11.3 as well. Skipped on 2026-10-08 because they are the heavy steps.
- [ ] **Collect listeners.** Share the study page, aim for 20-30 classmates, then run
      `python -m ecgmusic.listening_study <responses>`.
- [ ] **Validate the emotion stage** against self-reported emotion, starting with WESAD, then
      DREAMER and AMIGOS. Use plain HRV as the baseline
      ([§13](project_description.md#13-validation-plan)).
- [ ] **Listening study — now the main deliverable** (decided 2026-10-08). Classmates hear the
      pieces blind and rate them. This tests the music → emotion step on its own, needs no compute
      and no new dataset, and closes the one gap that belongs to the sonification itself: whether a
      listener can actually hear what the mapping encodes. Design is in the log entry below.
- [ ] **A mapping for healthy hearts**, so that calm, breathing-locked variability (respiratory
      sinus arrhythmia) is not read as tension.
- [ ] **Listen critically and tune by ear:** the 12% scale threshold, the 85% note length, the
      12% and 25% chord thresholds, and the instrument choices.
- [ ] **Decide the final course deliverable** (report, slides, live demo).
- [x] **Commit the rewrite and the documents** (done 2026-10-01, on the branch
      `claude/inner-emotion-rewrite`).
- [ ] **Merge that branch into `main` and push to GitHub**, when the user wants.
- [ ] **Each teammate checks their own Sprint 3 report** before it is submitted. The split of
      the work was proposed at the user's request.

---

## Log

### 2026-10-09 · README brought up to date

- Rewrote [README.md](README.md) around the project as it now stands, rather than as it was.
- **Added:** a status line at the top; record 219 written up in §7 as a result rather than an
  omission, with the conclusion it supports ("the music is an instrument for noticing things the
  label does not carry"); a new §8.3 on the listening study with the four possible outcomes and
  what each would mean; §8.4 for the dataset validation that follows; §9.5, the study workflow end
  to end from building the clips to running the analysis.
- **Fixed:** a broken project-structure tree left over from removing the package — it still listed
  `pipeline.py` and `__main__.py`; a stale `--no-audio` flag from the deleted command line; a
  dangling §9.5 anchor; and the gitignore list, which named `venv/` and omitted the study mp3s
  and `responses.csv`.
- Every relative link and in-page anchor was re-checked; all resolve. 788 lines.

### 2026-10-09 · Full run with audio

- Ran the notebook end to end with `RENDER_AUDIO` and `BUILD_ALL` on, via `nbclient`, and saved
  it **with its outputs** — it now shows a complete run rather than empty cells. 235 s.
- **Produced:** 32 WAVs, 32 MIDI files, 16 score plots and the 16 study mp3s. All 14 example rows
  match the published [§11.1](project_description.md#111-heartbeats-music-and-our-model) table
  exactly, for the third independent time.
- **Two defects found and fixed while doing it.**
  - §10 composed record 219 but never saved it, so it had no `melody.wav`. §11 silently built a
    **14-clip** study set instead of 16, dropping the hidden control — the most interesting part
    of the study. §10 now saves both 219 pieces and writes `record219_excluded.csv` itself.
  - Turning the switches on by search-and-replace also flipped the FluidSynth fallback inside
    `if RENDER_AUDIO and shutil.which(...) is None:` from `False` to `True`, which would have
    *enabled* audio on a machine without FluidSynth. Caught before the run.
- **No drift.** `KEY.csv`, `examples_summary.csv` and `record219_excluded.csv` have identical
  columns and identical values to the committed versions; the clip numbering is unchanged, so the
  mp3s already prepared are still valid. The only difference is line endings: the old files came
  from Python's `csv` module (CRLF), the notebook writes via pandas (LF).
- **Switches then set back to `False`** at the user's request, and the notebook re-executed in
  that configuration (43 s) so the saved outputs match the switches shown. It still streams 04043,
  composes both clips, draws all five figures, and loads the 14-row result table from
  `output/examples_summary.csv`. The audio, score plots and study mp3s from the full run stay on
  disk; a reader sees real results without a four-minute wait.

### 2026-10-09 · The notebook replaces the package

- **The user's instruction:** keep one notebook with the whole workflow and its supporting files,
  and remove what is no longer needed.
- **Deleted** the `ecgmusic/` package (11 modules) and `main.ipynb`. Both are in git history at
  `aff587b` if they are ever wanted back.
- **The notebook now owns the workflow.** It writes to `output/` rather than a separate folder,
  and gained the last missing piece: `load_forms_csv` and `load_study_key`, so a Google Forms
  export can be dropped in as `responses.csv` and analysed without leaving the notebook. 59 cells.
- **Updated every reference** in [README.md](README.md), [Plan.md](Plan.md),
  [project_description.md](project_description.md) and
  [listening_study_questions.md](listening_study_questions.md): module paths became notebook
  sections, the command-line sections became notebook usage, and the project-structure trees were
  rewritten. All relative links were re-checked and resolve.
  - `sprint3/` was deliberately **not** touched: those reports were submitted and describe the
    project as it stood then.
  - Older entries in this log still name `ecgmusic` and `main.ipynb`, which is correct history;
    only the dead links were turned into plain text.
- **Verified by running it**, not by assuming: all 59 cells compile, the notebook was extracted
  and executed top to bottom against `output/`, and it reproduces 04043, the 7-of-7 valence and
  arousal result and record 219's inversion. The Forms path was exercised on a simulated export
  from 12 synthetic listeners; that file was deleted.
- **`responses.csv` is gitignored** — real responses could identify classmates.

### 2026-10-09 · One self-contained notebook; WAVs removed

- **Removed the generated WAV files** at the user's request: `output/` went from 187 MB to 8.2 MB.
  They were already gitignored, so nothing changed in git, and the 16 study mp3s were untouched.
  `python -m ecgmusic build` regenerates them. Note that `build_study.py` reads `melody.wav`, so
  rebuilding the blinded clip set now needs that run first.
- **Wrote [sonifying_the_heart.ipynb](sonifying_the_heart.ipynb)** — the user asked for one
  notebook holding everything, rather than code spread across modules. 57 cells (28 markdown,
  29 code), self-contained: it imports nothing from `ecgmusic/` and duplicates the full pipeline
  inline, so it can be read, run or handed over on its own.
  - Every parameter in one cell with the reasoning beside it; the sonification rule written out
    as a formula; a sanity-check table showing deviation → pitch before any heartbeat is involved.
  - Covers all four stages, the full 14-piece experiment, record 219, and the listening study
    (building the blinded set and analysing the ratings).
  - Expensive steps sit behind `RENDER_AUDIO`, `BUILD_ALL` and `BUILD_STUDY`, all off by default.
  - Writes to `output_nb/`, now gitignored, so a notebook run never disturbs `output/`.
  - Closes with what the project has and has not shown, stated plainly.
- **Verified, not assumed.** Every code cell compiles; the notebook was then extracted and
  executed top to bottom. It reproduces 04043 (RMSSD 8.5 / 134.9 ms, calm / tense, chords 14/0/0
  and 6/10/0), the 7-of-7 valence and arousal result, and record 219's inversion. `analyse_ratings`
  was exercised separately on synthetic listeners; those numbers were fake and were deleted.
- **Still open:** the user asked for the notebook "instead of modular py files", but `ecgmusic/`
  and `main.ipynb` were left in place rather than deleted — that choice is theirs to confirm.
- **Not done:** Essentia and music2emo still not re-run.

### 2026-10-08 · The code runs, and the listening study is built

- **The venv was broken.** `venv/` was created against Python 3.12, but `/usr/bin/python3` now
  points at 3.14 and 3.12 is gone from the system, so every import failed. Built `venv314/` with
  Python 3.14.4; pip resolved wheels at the pinned versions (numpy 2.5.3, scipy 1.18.1,
  wfdb 4.3.1, pretty_midi 0.2.11.post0, matplotlib 3.11.2). The old `venv/` was left alone.
- **The rewrite reproduces the first implementation exactly.** `python -m ecgmusic build
  --no-essentia` wrote all 14 examples, and **every** valence, arousal and chord count matches
  [§11.1](project_description.md#111-heartbeats-music-and-our-model) — including 08455's
  borderline `happy_excited` at (+0.07, +0.02). The "written but never run" risk is closed.
  Essentia and music2emo were skipped as the heavy steps, so §11.2 and §11.3 are still unchecked.
- **Record 219 regenerated too**, into `output/record219_excluded.csv`: RMSSD 270.6 ms for the
  clip labelled normal against 145.9 ms for the AFib clip, chords 3/2/2 against 9/1/0, and the
  inversion intact — the normal-labelled clip reads `tense_anxious`, the AFib one `calm_relaxed`.
- **The listening study was built** (`output/listening_study/`):
  - 16 clips: the 14 published plus both 219 clips as a hidden control.
  - **Plain melody, not the arrangement.** `melody.wav` renders on `PIANO_PROGRAM`, so the melody
    instrument is not the one our own emotion model picked. That removes the circularity
    [§11.2](project_description.md#112-essentia) warns about: the only thing varying between
    clips is the heart.
  - Converted to mono 96 kbps mp3 (6 MB total) and renamed `clip_01`..`clip_16`, in one fixed
    random order with no two clips from the same record adjacent. `KEY.csv` holds the mapping and
    must not be shown to participants. It is committed at the user's decision; the mp3s are not,
    since `ecgmusic/build_study.py` regenerates them deterministically.
  - A rating page was published, collecting responses centrally. Four questions per clip:
    pleasantness and energy (1-9, the DEAP/DREAMER scale), a forced choice between calm/tense/
    happy/sad (our four quadrants), and perceived rhythmic steadiness (1-9). The steadiness
    question separates "can they hear the irregularity" from "does it move their emotion" —
    two different claims.
  - Listeners are told nothing about hearts until they finish.
- **`ecgmusic/listening_study.py`** analyses the result: Spearman between model and listener
  means, a paired Wilcoxon per record, forced-choice hit rate against 25% chance, and the 219
  control. Exercised on 18 synthetic listeners to check it runs; **those numbers were fake and
  were deleted.** No real listeners yet.
- **Google Form instead of the published page.** At the user's request the circulated instrument
  is a Google Form they build themselves: [listening_study_questions.md](listening_study_questions.md)
  has the exact titles, scales, options, debrief text and audio-hosting steps. The question titles
  must keep their `clip_NN` prefix, because `listening_study.py` now parses Google Forms' own wide
  CSV export by finding that prefix in each column header. Both the Forms shape and the
  per-listener JSON shape were exercised on synthetic listeners, then deleted.
- **[Plan.md](Plan.md) written** — the project start to finish, what it has and has not shown, the
  two projects inside it, and six future steps each with what we could conclude from every
  outcome, including the ones that go against us.
- **Not done:** nothing committed. `output/listening_study/*.mp3` is 6 MB of regenerable audio
  that `.gitignore` does not currently exclude.

### 2026-10-08 · EEG direction explored and dropped; listening study chosen

- **Explored.** At the user's request we researched EEG-based work (EEG → music → emotion) and
  wrote a 20-page Word document arguing for it. The research is worth keeping in mind: EEG supplies
  both axes of Russell's plane directly (valence from frontal alpha asymmetry, arousal from the
  frontal beta/alpha ratio), where HRV supplies only arousal; and the EEG emotion datasets (DEAP,
  SEED, DREAMER, AMIGOS, MAHNOB-HCI) are far richer than ours.
- **Dropped, by the user's decision.** `EEG_vs_ECG_Proposal.docx` was deleted. Reasons that stand:
  - EEG sonification is a *more* crowded field than ECG sonification (1934; Lucier 1965; Miranda's
    BCMI), so switching would not make the project more novel;
  - too little time remains, and the ECG code has still never been run.
- **Decided instead: the listening study is the main deliverable.** The project's own claim —
  that the music carries the rhythm's character — has never been tested on a human listener. That
  is the gap that belongs to the sonification itself, and it is cheap to close.
- **Also settled in discussion:** the project is really two projects. Project 1 (the sonification)
  is the deliverable and is nearly done; Project 2 (inner emotion detection) is the research
  question and stays as future work. Novelty is not the bar for the course deliverable; honest
  execution is.
- **Not done:** nothing committed; the study is designed but not run; the code still has not been
  executed.

### 2026-10-01 · Sprint 3 reports

- **The request.** The user shared the Sprint 1 and Sprint 2 submissions and asked for four
  LaTeX documents, kept as short as those:
  - a team report, `Sprint3`;
  - one individual contribution report per member, `<roll number>_Sprint3`.
- **What was written.** All four are in `sprint3/`, compiled with `pdflatex`. LaTeX build files
  were removed.
  - The team report (3 pages) covers the four-stage pipeline, the results table, the changes from
    the Sprint 2 plan, next steps and contributions.
  - Each individual report is 1 page: role, what was done, key result, next steps.
- **The split of the work.** The user asked me to divide it, so it follows the pipeline stages:
  - Chervith Reddy: ECG data and heartbeats;
  - Manidhar Sukasi: music and integration;
  - Sathwik Reddy: emotion and evaluation.
- **Later change:** at the user's request, the GitHub link was removed from the team report.
- **Not done:** nothing committed.

### 2026-10-01 · Everything committed

- The user asked to commit everything. All the work went into one commit on a new branch,
  `claude/inner-emotion-rewrite`, rather than straight onto `main`. It contains:
  - the `ecgmusic/` package and `main.ipynb`;
  - the new `README.md`, `project_description.md` and this file;
  - the updated `requirements.txt` and `.gitignore`;
  - the removal of `PRESENTATION.md`, `PROGRESS.md` and `music_workshop.pdf`, which the user had
    deleted.
- Fixed a stale `.gitignore` comment that still named the deleted `src/download_db.py`.
- Nothing was pushed to GitHub.

### 2026-10-01 · New documentation, a bug fix and a data correction

- **What the user asked.** The user moved the old documents and generated folders to the Trash:
  `PRESENTATION.md`, `PROGRESS.md`, `DATASET_AND_ETHICS_NOTES.md`, `music_workshop.pdf`,
  `requirements.txt`, `output/`, `data/` and `models/`. They then asked for new files written for
  the inner-emotion framing: this `Progress.md` and `project_description.md`.
- **Wrote [project_description.md](project_description.md).** It is the full description, stage
  by stage:
  - motivation, research questions, and what changed since the proposal;
  - every stage and parameter;
  - the result tables, the comparison of the three models and a discussion;
  - a validation plan, where the data comes from, and ethics (including use with autistic people);
  - limitations, future work and how to reproduce the results.
- **Recreated `requirements.txt`.** It has the same pins as before, because the README's install
  step needs it.
- **Did not recreate `output/`.** Its numbers came from the first implementation. They now live in
  project_description.md §11 with their origin stated, and running the pipeline regenerates
  `output/`.
- **Bug fixed: Essentia's "sad" and "relaxed" were inverted.**
  - **Cause.** Each Essentia mood classifier outputs two probabilities, in a model-specific order
    (`happy, non_happy`; `non_sad, sad`; `non_relaxed, relaxed`; `aggressive, not_aggressive`).
    This was checked against the models' own metadata files. The code always read the first one,
    so "sad" and "relaxed" were really *not* sad and *not* relaxed.
  - **Fix.** `config.MOOD_COLUMNS` now names the right column for each mood, and
    `essentia_models.py` uses it.
  - **Saved results.** They were corrected as 1 minus the saved value, which is exact because the
    two probabilities sum to 1. The valence/arousal model (DEAM) was checked too and was already
    correct, so the three-way comparison is unchanged.
  - **Corrected findings.**
    - "Relaxed" is every piece's strongest mood.
    - AFib melodies sound happier, more aggressive, less sad and less relaxed than the normal
      ones, in all 7 recordings.
    - The arrangement makes the normal pieces even calmer: relaxed 0.97–0.98, sad 0.90–0.93.
  - **Withdrawn claims.** "Every clip's strongest mood is sad" and "the arrangement lowers the
    normal pieces' sadness by about 70%". Both came from the inverted columns.
- **Data correction: 6 people, not 7.**
  - PhysioNet's header for `mitdb` record 202 says it "was taken from the same analog tape as
    record 201". Both records are from a 68-year-old man.
  - So the 7 recordings come from 6 people. Comparisons are now described per recording.
- **Updated the other files to match.**
  - [README.md](README.md): links to the new documents; corrected Essentia findings and people
    count; a note on where the numbers come from.
  - `main.ipynb`: new links. It now builds the examples itself when `output/` is
    missing, and the pretrained-model sections explain how to create their tables instead of
    failing. Corrected Essentia text and people count.
  - `ecgmusic/__main__.py`: the warning printed after an analysis now points to
    project_description.md.
- **Checks.** Static only, nothing executed:
  - `compile()` on every module and every notebook code cell;
  - the notebook's JSON is valid;
  - every relative link and section anchor in the three Markdown files resolves.

### 2026-10-01 · README rewritten around inner emotion detection

- The user clarified the flow: **ECG data → Heartbeats → Music → Emotion**, an inner emotion
  detection project.
- The README was rewritten around those four stages. It gained a worked example for one person,
  the results, an honest validation-status section, and the emotion-labelled ECG datasets for the
  next step (WESAD, DREAMER, AMIGOS).

### 2026-10-01 · Old code removed from git

- The user asked to remove all old code. With their explicit permission, the removal alone was
  committed: `b572a24 remove old src/ implementation`. It deletes the old `src/` files and
  `notebooks/.gitkeep`, and nothing else.

### 2026-10-01 · From-scratch rewrite: the `ecgmusic` package and `main.ipynb`

- **The user's instruction:** rewrite the whole codebase from scratch, writing code only and
  running nothing, because this machine is low on compute.
- **New package**, organised by responsibility:
  - `config` (every parameter) and `data` (Stages 1–2);
  - `melody`, `arrangement`, `audio` and `plots` (Stage 3);
  - `emotion`, `essentia_models` and `music2emo_crosscheck` (Stage 4);
  - `pipeline` and a command line (`python -m ecgmusic {download,build,analyze}`).
- **Same rules and parameters** as the verified first implementation, now built on dataclasses.
- **New features:**
  - records are streamed instead of downloaded;
  - `--no-audio` for MIDI and plots without FluidSynth;
  - CSV input;
  - a clear error when FluidSynth is missing;
  - an `ECGMUSIC_SOUNDFONT` override;
  - a valence–arousal plot of all examples.
- **`main.ipynb`:** a 40-cell walkthrough with detailed explanations. The expensive
  steps sit behind four switches that are off by default. It is saved without outputs.
- **Two earlier claims corrected while writing:**
  - Tempo example: record 201's AFib clip (101 bpm) is slower than 04043's normal clip (108 bpm).
  - It is the *standard deviation* of a normal melody's pitches that is at most 2 semitones, not
    its distance from the average.

### 2026-10-01 · Three-part arrangement; two melody bugs fixed

- **Arrangement.**
  - Melody, plus strings playing C–Am–F–G. A chord turns diminished at 12% average deviation and
    into a cluster at 25%. Normal rhythm never went above 5.5%.
  - A lub-dub bass-drum pulse on every beat.
  - Mix measured on 04043: strings 7–9 dB and pulse 12–17 dB below the melody.
- **Two melody bugs fixed.**
  - Faster beats went *down*, the opposite of the design.
  - Downward "pentatonic" steps mirrored the intervals (B♭, A♭) instead of walking down the scale
    (A, G).
- **Regression check.** RMSSD, note counts, % chromatic and emotion quadrants were identical before
  and after; only the pitches changed, as intended. Essentia and music2emo were re-run on the new
  pieces.

### 2026-10-01 · Repository cleanup

- Removed the 2.3 GB music2emo checkout after its results were saved, plus leftover files.
- Added the missing `essentia-tensorflow` pin to `requirements.txt`.

### 2026-10-01 · Any ECG file; where the data comes from

- **Automatic heartbeat detection (XQRS)** for any recording, so no annotation files are needed.
  We checked it on record 04043 with its annotations hidden:
  - first 30 s: 53 beats, 559 ms, 14.2 ms, against 54, 559 ms and 13.8 ms annotated;
  - a window inside AFib: 205.8 ms, read as tense.
- **Data provenance.** We researched who the databases come from, using PhysioNet's pages and the
  original papers. They contain adult cardiac patients only, with no emotional, psychological or
  neurodevelopmental data.
- **HRV and autism.** We gathered research on heart-rate variability in autism, for the user's
  idea of using the tool with autistic people. Any such use needs its own validation and ethical
  review.

### 2026-10-01 · Stage 4: emotion read from the music

- **The user's request:** map the generated music to emotion using open models, and change the
  instruments if needed.
- **Our model:**
  - Russell's circumplex, with cues from Gabrielsson & Lindström: rhythmic irregularity, pitch
    spread and consonance.
  - Tempo and loudness are left out on purpose.
  - Result: normal 7 of 7 calm, AFib 6 of 7 tense.
- **Essentia:** four mood classifiers and DEAM valence/arousal.
- **music2emo**, in its own environment:
  - older pinned libraries;
  - `mir_eval` from PyPI, because installing from a git URL was blocked;
  - `setuptools<81`, which restores `pkg_resources`.
- **Three-way comparison:** every method hears a difference between the rhythms, but no two agree
  on both valence and arousal.
- **Instrument by emotion:** calm gets nylon guitar, tense distortion guitar, happy marimba and sad
  cello.
- *Later found:* Essentia's "sad" and "relaxed" columns were read inverted. See the newest entry.

### 2026-09-25 · Extended to `mitdb`

- Annotation reading generalised to `mitdb`, where beats and rhythm changes share one file.
- Only 3 of its 48 records (201, 202, 219) have at least 30 s of both rhythms.
- **Record 219 excluded.** Its steadiest "normal" window (RMSSD 270.6 ms) is more irregular than
  its AFib clip (145.9 ms), because of 133 non-conducted P-waves.

### 2026-09-25 · Robustness and audio quality

- Note loudness now uses the local ECG maximum within ±5 samples of each beat.
- One bad record no longer stops a batch.
- Audio is normalised to an 85% peak; raw renders peaked at only about 5%.

### 2026-09-25 · Five records; clip selection fixed

- Running 5 `afdb` records exposed a data-quality problem. Taking the first 30 s made two
  "normal" clips more irregular than AFib (04015: 199 ms against 105 ms), because of `afdb`'s
  automatic beat marks.
- **Fix:** keep the steadiest normal window and the AFib window with the most detected beats.
- **After the fix:** normal 7.6–18.6 ms against AFib 99.9–141.9 ms.

### 2026-09-25 · First heartbeats and first melody

- R-R intervals and RMSSD for record 04043. Its first labelled windows gave 13.8 ms (normal)
  against 194.7 ms (AFib).
- First melody mapping, MIDI and audio.
- The full `afdb` download finished: 123 files, about 625 MB.

### 2026-09-24 · Setup and data access

- Read the proposal and turned it into a phased plan.
- Python 3.12.3 virtual environment and packages. The user installed FluidSynth 2.3.4 and the
  FluidR3 GM soundfont.
- **Download speed.** PhysioNet allows about 20 KB/s per connection, and `wfdb`'s downloader opens
  only two. We wrote a parallel `curl` downloader, and used streaming via `pn_dir` for quick looks.

---

## Known issues

- **Calm can sound tense.** Healthy, breathing-locked variability would be read as tension
  ([project_description.md §12](project_description.md#12-discussion-from-the-musics-emotion-to-inner-emotion)).
- **The three emotion models disagree** on which emotion separates the rhythms.
- **`afdb`'s heartbeat marks are unaudited.** Clip selection avoids most glitches, but not all.
- **The rewritten code has not reproduced the results yet.**
- **Older entries use uncorrected Essentia numbers.** Older entries in this log, and any copies of
  the old documents, describe Essentia's "sad" and "relaxed" before the fix. The corrected values
  are in [project_description.md §11.2](project_description.md#112-essentia).
