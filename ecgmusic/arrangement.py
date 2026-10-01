"""Arrange a melody into a three-part piece: melody, string harmony and a heartbeat pulse."""
from dataclasses import dataclass, field

import numpy as np

from . import config
from .melody import Note


@dataclass
class Chord:
    start: float
    end: float
    pitches: list
    tier: str
    velocity: int


@dataclass
class Track:
    name: str
    program: int
    notes: list = field(default_factory=list)
    is_drum: bool = False


def tension_tier(mean_deviation):
    if mean_deviation >= config.CHAOTIC_AT:
        return "chaotic"
    return "tense" if mean_deviation >= config.TENSE_AT else "consonant"


def harmonize(notes):
    """One chord per BEATS_PER_CHORD beats along C-Am-F-G, soured as the beats get irregular."""
    chords = []
    for i in range(0, len(notes), config.BEATS_PER_CHORD):
        group = notes[i:i + config.BEATS_PER_CHORD]
        root, quality = config.PROGRESSION[(i // config.BEATS_PER_CHORD) % len(config.PROGRESSION)]
        tier = tension_tier(np.mean([abs(n.deviation) for n in group]))
        shape = config.CHORD_SHAPES.get(tier, quality)
        chords.append(Chord(start=group[0].start, end=group[-1].start + group[-1].rr,
                            pitches=[root + interval for interval in shape],
                            tier=tier, velocity=config.CHORD_VELOCITY[tier]))
    return chords


def heartbeat_pulse(notes):
    """A 'lub-dub' bass-drum pair on every beat, as loud as that beat's melody note."""
    hits = []
    for n in notes:
        lub = int(np.interp(n.velocity, config.VELOCITY_RANGE, config.PULSE_VELOCITY_RANGE))
        dub_at = n.start + min(config.DUB_DELAY_FRACTION * n.rr, config.DUB_DELAY_MAX)
        hits.append(Note(config.LUB_DRUM, n.start, config.DRUM_HIT_SECONDS, lub))
        hits.append(Note(config.DUB_DRUM, dub_at, config.DRUM_HIT_SECONDS, int(lub * config.DUB_VELOCITY_RATIO)))
    return hits


def arrange(notes, melody_program):
    """The three tracks of the piece, plus the chord list (for plots and statistics)."""
    chords = harmonize(notes)
    harmony = [Note(pitch, c.start, c.end - c.start, c.velocity) for c in chords for pitch in c.pitches]
    tracks = [
        Track("melody", melody_program, notes),
        Track("harmony", config.STRINGS_PROGRAM, harmony),
        Track("pulse", config.DRUM_KIT_PROGRAM, heartbeat_pulse(notes), is_drum=True),
    ]
    return tracks, chords
