#!/usr/bin/env python3
"""
Merge a directory tree of PDFs into a single PDF, in tree order
(folders and files sorted depth-first, with natural number sorting
so "page2.pdf" comes before "page10.pdf").

Optionally adds a bookmark/outline for each source file (and each
folder), so the merged PDF has a navigable table of contents matching
the original tree structure.

Requires: pypdf  (pip install pypdf --break-system-packages)

Usage:
    python merge_tree_to_pdf.py <input_dir> <output.pdf> [--bookmarks] [--include PATTERN]

Examples:
    python merge_tree_to_pdf.py ./pdfout merged.pdf
    python merge_tree_to_pdf.py ./pdfout merged.pdf --bookmarks
    python merge_tree_to_pdf.py ./pdfout merged.pdf --include "*.pdf" --bookmarks
"""

import argparse
import fnmatch
import re
import sys
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    sys.exit(
        "Error: pypdf is required.\n"
        "Install it with: pip install pypdf --break-system-packages"
    )


def natural_key(s: str):
    """Sort key that handles embedded numbers naturally (file2 < file10)."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def collect_tree(input_dir: Path, pattern: str):
    """
    Walk the directory tree depth-first, sorted naturally at each level.
    Returns a flat ordered list of (pdf_path, relative_path) tuples and,
    separately, the nested structure for bookmark building.
    """
    entries = []  # (Path, depth, is_dir)

    def walk(dir_path: Path, depth: int):
        children = sorted(dir_path.iterdir(), key=lambda p: natural_key(p.name))
        subdirs = [c for c in children if c.is_dir()]
        files = [
            c
            for c in children
            if c.is_file() and c.suffix.lower() == ".pdf" and fnmatch.fnmatch(c.name, pattern)
        ]
        for f in files:
            entries.append((f, depth, False))
        for d in subdirs:
            entries.append((d, depth, True))
            walk(d, depth + 1)

    walk(input_dir, 0)
    return entries


def build_merged_pdf(input_dir: Path, output_path: Path, pattern: str, add_bookmarks: bool):
    entries = collect_tree(input_dir, pattern)
    pdf_files = [e for e in entries if not e[2]]

    if not pdf_files:
        sys.exit(f"No PDF files found under {input_dir} matching '{pattern}'")

    writer = PdfWriter()
    page_count = 0
    converted, failed = 0, []

    # Pass 1: merge every page first, and record where each entry's
    # content starts. Bookmarks can only safely point at pages that
    # already exist in the writer, so we add them in a second pass below.
    bookmark_plan = []  # (depth, is_dir, title, start_page)

    for path, depth, is_dir in entries:
        if is_dir:
            if add_bookmarks:
                bookmark_plan.append((depth, True, path.name + "/", page_count))
            continue

        rel = path.relative_to(input_dir)
        try:
            reader = PdfReader(str(path))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    failed.append((rel, "encrypted/password-protected"))
                    continue
            start_page = page_count
            for page in reader.pages:
                writer.add_page(page)
                page_count += 1
            if add_bookmarks:
                bookmark_plan.append((depth, False, path.stem, start_page))
            converted += 1
            print(f"  + {rel} ({len(reader.pages)} page(s))")
        except Exception as exc:
            failed.append((rel, str(exc)))
            print(f"  ! {rel} -> FAILED: {exc}")

    # Pass 2: now that every page exists in the writer, add the outline
    # items (folders and files) in tree order, nesting by depth.
    if add_bookmarks:
        folder_stack = []  # (depth, bookmark_obj)
        for depth, is_dir, title, start_page in bookmark_plan:
            while folder_stack and folder_stack[-1][0] >= depth:
                folder_stack.pop()
            parent = folder_stack[-1][1] if folder_stack else None
            bm = writer.add_outline_item(title, start_page, parent=parent)
            if is_dir:
                folder_stack.append((depth, bm))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"\nMerged {converted} file(s), {page_count} total page(s) -> {output_path}")
    if failed:
        print(f"\n{len(failed)} file(s) failed to merge:")
        for rel, reason in failed:
            print(f"  - {rel}: {reason}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_dir", type=Path, help="Root directory containing PDFs (searched recursively)")
    parser.add_argument("output_pdf", type=Path, help="Path to write the merged PDF")
    parser.add_argument(
        "--include", default="*.pdf", help="Filename glob pattern to include (default: *.pdf)"
    )
    parser.add_argument(
        "--bookmarks",
        action="store_true",
        help="Add a navigable outline/bookmark per file and folder, matching the tree structure",
    )
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    if not input_dir.is_dir():
        sys.exit(f"Error: input directory does not exist: {input_dir}")

    print(f"Scanning {input_dir} for PDFs matching '{args.include}'...\n")
    build_merged_pdf(input_dir, args.output_pdf.resolve(), args.include, args.bookmarks)


if __name__ == "__main__":
    main()
