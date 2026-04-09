#!/usr/bin/env python3
"""
HEVC to MP4 Converter for WSL
Usage: python3 hevc_to_mp4.py <input_file_or_uri> [--output <output_file>]
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def convert_wsl_uri_to_path(uri: str) -> str:
    """
    Convert various URI/path formats to a WSL-compatible Linux path.
    Handles:
      - Windows paths:       C:\\Users\\...  or  C:/Users/...
      - UNC paths:           \\\\server\\share\\...
      - file:// URIs:        file:///C:/Users/...
      - WSL mnt paths:       /mnt/c/Users/...  (returned as-is)
      - Relative/Linux paths (returned as-is)
    """
    original = uri

    # Strip file:// URI scheme
    if uri.lower().startswith("file:///"):
        uri = uri[8:]           # remove 'file:///'
        uri = uri.replace("%20", " ").replace("%28", "(").replace("%29", ")")
    elif uri.lower().startswith("file://"):
        uri = uri[7:]

    # UNC path  \\server\share\...
    unc_match = re.match(r"^[\\]{2}([^\\]+)[\\](.+)$", uri)
    if unc_match:
        print(f"[warning] UNC paths ({original}) may not be accessible inside WSL.", file=sys.stderr)
        uri = "/" + uri.replace("\\", "/").lstrip("/")
        return uri

    # Windows drive letter  C:\...  or  C:/...
    win_match = re.match(r"^([A-Za-z]):[/\\](.*)$", uri)
    if win_match:
        drive = win_match.group(1).lower()
        rest  = win_match.group(2).replace("\\", "/")
        return f"/mnt/{drive}/{rest}"

    # Already a Linux / WSL path — return as-is
    return uri


def find_ffmpeg() -> str:
    """Return the ffmpeg executable path, or raise if not found."""
    for candidate in ("ffmpeg", "/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
        try:
            subprocess.run([candidate, "-version"],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           check=True)
            return candidate
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    raise FileNotFoundError(
        "ffmpeg not found. Install it with:  sudo apt update && sudo apt install ffmpeg"
    )


def build_output_path(input_path: str, output_arg) -> str:
    """Derive the output .mp4 path from the input path (or use --output if given)."""
    if output_arg:
        return output_arg
    p = Path(input_path)
    return str(p.with_suffix(".mp4"))


def convert(input_path: str, output_path: str, ffmpeg: str) -> None:
    """Run the ffmpeg conversion."""
    if not os.path.isfile(input_path):
        print(f"[error] Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if os.path.abspath(input_path) == os.path.abspath(output_path):
        print("[error] Input and output paths are the same.", file=sys.stderr)
        sys.exit(1)

    cmd = [
        ffmpeg,
        "-i", input_path,
        "-c:v", "copy",          # copy HEVC stream — no re-encode, lossless & fast
        "-c:a", "aac",           # re-encode audio to AAC for broad MP4 compatibility
        "-b:a", "192k",
        "-movflags", "+faststart",   # web-friendly: move moov atom to front
        "-y",                    # overwrite output without asking
        output_path,
    ]

    print(f"[info] Input  : {input_path}")
    print(f"[info] Output : {output_path}")
    print(f"[info] Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd)

    if result.returncode == 0:
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"\n[success] Conversion complete -> {output_path}  ({size_mb:.1f} MB)")
    else:
        print(f"\n[error] ffmpeg exited with code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="Convert HEVC video to MP4 (WSL-aware path handling)."
    )
    parser.add_argument(
        "input",
        help="Input file path or URI (Windows path, file:// URI, or Linux path).",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output .mp4 file path (default: same directory/name as input).",
    )
    args = parser.parse_args()

    ffmpeg      = find_ffmpeg()
    input_path  = convert_wsl_uri_to_path(args.input)
    output_path = build_output_path(input_path, args.output)

    convert(input_path, output_path, ffmpeg)


if __name__ == "__main__":
    main()
