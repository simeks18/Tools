#!/usr/bin/env python3
"""
Convert a directory tree of Word documents (.doc, .docx) into PDFs,
preserving the original folder structure in the output location.

Requires LibreOffice installed and available on PATH as `soffice`
(on most Linux distros: `sudo apt install libreoffice`;
 on macOS: `brew install --cask libreoffice`;
 on Windows: install LibreOffice and add its program folder to PATH).

Usage:
    python convert_tree_to_pdf.py <input_dir> <output_dir> [--workers N] [--overwrite]

Example:
    python convert_tree_to_pdf.py ./my_docs ./my_docs_pdf
"""

import argparse
import concurrent.futures
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

# Each thread gets its own LibreOffice user profile dir to avoid lock conflicts.
_thread_local = threading.local()

WORD_EXTENSIONS = {".doc", ".docx", ".dot", ".dotx", ".rtf"}


def find_soffice() -> str:
    """Locate the LibreOffice headless binary."""
    for name in ("soffice", "libreoffice"):
        path = shutil.which(name)
        if path:
            return path
    # Common macOS install location not always on PATH
    mac_path = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if Path(mac_path).exists():
        return mac_path
    sys.exit(
        "Error: could not find LibreOffice ('soffice'/'libreoffice') on PATH.\n"
        "Install LibreOffice and ensure it's accessible from the command line."
    )


def collect_word_files(input_dir: Path):
    """Recursively find all Word documents under input_dir."""
    return [
        p
        for p in input_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in WORD_EXTENSIONS
    ]


def convert_one(soffice_bin: str, src: Path, input_dir: Path, output_dir: Path, overwrite: bool):
    """Convert a single Word document to PDF, mirroring its relative path."""
    rel_dir = src.parent.relative_to(input_dir)
    dest_dir = output_dir / rel_dir
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_pdf = dest_dir / (src.stem + ".pdf")
    if dest_pdf.exists() and not overwrite:
        return src, dest_pdf, "skipped (already exists)"

    # Give this thread its own LibreOffice profile dir so parallel runs
    # don't fight over the same lock file.
    if not hasattr(_thread_local, "profile_dir"):
        _thread_local.profile_dir = tempfile.mkdtemp(prefix="soffice_profile_")
    profile_uri = Path(_thread_local.profile_dir).as_uri()

    # LibreOffice writes to a directory using the source filename stem.
    cmd = [
        soffice_bin,
        "--headless",
        "--norestore",
        f"-env:UserInstallation={profile_uri}",
        "--convert-to",
        "pdf",
        "--outdir",
        str(dest_dir),
        str(src),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0 or not dest_pdf.exists():
        return src, dest_pdf, f"FAILED: {result.stderr.strip() or result.stdout.strip()}"

    return src, dest_pdf, "ok"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_dir", type=Path, help="Root directory containing Word documents")
    parser.add_argument("output_dir", type=Path, help="Directory to write the converted PDFs into")
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help=(
            "Number of parallel conversion workers (default: 1). "
            "LibreOffice headless can be unstable when run in parallel on some "
            "systems even with isolated profiles -- raise this only if you've "
            "verified it's stable in your environment."
        ),
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Re-convert and overwrite PDFs that already exist"
    )
    args = parser.parse_args()

    input_dir: Path = args.input_dir.resolve()
    output_dir: Path = args.output_dir.resolve()

    if not input_dir.is_dir():
        sys.exit(f"Error: input directory does not exist: {input_dir}")

    soffice_bin = find_soffice()
    files = collect_word_files(input_dir)

    if not files:
        print(f"No Word documents found under {input_dir}")
        return

    print(f"Found {len(files)} Word document(s) under {input_dir}")
    print(f"Converting with {args.workers} worker(s)...\n")

    output_dir.mkdir(parents=True, exist_ok=True)

    ok, skipped, failed = 0, 0, 0
    # LibreOffice headless conversions don't parallelize safely with a single
    # shared user profile by default, so each worker gets its own profile dir
    # to avoid lock conflicts.
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(convert_one, soffice_bin, f, input_dir, output_dir, args.overwrite): f
            for f in files
        }
        for future in concurrent.futures.as_completed(futures):
            src, dest, status = future.result()
            rel = src.relative_to(input_dir)
            print(f"  {rel} -> {status}")
            if status == "ok":
                ok += 1
            elif status.startswith("skipped"):
                skipped += 1
            else:
                failed += 1

    print(f"\nDone. {ok} converted, {skipped} skipped, {failed} failed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
