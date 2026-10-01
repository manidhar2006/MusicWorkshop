"""Write tracks to MIDI and render them to WAV audio with FluidSynth."""
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pretty_midi
from scipy.io import wavfile

from . import config


def write_midi(tracks, path):
    midi = pretty_midi.PrettyMIDI()
    for track in tracks:
        instrument = pretty_midi.Instrument(program=track.program, is_drum=track.is_drum, name=track.name)
        instrument.notes.extend(
            pretty_midi.Note(velocity=int(n.velocity), pitch=int(n.pitch), start=n.start, end=n.start + n.duration)
            for n in track.notes)
        midi.instruments.append(instrument)
    midi.write(str(path))
    return Path(path)


def normalise(wav_path, level=config.PEAK_LEVEL):
    """Scale the loudest sample to `level` of full scale, in place."""
    rate, data = wavfile.read(str(wav_path))
    full_scale = np.iinfo(data.dtype).max
    peak = np.abs(data.astype(np.int64)).max()
    if peak:
        scaled = data.astype(np.float64) * (level * full_scale / peak)
        wavfile.write(str(wav_path), rate, np.clip(scaled, -full_scale - 1, full_scale).astype(data.dtype))


def render_wav(midi_path, wav_path):
    if shutil.which("fluidsynth") is None:
        raise RuntimeError("FluidSynth is not installed (Ubuntu: sudo apt install fluidsynth fluid-soundfont-gm)")
    result = subprocess.run(["fluidsynth", "-ni", config.SOUNDFONT, str(midi_path), "-F", str(wav_path),
                             "-r", str(config.SAMPLE_RATE)], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"fluidsynth failed: {result.stderr.strip()}")
    normalise(wav_path)
    return Path(wav_path)


def render(tracks, base_path, audio=True):
    """Write base_path.mid and, if `audio`, base_path.wav. Returns (midi path, wav path or None)."""
    base_path = Path(base_path)
    midi_path = write_midi(tracks, base_path.with_suffix(".mid"))
    wav_path = render_wav(midi_path, base_path.with_suffix(".wav")) if audio else None
    return midi_path, wav_path
