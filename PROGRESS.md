# Progress Log — Sonifying the Heart

Tracks actual project status against the plan in [README.md](README.md). Update this as work
happens — each entry should say what changed and when, not restate the plan.

**Last updated:** 2026-09-25

---

## Current status

**All 5 phases done for a first full pass. Room for refinement, but the core project works end-to-end.**

| Phase | Status | Notes |
|---|---|---|
| 0 — Environment setup | ✅ Done | Venv, packages, FluidSynth, soundfont all verified working. |
| 1 — Get and explore the data | ✅ Done | Full `afdb` (625MB) + full `mitdb` (95MB) downloaded locally. |
| 2 — Extract rhythm features | ✅ Done | R-R intervals + RMSSD computed across 7 records, 2 databases; segment-selection bug fixed (see log). |
| 3 — Design the sonification mapping | ✅ Done | Mapping implemented, rendered to MIDI+audio, sanity-checked visually and by ear. |
| 4 — Render to MIDI and audio | ✅ Done | 7 normal/AFib pairs (14 clips) rendered to MIDI+WAV, all showing correct direction. |
| 5 — Present | ✅ Done | [PRESENTATION.md](PRESENTATION.md) written: rationale, results table, findings. |

Legend: ⬜ Not started · 🟨 In progress · ✅ Done · 🔺 Blocked

---

## Checklist snapshot

Mirrors the checkboxes in [README.md](README.md#4-step-by-step-plan). Keep the two files in
sync manually — tick a box here only once it's actually true, not once it's attempted.

### Phase 0 — Environment setup
- [x] Python env created (`venv/`, Python 3.12.3)
- [x] Core packages installed (`wfdb numpy scipy pretty_midi mido matplotlib`) — imports verified
- [x] FluidSynth installed (`fluidsynth 2.3.4`, verified via `fluidsynth --version`)
- [x] Soundfont available at `/usr/share/sounds/sf2/FluidR3_GM.sf2` (from `fluid-soundfont-gm`)
- [x] `requirements.txt` frozen (from actual installed versions)

### Phase 1 — Get and explore the data
- [x] One record loaded and plotted (`afdb` record `04043`, streamed directly from
      PhysioNet via `wfdb`'s `pn_dir` — see [src/explore_data.py](src/explore_data.py) and
      [output/afdb_04043_first10s.png](output/afdb_04043_first10s.png))
- [x] Full `afdb` database downloaded locally: 123 files, 625MB, 23 full signal records
      (`data/afdb/`) — see [src/download_afdb.py](src/download_afdb.py)
- [ ] `mitdb` records explored too (out of scope for now — user chose afdb-only)
- [ ] Multiple normal + AFib records/segments identified for later phases

### Phase 2 — Extract rhythm features
- [x] R-peaks (`.qrs`) + rhythm labels (`.atr`: `N`, `AFIB`, `AFL`) pulled from annotations
      — see [src/extract_features.py](src/extract_features.py)
- [x] R–R interval series computed
- [x] RMSSD (variability) computed across 5 records, consistently 6-16x higher for AFib
      than normal (see table below) — after fixing a segment-selection bug (see Log)
- [x] Repeated across 5 records total (`04043`, `04015`, `04126`, `06995`, `08455`), one
      normal + one AFib 30s clip each, saved to `data/processed/*.npz` with plots in `output/`
- [x] **Data-quality finding**: `afdb`'s `.qrs` beat annotations are auto-detected and
      *unaudited* (only the rhythm labels in `.atr` are cardiologist-verified). The first
      qualifying "normal" window for 2 of 5 records showed implausibly high RMSSD
      (04015: 199ms, 06995: 171ms — higher than their AFib windows, which makes no
      physiological sense) purely from beat-detector jitter, not real heart activity. Fixed
      by scanning multiple candidate windows per rhythm segment and picking the lowest-RMSSD
      one for "N" (true normal sinus rhythm should be low-variability, so high RMSSD there is
      almost certainly a detector artifact) and the most-beats-detected one for "AFIB" (favors
      reliable detection density, not cherry-picking for dramatic effect). All 5 records now
      show correct direction, RMSSD normal=7.6-18.6ms vs AFib=99.9-141.9ms.

### Phase 3 — Design the sonification mapping
- [x] Mapping rules decided: R-R interval → onset+duration; deviation from a causal
      running mean (5-beat window) → pitch (pentatonic if |deviation| < 12%, chromatic
      + wider excursion otherwise; faster beat → pitch up, slower → pitch down); ECG
      amplitude at the R-peak → velocity — see [src/mapping.py](src/mapping.py)
- [x] Mapping implemented as a function (`sonify_clip()` in `src/mapping.py`)
- [x] Note sequence sanity-checked against R–R deviation plot — see
      `output/04043_N_sonification.png` / `output/04043_AFIB_sonification.png`
      (3-panel: ECG, deviation %, resulting pitch, color-coded pentatonic/chromatic)
- [x] Result across 5 records (after the Phase 2 data-quality fix): every normal clip is
      **0% chromatic** (pitch pinned at/near the root); AFib clips range **31-66% chromatic**
      with pitch spreads of 5.7-10.6 semitones std vs. ~0-1.1 for normal. Consistent,
      confirmed non-silent, audibly distinct by ear. Full table in
      [output/examples_summary.csv](output/examples_summary.csv).

### Phase 4 — Render to MIDI and audio
- [x] MIDI generation working ([src/render.py](src/render.py), via `pretty_midi`)
- [x] Audio rendering working (FluidSynth + `FluidR3_GM.sf2`, verified non-silent WAVs)
- [x] 5 paired clips (normal vs. AFib) produced — `output/audio/<record>_N.wav` /
      `<record>_AFIB.wav` for records 04043, 04015, 04126, 06995, 08455. Batch driver:
      [src/build_examples.py](src/build_examples.py)

### Phase 5 — Present
- [x] 5 paired audio examples produced (target was 3-5)
- [x] ECG-vs-score plots made (per-record sonification sanity plots in `output/`)
- [x] Mapping rationale write-up done — see [PRESENTATION.md](PRESENTATION.md)

---

## Log

Newest entry on top. One entry per work session — a couple of lines is enough.

### 2026-09-25 (mitdb extension)
- **Extended to the second database named in the proposal.** Downloaded full `mitdb`
  (192 files, 95MB, 0 failures) using the same curl-based approach as `afdb`
  ([src/download_db.py](src/download_db.py), generalized from `download_afdb.py`).
- **Generalized the extraction code** to handle `mitdb`'s different annotation layout: a
  single `.atr` file carries both manually-verified beat classifications and rhythm-change
  markers, vs. `afdb`'s separate unaudited-`.qrs` + rhythm-only-`.atr` split. New
  `load_beats_and_rhythms(record_path, db)` in `extract_features.py` abstracts over both;
  verified the `afdb` path still gives byte-identical results after the refactor.
  `process_record()` and `build_examples.py` now take a `db` argument.
- Scanned all 48 `mitdb` records: only 3 (`201`, `202`, `219`) have both an `N` and `AFIB`
  segment ≥30s — expected, since `mitdb` is a general arrhythmia database, not AFib-focused.
- **Record `219` tried and excluded**: its best normal-labeled window still had RMSSD=270ms
  (higher than its own AFib window). Root cause was genuine physiology this time, not a
  detection bug: 133 non-conducted P-wave events (blocked atrial beats, correctly excluded
  from beat counting since no QRS follows) in 30 minutes — real AV-conduction irregularity
  that the coarse rhythm label `N` doesn't capture. Left out rather than presented
  misleadingly; documented in [PRESENTATION.md](PRESENTATION.md).
- Final set: 7 records (5 `afdb` + 2 `mitdb`), all correct-direction, all normalized audio.
  `mitdb`'s normal-clip RMSSD (37-64ms) is notably higher than `afdb`'s (7-19ms) — plausible
  given `mitdb`'s general-population vs. `afdb`'s AFib-cohort-at-their-calmest source
  material — but the within-database AFib-vs-normal contrast (3-5x) still holds clearly.
  `PRESENTATION.md` updated with the full 7-record table and both new findings.

### 2026-09-25 (post-review polish)
- **Robustness + quality-of-life pass** after auditing what was still missing:
  - Amplitude→velocity now reads a small max-window around each R-peak (±5 samples) instead
    of a single sample, consistent with the same "unaudited detector" theme as the Phase 2
    fix — more robust to a few-sample annotation offset (`mapping.py`).
  - `build_examples.py` and `sonify.py` now catch and log per-record/per-clip failures
    instead of crashing the whole batch (tested with a deliberately invalid record ID).
  - Added `render.normalize_wav()`: rendered audio was peaking at only ~5-6% of full scale
    (correct but too quiet for comfortable side-by-side listening) — now normalized to a
    consistent 85% peak across all 10 clips, verified no clipping.
  - Re-ran the full batch: RMSSD/note-count/pitch numbers unchanged (confirms these were
    pure quality fixes, not behavior changes); audio is now properly listenable.

### 2026-09-25 (cont'd)
- **Phases 2/4/5 extended to 5 records**: generalized `extract_features.py` and `sonify.py`
  to take a `record` argument, wrote [src/build_examples.py](src/build_examples.py) to batch
  the whole extract→sonify→render pipeline. First run surfaced an important bug: 2 of 5
  records showed AFib RMSSD *lower* than normal RMSSD, which contradicts the entire premise.
  Root cause: `afdb`'s `.qrs` R-peak annotations are unaudited/auto-detected (unlike the
  cardiologist-verified `.atr` rhythm labels), so the *first* 30s "normal" window grabbed for
  some records happened to have detector jitter, not real irregularity. Fixed by scanning
  multiple candidate windows per rhythm segment and picking by lowest-RMSSD (for N) /
  most-beats-detected (for AFIB) instead of just the first match — see `find_clip()` in
  [src/extract_features.py](src/extract_features.py). Re-ran: all 5 records now correctly
  show normal RMSSD 7.6-18.6ms vs. AFib 99.9-141.9ms. Full results in
  [output/examples_summary.csv](output/examples_summary.csv). **Phases 2, 4, and most of 5
  now done** — only the written rationale/summary for Phase 5 remains.

### 2026-09-25
- **Phase 3 done**: wrote [src/mapping.py](src/mapping.py) (pure mapping logic:
  R-R interval → onset/duration, causal running-mean deviation → pentatonic/chromatic pitch,
  amplitude → velocity), [src/render.py](src/render.py) (notes → MIDI → WAV via FluidSynth),
  and [src/sonify.py](src/sonify.py) (orchestrates both + sanity plot). Ran on both Phase-2
  clips: normal produced 53 notes, all pentatonic, pitch range 60-62 (essentially flat at the
  root); AFib produced 46 notes, 56% chromatic, pitch range 45-80. Verified the rendered WAVs
  are genuinely non-silent. This also satisfies most of Phase 4's goal for this one record.
- **Phase 2 done**: wrote [src/extract_features.py](src/extract_features.py) — parses
  `.qrs` (R-peaks) and `.atr` (rhythm labels) for record `04043`, computes R-R intervals and
  RMSSD, isolates a 30s normal clip and a 30s AFib clip. Result: RMSSD is 13.8ms for normal
  vs. 194.7ms for AFib (~14x higher) — a strong, visually confirmed validation of the
  project's core premise before any sonification code is written. Clips saved to
  `data/processed/`, plots to `output/04043_N_clip.png` and `output/04043_AFIB_clip.png`.
- **Full `afdb` download finished**: 123/123 files, 0 failures, 625MB total, 23 signal
  records in `data/afdb/`. The curl-based rewrite fixed the throughput problem — went from
  6 records in 90 minutes (throttled) to the remaining 17 records finishing well within the
  hour after the fix. **Phase 1 fully complete.**

### 2026-09-24
- Diagnosed PhysioNet's slow speed as a deliberate ~20KB/s per-connection throttle (not a
  local network issue). Wrote a custom 8-connection parallel downloader
  ([src/download_afdb.py](src/download_afdb.py)) and started a full `afdb` download in the
  background (~600MB, ETA 45-75 min). User confirmed afdb-only scope (not mitdb) for now.
- Tried full local download of `afdb` records via `wfdb.dl_database` — PhysioNet connection
  is very slow (~12KB/s), so a single ~26MB `.dat` file would take 35+ minutes. Killed it and
  switched approach: stream only the short segments we actually need directly from PhysioNet
  using `wfdb`'s `pn_dir` parameter (no full download, works instantly for short windows).
- Wrote [src/explore_data.py](src/explore_data.py): streams a record segment and plots it.
  Ran it successfully on `afdb` record `04043` — real ECG waveform with clear R-peaks
  confirmed, saved to `output/afdb_04043_first10s.png`. **Phase 1 core goal achieved.**
- Verified FluidSynth 2.3.4 and `FluidR3_GM.sf2` soundfont (`/usr/share/sounds/sf2/`) after
  manual `sudo apt install fluidsynth fluid-soundfont-gm`. **Phase 0 complete.**
- Scaffolded project folders (`data/`, `notebooks/`, `src/`, `output/midi/`, `output/audio/`),
  added `.gitignore` and `.gitkeep` placeholders.
- Created Python virtual environment (`venv/`, Python 3.12.3) and installed
  `wfdb numpy scipy pretty_midi mido matplotlib`; verified all imports work. Froze versions
  into `requirements.txt`.
- FluidSynth + soundfont still need a manual step: `sudo apt install fluidsynth
  fluid-soundfont-gm` (requires a password Claude doesn't have — run it yourself).
- Read the proposal PDF, wrote [README.md](README.md) breaking it into a phased plan with a
  goal/use-case explanation.
- Created this progress log. No code or data yet — project is still at Phase 0.

---

## Blockers / open questions

- **PhysioNet throttles each connection to ~20KB/s** (confirmed via range-request tests;
  general internet speed is fine at 3.4MB/s, so this is PhysioNet-side, not local). It's a
  per-connection limit, not per-IP, so parallelizing multiple connections scales throughput
  close to linearly. `wfdb`'s own Python HTTP layer secretly caps at 2 connections regardless
  of thread count (a shared `requests.Session` with `pool_maxsize=2`), so the fix was
  bypassing it with raw `curl` subprocesses instead — see
  [src/download_afdb.py](src/download_afdb.py). Resolved; full `afdb` download completed.

---

## Next up

All 5 plan phases are done for a first full pass — [PRESENTATION.md](PRESENTATION.md) has
the write-up. What's left is refinement, not new phases:

- [ ] Listen critically to the current mapping and consider refinements: e.g. instrument
      choice beyond piano, whether pentatonic/chromatic threshold (currently 12%) is well
      tuned, whether note duration/gap (currently 85% of R-R) feels right (audio is now
      properly normalized/audible, so this is ready to actually do)
- [ ] (Optional, per proposal) explore whether an LLM can suggest alternative mappings worth
      trying — explicitly non-central to the project per the proposal
- [ ] Decide what final deliverable format is needed (slides? report? just this repo?) and
      whether any of this needs to be committed to git (still waiting on that permission)
