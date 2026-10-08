# Listening Study — Google Form Questions

Everything needed to build the form and circulate it. Copy the text in the boxes straight into
Google Forms.

**Audio:** `output/listening_study/clip_01.mp3` … `clip_16.mp3` (16 files, ~380 KB each).
**The answer key:** `output/listening_study/KEY.csv`. **Never share it with participants**, and
don't paste any of it into the form. Section 11 of the notebook rebuilds both the clips and the
key if you need them again.

---

## 1. Before you build the form

### Host the audio

Google Forms cannot play an audio file directly, so the clips have to live somewhere the
participant can reach in one click.

**Recommended — Google Drive.** Upload all 16 mp3s to one Drive folder, set the folder to
*Anyone with the link → Viewer*, then copy each file's individual link. A participant clicks it,
Drive's preview player opens in a new tab, they listen, they come back.

**Nicer, but more work — YouTube.** Turn each clip into a video with a still image, upload as
*Unlisted*, and use Forms' own "Add video" button so the player sits inside the form. One command
per clip:

```bash
ffmpeg -loop 1 -i cover.png -i clip_01.mp3 -shortest -c:v libx264 -tune stillimage -c:a aac -b:a 128k clip_01.mp4
```

### Rules that decide whether the result means anything

- **Do not tell participants what the clips are** until they have finished. Not in the title, not
  in the description, not in the message you send with the link. If they know some clips come
  from a diseased heart, they will rate the label instead of the sound.
- **Keep the clips in the numbered order.** It is already randomised, and no two clips from the
  same recording sit next to each other.
- **Do not rename the clips** or reorder them. `KEY.csv` maps `clip_01`…`clip_16` back to the
  recordings, and the analysis depends on that mapping.
- **Keep the question titles exactly as written below.** The analysis script finds each column by
  looking for `clip_NN` plus a keyword in the column header. Change the wording and the parser
  stops finding it.
- Turn on **Required** for every question.
- Leave *Collect email addresses* **off**. The study is anonymous.

---

## 2. Form header

> **Title**
> ```
> How does this music feel?
> ```

> **Description**
> ```
> You'll hear 16 short piano pieces, about 30 seconds each, and answer four quick questions
> about each one. It takes around 15 minutes.
>
> Please use headphones if you can, and find somewhere reasonably quiet.
>
> There are no right answers. We want your immediate impression, not a considered analysis —
> trust your first reaction.
>
> Your answers are anonymous and will be used only for a course project. Taking part is
> voluntary and you can stop at any point.
>
> We're deliberately not saying where this music comes from until the end. Knowing would change
> what you hear.
> ```

---

## 3. Opening section — two questions

> **Question** · *Short answer*, Required, with response validation set to **Number → Whole
> number → Between 0 and 40**
> ```
> Years of formal musical training
> ```
> **Description**
> ```
> Lessons, school music, an instrument you studied. Enter 0 if none.
> ```

> **Question** · *Multiple choice*, Required
> ```
> How are you listening?
> ```
> Options:
> ```
> Headphones or earphones
> Laptop or phone speakers
> External speakers
> ```

---

## 4. The 16 clip sections

Make **one section per clip** (*Add section*), so participants see one piece at a time. Each
section is identical except for the number. Below is the pattern for clip 01 — repeat it for
`clip_02` through `clip_16`, changing only the two-digit number everywhere it appears.

> **Section title**
> ```
> Clip 1 of 16
> ```
> **Section description** — paste the Drive link for this clip
> ```
> Listen to the whole clip once, then answer the four questions below.
>
> ▶ <paste the link to clip_01.mp3 here>
> ```

Then the four questions, in this order.

### Question 1 · *Linear scale*, Required

> **Title** — the `clip_01` prefix matters, keep it
> ```
> clip_01 - How pleasant does it sound?
> ```
> Scale: **1 to 9**
> Label for 1:
> ```
> Very unpleasant
> ```
> Label for 9:
> ```
> Very pleasant
> ```

### Question 2 · *Linear scale*, Required

> **Title**
> ```
> clip_01 - How energetic does it sound?
> ```
> Scale: **1 to 9**
> Label for 1:
> ```
> Very calm
> ```
> Label for 9:
> ```
> Very energetic
> ```

### Question 3 · *Multiple choice*, Required

> **Title**
> ```
> clip_01 - Which word fits best?
> ```
> Options — exactly these four words, in lower case:
> ```
> calm
> tense
> happy
> sad
> ```

### Question 4 · *Linear scale*, Required

> **Title**
> ```
> clip_01 - How steady was the rhythm?
> ```
> **Description**
> ```
> Did the beat feel even, or did it wander?
> ```
> Scale: **1 to 9**
> Label for 1:
> ```
> Very irregular
> ```
> Label for 9:
> ```
> Very steady
> ```

**Tip:** build clip 01's section completely, then use the section's ⋮ menu → **Duplicate
section** fifteen times, and edit the number in each. Far faster than building 64 questions by
hand.

---

## 5. Closing section — the debrief

Add one last section after clip 16. It carries no questions; it is what participants read once
their answers are in.

> **Section title**
> ```
> What you were listening to
> ```
> **Description**
> ```
> Every piece was generated from a real human heartbeat. Each note is one beat of a recorded
> ECG: the pitch follows how early or late that beat arrived compared with the beats before it,
> and the note lasts as long as the gap to the next beat.
>
> Half the clips came from hearts in normal rhythm. The other half came from the same people
> during atrial fibrillation, a condition where the heart beats irregularly. Nothing else
> differed — same instrument, same rules, same length.
>
> We're testing whether that difference survives the trip into music and reaches a listener.
> Your answers are what tells us.
>
> The recordings come from the MIT-BIH databases on PhysioNet, collected from cardiac patients
> in Boston between 1975 and 1983.
>
> Thank you.
> ```

---

## 6. The four questions, and why each is there

| # | Question | What it measures | Why it is in the form |
|---|---|---|---|
| 1 | How pleasant | **Valence**, 1–9 | The first axis of Russell's circumplex, which our model outputs. The 1–9 scale is the one DEAP, DREAMER and MAHNOB-HCI use, so our numbers sit on a standard scale. |
| 2 | How energetic | **Arousal**, 1–9 | The second axis. Together, questions 1 and 2 are directly comparable to the model's own valence and arousal. |
| 3 | Which word | **Quadrant**, forced choice | The four options are exactly our four quadrants, so we get a hit rate against a 25% chance level. |
| 4 | How steady | **Perceived irregularity**, 1–9 | Separates two different claims: *can they hear the irregularity* and *does it change how they feel*. Without this we could not tell which step of the pipeline worked. |

---

## 7. How many people

Twenty to thirty is plenty. The main test is **paired** — each recording contributes one normal
clip and one AFib clip, compared against each other — which is statistically efficient and does
not need a large sample.

Run it on two or three people first and watch them do it. You are checking that the links play,
that the form is not confusing, and that it really takes about fifteen minutes.

---

## 8. When the responses are in

In the Forms editor open **Responses → ⋮ → Download responses (.csv)**, then:

Save it as `responses.csv` beside the notebook, open
[sonifying_the_heart.ipynb](sonifying_the_heart.ipynb), and run **section 11**. It reads Google
Forms' own export shape directly — finding each rating column by the `clip_NN` in its header —
and reports:

1. **Spearman correlation** between the model's valence and arousal and the listeners' means,
   across all 16 clips. The headline number: does the model predict what people hear?
2. **A paired comparison per recording**, AFib against normal, with a Wilcoxon signed-rank test.
3. **The forced-choice hit rate** against the 25% chance level.
4. **Record 219**, the hidden control — see below.

### The hidden control

Two of the sixteen clips come from record 219, which is **not** in our published results. The
database labels one of its stretches "normal", but our pipeline disagreed and flagged it as the
more irregular of the two — correctly, as its annotations show 133 non-conducted P-waves.

If listeners also rate the *normal*-labelled clip as the less steady one, that is independent
human confirmation of the strongest finding in the project. The analysis checks this
automatically and says so in plain words.

Nothing in the form marks these two clips out, and nothing should.
