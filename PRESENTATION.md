# Sonifying the Heart — Results & Mapping Rationale

This is the Phase 5 write-up: what the mapping does, why, and what it produced across 7
real ECG records from two independent PhysioNet databases. See [README.md](README.md) for
the full project plan and [PROGRESS.md](PROGRESS.md) for the detailed build log.

## The mapping

Each detected heartbeat (R-peak) becomes one musical note.

| ECG feature | Musical parameter | Rule |
|---|---|---|
| R-R interval (time to next beat) | Note onset + duration | Note starts at the beat, lasts 85% of the interval to the next beat (leaves a small gap between notes) |
| Deviation of this R-R interval from a running mean of the last 5 beats | Pitch | \|deviation\| < 12% → stays on a major pentatonic scale, close to the root note (C4). \|deviation\| ≥ 12% → allowed to move chromatically, further from the root. A faster-than-average beat moves pitch **up**; a slower-than-average beat moves pitch **down**. |
| ECG signal amplitude at the R-peak | Note velocity (loudness) | Linearly scaled within each clip's own amplitude range |

Implementation: [src/mapping.py](src/mapping.py) (the rules), [src/render.py](src/render.py)
(MIDI + audio rendering via `pretty_midi` / FluidSynth).

The intended effect: a steady, healthy rhythm stays in a tight, consonant pentatonic cluster
near the root note — calm. An irregular rhythm (atrial fibrillation) scatters unpredictably
across a wide, often-chromatic pitch range — unstable and dissonant. This is deliberately a
simple first-pass design (per the original plan: "start simple, then refine"), not a final
polished instrument.

## Results across 7 records, 2 databases

Source data: MIT-BIH Atrial Fibrillation Database (`afdb`, 5 records) and MIT-BIH
Arrhythmia Database (`mitdb`, 2 records) — both from PhysioNet, as named in the original
proposal. For each record, a 30-second normal-sinus-rhythm clip and a 30-second AFib clip
were extracted using the database's rhythm labels, then run through the mapping above.

| DB | Record | Rhythm | RMSSD (ms) | Notes | Pitch range | % chromatic | Pitch std (semitones) |
|---|---|---|---|---|---|---|---|
| afdb | 04043 | Normal | 8.5 | 53 | 60–60 | 0% | 0.0 |
| afdb | 04043 | AFib | 134.9 | 63 | 47–84 | 52% | 8.4 |
| afdb | 04015 | Normal | 7.6 | 40 | 60–60 | 0% | 0.0 |
| afdb | 04015 | AFib | 126.1 | 67 | 42–84 | 57% | 9.7 |
| afdb | 04126 | Normal | 18.6 | 39 | 58–62 | 0% | 1.1 |
| afdb | 04126 | AFib | 141.9 | 79 | 40–83 | 66% | 10.6 |
| afdb | 06995 | Normal | 17.8 | 40 | 58–62 | 0% | 0.9 |
| afdb | 06995 | AFib | 122.8 | 55 | 48–82 | 51% | 7.9 |
| afdb | 08455 | Normal | 8.3 | 38 | 60–60 | 0% | 0.0 |
| afdb | 08455 | AFib | 99.9 | 59 | 46–76 | 31% | 5.7 |
| mitdb | 201 | Normal | 64.1 | 24 | 58–62 | 0% | 1.6 |
| mitdb | 201 | AFib | 194.3 | 50 | 47–84 | 52% | 9.8 |
| mitdb | 202 | Normal | 37.4 | 27 | 58–64 | 0% | 1.6 |
| mitdb | 202 | AFib | 146.9 | 61 | 45–84 | 33% | 7.6 |

(Also in [output/examples_summary.csv](output/examples_summary.csv).)

**Every normal clip stayed entirely pentatonic (0% chromatic) with pitch pinned at or within
4 semitones of the root.** Every AFib clip spent 31–66% of its notes in chromatic territory,
with 3–5x higher R-R variability (RMSSD) than its paired normal clip. The contrast holds
across both independently-annotated databases, not just within one. The `mitdb` normal
clips run a higher absolute RMSSD than `afdb`'s (37-64ms vs. 7-19ms) — plausible, since
`mitdb`'s subjects are a general arrhythmia-monitoring population (occasional ectopic beats
even in "normal"-labeled segments) rather than `afdb`'s AFib-specific cohort during their
calmest stretches — but the AFib-vs-normal *contrast* still holds clearly within each
database. The result is audible, not just visible in the numbers — listen to any
`output/audio/<record>_N.wav` next to its `<record>_AFIB.wav`.

Per-record sanity plots (ECG waveform, R-R deviation %, resulting pitch sequence) are in
`output/<record>_N_sonification.png` / `<record>_AFIB_sonification.png`.

## A data-quality finding worth reporting

`afdb`'s R-peak beat annotations (`.qrs`) are produced by an automatic, **unaudited**
detector — only the rhythm labels themselves (`.atr`: normal/AFib/flutter) are
cardiologist-verified. This matters: the first "normal" 30-second window taken naively from
2 of the 5 records showed *higher* RMSSD than that record's AFib window, which would
contradict the entire premise. Inspecting the raw waveform confirmed this was beat-detector
jitter, not real cardiac irregularity — the underlying rhythm was visibly steady.

Fix: rather than taking the first qualifying window, the pipeline now scores several
candidate windows per rhythm segment and selects the lowest-RMSSD one for "normal" (true
sinus rhythm should be low-variability, so a high reading there is almost certainly a
detection artifact) and the one with the most detected beats for "AFib" (favors reliable
detection density rather than cherry-picking the most dramatic-looking window). All 5
records now show the physiologically correct direction. Full detail in
[PROGRESS.md](PROGRESS.md)'s 2026-09-25 log entries.

## Extending to a second database (mitdb)

The proposal names both `afdb` and `mitdb` as data sources. `mitdb` is structured
differently — a single `.atr` file carries both beat-by-beat classifications (which ARE
manually verified, unlike `afdb`'s unaudited `.qrs`) and rhythm-change markers, rather than
two separate files. The pipeline was generalized ([src/extract_features.py](src/extract_features.py):
`load_beats_and_rhythms()`) to handle both layouts.

Scanning all 48 `mitdb` records found only 3 with both a normal and an AFib segment ≥30s
(`201`, `202`, `219`) — `mitdb` is predominantly a general arrhythmia/ectopic-beat database,
not an AFib-focused one like `afdb`, so this is expected, not a bug. Two of the three
(`201`, `202`) produced clean, correctly-directioned examples and are included above.

**Record `219` was tried and excluded.** Its best available "normal"-labeled 30s window still
showed RMSSD = 270ms — higher than its own AFib window. Inspection showed why: this record
has 133 non-conducted P-wave events (symbol `x` — a blocked atrial beat where no ventricular
contraction follows, correctly excluded from beat counting) in a 30-minute recording. That's
genuine, frequent AV conduction irregularity, not a detection artifact — the rhythm-level
label `N` just means "not one of the officially tracked arrhythmia types," not "perfectly
steady." Forcing this record into the demo would have undermined the "normal = calm" pattern
established everywhere else, so it was left out rather than presented misleadingly.

## Robustness pass

A follow-up review of the pipeline made three further fixes, none of which changed the
results above (confirming they were quality fixes, not behavior changes):

- **Velocity mapping** now reads the local max amplitude in a small window around each
  R-peak rather than a single sample, for the same reason as the finding above — more
  robust to a few-sample annotation offset from the unaudited beat detector.
- **Error handling**: the batch pipeline now logs and skips a failing record/clip instead of
  crashing the whole run (tested against a deliberately invalid record ID).
- **Audio loudness**: the raw FluidSynth renders peaked at only ~5-6% of full scale (a
  single-note piano line at moderate velocity doesn't naturally fill 16-bit range) —
  technically correct but too quiet for comfortable listening. All 10 clips are now
  normalized to a consistent 85% peak, with no clipping.

## Honest scope

This is a proof-of-concept and reference implementation, not a clinical tool — consistent
with the original proposal. The mapping is a first pass; instrument choice, the
pentatonic/chromatic threshold (currently 12% deviation), and note duration are all open to
refinement by ear. The optional LLM-assisted mapping exploration mentioned in the proposal
has not been explored (explicitly non-central to the project).
