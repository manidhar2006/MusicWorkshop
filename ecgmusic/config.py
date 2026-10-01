"""Every path and tunable number used by the pipeline, in one place."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
EXAMPLES_DIR = OUTPUT_DIR / "examples"
ANALYSIS_DIR = OUTPUT_DIR / "analysis"
ESSENTIA_DIR = ROOT / "models" / "essentia"
MUSIC2EMO_DIR = ROOT / "external" / "Music2Emotion"

# --- ECG data -------------------------------------------------------------------------------
PHYSIONET_FILES_URL = "https://physionet.org/files"
DOWNLOAD_WORKERS = 8
EXAMPLE_RECORDS = (("afdb", "04015"), ("afdb", "04043"), ("afdb", "04126"), ("afdb", "06995"),
                   ("afdb", "08455"), ("mitdb", "201"), ("mitdb", "202"))
CLIP_SECONDS = 30
CANDIDATE_WINDOWS = 5
MIN_INTERVALS_PER_WINDOW = 5
# afdb's automatic beat marks can jitter inside a correctly labelled "N" stretch, so the
# steadiest normal window is kept (real sinus rhythm is low-variability) and the AFib window
# with the most detected beats.
SELECTION = {"N": "steadiest", "AFIB": "most_beats"}
BEAT_SYMBOLS = frozenset("NLRBAJSVrFejnE/fQ")
MIN_ANALYSIS_SECONDS = 5
MIN_DETECTED_BEATS = 6

# --- Melody ---------------------------------------------------------------------------------
ROOT_NOTE = 60  # C4
PENTATONIC = (0, 2, 4, 7, 9)  # C D E G A
CHROMATIC = tuple(range(12))
OCTAVE_RANGE = 2
RUNNING_MEAN_BEATS = 5
CHROMATIC_THRESHOLD = 0.12
FULL_RANGE_DEVIATION = 0.5
NOTE_LENGTH = 0.85  # fraction of the R-R interval
VELOCITY_RANGE = (40, 110)
PITCH_RANGE = (21, 108)
PEAK_SEARCH_SAMPLES = 5

# --- Emotion estimate -----------------------------------------------------------------------
QUADRANTS = {
    "happy_excited": {"valence": "+", "arousal": "+", "program": 12, "instrument": "Marimba"},
    "tense_anxious": {"valence": "-", "arousal": "+", "program": 30, "instrument": "Distortion Guitar"},
    "sad_depressed": {"valence": "-", "arousal": "-", "program": 42, "instrument": "Cello"},
    "calm_relaxed": {"valence": "+", "arousal": "-", "program": 24, "instrument": "Acoustic Guitar (nylon)"},
}
# Calibrated on the 14 example clips. Tempo and loudness are left out on purpose: tempo varies
# more between people than between rhythms, and loudness is re-scaled inside every clip.
IRREGULARITY_RANGE = (0.0, 0.30)
SPREAD_RANGE = (0.0, 11.0)
CONSONANCE_RANGE = (0.30, 1.0)
AROUSAL_WEIGHTS = (0.55, 0.45)  # rhythmic irregularity, pitch spread
VALENCE_WEIGHTS = (0.70, 0.30)  # consonance, pitch steadiness

# --- Arrangement ----------------------------------------------------------------------------
PROGRESSION = ((48, (0, 4, 7)), (45, (0, 3, 7)), (41, (0, 4, 7)), (43, (0, 4, 7)))  # C Am F G
BEATS_PER_CHORD = 4
TENSE_AT, CHAOTIC_AT = 0.12, 0.25  # average |R-R deviation| of a chord's beats
CHORD_SHAPES = {"tense": (0, 3, 6), "chaotic": (0, 1, 6)}  # diminished triad, semitone cluster
CHORD_VELOCITY = {"consonant": 34, "tense": 44, "chaotic": 54}
PIANO_PROGRAM, STRINGS_PROGRAM, DRUM_KIT_PROGRAM = 0, 48, 0
LUB_DRUM, DUB_DRUM = 35, 36  # acoustic bass drum, bass drum 1
DRUM_HIT_SECONDS = 0.1
DUB_DELAY_FRACTION, DUB_DELAY_MAX = 0.35, 0.30
DUB_VELOCITY_RATIO = 0.6
PULSE_VELOCITY_RANGE = (30, 70)

# --- Audio ----------------------------------------------------------------------------------
SOUNDFONT = os.environ.get("ECGMUSIC_SOUNDFONT", "/usr/share/sounds/sf2/FluidR3_GM.sf2")
SAMPLE_RATE = 44100
PEAK_LEVEL = 0.85  # raw renders of sparse parts peak near 5% of full scale

# --- Pretrained music-emotion models --------------------------------------------------------
ESSENTIA_URL = "https://essentia.upf.edu/models/"
MOODS = ("happy", "sad", "relaxed", "aggressive")
# Softmax column that holds the mood itself. The class order differs between the models (see each
# model's .json metadata): happy/non_happy, non_sad/sad, non_relaxed/relaxed, aggressive/not_aggressive.
MOOD_COLUMNS = {"happy": 0, "sad": 1, "relaxed": 1, "aggressive": 0}
ESSENTIA_FILES = {
    "effnet": "feature-extractors/discogs-effnet/discogs-effnet-bs64-1.pb",
    "musicnn": "feature-extractors/musicnn/msd-musicnn-1.pb",
    "deam": "classification-heads/deam/deam-msd-musicnn-2.pb",
    **{mood: f"classification-heads/mood_{mood}/mood_{mood}-discogs-effnet-1.pb" for mood in MOODS},
}
