"""
Full local download of a PhysioNet database (generalized from the original
afdb-only downloader).

PhysioNet throttles each HTTP connection to ~20KB/s. wfdb.dl_database() (and
even a hand-rolled ThreadPoolExecutor calling wfdb's own download function)
is stuck at effectively 2 concurrent connections regardless of thread count,
because wfdb.io._url uses one shared requests.Session with
HTTPAdapter(pool_maxsize=2, pool_block=True) - every thread funnels through
that same 2-connection pool.

This script bypasses wfdb's networking layer entirely and shells out to curl
per file (each curl process gets its own OS-level TCP connection, so N
parallel curl processes really do give N times the throughput). curl's -C -
resumes partially-downloaded files, so re-running this script after an
interruption picks up where it left off instead of restarting.
"""
import argparse
import os
import posixpath
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

import wfdb
from wfdb.io import download

N_WORKERS = 8
BASE_URL = "https://physionet.org/files"
DATA_ROOT = os.path.join(os.path.dirname(__file__), "..", "data")


def build_file_list(db_dir_name):
    db_dir = posixpath.join(db_dir_name, download.get_version(db_dir_name))
    record_list = download.get_record_list(db_dir, "all")
    annotators = download.get_annotators(db_dir, "all")

    files = []
    for rec in record_list:
        files.append(rec + ".hea")
        record = wfdb.rdheader(rec, pn_dir=db_dir)
        for f in record.file_name or []:
            files.append(f)
        if annotators is not None:
            for a in annotators:
                ann_file = rec + "." + a
                url = posixpath.join(download.config.db_index_url, db_dir, ann_file)
                try:
                    from wfdb.io import _url

                    _url.openurl(url, check_access=True)
                    files.append(ann_file)
                except FileNotFoundError:
                    pass
    return db_dir, files


def curl_download(db_dir, filename, dl_dir):
    url = f"{BASE_URL}/{db_dir}/{filename}"
    local_path = os.path.join(dl_dir, filename)
    result = subprocess.run(
        ["curl", "-sS", "-f", "-C", "-", "-o", local_path, url],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed for {filename}: {result.stderr.strip()}")
    return filename


def download_database(db_dir_name, n_workers=N_WORKERS):
    dl_dir = os.path.join(DATA_ROOT, db_dir_name)
    os.makedirs(dl_dir, exist_ok=True)
    print(f"Building file list for {db_dir_name} (one-time metadata pass over PhysioNet)...")
    db_dir, files = build_file_list(db_dir_name)
    print(f"{len(files)} files to fetch, {n_workers} parallel curl connections...")

    done, failed = 0, []
    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        futures = {pool.submit(curl_download, db_dir, f, dl_dir): f for f in files}
        for fut in as_completed(futures):
            f = futures[fut]
            done += 1
            try:
                fut.result()
                print(f"[{done}/{len(files)}] OK {f}")
            except Exception as e:
                print(f"[{done}/{len(files)}] FAILED {f}: {e}")
                failed.append(f)

    print(f"Download pass complete for {db_dir_name}.")
    if failed:
        print(f"{len(failed)} file(s) failed, re-run this script to retry them: {failed}")
    return failed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("db", help="PhysioNet database directory name, e.g. afdb, mitdb")
    args = parser.parse_args()
    download_database(args.db)
