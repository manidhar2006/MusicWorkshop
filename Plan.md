# Sonifying the Heart — where we are, and what comes next

**Inner emotion detection from ECG through music:** ECG data → Heartbeats → Music → Emotion

**Written:** 2026-10-08 · Overview: [README.md](README.md) · Full detail:
[project_description.md](project_description.md) · Session log: [Progress.md](Progress.md)

This file is the single place to understand the project from the beginning, what it has actually
shown, what it has not, and what each remaining step would let us conclude. It is the one to read
first, and the one to hand to someone who has not followed along.

---

## Contents

1. [The idea in one page](#1-the-idea-in-one-page)
2. [The story so far](#2-the-story-so-far)
3. [Where we stand today](#3-where-we-stand-today)
4. [What we have shown, and what we have not](#4-what-we-have-shown-and-what-we-have-not)
5. [The two projects inside this one](#5-the-two-projects-inside-this-one)
6. [Future steps, and what each would let us conclude](#6-future-steps-and-what-each-would-let-us-conclude)
7. [Decisions that are not ours to make alone](#7-decisions-that-are-not-ours-to-make-alone)
8. [What the final deliverable could be](#8-what-the-final-deliverable-could-be)
9. [The honest summary](#9-the-honest-summary)

---

## 1. The idea in one page

A heart does not beat like a metronome. The gap between one beat and the next shifts constantly,
and how it shifts says something about the state of the body producing it. We turn that shifting
into music, and then ask what emotion the music carries.

The pipeline has four stages.

| Stage | What happens | Where it lives |
|---|---|---|
| **1. ECG data** | Real recordings from PhysioNet, streamed on demand. Any WFDB or CSV file also works. | [`data.py`](ecgmusic/data.py) |
| **2. Heartbeats** | Find the R-peaks, from annotations or the XQRS detector. Compute R–R intervals and RMSSD. Pick a 30-second clip. | [`data.py`](ecgmusic/data.py) |
| **3. Music** | One note per heartbeat, plus a string harmony and a lub-dub pulse. Render to MIDI, audio and a score. | [`melody.py`](ecgmusic/melody.py), [`arrangement.py`](ecgmusic/arrangement.py), [`audio.py`](ecgmusic/audio.py) |
| **4. Emotion** | Place the music on Russell's valence–arousal plane, with two pretrained models as independent second opinions. | [`emotion.py`](ecgmusic/emotion.py), [`essentia_models.py`](ecgmusic/essentia_models.py) |

**The sonification rule**, which is the heart of the project:

- Each heartbeat becomes exactly one note, starting at the R-peak.
- The note lasts 85% of the gap to the next beat, so the rhythm of the music *is* the rhythm of
  the heart.
- Its loudness comes from the ECG amplitude at that beat.
- Its **pitch** follows how far that beat's interval deviates from the mean of the previous five.
  On time means C4; a faster beat goes up the scale, a slower one goes down.
- While the deviation stays under 12% the melody uses the C major pentatonic scale, so it stays
  consonant. Past 12% it goes chromatic, and starts to sound wrong.
- The harmony sours in step: a chord turns diminished at 12% average deviation, and into a
  semitone cluster at 25%.

Nothing in that rule knows what disease the person has. It only knows timing.

**What we compare.** Most recordings in the MIT-BIH Atrial Fibrillation Database contain both
normal rhythm and atrial fibrillation, so we can hear *the same person* in both states — holding
age, physiology, electrodes and equipment constant. That is the experiment: 7 recordings from 6
people, one normal clip and one AFib clip each, 14 pieces.

---

## 2. The story so far

### Setting up — late September

Read the proposal, turned it into a phased plan, built the environment. Discovered that PhysioNet
throttles each connection to roughly 20 KB/s and that `wfdb`'s own downloader opens only two, so
we wrote a parallel downloader and used streaming for quick looks.

### First heartbeats, first melody

R–R intervals and RMSSD for record 04043: 13.8 ms in the normal window against 194.7 ms in the
AFib window. The first melody, the first MIDI file, the first audio.

### The data fought back

Running five records exposed a real problem. Taking the first 30 seconds of each made two
"normal" clips *more* irregular than their AFib counterparts — record 04015 gave 199 ms against
105 ms. The cause was `afdb`'s heartbeat marks, which come from an automatic detector and were
never corrected by hand, so they jitter inside correctly labelled normal stretches.

**The fix:** instead of taking the first window, keep the *steadiest* normal window and the AFib
window with the most detected beats. After that, normal clips ran 7.6–18.6 ms against AFib
99.9–141.9 ms. This is the sort of thing that only shows up when you actually look at the data.

### Record 219, which turned out to matter

Extending to `mitdb` found three records with both rhythms: 201, 202 and 219. We excluded 219,
because even its steadiest "normal" window has an RMSSD of 270.6 ms — *more* irregular than its
own AFib clip at 145.9 ms.

The annotations explain it: 133 non-conducted P-waves, atrial beats blocked before they reach the
ventricles. A genuine irregularity that the label "normal" does not capture. Every stage of our
pipeline flagged this record independently, without being told anything.

At the time this looked like a nuisance. It is now one of the two most interesting results we
have.

### The arrangement, and two bugs

Added strings playing C–Am–F–G, souring with the rhythm, and a lub-dub bass-drum pulse on every
beat. Mixed so the strings sit 7–9 dB and the pulse 12–17 dB below the melody.

Two melody bugs surfaced while writing it: faster beats were going *down* instead of up, and
downward steps were mirroring intervals instead of walking down the scale. Both fixed, with a
regression check confirming that only the pitches changed.

### Stage 4 — reading emotion from the music

Built our own model on Russell's circumplex, using three musical cues: rhythmic irregularity,
pitch spread and consonance. Tempo and loudness are deliberately excluded, because tempo varies
more between people than between rhythms.

Then two independent opinions: Essentia's four mood classifiers plus its DEAM valence/arousal
head, and music2emo in its own environment.

### The Essentia bug, and a retraction

Each Essentia mood classifier outputs two probabilities, in a model-specific order — `happy,
non_happy` but `non_sad, sad`. Our code always read the first one, so "sad" and "relaxed" were
reporting *not* sad and *not* relaxed.

We checked every model's metadata, fixed the column mapping, corrected the saved results, and
**withdrew two published claims**: "every clip's strongest mood is sad", and "the arrangement
lowers the normal pieces' sadness by about 70%". Both were artefacts of the inversion.

In the same pass we corrected the participant count: PhysioNet's header says `mitdb` record 202
came from the same analog tape as record 201, so the 7 recordings are from **6 people**, not 7.

### The rewrite

Rewrote the whole codebase as the `ecgmusic` package with a 40-cell notebook, organised by
responsibility. Written without executing anything, because the machine was low on compute —
which left the project with a serious unverified risk for a week.

### Sprint 3, and then today

Sprint 3 reports written and compiled. Then, on 8 October:

- Explored moving the input signal from ECG to **EEG** and wrote a case for it. Dropped it: EEG
  sonification is a *more* crowded field than ECG sonification, so switching would not make the
  project more novel, and there was no working prototype to switch.
- **Ran the code.** The venv turned out to be broken — built against Python 3.12, which no longer
  exists on this system. Rebuilt it, and the pipeline ran end to end.
- **All 14 examples reproduced the published numbers exactly.**
- Built the listening study.

---

## 3. Where we stand today

| Part | Status | Note |
|---|---|---|
| Stage 1: ECG data | ✅ Done | `afdb` and `mitdb`, streamed. Any WFDB or CSV file works. |
| Stage 2: Heartbeats | ✅ Done | Annotations or XQRS; clip selection survives `afdb`'s jittery marks. |
| Stage 3: Music | ✅ Done | Melody, arrangement, MIDI, audio, score plots. |
| Stage 4: Emotion | ✅ Built · ⬜ not validated | Three models. Never compared against what anyone actually felt. |
| Code | ✅ Run and verified | 14/14 examples match §11.1 exactly, 8 October. |
| Essentia / music2emo tables | 🟨 Not re-run | §11.2 and §11.3 still rest on the first implementation. |
| Listening study | ✅ Built, ⬜ no listeners | 16 blinded clips, form questions, analysis script. |
| Documentation | ✅ Done | README, project_description, Progress, this file. |
| Git | 🟨 Uncommitted | Today's work is not committed. |

### What exists on disk

```
ecgmusic/                       the package — 11 modules
main.ipynb                      40-cell walkthrough
output/examples/                14 pieces: MIDI, WAV, score PNG
output/listening_study/         16 blinded mp3s + KEY.csv
listening_study_questions.md    the Google Form, ready to build
project_description.md          the full description, 18 sections
```

---

## 4. What we have shown, and what we have not

### Shown

1. **The sonification is faithful and reproducible.** The same rules, independently reimplemented,
   produce identical numbers on all 14 clips.
2. **The music separates the two rhythms, every time.** Every normal melody stays entirely within
   the scale, with a pitch standard deviation of at most 2 semitones; three never leave C4. Every
   AFib melody leaves the scale for 31–66% of its notes. All 67 chords under the normal pieces are
   consonant; 68 of the 111 AFib chords turn tense or chaotic.
3. **Our emotion model moves consistently with the rhythm.** 7 of 7 normal pieces read calm, 6 of
   7 AFib pieces read tense, and every AFib piece has lower valence and higher arousal than the
   same person's normal piece.
4. **The system conveys degree, not just category.** Record 08455's AFib stretch is genuinely
   mild, and the system placed it at the centre of the plane rather than in the tense quadrant.
5. **The system caught a mislabelled record.** 219, independently flagged by every stage.
6. **Pretrained music-emotion models are unreliable on music like this.** All three methods hear a
   difference in every recording, but no two agree on both axes. Essentia hears AFib as *higher*
   in valence in 7 of 7; music2emo hears it as *lower* in 6 of 7.

### Not shown

1. **That any listener can hear any of this.** Every claim above is a measurement on our own
   output. No human has been asked.
2. **That the music's emotion reflects the person's emotion.** This is the project's central
   hypothesis and it is untested. The databases we use contain no emotional or psychological data
   at all, so it *cannot* be tested on them.
3. **That the mapping is right for healthy hearts.** Slow, relaxed breathing raises beat-to-beat
   variability (respiratory sinus arrhythmia) while acute stress lowers it — the opposite of our
   mapping. Our rule would call a calm, healthy person tense.
4. **That this beats plain HRV.** Our model is, in effect, a musical re-description of heart-rate
   variability. Whether routing through music adds anything is an open question.

### The honest statement of what the system does

> It detects how calm or agitated the **heart's rhythm sounds**, and names that with the
> vocabulary of music emotion. Whether that corresponds to the person's inner emotion is the
> hypothesis, not the finding.

---

## 5. The two projects inside this one

Most of the confusion about this project comes from it being two projects under one name.

| | **Project 1 — the sonification** | **Project 2 — inner emotion detection** |
|---|---|---|
| **Claim** | Cardiac rhythm can be translated into music faithfully enough that a listener hears what is clinically there | The emotion of that music reflects what the person feels |
| **Status** | Nearly finished; one gap left | Unvalidated, and unvalidatable on our data |
| **What it needs** | Listeners | Emotion-labelled physiological datasets, access requests, a subject-independent study |
| **Cost to finish** | One class session | A semester at least |
| **Is it novel?** | No. ECG sonification is established. | The specific question is open, but crowded. |

**Project 1 is the course deliverable. Project 2 is the research question we raise at the end.**

Novelty is not the bar for a course project — honest execution is, and that is where this work is
strong. Three times now the project has chosen accuracy over a better-looking result: withdrawing
the Essentia claims, excluding record 219, and correcting 7 people to 6.

---

## 6. Future steps, and what each would let us conclude

This is the part that matters. Each step is listed with what it costs and, more importantly,
**what we could honestly say afterwards** — including when the result goes against us.

### Step 1 — Run the listening study · *the one that finishes Project 1*

**Do:** circulate the form in
[listening_study_questions.md](listening_study_questions.md), collect 20–30 responses, run
`python -m ecgmusic.listening_study responses.csv`.

**Cost:** one class session. No compute, no dataset access, no approvals.

**Why it is the right next step:** every claim we have is a measurement on our own output. This
is the only step that puts a human in the loop, and it closes the one gap that belongs to Project
1 rather than Project 2.

**What we could conclude:**

| Outcome | Interpretation |
|---|---|
| Listeners rate AFib clips as less steady **and** lower valence / higher arousal, tracking the model | The translation works end to end. The sonification carries clinically meaningful structure to an untrained ear. **Project 1 is complete and verified.** |
| Listeners hear the irregularity (Q4) but their emotion ratings don't move | The mapping is *audible* but not *affective*. We would have located the break precisely: the rhythm survives, the emotional reading is ours, not theirs. A sharper and more interesting finding than a flat success. |
| Listeners hear nothing reliable | The mapping is measurable but not perceptible. That is a genuine negative result about sonification design, and it would point at the obvious culprits — 30 seconds may be too short, the pentatonic constraint may be flattening the difference. |
| Trained musicians separate the clips but untrained listeners do not | The information is there but needs a trained ear. Relevant to any practical use, and a nice secondary result from one extra question. |

**The hidden control.** If listeners also rate record 219's *normal*-labelled clip as the less
steady one, our strongest finding upgrades from "our algorithm disagreed with a database label"
to **"human listeners agreed with our algorithm against the label."** That is the single best
sentence this project could earn.

---

### Step 2 — Re-run Essentia and music2emo · *tidying up*

**Do:** `python -m ecgmusic build` without `--no-essentia`, then the music2emo cross-check.

**Cost:** moderate compute. Downloads several TensorFlow models; music2emo needs its own
environment.

**What we could conclude:** §11.2 and §11.3 currently rest on the first implementation. If the
regenerated audio reproduces them, the *whole* results section is verified rather than two thirds
of it. If it does not, we have found a discrepancy worth investigating before anyone else does.

---

### Step 3 — Widen to more recordings · *cheap evidence*

**Do:** extend from 5 `afdb` records to the ~21 that have at least 30 seconds of both rhythms.

**Cost:** almost nothing — same light command, streaming plus numpy.

**What we could conclude:** "7 of 7 recordings" becomes "n of 21", roughly tripling the evidence
base for every claim in §11.1. It would also stress-test clip selection and will probably surface
another 219-like case — which would be a *good* outcome, because it would show the first one was
not a fluke.

---

### Step 4 — Tune the music by ear · *the part a music course cares about*

**Do:** listen critically and revisit the numbers that were never heard, only chosen: the 12%
chromatic threshold, the 85% note length, the 12% and 25% chord thresholds, the instrument
assignments.

**Cost:** listening time.

**What we could conclude:** so far every parameter has been justified by what it *measures*, not
by how it *sounds*. A music workshop deliverable should be able to say why a piece sounds the way
it does as a musical decision. This is also the step that would answer the harder question: is
this music worth listening to, or only different?

---

### Step 5 — Validate Stage 4 properly · *Project 2, and probably beyond this course*

**Do:** acquire WESAD, DREAMER or AMIGOS — ECG recorded with self-reported emotion — cut each
participant's signal into windows matching the labelled conditions, run `analyze_signal()` on
each, and correlate our valence and arousal against what the person reported. Baseline against
plain HRV. Fit on some participants and test on others (leave-one-subject-out).

**Cost:** high. Access requests, some with a signed licence; large downloads; a real analysis.

**What we could conclude:**

| Outcome | Interpretation |
|---|---|
| Our valence/arousal correlates with self-reports, and beats plain HRV | The strong result. Routing physiology through music adds information. |
| Correlates, but no better than plain HRV | The music is a *presentation* of HRV, not an extraction of anything new. Still worth having — a presentation layer has its own value — but the claim shrinks and must be stated honestly. |
| Does not correlate | The central hypothesis fails. We would report it, and §12 of the project description already predicts the likely reason: our mapping reads variability as tension, which inverts for healthy hearts. |

**Note the asymmetry.** Step 1 can be finished this semester and completes a project. Step 5
cannot, and might not succeed. That is why Step 1 comes first.

---

### Step 6 — A mapping for healthy hearts · *the known defect*

**Do:** distinguish slow, breathing-locked variability from beat-to-beat chaos — respiratory sinus
arrhythmia oscillates at breathing rate, around 0.15–0.4 Hz, while AFib is irregular at every
timescale. Read the former as calm.

**What we could conclude:** this is the single clearest known defect in the system, and it is
written down in §12 as a limitation. Fixing it would turn a stated limitation into a contribution,
and it is a prerequisite for the tool ever being pointed at a healthy person.

---

### Priority

```
Step 1  Listening study        ← do this first; it finishes Project 1
Step 3  Widen the records      ← nearly free, do it alongside
Step 2  Re-run the models      ← when compute allows
Step 4  Tune by ear            ← the music-course deliverable
Step 6  Healthy-heart mapping  ← if time allows
Step 5  Full validation        ← future work; name it, don't start it
```

---

## 7. Decisions that are not ours to make alone

Four questions for the professor. They change what the remaining weeks are spent on.

1. **What is the final deliverable?** Report, presentation, live demo, or a performance?
   Everything else follows from this.
2. **Does the music need to be *good*, or only *different*?** We have optimised for measurable
   separation. A music course may care whether the pieces are worth hearing — a different goal
   that would redirect the remaining effort towards Step 4.
3. **Is a listening study with classmates acceptable as validation, and can we use class time?**
4. **How much does novelty matter?** This is not a novel idea; ECG sonification is established.
   We think the contribution is honest execution plus two specific findings. Worth confirming that
   is the right standard.

---

## 8. What the final deliverable could be

Three options, not mutually exclusive.

**A report.** The material already exists — `project_description.md` is 18 sections and would
need editing down rather than writing. Add the listening-study result and it is finished.

**A presentation with live audio.** Thirty seconds of a normal clip against thirty seconds of the
same person's AFib clip makes the point faster than any table. The score plots are good enough to
project.

**A live demo.** `analyze_file` already takes any WFDB or CSV ECG file, detects beats with XQRS,
and produces music plus a score in one command. Dropping in a file and playing the result is a
strong five minutes, and the code for it is written and now verified to run.

---

## 9. The honest summary

What to say if asked to defend this project in two sentences:

> We built a complete, transparent system that turns a heartbeat into music, where every mapping
> decision is stated and testable. In doing so we caught a mislabelled record in a widely used
> medical database, found a bug in how a standard music-analysis toolkit's outputs are read, and
> showed that three independent music-emotion models cannot agree on music like ours — and the
> one thing nobody in this area usually checks, whether a listener can actually *hear* what the
> mapping encodes, is what we are testing next.

That is not a novelty claim. It is a claim about rigour, and it is one we can support.
