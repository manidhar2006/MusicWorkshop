"""ECG input: download PhysioNet databases, read annotations, choose clips and detect heartbeats."""
import posixpath
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import wfdb
from wfdb.io import _url, download

from . import config


@dataclass
class Clip:
    """A stretch of ECG together with the sample positions of its heartbeats (R-peaks)."""
    signal: np.ndarray
    peaks: np.ndarray
    fs: float
    label: str = ""

    @property
    def rr(self):
        """Seconds between consecutive heartbeats."""
        return np.diff(self.peaks) / self.fs

    @property
    def rmssd_ms(self):
        diffs = np.diff(self.rr)
        return float(np.sqrt(np.mean(diffs ** 2))) * 1000 if len(diffs) else float("nan")

    @property
    def mean_rr_ms(self):
        rr = self.rr
        return float(np.mean(rr)) * 1000 if len(rr) else float("nan")


# --- Downloading ----------------------------------------------------------------------------

def database_files(db):
    """(versioned directory, every file name) of a PhysioNet database."""
    version_dir = posixpath.join(db, download.get_version(db))
    annotators = download.get_annotators(version_dir, "all") or []
    files = []
    for record in download.get_record_list(version_dir, "all"):
        files.append(f"{record}.hea")
        files.extend(wfdb.rdheader(record, pn_dir=version_dir).file_name or [])
        for annotator in annotators:
            name = f"{record}.{annotator}"
            try:
                _url.openurl(posixpath.join(download.config.db_index_url, version_dir, name), check_access=True)
                files.append(name)
            except FileNotFoundError:
                pass
    return version_dir, files


def _fetch(version_dir, name, dest):
    result = subprocess.run(["curl", "-sS", "-f", "-C", "-", "-o", str(dest / name),
                             f"{config.PHYSIONET_FILES_URL}/{version_dir}/{name}"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())


def download_database(db, workers=config.DOWNLOAD_WORKERS):
    """Download a whole database into data/<db>/; returns the names of files that failed."""
    # PhysioNet throttles each connection and wfdb's downloader pools only two, so use parallel curl
    dest = config.DATA_DIR / db
    dest.mkdir(parents=True, exist_ok=True)
    print(f"Listing {db} on PhysioNet...")
    version_dir, files = database_files(db)
    failed = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_fetch, version_dir, name, dest): name for name in files}
        for done, future in enumerate(as_completed(futures), 1):
            name = futures[future]
            try:
                future.result()
                print(f"[{done}/{len(files)}] {name}")
            except RuntimeError as error:
                failed.append(name)
                print(f"[{done}/{len(files)}] FAILED {name}: {error}")
    return failed


# --- PhysioNet records ----------------------------------------------------------------------

def _record_source(record, db):
    """wfdb arguments for a record: the local copy if downloaded, otherwise stream it."""
    local = config.DATA_DIR / db / record
    if Path(f"{local}.hea").exists():
        return str(local), None
    return record, db


def _rhythm_intervals(samples, notes, total_samples):
    ends = list(samples[1:]) + [total_samples]
    return [(int(start), int(end), note.strip("(").strip("\x00").strip())
            for start, end, note in zip(samples, ends, notes)]


def load_annotations(record, db):
    """Heartbeat sample positions, rhythm intervals (start, end, label) and sampling rate."""
    name, pn_dir = _record_source(record, db)
    header = wfdb.rdheader(name, pn_dir=pn_dir)
    if db == "afdb":
        beats = wfdb.rdann(name, "qrs", pn_dir=pn_dir).sample
        atr = wfdb.rdann(name, "atr", pn_dir=pn_dir)
        rhythm_samples, rhythm_notes = atr.sample, atr.aux_note
    elif db == "mitdb":
        atr = wfdb.rdann(name, "atr", pn_dir=pn_dir)
        beats = atr.sample[np.array([symbol in config.BEAT_SYMBOLS for symbol in atr.symbol])]
        is_rhythm = np.array([symbol == "+" for symbol in atr.symbol])
        rhythm_samples = atr.sample[is_rhythm]
        rhythm_notes = [note for note, keep in zip(atr.aux_note, is_rhythm) if keep]
    else:
        raise ValueError(f"unknown database {db!r} (expected 'afdb' or 'mitdb')")
    return beats, _rhythm_intervals(rhythm_samples, rhythm_notes, header.sig_len), header.fs


def _rmssd(rr):
    return float(np.sqrt(np.mean(np.diff(rr) ** 2)))


def choose_window(intervals, label, beats, fs):
    """(start, end) sample of the best CLIP_SECONDS window inside stretches labelled `label`."""
    needed = int(config.CLIP_SECONDS * fs)
    rule = config.SELECTION[label]
    best = None
    for start, end, lbl in intervals:
        if lbl != label or end - start < needed:
            continue
        span = end - start - needed
        count = min(config.CANDIDATE_WINDOWS, span // needed + 1)
        offsets = np.linspace(0, span, count).astype(int) if span > 0 else [0]
        for offset in offsets:
            low = start + int(offset)
            peaks = beats[(beats >= low) & (beats < low + needed)]
            if len(peaks) - 1 < config.MIN_INTERVALS_PER_WINDOW:
                continue
            score = _rmssd(np.diff(peaks) / fs) if rule == "steadiest" else -len(peaks)
            if best is None or score < best[0]:
                best = (score, low)
    return None if best is None else (best[1], best[1] + needed)


def record_clips(record, db):
    """The chosen normal ("N") and atrial fibrillation ("AFIB") clips of a record, by label."""
    beats, intervals, fs = load_annotations(record, db)
    name, pn_dir = _record_source(record, db)
    clips = {}
    for label in config.SELECTION:
        window = choose_window(intervals, label, beats, fs)
        if window is None:
            continue
        low, high = window
        signal = wfdb.rdrecord(name, sampfrom=low, sampto=high, pn_dir=pn_dir).p_signal[:, 0]
        clips[label] = Clip(signal, beats[(beats >= low) & (beats < high)] - low, float(fs), label)
    return clips


# --- Any ECG file ---------------------------------------------------------------------------

def load_signal(path, fs=None, channel=0):
    """(signal, sampling rate) from a WFDB record (path without extension) or a sample file."""
    if Path(f"{path}.hea").exists():
        record = wfdb.rdrecord(str(path))
        return record.p_signal[:, channel], fs or record.fs
    if not Path(path).exists():
        raise ValueError(f"{path} not found (for a WFDB record, give the path without the extension)")
    if fs is None:
        raise ValueError(f"{path} is not a WFDB record, so the sampling rate (fs) is required")
    signal = np.loadtxt(path, delimiter="," if str(path).endswith(".csv") else None)
    return (signal[:, channel] if signal.ndim > 1 else signal), fs


def detect_beats(signal, fs):
    """R-peak sample positions found by the XQRS detector - no annotation file needed."""
    from wfdb.processing import xqrs_detect
    return xqrs_detect(signal, fs=fs, verbose=False)


def clip_from_signal(signal, fs, start=0.0, duration=60.0):
    """Cut a window out of a raw ECG signal and find its heartbeats."""
    low = int(start * fs)
    high = min(len(signal), low + int(duration * fs))
    if high - low < config.MIN_ANALYSIS_SECONDS * fs:
        raise ValueError(f"only {max(high - low, 0) / fs:.1f}s of signal in that window; "
                         f"need at least {config.MIN_ANALYSIS_SECONDS}s")
    window = np.asarray(signal[low:high])
    peaks = detect_beats(window, fs)
    if len(peaks) < config.MIN_DETECTED_BEATS:
        raise ValueError(f"only {len(peaks)} heartbeats found; try a longer duration or check fs/channel")
    return Clip(window, np.asarray(peaks), float(fs))
