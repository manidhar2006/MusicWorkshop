"""The sonification rule: every heartbeat becomes one melody note."""
from dataclasses import dataclass

import numpy as np

from . import config


@dataclass
class Note:
    pitch: int
    start: float
    duration: float
    velocity: int
    deviation: float = 0.0
    rr: float = 0.0
    chromatic: bool = False


def _scale_below(scale):
    """The same scale walked downward from the root: C D E G A -> C A G E D."""
    return sorted((12 - step) % 12 for step in scale)


def _offset(step, scale):
    octave, degree = divmod(step, len(scale))
    return octave * 12 + scale[degree]


def deviation_to_pitch(deviation):
    """MIDI pitch for a beat's R-R deviation: faster beats go up, slower ones down the scale."""
    scale = config.PENTATONIC if abs(deviation) < config.CHROMATIC_THRESHOLD else config.CHROMATIC
    steps = len(scale) * config.OCTAVE_RANGE
    step = round(float(min(abs(deviation) / config.FULL_RANGE_DEVIATION, 1.0)) * steps)
    if deviation < 0:
        pitch = config.ROOT_NOTE + _offset(step, scale)
    else:
        pitch = config.ROOT_NOTE - _offset(step, _scale_below(scale))
    low, high = config.PITCH_RANGE
    return int(min(max(pitch, low), high))


def running_means(rr):
    """Mean of each interval and up to RUNNING_MEAN_BEATS - 1 intervals before it."""
    n = config.RUNNING_MEAN_BEATS
    return np.array([np.mean(rr[max(0, i - n + 1):i + 1]) for i in range(len(rr))])


def beat_velocities(signal, peaks):
    """Note loudness from the ECG amplitude at each beat, scaled to VELOCITY_RANGE per clip."""
    # automatic R-peak marks can land a few samples off the apex, so take the local maximum
    w = config.PEAK_SEARCH_SAMPLES
    amplitudes = np.array([signal[max(0, p - w):p + w + 1].max() for p in peaks])
    low, high = config.VELOCITY_RANGE
    if amplitudes.max() <= amplitudes.min():
        return np.full(len(peaks), (low + high) // 2)
    scaled = np.interp(amplitudes, [amplitudes.min(), amplitudes.max()], [low, high])
    return np.clip(scaled, low, high).astype(int)


def melody(clip):
    """One note per heartbeat (the last beat has no following interval, so it is dropped)."""
    rr = clip.rr
    if len(rr) == 0:
        return []
    means = running_means(rr)
    velocities = beat_velocities(np.asarray(clip.signal), clip.peaks)
    notes = []
    for i, interval in enumerate(rr):
        deviation = float((interval - means[i]) / means[i])
        notes.append(Note(pitch=deviation_to_pitch(deviation),
                          start=float(clip.peaks[i] / clip.fs),
                          duration=float(interval * config.NOTE_LENGTH),
                          velocity=int(velocities[i]),
                          deviation=deviation,
                          rr=float(interval),
                          chromatic=abs(deviation) >= config.CHROMATIC_THRESHOLD))
    return notes
