"""
Phase 3: the actual sonification mapping.

Rules (per the proposal):
  - R-R interval        -> note onset time and duration (each beat = one note)
  - deviation of the current R-R interval from a running mean of recent
    R-R intervals -> pitch: small deviation stays inside a pentatonic scale
    close to the root note; larger deviation is allowed to move chromatically
    and further from the root (direction: a shorter-than-average interval,
    i.e. a faster beat, moves pitch UP; a longer-than-average interval moves
    pitch DOWN)
  - ECG amplitude at the R-peak -> note velocity (loudness)

A stable rhythm (small, consistent R-R intervals) should therefore produce a
tight cluster of pentatonic notes near the root - calm and consonant. An
irregular rhythm (AFib) should scatter across a wider, chromatic range -
unstable and dissonant. This is deliberately a straightforward first-pass
mapping (per the plan: "start simple, then refine").
"""
import numpy as np

PENTATONIC = [0, 2, 4, 7, 9]  # major pentatonic scale, semitone offsets
ROOT_NOTE = 60  # MIDI note number for C4 (middle C)
OCTAVE_RANGE = 2  # max octaves of pitch movement away from the root
RUNNING_MEAN_WINDOW = 5  # beats of trailing history used for the running mean
CHROMATIC_THRESHOLD = 0.12  # relative deviation above which chromatic pitches are allowed
MAX_DEVIATION_FOR_FULL_RANGE = 0.5  # relative deviation that maps to the full pitch range
NOTE_GAP_RATIO = 0.85  # note duration as a fraction of the R-R interval (leaves a gap)
MIN_VELOCITY, MAX_VELOCITY = 40, 110
MIN_MIDI_PITCH, MAX_MIDI_PITCH = 21, 108  # full piano range, clamps extreme excursions


def _running_means(rr, window=RUNNING_MEAN_WINDOW):
    """Causal running mean of R-R intervals: mean of the last `window` values
    up to and including index i (uses only past/current data, no lookahead)."""
    means = np.empty(len(rr))
    for i in range(len(rr)):
        start = max(0, i - window + 1)
        means[i] = np.mean(rr[start:i + 1])
    return means


def _deviation_to_pitch(deviation):
    """Map a signed relative R-R deviation to a MIDI pitch around ROOT_NOTE."""
    abs_dev = min(abs(deviation) / MAX_DEVIATION_FOR_FULL_RANGE, 1.0)
    scale = PENTATONIC if abs(deviation) < CHROMATIC_THRESHOLD else list(range(12))

    step_count = len(scale) * OCTAVE_RANGE
    step_index = round(abs_dev * step_count)
    octave, degree = divmod(step_index, len(scale))
    semitone_offset = octave * 12 + scale[degree]

    # shorter-than-average R-R (faster beat) -> pitch up; longer -> pitch down
    if deviation < 0:
        semitone_offset = -semitone_offset

    pitch = ROOT_NOTE + semitone_offset
    return int(np.clip(pitch, MIN_MIDI_PITCH, MAX_MIDI_PITCH))


def _amplitude_to_velocity(amplitude, amp_min, amp_max):
    if amp_max <= amp_min:
        return (MIN_VELOCITY + MAX_VELOCITY) // 2
    velocity = np.interp(amplitude, [amp_min, amp_max], [MIN_VELOCITY, MAX_VELOCITY])
    return int(np.clip(velocity, MIN_VELOCITY, MAX_VELOCITY))


PEAK_AMPLITUDE_WINDOW = 5  # samples either side of the annotated peak (20ms at 250Hz)


def _peak_amplitude(signal, peak_idx, window=PEAK_AMPLITUDE_WINDOW):
    """Max signal value in a small window around the annotated R-peak.

    afdb's .qrs annotations are an unaudited automatic detector (see the
    Phase 2 data-quality finding in extract_features.py) - the marked sample
    can land a few points off the true apex. Taking the local max in a small
    window is more robust to that jitter than reading a single sample.
    """
    lo = max(0, peak_idx - window)
    hi = min(len(signal), peak_idx + window + 1)
    return float(signal[lo:hi].max())


def sonify_clip(clip):
    """
    clip: dict with 'signal' (1D array), 'peaks_relative' (sample indices into
    signal), 'rr_intervals_sec' (len = len(peaks_relative) - 1), 'fs'.

    Returns a list of note dicts: {pitch, start, duration, velocity, deviation,
    used_chromatic} — one per beat except the last (which has no following
    R-R interval to derive a duration from).
    """
    signal = np.asarray(clip["signal"])
    peaks = np.asarray(clip["peaks_relative"])
    rr = np.asarray(clip["rr_intervals_sec"])
    fs = float(clip["fs"])

    peak_times = peaks / fs
    amplitudes = np.array([_peak_amplitude(signal, p) for p in peaks])
    amp_min, amp_max = float(amplitudes.min()), float(amplitudes.max())
    running_mean = _running_means(rr)

    notes = []
    for i in range(len(rr)):
        deviation = (rr[i] - running_mean[i]) / running_mean[i]
        pitch = _deviation_to_pitch(deviation)
        velocity = _amplitude_to_velocity(amplitudes[i], amp_min, amp_max)

        notes.append({
            "pitch": pitch,
            "start": float(peak_times[i]),
            "duration": float(rr[i] * NOTE_GAP_RATIO),
            "velocity": velocity,
            "deviation": float(deviation),
            "used_chromatic": abs(deviation) >= CHROMATIC_THRESHOLD,
        })
    return notes


if __name__ == "__main__":
    import os

    clip_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed",
                              "04043_N_clip.npz")
    with np.load(clip_path) as data:
        clip = {k: data[k] for k in data.files}
    notes = sonify_clip(clip)
    print(f"{len(notes)} notes generated")
    print("Pitch range:", min(n["pitch"] for n in notes), "-", max(n["pitch"] for n in notes))
    print("Chromatic notes:", sum(n["used_chromatic"] for n in notes), "/", len(notes))
