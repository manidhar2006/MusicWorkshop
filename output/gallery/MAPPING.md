# Gallery of examples — ECG and the music made from it

Each row is one 30-second clip: the ECG we started from, and the music the pipeline made
from it. Nothing was tuned per clip — one set of rules produced all of them.

**Do not share this with anyone who still has to take the listening study.** It is
labelled, so it gives away which recording is which. The blinded clip numbers are not in
here; they live only in `output/listening_study/KEY.csv`.

| Example | Rhythm | bpm | RMSSD | Notes off scale | Emotion | ECG image | Melody | Arrangement |
|---|---|---|---|---|---|---|---|---|
| `04015_AFIB` | afib | 137 | 126.1 ms | 57% | tense_anxious | [image](ecg/04015_AFIB_ecg.png) | [mp3](audio/04015_AFIB_melody.mp3) | [mp3](audio/04015_AFIB_arrangement.mp3) |
| `04015_N` | normal | 80 | 7.6 ms | 0% | calm_relaxed | [image](ecg/04015_N_ecg.png) | [mp3](audio/04015_N_melody.mp3) | [mp3](audio/04015_N_arrangement.mp3) |
| `04043_AFIB` | afib | 128 | 134.9 ms | 52% | tense_anxious | [image](ecg/04043_AFIB_ecg.png) | [mp3](audio/04043_AFIB_melody.mp3) | [mp3](audio/04043_AFIB_arrangement.mp3) |
| `04043_N` | normal | 108 | 8.5 ms | 0% | calm_relaxed | [image](ecg/04043_N_ecg.png) | [mp3](audio/04043_N_melody.mp3) | [mp3](audio/04043_N_arrangement.mp3) |
| `04126_AFIB` | afib | 160 | 141.9 ms | 66% | tense_anxious | [image](ecg/04126_AFIB_ecg.png) | [mp3](audio/04126_AFIB_melody.mp3) | [mp3](audio/04126_AFIB_arrangement.mp3) |
| `04126_N` | normal | 79 | 18.6 ms | 0% | calm_relaxed | [image](ecg/04126_N_ecg.png) | [mp3](audio/04126_N_melody.mp3) | [mp3](audio/04126_N_arrangement.mp3) |
| `06995_AFIB` | afib | 112 | 122.8 ms | 51% | tense_anxious | [image](ecg/06995_AFIB_ecg.png) | [mp3](audio/06995_AFIB_melody.mp3) | [mp3](audio/06995_AFIB_arrangement.mp3) |
| `06995_N` | normal | 83 | 17.8 ms | 0% | calm_relaxed | [image](ecg/06995_N_ecg.png) | [mp3](audio/06995_N_melody.mp3) | [mp3](audio/06995_N_arrangement.mp3) |
| `08455_AFIB` | afib | 122 | 99.9 ms | 31% | happy_excited | [image](ecg/08455_AFIB_ecg.png) | [mp3](audio/08455_AFIB_melody.mp3) | [mp3](audio/08455_AFIB_arrangement.mp3) |
| `08455_N` | normal | 79 | 8.3 ms | 0% | calm_relaxed | [image](ecg/08455_N_ecg.png) | [mp3](audio/08455_N_melody.mp3) | [mp3](audio/08455_N_arrangement.mp3) |
| `201_AFIB` | afib | 101 | 194.3 ms | 52% | tense_anxious | [image](ecg/201_AFIB_ecg.png) | [mp3](audio/201_AFIB_melody.mp3) | [mp3](audio/201_AFIB_arrangement.mp3) |
| `201_N` | normal | 50 | 64.1 ms | 0% | calm_relaxed | [image](ecg/201_N_ecg.png) | [mp3](audio/201_N_melody.mp3) | [mp3](audio/201_N_arrangement.mp3) |
| `202_AFIB` | afib | 125 | 146.9 ms | 33% | tense_anxious | [image](ecg/202_AFIB_ecg.png) | [mp3](audio/202_AFIB_melody.mp3) | [mp3](audio/202_AFIB_arrangement.mp3) |
| `202_N` | normal | 56 | 37.4 ms | 0% | calm_relaxed | [image](ecg/202_N_ecg.png) | [mp3](audio/202_N_melody.mp3) | [mp3](audio/202_N_arrangement.mp3) |
| `219_AFIB` ¹ | afib | 79 | 145.9 ms | 31% | calm_relaxed | [image](ecg/219_AFIB_ecg.png) | [mp3](audio/219_AFIB_melody.mp3) | [mp3](audio/219_AFIB_arrangement.mp3) |
| `219_N` ¹ | normal | 58 | 270.6 ms | 39% | tense_anxious | [image](ecg/219_N_ecg.png) | [mp3](audio/219_N_melody.mp3) | [mp3](audio/219_N_arrangement.mp3) |

¹ Record 219 is left out of the headline results table. The window its database calls
*normal* is more irregular than its AFib window - 133 blocked atrial beats - and every
stage of the pipeline flagged it without being told. It is kept here because that
disagreement is one of the project's more interesting findings.

## What to listen for

- **`_N` (normal rhythm)** - the beats arrive on schedule, so the melody stays on one note
  or close to it, over chords that never sour. Three of them never leave C4 at all.
- **`_AFIB`** - the beats arrive at random, so the melody scatters across three octaves and
  leaves the scale for between a third and two thirds of its notes.
- **`08455_AFIB`** is the interesting exception: a genuinely mild stretch of AFib, and the
  music reports it as mild rather than forcing it into a category.

## Columns in `MAPPING.csv`

| Column | Meaning |
|---|---|
| `example` | `<record>_<rhythm>`, matching the folder in `output/examples/` |
| `database`, `record` | where the recording comes from on PhysioNet |
| `rhythm` | `normal` or `afib`, as labelled by the database's own experts |
| `ecg_image` | the ECG picture: full clip, plus the opening enlarged with the gaps between beats in ms |
| `melody_mp3` | one note per heartbeat, plain piano |
| `arrangement_mp3` | the same melody on the instrument our emotion model chose, plus strings and a lub-dub pulse |
| `score_plot`, `melody_midi`, `arrangement_midi` | paths inside `output/`, relative to it |
| `heart_rate_bpm`, `rmssd_ms` | heart rate, and how much the beat-to-beat timing varies |
| `notes`, `pct_notes_off_scale` | how many notes, and the share that left the scale |
| `valence`, `arousal`, `emotion` | where our model places the piece on Russell's plane |
| `melody_instrument` | the instrument the emotion picked for the arrangement |
| `chords_consonant` / `_tense` / `_chaotic` | how the harmony reacted |

Regenerate everything here from the appendix of `sonifying_the_heart.ipynb`.
