# Sonifying the Heart: Project Description

### Inner emotion detection from ECG through music

> **ECG data → Heartbeats → Music → Emotion**

| | |
|---|---|
| **Course** | Music Workshop |
| **Team** | Chervith Reddy (2024101076) · Manidhar Sukasi (2023101067) · Sathwik Reddy (2024121002) |
| **Code** | [sonifying_the_heart.ipynb](sonifying_the_heart.ipynb) — the whole project in one self-contained notebook |
| **Other documents** | [README.md](README.md): overview, setup and resources · [Progress.md](Progress.md): dated log of the work |
| **Status (9 October 2026)** | All four stages are built, and the code reproduces every result in [§11.1](#111-heartbeats-music-and-our-model) exactly. The emotion stage has not yet been checked against how people actually felt ([§13](#13-validation-plan)); a listening study is built and waiting for listeners. |

---

## Contents

1. [Summary](#1-summary)
2. [Motivation](#2-motivation)
3. [Research questions](#3-research-questions)
4. [From the proposal to this project](#4-from-the-proposal-to-this-project)
5. [System overview](#5-system-overview)
6. [Stage 1: ECG data](#6-stage-1-ecg-data)
7. [Stage 2: Heartbeats](#7-stage-2-heartbeats)
8. [Stage 3: Music](#8-stage-3-music)
9. [Stage 4: Emotion, read from the music](#9-stage-4-emotion-read-from-the-music)
10. [The experiment](#10-the-experiment)
11. [Results](#11-results)
12. [Discussion: from the music's emotion to inner emotion](#12-discussion-from-the-musics-emotion-to-inner-emotion)
13. [Validation plan](#13-validation-plan)
14. [Where the data comes from, and ethics](#14-where-the-data-comes-from-and-ethics)
15. [Limitations](#15-limitations)
16. [Future work](#16-future-work)
17. [Reproducing the results](#17-reproducing-the-results)
18. [References](#18-references)

---

## 1. Summary

This project turns a person's electrocardiogram (ECG) into music. It then reads the emotion
expressed by that music, as a window into the person's inner emotional state. There are four
stages:

1. **ECG data.** A recording from PhysioNet, or any ECG file.
2. **Heartbeats.** The heartbeats (R-peaks) are found. They give the beat-to-beat intervals (R-R)
   and how much those intervals vary (RMSSD).
3. **Music.** Every heartbeat becomes a note.
   - A beat that arrives on time keeps the melody near home, on a calm pentatonic scale. A beat
     that arrives early or late pulls the melody away, and out of the scale.
   - Strings play a C–Am–F–G progression that sours into diminished chords and clusters as the
     rhythm gets irregular.
   - A soft "lub-dub" drum pulse follows every beat.
4. **Emotion.** Our own model places the music on Russell's valence–arousal plane, using three
   musical cues. Two pretrained music-emotion models, Essentia and music2emo, give independent
   second and third opinions.

We tested this on 14 clips of 30 seconds each. They come from 7 recordings of 6 heart patients:
a normal-rhythm clip and an atrial-fibrillation (AFib) clip from each recording. AFib serves as
a natural, expert-labelled example of an irregular heart.

- **The music separates the two rhythms in every recording.**
  - The normal clips stay on the scale, over consonant chords.
  - The AFib clips leave the scale for 31–66% of their notes, and 61% of their chords turn tense
    or chaotic.
- **Our model:** every normal piece reads as calm, and 6 of 7 AFib pieces as tense. The seventh
  is a mild AFib stretch that lands at the centre of the plane.
- **The pretrained models hear the difference in every recording, but describe it differently.**
  - Essentia hears the AFib pieces as livelier and more positive.
  - music2emo hears them as less pleasant and less energetic.
  - No two methods agree on both valence and arousal.
- **Not yet tested:** whether the emotion of the music matches the emotion of the person. The
  recordings come with no emotion reports. [§13](#13-validation-plan) sets out how to test this
  with ECG datasets that have them (WESAD, DREAMER, AMIGOS).

---

## 2. Motivation

**Emotions are inner states.** We usually learn how someone feels by asking them, or by watching
their face and listening to their voice. Some people find this hard. They may struggle to
identify or describe their own feelings, may not speak, or may express emotion differently from
what others expect. A signal from the body that reflects their inner state without words would
be valuable.

**The heart answers to the nervous system that carries emotion.** The heart rate is set beat by
beat by the autonomic nervous system, which has two branches:

- The **sympathetic** branch ("fight or flight") speeds the heart up.
- The **parasympathetic** branch, acting through the vagus nerve, slows it down.

Emotional arousal shifts the balance between the two. That is why heart-rate variability (HRV),
the beat-to-beat change in heart timing, is studied as a marker of stress and of emotion
regulation ([§14.4](#144-using-this-with-autistic-people-or-any-specific-group)).

**Music is a language of emotion that everyone can hear.** Music psychology describes the
emotion in music on two axes: **valence** (unpleasant to pleasant) and **arousal** (calm to
energetic) (Russell, 1980). It also knows which musical features push music along each axis
(Gabrielsson & Lindström, 2010). And there are trained models that recognise emotion in audio.

**The idea.** Let the heartbeat compose music, using rules taken from music-emotion research.
What the nervous system does to the heart then becomes something we can hear, and the emotion
of that music can be read. This gives:

- **An audible window:** anyone can hear a calm or an agitated heart, with no ECG training.
- **A measurable one:** the emotion of the music can be estimated, and cross-checked by
  independent models.

**Why not read the emotion from the HRV numbers directly?** That is the established research
route, and our validation plan uses it as the baseline to beat ([§13](#13-validation-plan)).
Going through music adds the audible window, the heart of a Music Workshop project, plus decades
of knowledge about how music carries emotion. It also adds assumptions, which is why the last
step is validated on its own.

---

## 3. Research questions

| | Question | Status |
|---|---|---|
| RQ1 | **Audibility.** Does a steady heart produce clearly different music from an irregular one? | **Yes**, in all 7 recordings ([§11.1](#111-heartbeats-music-and-our-model)) |
| RQ2 | **Consistency.** Does the emotion read from the music move consistently with the heart's rhythm? | **Yes for our model:** AFib pieces have lower valence and higher arousal in all 7 recordings ([§11.1](#111-heartbeats-music-and-our-model)) |
| RQ3 | **Agreement.** Do independent music-emotion models hear the same emotion? | **Partly.** All three hear a difference in every recording but disagree on which emotion it is ([§11.4](#114-do-the-three-methods-agree)) |
| RQ4 | **Validity.** Does the emotion read from the music match how the person actually felt? | **Not tested yet** ([§13](#13-validation-plan)) |

---

## 4. From the proposal to this project

Our Sprint 1 proposal, *Sonifying the Heart: Turning ECG Data into Music*, set out to make a
healthy and a diseased heart rhythm *audibly* different. Its intended uses were teaching
arrhythmia recognition, accessibility for visually impaired clinicians, and eyes-free monitoring.
Stages 1–3 implement that proposal. Stage 4 extends it into inner emotion detection.

| In the proposal | Where it is now |
|---|---|
| afdb and mitdb from PhysioNet, read with `wfdb` | Stage 1 ([§6](#6-stage-1-ecg-data)) |
| R-R intervals and RMSSD; segments chosen by rhythm label | Stage 2 ([§7](#7-stage-2-heartbeats)) |
| R-R intervals set note onsets and durations | Stage 3, melody ([§8.2](#82-melody-one-note-per-heartbeat)) |
| Deviation from a running mean sets the pitch: pentatonic when stable, chromatic when irregular | Stage 3, melody ([§8.2](#82-melody-one-note-per-heartbeat)) |
| ECG amplitude sets note velocity | Stage 3, melody ([§8.2](#82-melody-one-note-per-heartbeat)) |
| Beat-to-beat variability decides how consonant or dissonant the harmony is | Stage 3, harmony with tension tiers ([§8.3](#83-arrangement-harmony-and-pulse)) |
| MIDI with `pretty_midi`, audio with FluidSynth | Stage 3 ([§8.4](#84-audio)) |
| Paired audio examples, and plots that align the ECG with the score | 14 pieces, each with a score plot ([§8.5](#85-the-score-plot), [§10](#10-the-experiment)) |
| *Optional:* an LLM that suggests alternative mappings | not done |
| (not in the proposal) | **Added:** Stage 4, the emotion read from the music, with two pretrained models as cross-checks ([§9](#9-stage-4-emotion-read-from-the-music)) |
| (not in the proposal) | **Added:** any ECG file, with automatic heartbeat detection ([§7.1](#71-finding-the-heartbeats)) |
| (not in the proposal) | **Added:** a three-part arrangement whose melody instrument follows the detected emotion ([§8.3](#83-arrangement-harmony-and-pulse)) |

---

## 5. System overview

```
┌──────────────┐   ┌──────────────────┐   ┌──────────────────────────┐   ┌──────────────────────────┐
│ 1. ECG data  │──►│ 2. Heartbeats    │──►│ 3. Music                 │──►│ 4. Emotion               │
│              │   │                  │   │                          │   │                          │
│ PhysioNet    │   │ R-peaks          │   │ melody: 1 note per beat  │   │ our model: valence,      │
│ record, or   │   │ R-R intervals    │   │ harmony and pulse        │   │   arousal, quadrant      │
│ any ECG file │   │ RMSSD            │   │ MIDI · WAV · score       │   │ Essentia · music2emo     │
└──────────────┘   └──────────────────┘   └──────────────────────────┘   └──────────────────────────┘
   samples, fs           Clip                Note, Chord, Track               Emotion, model scores
                                                    ▲                                │
                                                    └───── melody instrument ────────┘
```

There is one feedback edge. The emotion that our model reads from the melody chooses the melody
instrument of the full arrangement. So inside the pipeline the order is: melody, then emotion,
then arrangement.

Everything lives in [sonifying_the_heart.ipynb](sonifying_the_heart.ipynb), which is
self-contained: it imports nothing from this project and runs top to bottom.

| Stage | Notebook section | Main functions | Produces |
|---|---|---|---|
| 1. ECG data | §3 | `record_clips`, `load_signal` | ECG samples and their sampling rate |
| 2. Heartbeats | §3 | `load_annotations`, `choose_window`, `detect_beats`, `clip_from_signal` | `Clip`: the signal, its R-peak positions, and `rr`, `rmssd_ms`, `mean_rr_ms` |
| 3. Music | §4, §6, §7 | `melody`, `arrange`, `render`, `plot_score` | `Note`s, `Chord`s, `Track`s; MIDI, WAV and a score image |
| 4. Emotion | §5 | `estimate_emotion` | `Emotion`: valence, arousal, quadrant and instrument |

§8 chains the stages:

- `compose(clip)` runs melody → emotion → arrangement without writing anything.
- `save()` writes the files.
- `build_examples()` makes the 14 examples and the result table.

§11 builds the listening study and analyses its ratings. Every parameter quoted in this document
sits in a single cell in §2.

---

## 6. Stage 1: ECG data

### 6.1 The two databases

Both databases come from [PhysioNet](https://physionet.org/), the open archive of physiological
recordings maintained by MIT. Both are named in our proposal.

| | MIT-BIH Atrial Fibrillation Database (`afdb`) | MIT-BIH Arrhythmia Database (`mitdb`) |
|---|---|---|
| Content | 25 recordings of about 10 hours; 23 include the ECG signal | 48 half-hour excerpts from 47 people |
| People | adults with atrial fibrillation, mostly paroxysmal (it comes and goes); no age or sex published | 25 men aged 32–89 and 22 women aged 23–89; about 60% inpatients |
| Origin | Beth Israel Hospital, Boston, 1983 | Beth Israel Hospital Arrhythmia Laboratory, Boston, 1975–1979 |
| How the recordings were chosen | people with AFib | 23 at random from 4,000 24-hour recordings, and 25 chosen for rare but clinically important arrhythmias |
| Signal | 2 leads, 250 Hz, 12-bit, about 0.1–40 Hz bandwidth | 2 leads, 360 Hz, 11-bit |
| Heartbeat marks | `.qrs`, from an automatic detector, not corrected by hand | inside `.atr`, checked by two or more cardiologists |
| Rhythm labels | `.atr`, by experts: `N` (normal), `AFIB`, `AFL` (flutter), `J` (junctional) | `+` marks inside `.atr`: `N`, `AFIB` and many others |
| Licence | Open Data Commons Attribution 1.0 | Open Data Commons Attribution 1.0 |

### 6.2 Why compare normal rhythm with atrial fibrillation

Atrial fibrillation is the most common sustained heart-rhythm disorder. The upper chambers
quiver instead of contracting, and the beats of the lower chambers arrive at irregular moments.
That makes it a natural, expert-labelled example of an irregular heart.

Most `afdb` recordings contain both rhythms: 21 of the 23 with a signal have at least 30 seconds
of each. So the same person can be heard in both states. That holds age, physiology, electrode
placement and recording equipment constant. `mitdb` is a general arrhythmia database, and only 3
of its 48 records (201, 202 and 219) have 30 seconds of both.

### 6.3 Getting the data

- **Streaming (default).** A record that is not in `data/` is streamed from PhysioNet with
  `wfdb`'s `pn_dir` option. Only the annotations and the 30-second windows actually used are
  fetched: a few hundred kilobytes per record.
- **Full download (optional).** The databases can be downloaded in full (`afdb` is about 625 MB,
  `mitdb` about 95 MB), but nothing in the notebook needs it.
  - PhysioNet limits each connection to roughly 20 KB/s, and `wfdb`'s own downloader opens only
    two connections. The downloader therefore runs 8 parallel `curl` transfers, which resume
    partial files.
  - Downloaded records are used automatically.

### 6.4 Any ECG file

- **Formats:** a WFDB record (give the path without its extension), or a plain-text or CSV file
  of samples with the sampling rate given as `--fs`. For several columns, pick one with
  `--channel`.
- **Window:** `--start` and `--duration` choose the stretch to use; the default is the first 60
  seconds.
- **Minimum:** at least 5 seconds of signal and 6 detected heartbeats are needed.

---

## 7. Stage 2: Heartbeats

### 7.1 Finding the heartbeats

Each heartbeat appears in the ECG as a sharp spike, the **R-peak**.

- **`afdb`:** the `.qrs` annotation file gives the R-peaks.
- **`mitdb`:** the `.atr` file mixes beat labels with rhythm-change marks. The code keeps every
  beat type as a heartbeat: normal, premature, escape, bundle-branch-block, paced, fusion and
  unclassifiable beats (`NLRBAJSVrFejnE/fQ`). It reads the `+` marks as rhythm changes.
- **Any other recording:** the **XQRS** detector from `wfdb` finds the R-peaks, so no annotation
  file is needed.

**Checking the detector.** We ran XQRS on record 04043 with its annotations hidden.

| Window | Heartbeats | Mean R-R | RMSSD | Read as |
|---|---|---|---|---|
| First 30 seconds, XQRS | 53 | 559 ms | 14.2 ms | calm (valence +0.97, arousal −0.90) |
| First 30 seconds, the database's annotations | 54 | 559 ms | 13.8 ms | |
| 30 seconds from 1070 s, inside AFib, XQRS | | | 205.8 ms | tense |

### 7.2 From heartbeats to rhythm

- **R-R interval:** the time between consecutive R-peaks, about 0.6–1.0 s for a resting heart.
- **Heart rate** = 60 / mean R-R.
- **RMSSD:** the standard measure of beat-to-beat variability.

$$\mathrm{RMSSD} = \sqrt{\frac{1}{N-1}\sum_{i=1}^{N-1}\left(RR_{i+1} - RR_i\right)^2}$$

At rest in normal rhythm, RMSSD is a few tens of milliseconds at most. In AFib it is often well
over 100 ms.

### 7.3 Choosing the 30-second clips

For every recording, one 30-second clip is cut from an expert-labelled normal stretch and one
from an AFib stretch. Up to 5 evenly spaced candidate windows are tried inside each long-enough
stretch, and each needs at least 5 intervals.

- **Normal:** the window with the *lowest RMSSD* wins.
- **AFib:** the window with the *most detected heartbeats* wins.

**Why not just take the first 30 seconds?** That is what our first version did. For two records
the "normal" clip then came out *more* irregular than the AFib clip. For `04015`, for example,
the first normal window had an RMSSD of 199 ms against 105 ms for AFib. The ECG showed a
perfectly steady rhythm with misplaced beat marks: `afdb`'s automatic detector jitters in places.

- Real normal rhythm has low variability, so the steadiest window steps around those glitches.
- In AFib the irregularity is genuine, so we ask only for the best-detected window, never the most
  dramatic one.

### 7.4 The recordings used

| Database | Records | People |
|---|---|---|
| `afdb` | 04015, 04043, 04126, 06995, 08455 | 5 |
| `mitdb` | 201, 202 | 1: both records come from the same tape of a 68-year-old man |

That makes 7 recordings, 6 people and 14 clips.

**Why record 219 is left out.** `mitdb` record 219 also has both rhythms. But even its steadiest
normal window has an RMSSD of 270.6 ms, more than its AFib clip (145.9 ms). Its annotations
explain why: 133 *non-conducted P-waves* in 30 minutes. These are atrial beats that are blocked
before they reach the ventricles, a genuine irregularity that the label "normal" does not
capture. Every later stage flags the record on its own ([§11.5](#115-the-excluded-record-219)).

---

## 8. Stage 3: Music

### 8.1 Design principles

- **The heart is the composer.** Every musical event is caused by a heartbeat, and the timing is
  never quantised: each note starts exactly when the heart beat.
- **Regular means at home, irregular means away.** A beat on time plays the home note C4. The
  further a beat strays from the recent average, the further the melody moves from home and the
  more dissonant the harmony becomes.
- **Keep it music.** A real scale, a real chord progression, a pedal tone and a heartbeat pulse
  make it a piece of music rather than an alarm signal. This matters for a Music Workshop project,
  and for Stage 4: music-emotion knowledge applies to music.

### 8.2 Melody: one note per heartbeat

| From the heartbeat | Becomes |
|---|---|
| The moment of the R-peak | The moment the note starts |
| The R-R interval that follows | The note's length: 85% of the interval, leaving a breath before the next note |
| How that interval differs from the recent average | The note's pitch |
| The ECG amplitude at the R-peak (the maximum within ±5 samples) | The note's loudness: MIDI velocity 40–110, scaled within each clip |

**Pitch.** Beat $i$'s *deviation* compares its interval with the mean of the last five intervals,
itself included:

$$d_i = \frac{RR_i - \overline{RR}_i}{\overline{RR}_i}$$

- **On time** ($d_i = 0$): the root note **C4**.
- **Faster than usual** ($d_i < 0$): the melody moves **up**.
- **Slower than usual** ($d_i > 0$): the melody moves **down**.
- **$|d_i|$ below 12%:** the melody steps along the **C-major pentatonic scale** (C D E G A),
  walking down it as A, G and up it as D, E. In practice this keeps the melody between G3 and E4.
- **$|d_i|$ of 12% or more:** the melody moves **chromatically**. The first note past the
  threshold is F♯, a tritone from C and the most unstable interval there is, so leaving the scale
  is heard at once.
- **The number of steps from C4** is $\operatorname{round}(\min(|d_i| / 0.5,\ 1) \times 2n)$,
  where $n$ is the size of the scale in use (5 or 12). A deviation of 50% or more reaches two
  octaves from C4.
- **The last beat of a clip has no following interval**, so it makes no note.

| Deviation | The beat was | Scale | Note |
|---|---|---|---|
| 0 | on time | pentatonic | C4 |
| −2% | slightly early | pentatonic | C4 |
| −7% | early | pentatonic | D4 |
| −9% | early | pentatonic | E4 |
| +7% | late | pentatonic | A3 |
| +9% | late | pentatonic | G3 |
| −30% | very early | chromatic | D5 |
| +30% | very late | chromatic | A♯2 |
| +50% or more | a long pause | chromatic | C2 |

### 8.3 Arrangement: harmony and pulse

**Harmony (string ensemble).** Every 4 heartbeats get one sustained chord, following the
progression **C – Am – F – G** (I – vi – IV – V), voiced below the melody:

| Chord | Notes |
|---|---|
| C | C3 E3 G3 |
| Am | A2 C3 E3 |
| F | F2 A2 C3 |
| G | G2 B2 D3 |

The chord's colour depends on the average $|d_i|$ of its 4 beats:

| Average deviation | Chord played | Sound | Velocity |
|---|---|---|---|
| below 12% | the progression's chord | consonant | 34 |
| 12% to 25% | a diminished triad on the same root (e.g. C E♭ G♭) | tense: the classic suspense chord | 44 |
| 25% and above | a cluster of root, minor second and tritone (e.g. C D♭ G♭) | chaotic | 54 |

- **Calibration:** in normal rhythm the 4-beat average never went above 5.5%. In AFib its median
  was 14%.
- **Recovery:** when an AFib stretch steadies for a moment, the progression comes back.
- **The pedal tone:** with a steady heart the melody sits on C4 while the chords move underneath.
  Because the pentatonic scale fits every chord of the progression, every in-scale note sounds
  consonant.

**Pulse (drums).** Every heartbeat triggers a soft "lub-dub" on two bass drums: the sound a
stethoscope hears.

- **"Lub"** (General MIDI drum 35) falls on the R-peak. Its velocity, 30–70, follows the beat's
  melody note.
- **"Dub"** (drum 36) follows after 35% of the beat's interval (at most 0.3 s), at 60% of the
  lub's velocity.
- In normal rhythm the pulse is even; in AFib it stumbles.

**Instrument.** The melody instrument is chosen by the emotion that Stage 4 reads from the melody:

| Emotion | Instrument (General MIDI program) |
|---|---|
| calm / relaxed | nylon-string guitar (24) |
| tense / anxious | distortion guitar (30) |
| happy / excited | marimba (12) |
| sad / depressed | cello (42) |

**Mix.** We rendered each part of record 04043 on its own. The strings sit about 7–9 dB below
the melody, and the pulse about 12–17 dB below it. The melody leads; the pulse is felt more than
heard.

### 8.4 Audio

Each piece is written as two MIDI files:

- `melody.mid`: the plain melody on a piano, the raw sonification.
- `arrangement.mid`: the full three-part piece.

[FluidSynth](https://www.fluidsynth.org/) renders both at 44.1 kHz with the FluidR3 General MIDI
soundfont. The audio is then normalised so that its loudest moment reaches 85% of full scale. A
raw render of such sparse parts peaks at only about 5%.

### 8.5 The score plot

`score.png` lines up three panels on one time axis:

1. The ECG, with its R-peaks.
2. Each beat's deviation, with dashed lines at ±12% where the melody leaves the scale.
3. The generated notes and chords.
   - Notes are blue when on the scale and red when chromatic.
   - Chords are green when consonant, orange when tense and purple when chaotic.

In a normal clip the melody is a flat line on C4 over green chords. In an AFib clip it scatters,
and the longest pauses make it plunge to C2.

---

## 9. Stage 4: Emotion, read from the music

### 9.1 The emotion space

We use **Russell's circumplex** (1980), the standard two-dimensional model in music-emotion
research:

| | low arousal | high arousal |
|---|---|---|
| **positive valence** | calm / relaxed | happy / excited |
| **negative valence** | sad / depressed | tense / anxious |

### 9.2 Our model

Our model reads the music, not the ECG. It uses three cues from the melody that music psychology
links to emotion (Gabrielsson & Lindström, 2010):

| Cue | Measured as | Normalised over | Pushes towards |
|---|---|---|---|
| rhythmic irregularity $\hat I$ | standard deviation ÷ mean of the gaps between note onsets | 0 – 0.30 | higher arousal |
| pitch spread $\hat S$ | standard deviation of the pitches, in semitones | 0 – 11 | higher arousal, lower valence |
| consonance $\hat C$ | share of the notes that stayed on the pentatonic scale | 0.30 – 1.0 | higher valence |

$$\text{arousal} = 2\left(0.55\,\hat I + 0.45\,\hat S - 0.5\right) \qquad \text{valence} = 2\left(0.70\,\hat C + 0.30\,(1 - \hat S) - 0.5\right)$$

- **Scale:** each cue is clipped to 0–1 after normalising, so valence and arousal run from −1
  to 1.
- **Emotion:** the signs of the two values pick the quadrant.
- **Calibration:** the ranges were calibrated on the 14 example clips.

**Why tempo and loudness are not used**, although they are the classic arousal cues:

- **Tempo** differs more between people than between rhythms. Record 201's AFib clip
  (101 beats per minute) is slower than record 04043's normal clip (108).
- **Loudness** is re-scaled within every clip, so it carries no information from one clip to the
  next.

**What this model really measures.** The notes sit exactly on the heartbeats, so the first cue is
the variability of the R-R intervals. The other two cues follow from the deviations. The model is
therefore a transparent *musical re-description* of heart-rate variability. That is a strength
(it is simple and explainable) and a reason to validate it ([§12](#12-discussion-from-the-musics-emotion-to-inner-emotion)).

### 9.3 Second opinion: Essentia

[Essentia](https://essentia.upf.edu/models.html), from the Music Technology Group at Universitat
Pompeu Fabra, provides pretrained models trained on real music by other researchers:

- **Four mood classifiers:** happy, sad, relaxed and aggressive. Each gives a probability from 0
  to 1. They run on Discogs-EffNet audio embeddings.
- **A valence/arousal regressor** trained on the DEAM dataset, on a 1–9 scale where 5 is neutral.
  It runs on MusiCNN embeddings.

Essentia listens to both renders of every piece: the plain melody and the full arrangement. The
models (about 25 MB) download automatically.

> **Correction.** Each mood classifier outputs two probabilities: the mood and its opposite. The
> two come in a different order for different moods: `happy, non_happy`, `non_sad, sad`,
> `non_relaxed, relaxed`, `aggressive, not_aggressive`.
>
> - **The error:** the first implementation always read the first column. So its "sad" and
>   "relaxed" scores were really the probabilities of *not* sad and *not* relaxed.
> - **The fix:** `config.MOOD_COLUMNS` now picks the right column for each mood.
> - **The numbers:** the saved results in [§11.2](#112-essentia) are corrected as 1 minus the
>   saved value. That is exact, because the two probabilities always sum to 1.

### 9.4 Third opinion: music2emo

[music2emo](https://github.com/AMAAI-Lab/Music2Emotion) (Kang & Herremans, 2025) is a newer model
built on the MERT-v1-95M music foundation model.

- **Outputs:** valence and arousal on a 1–9 scale, plus mood and theme tags from the MTG-Jamendo
  set.
- **Environment:** it needs older library versions than this project, so it runs in its own
  environment (see the README).
- **Input:** it listened to the plain melody of every piece.

### 9.5 How the three are compared

The three methods use different scales: −1 to 1, 1 to 9, and probabilities. So we compare
*directions*, not absolute values. For every recording we ask: does the AFib piece score higher
or lower than the same recording's normal piece, on valence and on arousal?

---

## 10. The experiment

- **Input:** 14 clips of 30 seconds: one normal and one AFib clip from each of the 7 recordings
  in [§7.4](#74-the-recordings-used).
- **Per clip:**
  - the melody and the arrangement, as MIDI and WAV;
  - a score plot;
  - our model's emotion;
  - Essentia on both renders;
  - music2emo on the melody.

> **Where the numbers come from.** The results below were produced by the project's first
> implementation, between 25 September and 1 October 2026.
>
> - **The rewrite:** the code was then rewritten from scratch with the same rules and parameters,
>   and on 8 October 2026 it reproduced every number in [§11.1](#111-heartbeats-music-and-our-model)
>   exactly. It was later consolidated into a single notebook.
> - **Two corrections** have been applied since:
>   - Essentia's "sad" and "relaxed" values ([§9.3](#93-second-opinion-essentia)).
>   - The finding that `mitdb` records 201 and 202 come from the same person, which changes
>   "7 people" to 6.
> - **Next:** running the pipeline again ([§17](#17-reproducing-the-results)) should reproduce
>   these tables.

---

## 11. Results

### 11.1 Heartbeats, music and our model

| Record | Rhythm | Heart rate (bpm) | RMSSD (ms) | Notes | Pitch range | Pitch SD (semitones) | Off-scale notes | Chords: consonant / tense / chaotic | Valence | Arousal | Emotion |
|---|---|---|---|---|---|---|---|---|---|---|---|
| afdb 04015 | normal | 80 | 7.6 | 40 | C4 | 0.0 | 0% | 10 / 0 / 0 | +1.00 | −0.97 | calm |
| afdb 04015 | AFib | 137 | 126.1 | 67 | C2–F♯5 | 9.8 | 57% | 5 / 9 / 3 | −0.67 | +0.76 | tense |
| afdb 04043 | normal | 108 | 8.5 | 53 | C4 | 0.0 | 0% | 14 / 0 / 0 | +1.00 | −0.96 | calm |
| afdb 04043 | AFib | 128 | 134.9 | 63 | C2–C♯5 | 8.5 | 52% | 6 / 10 / 0 | −0.51 | +0.45 | tense |
| afdb 04126 | normal | 79 | 18.6 | 39 | A3–D4 | 1.3 | 0% | 10 / 0 / 0 | +0.93 | −0.79 | calm |
| afdb 04126 | AFib | 160 | 141.9 | 79 | C♯2–G♯5 | 10.6 | 66% | 3 / 12 / 5 | −0.89 | +0.85 | tense |
| afdb 06995 | normal | 83 | 17.8 | 40 | A3–D4 | 1.2 | 0% | 10 / 0 / 0 | +0.93 | −0.81 | calm |
| afdb 06995 | AFib | 112 | 122.8 | 55 | D2–C5 | 8.0 | 51% | 6 / 7 / 1 | −0.45 | +0.31 | tense |
| afdb 08455 | normal | 79 | 8.3 | 38 | C4 | 0.0 | 0% | 10 / 0 / 0 | +1.00 | −0.96 | calm |
| afdb 08455 | AFib | 122 | 99.9 | 59 | G♯2–D5 | 5.9 | 31% | 11 / 4 / 0 | +0.07 | +0.02 | happy (borderline) |
| mitdb 201 | normal | 50 | 64.1 | 24 | A3–D4 | 1.9 | 0% | 6 / 0 / 0 | +0.89 | −0.69 | calm |
| mitdb 201 | AFib | 101 | 194.3 | 50 | C2–C♯5 | 9.8 | 52% | 3 / 9 / 1 | −0.58 | +0.76 | tense |
| mitdb 202 | normal | 56 | 37.4 | 27 | G3–D4 | 2.0 | 0% | 7 / 0 / 0 | +0.89 | −0.65 | calm |
| mitdb 202 | AFib | 125 | 146.9 | 61 | C2–D♯5 | 7.6 | 33% | 9 / 5 / 2 | −0.07 | +0.44 | tense |

- **Heartbeats.**
  - In every recording, the AFib clip is 3–17 times as variable as the normal clip.
  - The AFib clip also has the faster heart in every recording: 101–160 bpm, against 50–108 bpm.
  - The two `mitdb` normal clips vary more (37–64 ms) than the `afdb` ones (8–19 ms), but within
    each recording the gap is always large.
- **Melody.**
  - Every normal melody stays entirely on the scale, with a pitch standard deviation of at most 2
    semitones. Three of them never leave C4.
  - Every AFib melody leaves the scale for 31–66% of its notes, with a pitch standard deviation of
    6–11 semitones.
- **Harmony.**
  - All 67 chords under the normal pieces are consonant.
  - Under the AFib pieces, 68 of 111 chords (61%) turn tense (56) or chaotic (12).
- **Emotion.**
  - All 7 normal pieces read as **calm**, with valence +0.89 to +1.00 and arousal −0.65 to −0.97.
  - 6 of 7 AFib pieces read as **tense**. The seventh, `08455`, is a genuinely mild AFib stretch.
    It has the fewest off-scale notes (31%) and the smallest pitch spread of any AFib clip, and
    mostly consonant chords (11 / 4 / 0). It lands at the centre of the plane (+0.07, +0.02),
    just inside "happy", and so gets a marimba.
  - Compared with the same recording's normal piece, every AFib piece has lower valence and
    higher arousal: 7 of 7 on both axes.

### 11.2 Essentia

Plain melody (mood probabilities 0–1; valence and arousal on a 1–9 scale):

| Record | Rhythm | Happy | Sad | Relaxed | Aggressive | Valence | Arousal |
|---|---|---|---|---|---|---|---|
| afdb 04015 | normal | 0.055 | 0.705 | 0.920 | 0.053 | 3.64 | 3.75 |
| afdb 04015 | AFib | 0.139 | 0.504 | 0.815 | 0.135 | 4.18 | 4.20 |
| afdb 04043 | normal | 0.039 | 0.629 | 0.881 | 0.079 | 3.72 | 3.79 |
| afdb 04043 | AFib | 0.119 | 0.462 | 0.764 | 0.156 | 4.07 | 4.12 |
| afdb 04126 | normal | 0.062 | 0.674 | 0.913 | 0.055 | 3.56 | 3.69 |
| afdb 04126 | AFib | 0.127 | 0.522 | 0.819 | 0.139 | 4.51 | 4.36 |
| afdb 06995 | normal | 0.057 | 0.681 | 0.918 | 0.058 | 3.59 | 3.68 |
| afdb 06995 | AFib | 0.101 | 0.404 | 0.813 | 0.189 | 3.92 | 4.17 |
| afdb 08455 | normal | 0.052 | 0.710 | 0.922 | 0.046 | 3.56 | 3.74 |
| afdb 08455 | AFib | 0.104 | 0.531 | 0.798 | 0.144 | 3.91 | 3.94 |
| mitdb 201 | normal | 0.041 | 0.676 | 0.896 | 0.121 | 3.25 | 3.67 |
| mitdb 201 | AFib | 0.095 | 0.488 | 0.805 | 0.154 | 3.76 | 3.83 |
| mitdb 202 | normal | 0.042 | 0.619 | 0.894 | 0.115 | 3.37 | 3.66 |
| mitdb 202 | AFib | 0.124 | 0.374 | 0.684 | 0.256 | 4.14 | 4.21 |

Full arrangement:

| Record | Rhythm | Happy | Sad | Relaxed | Aggressive | Valence | Arousal |
|---|---|---|---|---|---|---|---|
| afdb 04015 | normal | 0.024 | 0.900 | 0.968 | 0.013 | 3.90 | 3.75 |
| afdb 04015 | AFib | 0.231 | 0.521 | 0.683 | 0.161 | 5.30 | 4.46 |
| afdb 04043 | normal | 0.027 | 0.905 | 0.966 | 0.020 | 4.06 | 3.79 |
| afdb 04043 | AFib | 0.198 | 0.556 | 0.712 | 0.171 | 4.71 | 4.60 |
| afdb 04126 | normal | 0.023 | 0.911 | 0.969 | 0.017 | 3.87 | 3.71 |
| afdb 04126 | AFib | 0.157 | 0.597 | 0.755 | 0.118 | 4.99 | 4.49 |
| afdb 06995 | normal | 0.018 | 0.925 | 0.973 | 0.013 | 3.99 | 3.69 |
| afdb 06995 | AFib | 0.208 | 0.484 | 0.697 | 0.151 | 5.42 | 4.57 |
| afdb 08455 | normal | 0.019 | 0.919 | 0.973 | 0.012 | 3.88 | 3.76 |
| afdb 08455 | AFib | 0.013 | 0.802 | 0.985 | 0.012 | 3.76 | 3.43 |
| mitdb 201 | normal | 0.019 | 0.908 | 0.977 | 0.011 | 3.67 | 3.68 |
| mitdb 201 | AFib | 0.131 | 0.590 | 0.776 | 0.155 | 4.65 | 4.35 |
| mitdb 202 | normal | 0.019 | 0.906 | 0.976 | 0.013 | 3.72 | 3.53 |
| mitdb 202 | AFib | 0.344 | 0.439 | 0.587 | 0.195 | 5.30 | 4.53 |

**Overall: Essentia hears every piece as calm.**

- "Relaxed" is the strongest mood of all 28 renders.
- For every plain melody, the DEAM valence and arousal stay below the neutral 5. These are
  low-key, slightly melancholic pieces.

**Plain melody: every AFib piece sounds livelier than the same recording's normal piece.** This
holds on all six measures in all 7 recordings (42 of 42 comparisons). The AFib melodies are:

| Measure | AFib | Normal |
|---|---|---|
| happy | 0.10–0.14 | 0.04–0.06 |
| aggressive | 0.14–0.26 | 0.05–0.12 |
| sad | 0.37–0.53 | 0.62–0.71 |
| relaxed | 0.68–0.82 | 0.88–0.92 |

They are also higher in valence and arousal.

**Full arrangement: the arrangement widens the gap.**

- **The normal arrangements are the calmest pieces of all:** relaxed 0.97–0.98 and sad
  0.90–0.93, with happy and aggressive at most 0.03.
- **Six of the seven AFib arrangements stay lively.** Compared with the normal ones they are 7–15
  times more aggressive (0.12–0.20 against 0.01–0.02) and 7–18 times happier (0.13–0.34 against
  0.02–0.03). Three of them pass the neutral valence of 5.
- **The exception is `08455` again.** Its mild AFib got a marimba and mostly consonant chords, and
  Essentia hears its arrangement as being as calm as a normal one.
- **Caveat:** the arrangement result is partly circular. The melody instrument, for example the
  distortion guitar for "tense", was chosen by our own model. It shows that the arrangement
  carries the intended character, not that our model was right.

### 11.3 music2emo

Plain melody (valence and arousal on a 1–9 scale):

| Record | Rhythm | Valence | Arousal | Mood and theme tags |
|---|---|---|---|---|
| afdb 04015 | normal | 4.88 | 3.94 | dark, film, game, sad, slow |
| afdb 04015 | AFib | 4.24 | 3.86 | commercial, film, fun, funny, game, movie, sad |
| afdb 04043 | normal | 5.19 | 4.78 | dark, fun, game, powerful, slow |
| afdb 04043 | AFib | 3.90 | 3.23 | commercial, film, fun, funny, game, love, sad |
| afdb 04126 | normal | 5.00 | 4.40 | dark, fun, game, love, sad, slow |
| afdb 04126 | AFib | 4.61 | 3.87 | adventure, commercial, documentary, film, fun, funny, game, love, sad |
| afdb 06995 | normal | 5.15 | 4.49 | dark, fun, game, sad, slow |
| afdb 06995 | AFib | 4.15 | 3.28 | fun, game, love, sad |
| afdb 08455 | normal | 5.48 | 4.82 | dark, fun, game, slow |
| afdb 08455 | AFib | 4.09 | 3.40 | film, fun, game, love, sad |
| mitdb 201 | normal | 4.07 | 3.32 | dark, film, fun, game, sad, slow |
| mitdb 201 | AFib | 4.51 | 3.73 | commercial, fun, funny, game, love, sad |
| mitdb 202 | normal | 4.62 | 3.83 | dark, fun, game, sad, slow |
| mitdb 202 | AFib | 4.39 | 3.81 | commercial, film, fun, funny, game, happy, love, sad |

- **Valence and arousal:** music2emo rates the AFib piece lower than the normal one, on both axes,
  in 6 of 7 recordings.
  - The exception is `201`, where it hears the AFib piece as both more pleasant and more
    energetic.
  - The arousal differences for `04015` and `202` are tiny (−0.08 and −0.02).
- **Its tags point the other way from its own numbers.**
  - Every normal piece is tagged "dark" and "slow", and no AFib piece is.
  - The AFib pieces collect "love" (6 of 7), "funny" (5 of 7) and "commercial" (5 of 7).
  - This is one more sign of how unstable emotion readings of such unusual music are.

### 11.4 Do the three methods agree?

AFib minus normal, per recording; positive means the AFib piece scores higher. Essentia is the
plain-melody DEAM reading.

| Record | Our model: valence | Our model: arousal | Essentia: valence | Essentia: arousal | music2emo: valence | music2emo: arousal |
|---|---|---|---|---|---|---|
| afdb 04015 | −1.67 | +1.73 | +0.55 | +0.46 | −0.63 | −0.08 |
| afdb 04043 | −1.51 | +1.41 | +0.35 | +0.34 | −1.29 | −1.55 |
| afdb 04126 | −1.82 | +1.64 | +0.95 | +0.67 | −0.38 | −0.52 |
| afdb 06995 | −1.38 | +1.12 | +0.33 | +0.49 | −1.00 | −1.21 |
| afdb 08455 | −0.93 | +0.98 | +0.35 | +0.20 | −1.39 | −1.42 |
| mitdb 201 | −1.47 | +1.45 | +0.51 | +0.16 | +0.45 | +0.41 |
| mitdb 202 | −0.96 | +1.09 | +0.76 | +0.55 | −0.24 | −0.02 |

| Method | Valence: AFib vs normal | Arousal: AFib vs normal |
|---|---|---|
| Our model | lower in 7 of 7 | higher in 7 of 7 |
| Essentia | **higher** in 7 of 7 | higher in 7 of 7 |
| music2emo | lower in 6 of 7 | **lower** in 6 of 7 |

- **All three methods hear a difference between the steady and the irregular heart, in every
  recording.**
- **They disagree on which emotion it is.**
  - Our model and music2emo agree on valence: the AFib music is less pleasant.
  - Our model and Essentia agree on arousal: the AFib music is more energetic.
  - Essentia and music2emo agree on neither.

### 11.5 The excluded record 219

Every method flags record 219 on its own:

- **Our model** reads its normal clip as *tense* and its AFib clip as *calm*.
- **The harmony** of its normal clip has tense and chaotic chords (3 / 2 / 2), while its AFib
  clip stays mostly consonant (9 / 1 / 0).
- **Essentia** hears its AFib piece as *less* energetic than its normal one, the opposite of every
  other recording.
- **music2emo** reverses its usual direction on both axes.

The pipeline is consistent: it reflects the actual rhythm, not the label. Here the rhythm behind
the "normal" label is not normal.

---

## 12. Discussion: from the music's emotion to inner emotion

**What has been shown.**

- The pipeline turns heartbeats into music that reliably differs between a steady and an
  irregular heart, in every recording tested (RQ1).
- Our model's emotion moves consistently with the rhythm (RQ2).
- Two independent models, trained on real music, also hear the difference in every recording
  (RQ3, first half).

**Why the models disagree.**

- **Each model learned from different music and different listeners.** DEAM, PMEmo, EMOMusic and
  MTG-Jamendo each have their own annotators and instructions. Weak agreement between
  music-emotion models is a known open problem.
- **None of them has heard music like ours.** These pieces are sparse, slow and synthetic. Every
  piece reads as mostly "relaxed" to Essentia, and music2emo's tags contradict its own numbers.
- **The pretrained models hear tempo; ours deliberately does not.** Every AFib clip is also the
  faster heart (101–160 bpm against 50–108). Faster music is classically heard as more energetic,
  and often as happier. That likely explains much of why Essentia hears the AFib pieces as
  livelier and more positive. Our model ignores tempo on purpose, and so hears "irregular, hence
  tense".

**The gap between the heart's rhythm and the person's feelings.** Our model is in effect a
musical re-description of heart-rate variability ([§9.2](#92-our-model)). Turning irregularity
into tension fits an arrhythmia. It is not yet known to fit emotions:

- **AFib is an electrical condition, not an emotion.** A calm person can have AFib, and in that
  case the music would sound tense.
- **In healthy hearts, calm can look irregular.** Slow, relaxed breathing makes the heart speed up
  on each in-breath and slow down on each out-breath. This is respiratory sinus arrhythmia, and it
  *raises* variability, while acute stress *lowers* it. Our mapping would read that healthy, calm
  variability as tension.
- **Medication shapes the rhythm too.** The man behind records 201 and 202 was taking propranolol
  (a beta-blocker) and digoxin, both of which slow the heart. His normal clips run at 50–56 bpm.

**Conclusion.** Today the system detects how calm or agitated the *heart's rhythm sounds*, and
names it with the vocabulary of music emotion. Whether that matches the person's *inner* emotion
is the central hypothesis of the project. It has not been tested yet, and [§13](#13-validation-plan)
describes how to test it.

---

## 13. Validation plan

Validation needs ECG recordings from people whose emotions were induced or self-reported at the
time:

| Dataset | People | ECG | Emotion information |
|---|---|---|---|
| [WESAD](https://archive.ics.uci.edu/dataset/465/wesad+wearable+stress+and+affect+detection) | 15 | chest ECG, 700 Hz | neutral, stress and amusement conditions, with self-report questionnaires |
| [DREAMER](https://zenodo.org/records/546113) | 23 | 2-channel ECG, 256 Hz | self-rated valence, arousal and dominance for 18 film clips |
| [AMIGOS](https://www.eecs.qmul.ac.uk/mmv/datasets/amigos/index.html) | 40 | ECG, with EEG and GSR | self-rated valence, arousal, dominance, liking and familiarity |

Access terms differ between these datasets; some require a signed request or an end-user licence
agreement.

**Protocol.**

1. **Windows.** Cut each participant's ECG into windows that match the labelled conditions or
   clips, for example 30–60 seconds each.
2. **Run Stage 1–4.** Run `analyze_signal()` on every window. It needs no annotations.
3. **Compare with what people reported.**
   - Correlate the detected valence and arousal with the self-ratings (Spearman's ρ, per person
     and pooled).
   - Check whether the conditions separate, for example WESAD's stress against baseline against
     amusement.
   - Compare quadrant agreement against chance.
4. **Baseline.** Run the same comparison with plain HRV features (RMSSD and mean heart rate). This
   tests whether going through music adds information, or only repackages HRV.
5. **Recalibrate fairly.** Fit the cue ranges and weights on some participants, and test on the
   others (leave-one-subject-out).
6. **Fix what fails.** For example, read slow, breathing-locked variability as calm rather than
   tense ([§12](#12-discussion-from-the-musics-emotion-to-inner-emotion)).
7. **Report the result whatever it is.** A negative result would be an honest finding.

A second, cheaper study tests the music → emotion step on its own. Listeners, for example
classmates, rate the valence and arousal of the 14 pieces. This shows whether people hear the
emotions our model assigns, independently of the heart.

---

## 14. Where the data comes from, and ethics

### 14.1 Who is in the example data

All the example recordings come from adult heart patients at Beth Israel Hospital in Boston,
recorded between 1975 and 1983.

- **`afdb`:** everyone has atrial fibrillation. No age, sex or other details are published.
- **`mitdb`:** a mixed group of in- and outpatients. Records 201 and 202 are two excerpts from
  the same tape of the same 68-year-old man. His header lists digoxin, a diuretic, propranolol and
  potassium chloride.

Neither database contains anything about emotion, mood, psychology or neurodevelopment. The
people were chosen purely on cardiac grounds. **These recordings can show that the music follows
the heart's rhythm. They cannot show that it follows anyone's feelings.**

### 14.2 Licence and attribution

Both databases are published under the Open Data Commons Attribution License 1.0. They are free
to use with attribution. Cite PhysioNet (Goldberger et al., 2000) and the database papers (Moody &
Mark, 1983 and 2001).

### 14.3 Your own ECG recordings

An ECG is personal health data.

- **Consent:** analyse someone's recording only with their consent.
- **Storage:** analyses of your own recordings belong in `output/analysis/`, which is kept out of git
  on purpose. Never commit or share real recordings or their results without permission.

### 14.4 Using this with autistic people, or any specific group

One motivation for inner emotion detection is to offer a non-verbal window into emotion. That
could help, for example, autistic people who find it hard to identify or describe their feelings.
There is genuine research in this direction:

- Resting HRV has been found to be lower in autistic adults than in non-autistic adults.
- HRV is being studied as an objective marker of emotion regulation in autism.
- Wearable heart-rate devices have been built for autistic children.
- Autistic traits change how cardiac activity, sensing one's own body (interoception) and
  emotion processing relate.

The links are in [README §11.7](README.md#117-related-research-heart-rate-variability-and-emotion).

That research works from HRV measures, with validation in the population concerned. Before this
project is used with any specific group:

- **Validate it first** ([§13](#13-validation-plan)), and then in the group itself. The emotion
  model was calibrated on 14 clips from cardiac patients.
- **Compare it with the direct route.** If plain HRV measures read emotion as well as the music
  does, use them for any assistive purpose, and keep the music as the listenable side.
- **Get ethical review, consent and, for children, assent** before collecting anyone's data.
- **Design it together with the people it is meant for**, and let them own the interpretation of
  their own signals.
- **Never present the detected emotion as a verdict** on how someone feels.

---

## 15. Limitations

- **Not a medical tool.** Nothing here has been validated for diagnosis.
- **Emotion not yet validated** against people's own reports ([§12](#12-discussion-from-the-musics-emotion-to-inner-emotion), [§13](#13-validation-plan)).
- **Small, specific data:** 14 clips from 6 adult heart patients in one hospital, recorded
  1975–1983.
- **Calibrated on the same clips it was tested on.** The emotion model's ranges and the harmony
  thresholds came from these 14 clips; there is no held-out test set yet.
- **Unaudited heartbeat marks.** `afdb`'s heartbeat annotations were never corrected by hand.
  Clip selection works around most glitches, but not all. Record 04126's AFib clip, for example,
  shows visible baseline wander.
- **Short clips.** 30 seconds is enough to hear a rhythm, but short by HRV-research standards,
  which often use 5 minutes.
- **Western musical conventions.** Pentatonic as calm, diminished chords as tense and minor
  seconds as chaotic are conventions of Western tonal music. Listeners from other traditions may
  hear them differently.
- **Pretrained models out of their domain.** They were trained on produced commercial music, not
  sonified heartbeats, and they disagree.
- **Partly circular arrangement results.** The melody instrument is chosen by our own model's
  emotion.
- **Results not yet reproduced with the rewritten code** ([§10](#10-the-experiment)).

---

## 16. Future work

1. **Run the rewritten pipeline** on a machine with enough compute, and confirm the tables in
   [§11](#11-results) ([§17](#17-reproducing-the-results)).
2. **Validate against self-reported emotion** with WESAD, DREAMER and AMIGOS
   ([§13](#13-validation-plan)).
3. **A listening study** with human raters, to test the music → emotion step on its own.
4. **A mapping for healthy hearts** that tells calm, breathing-locked variability apart from
   erratic variability. It could also use the heart rate itself as an arousal cue.
5. **Live mode:** stream from a wearable chest strap and play the music in real time.
6. **Musical refinement by ear:** the 12% scale threshold, the 85% note length, the 12% and 25%
   chord thresholds, and the instrument choices.
7. *(From the proposal, optional)* let an LLM suggest alternative mappings to try.

---

## 17. Reproducing the results

On a machine with enough compute:

```bash
sudo apt install fluidsynth fluid-soundfont-gm
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
jupyter notebook sonifying_the_heart.ipynb
```

Then set `RENDER_AUDIO` and `BUILD_ALL` to `True` at the top and run every cell. That writes the
14 pieces — MIDI, WAV and score plots — plus the result table to `output/`.

For music2emo, set up its separate environment as described in
[README §9.7](README.md#97-optional-reproducing-the-music2emo-results) and run it over
`output/examples/*/melody.wav` from there.

**What to compare.**

| File | Should match |
|---|---|
| `output/examples_summary.csv` | [§11.1](#111-heartbeats-music-and-our-model) |
| `output/essentia_results.csv` | [§11.2](#112-essentia); "sad" and "relaxed" now come out directly, with no correction |
| `output/music2emo_results.csv` | [§11.3](#113-music2emo) |

Small differences are possible if the FluidSynth or soundfont version changes the audio.

---

## 18. References

**ECG data**

- Goldberger AL, et al. PhysioBank, PhysioToolkit, and PhysioNet. *Circulation* 2000;101(23):e215–e220.
  [doi:10.1161/01.CIR.101.23.e215](https://doi.org/10.1161/01.CIR.101.23.e215)
- Moody GB, Mark RG. A new method for detecting atrial fibrillation using R-R intervals.
  *Computers in Cardiology* 1983;10:227–230. [MIT-BIH Atrial Fibrillation Database](https://physionet.org/content/afdb/1.0.0/)
- Moody GB, Mark RG. The impact of the MIT-BIH Arrhythmia Database. *IEEE Engineering in Medicine
  and Biology* 2001;20(3):45–50. [doi:10.1109/51.932724](https://doi.org/10.1109/51.932724) ·
  [MIT-BIH Arrhythmia Database](https://physionet.org/content/mitdb/1.0.0/)

**Music and emotion**

- Russell JA. A circumplex model of affect. *Journal of Personality and Social Psychology*
  1980;39(6):1161–1178.
- Gabrielsson A, Lindström E. The role of structure in the musical expression of emotions. In:
  Juslin PN, Sloboda JA (eds), *Handbook of Music and Emotion*. Oxford University Press, 2010.
- Aljanaki A, Yang Y-H, Soleymani M. Developing a benchmark for emotional analysis of music.
  *PLOS ONE* 2017 (the DEAM dataset).

**Pretrained models**

- Bogdanov D, et al. Essentia: an audio analysis library for music information retrieval. *ISMIR*
  2013. [Pretrained models](https://essentia.upf.edu/models.html)
- Alonso-Jiménez P, Serra X, Bogdanov D. Music representation learning based on editorial metadata
  from Discogs. *ISMIR* 2022.
- Kang J, Herremans D. Towards unified music emotion recognition across dimensional and
  categorical models. 2025. [arXiv:2502.03979](https://arxiv.org/abs/2502.03979) ·
  [code](https://github.com/AMAAI-Lab/Music2Emotion)

**ECG datasets with emotion labels**

- Schmidt P, et al. Introducing WESAD, a multimodal dataset for wearable stress and affect
  detection. *ICMI* 2018.
- Katsigiannis S, Ramzan N. DREAMER: a database for emotion recognition through EEG and ECG
  signals from wireless low-cost off-the-shelf devices. *IEEE Journal of Biomedical and Health
  Informatics* 2018.
- Miranda-Correa JA, et al. AMIGOS: a dataset for affect, personality and mood research on
  individuals and groups. *IEEE Transactions on Affective Computing* 2021.

Software, tools and the research on HRV and autism are linked in
[README §11](README.md#11-available-resources).
