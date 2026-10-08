# Sonifying the Heart: Inner Emotion Detection from ECG through Music

> **ECG data → Heartbeats → Music → Emotion**

A heartbeat already has a rhythm, and that rhythm is shaped by the same nervous system that
shapes how we feel. This project turns a person's electrocardiogram (ECG) into music, then reads
the emotion expressed by that music as a window into their inner emotional state.

A steady heart becomes a calm piece: one melody note held over a gentle chord progression, with
an even "lub-dub" pulse. An irregular heart becomes a restless one: the melody escapes the scale,
the chords sour into tension, and the pulse stumbles. The emotion in each piece is then detected
by our own music-emotion model and cross-checked by two independent, pretrained music-emotion
models.

- **Team:** Chervith Reddy (2024101076) · Manidhar Sukasi (2023101067) · Sathwik Reddy (2024121002)
- **Course:** Music Workshop
- **Start here:** [sonifying_the_heart.ipynb](sonifying_the_heart.ipynb) is the whole project in
  one self-contained notebook — every stage, with explanations, run top to bottom.
- **In depth:** [project_description.md](project_description.md) is the full description (design,
  results, validation plan, ethics). [Progress.md](Progress.md) is the dated log of the work.

---

## Contents

1. [The idea](#1-the-idea)
2. [The pipeline at a glance](#2-the-pipeline-at-a-glance)
3. [Stage 1: ECG data](#3-stage-1-ecg-data)
4. [Stage 2: Heartbeats](#4-stage-2-heartbeats)
5. [Stage 3: Music](#5-stage-3-music)
6. [Stage 4: Emotion, read from the music](#6-stage-4-emotion-read-from-the-music)
7. [Results](#7-results)
8. [Validation status: how far does it detect inner emotion?](#8-validation-status-how-far-does-it-detect-inner-emotion)
9. [Getting started](#9-getting-started)
10. [Project structure](#10-project-structure)
11. [Available resources](#11-available-resources)
12. [Limitations and ethics](#12-limitations-and-ethics)
13. [How the project was built](#13-how-the-project-was-built)

---

## 1. The idea

**Why the heart carries emotion.** The heart rate is steered beat by beat by the autonomic
nervous system. Its two branches pull in opposite directions: the "fight or flight" side speeds
the heart up, and the "rest and digest" side slows it down. The same system moves with emotional
arousal. This is why heart-rate variability (HRV), the beat-to-beat change in heart timing, is an
established research marker of stress and emotion regulation (see [§11.7](#117-related-research-heart-rate-variability-and-emotion)).

**Why go through music.** Music is one of the most studied carriers of emotion. Psychology
describes it on two axes, **valence** (unpleasant to pleasant) and **arousal** (calm to
energetic) (Russell, 1980). It also knows which musical features push music along each axis
(Gabrielsson & Lindström, 2010). Turning the heartbeat into music therefore does two things:

- **It makes the inner state audible.** Anyone can hear it, with no ECG training.
- **It makes the inner state measurable.** The emotion can be read with music-emotion models.

**Uses we have in mind:**

- **Inner-emotion awareness.** It gives a listenable, non-verbal window into a person's state,
  for example for people who find it hard to put feelings into words.
- **Teaching.** Students can learn to recognise heart-rhythm disorders by ear, not only by eye
  (from our proposal).
- **Accessibility.** Visually impaired clinicians and technicians get a way to read an ECG.
- **Eyes-free monitoring.** It works like a pulse-oximeter beep, but carries far more
  information.

This is a proof of concept for listening and research, not a medical device. How far the emotion
detection has been validated is described honestly in [§8](#8-validation-status-how-far-does-it-detect-inner-emotion).

---

## 2. The pipeline at a glance

```
 ┌───────────┐    ┌──────────────┐    ┌───────────────────────────┐    ┌───────────────────────┐
 │  ECG data │ ─► │  Heartbeats  │ ─► │           Music           │ ─► │        Emotion        │
 │           │    │              │    │                           │    │                       │
 │ PhysioNet │    │ R-peaks,     │    │ melody: 1 note per beat   │    │ valence & arousal of  │
 │ records,  │    │ R-R          │    │ harmony: C-Am-F-G, tension│    │ the music, on         │
 │ or your   │    │ intervals,   │    │   tiers                   │    │ Russell's circumplex  │
 │ own file  │    │ RMSSD        │    │ pulse: lub-dub per beat   │    │ + 2 pretrained models │
 └───────────┘    └──────────────┘    └───────────────────────────┘    └───────────────────────┘
   data.py           data.py           melody.py, arrangement.py,         emotion.py,
                                       audio.py, plots.py                 essentia_models.py
```

| Stage | Input → output | Notebook section |
|---|---|---|
| 1. ECG data | A recording: a PhysioNet record, or any WFDB record / CSV file of samples | §3 |
| 2. Heartbeats | ECG → heartbeat times (R-peaks), R-R intervals, beat-to-beat variability (RMSSD) | §3 |
| 3. Music | Heartbeats → melody, string harmony and drum pulse → MIDI, audio and a score | §4, §6, §7 |
| 4. Emotion | Music → valence, arousal and an emotion (calm, tense, happy or sad) | §5 |

All of it lives in [sonifying_the_heart.ipynb](sonifying_the_heart.ipynb). §8 joins the stages
together, and every parameter sits in one cell in §2.

---

## 3. Stage 1: ECG data

The examples use two open databases from [PhysioNet](https://physionet.org/), the archive of
physiological recordings maintained by MIT. Both are named in our proposal.

| | MIT-BIH Atrial Fibrillation Database (`afdb`) | MIT-BIH Arrhythmia Database (`mitdb`) |
|---|---|---|
| Recordings | 25 recordings of about 10 hours (23 contain the ECG signal) | 48 half-hour recordings from 47 people |
| People | adults with atrial fibrillation (AFib), mostly intermittent | 25 men aged 32–89, 22 women aged 23–89; about 60% hospital inpatients |
| Recorded | Beth Israel Hospital, Boston, 1983 | Beth Israel Hospital, Boston, 1975–1979 |
| Sampling | 250 Hz, 2 ECG leads | 360 Hz, 2 ECG leads |
| Heartbeat marks | automatic detector, never checked by hand | checked by two or more cardiologists |
| Rhythm labels | expert-labelled: normal (`N`), `AFIB`, flutter, junctional | expert-labelled: `N`, `AFIB` and many others |

Atrial fibrillation is the most common sustained heart-rhythm disorder: the upper chambers quiver
and the heartbeats arrive at irregular moments. Most `afdb` records contain stretches of both
normal rhythm and AFib (21 of the 23 with signal have at least 30 seconds of each). That makes the
database ideal for comparing a steady and an irregular heart in the same person.

**Nothing has to be downloaded.** A record missing from `data/` is streamed from PhysioNet, and
only the parts that are needed: the annotations plus 30 seconds of signal, a few hundred
kilobytes per record. Downloading the full databases (~720 MB) is optional.

Your own ECG recordings work too (see [§9.5](#95-your-own-ecg-file)). Who the PhysioNet recordings
come from, and what that means for using this with other people, is covered in
[project_description.md §14](project_description.md#14-where-the-data-comes-from-and-ethics).

---

## 4. Stage 2: Heartbeats

Every heartbeat shows up in the ECG as a sharp spike, the **R-peak**. The time between two
consecutive R-peaks is the **R-R interval**, about 0.6–1.0 s at rest. The sequence of R-R
intervals is the rhythm that becomes the music.

How steady the rhythm is gets measured with **RMSSD**, the standard beat-to-beat variability
measure:

$$\mathrm{RMSSD} = \sqrt{\frac{1}{N-1}\sum_{i=1}^{N-1}\left(RR_{i+1} - RR_i\right)^2}$$

**Finding the heartbeats.**

- **PhysioNet records:** we read the database's own beat annotations.
- **Any other recording:** the **XQRS** detector from `wfdb` finds the beats.

We checked the detector on record 04043 with its annotations hidden. For the first 30 seconds it
found 53 beats with a mean R-R of 559 ms and an RMSSD of 14.2 ms. The database's own marks give
54 beats, 559 ms and 13.8 ms for nearly the same stretch.

**Choosing 30-second clips.** For each example record we take one 30-second normal clip and one
AFib clip from the expert-labelled stretches. Up to 5 candidate windows are scored in each
stretch:

- **Normal:** the *steadiest* window wins.
- **AFib:** the window with the *most detected beats* wins.

The reason is a data-quality problem we found. `afdb`'s automatic beat marks jitter in places,
and our first version (which simply took the first 30 seconds) made two "normal" clips look
*more* irregular than AFib. Real normal rhythm is steady, so the steadiest window avoids those
glitches.

**Records used.** We used `afdb` 04015, 04043, 04126, 06995 and 08455, plus `mitdb` 201 and 202:
7 recordings and 14 clips. They come from 6 people, because `mitdb` 201 and 202 were taken from the
same tape of one 68-year-old man. `mitdb` record 219 also has both rhythms, but it was excluded. Its
"normal" stretches are full of blocked heartbeats (133 non-conducted P-waves in 30 minutes), so
even its steadiest normal window (RMSSD 270.6 ms) is more irregular than its AFib (145.9 ms).
Every later stage flags it independently.

---

## 5. Stage 3: Music

### 5.1 Melody: one note per heartbeat

| From the heartbeat | Becomes |
|---|---|
| The moment of the beat | The moment the note starts. The tempo is never quantised. |
| The R-R interval | The note's length: 85% of the interval |
| How the interval differs from the recent average | The note's pitch |
| The ECG amplitude at the beat | The note's loudness (MIDI velocity 40–110) |

**Pitch.** Each beat's interval is compared with the average of the last five intervals:

$$d_i = \frac{RR_i - \overline{RR}_i}{\overline{RR}_i}$$

- **On time** ($d_i = 0$): the root note **C4**.
- **Faster than usual** ($d_i < 0$): the melody moves **up**.
- **Slower than usual** ($d_i > 0$): the melody moves **down**.
- **Small deviations** (under 12%): the melody walks along the **C-major pentatonic scale**
  (C D E G A), which sounds consonant over almost any chord.
- **Larger deviations:** the melody leaves the scale and moves chromatically.
- **50% or more:** the melody reaches two octaves away from C4.

### 5.2 Arrangement: harmony and pulse

**Harmony (strings).** Every 4 heartbeats get one chord from the progression **C – Am – F – G**
(I – vi – IV – V), voiced below the melody. How irregular those 4 beats were decides the chord's
colour:

| Average deviation of the 4 beats | Chord | Sound |
|---|---|---|
| below 12% | the progression's chord | consonant |
| 12% to 25% | a diminished triad on the same root | tense, the classic suspense chord |
| 25% and above | a cluster of root, minor second and tritone | chaotic |

These thresholds were calibrated on real clips. In normal rhythm the 4-beat average never
exceeded 5.5%. In AFib, 61% of chords turn tense or worse.

With a steady heart the melody sits on C4 while the chords move underneath. This is a **pedal
tone**, a classic compositional device.

**Pulse (drums).** Every heartbeat triggers a soft **"lub-dub"** on two bass drums, the sound a
stethoscope hears. The "dub" follows after 35% of the beat's interval (0.3 s at most). In normal
rhythm the pulse is even; in AFib it stumbles.

**Instrument.** The melody instrument of the final piece comes from the emotion detected in
Stage 4:

| Emotion | Instrument |
|---|---|
| calm | nylon-string guitar |
| tense | distortion guitar |
| happy | marimba |
| sad | cello |

This way the piece sounds like the emotion it carries.

### 5.3 Audio and the score

Each piece is written as two MIDI files:

- `melody.mid` holds the melody alone on a piano: the raw sonification.
- `arrangement.mid` holds the full three-part piece.

Both are rendered to audio by [FluidSynth](https://www.fluidsynth.org/) with the FluidR3 General
MIDI soundfont. The audio is then normalised so the loudest moment reaches 85% of full scale.

A **score plot** lines up the ECG, each beat's deviation and the generated notes and chords on
one time axis. In a normal clip the melody is a flat line on C4 over green (consonant) chords. In
an AFib clip it scatters, and the long pauses make it plunge as low as C2.

---

## 6. Stage 4: Emotion, read from the music

### 6.1 Our music-emotion model

The emotion is read from the music itself, using three musical cues known to carry emotion
(Gabrielsson & Lindström, 2010):

| Cue | Measured as | Pushes towards |
|---|---|---|
| rhythmic irregularity $\hat I$ | spread of the gaps between notes | higher arousal |
| pitch spread $\hat S$ | standard deviation of the pitches | higher arousal, lower valence |
| consonance $\hat C$ | share of notes that stayed on the pentatonic scale | higher valence |

$$\text{arousal} = 2\left(0.55\,\hat I + 0.45\,\hat S - 0.5\right) \qquad \text{valence} = 2\left(0.70\,\hat C + 0.30\,(1 - \hat S) - 0.5\right)$$

Both values run from −1 to 1. Each cue is first normalised to 0–1 over a range calibrated on the
14 example clips. The quadrant of Russell's circumplex gives the emotion:

| | low arousal | high arousal |
|---|---|---|
| **positive valence** | calm / relaxed | happy / excited |
| **negative valence** | sad / depressed | tense / anxious |

**Why tempo and loudness are not used.**

- **Tempo:** it differs more between people than between emotional states. One person's
  irregular clip was slower than another person's steady one.
- **Loudness:** it is re-scaled within every clip, so it carries no information across clips.

### 6.2 Second and third opinions

Two independent models, trained on real music by other researchers, also listen to each piece:

- **[Essentia](https://essentia.upf.edu/models.html)** (Universitat Pompeu Fabra) gives four
  mood classifiers (happy, sad, relaxed, aggressive) and a valence/arousal model trained on the
  DEAM dataset. It listens to both the plain melody and the full arrangement.
- **[music2emo](https://github.com/AMAAI-Lab/Music2Emotion)** (Kang & Herremans, 2025) is a
  stronger MERT-based model with valence/arousal and mood tags. It listens to the plain melody.

### 6.3 Example: the four stages for one person (record 04043)

| | ECG data | Heartbeats | Music | Emotion |
|---|---|---|---|---|
| **Normal rhythm** | 30 s, `afdb` 04043 | 54 beats, RMSSD 8.5 ms | melody held on C4, 14 consonant chords, nylon guitar | **calm** (valence +1.00, arousal −0.96) |
| **Atrial fibrillation** | 30 s, same person | 64 beats, RMSSD 134.9 ms | melody from C2 to C♯5, 52% chromatic notes, 10 tense chords, distortion guitar | **tense** (valence −0.51, arousal +0.45) |

---

## 7. Results

All 14 clips, from 7 recordings of 6 people:

| Recording | Rhythm | Heartbeats: RMSSD (ms) | Music: notes outside the scale | Music: chords (consonant / tense / chaotic) | Emotion (valence, arousal) |
|---|---|---|---|---|---|
| afdb 04015 | normal | 7.6 | 0% | 10 / 0 / 0 | calm (+1.00, −0.97) |
| afdb 04015 | AFib | 126.1 | 57% | 5 / 9 / 3 | tense (−0.67, +0.76) |
| afdb 04043 | normal | 8.5 | 0% | 14 / 0 / 0 | calm (+1.00, −0.96) |
| afdb 04043 | AFib | 134.9 | 52% | 6 / 10 / 0 | tense (−0.51, +0.45) |
| afdb 04126 | normal | 18.6 | 0% | 10 / 0 / 0 | calm (+0.93, −0.79) |
| afdb 04126 | AFib | 141.9 | 66% | 3 / 12 / 5 | tense (−0.89, +0.85) |
| afdb 06995 | normal | 17.8 | 0% | 10 / 0 / 0 | calm (+0.93, −0.81) |
| afdb 06995 | AFib | 122.8 | 51% | 6 / 7 / 1 | tense (−0.45, +0.31) |
| afdb 08455 | normal | 8.3 | 0% | 10 / 0 / 0 | calm (+1.00, −0.96) |
| afdb 08455 | AFib | 99.9 | 31% | 11 / 4 / 0 | happy, borderline (+0.07, +0.02) |
| mitdb 201 | normal | 64.1 | 0% | 6 / 0 / 0 | calm (+0.89, −0.69) |
| mitdb 201 | AFib | 194.3 | 52% | 3 / 9 / 1 | tense (−0.58, +0.76) |
| mitdb 202 | normal | 37.4 | 0% | 7 / 0 / 0 | calm (+0.89, −0.65) |
| mitdb 202 | AFib | 146.9 | 33% | 9 / 5 / 2 | tense (−0.07, +0.44) |

**What happened at each stage:**

- **Heartbeats.** In every recording, the AFib clip is 3–17 times as variable as the normal clip.
- **Music.**
  - Every normal clip stayed entirely in the pentatonic scale, with all 67 of its chords
    consonant.
  - Every AFib clip left the scale for 31–66% of its notes, and 68 of its 111 chords turned
    tense or chaotic.
- **Emotion.**
  - All 7 normal clips were detected as **calm**, and 6 of 7 AFib clips as **tense**.
  - The seventh, `08455`, is a genuinely mild AFib stretch. It has the fewest notes outside the
    scale and lands at the centre of the emotion plane.

**Do independent emotion models hear the same?** Each method was asked: does the AFib piece
score lower or higher than the same recording's normal piece?

| Method | Valence (pleasantness): AFib vs normal | Arousal (energy): AFib vs normal |
|---|---|---|
| Our model | lower for 7 of 7 recordings | higher for 7 of 7 |
| Essentia | **higher** for 7 of 7 | higher for 7 of 7 |
| music2emo | lower for 6 of 7 | **lower** for 6 of 7 |

All three methods hear a clear difference between a steady and an irregular heart, in every
recording. They disagree on *which* emotion describes it:

- Our model and music2emo agree on valence.
- Our model and Essentia agree on arousal.

Disagreement between music-emotion models is a known open problem in the field.

**Essentia's mood classifiers fill in the picture.**

- **Every piece sounds mostly calm to Essentia:** "relaxed" is the strongest mood of all 28
  renders.
- **The AFib melodies sound livelier** than the normal ones in all 7 recordings: happier, more
  aggressive, less sad and less relaxed.
- **The full arrangement widens the gap.**
  - The normal arrangements become the calmest pieces of all (relaxed 0.97–0.98, sad
    0.90–0.93).
  - Six of the seven AFib arrangements sound 7–15 times more "aggressive" than the normal ones.

**Where these numbers come from.**

- **Reproduced.** They were produced by the project's first implementation, and reproduced
  exactly on 2026-10-08 by the current code — every valence, arousal and chord count.
- **Essentia correction:** the "sad" and "relaxed" readings were corrected on 2026-10-01. The first
  version read the wrong output column of those two classifiers; the details are in
  [Progress.md](Progress.md).
- **More detail:** every per-clip number from all three models is in
  [project_description.md §11](project_description.md#11-results), and
  [sonifying_the_heart.ipynb](sonifying_the_heart.ipynb) recomputes them.

---

## 8. Validation status: how far does it detect inner emotion?

**What has been shown:**

- The pipeline turns heartbeats into music that reliably differs between a steady and an
  irregular heart, in every recording tested.
- Three independent methods hear that difference.
- The emotion read from the music moves consistently with the heart's rhythm.

**What has not been shown yet:**

- **The music's emotion has not been checked against how people actually felt.** The MIT-BIH
  recordings come from heart patients in the 1970s–80s and contain no emotion reports. Our
  results show the detected emotion separating *heart rhythms*, not yet matching *feelings*.
- **Atrial fibrillation is an electrical heart condition, not an emotion.** A calm person can
  have AFib, and in such a case the music would sound tense.
- **In healthy hearts, calm can look irregular.** Slow, relaxed breathing makes the heart speed
  up on each in-breath and slow down on each out-breath, which *raises* beat-to-beat variability.
  Acute stress *lowers* it. Our mapping turns irregularity into tension, which fits arrhythmia but
  could mis-read this healthy, calm variability as tense.
- **The three emotion models disagree** on the exact emotion (see [§7](#7-results)).

**The next step** is to run the pipeline on ECG datasets that come with people's own emotion
ratings, compare the detected emotion with what participants reported, and recalibrate the
mapping:

| Dataset | People | ECG | Emotion labels |
|---|---|---|---|
| [WESAD](https://archive.ics.uci.edu/dataset/465/wesad+wearable+stress+and+affect+detection) | 15 | chest ECG, 700 Hz | neutral / stress / amusement conditions, with self-report questionnaires |
| [DREAMER](https://zenodo.org/records/546113) | 23 | 2-channel ECG, 256 Hz | self-rated valence, arousal, dominance for 18 film clips |
| [AMIGOS](https://www.eecs.qmul.ac.uk/mmv/datasets/amigos/index.html) | 40 | ECG (+ EEG, GSR) | self-rated valence, arousal, dominance, liking, familiarity |

The notebook's `clip_from_signal` already accepts any ECG file with no annotations, so this is
mostly a matter of running it over these datasets and comparing the results.

---

## 9. Getting started

### 9.1 Installation

```bash
sudo apt install fluidsynth fluid-soundfont-gm      # audio rendering (Ubuntu/Debian)
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 9.2 The notebook

```bash
jupyter notebook sonifying_the_heart.ipynb
```

This is the project. It runs all four stages with explanations, plots and results, and imports
nothing from anywhere else — 59 cells, read or run top to bottom. The expensive steps are
switches at the top, all off by default:

| Switch | When on |
|---|---|
| `RENDER_AUDIO` | renders WAV files with FluidSynth |
| `BUILD_ALL` | composes all 14 example pieces (streams 7 records; a few minutes) |
| `BUILD_STUDY` | builds the blinded listening-study clip set (needs `ffmpeg`) |

With the switches off it streams one record, composes both its clips, and draws every figure in
about a minute. Results for all 14 pieces load from `output/examples_summary.csv` if it is there.

### 9.3 One record, in four lines

Every function below is defined in the notebook; run its cells first.

```python
clips = record_clips('04043', 'afdb')     # Stages 1-2: streamed from PhysioNet
piece = compose(clips['AFIB'])            # Stages 3-4: melody, emotion, arrangement
print(piece.emotion.quadrant, piece.emotion.valence, piece.emotion.arousal)
save(piece, clips['AFIB'], 'my_piece', title='04043 AFib')   # MIDI, WAV, score.png
```

### 9.4 Your own ECG file

No annotations needed — the XQRS detector finds the beats.

```python
signal, fs = load_signal('my_ecg.csv', fs=250)
clip = clip_from_signal(signal, fs, start=0, duration=30)
piece = compose(clip)
save(piece, clip, 'my_analysis', title='my ECG')
```

Example output (the first 30 seconds of record 04043):

```
Beats: 53  mean R-R: 559 ms  RMSSD: 14.2 ms
Emotion: calm_relaxed (valence +0.97, arousal -0.90)
Harmony: 13 consonant, 0 tense, 0 chaotic chords
```

The results, the same three files as each example, go to `output/analysis/<name>/`. That folder
is kept out of git because a real person's ECG is personal health data.

### 9.6 Low-powered machines

- **No data download needed.** Records are streamed (a few hundred KB each).
- **No audio rendering needed.** `--no-audio`, or `RENDER_AUDIO = False`, gives MIDI and plots.
- **Essentia is optional.** It loads TensorFlow, so skip it on a small machine.
- **The notebook defaults to the cheap path.** It streams the data, makes MIDI and plots only,
  and skips the pretrained models.

### 9.7 Optional: reproducing the music2emo results

<details>
<summary>music2emo needs older library versions, so it runs in its own environment (~2.3 GB)</summary>

```bash
git clone --depth 1 https://github.com/AMAAI-Lab/Music2Emotion.git external/Music2Emotion
python3 -m venv external/Music2Emotion/venv_m2e
source external/Music2Emotion/venv_m2e/bin/activate
pip install torch==2.3.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cpu
pip install chordparser==0.4.2 fire==0.7.0 huggingface_hub==0.28.1 hydra-core==1.3.2 \
  librosa==0.10.2.post1 music21==9.3.0 numpy==1.26.4 numba==0.60.0 llvmlite==0.43.0 \
  nnAudio==0.3.1 omegaconf==2.3.0 pandas==2.2.3 Pillow==11.1.0 pretty_midi==0.2.10 \
  pytorch_lightning==2.4.0 PyYAML==6.0.1 Requests==2.32.3 scikit_learn==1.6.1 \
  torch_optimizer==0.3.0 torchmetrics==1.4.1 tqdm==4.66.5 transformers==4.44.0 \
  mir_eval gradio==5.15.0 spotipy==2.24.0 "setuptools<81"
# then run music2emo over output/examples/*/melody.wav from that environment
```
</details>

---

## 10. Project structure

```
├── sonifying_the_heart.ipynb     THE PROJECT: every stage, self-contained
├── README.md                     this file
├── Plan.md                       where the project stands and what comes next
├── project_description.md        full description: design, results, validation plan, ethics
├── Progress.md                   dated log of the work, newest first
├── listening_study_questions.md  the Google Form for the listening study
├── requirements.txt
│   ├── pipeline.py               chains the stages
│   └── __main__.py               command line
└── output/                       created by the pipeline (not in the repository yet)
    ├── examples/<record>_<rhythm>/   melody.mid, arrangement.mid, score.png (+ .wav when built)
    ├── examples_summary.csv          per-clip heartbeat, music and emotion results
    ├── essentia_results.csv          Essentia readings of every melody and arrangement
    └── music2emo_results.csv         music2emo readings of every melody
```

These are created locally and kept out of git:

- `venv/`
- `data/` (PhysioNet downloads)
- `models/` (Essentia weights)
- `external/` (music2emo)
- all `.wav` audio
- `output/analysis/`

---

## 11. Available resources

### 11.1 In this repository

| Resource | What it is |
|---|---|
| [sonifying_the_heart.ipynb](sonifying_the_heart.ipynb) | The project: all four stages with code, explanations, plots and results |
| [Plan.md](Plan.md) | Where the project stands, and what each remaining step would let us conclude |
| [project_description.md](project_description.md) | The full description: motivation, every stage in detail, all results, validation plan, data provenance and ethics |
| [Progress.md](Progress.md) | Dated log of the work, including the bugs found and how they were fixed |
| [listening_study_questions.md](listening_study_questions.md) | The Google Form for the listening study, ready to build |

Running the notebook writes these to `output/`:

| Output | What it is |
|---|---|
| `output/examples/<record>_<rhythm>/` | 14 pieces, one folder each, e.g. `04043_N` and `04043_AFIB`: `melody.mid`, `arrangement.mid`, `score.png`, plus `.wav` files when audio is rendered |
| `output/examples_summary.csv` | Per clip: RMSSD, mean R-R, notes, pitch range and spread, % chromatic, valence, arousal, emotion, instrument, chord counts |
| `output/essentia_results.csv` | Per clip and per render: happy, sad, relaxed and aggressive probabilities; DEAM valence and arousal (only when Essentia runs) |
| `output/music2emo_results.csv` | Per clip: music2emo valence, arousal and mood tags (written by the separate music2emo step, [§9.7](#97-optional-reproducing-the-music2emo-results)) |

MIDI files open in any DAW, in MuseScore, or in an online MIDI player. Until the pipeline has
been run, the results are in [project_description.md §11](project_description.md#11-results).

### 11.2 ECG datasets used

- [MIT-BIH Atrial Fibrillation Database](https://physionet.org/content/afdb/1.0.0/): 25 ten-hour
  recordings of people with AFib.
- [MIT-BIH Arrhythmia Database](https://physionet.org/content/mitdb/1.0.0/): 48 half-hour
  recordings from 47 people.
- [PhysioNet](https://physionet.org/): the archive hosting both.

### 11.3 ECG datasets with emotion labels (for validating Stage 4)

- [WESAD](https://archive.ics.uci.edu/dataset/465/wesad+wearable+stress+and+affect+detection):
  wearable stress and affect detection.
  - 15 people; chest ECG at 700 Hz.
  - Neutral, stress and amusement conditions, plus self-reports.
  - Schmidt & Reiss, 2018, [doi:10.24432/C57K5T](https://doi.org/10.24432/C57K5T).
- [DREAMER](https://zenodo.org/records/546113): EEG and ECG from 23 people watching 18 film
  clips.
  - Self-rated valence, arousal and dominance.
  - Katsigiannis & Ramzan, 2018.
- [AMIGOS](https://www.eecs.qmul.ac.uk/mmv/datasets/amigos/index.html): EEG, ECG and GSR from 40
  people watching emotional videos, alone and in groups.
  - Self-rated valence, arousal and more.
  - Miranda-Correa et al., 2018.

### 11.4 Pretrained music-emotion models

| Model | Used for | Link |
|---|---|---|
| Discogs-EffNet embeddings | audio features for the mood classifiers | [discogs-effnet-bs64-1.pb](https://essentia.upf.edu/models/feature-extractors/discogs-effnet/discogs-effnet-bs64-1.pb) |
| Mood classifiers: happy, sad, relaxed, aggressive | the four mood probabilities | [mood_happy](https://essentia.upf.edu/models/classification-heads/mood_happy/mood_happy-discogs-effnet-1.pb) · [mood_sad](https://essentia.upf.edu/models/classification-heads/mood_sad/mood_sad-discogs-effnet-1.pb) · [mood_relaxed](https://essentia.upf.edu/models/classification-heads/mood_relaxed/mood_relaxed-discogs-effnet-1.pb) · [mood_aggressive](https://essentia.upf.edu/models/classification-heads/mood_aggressive/mood_aggressive-discogs-effnet-1.pb) |
| MusiCNN embeddings | audio features for the valence/arousal model | [msd-musicnn-1.pb](https://essentia.upf.edu/models/feature-extractors/musicnn/msd-musicnn-1.pb) |
| DEAM valence/arousal regressor | valence and arousal on a 1–9 scale | [deam-msd-musicnn-2.pb](https://essentia.upf.edu/models/classification-heads/deam/deam-msd-musicnn-2.pb) |
| music2emo | valence, arousal and mood tags | [code](https://github.com/AMAAI-Lab/Music2Emotion) · [model](https://huggingface.co/amaai-lab/music2emo) · [paper](https://arxiv.org/abs/2502.03979) |
| MERT-v1-95M | the audio backbone used by music2emo | [Hugging Face](https://huggingface.co/m-a-p/MERT-v1-95M) |

The Essentia models (about 25 MB) download automatically on first use. The full catalogue is at
[essentia.upf.edu/models](https://essentia.upf.edu/models.html).

### 11.5 Software and tools

| Tool | Used for |
|---|---|
| [wfdb-python](https://github.com/MIT-LCP/wfdb-python) | reading PhysioNet records, streaming, XQRS heartbeat detection |
| [NumPy](https://numpy.org/) · [SciPy](https://scipy.org/) | signal processing, audio files |
| [pretty_midi](https://github.com/craffel/pretty-midi) · [mido](https://mido.readthedocs.io/) | writing MIDI |
| [FluidSynth](https://www.fluidsynth.org/) + FluidR3 GM soundfont (`fluid-soundfont-gm`) | rendering MIDI to audio |
| [Essentia](https://essentia.upf.edu/) (`essentia-tensorflow`) | running the pretrained models |
| [Matplotlib](https://matplotlib.org/) | score, ECG and emotion-plane plots |
| [pandas](https://pandas.pydata.org/) · [Jupyter](https://jupyter.org/) | the notebook |

Library versions are listed in [requirements.txt](requirements.txt). To use a different
soundfont, set `ECGMUSIC_SOUNDFONT`.

### 11.6 Papers

**ECG data**

- Goldberger AL, et al. PhysioBank, PhysioToolkit, and PhysioNet. *Circulation* 2000;101(23):e215–e220.
  [doi:10.1161/01.CIR.101.23.e215](https://doi.org/10.1161/01.CIR.101.23.e215)
- Moody GB, Mark RG. A new method for detecting atrial fibrillation using R-R intervals.
  *Computers in Cardiology* 1983;10:227–230.
- Moody GB, Mark RG. The impact of the MIT-BIH Arrhythmia Database. *IEEE Engineering in Medicine
  and Biology* 2001;20(3):45–50. [doi:10.1109/51.932724](https://doi.org/10.1109/51.932724)

**Music and emotion**

- Russell JA. A circumplex model of affect. *Journal of Personality and Social Psychology*
  1980;39(6):1161–1178.
- Gabrielsson A, Lindström E. The role of structure in the musical expression of emotions. In:
  Juslin PN, Sloboda JA (eds), *Handbook of Music and Emotion*. Oxford University Press, 2010.
- Aljanaki A, Yang Y-H, Soleymani M. Developing a benchmark for emotional analysis of music.
  *PLOS ONE* 2017 (the DEAM dataset).

**Pretrained models**

- Bogdanov D, et al. Essentia: an audio analysis library for music information retrieval.
  *ISMIR* 2013.
- Alonso-Jiménez P, Serra X, Bogdanov D. Music representation learning based on editorial metadata
  from Discogs. *ISMIR* 2022.
- Kang J, Herremans D. Towards unified music emotion recognition across dimensional and
  categorical models. 2025. [arXiv:2502.03979](https://arxiv.org/abs/2502.03979)

**ECG datasets with emotion labels**

- Schmidt P, et al. Introducing WESAD, a multimodal dataset for wearable stress and affect
  detection. *ICMI* 2018.
- Katsigiannis S, Ramzan N. DREAMER: a database for emotion recognition through EEG and ECG
  signals from wireless low-cost off-the-shelf devices. *IEEE Journal of Biomedical and Health
  Informatics* 2018.
- Miranda-Correa JA, et al. AMIGOS: a dataset for affect, personality and mood research on
  individuals and groups. *IEEE Transactions on Affective Computing* 2021.

### 11.7 Related research: heart-rate variability and emotion

- [Reduced heart rate variability in adults with autism spectrum disorder](https://pubmed.ncbi.nlm.nih.gov/30972967/) (PubMed)
- [Heart rate variability and intervention outcomes targeting emotion regulation in autism](https://www.nature.com/articles/s41598-024-66084-z)
  (*Scientific Reports*, 2024)
- [A wearable heart rate measurement device for children with autism spectrum disorder](https://www.nature.com/articles/s41598-020-75768-1)
  (*Scientific Reports*, 2020)
- [Autistic traits moderate relations between cardiac autonomic activity, interoceptive accuracy, and emotion processing](https://pubmed.ncbi.nlm.nih.gov/32353400/)
  (PubMed, 2020)

How this research relates to the project is discussed in
[project_description.md §14.4](project_description.md#144-using-this-with-autistic-people-or-any-specific-group).

---

## 12. Limitations and ethics

- **Not a medical tool.** Nothing here was validated for diagnosis.
- **Emotion detection is not yet validated against people's own reports.** See
  [§8](#8-validation-status-how-far-does-it-detect-inner-emotion). Treat the detected emotion as
  the character of the person's heart-music, not as a verdict on how they feel.
- **A small, specific dataset.** The results come from 14 clips of 6 adult heart patients,
  recorded in one Boston hospital between 1975 and 1983. The emotion model's ranges were
  calibrated on exactly these clips.
- **Automatic beat marks.** `afdb`'s heartbeat annotations were never corrected by hand. Clip
  selection works around most glitches, but not all.
- **Other people need their own study.** Using this with a specific group, for example as a
  non-verbal emotion aid for autistic people, needs its own validation, consent and ethical
  review. See [project_description.md §14](project_description.md#14-where-the-data-comes-from-and-ethics).
- **Privacy.** ECG recordings are personal health data. Analyses of your own files are kept out
  of git (`output/analysis/`).

---

## 13. How the project was built

The full, dated story is in [Progress.md](Progress.md). In short:

1. **Proposal to plan.** The proposal was turned into a phased plan: environment, data,
   heartbeats, music, presentation.
2. **Data.**
   - Downloaded `afdb` and `mitdb` with a parallel downloader. PhysioNet throttles each
     connection, and `wfdb`'s own downloader uses only two.
   - Later added streaming, so no download is needed.
3. **Heartbeats.** RMSSD clearly separated normal from AFib. We found that `afdb`'s unaudited
   beat marks were corrupting some normal clips, and fixed clip selection.
4. **Music.**
   - Built the melody mapping, then the three-part arrangement (harmony with tension tiers, and
     the lub-dub pulse).
   - Fixed two melody bugs: faster beats went the wrong way, and downward steps left the scale.
5. **Emotion.**
   - Added the music-emotion model.
   - Cross-checked it against Essentia and music2emo, and reported their disagreement honestly.
6. **Any ECG file.** Added XQRS heartbeat detection and checked it against expert annotations.
7. **Rewrite.** Rewrote everything from scratch, and later consolidated it into the single
   notebook [sonifying_the_heart.ipynb](sonifying_the_heart.ipynb).
8. **Inner emotion detection.**
   - Reframed the documentation around ECG data → Heartbeats → Music → Emotion, and wrote
     [project_description.md](project_description.md).
   - Fixed two errors found along the way. Essentia's "sad" and "relaxed" readings were inverted.
     And two of the recordings come from the same person, so the examples cover 6 people, not 7.
