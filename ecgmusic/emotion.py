"""Estimate a melody's emotional character on Russell's valence-arousal plane."""
from dataclasses import dataclass

import numpy as np

from . import config


@dataclass
class Emotion:
    valence: float
    arousal: float
    quadrant: str
    instrument: str
    program: int


def descriptors(notes):
    """The three musical cues the estimate is built from."""
    pitches = np.array([n.pitch for n in notes])
    iois = np.diff([n.start for n in notes])
    irregularity = float(np.std(iois) / np.mean(iois)) if len(iois) and np.mean(iois) > 0 else 0.0
    return {
        "rhythmic_irregularity": float(np.clip(irregularity, 0.0, 1.0)),
        "pitch_spread": float(pitches.std()),
        "consonance": 1.0 - float(np.mean([n.chromatic for n in notes])),
    }


def _normalise(value, bounds):
    low, high = bounds
    return float(np.clip((value - low) / (high - low), 0.0, 1.0))


def valence_arousal(cues):
    """Valence and arousal in [-1, 1]."""
    irregular = _normalise(cues["rhythmic_irregularity"], config.IRREGULARITY_RANGE)
    spread = _normalise(cues["pitch_spread"], config.SPREAD_RANGE)
    consonance = _normalise(cues["consonance"], config.CONSONANCE_RANGE)
    arousal = (config.AROUSAL_WEIGHTS[0] * irregular + config.AROUSAL_WEIGHTS[1] * spread - 0.5) * 2
    valence = (config.VALENCE_WEIGHTS[0] * consonance + config.VALENCE_WEIGHTS[1] * (1 - spread) - 0.5) * 2
    return float(valence), float(arousal)


def estimate_emotion(notes):
    valence, arousal = valence_arousal(descriptors(notes))
    signs = ("+" if valence >= 0 else "-", "+" if arousal >= 0 else "-")
    quadrant = next(name for name, q in config.QUADRANTS.items() if (q["valence"], q["arousal"]) == signs)
    q = config.QUADRANTS[quadrant]
    return Emotion(valence, arousal, quadrant, q["instrument"], q["program"])
