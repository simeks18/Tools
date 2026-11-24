
#!/usr/bin/env python3

import argparse
import codecs
import re
import sys
from pathlib import Path

SUPPORTED_EXTENSIONS = {".ps1", ".psm1", ".psd1"}


def read_powershell(filepath):
    """Read PowerShell files with encoding detection."""

    data = filepath.read_bytes()

    if data.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
        return data.decode("utf-32")

    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return data.decode("utf-16")

    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252")


def convert_file(filepath, output_dir=None, overwrite=False):
    """Convert one PowerShell file into Markdown and TXT."""

    filepath = Path(filepath).expanduser()

    if not filepath.is_file():
        raise FileNotFoundError(filepath)

    if filepath.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {filepath.suffix}")

    content = read_powershell(filepath)

    destination = (
        Path(output_dir).expanduser()
        if output_dir else filepath.parent
    )

    destination.mkdir(parents=True, exist_ok=True)

    md_path = destination / f"{filepath.stem}.md"
    txt_path = destination / f"{filepath.stem}.txt"

    # Prevent accidental overwriting.
    if not overwrite:
        for path in (md_path, txt_path):
            if path.exists():
                raise FileExistsError(
                    f"{path} already exists. Use --overwrite."
                )

    # Ensure embedded backticks cannot break the Markdown fence.
    longest = max(
        (len(match) for match in re.findall(r"`+", content)),
        default=0
    )
    fence = "`" * max(3, longest + 1)

    markdown = (
        f"# {filepath.name}\n\n"
        f"{fence}powershell\n"
        f"{content}"
        f"{'' if content.endswith(chr(10)) else chr(10)}"
        f"{fence}\n"
    )

    md_path.write_text(markdown, encoding="utf-8")
    txt_path.write_text(content, encoding="utf-8")

    return md_path, txt_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert PowerShell files to Markdown and TXT."
    )

    parser.add_argument(
        "files",
        nargs="+",
        help="PowerShell files to convert"
    )

    parser.add_argument(
        "-o", "--output-dir",
        help="Optional output directory"
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files"
    )

    args = parser.parse_args()

    successful = 0
    failed = 0

    for filename in args.files:
        try:
            md, txt = convert_file(
                filename,
                args.output_dir,
                args.overwrite
            )

            print(f"[OK] {filename}")
            print(f"     Markdown: {md}")
            print(f"     Text:     {txt}")

            successful += 1

        except (OSError, ValueError) as error:
            print(f"[ERROR] {filename}: {error}", file=sys.stderr)
            failed += 1

    print(f"\nConverted: {successful} | Failed: {failed}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
