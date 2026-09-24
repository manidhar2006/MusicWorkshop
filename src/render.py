"""
Phase 4 (used already here for Phase 3 sanity-checks): turn a note list from
mapping.sonify_clip() into a MIDI file, and optionally render that MIDI to a
WAV file via FluidSynth.
"""
import subprocess

import numpy as np
import pretty_midi
from scipy.io import wavfile

DEFAULT_SOUNDFONT = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
ACOUSTIC_GRAND_PIANO = 0
NORMALIZE_TARGET = 0.85  # target peak as a fraction of full scale after normalization


def notes_to_midi(notes, out_path, instrument_program=ACOUSTIC_GRAND_PIANO):
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=instrument_program)
    for n in notes:
        instrument.notes.append(pretty_midi.Note(
            velocity=n["velocity"],
            pitch=n["pitch"],
            start=n["start"],
            end=n["start"] + n["duration"],
        ))
    midi.instruments.append(instrument)
    midi.write(out_path)
    return out_path


def midi_to_wav(midi_path, wav_path, soundfont=DEFAULT_SOUNDFONT, normalize=True):
    result = subprocess.run(
        ["fluidsynth", "-ni", soundfont, midi_path, "-F", wav_path, "-r", "44100"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"fluidsynth failed: {result.stderr}")
    if normalize:
        normalize_wav(wav_path)
    return wav_path


def normalize_wav(wav_path, target=NORMALIZE_TARGET):
    """Scale a WAV's peak amplitude up to `target` * full-scale in place.

    FluidSynth renders single-note melodic lines at moderate velocity well
    below full scale (observed ~5-6% peak), which is too quiet for
    comfortable side-by-side listening. This brings it up without clipping.
    """
    fs, data = wavfile.read(wav_path)
    max_possible = np.iinfo(data.dtype).max
    peak = np.abs(data).max()
    if peak == 0:
        return
    gain = (target * max_possible) / peak
    scaled = np.clip(data.astype(np.float64) * gain, -max_possible - 1, max_possible)
    wavfile.write(wav_path, fs, scaled.astype(data.dtype))
