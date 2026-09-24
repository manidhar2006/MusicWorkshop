"""
Phase 1: read a short window of an ECG record straight from PhysioNet (no full
local download needed - the raw records are ~10 hours / tens of MB each, and we
only ever need short segments for the sonification clips) and plot it.
"""
import matplotlib.pyplot as plt
import wfdb

RECORD = "04043"       # MIT-BIH Atrial Fibrillation Database record
PN_DIR = "afdb"
DURATION_SEC = 10


def load_segment(record=RECORD, pn_dir=PN_DIR, duration_sec=DURATION_SEC):
    header = wfdb.rdheader(record, pn_dir=pn_dir)
    n_samples = int(duration_sec * header.fs)
    return wfdb.rdrecord(record, pn_dir=pn_dir, sampto=n_samples)


def plot_segment(record, out_path):
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(record.p_signal[:, 0], linewidth=0.8)
    ax.set_title(f"Record {record.record_name} - {record.sig_name[0]}")
    ax.set_xlabel(f"Sample (fs={record.fs} Hz)")
    ax.set_ylabel("Amplitude (mV)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    print(f"Saved plot to {out_path}")


if __name__ == "__main__":
    rec = load_segment()
    print(f"Loaded record {rec.record_name}: {rec.p_signal.shape[0]} samples, "
          f"{rec.p_signal.shape[1]} channels, fs={rec.fs} Hz")
    plot_segment(rec, "output/afdb_04043_first10s.png")
